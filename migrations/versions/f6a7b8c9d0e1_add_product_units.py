"""Add product units for pharmacy pack conversions

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-08-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "product_units",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("product_id", sa.String(length=36), nullable=False),
        sa.Column("unit_id", sa.String(length=36), nullable=False),
        sa.Column("conversion_factor_to_base", sa.Numeric(18, 6), nullable=False),
        sa.Column("is_base", sa.Boolean(), nullable=False),
        sa.Column("can_sell", sa.Boolean(), nullable=False),
        sa.Column("can_receive", sa.Boolean(), nullable=False),
        sa.Column("sale_price", sa.Numeric(18, 2), nullable=True),
        sa.Column("minimum_sale_price", sa.Numeric(18, 2), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["unit_id"], ["units_of_measure.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "product_id",
            "unit_id",
            name="uq_product_units_tenant_product_unit",
        ),
    )
    op.create_index(op.f("ix_product_units_product_id"), "product_units", ["product_id"])
    op.create_index(op.f("ix_product_units_tenant_id"), "product_units", ["tenant_id"])
    op.create_index(op.f("ix_product_units_unit_id"), "product_units", ["unit_id"])
    op.create_index(
        "ix_product_units_one_base_per_product",
        "product_units",
        ["tenant_id", "product_id"],
        unique=True,
        postgresql_where=sa.text("is_base = true"),
    )

    op.add_column("product_codes", sa.Column("product_unit_id", sa.String(length=36), nullable=True))
    op.create_index(op.f("ix_product_codes_product_unit_id"), "product_codes", ["product_unit_id"])
    op.create_foreign_key(
        "fk_product_codes_product_unit_id_product_units",
        "product_codes",
        "product_units",
        ["product_unit_id"],
        ["id"],
    )

    op.add_column("goods_receipt_items", sa.Column("product_unit_id", sa.String(length=36), nullable=True))
    op.add_column("goods_receipt_items", sa.Column("base_quantity", sa.Numeric(18, 4), nullable=True))
    op.add_column("goods_receipt_items", sa.Column("unit_code_snapshot", sa.String(length=20), nullable=True))
    op.add_column("goods_receipt_items", sa.Column("unit_name_snapshot", sa.String(length=50), nullable=True))
    op.add_column("goods_receipt_items", sa.Column("conversion_factor_to_base", sa.Numeric(18, 6), nullable=True))
    op.add_column("goods_receipt_items", sa.Column("base_unit_cost", sa.Numeric(18, 2), nullable=True))
    op.create_index(op.f("ix_goods_receipt_items_product_unit_id"), "goods_receipt_items", ["product_unit_id"])
    op.create_foreign_key(
        "fk_goods_receipt_items_product_unit_id_product_units",
        "goods_receipt_items",
        "product_units",
        ["product_unit_id"],
        ["id"],
    )

    op.add_column("sale_items", sa.Column("product_unit_id", sa.String(length=36), nullable=True))
    op.add_column("sale_items", sa.Column("base_quantity", sa.Numeric(18, 4), nullable=True))
    op.add_column("sale_items", sa.Column("unit_code_snapshot", sa.String(length=20), nullable=True))
    op.add_column("sale_items", sa.Column("unit_name_snapshot", sa.String(length=50), nullable=True))
    op.add_column("sale_items", sa.Column("conversion_factor_to_base", sa.Numeric(18, 6), nullable=True))
    op.create_index(op.f("ix_sale_items_product_unit_id"), "sale_items", ["product_unit_id"])
    op.create_foreign_key(
        "fk_sale_items_product_unit_id_product_units",
        "sale_items",
        "product_units",
        ["product_unit_id"],
        ["id"],
    )

    op.add_column("sale_refund_items", sa.Column("base_quantity", sa.Numeric(18, 4), nullable=True))

    op.execute(
        sa.text(
            """
            INSERT INTO product_units (
                id,
                tenant_id,
                product_id,
                unit_id,
                conversion_factor_to_base,
                is_base,
                can_sell,
                can_receive,
                sale_price,
                minimum_sale_price,
                is_active,
                created_at,
                updated_at
            )
            SELECT
                md5(products.id || products.unit_id),
                products.tenant_id,
                products.id,
                products.unit_id,
                1,
                true,
                true,
                true,
                products.default_sale_price,
                products.min_sale_price,
                true,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            FROM products
            WHERE products.unit_id IS NOT NULL
            ON CONFLICT (tenant_id, product_id, unit_id) DO NOTHING
            """
        )
    )
    op.execute(sa.text("UPDATE goods_receipt_items SET base_quantity = quantity WHERE base_quantity IS NULL"))
    op.execute(sa.text("UPDATE goods_receipt_items SET conversion_factor_to_base = 1 WHERE conversion_factor_to_base IS NULL"))
    op.execute(sa.text("UPDATE goods_receipt_items SET base_unit_cost = unit_cost WHERE base_unit_cost IS NULL"))
    op.execute(sa.text("UPDATE sale_items SET base_quantity = quantity WHERE base_quantity IS NULL"))
    op.execute(sa.text("UPDATE sale_items SET conversion_factor_to_base = 1 WHERE conversion_factor_to_base IS NULL"))
    op.execute(sa.text("UPDATE sale_refund_items SET base_quantity = quantity WHERE base_quantity IS NULL"))

    op.alter_column("goods_receipt_items", "base_quantity", nullable=False)
    op.alter_column("goods_receipt_items", "conversion_factor_to_base", nullable=False)
    op.alter_column("goods_receipt_items", "base_unit_cost", nullable=False)
    op.alter_column("sale_items", "base_quantity", nullable=False)
    op.alter_column("sale_items", "conversion_factor_to_base", nullable=False)
    op.alter_column("sale_refund_items", "base_quantity", nullable=False)


def downgrade():
    op.alter_column("sale_refund_items", "base_quantity", nullable=True)
    op.drop_column("sale_refund_items", "base_quantity")

    op.drop_constraint("fk_sale_items_product_unit_id_product_units", "sale_items", type_="foreignkey")
    op.drop_index(op.f("ix_sale_items_product_unit_id"), table_name="sale_items")
    op.drop_column("sale_items", "conversion_factor_to_base")
    op.drop_column("sale_items", "unit_name_snapshot")
    op.drop_column("sale_items", "unit_code_snapshot")
    op.drop_column("sale_items", "base_quantity")
    op.drop_column("sale_items", "product_unit_id")

    op.drop_constraint("fk_goods_receipt_items_product_unit_id_product_units", "goods_receipt_items", type_="foreignkey")
    op.drop_index(op.f("ix_goods_receipt_items_product_unit_id"), table_name="goods_receipt_items")
    op.drop_column("goods_receipt_items", "base_unit_cost")
    op.drop_column("goods_receipt_items", "conversion_factor_to_base")
    op.drop_column("goods_receipt_items", "unit_name_snapshot")
    op.drop_column("goods_receipt_items", "unit_code_snapshot")
    op.drop_column("goods_receipt_items", "base_quantity")
    op.drop_column("goods_receipt_items", "product_unit_id")

    op.drop_constraint("fk_product_codes_product_unit_id_product_units", "product_codes", type_="foreignkey")
    op.drop_index(op.f("ix_product_codes_product_unit_id"), table_name="product_codes")
    op.drop_column("product_codes", "product_unit_id")

    op.drop_index("ix_product_units_one_base_per_product", table_name="product_units")
    op.drop_index(op.f("ix_product_units_unit_id"), table_name="product_units")
    op.drop_index(op.f("ix_product_units_tenant_id"), table_name="product_units")
    op.drop_index(op.f("ix_product_units_product_id"), table_name="product_units")
    op.drop_table("product_units")
