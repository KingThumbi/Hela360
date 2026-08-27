from __future__ import annotations

from dataclasses import dataclass
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


def _product_ids(payload: dict[str, Any]) -> tuple[str, ...]:
    raw = payload.get("product_ids")
    if raw in (None, ""):
        return ()
    if not isinstance(raw, list):
        raise ValidationError("product_ids must be a list.")

    normalized: list[str] = []
    seen: set[str] = set()
    for index, value in enumerate(raw):
        if not isinstance(value, str):
            raise ValidationError(f"product_ids[{index}] must be a string.")
        product_id = value.strip()
        if not product_id:
            raise ValidationError(f"product_ids[{index}] is required.")
        if len(product_id) > 36:
            raise ValidationError(f"product_ids[{index}] must be 36 characters or fewer.")
        if product_id not in seen:
            normalized.append(product_id)
            seen.add(product_id)
    return tuple(normalized)


@dataclass(frozen=True, slots=True)
class CreateStockCountRequest:
    warehouse_id: str
    idempotency_key: str
    product_ids: tuple[str, ...] = ()
    notes: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "CreateStockCountRequest":
        if not isinstance(payload, dict):
            raise ValidationError("Request payload must be an object.")

        return cls(
            warehouse_id=_required_text(payload, "warehouse_id", max_length=36),
            idempotency_key=_required_text(
                payload,
                "idempotency_key",
                max_length=120,
            ),
            product_ids=_product_ids(payload),
            notes=_optional_text(payload, "notes", max_length=10000),
        )


@dataclass(frozen=True, slots=True)
class UpdateStockCountItemRequest:
    counted_quantity: Decimal
    notes: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "UpdateStockCountItemRequest":
        if not isinstance(payload, dict):
            raise ValidationError("Request payload must be an object.")

        counted_quantity = _decimal(payload, "counted_quantity")
        if counted_quantity < Decimal("0"):
            raise ValidationError("counted_quantity must be non-negative.")

        return cls(
            counted_quantity=counted_quantity,
            notes=_optional_text(payload, "notes", max_length=10000),
        )
