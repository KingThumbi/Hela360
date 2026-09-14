"""
Hela360 Canonical Unit-of-Measure Models
========================================

Platform-owned semantic unit catalogue.

CanonicalUnitOfMeasure defines what a unit means globally across Hela360.
It intentionally has no tenant_id.

Tenant UnitOfMeasure records remain operational tenant references.
ProductUnit remains the source of product-specific conversion factors.
"""

from app.extensions import db
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class CanonicalUnitOfMeasure(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    db.Model,
):
    """
    Platform-wide canonical unit-of-measure identity.

    Examples:
    - TAB / Tablet
    - CAP / Capsule
    - BOT / Bottle
    - TUBE / Tube
    - VIAL / Vial
    - EA / Each
    - BOX / Box
    - CARTON / Carton

    Conversion factors do not belong here. Product-specific conversion is
    represented by ProductUnit.conversion_factor_to_base.
    """

    __tablename__ = "canonical_units_of_measure"
    __table_args__ = (
        db.UniqueConstraint(
            "code",
            name="uq_canonical_units_of_measure_code",
        ),
    )

    code = db.Column(
        db.String(20),
        nullable=False,
        index=True,
    )

    name = db.Column(
        db.String(100),
        nullable=False,
        index=True,
    )

    unit_family = db.Column(
        db.String(30),
        nullable=False,
        index=True,
    )

    description = db.Column(
        db.Text,
    )

    is_packaging_unit = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    sort_order = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )
