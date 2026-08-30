from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from flask import Flask

from app.api.catalogue import bp as catalogue_bp
from app.api.errors import register_error_handlers
from app.auth.exceptions import PermissionDeniedError
from app.extensions import db
from app.models import MasterItem, Product, Tenant


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
        catalogue_bp,
        url_prefix="/api",
    )
    register_error_handlers(app)

    with app.app_context():
        Tenant.__table__.create(db.engine)
        MasterItem.__table__.create(db.engine)
        Product.__table__.create(db.engine)

        db.session.add_all(
            [
                Tenant(
                    id="tenant-1",
                    legal_name="Tenant 1",
                    display_name="Tenant 1",
                    business_code="T1",
                    workspace_slug="tenant-1",
                ),
                Tenant(
                    id="tenant-2",
                    legal_name="Tenant 2",
                    display_name="Tenant 2",
                    business_code="T2",
                    workspace_slug="tenant-2",
                ),
            ]
        )

        db.session.commit()

        yield app

        db.session.remove()

        Product.__table__.drop(db.engine)
        MasterItem.__table__.drop(db.engine)
        Tenant.__table__.drop(db.engine)


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
        "app.services.tenant.auth.decorators."
        "get_current_identity",
        lambda: identity,
    )

    monkeypatch.setattr(
        "app.auth.jwt.get_current_identity",
        lambda: identity,
    )

    monkeypatch.setattr(
        "app.api.catalogue.get_current_identity",
        lambda: identity,
    )

    monkeypatch.setattr(
        "app.services.tenant.auth.decorators."
        "authorization_service.authorize",
        lambda *args, **kwargs: None,
    )

    return app_context.test_client()


def _master_item(
    *,
    code: str,
    name: str,
    review_status: str = "approved",
    is_active: bool = True,
    generic_name: str | None = None,
    dosage_form: str | None = None,
    category_name: str | None = None,
) -> MasterItem:
    item = MasterItem(
        id=str(uuid4()),
        master_code=code,
        canonical_name=name,
        generic_name=generic_name,
        dosage_form=dosage_form,
        category_name=category_name,
        item_class="medicine",
        review_status=review_status,
        is_active=is_active,
    )

    db.session.add(item)
    db.session.flush()

    return item


def _product(
    *,
    tenant_id: str,
    master_item_id: str,
    sku: str,
    name: str,
    is_active: bool = True,
) -> Product:
    product = Product(
        id=str(uuid4()),
        tenant_id=tenant_id,
        master_item_id=master_item_id,
        internal_sku=sku,
        name=name,
        is_active=is_active,
    )

    db.session.add(product)
    db.session.flush()

    return product


def test_catalogue_list_returns_expected_envelope(client):
    item = _master_item(
        code="HMI-000001",
        name="Amoxicillin 500 mg Capsules",
        generic_name="Amoxicillin",
        dosage_form="Capsule",
        category_name="Antibiotics",
    )

    db.session.commit()

    response = client.get(
        "/api/catalogue/items"
    )

    assert response.status_code == 200
    assert response.json["ok"] is True
    assert response.json["count"] == 1

    assert response.json["pagination"] == {
        "page": 1,
        "per_page": 25,
        "total": 1,
        "pages": 1,
        "has_prev": False,
        "has_next": False,
    }

    result = response.json["items"][0]

    assert result["id"] == item.id
    assert result["master_code"] == "HMI-000001"
    assert (
        result["canonical_name"]
        == "Amoxicillin 500 mg Capsules"
    )
    assert result["adoption"] == {
        "is_adopted": False,
        "product_id": None,
        "internal_sku": None,
        "product_name": None,
        "product_is_active": None,
    }


def test_catalogue_list_hides_draft_and_inactive_items(
    client,
):
    _master_item(
        code="HMI-VISIBLE",
        name="Visible Item",
    )

    _master_item(
        code="HMI-DRAFT",
        name="Draft Item",
        review_status="draft",
    )

    _master_item(
        code="HMI-INACTIVE",
        name="Inactive Item",
        is_active=False,
    )

    db.session.commit()

    response = client.get(
        "/api/catalogue/items"
    )

    assert response.status_code == 200
    assert response.json["count"] == 1
    assert (
        response.json["items"][0]["master_code"]
        == "HMI-VISIBLE"
    )


def test_catalogue_list_reports_current_tenant_adoption(
    client,
):
    item = _master_item(
        code="HMI-ADOPTED",
        name="Adopted Master Item",
    )

    product = _product(
        tenant_id="tenant-1",
        master_item_id=item.id,
        sku="T1-2026-000001",
        name="Tenant Product",
    )

    db.session.commit()

    response = client.get(
        "/api/catalogue/items"
    )

    assert response.status_code == 200

    adoption = response.json["items"][0]["adoption"]

    assert adoption["is_adopted"] is True
    assert adoption["product_id"] == product.id
    assert adoption["internal_sku"] == "T1-2026-000001"
    assert adoption["product_name"] == "Tenant Product"
    assert adoption["product_is_active"] is True


def test_catalogue_adoption_is_tenant_isolated(
    client,
):
    item = _master_item(
        code="HMI-OTHER-TENANT",
        name="Other Tenant Item",
    )

    _product(
        tenant_id="tenant-2",
        master_item_id=item.id,
        sku="T2-2026-000001",
        name="Other Tenant Product",
    )

    db.session.commit()

    response = client.get(
        "/api/catalogue/items"
    )

    assert response.status_code == 200

    adoption = response.json["items"][0]["adoption"]

    assert adoption["is_adopted"] is False
    assert adoption["product_id"] is None
    assert adoption["internal_sku"] is None


def test_catalogue_available_filter_excludes_adopted_items(
    client,
):
    adopted = _master_item(
        code="HMI-ADOPTED-002",
        name="Adopted Item",
    )

    available = _master_item(
        code="HMI-AVAILABLE",
        name="Available Item",
    )

    _product(
        tenant_id="tenant-1",
        master_item_id=adopted.id,
        sku="ADOPTED-002",
        name="Adopted Product",
    )

    db.session.commit()

    response = client.get(
        "/api/catalogue/items"
        "?adoption_status=available"
    )

    assert response.status_code == 200
    assert response.json["count"] == 1

    assert (
        response.json["items"][0]["id"]
        == available.id
    )


def test_catalogue_adopted_filter_returns_adopted_items(
    client,
):
    adopted = _master_item(
        code="HMI-ADOPTED-003",
        name="Adopted Item",
    )

    _master_item(
        code="HMI-AVAILABLE-003",
        name="Available Item",
    )

    _product(
        tenant_id="tenant-1",
        master_item_id=adopted.id,
        sku="ADOPTED-003",
        name="Adopted Product",
    )

    db.session.commit()

    response = client.get(
        "/api/catalogue/items"
        "?adoption_status=adopted"
    )

    assert response.status_code == 200
    assert response.json["count"] == 1

    assert (
        response.json["items"][0]["id"]
        == adopted.id
    )


def test_catalogue_search_uses_q_alias(client):
    matching = _master_item(
        code="HMI-AMOX",
        name="Amoxicillin 500 mg Capsules",
        generic_name="Amoxicillin",
    )

    _master_item(
        code="HMI-PARA",
        name="Paracetamol Tablets",
        generic_name="Paracetamol",
    )

    db.session.commit()

    response = client.get(
        "/api/catalogue/items?q=amoxicillin"
    )

    assert response.status_code == 200
    assert response.json["count"] == 1
    assert (
        response.json["items"][0]["id"]
        == matching.id
    )


def test_catalogue_list_rejects_invalid_adoption_status(
    client,
):
    response = client.get(
        "/api/catalogue/items"
        "?adoption_status=unknown"
    )

    assert response.status_code == 400
    assert response.json["ok"] is False
    assert (
        response.json["error"]
        == "adoption_status must be one of: "
        "all, available, adopted."
    )


def test_catalogue_list_rejects_excessive_page_size(
    client,
):
    response = client.get(
        "/api/catalogue/items?per_page=101"
    )

    assert response.status_code == 400
    assert response.json == {
        "ok": False,
        "error": "per_page must not exceed 100.",
    }


def test_catalogue_detail_returns_item(client):
    item = _master_item(
        code="HMI-DETAIL",
        name="Catalogue Detail Item",
    )

    db.session.commit()

    response = client.get(
        f"/api/catalogue/items/{item.id}"
    )

    assert response.status_code == 200
    assert response.json["ok"] is True
    assert response.json["item"]["id"] == item.id
    assert (
        response.json["item"]["master_code"]
        == "HMI-DETAIL"
    )


def test_catalogue_detail_returns_404_for_missing_item(
    client,
):
    response = client.get(
        "/api/catalogue/items/"
        "00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 404
    assert response.json == {
        "ok": False,
        "error": "Catalogue item not found.",
    }


def test_catalogue_list_requires_products_view_permission(
    app_context,
    monkeypatch: pytest.MonkeyPatch,
):
    identity = SimpleNamespace(
        user_id="user-1",
        tenant_id="tenant-1",
        branch_id="branch-1",
    )

    monkeypatch.setattr(
        "app.services.tenant.auth.decorators."
        "get_current_identity",
        lambda: identity,
    )

    monkeypatch.setattr(
        "app.services.tenant.auth.decorators."
        "authorization_service.authorize",
        lambda *args, **kwargs: (
            _ for _ in ()
        ).throw(
            PermissionDeniedError(
                "Permission denied."
            )
        ),
    )

    response = app_context.test_client().get(
        "/api/catalogue/items"
    )

    assert response.status_code == 403
    assert (
        response.json["error"]["code"]
        == "AUTHORIZATION_DENIED"
    )
