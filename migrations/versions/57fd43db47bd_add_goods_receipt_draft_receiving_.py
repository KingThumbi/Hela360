"""add goods receipt draft receiving lifecycle

Revision ID: 57fd43db47bd
Revises: aed3cefaa6e1

"""

from alembic import op
import sqlalchemy as sa


revision = "57fd43db47bd"
down_revision = "aed3cefaa6e1"
branch_labels = None
depends_on = None


def upgrade():
    # Creator is distinct from the user who eventually completes receiving.
    # Add it nullable first so existing receipt evidence can be preserved.
    op.add_column(
        "goods_receipts",
        sa.Column(
            "created_by",
            sa.String(length=36),
            nullable=True,
        ),
    )

    op.create_index(
        op.f("ix_goods_receipts_created_by"),
        "goods_receipts",
        ["created_by"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_goods_receipts_created_by_users",
        "goods_receipts",
        "users",
        ["created_by"],
        ["id"],
    )

    # Every historical receipt was created through the old completed-receipt
    # flow, so its receiver is the strongest available creator evidence.
    op.execute(
        """
        UPDATE goods_receipts
        SET created_by = received_by
        WHERE created_by IS NULL
        """
    )

    op.alter_column(
        "goods_receipts",
        "created_by",
        existing_type=sa.String(length=36),
        nullable=False,
    )

    op.add_column(
        "goods_receipts",
        sa.Column(
            "receiving_started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "goods_receipts",
        sa.Column(
            "receiving_started_by",
            sa.String(length=36),
            nullable=True,
        ),
    )

    op.create_index(
        op.f("ix_goods_receipts_receiving_started_by"),
        "goods_receipts",
        ["receiving_started_by"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_goods_receipts_receiving_started_by_users",
        "goods_receipts",
        "users",
        ["receiving_started_by"],
        ["id"],
    )

    # Draft and receiving records have not completed physical receipt yet.
    op.alter_column(
        "goods_receipts",
        "received_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
    )

    op.alter_column(
        "goods_receipts",
        "received_by",
        existing_type=sa.String(length=36),
        nullable=True,
    )


def downgrade():
    bind = op.get_bind()

    incomplete_count = bind.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM goods_receipts
            WHERE received_at IS NULL
               OR received_by IS NULL
            """
        )
    ).scalar_one()

    if incomplete_count:
        raise RuntimeError(
            "Cannot downgrade goods receipt draft/receiving lifecycle "
            "while incomplete goods receipts exist."
        )

    op.alter_column(
        "goods_receipts",
        "received_by",
        existing_type=sa.String(length=36),
        nullable=False,
    )

    op.alter_column(
        "goods_receipts",
        "received_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )

    op.drop_constraint(
        "fk_goods_receipts_receiving_started_by_users",
        "goods_receipts",
        type_="foreignkey",
    )

    op.drop_index(
        op.f("ix_goods_receipts_receiving_started_by"),
        table_name="goods_receipts",
    )

    op.drop_column(
        "goods_receipts",
        "receiving_started_by",
    )
    op.drop_column(
        "goods_receipts",
        "receiving_started_at",
    )

    op.drop_constraint(
        "fk_goods_receipts_created_by_users",
        "goods_receipts",
        type_="foreignkey",
    )

    op.drop_index(
        op.f("ix_goods_receipts_created_by"),
        table_name="goods_receipts",
    )

    op.drop_column(
        "goods_receipts",
        "created_by",
    )
