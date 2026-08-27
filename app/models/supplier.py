from app.extensions import db
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Supplier(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "suppliers"
    __table_args__ = (
        db.UniqueConstraint(
            "tenant_id",
            "supplier_code",
            name="uq_suppliers_tenant_supplier_code",
        ),
        db.UniqueConstraint(
            "tenant_id",
            "tax_number",
            name="uq_suppliers_tenant_tax_number",
        ),
        db.UniqueConstraint(
            "tenant_id",
            "registration_number",
            name="uq_suppliers_tenant_registration_number",
        ),
    )

    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    supplier_code = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    legal_name = db.Column(db.String(200))
    contact_person = db.Column(db.String(150))
    email = db.Column(db.String(150), index=True)
    phone = db.Column(db.String(50), index=True)
    alternate_phone = db.Column(db.String(50))
    address_line_1 = db.Column(db.String(200))
    address_line_2 = db.Column(db.String(200))
    city = db.Column(db.String(100))
    county_or_region = db.Column(db.String(100))
    country = db.Column(db.String(100))
    postal_code = db.Column(db.String(30))
    tax_number = db.Column(db.String(80))
    registration_number = db.Column(db.String(80))
    payment_terms_days = db.Column(db.Integer, nullable=False, default=0)
    credit_limit = db.Column(db.Numeric(18, 2), nullable=False, default=0)
    currency = db.Column(db.String(3), nullable=False, default="KES")
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
