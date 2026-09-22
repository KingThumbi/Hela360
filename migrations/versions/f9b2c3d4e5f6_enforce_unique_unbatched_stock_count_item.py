"""enforce unique unbatched stock count item identity

Revision ID: f9b2c3d4e5f6
Revises: e8a1b2c3d4f5
"""

from alembic import op
import sqlalchemy as sa


revision = "f9b2c3d4e5f6"
down_revision = "e8a1b2c3d4f5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "uq_stock_count_items_unbatched_count_product",
        "stock_count_items",
        ["stock_count_id", "product_id"],
        unique=True,
        postgresql_where=sa.text(
            "batch_id IS NULL "
            "AND observed_batch_number IS NULL "
            "AND observed_expiry_date IS NULL"
        ),
    )


def downgrade():
    op.drop_index(
        "uq_stock_count_items_unbatched_count_product",
        table_name="stock_count_items",
    )
