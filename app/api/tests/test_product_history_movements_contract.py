from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from flask import Flask

from app.api.errors import register_error_handlers
from app.api.products import bp as products_bp
from app.extensions import db
from app.models import (
    Branch,
    InventoryBatch,
    InventoryMovement,
    Product,
    Tenant,
    User,
    Warehouse,
)


TENANT_ID = "tenant-a"
OTHER_TENANT_ID = "tenant-b"

BRANCH_ID = "branch-a"
OTHER_BRANCH_ID = "branch-b"

USER_ID = "user-a"

PRODUCT_ID = "product-a"
SECOND_PRODUCT_ID = "product-b"

WAREHOUSE_ID = "warehouse-a"
SECOND_WAREHOUSE_ID = "warehouse-b"
OTHER_BRANCH_WAREHOUSE_ID = "warehouse-c"

BATCH_ID = "batch-a"


@pytest.fixture()
def app_context():
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TESTING=True,
    )

    db.init_app(app)
    app.register_blueprint(products_bp, url_prefix="/api")
    register_error_handlers(app)

    with app.app_context():
        Tenant.__table__.create(db.engine)
        Branch.__table__.create(db.engine)
        User.__table__.create(db.engine)
        Product.__table__.create(db.engine)
        Warehouse.__table__.create(db.engine)
        InventoryBatch.__table__.create(db.engine)
        InventoryMovement.__table__.create(db.engine)

        seed_data()

        yield app

        db.session.remove()

        InventoryMovement.__table__.drop(db.engine)
        InventoryBatch.__table__.drop(db.engine)
        Warehouse.__table__.drop(db.engine)
        Product.__table__.drop(db.engine)
        User.__table__.drop(db.engine)
        Branch.__table__.drop(db.engine)
        Tenant.__table__.drop(db.engine)


@pytest.fixture()
def identity():
    return SimpleNamespace(
        user_id=USER_ID,
        tenant_id=TENANT_ID,
        branch_id=BRANCH_ID,
    )


@pytest.fixture()
def client(
    app_context,
    identity: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.get_current_identity",
        lambda: identity,
    )
    monkeypatch.setattr(
        "app.auth.jwt.get_current_identity",
        lambda: identity,
    )
    monkeypatch.setattr(
        "app.api.products.get_current_identity",
        lambda: identity,
    )
    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.authorization_service.authorize",
        lambda *args, **kwargs: None,
    )

    return app_context.test_client()


def movement(
    movement_id: str,
    *,
    tenant_id: str = TENANT_ID,
    branch_id: str = BRANCH_ID,
    product_id: str,
    warehouse_id: str,
    batch_id: str | None = None,
    sale_item_id: str | None = None,
    created_by: str = USER_ID,
    movement_type: str = "sale",
    quantity: Decimal = Decimal("-1.0000"),
    reference_type: str = "sale",
    reference_id: str = "sale-1",
    created_at: datetime,
) -> InventoryMovement:
    return InventoryMovement(
        id=movement_id,
        tenant_id=tenant_id,
        branch_id=branch_id,
        warehouse_id=warehouse_id,
        product_id=product_id,
        batch_id=batch_id,
        sale_item_id=sale_item_id,
        movement_type=movement_type,
        quantity=quantity,
        unit_cost=Decimal("3.25"),
        unit_price=Decimal("5.50"),
        reference_type=reference_type,
        reference_id=reference_id,
        notes="internal note",
        created_by=created_by,
        created_at=created_at,
        updated_at=created_at,
    )


def seed_data():
    newer = datetime(
        2026,
        8,
        9,
        12,
        0,
        tzinfo=timezone.utc,
    )
    older = datetime(
        2026,
        8,
        8,
        10,
        0,
        tzinfo=timezone.utc,
    )

    db.session.add_all(
        [
            Tenant(
                id=TENANT_ID,
                legal_name="Tenant A",
                display_name="Tenant A",
            ),
            Tenant(
                id=OTHER_TENANT_ID,
                legal_name="Tenant B",
                display_name="Tenant B",
            ),
            Branch(
                id=BRANCH_ID,
                tenant_id=TENANT_ID,
                code="BR-A",
                name="Branch A",
            ),
            Branch(
                id=OTHER_BRANCH_ID,
                tenant_id=TENANT_ID,
                code="BR-B",
                name="Branch B",
            ),
            User(
                id=USER_ID,
                tenant_id=TENANT_ID,
                branch_id=BRANCH_ID,
                first_name="Inventory",
                last_name="Auditor",
                email="inventory@example.test",
                username="inventory",
                password_hash="hash",
            ),
            Product(
                id=PRODUCT_ID,
                tenant_id=TENANT_ID,
                internal_sku="ASP-100",
                name="Aspirin 100mg",
            ),
            Product(
                id=SECOND_PRODUCT_ID,
                tenant_id=TENANT_ID,
                internal_sku="ORS-001",
                name="ORS Sachet",
            ),
            Product(
                id="other-tenant-product",
                tenant_id=OTHER_TENANT_ID,
                internal_sku="OTHER",
                name="Other Tenant Product",
            ),
            Warehouse(
                id=WAREHOUSE_ID,
                tenant_id=TENANT_ID,
                branch_id=BRANCH_ID,
                code="MAIN",
                name="Main Warehouse",
            ),
            Warehouse(
                id=SECOND_WAREHOUSE_ID,
                tenant_id=TENANT_ID,
                branch_id=BRANCH_ID,
                code="FRONT",
                name="Front Store",
            ),
            Warehouse(
                id=OTHER_BRANCH_WAREHOUSE_ID,
                tenant_id=TENANT_ID,
                branch_id=OTHER_BRANCH_ID,
                code="OTHER-BR",
                name="Other Branch Warehouse",
            ),
            Warehouse(
                id="other-tenant-warehouse",
                tenant_id=OTHER_TENANT_ID,
                branch_id=OTHER_BRANCH_ID,
                code="OTHER",
                name="Other Tenant Warehouse",
            ),
            InventoryBatch(
                id=BATCH_ID,
                tenant_id=TENANT_ID,
                product_id=PRODUCT_ID,
                warehouse_id=WAREHOUSE_ID,
                batch_number="BATCH-1",
                expiry_date=date(2027, 1, 31),
                quantity_on_hand=Decimal("10.0000"),
                quantity_reserved=Decimal("0.0000"),
            ),
            movement(
                "movement-new",
                product_id=PRODUCT_ID,
                warehouse_id=WAREHOUSE_ID,
                batch_id=BATCH_ID,
                movement_type="sale_refund_return",
                quantity=Decimal("1.0000"),
                reference_type="sale_refund",
                reference_id="refund-1",
                created_at=newer,
            ),
            movement(
                "movement-old",
                product_id=PRODUCT_ID,
                warehouse_id=WAREHOUSE_ID,
                batch_id=BATCH_ID,
                movement_type="sale",
                quantity=Decimal("-2.0000"),
                reference_type="sale",
                reference_id="sale-1",
                created_at=older,
            ),
            movement(
                "movement-other-product",
                product_id=SECOND_PRODUCT_ID,
                warehouse_id=SECOND_WAREHOUSE_ID,
                movement_type="sale_void",
                quantity=Decimal("1.0000"),
                reference_type="sale_void",
                reference_id="sale-2",
                created_at=older + timedelta(hours=1),
            ),
            movement(
                "movement-other-branch",
                branch_id=OTHER_BRANCH_ID,
                product_id=PRODUCT_ID,
                warehouse_id=OTHER_BRANCH_WAREHOUSE_ID,
                movement_type="sale",
                quantity=Decimal("-1.0000"),
                reference_type="sale",
                reference_id="other-branch-sale",
                created_at=newer,
            ),
        ]
    )

    db.session.commit()


def test_product_movement_history_is_product_and_branch_scoped(
    client,
):
    response = client.get(
        f"/api/products/{PRODUCT_ID}/history/movements"
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["ok"] is True
    assert [item["id"] for item in payload["items"]] == [
        "movement-new",
        "movement-old",
    ]

    assert payload["items"][0]["quantity"] == "1.0000"
    assert payload["items"][0]["reference"] == {
        "type": "sale_refund",
        "id": "refund-1",
    }

    assert payload["items"][1]["quantity"] == "-2.0000"
    assert payload["items"][1]["reference"] == {
        "type": "sale",
        "id": "sale-1",
    }


def test_product_movement_history_path_product_cannot_be_overridden(
    client,
):
    response = client.get(
        (
            f"/api/products/{PRODUCT_ID}/history/movements"
            f"?product_id={SECOND_PRODUCT_ID}"
        )
    )

    assert response.status_code == 200

    ids = [
        item["id"]
        for item in response.get_json()["items"]
    ]

    assert ids == [
        "movement-new",
        "movement-old",
    ]
    assert "movement-other-product" not in ids


def test_product_movement_history_supports_filters(client):
    response = client.get(
        (
            f"/api/products/{PRODUCT_ID}/history/movements"
            "?movement_type=sale"
            "&reference_type=sale"
        )
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert [item["id"] for item in payload["items"]] == [
        "movement-old",
    ]


def test_product_movement_history_is_paginated(client):
    response = client.get(
        (
            f"/api/products/{PRODUCT_ID}/history/movements"
            "?page=1&per_page=1"
        )
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert [item["id"] for item in payload["items"]] == [
        "movement-new",
    ]

    assert payload["pagination"] == {
        "page": 1,
        "per_page": 1,
        "total": 2,
        "pages": 2,
        "has_prev": False,
        "has_next": True,
    }


def test_product_movement_history_rejects_cross_tenant_product(
    client,
):
    response = client.get(
        "/api/products/other-tenant-product/history/movements"
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "ok": False,
        "error": "product_id is not valid for this tenant.",
    }


def test_product_movement_history_requires_branch(
    client,
    identity: SimpleNamespace,
):
    identity.branch_id = None

    response = client.get(
        f"/api/products/{PRODUCT_ID}/history/movements"
    )

    assert response.status_code == 400
    assert "branch" in response.get_json()["error"]


def test_product_movement_history_requires_inventory_read(
    app_context,
    identity: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
):
    captured = {}

    def deny(*args, **kwargs):
        captured["kwargs"] = kwargs

        from app.auth.exceptions import PermissionDeniedError

        raise PermissionDeniedError("denied")

    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.get_current_identity",
        lambda: identity,
    )
    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.authorization_service.authorize",
        deny,
    )

    response = app_context.test_client().get(
        f"/api/products/{PRODUCT_ID}/history/movements"
    )

    assert response.status_code == 403
    assert captured["kwargs"]["permission"] == "inventory.read"


def test_product_movement_history_supports_batch_filter(
    client,
):
    response = client.get(
        (
            f"/api/products/{PRODUCT_ID}/history/movements"
            f"?batch_id={BATCH_ID}"
        )
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert [
        item["id"]
        for item in payload["items"]
    ] == [
        "movement-new",
        "movement-old",
    ]

    assert all(
        item["batch"]["id"] == BATCH_ID
        for item in payload["items"]
    )


def test_product_movement_history_unknown_batch_is_empty(
    client,
):
    response = client.get(
        (
            f"/api/products/{PRODUCT_ID}/history/movements"
            "?batch_id=does-not-exist"
        )
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["items"] == []
    assert payload["pagination"]["total"] == 0


def test_product_movement_history_exposes_persisted_prices(
    client,
):
    response = client.get(
        (
            f"/api/products/{PRODUCT_ID}/history/movements"
            f"?batch_id={BATCH_ID}"
        )
    )

    assert response.status_code == 200

    item = response.get_json()["items"][0]

    assert item["unit_cost"] == "3.25"
    assert item["unit_price"] == "5.50"
