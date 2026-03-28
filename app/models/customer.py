# app/models/customer.py
from app.extensions import db
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Customer(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "customers"
    __table_args__ = (db.UniqueConstraint("tenant_id", "customer_number", name="uq_customers_tenant_customer_number"),)

    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    customer_number = db.Column(db.String(50), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100))
    other_names = db.Column(db.String(150))
    phone = db.Column(db.String(50), index=True)
    email = db.Column(db.String(150), index=True)
    gender = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    id_number = db.Column(db.String(50))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    loyalty_points = db.Column(db.Numeric(18, 2), nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)