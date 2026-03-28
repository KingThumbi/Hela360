"""add sale refunds

Revision ID: 8fc9a0626e01
Revises: ee59b6fce6e4
Create Date: 2026-03-22 00:23:46.047735

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8fc9a0626e01'
down_revision = 'ee59b6fce6e4'
branch_labels = None
depends_on = None



def upgrade():
    op.add_column(
        "sales",
        sa.Column("refunded_amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
    )
    op.add_column(
        "sales",
        sa.Column("refund_status", sa.String(length=20), nullable=False, server_default="not_refunded"),
    )

    op.create_table(
        "sale_refunds",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),

        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("sale_id", sa.String(length=36), nullable=False),
        sa.Column("branch_id", sa.String(length=36), nullable=False),
        sa.Column("warehouse_id", sa.String(length=36), nullable=False),
        sa.Column("till_id", sa.String(length=36), nullable=False),
        sa.Column("cashier_id", sa.String(length=36), nullable=False),
        sa.Column("customer_id", sa.String(length=36), nullable=True),

        sa.Column("refund_number", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="posted"),

        sa.Column("refund_subtotal", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("refund_discount_amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("refund_tax_amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("refund_total_amount", sa.Numeric(18, 2), nullable=False, server_default="0"),

        sa.Column("stock_returned", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),

        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"]),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"]),
        sa.ForeignKeyConstraint(["till_id"], ["tills.id"]),
        sa.ForeignKeyConstraint(["cashier_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "refund_number", name="uq_sale_refunds_tenant_refund_number"),
    )

    op.create_index("ix_sale_refunds_tenant_id", "sale_refunds", ["tenant_id"])
    op.create_index("ix_sale_refunds_sale_id", "sale_refunds", ["sale_id"])
    op.create_index("ix_sale_refunds_branch_id", "sale_refunds", ["branch_id"])
    op.create_index("ix_sale_refunds_warehouse_id", "sale_refunds", ["warehouse_id"])
    op.create_index("ix_sale_refunds_till_id", "sale_refunds", ["till_id"])
    op.create_index("ix_sale_refunds_cashier_id", "sale_refunds", ["cashier_id"])

    op.create_table(
        "sale_refund_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),

        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("refund_id", sa.String(length=36), nullable=False),
        sa.Column("sale_id", sa.String(length=36), nullable=False),
        sa.Column("sale_item_id", sa.String(length=36), nullable=False),
        sa.Column("product_id", sa.String(length=36), nullable=False),
        sa.Column("batch_id", sa.String(length=36), nullable=True),

        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("unit_price", sa.Numeric(18, 2), nullable=False),
        sa.Column("discount_amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("tax_amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("line_total", sa.Numeric(18, 2), nullable=False),

        sa.Column("return_to_stock", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("condition_note", sa.Text(), nullable=True),

        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["refund_id"], ["sale_refunds.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"]),
        sa.ForeignKeyConstraint(["sale_item_id"], ["sale_items.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["batch_id"], ["inventory_batches.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_sale_refund_items_tenant_id", "sale_refund_items", ["tenant_id"])
    op.create_index("ix_sale_refund_items_refund_id", "sale_refund_items", ["refund_id"])
    op.create_index("ix_sale_refund_items_sale_id", "sale_refund_items", ["sale_id"])
    op.create_index("ix_sale_refund_items_sale_item_id", "sale_refund_items", ["sale_item_id"])
    op.create_index("ix_sale_refund_items_product_id", "sale_refund_items", ["product_id"])
    op.create_index("ix_sale_refund_items_batch_id", "sale_refund_items", ["batch_id"])

    op.alter_column("sales", "refunded_amount", server_default=None)
    op.alter_column("sales", "refund_status", server_default=None)


def downgrade():
    op.drop_index("ix_sale_refund_items_batch_id", table_name="sale_refund_items")
    op.drop_index("ix_sale_refund_items_product_id", table_name="sale_refund_items")
    op.drop_index("ix_sale_refund_items_sale_item_id", table_name="sale_refund_items")
    op.drop_index("ix_sale_refund_items_sale_id", table_name="sale_refund_items")
    op.drop_index("ix_sale_refund_items_refund_id", table_name="sale_refund_items")
    op.drop_index("ix_sale_refund_items_tenant_id", table_name="sale_refund_items")
    op.drop_table("sale_refund_items")

    op.drop_index("ix_sale_refunds_cashier_id", table_name="sale_refunds")
    op.drop_index("ix_sale_refunds_till_id", table_name="sale_refunds")
    op.drop_index("ix_sale_refunds_warehouse_id", table_name="sale_refunds")
    op.drop_index("ix_sale_refunds_branch_id", table_name="sale_refunds")
    op.drop_index("ix_sale_refunds_sale_id", table_name="sale_refunds")
    op.drop_index("ix_sale_refunds_tenant_id", table_name="sale_refunds")
    op.drop_table("sale_refunds")

    op.drop_column("sales", "refund_status")
    op.drop_column("sales", "refunded_amount")