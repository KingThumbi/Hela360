from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone

from sqlalchemy import func

from app.models import Product, Till, TillShift
from app.models.pos import Sale, SaleItem, SalePayment, SaleRefund, SaleRefundItem
from app.services.tenant.auth.authorization_context import AuthorizationContext
from app.services.tenant.pos.till_shift_service import (
    shift_is_owned_by_session,
)
from app.services.tenant.inventory.refund_stock_service import (
    RefundStockRestorationError,
    restore_refund_stock,
)


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

    def create_refund(
        self,
        *,
        identity: AuthorizationContext,
        sale_id: str,
        payload: dict,
    ) -> SaleRefund:
        """
        Create a partial or full refund for a sale.

        The authenticated AuthorizationContext is the single source of truth
        for tenant, branch and refunding user.
        """

        if not identity.branch_id:
            raise RefundError(
                "Authenticated user is not assigned to a branch.",
                403,
            )

        now = utcnow()
        till_shift = self._require_open_till_shift(identity)

        items_payload = payload.get("items") or []
        reason = (payload.get("reason") or "").strip() or None
        notes = (payload.get("notes") or "").strip() or None

        if not items_payload:
            raise RefundError(
                "At least one refund item is required.",
                400,
            )

        sale = (
            self.session.query(Sale)
            .filter(
                Sale.id == sale_id,
                Sale.tenant_id == identity.tenant_id,
            )
            .with_for_update()
            .first()
        )

        if not sale:
            raise RefundError("Sale not found.", 404)

        if str(sale.branch_id) != str(identity.branch_id):
            raise RefundError(
                "You cannot refund sales from another branch.",
                403,
            )

        if (sale.status or "").lower() == "voided":
            raise RefundError(
                "Voided sales cannot be refunded.",
                409,
            )

        sale_items = (
            self.session.query(SaleItem)
            .filter(SaleItem.sale_id == sale.id)
            .with_for_update()
            .all()
        )

        if not sale_items:
            raise RefundError(
                "Sale has no items.",
                400,
            )

        sale_item_map = {
            item.id: item
            for item in sale_items
        }
        product_ids = {
            str(item.product_id)
            for item in sale_items
            if item.product_id
        }
        products = (
            self.session.query(Product)
            .filter(
                Product.tenant_id == identity.tenant_id,
                Product.id.in_(product_ids),
            )
            .with_for_update()
            .all()
            if product_ids
            else []
        )
        product_map = {
            str(product.id): product
            for product in products
        }

        already_refunded_rows = (
            self.session.query(
                SaleRefundItem.sale_item_id,
                func.coalesce(
                    func.sum(SaleRefundItem.quantity),
                    0,
                ),
            )
            .join(
                SaleRefund,
                SaleRefund.id == SaleRefundItem.refund_id,
            )
            .filter(
                SaleRefund.sale_id == sale.id,
                SaleRefund.tenant_id == identity.tenant_id,
                SaleRefund.status == "posted",
            )
            .group_by(SaleRefundItem.sale_item_id)
            .all()
        )

        refunded_qty_map = {
            sale_item_id: d(quantity)
            for sale_item_id, quantity in already_refunded_rows
        }

        total_posted_refunds = (
            self.session.query(
                func.coalesce(
                    func.sum(SaleRefund.refund_total_amount),
                    0,
                )
            )
            .filter(
                SaleRefund.sale_id == sale.id,
                SaleRefund.tenant_id == identity.tenant_id,
                SaleRefund.status == "posted",
            )
            .scalar()
        )

        total_posted_refunds = d(total_posted_refunds)

        max_refundable_amount = q2(
            d(sale.paid_amount) - total_posted_refunds
        )

        if max_refundable_amount <= Decimal("0.00"):
            raise RefundError(
                "This sale has already been fully refunded.",
                409,
            )

        refund_number = self._generate_refund_number(
            identity.tenant_id,
        )

        refund = SaleRefund(
            tenant_id=identity.tenant_id,
            sale_id=sale.id,
            branch_id=sale.branch_id,
            warehouse_id=sale.warehouse_id,
            till_id=sale.till_id,
            till_shift_id=till_shift.id,
            cashier_id=identity.user_id,
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
            return_to_stock = bool(
                entry.get("return_to_stock", True)
            )
            condition_note = (
                entry.get("condition_note") or ""
            ).strip() or None

            if not sale_item_id:
                raise RefundError(
                    "sale_item_id is required for each item.",
                    400,
                )

            if qty <= Decimal("0.00"):
                raise RefundError(
                    "Refund quantity must be greater than zero.",
                    400,
                )

            sale_item = sale_item_map.get(sale_item_id)

            if sale_item is None:
                raise RefundError(
                    f"Sale item {sale_item_id} does not belong to this sale.",
                    400,
                )

            original_qty = d(sale_item.quantity)
            original_base_qty = d(
                getattr(sale_item, "base_quantity", None)
                or sale_item.quantity
            )

            already_refunded_qty = refunded_qty_map.get(
                sale_item.id,
                Decimal("0.0000"),
            )

            remaining_qty = q4(
                original_qty - already_refunded_qty
            )

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
            base_qty = prorate(
                original_base_qty,
                qty,
                original_qty,
            )

            line_subtotal = q2(
                d(sale_item.unit_price) * qty
            )

            line_discount = prorate(
                d(sale_item.discount_amount),
                qty,
                original_qty,
            )

            line_tax = prorate(
                d(sale_item.tax_amount),
                qty,
                original_qty,
            )

            line_total = prorate(
                d(sale_item.line_total),
                qty,
                original_qty,
            )

            refund_item = SaleRefundItem(
                tenant_id=identity.tenant_id,
                refund_id=refund.id,
                sale_id=sale.id,
                sale_item_id=sale_item.id,
                product_id=sale_item.product_id,
                batch_id=sale_item.batch_id,
                quantity=qty,
                base_quantity=base_qty,
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
                product = product_map.get(str(sale_item.product_id))
                if product is None:
                    raise RefundError(
                        f"Product not found for sale item {sale_item.id}.",
                        409,
                    )

                try:
                    restored_lines = restore_refund_stock(
                        self.session,
                        tenant_id=str(sale.tenant_id),
                        branch_id=str(sale.branch_id),
                        warehouse_id=str(sale.warehouse_id),
                        sale_id=str(sale.id),
                        sale_item_id=str(sale_item.id),
                        product=product,
                        quantity=base_qty,
                        refund_id=str(refund.id),
                        refund_number=refund.refund_number,
                        created_by=str(identity.user_id),
                        note=reason,
                        now=now,
                    )
                except RefundStockRestorationError as exc:
                    raise RefundError(str(exc), 409) from exc

                any_stock_returned = any_stock_returned or bool(restored_lines)

            total_item_refunded_qty = q4(
                already_refunded_qty + qty
            )

            if total_item_refunded_qty >= original_qty:
                sale_item.is_returned = True

        if running_total > max_refundable_amount:
            raise RefundError(
                "Refund total exceeds collected payment remaining for refund.",
                409,
            )

        refund.refund_subtotal = q2(running_subtotal)
        refund.refund_discount_amount = q2(running_discount)
        refund.refund_tax_amount = q2(running_tax)
        refund.refund_total_amount = q2(running_total)
        refund.stock_returned = any_stock_returned
        refund.updated_at = now

        self.session.add(
            SalePayment(
                sale_id=sale.id,
                payment_method_id=self._resolve_refund_payment_method_id(
                    sale.id,
                ),
                amount=q2(-running_total),
                reference_number=refund.refund_number,
                paid_at=now,
                received_by=identity.user_id,
            )
        )

        new_total_refunded = q2(
            total_posted_refunds + running_total
        )

        sale.refunded_amount = new_total_refunded

        if new_total_refunded <= Decimal("0.00"):
            sale.refund_status = "not_refunded"
        elif new_total_refunded < d(sale.paid_amount):
            sale.refund_status = "partially_refunded"
        else:
            sale.refund_status = "refunded"

        sale.status = (
            "refunded"
            if sale.refund_status == "refunded"
            else "partially_refunded"
        )

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

    def _require_open_till_shift(
        self,
        identity: AuthorizationContext,
    ) -> TillShift:
        shift = (
            self.session.query(TillShift)
            .filter(
                TillShift.tenant_id == str(identity.tenant_id),
                TillShift.branch_id == str(identity.branch_id),
                TillShift.cashier_id == str(identity.user_id),
                TillShift.status == "open",
                TillShift.closed_at.is_(None),
            )
            .with_for_update()
            .order_by(
                TillShift.opened_at.desc(),
                TillShift.created_at.desc(),
            )
            .first()
        )

        if not shift:
            raise RefundError(
                "Open till shift is required to process refunds.",
                409,
            )

        if not shift_is_owned_by_session(
            shift,
            identity.session_id,
        ):
            raise RefundError(
                "This till shift is active on another session.",
                409,
            )

        till = (
            self.session.query(Till)
            .filter(
                Till.id == str(shift.till_id),
                Till.tenant_id == str(identity.tenant_id),
                Till.branch_id == str(identity.branch_id),
                Till.is_active.is_(True),
            )
            .with_for_update()
            .first()
        )

        if not till:
            raise RefundError(
                "Active till not found for this refund shift.",
                409,
            )

        return shift

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
