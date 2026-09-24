"""add stock count unit provenance

Revision ID: a4d7e9f1b2c3
Revises: f9b2c3d4e5f6
Create Date: 2026-09-24
"""

from alembic import op
import sqlalchemy as sa


revision = "a4d7e9f1b2c3"
down_revision = "f9b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table(
        "stock_count_items"
    ) as batch_op:
        batch_op.add_column(
            sa.Column(
                "counted_unit_quantity",
                sa.Numeric(
                    precision=18,
                    scale=4,
                ),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "counted_product_unit_id",
                sa.String(length=36),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "counted_unit_code_snapshot",
                sa.String(length=20),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "counted_unit_name_snapshot",
                sa.String(length=50),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "counted_conversion_factor_to_base",
                sa.Numeric(
                    precision=18,
                    scale=6,
                ),
                nullable=True,
            )
        )

        batch_op.create_index(
            op.f(
                "ix_stock_count_items_"
                "counted_product_unit_id"
            ),
            [
                "counted_product_unit_id",
            ],
            unique=False,
        )

        batch_op.create_foreign_key(
            (
                "fk_stock_count_items_"
                "counted_product_unit_id_"
                "product_units"
            ),
            "product_units",
            [
                "counted_product_unit_id",
            ],
            [
                "id",
            ],
        )

    # Historical counted rows were entered in canonical/base
    # quantity because multi-UOM Stock Count did not yet exist.
    op.execute(
        sa.text(
            """
            UPDATE stock_count_items
            SET
                counted_unit_quantity =
                    counted_quantity,
                counted_conversion_factor_to_base =
                    1
            WHERE counted_quantity IS NOT NULL
              AND counted_unit_quantity IS NULL
            """
        )
    )


def downgrade():
    with op.batch_alter_table(
        "stock_count_items"
    ) as batch_op:
        batch_op.drop_constraint(
            (
                "fk_stock_count_items_"
                "counted_product_unit_id_"
                "product_units"
            ),
            type_="foreignkey",
        )

        batch_op.drop_index(
            op.f(
                "ix_stock_count_items_"
                "counted_product_unit_id"
            )
        )

        batch_op.drop_column(
            "counted_conversion_factor_to_base"
        )
        batch_op.drop_column(
            "counted_unit_name_snapshot"
        )
        batch_op.drop_column(
            "counted_unit_code_snapshot"
        )
        batch_op.drop_column(
            "counted_product_unit_id"
        )
        batch_op.drop_column(
            "counted_unit_quantity"
        )
