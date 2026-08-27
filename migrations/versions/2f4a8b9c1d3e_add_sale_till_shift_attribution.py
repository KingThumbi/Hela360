"""Add sale till shift attribution

Revision ID: 2f4a8b9c1d3e
Revises: 8f3b7c2a9d10
Create Date: 2026-08-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "2f4a8b9c1d3e"
down_revision = "8f3b7c2a9d10"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("sales", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("till_shift_id", sa.UUID(), nullable=True)
        )
        batch_op.create_index(
            batch_op.f("ix_sales_till_shift_id"),
            ["till_shift_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_sales_till_shift_id_till_shifts",
            "till_shifts",
            ["till_shift_id"],
            ["id"],
        )


def downgrade():
    with op.batch_alter_table("sales", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_sales_till_shift_id_till_shifts",
            type_="foreignkey",
        )
        batch_op.drop_index(batch_op.f("ix_sales_till_shift_id"))
        batch_op.drop_column("till_shift_id")
