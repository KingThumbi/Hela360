"""Add stock adjustments

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "stock_adjustments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("branch_id", sa.String(length=36), nullable=False),
        sa.Column("warehouse_id", sa.String(length=36), nullable=False),
        sa.Column("adjustment_number", sa.String(length=50), nullable=False),
        sa.Column("reason_code", sa.String(length=40), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("source_type", sa.String(length=40), nullable=False),
        sa.Column("source_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("idempotency_key", sa.String(length=120), nullable=False),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("posted_by", sa.String(length=36), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.ForeignKeyConstraint(["posted_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "adjustment_number",
            name="uq_stock_adjustments_tenant_adjustment_number",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "idempotency_key",
            name="uq_stock_adjustments_tenant_idempotency_key",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "source_type",
            "source_id",
            name="uq_stock_adjustments_tenant_source",
        ),
    )
    op.create_index(op.f("ix_stock_adjustments_adjustment_number"), "stock_adjustments", ["adjustment_number"])
    op.create_index(op.f("ix_stock_adjustments_branch_id"), "stock_adjustments", ["branch_id"])
    op.create_index(op.f("ix_stock_adjustments_idempotency_key"), "stock_adjustments", ["idempotency_key"])
    op.create_index(op.f("ix_stock_adjustments_posted_at"), "stock_adjustments", ["posted_at"])
    op.create_index(op.f("ix_stock_adjustments_posted_by"), "stock_adjustments", ["posted_by"])
    op.create_index(op.f("ix_stock_adjustments_reason_code"), "stock_adjustments", ["reason_code"])
    op.create_index(op.f("ix_stock_adjustments_source_id"), "stock_adjustments", ["source_id"])
    op.create_index(op.f("ix_stock_adjustments_source_type"), "stock_adjustments", ["source_type"])
    op.create_index(op.f("ix_stock_adjustments_status"), "stock_adjustments", ["status"])
    op.create_index(op.f("ix_stock_adjustments_tenant_id"), "stock_adjustments", ["tenant_id"])
    op.create_index(op.f("ix_stock_adjustments_warehouse_id"), "stock_adjustments", ["warehouse_id"])

    op.create_table(
        "stock_adjustment_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("stock_adjustment_id", sa.String(length=36), nullable=False),
        sa.Column("product_id", sa.String(length=36), nullable=False),
        sa.Column("batch_id", sa.String(length=36), nullable=True),
        sa.Column("stock_count_item_id", sa.String(length=36), nullable=True),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("quantity_delta", sa.Numeric(18, 4), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["inventory_batches.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["stock_adjustment_id"], ["stock_adjustments.id"]),
        sa.ForeignKeyConstraint(["stock_count_item_id"], ["stock_count_items.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "stock_adjustment_id",
            "line_number",
            name="uq_stock_adjustment_items_adjustment_line",
        ),
        sa.UniqueConstraint(
            "stock_adjustment_id",
            "product_id",
            "batch_id",
            name="uq_stock_adjustment_items_adjustment_product_batch",
        ),
    )
    op.create_index(op.f("ix_stock_adjustment_items_batch_id"), "stock_adjustment_items", ["batch_id"])
    op.create_index(op.f("ix_stock_adjustment_items_product_id"), "stock_adjustment_items", ["product_id"])
    op.create_index(op.f("ix_stock_adjustment_items_stock_adjustment_id"), "stock_adjustment_items", ["stock_adjustment_id"])
    op.create_index(op.f("ix_stock_adjustment_items_stock_count_item_id"), "stock_adjustment_items", ["stock_count_item_id"])

    op.execute(
        sa.text(
            """
            INSERT INTO permissions (id, code, name, module_code, description)
            VALUES (
                'perm-inventory-adjust',
                'inventory.adjust',
                'Inventory Adjust',
                'inventory',
                'Post auditable stock quantity adjustments.'
            )
            ON CONFLICT (code) DO NOTHING
            """
        )
    )


def downgrade():
    op.execute(sa.text("DELETE FROM permissions WHERE code = 'inventory.adjust'"))
    op.drop_index(op.f("ix_stock_adjustment_items_stock_count_item_id"), table_name="stock_adjustment_items")
    op.drop_index(op.f("ix_stock_adjustment_items_stock_adjustment_id"), table_name="stock_adjustment_items")
    op.drop_index(op.f("ix_stock_adjustment_items_product_id"), table_name="stock_adjustment_items")
    op.drop_index(op.f("ix_stock_adjustment_items_batch_id"), table_name="stock_adjustment_items")
    op.drop_table("stock_adjustment_items")
    op.drop_index(op.f("ix_stock_adjustments_warehouse_id"), table_name="stock_adjustments")
    op.drop_index(op.f("ix_stock_adjustments_tenant_id"), table_name="stock_adjustments")
    op.drop_index(op.f("ix_stock_adjustments_status"), table_name="stock_adjustments")
    op.drop_index(op.f("ix_stock_adjustments_source_type"), table_name="stock_adjustments")
    op.drop_index(op.f("ix_stock_adjustments_source_id"), table_name="stock_adjustments")
    op.drop_index(op.f("ix_stock_adjustments_reason_code"), table_name="stock_adjustments")
    op.drop_index(op.f("ix_stock_adjustments_posted_by"), table_name="stock_adjustments")
    op.drop_index(op.f("ix_stock_adjustments_posted_at"), table_name="stock_adjustments")
    op.drop_index(op.f("ix_stock_adjustments_idempotency_key"), table_name="stock_adjustments")
    op.drop_index(op.f("ix_stock_adjustments_branch_id"), table_name="stock_adjustments")
    op.drop_index(op.f("ix_stock_adjustments_adjustment_number"), table_name="stock_adjustments")
    op.drop_table("stock_adjustments")
