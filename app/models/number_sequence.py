"""
Hela360 Number Sequence Model
=============================
"""

from app.extensions import db
from app.models.base import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class NumberSequence(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    db.Model,
):
    __tablename__ = "number_sequences"

    __table_args__ = (
        db.UniqueConstraint(
            "tenant_id",
            "namespace",
            name="uq_number_sequences_tenant_namespace",
        ),
    )

    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    namespace = db.Column(
        db.String(50),
        nullable=False,
    )

    next_value = db.Column(
        db.BigInteger,
        nullable=False,
        default=1,
    )
