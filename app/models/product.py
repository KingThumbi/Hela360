from app.extensions import db
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class ProductCategory(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "product_categories"
    __table_args__ = (
        db.UniqueConstraint("tenant_id", "name", name="uq_product_categories_tenant_name"),
    )

    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    parent_id = db.Column(db.String(36), db.ForeignKey("product_categories.id"))
    code = db.Column(db.String(50))
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, nullable=False, default=True)


class Brand(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "brands"
    __table_args__ = (
        db.UniqueConstraint("tenant_id", "name", name="uq_brands_tenant_name"),
    )

    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)


class UnitOfMeasure(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "units_of_measure"
    __table_args__ = (
        db.UniqueConstraint("tenant_id", "code", name="uq_units_tenant_code"),
    )

    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    code = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    base_factor = db.Column(db.Numeric(18, 6), nullable=False, default=1)


class Product(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "products"
    __table_args__ = (
        db.UniqueConstraint("tenant_id", "internal_sku", name="uq_products_tenant_internal_sku"),
        db.Index(
            "ix_products_one_master_item_per_tenant",
            "tenant_id",
            "master_item_id",
            unique=True,
            postgresql_where=db.text("master_item_id IS NOT NULL"),
        ),
    )

    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    category_id = db.Column(db.String(36), db.ForeignKey("product_categories.id"), index=True)
    brand_id = db.Column(db.String(36), db.ForeignKey("brands.id"), index=True)
    unit_id = db.Column(db.String(36), db.ForeignKey("units_of_measure.id"), index=True)

    master_item_id = db.Column(
        db.String(36),
        db.ForeignKey("master_items.id"),
        index=True,
    )

    internal_sku = db.Column(db.String(60), nullable=False)
    supplier_sku = db.Column(db.String(60))
    name = db.Column(db.String(200), nullable=False)
    generic_name = db.Column(db.String(200))
    description = db.Column(db.Text)

    product_type = db.Column(db.String(30), nullable=False, default="stockable")
    track_inventory = db.Column(db.Boolean, nullable=False, default=True)
    track_batches = db.Column(db.Boolean, nullable=False, default=False)
    track_expiry = db.Column(db.Boolean, nullable=False, default=False)
    requires_prescription = db.Column(db.Boolean, nullable=False, default=False)

    allow_negative_stock = db.Column(db.Boolean, nullable=False, default=False)
    reorder_level = db.Column(db.Numeric(18, 4), nullable=False, default=0)
    reorder_qty = db.Column(db.Numeric(18, 4), nullable=False, default=0)

    min_sale_price = db.Column(db.Numeric(18, 2))
    default_sale_price = db.Column(db.Numeric(18, 2))
    cost_price = db.Column(db.Numeric(18, 2))

    tax_code = db.Column(db.String(30))
    pack_size = db.Column(db.String(100))
    manufacturer = db.Column(db.String(150))
    country_of_origin = db.Column(db.String(100))
    image_url = db.Column(db.Text)

    is_active = db.Column(db.Boolean, nullable=False, default=True)


class ProductUnit(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "product_units"
    __table_args__ = (
        db.UniqueConstraint(
            "tenant_id",
            "product_id",
            "unit_id",
            name="uq_product_units_tenant_product_unit",
        ),
        db.Index(
            "ix_product_units_one_base_per_product",
            "tenant_id",
            "product_id",
            unique=True,
            postgresql_where=db.text("is_base = true"),
        ),
    )

    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )
    product_id = db.Column(
        db.String(36),
        db.ForeignKey("products.id"),
        nullable=False,
        index=True,
    )
    unit_id = db.Column(
        db.String(36),
        db.ForeignKey("units_of_measure.id"),
        nullable=False,
        index=True,
    )

    conversion_factor_to_base = db.Column(
        db.Numeric(18, 6),
        nullable=False,
        default=1,
    )
    is_base = db.Column(db.Boolean, nullable=False, default=False)
    can_sell = db.Column(db.Boolean, nullable=False, default=True)
    can_receive = db.Column(db.Boolean, nullable=False, default=True)
    sale_price = db.Column(db.Numeric(18, 2))
    minimum_sale_price = db.Column(db.Numeric(18, 2))
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    
class ProductCode(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "product_codes"
    __table_args__ = (
        db.UniqueConstraint("tenant_id", "code_value", name="uq_product_codes_tenant_code_value"),
    )

    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    product_id = db.Column(db.String(36), db.ForeignKey("products.id"), nullable=False, index=True)
    product_unit_id = db.Column(db.String(36), db.ForeignKey("product_units.id"), index=True)

    code_type = db.Column(db.String(20), nullable=False)
    code_value = db.Column(db.String(200), nullable=False)
    is_primary = db.Column(db.Boolean, nullable=False, default=False)
    generated_by_system = db.Column(db.Boolean, nullable=False, default=False)
