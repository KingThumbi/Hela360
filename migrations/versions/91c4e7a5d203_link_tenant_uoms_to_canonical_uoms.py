"""link tenant uoms to canonical uoms

Revision ID: 91c4e7a5d203
Revises: 8d7f4c6a2b10

"""

from alembic import op
import sqlalchemy as sa


revision = "91c4e7a5d203"
down_revision = "8d7f4c6a2b10"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "units_of_measure",
        sa.Column(
            "canonical_uom_id",
            sa.String(length=36),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_units_of_measure_canonical_uom_id",
        "units_of_measure",
        ["canonical_uom_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_units_of_measure_canonical_uom_id",
        "units_of_measure",
        "canonical_units_of_measure",
        ["canonical_uom_id"],
        ["id"],
    )


def downgrade():
    op.drop_constraint(
        "fk_units_of_measure_canonical_uom_id",
        "units_of_measure",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_units_of_measure_canonical_uom_id",
        table_name="units_of_measure",
    )

    op.drop_column(
        "units_of_measure",
        "canonical_uom_id",
    )
