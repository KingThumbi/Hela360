"""Add till warehouse attribution

Revision ID: 6c2f9d8a1b4e
Revises: 2f4a8b9c1d3e
Create Date: 2026-08-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "6c2f9d8a1b4e"
down_revision = "2f4a8b9c1d3e"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("tills", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("warehouse_id", sa.String(length=36), nullable=True)
        )
        batch_op.create_index(
            batch_op.f("ix_tills_warehouse_id"),
            ["warehouse_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_tills_warehouse_id_warehouses",
            "warehouses",
            ["warehouse_id"],
            ["id"],
        )


def downgrade():
    with op.batch_alter_table("tills", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_tills_warehouse_id_warehouses",
            type_="foreignkey",
        )
        batch_op.drop_index(batch_op.f("ix_tills_warehouse_id"))
        batch_op.drop_column("warehouse_id")
