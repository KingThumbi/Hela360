# app/models/tenant.py
from app.extensions import db
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Tenant(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "tenants"

    legal_name = db.Column(db.String(200), nullable=False)
    display_name = db.Column(db.String(200), nullable=False)
    business_type = db.Column(db.String(50), nullable=False, default="pharmacy")
    phone = db.Column(db.String(50))
    email = db.Column(db.String(150))
    country_code = db.Column(db.String(10), nullable=False, default="KE")
    timezone = db.Column(db.String(100), nullable=False, default="Africa/Nairobi")
    base_currency = db.Column(db.String(3), nullable=False, default="KES")
    status = db.Column(db.String(30), nullable=False, default="active")

    branches = db.relationship("Branch", back_populates="tenant", cascade="all, delete-orphan")


class Branch(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "branches"
    __table_args__ = (
        db.UniqueConstraint("tenant_id", "code", name="uq_branches_tenant_code"),
        db.UniqueConstraint("tenant_id", "name", name="uq_branches_tenant_name"),
    )

    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    code = db.Column(db.String(30), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(50))
    email = db.Column(db.String(150))
    address_line1 = db.Column(db.String(200))
    address_line2 = db.Column(db.String(200))
    city = db.Column(db.String(100))
    county_state = db.Column(db.String(100))
    country = db.Column(db.String(100), default="Kenya")
    is_head_office = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    tenant = db.relationship("Tenant", back_populates="branches")