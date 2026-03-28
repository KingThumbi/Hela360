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
    movement_type = db.Column(db.String(40), nullable=False, index=True)
    quantity = db.Column(db.Numeric(18, 4), nullable=False)
    unit_cost = db.Column(db.Numeric(18, 2))
    unit_price = db.Column(db.Numeric(18, 2))
    reference_type = db.Column(db.String(50), nullable=False, index=True)
    reference_id = db.Column(db.String(36), nullable=False, index=True)
    notes = db.Column(db.Text)
    created_by = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)