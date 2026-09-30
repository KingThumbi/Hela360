from __future__ import annotations

from datetime import date, datetime, timezone
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

WAREHOUSE_ID = "warehouse-a"
SECOND_WAREHOUSE_ID = "warehouse-b"
OTHER_BRANCH_WAREHOUSE_ID = "warehouse-c"


@pytest.fixture()
def app_context():
    app = Flask(__name__)

    app.config.update(
        SQLALCHEMY_DATABASE_URI=(
            "sqlite:///:memory:"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TESTING=True,
    )

    db.init_app(app)

    app.register_blueprint(
        products_bp,
        url_prefix="/api",
    )

    register_error_handlers(app)

    with app.app_context():
        Tenant.__table__.create(db.engine)
        Branch.__table__.create(db.engine)
        User.__table__.create(db.engine)
        Product.__table__.create(db.engine)
        Warehouse.__table__.create(db.engine)
        InventoryBatch.__table__.create(
            db.engine
        )

        seed_data()

        yield app

        db.session.remove()

        InventoryBatch.__table__.drop(
            db.engine
        )
        Warehouse.__table__.drop(
            db.engine
        )
        Product.__table__.drop(
            db.engine
        )
        User.__table__.drop(
            db.engine
        )
        Branch.__table__.drop(
            db.engine
        )
        Tenant.__table__.drop(
            db.engine
        )


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
        "app.services.tenant.auth.decorators."
        "get_current_identity",
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
        "app.services.tenant.auth.decorators."
        "authorization_service.authorize",
        lambda *args, **kwargs: None,
    )

    return app_context.test_client()


def seed_data():
    received = datetime(
        2026,
        8,
        1,
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
                track_batches=True,
                track_expiry=True,
            ),
            Product(
                id="other-tenant-product",
                tenant_id=OTHER_TENANT_ID,
                internal_sku="OTHER",
                name="Other Product",
                track_batches=True,
                track_expiry=True,
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
                code="OTHER",
                name="Other Branch",
            ),
        ]
    )

    db.session.flush()

    db.session.add_all(
        [
            InventoryBatch(
                id="batch-main",
                tenant_id=TENANT_ID,
                product_id=PRODUCT_ID,
                warehouse_id=WAREHOUSE_ID,
                batch_number="BATCH-MAIN",
                manufacture_date=date(
                    2026,
                    1,
                    1,
                ),
                expiry_date=date(
                    2099,
                    1,
                    31,
                ),
                unit_cost=Decimal("125.00"),
                quantity_on_hand=Decimal(
                    "10.0000"
                ),
                quantity_reserved=Decimal(
                    "2.0000"
                ),
                status="available",
                received_at=received,
            ),
            InventoryBatch(
                id="batch-front",
                tenant_id=TENANT_ID,
                product_id=PRODUCT_ID,
                warehouse_id=(
                    SECOND_WAREHOUSE_ID
                ),
                batch_number="BATCH-FRONT",
                expiry_date=date(
                    2099,
                    6,
                    30,
                ),
                unit_cost=Decimal("130.00"),
                quantity_on_hand=Decimal(
                    "5.0000"
                ),
                quantity_reserved=Decimal(
                    "0.0000"
                ),
                status="available",
                received_at=received,
            ),
            InventoryBatch(
                id="batch-zero",
                tenant_id=TENANT_ID,
                product_id=PRODUCT_ID,
                warehouse_id=WAREHOUSE_ID,
                batch_number="BATCH-ZERO",
                expiry_date=date(
                    2099,
                    12,
                    31,
                ),
                unit_cost=Decimal("120.00"),
                quantity_on_hand=Decimal(
                    "0.0000"
                ),
                quantity_reserved=Decimal(
                    "0.0000"
                ),
                status="available",
                received_at=received,
            ),
            InventoryBatch(
                id="batch-other-branch",
                tenant_id=TENANT_ID,
                product_id=PRODUCT_ID,
                warehouse_id=(
                    OTHER_BRANCH_WAREHOUSE_ID
                ),
                batch_number="BATCH-OTHER",
                expiry_date=date(
                    2099,
                    1,
                    31,
                ),
                quantity_on_hand=Decimal(
                    "99.0000"
                ),
                quantity_reserved=Decimal(
                    "0.0000"
                ),
                status="available",
                received_at=received,
            ),
        ]
    )

    db.session.commit()


def test_product_batch_history_is_product_and_branch_scoped(
    client,
):
    response = client.get(
        f"/api/products/{PRODUCT_ID}/history/batches"
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["ok"] is True

    assert {
        item["id"]
        for item in payload["items"]
    } == {
        "batch-main",
        "batch-front",
    }

    main = next(
        item
        for item in payload["items"]
        if item["id"] == "batch-main"
    )

    assert main["warehouse"] == {
        "id": WAREHOUSE_ID,
        "code": "MAIN",
        "name": "Main Warehouse",
    }

    assert main["batch_number"] == (
        "BATCH-MAIN"
    )

    assert main["unit_cost"] == "125.00"

    assert main["quantity_on_hand"] == (
        "10.0000"
    )

    assert main["quantity_reserved"] == (
        "2.0000"
    )

    assert main["quantity_available"] == (
        "8.0000"
    )

    assert main["is_expired"] is False
    assert main["is_sellable"] is True


def test_product_batch_history_can_include_zero_quantity(
    client,
):
    response = client.get(
        (
            f"/api/products/{PRODUCT_ID}"
            "/history/batches"
            "?include_zero=true"
        )
    )

    assert response.status_code == 200

    ids = {
        item["id"]
        for item in response.get_json()[
            "items"
        ]
    }

    assert ids == {
        "batch-main",
        "batch-front",
        "batch-zero",
    }


def test_product_batch_history_supports_warehouse_filter(
    client,
):
    response = client.get(
        (
            f"/api/products/{PRODUCT_ID}"
            "/history/batches"
            f"?warehouse_id={WAREHOUSE_ID}"
            "&include_zero=true"
        )
    )

    assert response.status_code == 200

    ids = {
        item["id"]
        for item in response.get_json()[
            "items"
        ]
    }

    assert ids == {
        "batch-main",
        "batch-zero",
    }


def test_product_batch_history_is_paginated(
    client,
):
    response = client.get(
        (
            f"/api/products/{PRODUCT_ID}"
            "/history/batches"
            "?page=1&per_page=1"
        )
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert len(payload["items"]) == 1

    assert payload["pagination"] == {
        "page": 1,
        "per_page": 1,
        "total": 2,
        "pages": 2,
        "has_prev": False,
        "has_next": True,
    }


def test_product_batch_history_rejects_cross_tenant_product(
    client,
):
    response = client.get(
        (
            "/api/products/"
            "other-tenant-product/"
            "history/batches"
        )
    )

    assert response.status_code == 404

    assert response.get_json() == {
        "ok": False,
        "error": "Product not found.",
    }


def test_product_batch_history_requires_branch(
    client,
    identity: SimpleNamespace,
):
    identity.branch_id = None

    response = client.get(
        f"/api/products/{PRODUCT_ID}/history/batches"
    )

    assert response.status_code == 400

    assert "branch" in (
        response.get_json()["error"].lower()
    )


def test_product_batch_history_requires_inventory_read(
    app_context,
    identity: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
):
    captured = {}

    def deny(*args, **kwargs):
        captured["kwargs"] = kwargs

        from app.auth.exceptions import (
            PermissionDeniedError,
        )

        raise PermissionDeniedError(
            "denied"
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
        "app.services.tenant.auth.decorators."
        "authorization_service.authorize",
        deny,
    )

    client = app_context.test_client()

    response = client.get(
        f"/api/products/{PRODUCT_ID}/history/batches"
    )

    assert response.status_code == 403
