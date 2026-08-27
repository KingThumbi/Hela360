from __future__ import annotations

from decimal import Decimal

from app.errors import NotFoundError, ValidationError
from sqlalchemy.orm import noload

from app.models import (
    Branch,
    Customer,
    PaymentMethod,
    Product,
    Sale,
    SaleItem,
    SalePayment,
    Tenant,
    Till,
    TillShift,
    User,
)
from app.services.tenant.auth.authorization_context import AuthorizationContext


def _decimal(value, default: str = "0.00") -> str:
    if value is None:
        return default
    if isinstance(value, Decimal):
        return str(value)
    return str(value)


def _timestamp(value) -> str | None:
    return value.isoformat() if value else None


def _get_plain(session, model, primary_key):
    return (
        session.query(model)
        .options(noload("*"))
        .filter(model.id == primary_key)
        .first()
    )


def _full_name(user_or_customer) -> str | None:
    parts = [
        getattr(user_or_customer, "first_name", None),
        getattr(user_or_customer, "other_names", None),
        getattr(user_or_customer, "last_name", None),
    ]
    name = " ".join(part.strip() for part in parts if part and part.strip())
    return name or getattr(user_or_customer, "username", None)


class ReceiptService:
    def __init__(self, session):
        self.session = session

    def get_receipt(
        self,
        *,
        identity: AuthorizationContext,
        sale_id: str,
    ) -> dict:
        if not identity.branch_id:
            raise ValidationError(
                "Authenticated user is not assigned to a branch."
            )

        sale = (
            self.session.query(Sale)
            .filter(
                Sale.tenant_id == identity.tenant_id,
                Sale.id == sale_id,
            )
            .first()
        )

        if not sale:
            raise NotFoundError("Sale receipt not found.")

        if str(sale.branch_id) != str(identity.branch_id):
            raise NotFoundError("Sale receipt not found.")

        tenant = _get_plain(self.session, Tenant, str(sale.tenant_id))
        branch = _get_plain(self.session, Branch, str(sale.branch_id))
        customer = (
            _get_plain(self.session, Customer, str(sale.customer_id))
            if sale.customer_id
            else None
        )
        cashier = (
            _get_plain(self.session, User, str(sale.cashier_id))
            if sale.cashier_id
            else None
        )
        till = (
            _get_plain(self.session, Till, str(sale.till_id))
            if sale.till_id
            else None
        )
        till_shift = (
            _get_plain(self.session, TillShift, sale.till_shift_id)
            if sale.till_shift_id
            else None
        )

        items = (
            self.session.query(SaleItem)
            .filter(SaleItem.sale_id == sale.id)
            .order_by(SaleItem.id.asc())
            .all()
        )
        product_ids = [
            str(item.product_id)
            for item in items
            if item.product_id
        ]
        products = (
            self.session.query(Product)
            .filter(
                Product.tenant_id == identity.tenant_id,
                Product.id.in_(product_ids),
            )
            .all()
            if product_ids
            else []
        )
        product_map = {str(product.id): product for product in products}

        payments = (
            self.session.query(SalePayment)
            .filter(SalePayment.sale_id == sale.id)
            .order_by(SalePayment.paid_at.asc(), SalePayment.id.asc())
            .all()
        )
        method_ids = [
            str(payment.payment_method_id)
            for payment in payments
            if payment.payment_method_id
        ]
        methods = (
            self.session.query(PaymentMethod)
            .filter(
                PaymentMethod.tenant_id == identity.tenant_id,
                PaymentMethod.id.in_(method_ids),
            )
            .all()
            if method_ids
            else []
        )
        method_map = {str(method.id): method for method in methods}

        currency = getattr(tenant, "base_currency", None) if tenant else None

        return {
            "sale": {
                "id": str(sale.id),
                "sale_number": sale.sale_number,
                "status": sale.status,
                "sold_at": _timestamp(getattr(sale, "sale_date", None)),
                "created_at": _timestamp(getattr(sale, "created_at", None)),
                "till_shift_id": str(sale.till_shift_id)
                if sale.till_shift_id
                else None,
                "refund_status": getattr(sale, "refund_status", None),
                "refunded_amount": _decimal(
                    getattr(sale, "refunded_amount", None)
                ),
            },
            "seller": {
                "id": str(tenant.id) if tenant else str(sale.tenant_id),
                "display_name": getattr(tenant, "display_name", None),
                "legal_name": getattr(tenant, "legal_name", None),
                "phone": getattr(tenant, "phone", None),
                "email": getattr(tenant, "email", None),
                "currency": currency,
            },
            "branch": {
                "id": str(branch.id) if branch else str(sale.branch_id),
                "code": getattr(branch, "code", None),
                "name": getattr(branch, "name", None),
                "phone": getattr(branch, "phone", None),
                "email": getattr(branch, "email", None),
                "address_line1": getattr(branch, "address_line1", None),
                "address_line2": getattr(branch, "address_line2", None),
                "city": getattr(branch, "city", None),
                "county_state": getattr(branch, "county_state", None),
                "country": getattr(branch, "country", None),
            },
            "customer": self._serialize_customer(customer),
            "items": [
                self._serialize_item(item, product_map.get(str(item.product_id)))
                for item in items
            ],
            "payments": [
                self._serialize_payment(
                    payment,
                    method_map.get(str(payment.payment_method_id)),
                )
                for payment in payments
            ],
            "totals": {
                "subtotal": _decimal(sale.subtotal),
                "discount_amount": _decimal(sale.discount_amount),
                "tax_amount": _decimal(sale.tax_amount),
                "total_amount": _decimal(sale.total_amount),
                "paid_amount": _decimal(sale.paid_amount),
                "balance_due": _decimal(sale.balance_due),
                "currency": currency,
            },
            "cashier": self._serialize_cashier(cashier),
            "till": self._serialize_till(till),
            "till_shift": self._serialize_till_shift(till_shift),
        }

    def _serialize_customer(self, customer: Customer | None) -> dict | None:
        if not customer:
            return None

        return {
            "id": str(customer.id),
            "customer_number": customer.customer_number,
            "full_name": _full_name(customer),
            "phone": customer.phone,
        }

    def _serialize_item(
        self,
        item: SaleItem,
        product: Product | None,
    ) -> dict:
        return {
            "id": str(item.id),
            "product_id": str(item.product_id) if item.product_id else None,
            "description": getattr(product, "name", None)
            or str(item.product_id),
            "sku": getattr(product, "internal_sku", None),
            "quantity": _decimal(item.quantity, "0.0000"),
            "unit_price": _decimal(item.unit_price),
            "discount_amount": _decimal(item.discount_amount),
            "tax_amount": _decimal(item.tax_amount),
            "line_total": _decimal(item.line_total),
        }

    def _serialize_payment(
        self,
        payment: SalePayment,
        method: PaymentMethod | None,
    ) -> dict:
        return {
            "id": str(payment.id),
            "payment_method_id": str(payment.payment_method_id)
            if payment.payment_method_id
            else None,
            "payment_method": {
                "id": str(method.id),
                "name": method.name,
                "code": method.code,
                "method_type": method.method_type,
            }
            if method
            else None,
            "amount": _decimal(payment.amount),
            "reference": payment.reference_number,
            "paid_at": _timestamp(payment.paid_at),
        }

    def _serialize_cashier(self, cashier: User | None) -> dict | None:
        if not cashier:
            return None

        return {
            "id": str(cashier.id),
            "name": _full_name(cashier),
            "username": cashier.username,
        }

    def _serialize_till(self, till: Till | None) -> dict | None:
        if not till:
            return None

        return {
            "id": str(till.id),
            "code": till.code,
            "name": till.name,
        }

    def _serialize_till_shift(
        self,
        till_shift: TillShift | None,
    ) -> dict | None:
        if not till_shift:
            return None

        return {
            "id": str(till_shift.id),
            "opened_at": _timestamp(till_shift.opened_at),
            "closed_at": _timestamp(till_shift.closed_at),
            "status": till_shift.status,
        }
