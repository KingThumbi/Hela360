"""
Hela360 Tenant Dashboard Query Service
======================================

Builds the tenant administrator's operational dashboard read projection.

Architectural Responsibilities
------------------------------
- Aggregate authoritative operational data for the authenticated tenant.
- Preserve authenticated branch scope.
- Provide management-oriented sales and inventory summaries.
- Keep dashboard aggregation out of Flask routes.
- Keep presentation concerns out of backend domain queries.
- Preserve exact monetary values across the API boundary.

Security Boundary
-----------------
Tenant and branch scope MUST originate from authenticated backend context.

This service does not authorize requests by itself. HTTP entry points remain
responsible for authentication and RBAC enforcement before invoking it.

The dashboard is a read projection only. It MUST NOT become the source of
truth for sales, inventory, payments, refunds, procurement, finance or other
Hela360 domains.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import func

from app.models import PaymentMethod, Tenant
from app.models.pos import Sale, SalePayment, SaleRefund
from app.models.inventory import Warehouse
from app.services.tenant.inventory import (
    InventoryListFilters,
    InventoryQueryService,
)


ZERO = Decimal("0.00")


class DashboardQueryError(ValueError):
    """Raised when a dashboard projection cannot be produced safely."""


@dataclass(frozen=True)
class DashboardPeriod:
    """
    Inclusive/exclusive reporting period.

    start <= timestamp < end
    """

    start: datetime
    end: datetime


def _money(value: Any) -> str:
    """
    Serialize monetary values without converting through float.
    """

    if value is None:
        value = ZERO

    if not isinstance(value, Decimal):
        value = Decimal(str(value))

    return str(value.quantize(Decimal("0.01")))


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _resolve_timezone(
    timezone_name: str,
) -> ZoneInfo:
    """
    Resolve a configured IANA tenant timezone.

    Dashboard reporting MUST fail explicitly when tenant timezone
    configuration is invalid rather than silently falling back to the
    application server timezone.
    """

    try:
        return ZoneInfo(timezone_name)
    except (
        ZoneInfoNotFoundError,
        ValueError,
        TypeError,
    ) as exc:
        raise DashboardQueryError(
            f"Invalid tenant timezone: {timezone_name!r}."
        ) from exc


def _day_period(
    value: date,
    tenant_timezone: ZoneInfo,
) -> DashboardPeriod:
    """
    Construct one tenant-local calendar day as UTC query boundaries.

    Persisted operational timestamps are timezone-aware. Reporting periods
    originate in the tenant's configured business timezone and are converted
    to UTC before querying persisted transactions.
    """

    local_start = datetime.combine(
        value,
        time.min,
        tzinfo=tenant_timezone,
    )

    local_end = datetime.combine(
        value + timedelta(days=1),
        time.min,
        tzinfo=tenant_timezone,
    )

    return DashboardPeriod(
        start=local_start.astimezone(timezone.utc),
        end=local_end.astimezone(timezone.utc),
    )


class DashboardQueryService:
    """
    Tenant dashboard read-projection service.
    """

    def __init__(self, session):
        self.session = session

    def overview(
        self,
        *,
        tenant_id: str,
        branch_id: str | None,
        operational_date: date | None = None,
    ) -> dict:
        """
        Build the initial tenant-administrator dashboard projection.

        Dashboard v1 intentionally focuses on operational information already
        backed by authoritative Hela360 transactional data:

        - today's sales
        - month-to-date sales
        - today's payment mix
        - inventory health
        - recent sales

        Finance, procurement, profitability and richer analytics are additive
        future dashboard capabilities.
        """

        if not tenant_id:
            raise DashboardQueryError(
                "Authenticated tenant is unavailable."
            )

        if not branch_id:
            raise DashboardQueryError(
                "Authenticated user is not assigned to a branch."
            )

        tenant = (
            self.session.query(Tenant)
            .filter(
                Tenant.id == tenant_id,
            )
            .one_or_none()
        )

        if tenant is None:
            raise DashboardQueryError(
                "Authenticated tenant does not exist."
            )

        tenant_timezone = _resolve_timezone(
            tenant.timezone
        )

        today = (
            operational_date
            if operational_date is not None
            else _utc_now()
            .astimezone(tenant_timezone)
            .date()
        )

        today_period = _day_period(
            today,
            tenant_timezone,
        )

        month_start_period = _day_period(
            today.replace(day=1),
            tenant_timezone,
        )

        month_period = DashboardPeriod(
            start=month_start_period.start,
            end=today_period.end,
        )

        return {
            "scope": {
                "tenant_id": str(tenant_id),
                "branch_id": str(branch_id),
                "generated_at": _utc_now().isoformat(),
                "operational_date": today.isoformat(),
                "timezone": tenant.timezone,
                "currency": tenant.base_currency,
            },
            "sales": {
                "today": self._sales_summary(
                    tenant_id=tenant_id,
                    branch_id=branch_id,
                    period=today_period,
                ),
                "month_to_date": self._sales_summary(
                    tenant_id=tenant_id,
                    branch_id=branch_id,
                    period=month_period,
                ),
            },
            "payments": {
                "today": self._payment_mix(
                    tenant_id=tenant_id,
                    branch_id=branch_id,
                    period=today_period,
                ),
            },
            "inventory": self._inventory_health(
                tenant_id=tenant_id,
                branch_id=branch_id,
                operational_date=today,
            ),
            "recent_sales": self._recent_sales(
                tenant_id=tenant_id,
                branch_id=branch_id,
                limit=5,
            ),
            "alerts": [],
        }

    def _base_sales_query(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        period: DashboardPeriod | None = None,
    ):
        query = self.session.query(Sale).filter(
            Sale.tenant_id == tenant_id,
            Sale.branch_id == branch_id,
        )

        if period is not None:
            query = query.filter(
                Sale.sale_date >= period.start,
                Sale.sale_date < period.end,
            )

        return query

    def _sales_summary(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        period: DashboardPeriod,
    ) -> dict:
        """
        Aggregate persisted sale totals for one reporting period.

        `gross_sales` currently represents the sum of persisted Sale totals.
        Refunds are reported independently and deducted to derive net sales.

        This intentionally avoids deriving management totals in the frontend.
        """

        aggregate = (
            self._base_sales_query(
                tenant_id=tenant_id,
                branch_id=branch_id,
                period=period,
            )
            .with_entities(
                func.count(Sale.id),
                func.coalesce(func.sum(Sale.total_amount), 0),
                func.coalesce(func.sum(Sale.discount_amount), 0),
                func.coalesce(func.sum(Sale.paid_amount), 0),
                func.coalesce(func.sum(Sale.balance_due), 0),
            )
            .first()
        )

        transaction_count = int(aggregate[0] or 0)
        gross_sales = Decimal(str(aggregate[1] or 0))
        discounts = Decimal(str(aggregate[2] or 0))
        paid_amount = Decimal(str(aggregate[3] or 0))
        balance_due = Decimal(str(aggregate[4] or 0))

        refunds = self._refund_total(
            tenant_id=tenant_id,
            branch_id=branch_id,
            period=period,
        )

        net_sales = gross_sales - refunds

        average_basket = (
            gross_sales / transaction_count
            if transaction_count
            else ZERO
        )

        return {
            "gross_sales": _money(gross_sales),
            "discounts": _money(discounts),
            "refunds": _money(refunds),
            "net_sales": _money(net_sales),
            "transactions": transaction_count,
            "average_basket": _money(average_basket),
            "paid_amount": _money(paid_amount),
            "balance_due": _money(balance_due),
        }

    def _refund_total(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        period: DashboardPeriod,
    ) -> Decimal:
        """
        Aggregate persisted refund totals for the reporting period.

        Refund status semantics will remain explicit here as the refund
        workflow evolves.
        """

        value = (
            self.session.query(
                func.coalesce(
                    func.sum(SaleRefund.refund_total_amount),
                    0,
                )
            )
            .filter(
                SaleRefund.tenant_id == tenant_id,
                SaleRefund.branch_id == branch_id,
                SaleRefund.status == "posted",
                SaleRefund.created_at >= period.start,
                SaleRefund.created_at < period.end,
            )
            .scalar()
        )

        return Decimal(str(value or 0))

    def _payment_mix(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        period: DashboardPeriod,
    ) -> list[dict]:
        """
        Aggregate payment amounts by persisted payment method.
        """

        rows = (
            self.session.query(
                SalePayment.payment_method_id,
                PaymentMethod.code,
                PaymentMethod.name,
                PaymentMethod.method_type,
                func.coalesce(
                    func.sum(SalePayment.amount),
                    0,
                ).label("amount"),
                func.count(SalePayment.id).label(
                    "transaction_count"
                ),
            )
            .join(
                Sale,
                Sale.id == SalePayment.sale_id,
            )
            .join(
                PaymentMethod,
                PaymentMethod.id
                == SalePayment.payment_method_id,
            )
            .filter(
                Sale.tenant_id == tenant_id,
                Sale.branch_id == branch_id,
                SalePayment.paid_at >= period.start,
                SalePayment.paid_at < period.end,
            )
            .group_by(
                SalePayment.payment_method_id,
                PaymentMethod.code,
                PaymentMethod.name,
                PaymentMethod.method_type,
            )
            .order_by(
                func.sum(SalePayment.amount).desc()
            )
            .all()
        )

        return [
            {
                "payment_method_id": (
                    str(row.payment_method_id)
                    if row.payment_method_id
                    else None
                ),
                "code": row.code,
                "name": row.name,
                "method_type": row.method_type,
                "amount": _money(row.amount),
                "transaction_count": int(
                    row.transaction_count or 0
                ),
            }
            for row in rows
        ]

    def _inventory_health(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        operational_date: date,
    ) -> dict:
        """
        Aggregate inventory health using InventoryQueryService's canonical
        stock projection.

        This deliberately reuses existing low-stock, out-of-stock, expiry and
        sellability semantics rather than defining dashboard-specific rules.

        The current implementation uses the public inventory read service.
        A future optimized aggregate inventory query may replace this internal
        implementation without changing the dashboard response contract.
        """

        filters = InventoryListFilters(
            page=1,
            per_page=100000,
            search=None,
            warehouse_id=None,
            stock_status=None,
            expires_before=operational_date + timedelta(days=90),
        )

        items, pagination = InventoryQueryService(
            self.session
        ).list_stock(
            tenant_id=tenant_id,
            branch_id=branch_id,
            filters=filters,
            operational_date=operational_date,
        )

        return {
            "stock_records": int(
                pagination.get("total", len(items))
            ),
            "low_stock": sum(
                1 for item in items
                if item.get("is_low_stock")
            ),
            "out_of_stock": sum(
                1 for item in items
                if item.get("is_out_of_stock")
            ),
            "expiring_soon": sum(
                1 for item in items
                if item.get("has_expiring_stock")
            ),
            "expired": sum(
                1 for item in items
                if item.get("has_expired_stock")
            ),
        }

    def _recent_sales(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        limit: int,
    ) -> list[dict]:
        sales = (
            self._base_sales_query(
                tenant_id=tenant_id,
                branch_id=branch_id,
            )
            .order_by(
                Sale.sale_date.desc(),
                Sale.id.desc(),
            )
            .limit(limit)
            .all()
        )

        return [
            {
                "id": str(sale.id),
                "sale_number": sale.sale_number,
                "sale_date": (
                    sale.sale_date.isoformat()
                    if sale.sale_date
                    else None
                ),
                "status": sale.status,
                "total_amount": _money(
                    sale.total_amount
                ),
                "paid_amount": _money(
                    sale.paid_amount
                ),
                "balance_due": _money(
                    sale.balance_due
                ),
            }
            for sale in sales
        ]
