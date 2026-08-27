"""Add goods receipts

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-08-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint(
        "uq_inventory_batches_tenant_warehouse_product_batch",
        "inventory_batches",
        ["tenant_id", "warehouse_id", "product_id", "batch_number"],
    )

    op.create_table(
        "goods_receipts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("branch_id", sa.String(length=36), nullable=False),
        sa.Column("warehouse_id", sa.String(length=36), nullable=False),
        sa.Column("supplier_id", sa.String(length=36), nullable=True),
        sa.Column("receipt_number", sa.String(length=50), nullable=False),
        sa.Column("supplier_reference", sa.String(length=120), nullable=True),
        sa.Column("idempotency_key", sa.String(length=120), nullable=False),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("received_by", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.ForeignKeyConstraint(["received_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "idempotency_key",
            name="uq_goods_receipts_tenant_idempotency_key",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "receipt_number",
            name="uq_goods_receipts_tenant_receipt_number",
        ),
    )
    op.create_index(
        op.f("ix_goods_receipts_branch_id"),
        "goods_receipts",
        ["branch_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_goods_receipts_idempotency_key"),
        "goods_receipts",
        ["idempotency_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_goods_receipts_received_at"),
        "goods_receipts",
        ["received_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_goods_receipts_received_by"),
        "goods_receipts",
        ["received_by"],
        unique=False,
    )
    op.create_index(
        op.f("ix_goods_receipts_receipt_number"),
        "goods_receipts",
        ["receipt_number"],
        unique=False,
    )
    op.create_index(
        op.f("ix_goods_receipts_status"),
        "goods_receipts",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_goods_receipts_supplier_id"),
        "goods_receipts",
        ["supplier_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_goods_receipts_tenant_id"),
        "goods_receipts",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_goods_receipts_warehouse_id"),
        "goods_receipts",
        ["warehouse_id"],
        unique=False,
    )

    op.create_table(
        "goods_receipt_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("goods_receipt_id", sa.String(length=36), nullable=False),
        sa.Column("product_id", sa.String(length=36), nullable=False),
        sa.Column("batch_id", sa.String(length=36), nullable=True),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("batch_number", sa.String(length=100), nullable=True),
        sa.Column("manufacture_date", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("unit_cost", sa.Numeric(18, 2), nullable=False),
        sa.Column("supplier_batch_reference", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["inventory_batches.id"]),
        sa.ForeignKeyConstraint(["goods_receipt_id"], ["goods_receipts.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "goods_receipt_id",
            "line_number",
            name="uq_goods_receipt_items_receipt_line",
        ),
    )
    op.create_index(
        op.f("ix_goods_receipt_items_batch_id"),
        "goods_receipt_items",
        ["batch_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_goods_receipt_items_goods_receipt_id"),
        "goods_receipt_items",
        ["goods_receipt_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_goods_receipt_items_product_id"),
        "goods_receipt_items",
        ["product_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_goods_receipt_items_product_id"),
        table_name="goods_receipt_items",
    )
    op.drop_index(
        op.f("ix_goods_receipt_items_goods_receipt_id"),
        table_name="goods_receipt_items",
    )
    op.drop_index(
        op.f("ix_goods_receipt_items_batch_id"),
        table_name="goods_receipt_items",
    )
    op.drop_table("goods_receipt_items")
    op.drop_index(
        op.f("ix_goods_receipts_warehouse_id"),
        table_name="goods_receipts",
    )
    op.drop_index(
        op.f("ix_goods_receipts_tenant_id"),
        table_name="goods_receipts",
    )
    op.drop_index(
        op.f("ix_goods_receipts_supplier_id"),
        table_name="goods_receipts",
    )
    op.drop_index(
        op.f("ix_goods_receipts_status"),
        table_name="goods_receipts",
    )
    op.drop_index(
        op.f("ix_goods_receipts_receipt_number"),
        table_name="goods_receipts",
    )
    op.drop_index(
        op.f("ix_goods_receipts_received_by"),
        table_name="goods_receipts",
    )
    op.drop_index(
        op.f("ix_goods_receipts_received_at"),
        table_name="goods_receipts",
    )
    op.drop_index(
        op.f("ix_goods_receipts_idempotency_key"),
        table_name="goods_receipts",
    )
    op.drop_index(
        op.f("ix_goods_receipts_branch_id"),
        table_name="goods_receipts",
    )
    op.drop_table("goods_receipts")
    op.drop_constraint(
        "uq_inventory_batches_tenant_warehouse_product_batch",
        "inventory_batches",
        type_="unique",
    )
