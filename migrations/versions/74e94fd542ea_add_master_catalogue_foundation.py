"""add master catalogue foundation

Revision ID: 74e94fd542ea
Revises: 52bde25d92a6
Create Date: 2026-08-29 22:18:04.147822

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "74e94fd542ea"
down_revision = "52bde25d92a6"
branch_labels = None
depends_on = None


def upgrade():
    # ------------------------------------------------------------------
    # Catalogue suppliers
    # ------------------------------------------------------------------

    op.create_table(
        "catalogue_suppliers",
        sa.Column(
            "name",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "normalized_name",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "country",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "id",
        ),
        sa.UniqueConstraint(
            "normalized_name",
            name="uq_catalogue_suppliers_normalized_name",
        ),
    )

    op.create_index(
        "ix_catalogue_suppliers_is_active",
        "catalogue_suppliers",
        ["is_active"],
        unique=False,
    )

    op.create_index(
        "ix_catalogue_suppliers_normalized_name",
        "catalogue_suppliers",
        ["normalized_name"],
        unique=False,
    )

    # ------------------------------------------------------------------
    # Master items
    # ------------------------------------------------------------------

    op.create_table(
        "master_items",
        sa.Column(
            "master_code",
            sa.String(length=60),
            nullable=False,
        ),
        sa.Column(
            "canonical_name",
            sa.String(length=250),
            nullable=False,
        ),
        sa.Column(
            "brand_name",
            sa.String(length=150),
            nullable=True,
        ),
        sa.Column(
            "generic_name",
            sa.String(length=500),
            nullable=True,
        ),
        sa.Column(
            "strength",
            sa.String(length=150),
            nullable=True,
        ),
        sa.Column(
            "dosage_form",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "pack_quantity",
            sa.Numeric(
                precision=18,
                scale=6,
            ),
            nullable=True,
        ),
        sa.Column(
            "pack_unit",
            sa.String(length=50),
            nullable=True,
        ),
        sa.Column(
            "pack_type",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "item_class",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "category_name",
            sa.String(length=150),
            nullable=True,
        ),
        sa.Column(
            "subcategory_name",
            sa.String(length=150),
            nullable=True,
        ),
        sa.Column(
            "manufacturer",
            sa.String(length=200),
            nullable=True,
        ),
        sa.Column(
            "country_of_origin",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "cold_chain",
            sa.Boolean(),
            nullable=True,
        ),
        sa.Column(
            "restricted_item",
            sa.Boolean(),
            nullable=True,
        ),
        sa.Column(
            "requires_prescription",
            sa.Boolean(),
            nullable=True,
        ),
        sa.Column(
            "tax_classification",
            sa.String(length=50),
            nullable=True,
        ),
        sa.Column(
            "review_status",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "id",
        ),
        sa.UniqueConstraint(
            "master_code",
            name="uq_master_items_master_code",
        ),
    )

    op.create_index(
        "ix_master_items_canonical_name",
        "master_items",
        ["canonical_name"],
        unique=False,
    )

    op.create_index(
        "ix_master_items_category_name",
        "master_items",
        ["category_name"],
        unique=False,
    )

    op.create_index(
        "ix_master_items_dosage_form",
        "master_items",
        ["dosage_form"],
        unique=False,
    )

    op.create_index(
        "ix_master_items_is_active",
        "master_items",
        ["is_active"],
        unique=False,
    )

    op.create_index(
        "ix_master_items_item_class",
        "master_items",
        ["item_class"],
        unique=False,
    )

    op.create_index(
        "ix_master_items_master_code",
        "master_items",
        ["master_code"],
        unique=False,
    )

    op.create_index(
        "ix_master_items_review_status",
        "master_items",
        ["review_status"],
        unique=False,
    )

    # ------------------------------------------------------------------
    # Supplier mappings
    # ------------------------------------------------------------------

    op.create_table(
        "master_item_supplier_mappings",
        sa.Column(
            "master_item_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "catalogue_supplier_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "supplier_item_code",
            sa.String(length=120),
            nullable=True,
        ),
        sa.Column(
            "supplier_item_name",
            sa.String(length=300),
            nullable=False,
        ),
        sa.Column(
            "source_description",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["catalogue_supplier_id"],
            ["catalogue_suppliers.id"],
            name="fk_mism_catalogue_supplier",
        ),
        sa.ForeignKeyConstraint(
            ["master_item_id"],
            ["master_items.id"],
            name="fk_mism_master_item",
        ),
        sa.PrimaryKeyConstraint(
            "id",
        ),
        sa.UniqueConstraint(
            "catalogue_supplier_id",
            "supplier_item_code",
            name=(
                "uq_master_item_supplier_mappings_"
                "supplier_item_code"
            ),
        ),
    )

    op.create_index(
        "ix_master_item_supplier_mappings_catalogue_supplier_id",
        "master_item_supplier_mappings",
        ["catalogue_supplier_id"],
        unique=False,
    )

    op.create_index(
        "ix_master_item_supplier_mappings_is_active",
        "master_item_supplier_mappings",
        ["is_active"],
        unique=False,
    )

    op.create_index(
        "ix_master_item_supplier_mappings_master_item_id",
        "master_item_supplier_mappings",
        ["master_item_id"],
        unique=False,
    )

    # ------------------------------------------------------------------
    # Supplier price history
    # ------------------------------------------------------------------

    op.create_table(
        "supplier_item_prices",
        sa.Column(
            "supplier_mapping_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "price_type",
            sa.String(length=40),
            nullable=False,
        ),
        sa.Column(
            "amount",
            sa.Numeric(
                precision=18,
                scale=2,
            ),
            nullable=False,
        ),
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
        ),
        sa.Column(
            "discount_percent",
            sa.Numeric(
                precision=9,
                scale=4,
            ),
            nullable=True,
        ),
        sa.Column(
            "vat_source",
            sa.String(length=50),
            nullable=True,
        ),
        sa.Column(
            "effective_date",
            sa.Date(),
            nullable=True,
        ),
        sa.Column(
            "source_document",
            sa.String(length=300),
            nullable=True,
        ),
        sa.Column(
            "source_location",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "is_comparable_procurement",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["supplier_mapping_id"],
            ["master_item_supplier_mappings.id"],
            name="fk_supplier_prices_mapping",
        ),
        sa.PrimaryKeyConstraint(
            "id",
        ),
    )

    op.create_index(
        "ix_supplier_item_prices_effective_date",
        "supplier_item_prices",
        ["effective_date"],
        unique=False,
    )

    op.create_index(
        "ix_supplier_item_prices_price_type",
        "supplier_item_prices",
        ["price_type"],
        unique=False,
    )

    op.create_index(
        "ix_supplier_item_prices_supplier_mapping_id",
        "supplier_item_prices",
        ["supplier_mapping_id"],
        unique=False,
    )

    # ------------------------------------------------------------------
    # Tenant Product → MasterItem linkage
    # ------------------------------------------------------------------

    with op.batch_alter_table(
        "products",
        schema=None,
    ) as batch_op:
        batch_op.add_column(
            sa.Column(
                "master_item_id",
                sa.String(length=36),
                nullable=True,
            )
        )

        batch_op.create_index(
            "ix_products_master_item_id",
            ["master_item_id"],
            unique=False,
        )

        batch_op.create_foreign_key(
            "fk_products_master_item_id_master_items",
            "master_items",
            ["master_item_id"],
            ["id"],
        )

    # ------------------------------------------------------------------
    # One MasterItem may be adopted only once per tenant.
    #
    # Multiple tenant-only Products remain valid because PostgreSQL excludes
    # rows where master_item_id IS NULL from this partial unique index.
    # ------------------------------------------------------------------

    op.create_index(
        "ix_products_one_master_item_per_tenant",
        "products",
        [
            "tenant_id",
            "master_item_id",
        ],
        unique=True,
        postgresql_where=sa.text(
            "master_item_id IS NOT NULL"
        ),
    )


def downgrade():
    # ------------------------------------------------------------------
    # Product → MasterItem linkage
    # ------------------------------------------------------------------

    op.drop_index(
        "ix_products_one_master_item_per_tenant",
        table_name="products",
    )

    with op.batch_alter_table(
        "products",
        schema=None,
    ) as batch_op:
        batch_op.drop_constraint(
            "fk_products_master_item_id_master_items",
            type_="foreignkey",
        )

        batch_op.drop_index(
            "ix_products_master_item_id",
        )

        batch_op.drop_column(
            "master_item_id",
        )

    # ------------------------------------------------------------------
    # Supplier price history
    # ------------------------------------------------------------------

    op.drop_index(
        "ix_supplier_item_prices_supplier_mapping_id",
        table_name="supplier_item_prices",
    )

    op.drop_index(
        "ix_supplier_item_prices_price_type",
        table_name="supplier_item_prices",
    )

    op.drop_index(
        "ix_supplier_item_prices_effective_date",
        table_name="supplier_item_prices",
    )

    op.drop_table(
        "supplier_item_prices",
    )

    # ------------------------------------------------------------------
    # Supplier mappings
    # ------------------------------------------------------------------

    op.drop_index(
        "ix_master_item_supplier_mappings_master_item_id",
        table_name="master_item_supplier_mappings",
    )

    op.drop_index(
        "ix_master_item_supplier_mappings_is_active",
        table_name="master_item_supplier_mappings",
    )

    op.drop_index(
        "ix_master_item_supplier_mappings_catalogue_supplier_id",
        table_name="master_item_supplier_mappings",
    )

    op.drop_table(
        "master_item_supplier_mappings",
    )

    # ------------------------------------------------------------------
    # Master items
    # ------------------------------------------------------------------

    op.drop_index(
        "ix_master_items_review_status",
        table_name="master_items",
    )

    op.drop_index(
        "ix_master_items_master_code",
        table_name="master_items",
    )

    op.drop_index(
        "ix_master_items_item_class",
        table_name="master_items",
    )

    op.drop_index(
        "ix_master_items_is_active",
        table_name="master_items",
    )

    op.drop_index(
        "ix_master_items_dosage_form",
        table_name="master_items",
    )

    op.drop_index(
        "ix_master_items_category_name",
        table_name="master_items",
    )

    op.drop_index(
        "ix_master_items_canonical_name",
        table_name="master_items",
    )

    op.drop_table(
        "master_items",
    )

    # ------------------------------------------------------------------
    # Catalogue suppliers
    # ------------------------------------------------------------------

    op.drop_index(
        "ix_catalogue_suppliers_normalized_name",
        table_name="catalogue_suppliers",
    )

    op.drop_index(
        "ix_catalogue_suppliers_is_active",
        table_name="catalogue_suppliers",
    )

    op.drop_table(
        "catalogue_suppliers",
    )