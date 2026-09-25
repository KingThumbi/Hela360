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

    # Commercial document supplied with the physical delivery.
    supplier_invoice_number = db.Column(db.String(120), index=True)
    supplier_invoice_date = db.Column(db.Date, index=True)
    payment_terms = db.Column(db.String(120))
    invoice_currency = db.Column(db.String(3), nullable=False, default="KES")

    # Values declared on the supplier document.
    supplier_subtotal = db.Column(db.Numeric(18, 2))
    supplier_discount_total = db.Column(db.Numeric(18, 2))
    supplier_tax_total = db.Column(db.Numeric(18, 2))
    supplier_invoice_total = db.Column(db.Numeric(18, 2))

    # Values independently calculated by Hela360.
    calculated_subtotal = db.Column(db.Numeric(18, 2))
    calculated_tax_total = db.Column(db.Numeric(18, 2))
    calculated_total = db.Column(db.Numeric(18, 2))
    reconciliation_difference = db.Column(db.Numeric(18, 2))

    idempotency_key = db.Column(db.String(120), nullable=False, index=True)
    request_fingerprint = db.Column(db.String(64), nullable=False)

    created_by = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    receiving_started_at = db.Column(
        db.DateTime(timezone=True),
    )
    receiving_started_by = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        index=True,
    )

    received_at = db.Column(
        db.DateTime(timezone=True),
        index=True,
    )
    received_by = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        index=True,
    )

    # The compatibility create endpoint enters directly at RECEIVED.
    # Structured receiving begins at DRAFT.
    status = db.Column(
        db.String(30),
        nullable=False,
        default="received",
        index=True,
    )

    under_review_at = db.Column(db.DateTime(timezone=True))
    under_review_by = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        index=True,
    )

    approved_at = db.Column(db.DateTime(timezone=True))
    approved_by = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        index=True,
    )

    posted_at = db.Column(db.DateTime(timezone=True), index=True)
    posted_by = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        index=True,
    )

    cancelled_at = db.Column(db.DateTime(timezone=True))
    cancelled_by = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        index=True,
    )

    notes = db.Column(db.Text)
    received_by = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        index=True,
    )


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
    # Existing quantity remains authoritative during compatibility migration.
    quantity = db.Column(db.Numeric(18, 4), nullable=False)

    invoiced_quantity = db.Column(db.Numeric(18, 4))
    received_quantity = db.Column(db.Numeric(18, 4))
    accepted_quantity = db.Column(db.Numeric(18, 4))
    rejected_quantity = db.Column(db.Numeric(18, 4))
    bonus_quantity = db.Column(db.Numeric(18, 4))

    base_quantity = db.Column(db.Numeric(18, 4), nullable=False, default=0)
    unit_code_snapshot = db.Column(db.String(20))
    unit_name_snapshot = db.Column(db.String(50))
    conversion_factor_to_base = db.Column(db.Numeric(18, 6), nullable=False, default=1)

    # Snapshot the supplier's own representation of the item.
    supplier_item_code = db.Column(db.String(120), index=True)
    supplier_description = db.Column(db.String(500))

    batch_number = db.Column(db.String(100))
    manufacture_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)

    # Existing costs remain authoritative during compatibility migration.
    unit_cost = db.Column(db.Numeric(18, 2), nullable=False, default=0)
    base_unit_cost = db.Column(db.Numeric(18, 2), nullable=False, default=0)

    supplier_unit_price = db.Column(db.Numeric(18, 2))
    discount_percent = db.Column(db.Numeric(9, 4))
    discount_amount = db.Column(db.Numeric(18, 2))
    tax_rate = db.Column(db.Numeric(9, 4))
    tax_amount = db.Column(db.Numeric(18, 2))
    net_unit_cost = db.Column(db.Numeric(18, 2))
    line_total = db.Column(db.Numeric(18, 2))

    discrepancy_status = db.Column(db.String(30), index=True)
    discrepancy_reason = db.Column(db.String(500))

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
        db.Index(
            "uq_stock_counts_one_open_per_warehouse",
            "tenant_id",
            "warehouse_id",
            unique=True,
            postgresql_where=db.text("status = 'open'"),
            sqlite_where=db.text("status = 'open'"),
        ),
    )

    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id = db.Column(db.String(36), db.ForeignKey("branches.id"), nullable=False, index=True)
    warehouse_id = db.Column(db.String(36), db.ForeignKey("warehouses.id"), nullable=False, index=True)
    count_number = db.Column(db.String(50), nullable=False, index=True)
    idempotency_key = db.Column(db.String(120), nullable=False, index=True)
    request_fingerprint = db.Column(db.String(64), nullable=False)
    scope_type = db.Column(db.String(30), nullable=False, default="full")
    count_mode = db.Column(
        db.String(20),
        nullable=False,
        default="blind",
        index=True,
    )
    status = db.Column(db.String(30), nullable=False, default="open", index=True)
    snapshot_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    started_at = db.Column(db.DateTime(timezone=True), nullable=False)
    started_by = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    completed_at = db.Column(db.DateTime(timezone=True))
    completed_by = db.Column(db.String(36), db.ForeignKey("users.id"))
    cancelled_at = db.Column(db.DateTime(timezone=True))
    cancelled_by = db.Column(db.String(36), db.ForeignKey("users.id"))

    superseded_at = db.Column(db.DateTime(timezone=True))
    superseded_by = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        index=True,
    )
    superseded_reason = db.Column(db.Text)

    notes = db.Column(db.Text)


class StockCountScopeProduct(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    db.Model,
):
    """
    Persist one Product explicitly selected into a Stock Count scope.

    This is scope metadata, not physical inventory evidence.

    Snapshot and discovered quantities remain represented exclusively by
    StockCountItem.
    """

    __tablename__ = "stock_count_scope_products"
    __table_args__ = (
        db.UniqueConstraint(
            "stock_count_id",
            "product_id",
            name=(
                "uq_stock_count_scope_products_"
                "count_product"
            ),
        ),
    )

    stock_count_id = db.Column(
        db.String(36),
        db.ForeignKey("stock_counts.id"),
        nullable=False,
        index=True,
    )
    product_id = db.Column(
        db.String(36),
        db.ForeignKey("products.id"),
        nullable=False,
        index=True,
    )
    no_stock_confirmed_at = db.Column(
        db.DateTime(timezone=True),
    )
    no_stock_confirmed_by = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        index=True,
    )

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
        db.Index(
            "uq_stock_count_items_unbatched_count_product",
            "stock_count_id",
            "product_id",
            unique=True,
            postgresql_where=db.text(
                "batch_id IS NULL "
                "AND observed_batch_number IS NULL "
                "AND observed_expiry_date IS NULL"
            ),
            sqlite_where=db.text(
                "batch_id IS NULL "
                "AND observed_batch_number IS NULL "
                "AND observed_expiry_date IS NULL"
            ),
        ),
    )

    stock_count_id = db.Column(db.String(36), db.ForeignKey("stock_counts.id"), nullable=False, index=True)
    product_id = db.Column(db.String(36), db.ForeignKey("products.id"), nullable=False, index=True)
    batch_id = db.Column(db.String(36), db.ForeignKey("inventory_batches.id"), index=True)
    source_type = db.Column(
        db.String(20),
        nullable=False,
        default="snapshot",
        index=True,
    )
    observed_batch_number = db.Column(
        db.String(100),
        index=True,
    )
    observed_expiry_date = db.Column(
        db.Date,
        index=True,
    )
    line_number = db.Column(db.Integer, nullable=False)
    snapshot_quantity = db.Column(db.Numeric(18, 4), nullable=False, default=0)
    expected_quantity = db.Column(db.Numeric(18, 4), nullable=False, default=0)
    # Canonical/base quantity used for variance and inventory posting.
    counted_quantity = db.Column(db.Numeric(18, 4))

    # Preserve the counter's original physical entry representation.
    counted_unit_quantity = db.Column(db.Numeric(18, 4))
    counted_product_unit_id = db.Column(
        db.String(36),
        db.ForeignKey("product_units.id"),
        index=True,
    )
    counted_unit_code_snapshot = db.Column(db.String(20))
    counted_unit_name_snapshot = db.Column(db.String(50))
    counted_conversion_factor_to_base = db.Column(
        db.Numeric(18, 6),
    )

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
