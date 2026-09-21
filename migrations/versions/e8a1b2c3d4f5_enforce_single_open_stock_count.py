"""enforce single open stock count per warehouse

Revision ID: e8a1b2c3d4f5
Revises: d7f9a3c1e602
"""

from alembic import op
import sqlalchemy as sa


revision = "e8a1b2c3d4f5"
down_revision = "d7f9a3c1e602"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "uq_stock_counts_one_open_per_warehouse",
        "stock_counts",
        ["tenant_id", "warehouse_id"],
        unique=True,
        postgresql_where=sa.text("status = 'open'"),
    )


def downgrade():
    op.drop_index(
        "uq_stock_counts_one_open_per_warehouse",
        table_name="stock_counts",
    )
