from __future__ import annotations

from types import SimpleNamespace

import pytest
from flask import Flask

from app.api.errors import register_error_handlers
from app.api.suppliers import bp as suppliers_bp
from app.auth.exceptions import PermissionDeniedError
from app.extensions import db
from app.models import Supplier, Tenant
from app.schemas import CreateSupplierRequest, SupplierListFilters, UpdateSupplierRequest
from app.services.tenant.procurement import SupplierService


@pytest.fixture()
def app_context():
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TESTING=True,
    )
    db.init_app(app)
    app.register_blueprint(suppliers_bp, url_prefix="/api")
    register_error_handlers(app)

    with app.app_context():
        Tenant.__table__.create(db.engine)
        Supplier.__table__.create(db.engine)
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
        Supplier.__table__.drop(db.engine)
        Tenant.__table__.drop(db.engine)


@pytest.fixture()
def service() -> SupplierService:
    return SupplierService()


def create_request(code: str = "SUP-001", name: str = "Acme Medical"):
    return CreateSupplierRequest.from_payload(
        {
            "supplier_code": code,
            "name": name,
            "email": "orders@example.com",
            "phone": "+254700000000",
            "payment_terms_days": 30,
            "credit_limit": "10000.00",
            "currency": "KES",
        }
    )


def test_create_list_get_update_and_lifecycle(app_context, service):
    supplier = service.create_supplier("tenant-1", create_request())

    assert supplier.id
    assert supplier.tenant_id == "tenant-1"
    assert supplier.is_active is True

    items, pagination = service.list_suppliers(
        "tenant-1",
        SupplierListFilters(page=1, page_size=10),
    )

    assert [item.id for item in items] == [supplier.id]
    assert pagination["total"] == 1
    assert pagination["page"] == 1

    found = service.get_supplier("tenant-1", supplier.id)
    assert found.supplier_code == "SUP-001"

    updated = service.update_supplier(
        "tenant-1",
        supplier.id,
        UpdateSupplierRequest.from_payload(
            {
                "name": "Acme Medical Supplies",
                "credit_limit": "25000.00",
            }
        ),
    )
    assert updated.name == "Acme Medical Supplies"
    assert str(updated.credit_limit) == "25000.00"

    inactive = service.deactivate_supplier("tenant-1", supplier.id)
    assert inactive.is_active is False

    active = service.reactivate_supplier("tenant-1", supplier.id)
    assert active.is_active is True


def test_tenant_isolation_and_cross_tenant_lookup(app_context, service):
    supplier = service.create_supplier("tenant-1", create_request())

    assert service.list_suppliers(
        "tenant-2",
        SupplierListFilters(page=1, page_size=10),
    )[0] == []

    with pytest.raises(Exception, match="Supplier not found"):
        service.get_supplier("tenant-2", supplier.id)


def test_duplicate_supplier_code_rejected_per_tenant(app_context, service):
    service.create_supplier("tenant-1", create_request())

    with pytest.raises(Exception, match="supplier_code already exists"):
        service.create_supplier("tenant-1", create_request())

    other_tenant = service.create_supplier("tenant-2", create_request())
    assert other_tenant.tenant_id == "tenant-2"


def test_validation_failure():
    with pytest.raises(Exception, match="email must be a valid email address"):
        CreateSupplierRequest.from_payload(
            {
                "supplier_code": "SUP-001",
                "name": "Acme Medical",
                "email": "not-email",
            }
        )


def test_inactive_filter(app_context, service):
    active = service.create_supplier("tenant-1", create_request("SUP-001", "Active"))
    inactive = service.create_supplier("tenant-1", create_request("SUP-002", "Inactive"))
    service.deactivate_supplier("tenant-1", inactive.id)

    items, pagination = service.list_suppliers(
        "tenant-1",
        SupplierListFilters(page=1, page_size=10, is_active=True),
    )

    assert [item.id for item in items] == [active.id]
    assert pagination["total"] == 1


def test_supplier_api_envelope_and_authorization(
    app_context,
    monkeypatch: pytest.MonkeyPatch,
):
    client = app_context.test_client()
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
        "app.api.utils.get_current_identity",
        lambda: identity,
    )
    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.authorization_service.authorize",
        lambda *args, **kwargs: None,
    )

    create_response = client.post(
        "/api/suppliers",
        json={
            "supplier_code": "SUP-001",
            "name": "Acme Medical",
        },
    )

    assert create_response.status_code == 201
    assert create_response.json["ok"] is True
    assert create_response.json["item"]["tenant_id"] == "tenant-1"

    list_response = client.get("/api/suppliers?page=1&page_size=5")

    assert list_response.status_code == 200
    assert list_response.json["ok"] is True
    assert list_response.json["pagination"]["page_size"] == 5
    assert list_response.json["pagination"]["total"] == 1

    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.authorization_service.authorize",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            PermissionDeniedError("Permission denied.")
        ),
    )

    denied_response = client.get("/api/suppliers")

    assert denied_response.status_code == 403
    assert denied_response.json["error"]["code"] == "AUTHORIZATION_DENIED"
