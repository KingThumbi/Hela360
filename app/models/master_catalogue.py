"""
Hela360 Master Catalogue Models
===============================

Platform-wide canonical catalogue identities and supplier source mappings.

Architectural boundaries
------------------------
The master catalogue is platform-owned, not tenant-owned.

A MasterItem describes what an item is.

A tenant Product remains the operational entity for:

* POS
* inventory
* procurement
* tenant pricing
* tenant SKU
* tenant categories and brands
* stock, batches and expiry

Supplier catalogue mappings preserve external distributor identity and
historical pricing without turning supplier prices into canonical item data.
"""

from app.extensions import db
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class MasterItem(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    """
    Platform-wide canonical item identity.

    This model intentionally has no tenant_id.
    """

    __tablename__ = "master_items"
    __table_args__ = (
        db.UniqueConstraint(
            "master_code",
            name="uq_master_items_master_code",
        ),
    )

    master_code = db.Column(
        db.String(60),
        nullable=False,
        index=True,
    )

    canonical_name = db.Column(
        db.String(250),
        nullable=False,
        index=True,
    )

    brand_name = db.Column(
        db.String(150),
    )

    generic_name = db.Column(
        db.String(500),
    )

    strength = db.Column(
        db.String(150),
    )

    dosage_form = db.Column(
        db.String(100),
        index=True,
    )

    pack_quantity = db.Column(
        db.Numeric(18, 6),
    )

    pack_unit = db.Column(
        db.String(50),
    )

    pack_type = db.Column(
        db.String(100),
    )

    item_class = db.Column(
        db.String(100),
        index=True,
    )

    category_name = db.Column(
        db.String(150),
        index=True,
    )

    subcategory_name = db.Column(
        db.String(150),
    )

    manufacturer = db.Column(
        db.String(200),
    )

    country_of_origin = db.Column(
        db.String(100),
    )

    cold_chain = db.Column(
        db.Boolean,
    )

    restricted_item = db.Column(
        db.Boolean,
    )

    requires_prescription = db.Column(
        db.Boolean,
    )

    tax_classification = db.Column(
        db.String(50),
    )

    review_status = db.Column(
        db.String(30),
        nullable=False,
        default="draft",
        index=True,
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        index=True,
    )


class CatalogueSupplier(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    """
    Platform catalogue supplier identity.

    This is deliberately separate from tenant-owned Supplier records.
    """

    __tablename__ = "catalogue_suppliers"
    __table_args__ = (
        db.UniqueConstraint(
            "normalized_name",
            name="uq_catalogue_suppliers_normalized_name",
        ),
    )

    name = db.Column(
        db.String(200),
        nullable=False,
    )

    normalized_name = db.Column(
        db.String(200),
        nullable=False,
        index=True,
    )

    country = db.Column(
        db.String(100),
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        index=True,
    )


class MasterItemSupplierMapping(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    db.Model,
):
    """
    Map one supplier catalogue listing to a canonical MasterItem.
    """

    __tablename__ = "master_item_supplier_mappings"
    __table_args__ = (
        db.UniqueConstraint(
            "catalogue_supplier_id",
            "supplier_item_code",
            name=(
                "uq_master_item_supplier_mappings_"
                "supplier_item_code"
            ),
        ),
    )

    master_item_id = db.Column(
        db.String(36),
        db.ForeignKey("master_items.id"),
        nullable=False,
        index=True,
    )

    catalogue_supplier_id = db.Column(
        db.String(36),
        db.ForeignKey("catalogue_suppliers.id"),
        nullable=False,
        index=True,
    )

    supplier_item_code = db.Column(
        db.String(120),
    )

    supplier_item_name = db.Column(
        db.String(300),
        nullable=False,
    )

    source_description = db.Column(
        db.Text,
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        index=True,
    )


class SupplierItemPrice(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    db.Model,
):
    """
    Dated supplier price evidence for one supplier item mapping.
    """

    __tablename__ = "supplier_item_prices"

    supplier_mapping_id = db.Column(
        db.String(36),
        db.ForeignKey("master_item_supplier_mappings.id"),
        nullable=False,
        index=True,
    )

    source_offer_key = db.Column(
        db.String(60),
        unique=True,
        index=True,
    )

    price_type = db.Column(
        db.String(40),
        nullable=False,
        index=True,
    )

    amount = db.Column(
        db.Numeric(18, 2),
        nullable=False,
    )

    currency = db.Column(
        db.String(3),
        nullable=False,
        default="KES",
    )

    discount_percent = db.Column(
        db.Numeric(9, 4),
    )

    vat_source = db.Column(
        db.String(50),
    )

    effective_date = db.Column(
        db.Date,
        index=True,
    )

    source_document = db.Column(
        db.String(300),
    )

    source_location = db.Column(
        db.String(100),
    )

    is_comparable_procurement = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )
