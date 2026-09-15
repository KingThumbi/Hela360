"""add tenant UOM remediation reviews

Revision ID: c6e8a2f4d911
Revises: 91c4e7a5d203
Create Date: 2026-09-15
"""

from alembic import op
import sqlalchemy as sa


revision = "c6e8a2f4d911"
down_revision = "91c4e7a5d203"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tenant_uom_remediation_reviews",
        sa.Column(
            "tenant_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "source_uom_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "audit_classification",
            sa.String(length=40),
            nullable=False,
        ),
        sa.Column(
            "recommended_action",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "suggested_canonical_code",
            sa.String(length=20),
            nullable=True,
        ),
        sa.Column(
            "selected_action",
            sa.String(length=50),
            nullable=True,
        ),
        sa.Column(
            "selected_canonical_uom_id",
            sa.String(length=36),
            nullable=True,
        ),
        sa.Column(
            "planner_version",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "planner_fingerprint",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "planner_snapshot",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "created_by",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "reviewed_by",
            sa.String(length=36),
            nullable=True,
        ),
        sa.Column(
            "reviewed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "review_reason",
            sa.Text(),
            nullable=True,
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
        sa.CheckConstraint(
            (
                "status IN ("
                "'pending', "
                "'approved', "
                "'rejected', "
                "'superseded', "
                "'executed'"
                ")"
            ),
            name=(
                "ck_tenant_uom_remediation_reviews_status"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["selected_canonical_uom_id"],
            ["canonical_units_of_measure.id"],
        ),
        sa.ForeignKeyConstraint(
            ["source_uom_id"],
            ["units_of_measure.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f(
            "ix_tenant_uom_remediation_reviews_tenant_id"
        ),
        "tenant_uom_remediation_reviews",
        ["tenant_id"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_tenant_uom_remediation_reviews_source_uom_id"
        ),
        "tenant_uom_remediation_reviews",
        ["source_uom_id"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_tenant_uom_remediation_reviews_status"
        ),
        "tenant_uom_remediation_reviews",
        ["status"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_tenant_uom_remediation_reviews_"
            "audit_classification"
        ),
        "tenant_uom_remediation_reviews",
        ["audit_classification"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_tenant_uom_remediation_reviews_"
            "recommended_action"
        ),
        "tenant_uom_remediation_reviews",
        ["recommended_action"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_tenant_uom_remediation_reviews_"
            "selected_action"
        ),
        "tenant_uom_remediation_reviews",
        ["selected_action"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_tenant_uom_remediation_reviews_"
            "selected_canonical_uom_id"
        ),
        "tenant_uom_remediation_reviews",
        ["selected_canonical_uom_id"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_tenant_uom_remediation_reviews_"
            "planner_fingerprint"
        ),
        "tenant_uom_remediation_reviews",
        ["planner_fingerprint"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_tenant_uom_remediation_reviews_created_by"
        ),
        "tenant_uom_remediation_reviews",
        ["created_by"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_tenant_uom_remediation_reviews_reviewed_by"
        ),
        "tenant_uom_remediation_reviews",
        ["reviewed_by"],
        unique=False,
    )

    op.create_index(
        "ix_tenant_uom_remediation_reviews_one_active",
        "tenant_uom_remediation_reviews",
        ["tenant_id", "source_uom_id"],
        unique=True,
        postgresql_where=sa.text(
            "status IN ('pending', 'approved')"
        ),
    )

    op.create_table(
        "tenant_uom_remediation_product_decisions",
        sa.Column(
            "review_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "source_product_unit_id",
            sa.String(length=36),
            nullable=True,
        ),
        sa.Column(
            "recommended_action",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "suggested_canonical_code",
            sa.String(length=20),
            nullable=True,
        ),
        sa.Column(
            "selected_action",
            sa.String(length=50),
            nullable=True,
        ),
        sa.Column(
            "target_canonical_uom_id",
            sa.String(length=36),
            nullable=True,
        ),
        sa.Column(
            "target_tenant_uom_id",
            sa.String(length=36),
            nullable=True,
        ),
        sa.Column(
            "preserve_historical_unit",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "review_note",
            sa.Text(),
            nullable=True,
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
            ["review_id"],
            ["tenant_uom_remediation_reviews.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_product_unit_id"],
            ["product_units.id"],
        ),
        sa.ForeignKeyConstraint(
            ["target_canonical_uom_id"],
            ["canonical_units_of_measure.id"],
        ),
        sa.ForeignKeyConstraint(
            ["target_tenant_uom_id"],
            ["units_of_measure.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "review_id",
            "product_id",
            name=(
                "uq_tenant_uom_remediation_decisions_"
                "review_product"
            ),
        ),
    )

    for column in (
        "review_id",
        "tenant_id",
        "product_id",
        "source_product_unit_id",
        "recommended_action",
        "selected_action",
        "target_canonical_uom_id",
        "target_tenant_uom_id",
    ):
        op.create_index(
            op.f(
                "ix_tenant_uom_remediation_product_"
                f"decisions_{column}"
            ),
            "tenant_uom_remediation_product_decisions",
            [column],
            unique=False,
        )


def downgrade():
    for column in reversed(
        (
            "review_id",
            "tenant_id",
            "product_id",
            "source_product_unit_id",
            "recommended_action",
            "selected_action",
            "target_canonical_uom_id",
            "target_tenant_uom_id",
        )
    ):
        op.drop_index(
            op.f(
                "ix_tenant_uom_remediation_product_"
                f"decisions_{column}"
            ),
            table_name=(
                "tenant_uom_remediation_product_decisions"
            ),
        )

    op.drop_table(
        "tenant_uom_remediation_product_decisions"
    )

    op.drop_index(
        "ix_tenant_uom_remediation_reviews_one_active",
        table_name="tenant_uom_remediation_reviews",
    )

    for column in reversed(
        (
            "tenant_id",
            "source_uom_id",
            "status",
            "audit_classification",
            "recommended_action",
            "selected_action",
            "selected_canonical_uom_id",
            "planner_fingerprint",
            "created_by",
            "reviewed_by",
        )
    ):
        op.drop_index(
            op.f(
                "ix_tenant_uom_remediation_reviews_"
                f"{column}"
            ),
            table_name=(
                "tenant_uom_remediation_reviews"
            ),
        )

    op.drop_table(
        "tenant_uom_remediation_reviews"
    )
