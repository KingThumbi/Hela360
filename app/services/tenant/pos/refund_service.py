from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.pos import Sale, SaleItem, SalePayment, SaleRefund, SaleRefundItem
from app.models.inventory import InventoryMovement


TWOPLACES = Decimal("0.01")
FOURPLACES = Decimal("0.0001")


def utcnow():
    return datetime.now(timezone.utc)


def d(value) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def q2(value) -> Decimal:
    return d(value).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def q4(value) -> Decimal:
    return d(value).quantize(FOURPLACES, rounding=ROUND_HALF_UP)


def prorate(amount: Decimal, qty: Decimal, original_qty: Decimal) -> Decimal:
    if original_qty <= 0:
        return Decimal("0.00")
    return q2((d(amount) * d(qty)) / d(original_qty))


class RefundError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class RefundService:
    def __init__(self, session):
        self.session = session

    def create_refund(self, tenant_id: str, sale_id: str, payload: dict) -> SaleRefund:
        now = utcnow()
        items_payload = payload.get("items") or []
        reason = (payload.get("reason") or "").strip() or None
        notes = (payload.get("notes") or "").strip() or None

        if not items_payload:
            raise RefundError("At least one refund item is required.", 400)

        sale = (
            self.session.query(Sale)
            .filter(Sale.id == sale_id, Sale.tenant_id == tenant_id)
            .with_for_update()
            .first()
        )
        if not sale:
            raise RefundError("Sale not found.", 404)

        if (sale.status or "").lower() == "voided":
            raise RefundError("Voided sales cannot be refunded.", 409)

        sale_items = (
            self.session.query(SaleItem)
            .filter(SaleItem.sale_id == sale.id)
            .with_for_update()
            .all()
        )
        if not sale_items:
            raise RefundError("Sale has no items.", 400)

        sale_item_map = {item.id: item for item in sale_items}

        already_refunded_rows = (
            self.session.query(
                SaleRefundItem.sale_item_id,
                func.coalesce(func.sum(SaleRefundItem.quantity), 0),
            )
            .join(SaleRefund, SaleRefund.id == SaleRefundItem.refund_id)
            .filter(
                SaleRefund.sale_id == sale.id,
                SaleRefund.tenant_id == tenant_id,
                SaleRefund.status == "posted",
            )
            .group_by(SaleRefundItem.sale_item_id)
            .all()
        )
        refunded_qty_map = {sale_item_id: d(qty) for sale_item_id, qty in already_refunded_rows}

        total_posted_refunds = (
            self.session.query(func.coalesce(func.sum(SaleRefund.refund_total_amount), 0))
            .filter(
                SaleRefund.sale_id == sale.id,
                SaleRefund.tenant_id == tenant_id,
                SaleRefund.status == "posted",
            )
            .scalar()
        )
        total_posted_refunds = d(total_posted_refunds)

        max_refundable_amount = q2(d(sale.paid_amount) - total_posted_refunds)
        if max_refundable_amount <= Decimal("0.00"):
            raise RefundError("This sale has already been fully refunded.", 409)

        refund_number = self._generate_refund_number(tenant_id)

        refund = SaleRefund(
            tenant_id=tenant_id,
            sale_id=sale.id,
            branch_id=sale.branch_id,
            warehouse_id=sale.warehouse_id,
            till_id=sale.till_id,
            cashier_id=sale.cashier_id,
            customer_id=sale.customer_id,
            refund_number=refund_number,
            status="posted",
            refund_subtotal=Decimal("0.00"),
            refund_discount_amount=Decimal("0.00"),
            refund_tax_amount=Decimal("0.00"),
            refund_total_amount=Decimal("0.00"),
            stock_returned=False,
            reason=reason,
            notes=notes,
            created_at=now,
            updated_at=now,
        )
        self.session.add(refund)
        self.session.flush()

        running_subtotal = Decimal("0.00")
        running_discount = Decimal("0.00")
        running_tax = Decimal("0.00")
        running_total = Decimal("0.00")
        any_stock_returned = False

        for entry in items_payload:
            sale_item_id = entry.get("sale_item_id")
            qty = q4(entry.get("quantity", 0))
            return_to_stock = bool(entry.get("return_to_stock", True))
            condition_note = (entry.get("condition_note") or "").strip() or None

            if not sale_item_id:
                raise RefundError("sale_item_id is required for each item.", 400)
            if qty <= 0:
                raise RefundError("Refund quantity must be greater than zero.", 400)

            sale_item = sale_item_map.get(sale_item_id)
            if not sale_item:
                raise RefundError(f"Sale item {sale_item_id} does not belong to this sale.", 400)

            original_qty = d(sale_item.quantity)
            already_refunded_qty = refunded_qty_map.get(sale_item.id, Decimal("0.0000"))
            remaining_qty = q4(original_qty - already_refunded_qty)

            if remaining_qty <= Decimal("0.0000"):
                raise RefundError(
                    f"Sale item {sale_item.id} has no refundable quantity remaining.",
                    409,
                )

            if qty > remaining_qty:
                raise RefundError(
                    f"Requested refund quantity {qty} exceeds remaining refundable quantity {remaining_qty} for sale item {sale_item.id}.",
                    409,
                )
            line_subtotal = q2(d(sale_item.unit_price) * qty)
            line_discount = prorate(d(sale_item.discount_amount), qty, original_qty)
            line_tax = prorate(d(sale_item.tax_amount), qty, original_qty)
            line_total = prorate(d(sale_item.line_total), qty, original_qty)

            refund_item = SaleRefundItem(
                tenant_id=tenant_id,
                refund_id=refund.id,
                sale_id=sale.id,
                sale_item_id=sale_item.id,
                product_id=sale_item.product_id,
                batch_id=sale_item.batch_id,
                quantity=qty,
                unit_price=sale_item.unit_price,
                discount_amount=line_discount,
                tax_amount=line_tax,
                line_total=line_total,
                return_to_stock=return_to_stock,
                condition_note=condition_note,
                created_at=now,
            )
            self.session.add(refund_item)

            running_subtotal += line_subtotal
            running_discount += line_discount
            running_tax += line_tax
            running_total += line_total

            if return_to_stock:
                self._create_stock_return_movement(
                    sale=sale,
                    sale_item=sale_item,
                    refund=refund,
                    qty=qty,
                    now=now,
                    note=reason,
                )
                any_stock_returned = True

            total_item_refunded_qty = q4(already_refunded_qty + qty)
            if total_item_refunded_qty >= original_qty:
                sale_item.is_returned = True

        max_refundable_amount = q2(d(sale.paid_amount) - total_posted_refunds)
        if running_total > max_refundable_amount:
            raise RefundError("Refund total exceeds collected payment remaining for refund.", 409)

        refund.refund_subtotal = q2(running_subtotal)
        refund.refund_discount_amount = q2(running_discount)
        refund.refund_tax_amount = q2(running_tax)
        refund.refund_total_amount = q2(running_total)
        refund.stock_returned = any_stock_returned
        refund.updated_at = now

        refund_payment = SalePayment(
            sale_id=sale.id,
            payment_method_id=self._resolve_refund_payment_method_id(sale.id),
            amount=q2(-running_total),
            reference_number=refund.refund_number,
            paid_at=now,
            received_by=sale.cashier_id,
        )
        self.session.add(refund_payment)

        new_total_refunded = q2(total_posted_refunds + running_total)
        sale.refunded_amount = new_total_refunded

        if new_total_refunded <= Decimal("0.00"):
            sale.refund_status = "not_refunded"
        elif new_total_refunded < d(sale.paid_amount):
            sale.refund_status = "partially_refunded"
        else:
            sale.refund_status = "refunded"

        if sale.refund_status == "refunded":
            sale.status = "refunded"
        else:
            sale.status = "partially_refunded"

        self.session.flush()
        return refund

    def _generate_refund_number(self, tenant_id: str) -> str:
        count = (
            self.session.query(func.count(SaleRefund.id))
            .filter(SaleRefund.tenant_id == tenant_id)
            .scalar()
            or 0
        )
        return f"RF-{int(count) + 1:05d}"

    def _create_stock_return_movement(self, sale, sale_item, refund, qty, now, note=None):
        movement = InventoryMovement(
            tenant_id=sale.tenant_id,
            branch_id=sale.branch_id,
            warehouse_id=sale.warehouse_id,
            product_id=sale_item.product_id,
            batch_id=sale_item.batch_id,
            movement_type="sale_refund_return",
            quantity=qty,
            unit_cost=sale_item.cost_of_sale,
            reference_type="sale_refund",
            reference_id=refund.id,
            created_by=sale.cashier_id,
        )        
        if hasattr(movement, "notes"):
            movement.notes = f"Stock returned from refund {refund.refund_number}" + (f": {note}" if note else "")
        self.session.add(movement)

    def _resolve_refund_payment_method_id(self, sale_id: str) -> str:
        payment = (
            self.session.query(SalePayment)
            .filter(SalePayment.sale_id == sale_id)
            .order_by(SalePayment.paid_at.asc())
            .first()
        )
        if not payment:
            raise RefundError("Cannot create refund payment transaction because original sale has no payment record.", 409)
        return payment.payment_method_id