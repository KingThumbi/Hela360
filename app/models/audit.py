# app/models/audit.py
from app.extensions import db
from app.models.base import TimestampMixin


class AuditLog(TimestampMixin, db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    tenant_id = db.Column(db.String(36), nullable=False, index=True)
    branch_id = db.Column(db.String(36), index=True)
    user_id = db.Column(db.String(36), index=True)
    module_code = db.Column(db.String(50), nullable=False, index=True)
    entity_type = db.Column(db.String(100), nullable=False, index=True)
    entity_id = db.Column(db.String(36), index=True)
    action = db.Column(db.String(50), nullable=False, index=True)
    old_values = db.Column(db.JSON)
    new_values = db.Column(db.JSON)
    reason = db.Column(db.Text)
    ip_address = db.Column(db.String(64))
    user_agent = db.Column(db.Text)