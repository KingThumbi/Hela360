from __future__ import annotations

from types import SimpleNamespace

import pytest
from flask import Flask

from app.api.customers import bp as customers_bp
from app.api.errors import register_error_handlers
from app.auth.exceptions import PermissionDeniedError
from app.extensions import db
from app.models import Customer, Tenant


@pytest.fixture()
def app_context():
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TESTING=True,
    )
    db.init_app(app)
    app.register_blueprint(customers_bp, url_prefix="/api")
    register_error_handlers(app)

    with app.app_context():
        Tenant.__table__.create(db.engine)
        Customer.__table__.create(db.engine)

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
        Customer.__table__.drop(db.engine)
        Tenant.__table__.drop(db.engine)


@pytest.fixture()
def client(app_context, monkeypatch: pytest.MonkeyPatch):
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
        "app.services.tenant.auth.decorators.authorization_service.authorize",
        lambda *args, **kwargs: None,
    )

    return app_context.test_client()


def add_customer(
    tenant_id: str,
    customer_number: str,
    first_name: str,
    *,
    last_name: str | None = None,
    phone: str | None = None,
    email: str | None = None,
    id_number: str | None = None,
    city: str | None = None,
    is_active: bool = True,
) -> Customer:
    customer = Customer(
        tenant_id=tenant_id,
        customer_number=customer_number,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        email=email,
        id_number=id_number,
        city=city,
        is_active=is_active,
    )
    db.session.add(customer)
    db.session.flush()
    return customer


def test_customer_list_empty_envelope(client):
    response = client.get("/api/customers")

    assert response.status_code == 200
    assert response.json == {
        "ok": True,
        "count": 0,
        "items": [],
    }


def test_customer_list_returns_serialized_tenant_customers(client):
    add_customer(
        "tenant-1",
        "CUST-001",
        "Amina",
        last_name="Otieno",
        phone="+254700000001",
        email="amina@example.test",
        id_number="ID-001",
        city="Nairobi",
    )
    add_customer(
        "tenant-2",
        "CUST-002",
        "Hidden",
    )
    db.session.commit()

    response = client.get("/api/customers")

    assert response.status_code == 200
    assert response.json["ok"] is True
    assert response.json["count"] == 1
    assert len(response.json["items"]) == 1

    item = response.json["items"][0]
    assert item["tenant_id"] == "tenant-1"
    assert item["customer_number"] == "CUST-001"
    assert item["first_name"] == "Amina"
    assert item["last_name"] == "Otieno"
    assert item["full_name"] == "Amina Otieno"
    assert item["phone"] == "+254700000001"
    assert item["email"] == "amina@example.test"
    assert item["city"] == "Nairobi"
    assert item["loyalty_points"] == "0.00"
    assert item["is_active"] is True


def test_customer_list_search_is_tenant_scoped(client):
    add_customer(
        "tenant-1",
        "CUST-001",
        "Amina",
    )
    add_customer(
        "tenant-2",
        "CUST-002",
        "Tenant",
        phone="MATCH-ONLY-OTHER-TENANT",
    )
    db.session.commit()

    response = client.get("/api/customers?search=match")

    assert response.status_code == 200
    assert response.json["ok"] is True
    assert response.json["count"] == 0
    assert response.json["items"] == []


def test_customer_list_search_matches_supported_fields(client):
    add_customer(
        "tenant-1",
        "CUST-001",
        "Amina",
        phone="+254700000001",
    )
    add_customer(
        "tenant-1",
        "CUST-002",
        "Brian",
    )
    db.session.commit()

    response = client.get("/api/customers?search=700000001")

    assert response.status_code == 200
    assert response.json["count"] == 1
    assert response.json["items"][0]["customer_number"] == "CUST-001"


def test_customer_list_pagination_count_is_tenant_scoped(client):
    add_customer("tenant-1", "CUST-001", "Alpha")
    add_customer("tenant-1", "CUST-002", "Beta")
    add_customer("tenant-1", "CUST-003", "Gamma")
    add_customer("tenant-2", "CUST-004", "Other")
    db.session.commit()

    response = client.get("/api/customers?page=2&per_page=1")

    assert response.status_code == 200
    assert response.json["ok"] is True
    assert response.json["count"] == 3
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["first_name"] == "Beta"


def test_customer_list_rejects_invalid_pagination(client):
    response = client.get("/api/customers?page=0&per_page=25")

    assert response.status_code == 400
    assert response.json == {
        "ok": False,
        "error": "page must be a positive integer.",
    }


def test_customer_detail_remains_tenant_scoped(client):
    customer = add_customer(
        "tenant-1",
        "CUST-001",
        "Amina",
    )
    hidden = add_customer(
        "tenant-2",
        "CUST-002",
        "Hidden",
    )
    db.session.commit()

    detail_response = client.get(f"/api/customers/{customer.id}")
    hidden_response = client.get(f"/api/customers/{hidden.id}")

    assert detail_response.status_code == 200
    assert detail_response.json["item"]["id"] == customer.id
    assert hidden_response.status_code == 404


def test_customer_create_uses_authenticated_tenant(client):
    response = client.post(
        "/api/customers",
        json={
            "first_name": "Amina",
            "last_name": "Otieno",
            "phone": "+254700000001",
            "email": "AMINA@EXAMPLE.TEST",
            "date_of_birth": "1990-01-02",
            "city": "Nairobi",
        },
    )

    assert response.status_code == 201
    assert response.json["ok"] is True
    assert response.json["item"]["tenant_id"] == "tenant-1"
    assert response.json["item"]["customer_number"] == "CUST-00001"
    assert response.json["item"]["email"] == "amina@example.test"
    assert response.json["item"]["date_of_birth"] == "1990-01-02"


def test_customer_create_rejects_invalid_date_of_birth(client):
    response = client.post(
        "/api/customers",
        json={
            "first_name": "Amina",
            "date_of_birth": "02-01-1990",
        },
    )

    assert response.status_code == 400
    assert response.json == {
        "ok": False,
        "error": "date_of_birth must use YYYY-MM-DD.",
    }


def test_customer_create_rejects_duplicate_phone(client):
    add_customer(
        "tenant-1",
        "CUST-001",
        "Amina",
        phone="+254700000001",
    )
    db.session.commit()

    response = client.post(
        "/api/customers",
        json={
            "first_name": "Brian",
            "phone": "+254700000001",
        },
    )

    assert response.status_code == 409
    assert response.json == {
        "ok": False,
        "error": "A customer with that phone already exists.",
    }


def test_customer_list_missing_permission_is_rejected(
    app_context,
    monkeypatch: pytest.MonkeyPatch,
):
    identity = SimpleNamespace(
        user_id="user-1",
        tenant_id="tenant-1",
        branch_id=None,
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
        "app.services.tenant.auth.decorators.authorization_service.authorize",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            PermissionDeniedError("Permission denied.")
        ),
    )

    response = app_context.test_client().get("/api/customers")

    assert response.status_code == 403
    assert response.json["error"]["code"] == "AUTHORIZATION_DENIED"
