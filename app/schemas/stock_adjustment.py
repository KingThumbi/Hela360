from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from app.errors import ValidationError


REASON_CODES = {
    "stock_count",
    "damage",
    "expiry",
    "breakage",
    "correction",
    "opening_balance",
    "other",
}


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


def _reason_code(payload: dict[str, Any], default: str) -> str:
    code = payload.get("reason_code")
    if code in (None, ""):
        return default
    if not isinstance(code, str):
        raise ValidationError("reason_code must be a string.")
    normalized = code.strip()
    if normalized not in REASON_CODES:
        raise ValidationError("reason_code is not supported.")
    return normalized


@dataclass(frozen=True, slots=True)
class CreateStockAdjustmentItemRequest:
    product_id: str
    quantity_delta: Decimal
    batch_id: str | None = None
    reason: str | None = None

    @classmethod
    def from_payload(
        cls,
        payload: dict[str, Any],
        *,
        index: int,
    ) -> "CreateStockAdjustmentItemRequest":
        if not isinstance(payload, dict):
            raise ValidationError(f"items[{index}] must be an object.")

        quantity_delta = _decimal(payload, "quantity_delta")
        if quantity_delta == Decimal("0"):
            raise ValidationError("quantity_delta must not be zero.")

        return cls(
            product_id=_required_text(payload, "product_id", max_length=36),
            batch_id=_optional_text(payload, "batch_id", max_length=36),
            quantity_delta=quantity_delta,
            reason=_optional_text(payload, "reason", max_length=255),
        )


@dataclass(frozen=True, slots=True)
class CreateStockAdjustmentRequest:
    warehouse_id: str
    idempotency_key: str
    reason_code: str
    items: tuple[CreateStockAdjustmentItemRequest, ...]
    reason: str | None = None
    notes: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "CreateStockAdjustmentRequest":
        if not isinstance(payload, dict):
            raise ValidationError("Request payload must be an object.")

        raw_items = payload.get("items")
        if not isinstance(raw_items, list) or not raw_items:
            raise ValidationError("items must contain at least one adjustment line.")

        items = tuple(
            CreateStockAdjustmentItemRequest.from_payload(item, index=index)
            for index, item in enumerate(raw_items)
        )

        return cls(
            warehouse_id=_required_text(payload, "warehouse_id", max_length=36),
            idempotency_key=_required_text(
                payload,
                "idempotency_key",
                max_length=120,
            ),
            reason_code=_reason_code(payload, "correction"),
            reason=_optional_text(payload, "reason", max_length=255),
            notes=_optional_text(payload, "notes", max_length=10000),
            items=items,
        )


@dataclass(frozen=True, slots=True)
class CreateStockAdjustmentFromCountRequest:
    idempotency_key: str
    reason_code: str = "stock_count"
    reason: str | None = None
    notes: str | None = None

    @classmethod
    def from_payload(
        cls,
        payload: dict[str, Any],
    ) -> "CreateStockAdjustmentFromCountRequest":
        if not isinstance(payload, dict):
            raise ValidationError("Request payload must be an object.")

        reason_code = _reason_code(payload, "stock_count")
        if reason_code != "stock_count":
            raise ValidationError("Stock Count adjustments must use reason_code stock_count.")

        return cls(
            idempotency_key=_required_text(
                payload,
                "idempotency_key",
                max_length=120,
            ),
            reason_code=reason_code,
            reason=_optional_text(payload, "reason", max_length=255),
            notes=_optional_text(payload, "notes", max_length=10000),
        )
