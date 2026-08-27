"""Add suppliers

Revision ID: 8f3b7c2a9d10
Revises: 19b1ccd035ac
Create Date: 2026-08-04 15:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "8f3b7c2a9d10"
down_revision = "19b1ccd035ac"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "suppliers",
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("supplier_code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("legal_name", sa.String(length=200), nullable=True),
        sa.Column("contact_person", sa.String(length=150), nullable=True),
        sa.Column("email", sa.String(length=150), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("alternate_phone", sa.String(length=50), nullable=True),
        sa.Column("address_line_1", sa.String(length=200), nullable=True),
        sa.Column("address_line_2", sa.String(length=200), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("county_or_region", sa.String(length=100), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("postal_code", sa.String(length=30), nullable=True),
        sa.Column("tax_number", sa.String(length=80), nullable=True),
        sa.Column("registration_number", sa.String(length=80), nullable=True),
        sa.Column("payment_terms_days", sa.Integer(), nullable=False),
        sa.Column("credit_limit", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "registration_number",
            name="uq_suppliers_tenant_registration_number",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "supplier_code",
            name="uq_suppliers_tenant_supplier_code",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "tax_number",
            name="uq_suppliers_tenant_tax_number",
        ),
    )

    with op.batch_alter_table("suppliers", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_suppliers_email"), ["email"], unique=False)
        batch_op.create_index(batch_op.f("ix_suppliers_is_active"), ["is_active"], unique=False)
        batch_op.create_index(batch_op.f("ix_suppliers_phone"), ["phone"], unique=False)
        batch_op.create_index(batch_op.f("ix_suppliers_tenant_id"), ["tenant_id"], unique=False)


def downgrade():
    with op.batch_alter_table("suppliers", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_suppliers_tenant_id"))
        batch_op.drop_index(batch_op.f("ix_suppliers_phone"))
        batch_op.drop_index(batch_op.f("ix_suppliers_is_active"))
        batch_op.drop_index(batch_op.f("ix_suppliers_email"))

    op.drop_table("suppliers")
