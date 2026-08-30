"""add source offer key to supplier prices

Revision ID: ecda314fd79c
Revises: 74e94fd542ea
Create Date: 2026-08-30 23:08:27.371989

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ecda314fd79c'
down_revision = '74e94fd542ea'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "supplier_item_prices",
        sa.Column(
            "source_offer_key",
            sa.String(length=60),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_supplier_item_prices_source_offer_key",
        "supplier_item_prices",
        ["source_offer_key"],
        unique=True,
    )

def downgrade():
    op.drop_index(
        "ix_supplier_item_prices_source_offer_key",
        table_name="supplier_item_prices",
    )

    op.drop_column(
        "supplier_item_prices",
        "source_offer_key",
    )
