from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from flask import Flask

from app.api.errors import register_error_handlers
from app.api.inventory import bp as inventory_bp
from app.extensions import db
from app.models import (
    Branch,
    InventoryBatch,
    Permission,
    Product,
    Role,
    RolePermission,
    StockBalance,
    Tenant,
    User,
    UserRole,
    UserSession,
    RefreshToken,
    PasswordResetToken,
    Warehouse,
)


TENANT_ID = "tenant-a"
OTHER_TENANT_ID = "tenant-b"
BRANCH_ID = "branch-a"
OTHER_BRANCH_ID = "branch-b"
USER_ID = "user-a"
WAREHOUSE_ID = "warehouse-a"
SECOND_WAREHOUSE_ID = "warehouse-b"
OTHER_BRANCH_WAREHOUSE_ID = "warehouse-c"
OTHER_TENANT_WAREHOUSE_ID = "warehouse-d"
PRODUCT_ID = "product-a"
RX_PRODUCT_ID = "product-b"
OUT_PRODUCT_ID = "product-c"
STOCK_ID = "stock-a"
RX_STOCK_ID = "stock-b"
OUT_STOCK_ID = "stock-c"
SECOND_WAREHOUSE_STOCK_ID = "stock-d"
OTHER_BRANCH_STOCK_ID = "stock-e"
OTHER_TENANT_STOCK_ID = "stock-f"


@pytest.fixture()
def app_context():
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TESTING=True,
    )
    db.init_app(app)
    app.register_blueprint(inventory_bp, url_prefix="/api")
    register_error_handlers(app)

    with app.app_context():
        Tenant.__table__.create(db.engine)
        Branch.__table__.create(db.engine)
        User.__table__.create(db.engine)
        Role.__table__.create(db.engine)
        Permission.__table__.create(db.engine)
        RolePermission.__table__.create(db.engine)
        UserRole.__table__.create(db.engine)
        UserSession.__table__.create(db.engine)
        RefreshToken.__table__.create(db.engine)
        PasswordResetToken.__table__.create(db.engine)
        Product.__table__.create(db.engine)
        Warehouse.__table__.create(db.engine)
        StockBalance.__table__.create(db.engine)
        InventoryBatch.__table__.create(db.engine)

        seed_data()

        yield app

        db.session.remove()
        InventoryBatch.__table__.drop(db.engine)
        StockBalance.__table__.drop(db.engine)
        Warehouse.__table__.drop(db.engine)
        Product.__table__.drop(db.engine)
        PasswordResetToken.__table__.drop(db.engine)
        RefreshToken.__table__.drop(db.engine)
        UserSession.__table__.drop(db.engine)
        UserRole.__table__.drop(db.engine)
        RolePermission.__table__.drop(db.engine)
        Permission.__table__.drop(db.engine)
        Role.__table__.drop(db.engine)
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
        "app.api.inventory._current_identity",
        lambda: identity,
    )
    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.authorization_service.authorize",
        lambda *args, **kwargs: None,
    )

    return app_context.test_client()


def seed_data():
    now = datetime(2026, 8, 9, 10, 0, tzinfo=timezone.utc)
    today = date.today()

    db.session.add_all(
        [
            Tenant(id=TENANT_ID, legal_name="Tenant A", display_name="Tenant A"),
            Tenant(id=OTHER_TENANT_ID, legal_name="Tenant B", display_name="Tenant B"),
            Branch(id=BRANCH_ID, tenant_id=TENANT_ID, code="BR-A", name="Branch A"),
            Branch(id=OTHER_BRANCH_ID, tenant_id=TENANT_ID, code="BR-B", name="Branch B"),
            User(
                id=USER_ID,
                tenant_id=TENANT_ID,
                branch_id=BRANCH_ID,
                first_name="Inventory",
                email="inventory@example.test",
                username="inventory",
                password_hash="hash",
            ),
            Product(
                id=PRODUCT_ID,
                tenant_id=TENANT_ID,
                internal_sku="ASP-100",
                supplier_sku="SUP-ASP",
                name="Aspirin 100mg",
                generic_name="Acetylsalicylic Acid",
                track_inventory=True,
                track_batches=True,
                track_expiry=False,
                reorder_level=Decimal("5.0000"),
                reorder_qty=Decimal("20.0000"),
            ),
            Product(
                id=RX_PRODUCT_ID,
                tenant_id=TENANT_ID,
                internal_sku="AMOX-500",
                name="Amoxicillin 500mg",
                generic_name="Amoxicillin",
                track_inventory=True,
                track_batches=True,
                track_expiry=True,
                requires_prescription=True,
                reorder_level=Decimal("5.0000"),
                reorder_qty=Decimal("10.0000"),
            ),
            Product(
                id=OUT_PRODUCT_ID,
                tenant_id=TENANT_ID,
                internal_sku="ORS-001",
                name="ORS Sachet",
                track_inventory=True,
                track_batches=False,
                track_expiry=False,
                reorder_level=Decimal("0.0000"),
                reorder_qty=Decimal("0.0000"),
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
                id=OTHER_TENANT_WAREHOUSE_ID,
                tenant_id=OTHER_TENANT_ID,
                branch_id=OTHER_BRANCH_ID,
                code="OTHER-TEN",
                name="Other Tenant Warehouse",
            ),
            StockBalance(
                id=STOCK_ID,
                tenant_id=TENANT_ID,
                branch_id=BRANCH_ID,
                warehouse_id=WAREHOUSE_ID,
                product_id=PRODUCT_ID,
                quantity_on_hand=Decimal("10.0000"),
                quantity_reserved=Decimal("2.0000"),
                quantity_available=Decimal("8.0000"),
                avg_unit_cost=Decimal("1.25"),
                created_at=now,
                updated_at=now,
            ),
            StockBalance(
                id=RX_STOCK_ID,
                tenant_id=TENANT_ID,
                branch_id=BRANCH_ID,
                warehouse_id=WAREHOUSE_ID,
                product_id=RX_PRODUCT_ID,
                quantity_on_hand=Decimal("4.0000"),
                quantity_reserved=Decimal("0.0000"),
                quantity_available=Decimal("4.0000"),
                avg_unit_cost=Decimal("2.50"),
                created_at=now,
                updated_at=now,
            ),
            StockBalance(
                id=OUT_STOCK_ID,
                tenant_id=TENANT_ID,
                branch_id=BRANCH_ID,
                warehouse_id=SECOND_WAREHOUSE_ID,
                product_id=OUT_PRODUCT_ID,
                quantity_on_hand=Decimal("0.0000"),
                quantity_reserved=Decimal("0.0000"),
                quantity_available=Decimal("0.0000"),
                avg_unit_cost=Decimal("0.50"),
                created_at=now,
                updated_at=now,
            ),
            StockBalance(
                id=SECOND_WAREHOUSE_STOCK_ID,
                tenant_id=TENANT_ID,
                branch_id=BRANCH_ID,
                warehouse_id=SECOND_WAREHOUSE_ID,
                product_id=PRODUCT_ID,
                quantity_on_hand=Decimal("3.0000"),
                quantity_reserved=Decimal("0.0000"),
                quantity_available=Decimal("3.0000"),
                avg_unit_cost=Decimal("1.25"),
                created_at=now,
                updated_at=now,
            ),
            StockBalance(
                id=OTHER_BRANCH_STOCK_ID,
                tenant_id=TENANT_ID,
                branch_id=OTHER_BRANCH_ID,
                warehouse_id=OTHER_BRANCH_WAREHOUSE_ID,
                product_id=PRODUCT_ID,
                quantity_on_hand=Decimal("99.0000"),
                quantity_reserved=Decimal("0.0000"),
                quantity_available=Decimal("99.0000"),
                avg_unit_cost=Decimal("1.25"),
                created_at=now,
                updated_at=now,
            ),
            StockBalance(
                id=OTHER_TENANT_STOCK_ID,
                tenant_id=OTHER_TENANT_ID,
                branch_id=OTHER_BRANCH_ID,
                warehouse_id=OTHER_TENANT_WAREHOUSE_ID,
                product_id="other-tenant-product",
                quantity_on_hand=Decimal("88.0000"),
                quantity_reserved=Decimal("0.0000"),
                quantity_available=Decimal("88.0000"),
                avg_unit_cost=Decimal("1.25"),
                created_at=now,
                updated_at=now,
            ),
            InventoryBatch(
                id="batch-valid",
                tenant_id=TENANT_ID,
                warehouse_id=WAREHOUSE_ID,
                product_id=RX_PRODUCT_ID,
                batch_number="RX-VALID",
                expiry_date=today + timedelta(days=20),
                quantity_on_hand=Decimal("2.0000"),
                quantity_reserved=Decimal("0.0000"),
                status="available",
                received_at=now,
                created_at=now,
                updated_at=now,
            ),
            InventoryBatch(
                id="batch-expired",
                tenant_id=TENANT_ID,
                warehouse_id=WAREHOUSE_ID,
                product_id=RX_PRODUCT_ID,
                batch_number="RX-OLD",
                expiry_date=today - timedelta(days=1),
                quantity_on_hand=Decimal("3.0000"),
                quantity_reserved=Decimal("0.0000"),
                status="available",
                received_at=now,
                created_at=now,
                updated_at=now,
            ),
            InventoryBatch(
                id="batch-null-expiry",
                tenant_id=TENANT_ID,
                warehouse_id=WAREHOUSE_ID,
                product_id=RX_PRODUCT_ID,
                batch_number="RX-NOEXP",
                expiry_date=None,
                quantity_on_hand=Decimal("1.0000"),
                quantity_reserved=Decimal("0.0000"),
                status="available",
                received_at=now,
                created_at=now,
                updated_at=now,
            ),
            InventoryBatch(
                id="batch-zero",
                tenant_id=TENANT_ID,
                warehouse_id=WAREHOUSE_ID,
                product_id=RX_PRODUCT_ID,
                batch_number="RX-ZERO",
                expiry_date=today + timedelta(days=90),
                quantity_on_hand=Decimal("0.0000"),
                quantity_reserved=Decimal("0.0000"),
                status="available",
                received_at=now,
                created_at=now,
                updated_at=now,
            ),
            InventoryBatch(
                id="batch-other-warehouse",
                tenant_id=TENANT_ID,
                warehouse_id=SECOND_WAREHOUSE_ID,
                product_id=RX_PRODUCT_ID,
                batch_number="RX-OTHER-WH",
                expiry_date=today + timedelta(days=30),
                quantity_on_hand=Decimal("7.0000"),
                quantity_reserved=Decimal("0.0000"),
                status="available",
                received_at=now,
                created_at=now,
                updated_at=now,
            ),
        ]
    )
    db.session.commit()


def test_inventory_list_requires_authentication(app_context):
    response = app_context.test_client().get("/api/inventory")

    assert response.status_code == 401


def test_inventory_list_requires_inventory_read_permission(
    app_context,
    identity: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
):
    captured = {}

    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.get_current_identity",
        lambda: identity,
    )
    monkeypatch.setattr(
        "app.auth.jwt.get_current_identity",
        lambda: identity,
    )
    monkeypatch.setattr(
        "app.api.inventory._current_identity",
        lambda: identity,
    )

    def deny(*args, **kwargs):
        captured["permission"] = kwargs.get("permission")
        from app.auth.exceptions import PermissionDeniedError

        raise PermissionDeniedError("Permission denied.")

    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.authorization_service.authorize",
        deny,
    )

    response = app_context.test_client().get("/api/inventory")

    assert response.status_code == 403
    assert captured["permission"] == "inventory.read"


def test_inventory_list_requires_branch(client, identity: SimpleNamespace):
    identity.branch_id = None

    response = client.get("/api/inventory")

    assert response.status_code == 400
    assert response.json["error"] == "Authenticated user is not assigned to a branch."


def test_inventory_list_is_current_tenant_and_branch_only(client):
    response = client.get("/api/inventory")

    assert response.status_code == 200
    assert response.json["pagination"]["total"] == 4
    assert {item["id"] for item in response.json["items"]} == {
        STOCK_ID,
        RX_STOCK_ID,
        OUT_STOCK_ID,
        SECOND_WAREHOUSE_STOCK_ID,
    }


def test_inventory_list_keeps_same_product_separate_by_warehouse(client):
    response = client.get("/api/inventory", query_string={"search": "Aspirin"})

    assert response.status_code == 200
    assert response.json["pagination"]["total"] == 2
    assert {
        (item["product"]["id"], item["warehouse"]["id"])
        for item in response.json["items"]
    } == {
        (PRODUCT_ID, WAREHOUSE_ID),
        (PRODUCT_ID, SECOND_WAREHOUSE_ID),
    }


def test_inventory_list_validates_warehouse_filter(client):
    invalid = client.get(
        "/api/inventory",
        query_string={"warehouse_id": OTHER_BRANCH_WAREHOUSE_ID},
    )
    valid = client.get(
        "/api/inventory",
        query_string={"warehouse_id": SECOND_WAREHOUSE_ID},
    )

    assert invalid.status_code == 400
    assert invalid.json["error"] == "warehouse_id is not valid for this branch."
    assert valid.status_code == 200
    assert {item["warehouse"]["id"] for item in valid.json["items"]} == {
        SECOND_WAREHOUSE_ID
    }


def test_inventory_list_supports_pagination_and_search(client):
    page = client.get("/api/inventory", query_string={"page": 2, "per_page": 2})
    search = client.get("/api/inventory", query_string={"search": "AMOX"})

    assert page.status_code == 200
    assert page.json["pagination"] == {
        "page": 2,
        "per_page": 2,
        "total": 4,
        "pages": 2,
        "has_prev": True,
        "has_next": False,
    }
    assert search.status_code == 200
    assert search.json["pagination"]["total"] == 1
    assert search.json["items"][0]["product"]["id"] == RX_PRODUCT_ID


def test_inventory_list_reports_quantities_and_stock_status(client):
    response = client.get("/api/inventory", query_string={"search": "AMOX"})

    assert response.status_code == 200
    item = response.json["items"][0]
    assert item["quantity_on_hand"] == "4.0000"
    assert item["quantity_reserved"] == "0.0000"
    assert item["quantity_available"] == "4.0000"
    assert item["sellable_quantity"] == "2.0000"
    assert item["expired_quantity"] == "3.0000"
    assert item["is_low_stock"] is True
    assert item["is_out_of_stock"] is False
    assert "avg_unit_cost" not in item


def test_inventory_list_filters_stock_status(client):
    low = client.get("/api/inventory", query_string={"stock_status": "low_stock"})
    out = client.get("/api/inventory", query_string={"stock_status": "out_of_stock"})
    expired = client.get(
        "/api/inventory",
        query_string={"stock_status": "expired_stock"},
    )

    assert low.status_code == 200
    assert {item["id"] for item in low.json["items"]} == {
        RX_STOCK_ID,
        SECOND_WAREHOUSE_STOCK_ID,
    }
    assert out.status_code == 200
    assert [item["id"] for item in out.json["items"]] == [OUT_STOCK_ID]
    assert expired.status_code == 200
    assert [item["id"] for item in expired.json["items"]] == [RX_STOCK_ID]


def test_inventory_list_reports_expiry_and_expires_before_filter(client):
    expected_earliest = (date.today() + timedelta(days=20)).isoformat()
    expires_before = (date.today() + timedelta(days=25)).isoformat()
    response = client.get(
        "/api/inventory",
        query_string={"expires_before": expires_before},
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json["items"]] == [RX_STOCK_ID]
    item = response.json["items"][0]
    assert item["has_expired_stock"] is True
    assert item["has_expiring_stock"] is True
    assert item["expired_batch_count"] == 1
    assert item["expiring_batch_count"] == 1
    assert item["earliest_sellable_expiry_date"] == expected_earliest


def test_inventory_list_rejects_invalid_filters(client):
    page = client.get("/api/inventory", query_string={"page": "0"})
    status = client.get("/api/inventory", query_string={"stock_status": "stale"})
    expiry = client.get("/api/inventory", query_string={"expires_before": "09-08-2026"})

    assert page.status_code == 400
    assert page.json["error"] == "page must be a positive integer."
    assert status.status_code == 400
    assert status.json["error"] == "stock_status is not supported."
    assert expiry.status_code == 400
    assert expiry.json["error"] == (
        "expires_before must be a valid date in YYYY-MM-DD format."
    )


def test_inventory_list_empty_result(client):
    response = client.get("/api/inventory", query_string={"search": "missing"})

    assert response.status_code == 200
    assert response.json["items"] == []
    assert response.json["pagination"]["total"] == 0


def test_inventory_batches_are_scoped_to_stock_balance_product_and_warehouse(client):
    response = client.get(f"/api/inventory/stock/{RX_STOCK_ID}/batches")

    assert response.status_code == 200
    assert response.json["stock"]["id"] == RX_STOCK_ID
    assert [item["id"] for item in response.json["items"]] == [
        "batch-valid",
        "batch-null-expiry",
        "batch-expired",
    ]
    assert "batch-zero" not in [item["id"] for item in response.json["items"]]
    assert "batch-other-warehouse" not in [
        item["id"] for item in response.json["items"]
    ]
    expired = response.json["items"][2]
    assert expired["is_expired"] is True
    assert expired["is_sellable"] is False
    assert "unit_cost" not in expired


def test_inventory_batches_can_include_zero_quantity_when_requested(client):
    response = client.get(
        f"/api/inventory/stock/{RX_STOCK_ID}/batches",
        query_string={"include_zero": "true"},
    )

    assert response.status_code == 200
    assert "batch-zero" in [item["id"] for item in response.json["items"]]


def test_inventory_batches_reject_cross_branch_stock_balance(client):
    response = client.get(f"/api/inventory/stock/{OTHER_BRANCH_STOCK_ID}/batches")

    assert response.status_code == 404
    assert response.json["error"] == "Stock balance not found."
