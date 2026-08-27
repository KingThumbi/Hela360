from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from sqlalchemy import func

from app.errors import ConflictError, NotFoundError, ValidationError
from app.models import (
    PaymentMethod,
    Sale,
    SalePayment,
    Till,
    TillShift,
    Warehouse,
)
from app.models.pos import SaleRefund
from app.models.security import (
    TokenRevocationReason,
    UserSession,
)
from app.services.tenant.auth.refresh_token_service import (
    RefreshTokenService,
)
from app.services.tenant.auth.session_service import (
    SessionService,
)


TWOPLACES = Decimal("0.01")


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _money(
    value,
    field_name: str,
    *,
    default: Decimal | None = None,
) -> Decimal:
    if value in (None, ""):
        if default is not None:
            return default

        raise ValidationError(
            f"{field_name} is required."
        )

    try:
        amount = Decimal(str(value))
    except (
        InvalidOperation,
        TypeError,
        ValueError,
    ) as exc:
        raise ValidationError(
            f"{field_name} must be a valid number."
        ) from exc

    if amount < 0:
        raise ValidationError(
            f"{field_name} cannot be negative."
        )

    return amount.quantize(
        TWOPLACES,
        rounding=ROUND_HALF_UP,
    )


def _identifier(
    value,
    field_name: str,
) -> str:
    """
    Normalize a Hela360 domain identifier.

    Hela360 tenant-domain identifiers are UUID-formatted
    String(36) values. Services therefore compare and persist
    identifiers as strings rather than converting them into
    native Python UUID objects.
    """
    if value in (None, ""):
        raise ValidationError(
            f"{field_name} is required."
        )

    return str(value)


def shift_is_owned_by_session(
    shift: TillShift,
    session_id: str | None,
) -> bool:
    """
    Return whether an open till shift is controlled by the
    authenticated session.

    Till-shift discovery and till-shift authority are intentionally
    separate concerns. A cashier may discover an existing open shift
    from another authenticated session, but only the session recorded
    in active_session_id may perform POS mutations against that shift.
    """
    if not session_id:
        return False

    active_session_id = getattr(
        shift,
        "active_session_id",
        None,
    )

    if not active_session_id:
        return False

    return str(active_session_id) == str(session_id)


class TillShiftService:
    def __init__(self, session):
        self.session = session

    def list_active_tills(
        self,
        *,
        tenant_id: str,
        branch_id: str,
    ) -> list[Till]:
        self._require_branch(branch_id)

        return (
            self.session.query(Till)
            .join(
                Warehouse,
                Warehouse.id == Till.warehouse_id,
            )
            .filter(
                Till.tenant_id == tenant_id,
                Till.branch_id == branch_id,
                Till.is_active.is_(True),
                Warehouse.tenant_id == tenant_id,
                Warehouse.branch_id == branch_id,
                Warehouse.is_active.is_(True),
            )
            .order_by(
                Till.code.asc(),
                Till.name.asc(),
                Till.created_at.asc(),
            )
            .all()
        )

    def get_current_shift(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        cashier_id: str,
        till_id: str | None = None,
    ) -> TillShift | None:
        self._require_branch(branch_id)

        query = self._open_shift_query(
            tenant_id=tenant_id,
            branch_id=branch_id,
        ).filter(
            TillShift.cashier_id
            == _identifier(
                cashier_id,
                "cashier_id",
            ),
        )

        if till_id:
            self._get_active_till(
                tenant_id=tenant_id,
                branch_id=branch_id,
                till_id=till_id,
            )

            query = query.filter(
                TillShift.till_id
                == _identifier(
                    till_id,
                    "till_id",
                ),
            )

        return (
            query.order_by(
                TillShift.opened_at.desc(),
                TillShift.created_at.desc(),
            )
            .first()
        )

    def open_shift(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        cashier_id: str,
        session_id: str,
        payload: dict,
    ) -> TillShift:
        self._require_branch(branch_id)

        till_id = payload.get("till_id")

        till = self._get_active_till(
            tenant_id=tenant_id,
            branch_id=branch_id,
            till_id=till_id,
        )

        self._require_till_warehouse(
            tenant_id=tenant_id,
            branch_id=branch_id,
            till=till,
        )

        cashier_id = _identifier(
            cashier_id,
            "cashier_id",
        )

        session_id = _identifier(
            session_id,
            "session_id",
        )

        till_id = _identifier(
            till.id,
            "till_id",
        )

        opening_float = _money(
            payload.get("opening_float"),
            "opening_float",
            default=Decimal("0.00"),
        )

        existing_till_shift = (
            self._open_shift_query(
                tenant_id=tenant_id,
                branch_id=branch_id,
            )
            .filter(
                TillShift.till_id == till_id
            )
            .first()
        )

        if existing_till_shift:
            raise ConflictError(
                "This till already has an open shift."
            )

        existing_cashier_shift = (
            self._open_shift_query(
                tenant_id=tenant_id,
                branch_id=branch_id,
            )
            .filter(
                TillShift.cashier_id == cashier_id
            )
            .first()
        )

        if existing_cashier_shift:
            raise ConflictError(
                "This cashier already has an open shift."
            )

        now = _now_utc()

        shift = TillShift(
            tenant_id=_identifier(
                tenant_id,
                "tenant_id",
            ),
            branch_id=_identifier(
                branch_id,
                "branch_id",
            ),
            till_id=till_id,
            cashier_id=cashier_id,
            active_session_id=session_id,
            status="open",
            opening_float=opening_float,
            notes=payload.get("notes"),
            opened_at=now,
            created_at=now,
            updated_at=now,
        )

        self.session.add(shift)
        self.session.commit()

        return shift

    def takeover_shift(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        cashier_id: str,
        session_id: str,
        shift_id: str,
    ) -> TillShift:
        """
        Transfer an existing open till shift to the authenticated session.

        Till takeover is an explicit session-ownership transfer. It does not
        open a new shift and does not change the till assigned to the shift.

        Transactional guarantees
        ------------------------
        - Lock the target TillShift.
        - Validate the requesting UserSession.
        - Revoke the previous owning UserSession.
        - Revoke active refresh tokens belonging to the previous session.
        - Transfer TillShift.active_session_id.
        - Commit all state changes together.

        Repeating takeover from the session that already owns the shift is
        idempotent.
        """

        self._require_branch(branch_id)

        tenant_id = _identifier(
            tenant_id,
            "tenant_id",
        )
        branch_id = _identifier(
            branch_id,
            "branch_id",
        )
        cashier_id = _identifier(
            cashier_id,
            "cashier_id",
        )
        session_id = _identifier(
            session_id,
            "session_id",
        )
        shift_id = _identifier(
            shift_id,
            "shift_id",
        )

        # ------------------------------------------------------------------
        # Lock and validate the cashier's shift.
        # ------------------------------------------------------------------

        shift = (
            self.session.query(TillShift)
            .filter(
                TillShift.id == shift_id,
                TillShift.tenant_id == tenant_id,
                TillShift.branch_id == branch_id,
                TillShift.cashier_id == cashier_id,
            )
            .with_for_update()
            .first()
        )

        if not shift:
            raise NotFoundError(
                "Open till shift not found."
            )

        if (
            shift.status != "open"
            or shift.closed_at is not None
        ):
            raise ConflictError(
                "Till shift is already closed."
            )

        # Ensure the shift's till remains valid before ownership transfer.
        self._get_active_till(
            tenant_id=tenant_id,
            branch_id=branch_id,
            till_id=shift.till_id,
        )

        # ------------------------------------------------------------------
        # Lock and validate the requesting authentication session.
        # ------------------------------------------------------------------

        new_session = (
            self.session.query(UserSession)
            .filter(
                UserSession.id == session_id,
                UserSession.user_id == cashier_id,
                UserSession.tenant_id == tenant_id,
            )
            .with_for_update()
            .first()
        )

        if not new_session:
            raise ConflictError(
                "Authenticated session is not valid for this cashier."
            )

        if not new_session.is_active:
            raise ConflictError(
                "Authenticated session is not active."
            )

        if (
            new_session.branch_id is not None
            and str(new_session.branch_id) != branch_id
        ):
            raise ConflictError(
                "Authenticated session belongs to another branch."
            )

        previous_session_id = (
            str(shift.active_session_id)
            if shift.active_session_id
            else None
        )

        # Already owned by the requesting session: idempotent success.
        if previous_session_id == session_id:
            return shift

        # ------------------------------------------------------------------
        # Retire the previous POS-owning authentication session.
        # ------------------------------------------------------------------

        if previous_session_id:
            previous_session = (
                self.session.query(UserSession)
                .filter(
                    UserSession.id == previous_session_id,
                    UserSession.user_id == cashier_id,
                    UserSession.tenant_id == tenant_id,
                )
                .with_for_update()
                .first()
            )

            if previous_session is not None:
                SessionService().revoke(
                    previous_session,
                    reason=TokenRevocationReason.SESSION_TAKEOVER,
                    revoked_by_user_id=cashier_id,
                    commit=False,
                )

            RefreshTokenService().revoke_session_tokens(
                session_id=previous_session_id,
                reason=TokenRevocationReason.SESSION_TAKEOVER,
                revoked_by_user_id=cashier_id,
                commit=False,
                emit_audit=False,
            )

        # ------------------------------------------------------------------
        # Transfer POS authority.
        # ------------------------------------------------------------------

        shift.active_session_id = session_id
        shift.updated_at = _now_utc()

        self.session.commit()

        return shift

    def close_shift(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        cashier_id: str,
        session_id: str,
        shift_id: str,
        payload: dict,
    ) -> tuple[TillShift, dict[str, Decimal]]:
        self._require_branch(branch_id)

        closing_cash = _money(
            payload.get("closing_cash"),
            "closing_cash",
        )

        shift = (
            self.session.query(TillShift)
            .filter(
                TillShift.id
                == _identifier(
                    shift_id,
                    "shift_id",
                ),
                TillShift.tenant_id
                == _identifier(
                    tenant_id,
                    "tenant_id",
                ),
                TillShift.branch_id
                == _identifier(
                    branch_id,
                    "branch_id",
                ),
                TillShift.cashier_id
                == _identifier(
                    cashier_id,
                    "cashier_id",
                ),
            )
            .first()
        )

        if not shift:
            raise NotFoundError(
                "Open till shift not found."
            )

        if (
            shift.status != "open"
            or shift.closed_at is not None
        ):
            raise ConflictError(
                "Till shift is already closed."
            )

        if not shift_is_owned_by_session(
            shift,
            session_id,
        ):
            raise ConflictError(
                "This till shift is active on another session."
            )

        self._get_active_till(
            tenant_id=tenant_id,
            branch_id=branch_id,
            till_id=shift.till_id,
        )

        closed_at = _now_utc()

        reconciliation = (
            self.calculate_reconciliation(
                shift=shift,
                closed_at=closed_at,
                closing_cash=closing_cash,
            )
        )

        shift.closing_cash = closing_cash
        shift.closed_at = closed_at
        shift.status = "closed"
        shift.active_session_id = None
        shift.notes = payload.get(
            "notes",
            shift.notes,
        )
        shift.updated_at = closed_at

        self.session.commit()

        return shift, reconciliation

    def calculate_reconciliation(
        self,
        *,
        shift: TillShift,
        closed_at: datetime,
        closing_cash: Decimal,
    ) -> dict[str, Decimal]:
        # closed_at is intentionally part of the reconciliation
        # contract even though current calculations aggregate by
        # till_shift_id.
        _ = closed_at

        cash_sales_total = (
            self.session.query(
                func.coalesce(
                    func.sum(SalePayment.amount),
                    0,
                )
            )
            .join(
                Sale,
                SalePayment.sale_id == Sale.id,
            )
            .join(
                PaymentMethod,
                SalePayment.payment_method_id
                == PaymentMethod.id,
            )
            .filter(
                Sale.till_shift_id == shift.id,
                PaymentMethod.tenant_id
                == shift.tenant_id,
                PaymentMethod.method_type
                == "cash",
                SalePayment.amount > 0,
            )
            .scalar()
        )

        cash_refunds_total = (
            self.session.query(
                func.coalesce(
                    func.sum(SalePayment.amount),
                    0,
                )
            )
            .join(
                SaleRefund,
                (
                    SaleRefund.sale_id
                    == SalePayment.sale_id
                )
                & (
                    SaleRefund.refund_number
                    == SalePayment.reference_number
                ),
            )
            .join(
                PaymentMethod,
                SalePayment.payment_method_id
                == PaymentMethod.id,
            )
            .filter(
                SaleRefund.till_shift_id
                == shift.id,
                SaleRefund.tenant_id
                == shift.tenant_id,
                SaleRefund.status == "posted",
                PaymentMethod.tenant_id
                == shift.tenant_id,
                PaymentMethod.method_type
                == "cash",
                SalePayment.amount < 0,
            )
            .scalar()
        )

        cash_sales_total = _money(
            cash_sales_total,
            "cash_sales_total",
            default=Decimal("0.00"),
        )

        cash_refunds_total = _money(
            abs(
                Decimal(
                    str(
                        cash_refunds_total
                        or 0
                    )
                )
            ),
            "cash_refunds_total",
            default=Decimal("0.00"),
        )

        opening_float = _money(
            shift.opening_float,
            "opening_float",
            default=Decimal("0.00"),
        )

        expected_cash = (
            opening_float
            + cash_sales_total
            - cash_refunds_total
        ).quantize(
            TWOPLACES,
            rounding=ROUND_HALF_UP,
        )

        cash_difference = (
            closing_cash - expected_cash
        ).quantize(
            TWOPLACES,
            rounding=ROUND_HALF_UP,
        )

        return {
            "opening_float": opening_float,
            "cash_sales_total": cash_sales_total,
            "cash_refunds_total": cash_refunds_total,
            "expected_cash": expected_cash,
            "closing_cash": closing_cash,
            "cash_difference": cash_difference,
        }

    def _require_branch(
        self,
        branch_id: str | None,
    ) -> None:
        if not branch_id:
            raise ValidationError(
                "Authenticated user is not assigned "
                "to a branch."
            )

    def _get_active_till(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        till_id: str | None,
    ) -> Till:
        till = (
            self.session.query(Till)
            .filter(
                Till.id == till_id,
                Till.tenant_id == tenant_id,
                Till.branch_id == branch_id,
                Till.is_active.is_(True),
            )
            .first()
        )

        if not till:
            raise NotFoundError(
                "Active till not found."
            )

        return till

    def _require_till_warehouse(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        till: Till,
    ) -> Warehouse:
        if not till.warehouse_id:
            raise ValidationError(
                "Till is not configured with a warehouse."
            )

        warehouse = (
            self.session.query(Warehouse)
            .filter(
                Warehouse.id
                == till.warehouse_id,
                Warehouse.tenant_id
                == tenant_id,
                Warehouse.branch_id
                == branch_id,
                Warehouse.is_active.is_(True),
            )
            .first()
        )

        if not warehouse:
            raise ValidationError(
                "Till warehouse is not active "
                "for this branch."
            )

        return warehouse

    def _open_shift_query(
        self,
        *,
        tenant_id: str,
        branch_id: str,
    ):
        return (
            self.session.query(TillShift)
            .filter(
                TillShift.tenant_id
                == _identifier(
                    tenant_id,
                    "tenant_id",
                ),
                TillShift.branch_id
                == _identifier(
                    branch_id,
                    "branch_id",
                ),
                TillShift.status == "open",
                TillShift.closed_at.is_(None),
            )
        )