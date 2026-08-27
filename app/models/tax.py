"""
Hela360 Tax Code Model
======================
"""

from app.extensions import db
from app.models.base import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class TaxCode(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    db.Model,
):
    __tablename__ = "tax_codes"

    __table_args__ = (
        db.UniqueConstraint(
            "tenant_id",
            "code",
            name="uq_tax_codes_tenant_code",
        ),
    )

    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    code = db.Column(
        db.String(30),
        nullable=False,
    )

    name = db.Column(
        db.String(100),
        nullable=False,
    )

    rate = db.Column(
        db.Numeric(9, 4),
        nullable=False,
        default=0,
    )

    description = db.Column(
        db.Text,
        nullable=True,
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )
