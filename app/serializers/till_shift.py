from decimal import Decimal

from app.models import TillShift


def _decimal_to_string(
    value,
    default: str = "0.00",
) -> str:
    if value is None:
        return default

    return str(value)


def serialize_till_shift(
    till_shift: TillShift,
    *,
    current_session_id: str | None = None,
) -> dict:
    """
    Serialize a till shift for API transport.

    ``owned_by_current_session`` is derived from authenticated request
    context supplied by the caller. The underlying ``active_session_id``
    remains an internal backend authority field and is intentionally not
    exposed through the API contract.
    """
    return {
        "owned_by_current_session": (
            current_session_id is not None
            and till_shift.active_session_id is not None
            and str(till_shift.active_session_id)
            == str(current_session_id)
        ),
        "id": str(till_shift.id),
        "branch_id": str(till_shift.branch_id),
        "till_id": str(till_shift.till_id),
        "cashier_id": str(till_shift.cashier_id),
        "status": till_shift.status,
        "opening_float": _decimal_to_string(
            till_shift.opening_float,
        ),
        "closing_cash": _decimal_to_string(
            till_shift.closing_cash,
        ),
        "notes": till_shift.notes,
        "opened_at": (
            till_shift.opened_at.isoformat()
            if till_shift.opened_at
            else None
        ),
        "closed_at": (
            till_shift.closed_at.isoformat()
            if till_shift.closed_at
            else None
        ),
        "created_at": (
            till_shift.created_at.isoformat()
            if till_shift.created_at
            else None
        ),
        "updated_at": (
            till_shift.updated_at.isoformat()
            if till_shift.updated_at
            else None
        ),
    }


def serialize_till_shift_reconciliation(
    *,
    opening_float: Decimal,
    cash_sales_total: Decimal,
    expected_cash: Decimal,
    closing_cash: Decimal,
    cash_difference: Decimal,
    cash_refunds_total: Decimal = Decimal("0.00"),
) -> dict:
    return {
        "opening_float": _decimal_to_string(opening_float),
        "cash_sales_total": _decimal_to_string(cash_sales_total),
        "cash_refunds_total": _decimal_to_string(cash_refunds_total),
        "expected_cash": _decimal_to_string(expected_cash),
        "closing_cash": _decimal_to_string(closing_cash),
        "cash_difference": _decimal_to_string(cash_difference),
    }
