"""add stock count scope products

Revision ID: 55445bee735c
Revises: 5a992cacd861
Create Date: 2026-08-29 14:16:35.392701

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "55445bee735c"
down_revision = "5a992cacd861"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "stock_count_scope_products",
        sa.Column(
            "stock_count_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.String(length=36),
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
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
        ),
        sa.ForeignKeyConstraint(
            ["stock_count_id"],
            ["stock_counts.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "stock_count_id",
            "product_id",
            name=(
                "uq_stock_count_scope_products_"
                "count_product"
            ),
        ),
    )

    with op.batch_alter_table(
        "stock_count_scope_products",
        schema=None,
    ) as batch_op:
        batch_op.create_index(
            batch_op.f(
                "ix_stock_count_scope_products_product_id"
            ),
            ["product_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f(
                "ix_stock_count_scope_products_stock_count_id"
            ),
            ["stock_count_id"],
            unique=False,
        )

    # Backfill explicit Product scope for selected Stock Counts that existed
    # before this table. Historically their selected scope was represented
    # only by StockCountItem rows. Full counts intentionally receive no rows.
    op.execute(
        sa.text(
            """
            WITH existing_scope AS (
                SELECT DISTINCT
                    sci.stock_count_id,
                    sci.product_id,
                    md5(
                        sci.stock_count_id
                        || ':'
                        || sci.product_id
                    ) AS scope_hash
                FROM stock_count_items AS sci
                INNER JOIN stock_counts AS sc
                    ON sc.id = sci.stock_count_id
                WHERE sc.scope_type = 'selected'
            )
            INSERT INTO stock_count_scope_products (
                id,
                stock_count_id,
                product_id,
                created_at,
                updated_at
            )
            SELECT
                substr(scope_hash, 1, 8)
                || '-'
                || substr(scope_hash, 9, 4)
                || '-'
                || substr(scope_hash, 13, 4)
                || '-'
                || substr(scope_hash, 17, 4)
                || '-'
                || substr(scope_hash, 21, 12),
                stock_count_id,
                product_id,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            FROM existing_scope
            ON CONFLICT (
                stock_count_id,
                product_id
            ) DO NOTHING
            """
        )
    )


def downgrade():
    with op.batch_alter_table(
        "stock_count_scope_products",
        schema=None,
    ) as batch_op:
        batch_op.drop_index(
            batch_op.f(
                "ix_stock_count_scope_products_stock_count_id"
            )
        )
        batch_op.drop_index(
            batch_op.f(
                "ix_stock_count_scope_products_product_id"
            )
        )

    op.drop_table("stock_count_scope_products")
