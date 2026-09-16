"""
Tenant UOM remediation review models.

These tables persist human review state and planner evidence for tenant
UOM normalization. They do not themselves modify operational Product,
ProductUnit, UnitOfMeasure, inventory, or sales records.
"""

from app.extensions import db
from app.models.base import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class TenantUOMRemediationReview(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    db.Model,
):
    __tablename__ = "tenant_uom_remediation_reviews"

    __table_args__ = (
        db.CheckConstraint(
            (
                "status IN ("
                "'pending', "
                "'approved', "
                "'rejected', "
                "'superseded', "
                "'executed'"
                ")"
            ),
            name="ck_tenant_uom_remediation_reviews_status",
        ),
        db.Index(
            "ix_tenant_uom_remediation_reviews_one_active",
            "tenant_id",
            "source_uom_id",
            unique=True,
            postgresql_where=db.text(
                "status IN ('pending', 'approved')"
            ),
        ),
    )

    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    source_uom_id = db.Column(
        db.String(36),
        db.ForeignKey("units_of_measure.id"),
        nullable=False,
        index=True,
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="pending",
        index=True,
    )

    audit_classification = db.Column(
        db.String(40),
        nullable=False,
        index=True,
    )

    recommended_action = db.Column(
        db.String(50),
        nullable=False,
        index=True,
    )

    suggested_canonical_code = db.Column(
        db.String(20),
    )

    selected_action = db.Column(
        db.String(50),
        index=True,
    )

    selected_canonical_uom_id = db.Column(
        db.String(36),
        db.ForeignKey("canonical_units_of_measure.id"),
        index=True,
    )

    planner_version = db.Column(
        db.String(30),
        nullable=False,
    )

    planner_fingerprint = db.Column(
        db.String(64),
        nullable=False,
        index=True,
    )

    planner_snapshot = db.Column(
        db.JSON,
        nullable=False,
    )

    created_by = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    reviewed_by = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        index=True,
    )

    reviewed_at = db.Column(
        db.DateTime(timezone=True),
    )

    review_reason = db.Column(
        db.Text,
    )

    executed_by = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        index=True,
    )

    executed_at = db.Column(
        db.DateTime(timezone=True),
    )

    execution_summary = db.Column(
        db.JSON,
    )


class TenantUOMRemediationProductDecision(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    db.Model,
):
    __tablename__ = (
        "tenant_uom_remediation_product_decisions"
    )

    __table_args__ = (
        db.UniqueConstraint(
            "review_id",
            "product_id",
            name=(
                "uq_tenant_uom_remediation_decisions_"
                "review_product"
            ),
        ),
    )

    review_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "tenant_uom_remediation_reviews.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    product_id = db.Column(
        db.String(36),
        db.ForeignKey("products.id"),
        nullable=False,
        index=True,
    )

    source_product_unit_id = db.Column(
        db.String(36),
        db.ForeignKey("product_units.id"),
        index=True,
    )

    recommended_action = db.Column(
        db.String(50),
        nullable=False,
        index=True,
    )

    suggested_canonical_code = db.Column(
        db.String(20),
    )

    selected_action = db.Column(
        db.String(50),
        index=True,
    )

    target_canonical_uom_id = db.Column(
        db.String(36),
        db.ForeignKey("canonical_units_of_measure.id"),
        index=True,
    )

    target_tenant_uom_id = db.Column(
        db.String(36),
        db.ForeignKey("units_of_measure.id"),
        index=True,
    )

    preserve_historical_unit = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

    review_note = db.Column(
        db.Text,
    )


__all__ = [
    "TenantUOMRemediationProductDecision",
    "TenantUOMRemediationReview",
]
