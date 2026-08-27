# app/models/shift.py
from app.extensions import db
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class TillShift(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    db.Model,
):
    """
    Operational POS till shift.

    A till shift represents the period during which a cashier is
    responsible for a specific till within a tenant and branch.

    Identifier Strategy
    -------------------
    Hela360 uses UUID-formatted String(36) identifiers throughout the
    tenant application domain.

    TillShift follows the same canonical identifier strategy so that
    tenant, branch, till, cashier, sale, and refund relationships remain
    type-consistent across the ERP.
    """

    __tablename__ = "till_shifts"

    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    branch_id = db.Column(
        db.String(36),
        db.ForeignKey("branches.id"),
        nullable=False,
        index=True,
    )

    till_id = db.Column(
        db.String(36),
        db.ForeignKey("tills.id"),
        nullable=False,
        index=True,
    )

    cashier_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    active_session_id = db.Column(
        db.String(36),
        db.ForeignKey("user_sessions.id"),
        nullable=True,
        index=True,
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="open",
        index=True,
    )

    opening_float = db.Column(
        db.Numeric(18, 2),
        nullable=False,
        default=0,
    )

    closing_cash = db.Column(
        db.Numeric(18, 2),
        nullable=True,
    )

    notes = db.Column(
        db.Text,
        nullable=True,
    )

    opened_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    closed_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    def __repr__(self):
        return (
            f"<TillShift {self.id} "
            f"till={self.till_id} "
            f"cashier={self.cashier_id} "
            f"status={self.status}>"
        )