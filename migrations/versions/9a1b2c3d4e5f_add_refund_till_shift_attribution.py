"""Add refund till shift attribution

Revision ID: 9a1b2c3d4e5f
Revises: 7d9e2f4a6c8b
Create Date: 2026-08-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "9a1b2c3d4e5f"
down_revision = "7d9e2f4a6c8b"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("sale_refunds", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("till_shift_id", sa.UUID(), nullable=True)
        )
        batch_op.create_index(
            batch_op.f("ix_sale_refunds_till_shift_id"),
            ["till_shift_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_sale_refunds_till_shift_id_till_shifts",
            "till_shifts",
            ["till_shift_id"],
            ["id"],
        )


def downgrade():
    with op.batch_alter_table("sale_refunds", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_sale_refunds_till_shift_id_till_shifts",
            type_="foreignkey",
        )
        batch_op.drop_index(batch_op.f("ix_sale_refunds_till_shift_id"))
        batch_op.drop_column("till_shift_id")
