# app/models/shift.py
import uuid
from datetime import datetime, timezone

from app.extensions import db


def utc_now():
    return datetime.now(timezone.utc)


class TillShift(db.Model):
    __tablename__ = "till_shifts"

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = db.Column(db.UUID(as_uuid=True), nullable=False, index=True)
    branch_id = db.Column(db.UUID(as_uuid=True), nullable=False, index=True)
    till_id = db.Column(db.UUID(as_uuid=True), nullable=False, index=True)
    cashier_id = db.Column(db.UUID(as_uuid=True), nullable=False, index=True)

    status = db.Column(db.String(20), nullable=False, default="open", index=True)

    opening_float = db.Column(db.Numeric(18, 2), nullable=False, default=0)
    closing_cash = db.Column(db.Numeric(18, 2), nullable=True)

    notes = db.Column(db.Text, nullable=True)

    opened_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now, index=True)
    closed_at = db.Column(db.DateTime(timezone=True), nullable=True, index=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    def __repr__(self):
        return f"<TillShift {self.id} till={self.till_id} cashier={self.cashier_id} status={self.status}>"