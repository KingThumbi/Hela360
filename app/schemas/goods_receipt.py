from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from app.errors import ValidationError


def _required_text(
    payload: dict[str, Any],
    field: str,
    *,
    max_length: int,
) -> str:
    value = payload.get(field)
    if value in (None, ""):
        raise ValidationError(f"{field} is required.")
    if not isinstance(value, str):
        raise ValidationError(f"{field} must be a string.")
    text = value.strip()
    if not text:
        raise ValidationError(f"{field} is required.")
    if len(text) > max_length:
        raise ValidationError(f"{field} must be {max_length} characters or fewer.")
    return text


def _optional_text(
    payload: dict[str, Any],
    field: str,
    *,
    max_length: int,
) -> str | None:
    value = payload.get(field)
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise ValidationError(f"{field} must be a string.")
    text = value.strip()
    if not text:
        return None
    if len(text) > max_length:
        raise ValidationError(f"{field} must be {max_length} characters or fewer.")
    return text


def _decimal(
    payload: dict[str, Any],
    field: str,
) -> Decimal:
    value = payload.get(field)
    if value in (None, ""):
        raise ValidationError(f"{field} is required.")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValidationError(f"{field} must be a valid number.") from exc


def _optional_date(
    payload: dict[str, Any],
    field: str,
) -> date | None:
    value = payload.get(field)
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise ValidationError(f"{field} must be a date string.")
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise ValidationError(
            f"{field} must be a valid date in YYYY-MM-DD format."
        ) from exc


def _optional_datetime(
    payload: dict[str, Any],
    field: str,
) -> datetime | None:
    value = payload.get(field)
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise ValidationError(f"{field} must be a datetime string.")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"{field} must be a valid ISO datetime.") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


@dataclass(frozen=True, slots=True)
class CreateGoodsReceiptItemRequest:
    product_id: str
    quantity: Decimal
    product_unit_id: str | None = None
    batch_number: str | None = None
    manufacture_date: date | None = None
    expiry_date: date | None = None
    unit_cost: Decimal = Decimal("0")
    supplier_batch_reference: str | None = None

    @classmethod
    def from_payload(
        cls,
        payload: dict[str, Any],
        *,
        index: int,
    ) -> "CreateGoodsReceiptItemRequest":
        if not isinstance(payload, dict):
            raise ValidationError(f"items[{index}] must be an object.")

        quantity = _decimal(payload, "quantity")
        if quantity <= Decimal("0"):
            raise ValidationError("quantity must be greater than zero.")

        unit_cost = _decimal(payload, "unit_cost")
        if unit_cost < Decimal("0"):
            raise ValidationError("unit_cost must be non-negative.")

        return cls(
            product_id=_required_text(payload, "product_id", max_length=36),
            quantity=quantity,
            product_unit_id=_optional_text(payload, "product_unit_id", max_length=36),
            batch_number=_optional_text(payload, "batch_number", max_length=100),
            manufacture_date=_optional_date(payload, "manufacture_date"),
            expiry_date=_optional_date(payload, "expiry_date"),
            unit_cost=unit_cost,
            supplier_batch_reference=_optional_text(
                payload,
                "supplier_batch_reference",
                max_length=120,
            ),
        )


@dataclass(frozen=True, slots=True)
class CreateGoodsReceiptRequest:
    warehouse_id: str
    idempotency_key: str
    items: tuple[CreateGoodsReceiptItemRequest, ...]
    supplier_id: str | None = None
    supplier_reference: str | None = None
    received_at: datetime | None = None
    notes: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "CreateGoodsReceiptRequest":
        if not isinstance(payload, dict):
            raise ValidationError("Request payload must be an object.")

        raw_items = payload.get("items")
        if not isinstance(raw_items, list) or not raw_items:
            raise ValidationError("items must contain at least one receipt line.")

        items = tuple(
            CreateGoodsReceiptItemRequest.from_payload(item, index=index)
            for index, item in enumerate(raw_items)
        )

        return cls(
            warehouse_id=_required_text(payload, "warehouse_id", max_length=36),
            idempotency_key=_required_text(
                payload,
                "idempotency_key",
                max_length=120,
            ),
            supplier_id=_optional_text(payload, "supplier_id", max_length=36),
            supplier_reference=_optional_text(
                payload,
                "supplier_reference",
                max_length=120,
            ),
            received_at=_optional_datetime(payload, "received_at"),
            notes=_optional_text(payload, "notes", max_length=10000),
            items=items,
        )
