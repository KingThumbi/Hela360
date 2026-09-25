"""add stock count superseded state

Revision ID: b5e8c1d2f3a4
Revises: a4d7e9f1b2c3
Create Date: 2026-09-25

"""

from alembic import op
import sqlalchemy as sa


revision = "b5e8c1d2f3a4"
down_revision = "a4d7e9f1b2c3"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table(
        "stock_counts",
        schema=None,
    ) as batch_op:
        batch_op.add_column(
            sa.Column(
                "superseded_at",
                sa.DateTime(timezone=True),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "superseded_by",
                sa.String(length=36),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "superseded_reason",
                sa.Text(),
                nullable=True,
            )
        )
        batch_op.create_index(
            "ix_stock_counts_superseded_by",
            ["superseded_by"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_stock_counts_superseded_by_users",
            "users",
            ["superseded_by"],
            ["id"],
        )


def downgrade():
    with op.batch_alter_table(
        "stock_counts",
        schema=None,
    ) as batch_op:
        batch_op.drop_constraint(
            "fk_stock_counts_superseded_by_users",
            type_="foreignkey",
        )
        batch_op.drop_index(
            "ix_stock_counts_superseded_by",
        )
        batch_op.drop_column(
            "superseded_reason",
        )
        batch_op.drop_column(
            "superseded_by",
        )
        batch_op.drop_column(
            "superseded_at",
        )
