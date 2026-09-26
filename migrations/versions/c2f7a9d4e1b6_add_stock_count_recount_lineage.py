"""add stock count recount lineage

Revision ID: c2f7a9d4e1b6
Revises: b5e8c1d2f3a4
Create Date: 2026-09-25

"""

from alembic import op
import sqlalchemy as sa


revision = "c2f7a9d4e1b6"
down_revision = "b5e8c1d2f3a4"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table(
        "stock_counts",
        schema=None,
    ) as batch_op:
        batch_op.add_column(
            sa.Column(
                "recount_of_stock_count_id",
                sa.String(length=36),
                nullable=True,
            )
        )
        batch_op.create_index(
            "ix_stock_counts_recount_of_stock_count_id",
            ["recount_of_stock_count_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_stock_counts_recount_of_stock_count_id",
            "stock_counts",
            ["recount_of_stock_count_id"],
            ["id"],
        )


def downgrade():
    with op.batch_alter_table(
        "stock_counts",
        schema=None,
    ) as batch_op:
        batch_op.drop_constraint(
            "fk_stock_counts_recount_of_stock_count_id",
            type_="foreignkey",
        )
        batch_op.drop_index(
            "ix_stock_counts_recount_of_stock_count_id",
        )
        batch_op.drop_column(
            "recount_of_stock_count_id",
        )
