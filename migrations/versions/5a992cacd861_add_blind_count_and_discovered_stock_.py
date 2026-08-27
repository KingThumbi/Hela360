"""add blind count and discovered stock count lines

Revision ID: 5a992cacd861
Revises: b8f22d01d49e
Create Date: 2026-08-27 21:52:32.562142

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "5a992cacd861"
down_revision = "b8f22d01d49e"
branch_labels = None
depends_on = None


def upgrade():
    # ------------------------------------------------------------------
    # Stock Count mode
    # ------------------------------------------------------------------

    op.add_column(
        "stock_counts",
        sa.Column(
            "count_mode",
            sa.String(length=20),
            nullable=False,
            server_default="blind",
        ),
    )

    op.create_index(
        op.f("ix_stock_counts_count_mode"),
        "stock_counts",
        ["count_mode"],
        unique=False,
    )

    # ------------------------------------------------------------------
    # Stock Count Item source / discovered physical identifiers
    # ------------------------------------------------------------------

    op.add_column(
        "stock_count_items",
        sa.Column(
            "source_type",
            sa.String(length=20),
            nullable=False,
            server_default="snapshot",
        ),
    )

    op.add_column(
        "stock_count_items",
        sa.Column(
            "observed_batch_number",
            sa.String(length=100),
            nullable=True,
        ),
    )

    op.add_column(
        "stock_count_items",
        sa.Column(
            "observed_expiry_date",
            sa.Date(),
            nullable=True,
        ),
    )

    op.create_index(
        op.f("ix_stock_count_items_source_type"),
        "stock_count_items",
        ["source_type"],
        unique=False,
    )

    op.create_index(
        op.f("ix_stock_count_items_observed_batch_number"),
        "stock_count_items",
        ["observed_batch_number"],
        unique=False,
    )

    op.create_index(
        op.f("ix_stock_count_items_observed_expiry_date"),
        "stock_count_items",
        ["observed_expiry_date"],
        unique=False,
    )

    # Existing Stock Counts become blind by default.
    #
    # Existing Stock Count Items represent snapshot-created lines.
    #
    # Keep the server defaults because these are also useful defensive DB
    # defaults for rows created outside the ORM.


def downgrade():
    op.drop_index(
        op.f("ix_stock_count_items_observed_expiry_date"),
        table_name="stock_count_items",
    )

    op.drop_index(
        op.f("ix_stock_count_items_observed_batch_number"),
        table_name="stock_count_items",
    )

    op.drop_index(
        op.f("ix_stock_count_items_source_type"),
        table_name="stock_count_items",
    )

    op.drop_column(
        "stock_count_items",
        "observed_expiry_date",
    )

    op.drop_column(
        "stock_count_items",
        "observed_batch_number",
    )

    op.drop_column(
        "stock_count_items",
        "source_type",
    )

    op.drop_index(
        op.f("ix_stock_counts_count_mode"),
        table_name="stock_counts",
    )

    op.drop_column(
        "stock_counts",
        "count_mode",
    )
