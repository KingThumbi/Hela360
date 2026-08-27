"""Add stock counts

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-08-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "stock_counts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("branch_id", sa.String(length=36), nullable=False),
        sa.Column("warehouse_id", sa.String(length=36), nullable=False),
        sa.Column("count_number", sa.String(length=50), nullable=False),
        sa.Column("idempotency_key", sa.String(length=120), nullable=False),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("scope_type", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("snapshot_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_by", sa.String(length=36), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_by", sa.String(length=36), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_by", sa.String(length=36), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.ForeignKeyConstraint(["cancelled_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["completed_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["started_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "count_number",
            name="uq_stock_counts_tenant_count_number",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "idempotency_key",
            name="uq_stock_counts_tenant_idempotency_key",
        ),
    )
    op.create_index(op.f("ix_stock_counts_branch_id"), "stock_counts", ["branch_id"])
    op.create_index(op.f("ix_stock_counts_count_number"), "stock_counts", ["count_number"])
    op.create_index(op.f("ix_stock_counts_idempotency_key"), "stock_counts", ["idempotency_key"])
    op.create_index(op.f("ix_stock_counts_snapshot_at"), "stock_counts", ["snapshot_at"])
    op.create_index(op.f("ix_stock_counts_started_by"), "stock_counts", ["started_by"])
    op.create_index(op.f("ix_stock_counts_status"), "stock_counts", ["status"])
    op.create_index(op.f("ix_stock_counts_tenant_id"), "stock_counts", ["tenant_id"])
    op.create_index(op.f("ix_stock_counts_warehouse_id"), "stock_counts", ["warehouse_id"])

    op.create_table(
        "stock_count_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("stock_count_id", sa.String(length=36), nullable=False),
        sa.Column("product_id", sa.String(length=36), nullable=False),
        sa.Column("batch_id", sa.String(length=36), nullable=True),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("snapshot_quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("expected_quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("counted_quantity", sa.Numeric(18, 4), nullable=True),
        sa.Column("variance_quantity", sa.Numeric(18, 4), nullable=True),
        sa.Column("counted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("counted_by", sa.String(length=36), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["inventory_batches.id"]),
        sa.ForeignKeyConstraint(["counted_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["stock_count_id"], ["stock_counts.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "stock_count_id",
            "line_number",
            name="uq_stock_count_items_count_line",
        ),
        sa.UniqueConstraint(
            "stock_count_id",
            "product_id",
            "batch_id",
            name="uq_stock_count_items_count_product_batch",
        ),
    )
    op.create_index(op.f("ix_stock_count_items_batch_id"), "stock_count_items", ["batch_id"])
    op.create_index(op.f("ix_stock_count_items_counted_by"), "stock_count_items", ["counted_by"])
    op.create_index(op.f("ix_stock_count_items_product_id"), "stock_count_items", ["product_id"])
    op.create_index(op.f("ix_stock_count_items_stock_count_id"), "stock_count_items", ["stock_count_id"])

    op.execute(
        sa.text(
            """
            INSERT INTO permissions (id, code, name, module_code, description)
            VALUES (
                'perm-inventory-count',
                'inventory.count',
                'Inventory Count',
                'inventory',
                'Create and complete stock count documents.'
            )
            ON CONFLICT (code) DO NOTHING
            """
        )
    )


def downgrade():
    op.execute(
        sa.text("DELETE FROM permissions WHERE code = 'inventory.count'")
    )
    op.drop_index(op.f("ix_stock_count_items_stock_count_id"), table_name="stock_count_items")
    op.drop_index(op.f("ix_stock_count_items_product_id"), table_name="stock_count_items")
    op.drop_index(op.f("ix_stock_count_items_counted_by"), table_name="stock_count_items")
    op.drop_index(op.f("ix_stock_count_items_batch_id"), table_name="stock_count_items")
    op.drop_table("stock_count_items")
    op.drop_index(op.f("ix_stock_counts_warehouse_id"), table_name="stock_counts")
    op.drop_index(op.f("ix_stock_counts_tenant_id"), table_name="stock_counts")
    op.drop_index(op.f("ix_stock_counts_status"), table_name="stock_counts")
    op.drop_index(op.f("ix_stock_counts_started_by"), table_name="stock_counts")
    op.drop_index(op.f("ix_stock_counts_snapshot_at"), table_name="stock_counts")
    op.drop_index(op.f("ix_stock_counts_idempotency_key"), table_name="stock_counts")
    op.drop_index(op.f("ix_stock_counts_count_number"), table_name="stock_counts")
    op.drop_index(op.f("ix_stock_counts_branch_id"), table_name="stock_counts")
    op.drop_table("stock_counts")
