"""Add inventory movement sale item trace

Revision ID: 7d9e2f4a6c8b
Revises: 6c2f9d8a1b4e
Create Date: 2026-08-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "7d9e2f4a6c8b"
down_revision = "6c2f9d8a1b4e"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("inventory_movements", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("sale_item_id", sa.String(length=36), nullable=True)
        )
        batch_op.create_index(
            batch_op.f("ix_inventory_movements_sale_item_id"),
            ["sale_item_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_inventory_movements_sale_item_id_sale_items",
            "sale_items",
            ["sale_item_id"],
            ["id"],
        )


def downgrade():
    with op.batch_alter_table("inventory_movements", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_inventory_movements_sale_item_id_sale_items",
            type_="foreignkey",
        )
        batch_op.drop_index(batch_op.f("ix_inventory_movements_sale_item_id"))
        batch_op.drop_column("sale_item_id")
