"""add canonical uom catalogue

Revision ID: 8d7f4c6a2b10
Revises: 57fd43db47bd

"""

from alembic import op
import sqlalchemy as sa


revision = "8d7f4c6a2b10"
down_revision = "57fd43db47bd"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "canonical_units_of_measure",
        sa.Column(
            "code",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "unit_family",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "is_packaging_unit",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "sort_order",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "id",
        ),
        sa.UniqueConstraint(
            "code",
            name="uq_canonical_units_of_measure_code",
        ),
    )

    op.create_index(
        "ix_canonical_units_of_measure_code",
        "canonical_units_of_measure",
        ["code"],
        unique=False,
    )

    op.create_index(
        "ix_canonical_units_of_measure_name",
        "canonical_units_of_measure",
        ["name"],
        unique=False,
    )

    op.create_index(
        "ix_canonical_units_of_measure_unit_family",
        "canonical_units_of_measure",
        ["unit_family"],
        unique=False,
    )

    op.create_index(
        "ix_canonical_units_of_measure_is_packaging_unit",
        "canonical_units_of_measure",
        ["is_packaging_unit"],
        unique=False,
    )

    op.create_index(
        "ix_canonical_units_of_measure_is_active",
        "canonical_units_of_measure",
        ["is_active"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_canonical_units_of_measure_is_active",
        table_name="canonical_units_of_measure",
    )

    op.drop_index(
        "ix_canonical_units_of_measure_is_packaging_unit",
        table_name="canonical_units_of_measure",
    )

    op.drop_index(
        "ix_canonical_units_of_measure_unit_family",
        table_name="canonical_units_of_measure",
    )

    op.drop_index(
        "ix_canonical_units_of_measure_name",
        table_name="canonical_units_of_measure",
    )

    op.drop_index(
        "ix_canonical_units_of_measure_code",
        table_name="canonical_units_of_measure",
    )

    op.drop_table(
        "canonical_units_of_measure"
    )
