from __future__ import annotations

from types import SimpleNamespace

import pytest
from flask import Flask

from app.api.customer_contacts import bp as customer_contacts_bp
from app.api.customers import bp as customers_bp
from app.api.errors import register_error_handlers
from app.extensions import db
from app.models import (
    AuditLog,
    Customer,
    CustomerContact,
    Tenant,
)


@pytest.fixture()
def app_context():
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TESTING=True,
    )

    db.init_app(app)

    app.register_blueprint(
        customers_bp,
        url_prefix="/api",
    )
    app.register_blueprint(
        customer_contacts_bp,
        url_prefix="/api",
    )

    register_error_handlers(app)

    with app.app_context():
        Tenant.__table__.create(db.engine)
        Customer.__table__.create(db.engine)
        CustomerContact.__table__.create(db.engine)
        AuditLog.__table__.create(db.engine)

        db.session.add_all(
            [
                Tenant(
                    id="tenant-1",
                    legal_name="Tenant 1",
                    display_name="Tenant 1",
                ),
                Tenant(
                    id="tenant-2",
                    legal_name="Tenant 2",
                    display_name="Tenant 2",
                ),
            ]
        )

        db.session.commit()

        yield app

        db.session.remove()

        AuditLog.__table__.drop(
            db.engine,
            checkfirst=True,
        )
        CustomerContact.__table__.drop(
            db.engine,
            checkfirst=True,
        )
        Customer.__table__.drop(
            db.engine,
            checkfirst=True,
        )
        Tenant.__table__.drop(
            db.engine,
            checkfirst=True,
        )


@pytest.fixture()
def client(
    app_context,
    monkeypatch: pytest.MonkeyPatch,
):
    identity = SimpleNamespace(
        user_id="user-1",
        tenant_id="tenant-1",
        branch_id="branch-1",
    )

    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.get_current_identity",
        lambda: identity,
    )

    monkeypatch.setattr(
        "app.auth.jwt.get_current_identity",
        lambda: identity,
    )

    monkeypatch.setattr(
        "app.api.customers._current_identity",
        lambda: identity,
    )

    monkeypatch.setattr(
        "app.api.customer_contacts._current_identity",
        lambda: identity,
    )

    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.authorization_service.authorize",
        lambda *args, **kwargs: None,
    )

    return app_context.test_client()


def add_customer(
    tenant_id: str,
    customer_number: str,
    first_name: str,
) -> Customer:
    customer = Customer(
        tenant_id=tenant_id,
        customer_number=customer_number,
        first_name=first_name,
        loyalty_points=0,
    )

    db.session.add(customer)
    db.session.flush()

    return customer


def test_customer_finance_profile_can_be_created(client):
    response = client.post(
        "/api/customers",
        json={
            "first_name": "Amina",
            "credit_limit": "25000.00",
            "payment_terms_days": 30,
            "currency": "kes",
            "tax_identifier": "PIN-123",
            "credit_hold": True,
        },
    )

    assert response.status_code == 201

    item = response.json["item"]

    assert item["credit_limit"] == "25000.00"
    assert item["payment_terms_days"] == 30
    assert item["currency"] == "KES"
    assert item["tax_identifier"] == "PIN-123"
    assert item["credit_hold"] is True


def test_customer_finance_profile_can_be_updated(client):
    customer = add_customer(
        "tenant-1",
        "CUST-001",
        "Amina",
    )
    db.session.commit()

    response = client.patch(
        f"/api/customers/{customer.id}/finance-profile",
        json={
            "credit_limit": "50000.00",
            "payment_terms_days": 45,
            "currency": "USD",
            "tax_identifier": "PIN-456",
            "credit_hold": True,
        },
    )

    assert response.status_code == 200

    item = response.json["finance_profile"]

    assert item["credit_limit"] == "50000.00"
    assert item["payment_terms_days"] == 45
    assert item["currency"] == "USD"
    assert item["tax_identifier"] == "PIN-456"
    assert item["credit_hold"] is True

    audit = (
        AuditLog.query
        .filter_by(
            entity_id=customer.id,
            entity_type="CustomerFinanceProfile",
        )
        .order_by(AuditLog.id.desc())
        .first()
    )

    assert audit is not None
    assert audit.module_code == "FINANCE"
    assert audit.action == "CUSTOMER_UPDATED"


def test_customer_finance_profile_rejects_negative_credit_limit(client):
    customer = add_customer(
        "tenant-1",
        "CUST-001",
        "Amina",
    )
    db.session.commit()

    response = client.patch(
        f"/api/customers/{customer.id}/finance-profile",
        json={
            "credit_limit": "-1",
        },
    )

    assert response.status_code == 400
    assert "credit_limit cannot be negative" in response.json["error"]


def test_customer_finance_profile_is_tenant_scoped(client):
    hidden = add_customer(
        "tenant-2",
        "CUST-002",
        "Hidden",
    )
    db.session.commit()

    response = client.patch(
        f"/api/customers/{hidden.id}/finance-profile",
        json={
            "credit_limit": "1000",
        },
    )

    assert response.status_code == 404


def test_customer_contact_create_and_list(client):
    customer = add_customer(
        "tenant-1",
        "CUST-001",
        "Amina",
    )
    db.session.commit()

    response = client.post(
        f"/api/customers/{customer.id}/contacts",
        json={
            "contact_name": "John Otieno",
            "role_title": "Accounts Manager",
            "phone": "+254700000001",
            "email": "john@example.test",
            "preferred_contact_method": "email",
            "is_primary": True,
            "is_billing_contact": True,
        },
    )

    assert response.status_code == 201

    item = response.json["item"]

    assert item["customer_id"] == customer.id
    assert item["tenant_id"] == "tenant-1"
    assert item["contact_name"] == "John Otieno"
    assert item["is_primary"] is True
    assert item["is_billing_contact"] is True
    assert item["is_active"] is True

    list_response = client.get(
        f"/api/customers/{customer.id}/contacts"
    )

    assert list_response.status_code == 200
    assert list_response.json["count"] == 1
    assert list_response.json["items"][0]["id"] == item["id"]


def test_only_one_active_primary_contact_is_retained(client):
    customer = add_customer(
        "tenant-1",
        "CUST-001",
        "Amina",
    )
    db.session.commit()

    first = client.post(
        f"/api/customers/{customer.id}/contacts",
        json={
            "contact_name": "First Contact",
            "is_primary": True,
        },
    )

    assert first.status_code == 201
    first_id = first.json["item"]["id"]

    second = client.post(
        f"/api/customers/{customer.id}/contacts",
        json={
            "contact_name": "Second Contact",
            "is_primary": True,
        },
    )

    assert second.status_code == 201

    first_contact = db.session.get(
        CustomerContact,
        first_id,
    )

    second_contact = db.session.get(
        CustomerContact,
        second.json["item"]["id"],
    )

    assert first_contact.is_primary is False
    assert second_contact.is_primary is True

    active_primary_count = (
        CustomerContact.query
        .filter_by(
            customer_id=customer.id,
            is_active=True,
            is_primary=True,
        )
        .count()
    )

    assert active_primary_count == 1


def test_deactivating_primary_contact_removes_primary_status(client):
    customer = add_customer(
        "tenant-1",
        "CUST-001",
        "Amina",
    )
    db.session.commit()

    created = client.post(
        f"/api/customers/{customer.id}/contacts",
        json={
            "contact_name": "Primary Contact",
            "is_primary": True,
        },
    )

    contact_id = created.json["item"]["id"]

    response = client.patch(
        f"/api/customers/{customer.id}/contacts/{contact_id}",
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 200
    assert response.json["item"]["is_active"] is False
    assert response.json["item"]["is_primary"] is False

    audit = (
        AuditLog.query
        .filter_by(
            entity_id=contact_id,
            entity_type="CustomerContact",
        )
        .order_by(AuditLog.id.desc())
        .first()
    )

    assert audit is not None
    assert audit.action == "CUSTOMER_CONTACT_DEACTIVATED"


def test_customer_contacts_are_tenant_scoped(client):
    hidden = add_customer(
        "tenant-2",
        "CUST-002",
        "Hidden",
    )
    db.session.commit()

    response = client.get(
        f"/api/customers/{hidden.id}/contacts"
    )

    assert response.status_code == 404
