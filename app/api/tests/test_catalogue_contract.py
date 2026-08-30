from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from flask import Flask

from app.api.catalogue import bp as catalogue_bp
from app.api.errors import register_error_handlers
from app.auth.exceptions import PermissionDeniedError
from app.extensions import db
from app.services.common.audit_service import AuditService
from app.models import (
    AuditLog,
    Brand,
    MasterItem,
    NumberSequence,
    Product,
    ProductCategory,
    ProductUnit,
    Tenant,
    UnitOfMeasure,
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
        catalogue_bp,
        url_prefix="/api",
    )
    register_error_handlers(app)

    with app.app_context():
        Tenant.__table__.create(db.engine)
        NumberSequence.__table__.create(db.engine)
        ProductCategory.__table__.create(db.engine)
        Brand.__table__.create(db.engine)
        UnitOfMeasure.__table__.create(db.engine)
        MasterItem.__table__.create(db.engine)
        Product.__table__.create(db.engine)
        ProductUnit.__table__.create(db.engine)
        AuditLog.__table__.create(db.engine)

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

        AuditLog.__table__.drop(db.engine)
        ProductUnit.__table__.drop(db.engine)
        Product.__table__.drop(db.engine)
        MasterItem.__table__.drop(db.engine)
        UnitOfMeasure.__table__.drop(db.engine)
        Brand.__table__.drop(db.engine)
        ProductCategory.__table__.drop(db.engine)
        NumberSequence.__table__.drop(db.engine)
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

    monkeypatch.setattr(
        AuditService,
        "log",
        lambda self, **kwargs: SimpleNamespace(
            id="audit-test-1"
        ),
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


def test_catalogue_adoption_creates_tenant_product(client):
    item = _master_item(
        code="HMI-API-ADOPT-001",
        name="Amoxicillin 500 mg Capsules",
        generic_name="Amoxicillin",
        category_name="Antibiotics",
    )

    db.session.commit()

    response = client.post(
        f"/api/catalogue/items/{item.id}/adopt",
        json={
            "internal_sku": "CAT-001",
        },
    )

    assert response.status_code == 201
    assert response.json["ok"] is True

    product_data = response.json["item"]

    assert product_data["tenant_id"] == "tenant-1"
    assert product_data["master_item_id"] == item.id
    assert product_data["internal_sku"] == "CAT-001"
    assert (
        product_data["name"]
        == "Amoxicillin 500 mg Capsules"
    )
    assert (
        product_data["generic_name"]
        == "Amoxicillin"
    )

    product = (
        db.session.query(Product)
        .filter(
            Product.tenant_id == "tenant-1",
            Product.master_item_id == item.id,
        )
        .one()
    )

    assert product.id == product_data["id"]


def test_catalogue_adoption_uses_generated_sku_when_omitted(
    client,
):
    item = _master_item(
        code="HMI-API-ADOPT-002",
        name="Generated SKU Product",
    )

    db.session.commit()

    response = client.post(
        f"/api/catalogue/items/{item.id}/adopt",
        json={},
    )

    assert response.status_code == 201

    sku = response.json["item"]["internal_sku"]

    assert sku
    assert sku != item.master_code


def test_catalogue_adoption_returns_existing_product_on_duplicate(
    client,
):
    item = _master_item(
        code="HMI-API-ADOPT-003",
        name="Duplicate Adoption Product",
    )

    product = _product(
        tenant_id="tenant-1",
        master_item_id=item.id,
        sku="EXISTING-001",
        name="Existing Product",
    )

    db.session.commit()

    response = client.post(
        f"/api/catalogue/items/{item.id}/adopt",
        json={
            "internal_sku": "NEW-SKU",
        },
    )

    assert response.status_code == 409
    assert response.json["ok"] is False
    assert (
        response.json["code"]
        == "master_item_already_adopted"
    )

    assert response.json["product"] == {
        "id": product.id,
        "master_item_id": item.id,
        "internal_sku": "EXISTING-001",
        "name": "Existing Product",
        "is_active": True,
    }


def test_catalogue_adoption_rejects_duplicate_explicit_sku(
    client,
):
    existing_master = _master_item(
        code="HMI-SKU-EXISTING",
        name="Existing SKU Master",
    )

    new_master = _master_item(
        code="HMI-SKU-NEW",
        name="New SKU Master",
    )

    _product(
        tenant_id="tenant-1",
        master_item_id=existing_master.id,
        sku="DUP-SKU-001",
        name="Existing SKU Product",
    )

    db.session.commit()

    response = client.post(
        f"/api/catalogue/items/{new_master.id}/adopt",
        json={
            "internal_sku": "DUP-SKU-001",
        },
    )

    assert response.status_code == 409
    assert response.json == {
        "ok": False,
        "error": (
            "A product with that internal_sku "
            "already exists."
        ),
    }


def test_catalogue_adoption_returns_404_for_draft_item(
    client,
):
    item = _master_item(
        code="HMI-DRAFT-ADOPT",
        name="Draft Adoption Product",
        review_status="draft",
    )

    db.session.commit()

    response = client.post(
        f"/api/catalogue/items/{item.id}/adopt",
        json={
            "internal_sku": "DRAFT-001",
        },
    )

    assert response.status_code == 404
    assert response.json == {
        "ok": False,
        "error": (
            "Catalogue item is not available "
            "for adoption."
        ),
    }


def test_catalogue_adoption_creates_explicit_base_unit(
    client,
):
    item = _master_item(
        code="HMI-UNIT-ADOPT",
        name="Unit Adoption Product",
    )

    db.session.commit()

    response = client.post(
        f"/api/catalogue/items/{item.id}/adopt",
        json={
            "internal_sku": "UNIT-API-001",
            "unit_code": "TAB",
            "unit_name": "Tablet",
        },
    )

    assert response.status_code == 201

    product_id = response.json["item"]["id"]

    product = db.session.get(
        Product,
        product_id,
    )

    assert product.unit_id is not None

    unit = db.session.get(
        UnitOfMeasure,
        product.unit_id,
    )

    assert unit.code == "TAB"
    assert unit.name == "Tablet"

    product_unit = (
        db.session.query(ProductUnit)
        .filter(
            ProductUnit.product_id == product.id,
            ProductUnit.is_base.is_(True),
        )
        .one()
    )

    assert product_unit.unit_id == unit.id


def test_catalogue_adoption_rejects_non_object_payload(
    client,
):
    item = _master_item(
        code="HMI-BAD-PAYLOAD",
        name="Bad Payload Product",
    )

    db.session.commit()

    response = client.post(
        f"/api/catalogue/items/{item.id}/adopt",
        json=["not", "an", "object"],
    )

    assert response.status_code == 400
    assert response.json == {
        "ok": False,
        "error": (
            "A catalogue adoption object is required."
        ),
    }


def test_catalogue_adoption_requires_products_create_permission(
    app_context,
    monkeypatch: pytest.MonkeyPatch,
):
    identity = SimpleNamespace(
        user_id="user-1",
        tenant_id="tenant-1",
        branch_id="branch-1",
        session_id="session-1",
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

    response = app_context.test_client().post(
        "/api/catalogue/items/"
        "00000000-0000-0000-0000-000000000000"
        "/adopt",
        json={},
    )

    assert response.status_code == 403
    assert (
        response.json["error"]["code"]
        == "AUTHORIZATION_DENIED"
    )
