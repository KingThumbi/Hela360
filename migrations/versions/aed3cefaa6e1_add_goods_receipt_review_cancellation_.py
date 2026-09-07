"""add goods receipt review cancellation audit

Revision ID: aed3cefaa6e1
Revises: 5675b38da92a
Create Date: 2026-09-07 21:20:27.541810

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "aed3cefaa6e1"
down_revision = "5675b38da92a"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "goods_receipts",
        sa.Column(
            "under_review_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "goods_receipts",
        sa.Column(
            "under_review_by",
            sa.String(length=36),
            nullable=True,
        ),
    )
    op.add_column(
        "goods_receipts",
        sa.Column(
            "cancelled_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "goods_receipts",
        sa.Column(
            "cancelled_by",
            sa.String(length=36),
            nullable=True,
        ),
    )

    op.create_index(
        op.f("ix_goods_receipts_under_review_by"),
        "goods_receipts",
        ["under_review_by"],
        unique=False,
    )
    op.create_index(
        op.f("ix_goods_receipts_cancelled_by"),
        "goods_receipts",
        ["cancelled_by"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_goods_receipts_under_review_by_users",
        "goods_receipts",
        "users",
        ["under_review_by"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_goods_receipts_cancelled_by_users",
        "goods_receipts",
        "users",
        ["cancelled_by"],
        ["id"],
    )


def downgrade():
    op.drop_constraint(
        "fk_goods_receipts_cancelled_by_users",
        "goods_receipts",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_goods_receipts_under_review_by_users",
        "goods_receipts",
        type_="foreignkey",
    )

    op.drop_index(
        op.f("ix_goods_receipts_cancelled_by"),
        table_name="goods_receipts",
    )
    op.drop_index(
        op.f("ix_goods_receipts_under_review_by"),
        table_name="goods_receipts",
    )

    op.drop_column(
        "goods_receipts",
        "cancelled_by",
    )
    op.drop_column(
        "goods_receipts",
        "cancelled_at",
    )
    op.drop_column(
        "goods_receipts",
        "under_review_by",
    )
    op.drop_column(
        "goods_receipts",
        "under_review_at",
    )
