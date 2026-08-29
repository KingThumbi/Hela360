"""add stock count no stock confirmation

Revision ID: 52bde25d92a6
Revises: 55445bee735c
Create Date: 2026-08-29 15:11:30.505026

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "52bde25d92a6"
down_revision = "55445bee735c"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table(
        "stock_count_scope_products",
        schema=None,
    ) as batch_op:
        batch_op.add_column(
            sa.Column(
                "no_stock_confirmed_at",
                sa.DateTime(timezone=True),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "no_stock_confirmed_by",
                sa.String(length=36),
                nullable=True,
            )
        )
        batch_op.create_index(
            batch_op.f(
                "ix_stock_count_scope_products_no_stock_confirmed_by"
            ),
            ["no_stock_confirmed_by"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_stock_count_scope_products_no_stock_confirmed_by_users",
            "users",
            ["no_stock_confirmed_by"],
            ["id"],
        )


def downgrade():
    with op.batch_alter_table(
        "stock_count_scope_products",
        schema=None,
    ) as batch_op:
        batch_op.drop_constraint(
            "fk_stock_count_scope_products_no_stock_confirmed_by_users",
            type_="foreignkey",
        )
        batch_op.drop_index(
            batch_op.f(
                "ix_stock_count_scope_products_no_stock_confirmed_by"
            )
        )
        batch_op.drop_column(
            "no_stock_confirmed_by"
        )
        batch_op.drop_column(
            "no_stock_confirmed_at"
        )
