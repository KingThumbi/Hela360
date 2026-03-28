from app.extensions import db
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from decimal import Decimal


class Till(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "tills"
    __table_args__ = (
        db.UniqueConstraint("tenant_id", "branch_id", "code", name="uq_tills_tenant_branch_code"),
    )

    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id = db.Column(db.String(36), db.ForeignKey("branches.id"), nullable=False, index=True)

    code = db.Column(db.String(30), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)


class Shift(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "shifts"

    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id = db.Column(db.String(36), db.ForeignKey("branches.id"), nullable=False, index=True)
    till_id = db.Column(db.String(36), db.ForeignKey("tills.id"), nullable=False, index=True)

    opened_by = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    opened_at = db.Column(db.DateTime(timezone=True), nullable=False)
    opening_float = db.Column(db.Numeric(18, 2), nullable=False, default=0)

    closed_by = db.Column(db.String(36), db.ForeignKey("users.id"))
    closed_at = db.Column(db.DateTime(timezone=True))

    closing_cash_expected = db.Column(db.Numeric(18, 2))
    closing_cash_counted = db.Column(db.Numeric(18, 2))
    variance_amount = db.Column(db.Numeric(18, 2))

    status = db.Column(db.String(20), nullable=False, default="open")


class Sale(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "sales"
    __table_args__ = (
        db.UniqueConstraint("tenant_id", "sale_number", name="uq_sales_tenant_sale_number"),
    )

    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id = db.Column(db.String(36), db.ForeignKey("branches.id"), nullable=False, index=True)
    till_id = db.Column(db.String(36), db.ForeignKey("tills.id"), nullable=False, index=True)
    shift_id = db.Column(db.String(36), db.ForeignKey("shifts.id"), index=True)
    warehouse_id = db.Column(db.String(36), db.ForeignKey("warehouses.id"), nullable=False, index=True)

    customer_id = db.Column(db.String(36), db.ForeignKey("customers.id"), index=True)

    sale_number = db.Column(db.String(50), nullable=False)
    sale_date = db.Column(db.DateTime(timezone=True), nullable=False, index=True)

    sale_channel = db.Column(db.String(30), nullable=False, default="pos")
    status = db.Column(db.String(30), nullable=False, default="completed")

    subtotal = db.Column(db.Numeric(18, 2), nullable=False, default=0)
    discount_amount = db.Column(db.Numeric(18, 2), nullable=False, default=0)
    tax_amount = db.Column(db.Numeric(18, 2), nullable=False, default=0)
    total_amount = db.Column(db.Numeric(18, 2), nullable=False, default=0)

    paid_amount = db.Column(db.Numeric(18, 2), nullable=False, default=0)
    balance_due = db.Column(db.Numeric(18, 2), nullable=False, default=0)

    notes = db.Column(db.Text)

    cashier_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    refunded_amount = db.Column(db.Numeric(18, 2), nullable=False, default=0)
    refund_status = db.Column(db.String(20), nullable=False, default="not_refunded")

class SaleItem(UUIDPrimaryKeyMixin, db.Model):
    __tablename__ = "sale_items"

    sale_id = db.Column(db.String(36), db.ForeignKey("sales.id"), nullable=False, index=True)
    product_id = db.Column(db.String(36), db.ForeignKey("products.id"), nullable=False, index=True)
    batch_id = db.Column(db.String(36), db.ForeignKey("inventory_batches.id"), index=True)

    quantity = db.Column(db.Numeric(18, 4), nullable=False)
    unit_price = db.Column(db.Numeric(18, 2), nullable=False)

    discount_amount = db.Column(db.Numeric(18, 2), nullable=False, default=0)
    tax_amount = db.Column(db.Numeric(18, 2), nullable=False, default=0)

    line_total = db.Column(db.Numeric(18, 2), nullable=False)
    cost_of_sale = db.Column(db.Numeric(18, 2))

    is_returned = db.Column(db.Boolean, nullable=False, default=False)


class PaymentMethod(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "payment_methods"
    __table_args__ = (
        db.UniqueConstraint("tenant_id", "code", name="uq_payment_methods_tenant_code"),
    )

    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)

    code = db.Column(db.String(30), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    method_type = db.Column(db.String(30), nullable=False)

    is_active = db.Column(db.Boolean, nullable=False, default=True)


class SalePayment(UUIDPrimaryKeyMixin, db.Model):
    __tablename__ = "sale_payments"

    sale_id = db.Column(db.String(36), db.ForeignKey("sales.id"), nullable=False, index=True)
    payment_method_id = db.Column(db.String(36), db.ForeignKey("payment_methods.id"), nullable=False, index=True)

    amount = db.Column(db.Numeric(18, 2), nullable=False)
    reference_number = db.Column(db.String(100))

    paid_at = db.Column(db.DateTime(timezone=True), nullable=False)
    received_by = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)

class SaleRefund(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "sale_refunds"
    __table_args__ = (
        db.UniqueConstraint("tenant_id", "refund_number", name="uq_sale_refunds_tenant_refund_number"),
    )

    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    sale_id = db.Column(db.String(36), db.ForeignKey("sales.id"), nullable=False, index=True)
    branch_id = db.Column(db.String(36), db.ForeignKey("branches.id"), nullable=False, index=True)
    warehouse_id = db.Column(db.String(36), db.ForeignKey("warehouses.id"), nullable=False, index=True)
    till_id = db.Column(db.String(36), db.ForeignKey("tills.id"), nullable=False, index=True)
    cashier_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    customer_id = db.Column(db.String(36), db.ForeignKey("customers.id"), index=True)

    refund_number = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="posted")

    refund_subtotal = db.Column(db.Numeric(18, 2), nullable=False, default=0)
    refund_discount_amount = db.Column(db.Numeric(18, 2), nullable=False, default=0)
    refund_tax_amount = db.Column(db.Numeric(18, 2), nullable=False, default=0)
    refund_total_amount = db.Column(db.Numeric(18, 2), nullable=False, default=0)

    stock_returned = db.Column(db.Boolean, nullable=False, default=False)
    reason = db.Column(db.Text)
    notes = db.Column(db.Text)

class SaleRefundItem(UUIDPrimaryKeyMixin, db.Model):
    __tablename__ = "sale_refund_items"

    created_at = db.Column(db.DateTime(timezone=True), nullable=False)

    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    refund_id = db.Column(db.String(36), db.ForeignKey("sale_refunds.id", ondelete="CASCADE"), nullable=False, index=True)
    sale_id = db.Column(db.String(36), db.ForeignKey("sales.id"), nullable=False, index=True)
    sale_item_id = db.Column(db.String(36), db.ForeignKey("sale_items.id"), nullable=False, index=True)
    product_id = db.Column(db.String(36), db.ForeignKey("products.id"), nullable=False, index=True)
    batch_id = db.Column(db.String(36), db.ForeignKey("inventory_batches.id"), index=True)

    quantity = db.Column(db.Numeric(18, 4), nullable=False)
    unit_price = db.Column(db.Numeric(18, 2), nullable=False)

    discount_amount = db.Column(db.Numeric(18, 2), nullable=False, default=0)
    tax_amount = db.Column(db.Numeric(18, 2), nullable=False, default=0)
    line_total = db.Column(db.Numeric(18, 2), nullable=False)

    return_to_stock = db.Column(db.Boolean, nullable=False, default=True)
    condition_note = db.Column(db.Text)

class SaleActionRequest(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "sale_action_requests"

    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    sale_id = db.Column(db.String(36), db.ForeignKey("sales.id"), nullable=False, index=True)

    action_type = db.Column(db.String(30), nullable=False, index=True)   # refund_sale | void_sale
    status = db.Column(db.String(20), nullable=False, default="pending") # pending | approved | rejected | executed | cancelled

    requested_by = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    approved_by = db.Column(db.String(36), db.ForeignKey("users.id"), index=True)
    rejected_by = db.Column(db.String(36), db.ForeignKey("users.id"), index=True)

    request_reason = db.Column(db.Text)
    decision_reason = db.Column(db.Text)
    request_payload = db.Column(db.JSON)

    requires_approval = db.Column(db.Boolean, nullable=False, default=True)
    approved_at = db.Column(db.DateTime(timezone=True))
    rejected_at = db.Column(db.DateTime(timezone=True))
    executed_at = db.Column(db.DateTime(timezone=True))        