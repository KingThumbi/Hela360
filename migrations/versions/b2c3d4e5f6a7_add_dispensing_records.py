"""Add dispensing records

Revision ID: b2c3d4e5f6a7
Revises: 9a1b2c3d4e5f
Create Date: 2026-08-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "b2c3d4e5f6a7"
down_revision = "9a1b2c3d4e5f"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "dispensing_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("branch_id", sa.String(length=36), nullable=False),
        sa.Column("customer_id", sa.String(length=36), nullable=False),
        sa.Column("sale_id", sa.String(length=36), nullable=False),
        sa.Column("sale_item_id", sa.String(length=36), nullable=False),
        sa.Column("product_id", sa.String(length=36), nullable=False),
        sa.Column("dispensed_quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("prescription_reference", sa.String(length=100), nullable=True),
        sa.Column("prescriber_name", sa.String(length=150), nullable=False),
        sa.Column(
            "prescriber_registration_number",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column("prescription_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("dispensed_by", sa.String(length=36), nullable=False),
        sa.Column("dispensed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["dispensed_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"]),
        sa.ForeignKeyConstraint(["sale_item_id"], ["sale_items.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "sale_item_id",
            name="uq_dispensing_records_sale_item_id",
        ),
    )
    op.create_index(
        op.f("ix_dispensing_records_branch_id"),
        "dispensing_records",
        ["branch_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dispensing_records_customer_id"),
        "dispensing_records",
        ["customer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dispensing_records_dispensed_by"),
        "dispensing_records",
        ["dispensed_by"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dispensing_records_product_id"),
        "dispensing_records",
        ["product_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dispensing_records_sale_id"),
        "dispensing_records",
        ["sale_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dispensing_records_sale_item_id"),
        "dispensing_records",
        ["sale_item_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dispensing_records_tenant_id"),
        "dispensing_records",
        ["tenant_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_dispensing_records_tenant_id"),
        table_name="dispensing_records",
    )
    op.drop_index(
        op.f("ix_dispensing_records_sale_item_id"),
        table_name="dispensing_records",
    )
    op.drop_index(
        op.f("ix_dispensing_records_sale_id"),
        table_name="dispensing_records",
    )
    op.drop_index(
        op.f("ix_dispensing_records_product_id"),
        table_name="dispensing_records",
    )
    op.drop_index(
        op.f("ix_dispensing_records_dispensed_by"),
        table_name="dispensing_records",
    )
    op.drop_index(
        op.f("ix_dispensing_records_customer_id"),
        table_name="dispensing_records",
    )
    op.drop_index(
        op.f("ix_dispensing_records_branch_id"),
        table_name="dispensing_records",
    )
    op.drop_table("dispensing_records")
