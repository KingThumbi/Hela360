"""add UOM remediation execution provenance

Revision ID: d7f9a3c1e602
Revises: c6e8a2f4d911
"""

from alembic import op
import sqlalchemy as sa


revision = "d7f9a3c1e602"
down_revision = "c6e8a2f4d911"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "tenant_uom_remediation_reviews",
        sa.Column(
            "executed_by",
            sa.String(length=36),
            nullable=True,
        ),
    )
    op.create_index(
        op.f(
            "ix_tenant_uom_remediation_reviews_executed_by"
        ),
        "tenant_uom_remediation_reviews",
        ["executed_by"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_uom_remediation_reviews_executed_by_users",
        "tenant_uom_remediation_reviews",
        "users",
        ["executed_by"],
        ["id"],
    )

    op.add_column(
        "tenant_uom_remediation_reviews",
        sa.Column(
            "executed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "tenant_uom_remediation_reviews",
        sa.Column(
            "execution_summary",
            sa.JSON(),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column(
        "tenant_uom_remediation_reviews",
        "execution_summary",
    )
    op.drop_column(
        "tenant_uom_remediation_reviews",
        "executed_at",
    )

    op.drop_constraint(
        "fk_uom_remediation_reviews_executed_by_users",
        "tenant_uom_remediation_reviews",
        type_="foreignkey",
    )
    op.drop_index(
        op.f(
            "ix_tenant_uom_remediation_reviews_executed_by"
        ),
        table_name="tenant_uom_remediation_reviews",
    )
    op.drop_column(
        "tenant_uom_remediation_reviews",
        "executed_by",
    )
