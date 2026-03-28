# app/models/base.py
import uuid
from datetime import datetime, timezone
from app.extensions import db


class TimestampMixin:
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class UUIDPrimaryKeyMixin:
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))