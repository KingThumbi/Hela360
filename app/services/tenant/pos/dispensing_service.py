from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal

from app.models import Customer, DispensingRecord, Product, SaleItem


class DispensingError(ValueError):
    pass


@dataclass(frozen=True)
class DispensingContext:
    prescription_reference: str | None
    prescriber_name: str
    prescriber_registration_number: str | None
    prescription_date: date | None
    notes: str | None


def _text(value, *, max_length: int, field_name: str, required: bool = False) -> str | None:
    if value is None:
        if required:
            raise DispensingError(f"{field_name} is required.")
        return None

    text = str(value).strip()
    if not text:
        if required:
            raise DispensingError(f"{field_name} is required.")
        return None

    if len(text) > max_length:
        raise DispensingError(
            f"{field_name} cannot exceed {max_length} characters."
        )

    return text


def _date(value) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    try:
        return date.fromisoformat(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise DispensingError(
            "prescription.prescription_date must be a valid date in YYYY-MM-DD format."
        ) from exc


class DispensingService:
    def __init__(self, session):
        self.session = session

    def context_from_payload(self, payload: dict | None) -> DispensingContext:
        if not isinstance(payload, dict):
            raise DispensingError("prescription is required for prescription products.")

        return DispensingContext(
            prescription_reference=_text(
                payload.get("prescription_reference")
                or payload.get("reference"),
                max_length=100,
                field_name="prescription.prescription_reference",
            ),
            prescriber_name=_text(
                payload.get("prescriber_name"),
                max_length=150,
                field_name="prescription.prescriber_name",
                required=True,
            )
            or "",
            prescriber_registration_number=_text(
                payload.get("prescriber_registration_number"),
                max_length=100,
                field_name="prescription.prescriber_registration_number",
            ),
            prescription_date=_date(payload.get("prescription_date")),
            notes=_text(
                payload.get("notes"),
                max_length=1000,
                field_name="prescription.notes",
            ),
        )

    def require_context_for_product(
        self,
        *,
        product: Product,
        customer: Customer | None,
        item_payload: dict,
    ) -> DispensingContext | None:
        if not bool(getattr(product, "requires_prescription", False)):
            return None

        if customer is None:
            raise DispensingError(
                "customer_id is required when a sale contains prescription products."
            )

        return self.context_from_payload(item_payload.get("prescription"))

    def build_record(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        customer: Customer,
        sale_id: str,
        sale_item: SaleItem,
        product: Product,
        context: DispensingContext,
        dispensed_by: str,
        dispensed_at: datetime | None = None,
    ) -> DispensingRecord:
        quantity = Decimal(str(sale_item.quantity))
        if quantity <= Decimal("0"):
            raise DispensingError("dispensed_quantity must be greater than zero.")

        if str(customer.tenant_id) != str(tenant_id):
            raise DispensingError("Customer is not valid for this tenant.")

        if str(product.tenant_id) != str(tenant_id):
            raise DispensingError("Product is not valid for this tenant.")

        if str(sale_item.product_id) != str(product.id):
            raise DispensingError("Sale item product does not match dispensing product.")

        now = dispensed_at or datetime.now(timezone.utc)

        return DispensingRecord(
            tenant_id=tenant_id,
            branch_id=branch_id,
            customer_id=str(customer.id),
            sale_id=sale_id,
            sale_item_id=str(sale_item.id),
            product_id=str(product.id),
            dispensed_quantity=quantity,
            prescription_reference=context.prescription_reference,
            prescriber_name=context.prescriber_name,
            prescriber_registration_number=context.prescriber_registration_number,
            prescription_date=context.prescription_date,
            notes=context.notes,
            dispensed_by=dispensed_by,
            dispensed_at=now,
            created_at=now,
            updated_at=now,
        )
