# app/models/inventory.py
from app.extensions import db
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Warehouse(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "warehouses"
    __table_args__ = (db.UniqueConstraint("tenant_id", "branch_id", "code", name="uq_warehouses_tenant_branch_code"),)

    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id = db.Column(db.String(36), db.ForeignKey("branches.id"), nullable=False, index=True)
    code = db.Column(db.String(30), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    warehouse_type = db.Column(db.String(30), nullable=False, default="main")
    is_active = db.Column(db.Boolean, nullable=False, default=True)


class InventoryBatch(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "inventory_batches"
    __table_args__ = (
        db.UniqueConstraint(
            "tenant_id",
            "warehouse_id",
            "product_id",
            "batch_number",
            name="uq_inventory_batches_tenant_warehouse_product_batch",
        ),
    )

    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    product_id = db.Column(db.String(36), db.ForeignKey("products.id"), nullable=False, index=True)
    warehouse_id = db.Column(db.String(36), db.ForeignKey("warehouses.id"), nullable=False, index=True)
    batch_number = db.Column(db.String(100), index=True)
    expiry_date = db.Column(db.Date, index=True)
    manufacture_date = db.Column(db.Date)
    unit_cost = db.Column(db.Numeric(18, 2))
    quantity_on_hand = db.Column(db.Numeric(18, 4), nullable=False, default=0)
    quantity_reserved = db.Column(db.Numeric(18, 4), nullable=False, default=0)
    status = db.Column(db.String(30), nullable=False, default="available")
    received_at = db.Column(db.DateTime(timezone=True))


class StockBalance(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "stock_balances"
    __table_args__ = (db.UniqueConstraint("tenant_id", "warehouse_id", "product_id", name="uq_stock_balances_tenant_warehouse_product"),)

    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id = db.Column(db.String(36), db.ForeignKey("branches.id"), nullable=False, index=True)
    warehouse_id = db.Column(db.String(36), db.ForeignKey("warehouses.id"), nullable=False, index=True)
    product_id = db.Column(db.String(36), db.ForeignKey("products.id"), nullable=False, index=True)
    quantity_on_hand = db.Column(db.Numeric(18, 4), nullable=False, default=0)
    quantity_reserved = db.Column(db.Numeric(18, 4), nullable=False, default=0)
    quantity_available = db.Column(db.Numeric(18, 4), nullable=False, default=0)
    avg_unit_cost = db.Column(db.Numeric(18, 2), nullable=False, default=0)


class InventoryMovement(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "inventory_movements"

    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id = db.Column(db.String(36), db.ForeignKey("branches.id"), nullable=False, index=True)
    warehouse_id = db.Column(db.String(36), db.ForeignKey("warehouses.id"), nullable=False, index=True)
    product_id = db.Column(db.String(36), db.ForeignKey("products.id"), nullable=False, index=True)
    batch_id = db.Column(db.String(36), db.ForeignKey("inventory_batches.id"), index=True)
    sale_item_id = db.Column(db.String(36), db.ForeignKey("sale_items.id"), index=True)
    movement_type = db.Column(db.String(40), nullable=False, index=True)
    quantity = db.Column(db.Numeric(18, 4), nullable=False)
    unit_cost = db.Column(db.Numeric(18, 2))
    unit_price = db.Column(db.Numeric(18, 2))
    reference_type = db.Column(db.String(50), nullable=False, index=True)
    reference_id = db.Column(db.String(36), nullable=False, index=True)
    notes = db.Column(db.Text)
    created_by = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)


class GoodsReceipt(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "goods_receipts"
    __table_args__ = (
        db.UniqueConstraint(
            "tenant_id",
            "receipt_number",
            name="uq_goods_receipts_tenant_receipt_number",
        ),
        db.UniqueConstraint(
            "tenant_id",
            "idempotency_key",
            name="uq_goods_receipts_tenant_idempotency_key",
        ),
    )

    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id = db.Column(db.String(36), db.ForeignKey("branches.id"), nullable=False, index=True)
    warehouse_id = db.Column(db.String(36), db.ForeignKey("warehouses.id"), nullable=False, index=True)
    supplier_id = db.Column(db.String(36), db.ForeignKey("suppliers.id"), index=True)
    receipt_number = db.Column(db.String(50), nullable=False, index=True)
    supplier_reference = db.Column(db.String(120))
    idempotency_key = db.Column(db.String(120), nullable=False, index=True)
    request_fingerprint = db.Column(db.String(64), nullable=False)
    received_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    status = db.Column(db.String(30), nullable=False, default="received", index=True)
    notes = db.Column(db.Text)
    received_by = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)


class GoodsReceiptItem(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "goods_receipt_items"
    __table_args__ = (
        db.UniqueConstraint(
            "goods_receipt_id",
            "line_number",
            name="uq_goods_receipt_items_receipt_line",
        ),
    )

    goods_receipt_id = db.Column(db.String(36), db.ForeignKey("goods_receipts.id"), nullable=False, index=True)
    product_id = db.Column(db.String(36), db.ForeignKey("products.id"), nullable=False, index=True)
    product_unit_id = db.Column(db.String(36), db.ForeignKey("product_units.id"), index=True)
    batch_id = db.Column(db.String(36), db.ForeignKey("inventory_batches.id"), index=True)
    line_number = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Numeric(18, 4), nullable=False)
    base_quantity = db.Column(db.Numeric(18, 4), nullable=False, default=0)
    unit_code_snapshot = db.Column(db.String(20))
    unit_name_snapshot = db.Column(db.String(50))
    conversion_factor_to_base = db.Column(db.Numeric(18, 6), nullable=False, default=1)
    batch_number = db.Column(db.String(100))
    manufacture_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    unit_cost = db.Column(db.Numeric(18, 2), nullable=False, default=0)
    base_unit_cost = db.Column(db.Numeric(18, 2), nullable=False, default=0)
    supplier_batch_reference = db.Column(db.String(120))


class StockCount(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "stock_counts"
    __table_args__ = (
        db.UniqueConstraint(
            "tenant_id",
            "count_number",
            name="uq_stock_counts_tenant_count_number",
        ),
        db.UniqueConstraint(
            "tenant_id",
            "idempotency_key",
            name="uq_stock_counts_tenant_idempotency_key",
        ),
    )

    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id = db.Column(db.String(36), db.ForeignKey("branches.id"), nullable=False, index=True)
    warehouse_id = db.Column(db.String(36), db.ForeignKey("warehouses.id"), nullable=False, index=True)
    count_number = db.Column(db.String(50), nullable=False, index=True)
    idempotency_key = db.Column(db.String(120), nullable=False, index=True)
    request_fingerprint = db.Column(db.String(64), nullable=False)
    scope_type = db.Column(db.String(30), nullable=False, default="full")
    status = db.Column(db.String(30), nullable=False, default="open", index=True)
    snapshot_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    started_at = db.Column(db.DateTime(timezone=True), nullable=False)
    started_by = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    completed_at = db.Column(db.DateTime(timezone=True))
    completed_by = db.Column(db.String(36), db.ForeignKey("users.id"))
    cancelled_at = db.Column(db.DateTime(timezone=True))
    cancelled_by = db.Column(db.String(36), db.ForeignKey("users.id"))
    notes = db.Column(db.Text)


class StockCountItem(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "stock_count_items"
    __table_args__ = (
        db.UniqueConstraint(
            "stock_count_id",
            "product_id",
            "batch_id",
            name="uq_stock_count_items_count_product_batch",
        ),
        db.UniqueConstraint(
            "stock_count_id",
            "line_number",
            name="uq_stock_count_items_count_line",
        ),
    )

    stock_count_id = db.Column(db.String(36), db.ForeignKey("stock_counts.id"), nullable=False, index=True)
    product_id = db.Column(db.String(36), db.ForeignKey("products.id"), nullable=False, index=True)
    batch_id = db.Column(db.String(36), db.ForeignKey("inventory_batches.id"), index=True)
    line_number = db.Column(db.Integer, nullable=False)
    snapshot_quantity = db.Column(db.Numeric(18, 4), nullable=False, default=0)
    expected_quantity = db.Column(db.Numeric(18, 4), nullable=False, default=0)
    counted_quantity = db.Column(db.Numeric(18, 4))
    variance_quantity = db.Column(db.Numeric(18, 4))
    counted_at = db.Column(db.DateTime(timezone=True))
    counted_by = db.Column(db.String(36), db.ForeignKey("users.id"), index=True)
    notes = db.Column(db.Text)


class StockAdjustment(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "stock_adjustments"
    __table_args__ = (
        db.UniqueConstraint(
            "tenant_id",
            "adjustment_number",
            name="uq_stock_adjustments_tenant_adjustment_number",
        ),
        db.UniqueConstraint(
            "tenant_id",
            "idempotency_key",
            name="uq_stock_adjustments_tenant_idempotency_key",
        ),
        db.UniqueConstraint(
            "tenant_id",
            "source_type",
            "source_id",
            name="uq_stock_adjustments_tenant_source",
        ),
    )

    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id = db.Column(db.String(36), db.ForeignKey("branches.id"), nullable=False, index=True)
    warehouse_id = db.Column(db.String(36), db.ForeignKey("warehouses.id"), nullable=False, index=True)
    adjustment_number = db.Column(db.String(50), nullable=False, index=True)
    reason_code = db.Column(db.String(40), nullable=False, index=True)
    reason = db.Column(db.String(255))
    source_type = db.Column(db.String(40), nullable=False, default="manual", index=True)
    source_id = db.Column(db.String(36), index=True)
    status = db.Column(db.String(30), nullable=False, default="posted", index=True)
    idempotency_key = db.Column(db.String(120), nullable=False, index=True)
    request_fingerprint = db.Column(db.String(64), nullable=False)
    posted_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    posted_by = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    notes = db.Column(db.Text)


class StockAdjustmentItem(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "stock_adjustment_items"
    __table_args__ = (
        db.UniqueConstraint(
            "stock_adjustment_id",
            "line_number",
            name="uq_stock_adjustment_items_adjustment_line",
        ),
        db.UniqueConstraint(
            "stock_adjustment_id",
            "product_id",
            "batch_id",
            name="uq_stock_adjustment_items_adjustment_product_batch",
        ),
    )

    stock_adjustment_id = db.Column(db.String(36), db.ForeignKey("stock_adjustments.id"), nullable=False, index=True)
    product_id = db.Column(db.String(36), db.ForeignKey("products.id"), nullable=False, index=True)
    batch_id = db.Column(db.String(36), db.ForeignKey("inventory_batches.id"), index=True)
    stock_count_item_id = db.Column(db.String(36), db.ForeignKey("stock_count_items.id"), index=True)
    line_number = db.Column(db.Integer, nullable=False)
    quantity_delta = db.Column(db.Numeric(18, 4), nullable=False)
    reason = db.Column(db.String(255))
