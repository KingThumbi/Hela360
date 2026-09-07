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
        raise ValidationError(
            f"{field} must be {max_length} characters or fewer."
        )
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
        raise ValidationError(
            f"{field} must be {max_length} characters or fewer."
        )
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
        raise ValidationError(
            f"{field} must be a valid number."
        ) from exc


def _optional_decimal(
    payload: dict[str, Any],
    field: str,
) -> Decimal | None:
    value = payload.get(field)
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValidationError(
            f"{field} must be a valid number."
        ) from exc


def _optional_non_negative_decimal(
    payload: dict[str, Any],
    field: str,
) -> Decimal | None:
    value = _optional_decimal(payload, field)
    if value is not None and value < Decimal("0"):
        raise ValidationError(
            f"{field} must be non-negative."
        )
    return value


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
        raise ValidationError(
            f"{field} must be a datetime string."
        )
    try:
        parsed = datetime.fromisoformat(
            value.strip().replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise ValidationError(
            f"{field} must be a valid ISO datetime."
        ) from exc

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

    # Supplier document quantities.
    invoiced_quantity: Decimal | None = None
    received_quantity: Decimal | None = None
    accepted_quantity: Decimal | None = None
    rejected_quantity: Decimal | None = None
    bonus_quantity: Decimal | None = None

    # Supplier item representation.
    supplier_item_code: str | None = None
    supplier_description: str | None = None

    # Supplier pricing evidence.
    supplier_unit_price: Decimal | None = None
    discount_percent: Decimal | None = None
    discount_amount: Decimal | None = None
    tax_rate: Decimal | None = None
    tax_amount: Decimal | None = None
    net_unit_cost: Decimal | None = None
    line_total: Decimal | None = None

    # Receipt discrepancy evidence.
    discrepancy_status: str | None = None
    discrepancy_reason: str | None = None

    @classmethod
    def from_payload(
        cls,
        payload: dict[str, Any],
        *,
        index: int,
    ) -> "CreateGoodsReceiptItemRequest":
        if not isinstance(payload, dict):
            raise ValidationError(
                f"items[{index}] must be an object."
            )

        quantity = _decimal(payload, "quantity")
        if quantity <= Decimal("0"):
            raise ValidationError(
                "quantity must be greater than zero."
            )

        unit_cost = _decimal(payload, "unit_cost")
        if unit_cost < Decimal("0"):
            raise ValidationError(
                "unit_cost must be non-negative."
            )

        invoiced_quantity = _optional_non_negative_decimal(
            payload,
            "invoiced_quantity",
        )
        received_quantity = _optional_non_negative_decimal(
            payload,
            "received_quantity",
        )
        accepted_quantity = _optional_non_negative_decimal(
            payload,
            "accepted_quantity",
        )
        rejected_quantity = _optional_non_negative_decimal(
            payload,
            "rejected_quantity",
        )
        bonus_quantity = _optional_non_negative_decimal(
            payload,
            "bonus_quantity",
        )

        supplier_unit_price = _optional_non_negative_decimal(
            payload,
            "supplier_unit_price",
        )
        discount_percent = _optional_non_negative_decimal(
            payload,
            "discount_percent",
        )
        discount_amount = _optional_non_negative_decimal(
            payload,
            "discount_amount",
        )
        tax_rate = _optional_non_negative_decimal(
            payload,
            "tax_rate",
        )
        tax_amount = _optional_non_negative_decimal(
            payload,
            "tax_amount",
        )
        net_unit_cost = _optional_non_negative_decimal(
            payload,
            "net_unit_cost",
        )
        line_total = _optional_non_negative_decimal(
            payload,
            "line_total",
        )

        if (
            discount_percent is not None
            and discount_percent > Decimal("100")
        ):
            raise ValidationError(
                "discount_percent must not exceed 100."
            )

        if tax_rate is not None and tax_rate > Decimal("100"):
            raise ValidationError(
                "tax_rate must not exceed 100."
            )

        return cls(
            product_id=_required_text(
                payload,
                "product_id",
                max_length=36,
            ),
            quantity=quantity,
            product_unit_id=_optional_text(
                payload,
                "product_unit_id",
                max_length=36,
            ),
            batch_number=_optional_text(
                payload,
                "batch_number",
                max_length=100,
            ),
            manufacture_date=_optional_date(
                payload,
                "manufacture_date",
            ),
            expiry_date=_optional_date(
                payload,
                "expiry_date",
            ),
            unit_cost=unit_cost,
            supplier_batch_reference=_optional_text(
                payload,
                "supplier_batch_reference",
                max_length=120,
            ),

            invoiced_quantity=invoiced_quantity,
            received_quantity=received_quantity,
            accepted_quantity=accepted_quantity,
            rejected_quantity=rejected_quantity,
            bonus_quantity=bonus_quantity,

            supplier_item_code=_optional_text(
                payload,
                "supplier_item_code",
                max_length=120,
            ),
            supplier_description=_optional_text(
                payload,
                "supplier_description",
                max_length=500,
            ),

            supplier_unit_price=supplier_unit_price,
            discount_percent=discount_percent,
            discount_amount=discount_amount,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            net_unit_cost=net_unit_cost,
            line_total=line_total,

            discrepancy_status=_optional_text(
                payload,
                "discrepancy_status",
                max_length=30,
            ),
            discrepancy_reason=_optional_text(
                payload,
                "discrepancy_reason",
                max_length=500,
            ),
        )


@dataclass(frozen=True, slots=True)
class CreateGoodsReceiptRequest:
    warehouse_id: str
    idempotency_key: str
    items: tuple[CreateGoodsReceiptItemRequest, ...]

    supplier_id: str | None = None
    supplier_reference: str | None = None

    supplier_invoice_number: str | None = None
    supplier_invoice_date: date | None = None
    payment_terms: str | None = None
    invoice_currency: str = "KES"

    supplier_subtotal: Decimal | None = None
    supplier_discount_total: Decimal | None = None
    supplier_tax_total: Decimal | None = None
    supplier_invoice_total: Decimal | None = None

    received_at: datetime | None = None
    notes: str | None = None

    @classmethod
    def from_payload(
        cls,
        payload: dict[str, Any],
    ) -> "CreateGoodsReceiptRequest":
        if not isinstance(payload, dict):
            raise ValidationError(
                "Request payload must be an object."
            )

        raw_items = payload.get("items")
        if not isinstance(raw_items, list) or not raw_items:
            raise ValidationError(
                "items must contain at least one receipt line."
            )

        items = tuple(
            CreateGoodsReceiptItemRequest.from_payload(
                item,
                index=index,
            )
            for index, item in enumerate(raw_items)
        )

        invoice_currency = (
            _optional_text(
                payload,
                "invoice_currency",
                max_length=3,
            )
            or "KES"
        ).upper()

        if len(invoice_currency) != 3:
            raise ValidationError(
                "invoice_currency must be a 3-letter currency code."
            )

        return cls(
            warehouse_id=_required_text(
                payload,
                "warehouse_id",
                max_length=36,
            ),
            idempotency_key=_required_text(
                payload,
                "idempotency_key",
                max_length=120,
            ),
            supplier_id=_optional_text(
                payload,
                "supplier_id",
                max_length=36,
            ),
            supplier_reference=_optional_text(
                payload,
                "supplier_reference",
                max_length=120,
            ),

            supplier_invoice_number=_optional_text(
                payload,
                "supplier_invoice_number",
                max_length=120,
            ),
            supplier_invoice_date=_optional_date(
                payload,
                "supplier_invoice_date",
            ),
            payment_terms=_optional_text(
                payload,
                "payment_terms",
                max_length=120,
            ),
            invoice_currency=invoice_currency,

            supplier_subtotal=_optional_non_negative_decimal(
                payload,
                "supplier_subtotal",
            ),
            supplier_discount_total=_optional_non_negative_decimal(
                payload,
                "supplier_discount_total",
            ),
            supplier_tax_total=_optional_non_negative_decimal(
                payload,
                "supplier_tax_total",
            ),
            supplier_invoice_total=_optional_non_negative_decimal(
                payload,
                "supplier_invoice_total",
            ),

            received_at=_optional_datetime(
                payload,
                "received_at",
            ),
            notes=_optional_text(
                payload,
                "notes",
                max_length=10000,
            ),
            items=items,
        )


@dataclass(frozen=True, slots=True)
class CreateGoodsReceiptDraftRequest:
    warehouse_id: str
    idempotency_key: str

    supplier_id: str | None = None
    supplier_reference: str | None = None

    supplier_invoice_number: str | None = None
    supplier_invoice_date: date | None = None
    payment_terms: str | None = None
    invoice_currency: str = "KES"

    supplier_subtotal: Decimal | None = None
    supplier_discount_total: Decimal | None = None
    supplier_tax_total: Decimal | None = None
    supplier_invoice_total: Decimal | None = None

    notes: str | None = None

    @classmethod
    def from_payload(
        cls,
        payload: dict[str, Any],
    ) -> "CreateGoodsReceiptDraftRequest":
        if not isinstance(payload, dict):
            raise ValidationError(
                "Request payload must be an object."
            )

        warehouse_id = _required_text(
            payload,
            "warehouse_id",
            max_length=36,
        )

        idempotency_key = _required_text(
            payload,
            "idempotency_key",
            max_length=120,
        )

        invoice_currency = (
            _optional_text(
                payload,
                "invoice_currency",
                max_length=3,
            )
            or "KES"
        ).upper()

        supplier_subtotal = _optional_decimal(
            payload,
            "supplier_subtotal",
        )
        supplier_discount_total = _optional_decimal(
            payload,
            "supplier_discount_total",
        )
        supplier_tax_total = _optional_decimal(
            payload,
            "supplier_tax_total",
        )
        supplier_invoice_total = _optional_decimal(
            payload,
            "supplier_invoice_total",
        )

        for field_name, value in (
            ("supplier_subtotal", supplier_subtotal),
            ("supplier_discount_total", supplier_discount_total),
            ("supplier_tax_total", supplier_tax_total),
            ("supplier_invoice_total", supplier_invoice_total),
        ):
            if value is not None and value < 0:
                raise ValidationError(
                    f"{field_name} must be greater than or equal to zero."
                )

        return cls(
            warehouse_id=warehouse_id,
            idempotency_key=idempotency_key,
            supplier_id=_optional_text(
                payload,
                "supplier_id",
                max_length=36,
            ),
            supplier_reference=_optional_text(
                payload,
                "supplier_reference",
                max_length=120,
            ),
            supplier_invoice_number=_optional_text(
                payload,
                "supplier_invoice_number",
                max_length=120,
            ),
            supplier_invoice_date=_optional_date(
                payload,
                "supplier_invoice_date",
            ),
            payment_terms=_optional_text(
                payload,
                "payment_terms",
                max_length=120,
            ),
            invoice_currency=invoice_currency,
            supplier_subtotal=supplier_subtotal,
            supplier_discount_total=supplier_discount_total,
            supplier_tax_total=supplier_tax_total,
            supplier_invoice_total=supplier_invoice_total,
            notes=_optional_text(
                payload,
                "notes",
                max_length=5000,
            ),
        )
