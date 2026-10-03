from app.extensions import db
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class CustomerContact(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    db.Model,
):
    __tablename__ = "customer_contacts"

    __table_args__ = (
        db.Index(
            "ix_customer_contacts_tenant_customer",
            "tenant_id",
            "customer_id",
        ),
        db.Index(
            "ix_customer_contacts_tenant_active",
            "tenant_id",
            "is_active",
        ),
        db.Index(
            "uq_customer_contacts_primary",
            "customer_id",
            unique=True,
            postgresql_where=db.text(
                "is_primary = true AND is_active = true"
            ),
            sqlite_where=db.text(
                "is_primary = 1 AND is_active = 1"
            ),
        ),
    )

    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    customer_id = db.Column(
        db.String(36),
        db.ForeignKey("customers.id"),
        nullable=False,
        index=True,
    )

    contact_name = db.Column(
        db.String(150),
        nullable=False,
    )

    role_title = db.Column(
        db.String(100),
        nullable=True,
    )

    phone = db.Column(
        db.String(50),
        nullable=True,
    )

    alternate_phone = db.Column(
        db.String(50),
        nullable=True,
    )

    email = db.Column(
        db.String(150),
        nullable=True,
    )

    preferred_contact_method = db.Column(
        db.String(30),
        nullable=True,
    )

    is_primary = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )

    is_billing_contact = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

    notes = db.Column(
        db.Text,
        nullable=True,
    )

    customer = db.relationship(
        "Customer",
        back_populates="contacts",
    )
