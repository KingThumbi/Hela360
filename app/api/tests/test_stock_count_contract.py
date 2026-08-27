from __future__ import annotations

from datetime import datetime, timezone
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
    InventoryMovement,
    Product,
    StockBalance,
    StockCount,
    StockCountItem,
    Tenant,
    User,
    Warehouse,
)


TENANT_ID = "tenant-a"
OTHER_TENANT_ID = "tenant-b"
BRANCH_ID = "branch-a"
OTHER_BRANCH_ID = "branch-b"
USER_ID = "user-a"
WAREHOUSE_ID = "warehouse-a"
OTHER_BRANCH_WAREHOUSE_ID = "warehouse-b"
OTHER_TENANT_WAREHOUSE_ID = "warehouse-c"
BATCH_PRODUCT_ID = "product-batch"
NON_BATCH_PRODUCT_ID = "product-loose"
ZERO_PRODUCT_ID = "product-zero"
BATCH_ID = "batch-current"
EXPIRED_BATCH_ID = "batch-expired"
ZERO_BATCH_ID = "batch-zero"


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
        Product.__table__.create(db.engine)
        Warehouse.__table__.create(db.engine)
        InventoryBatch.__table__.create(db.engine)
        StockBalance.__table__.create(db.engine)
        InventoryMovement.__table__.create(db.engine)
        StockCount.__table__.create(db.engine)
        StockCountItem.__table__.create(db.engine)
        seed_data()

        yield app

        db.session.remove()
        StockCountItem.__table__.drop(db.engine)
        StockCount.__table__.drop(db.engine)
        InventoryMovement.__table__.drop(db.engine)
        StockBalance.__table__.drop(db.engine)
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
        "app.api.inventory._current_identity",
        lambda: identity,
    )
    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.authorization_service.authorize",
        lambda *args, **kwargs: None,
    )

    return app_context.test_client()


def seed_data():
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
                first_name="Counter",
                last_name="User",
                email="counter@example.test",
                username="counter",
                password_hash="hash",
            ),
            Product(
                id=BATCH_PRODUCT_ID,
                tenant_id=TENANT_ID,
                internal_sku="AMOX-500",
                name="Amoxicillin 500mg",
                track_inventory=True,
                track_batches=True,
                track_expiry=True,
                is_active=True,
            ),
            Product(
                id=NON_BATCH_PRODUCT_ID,
                tenant_id=TENANT_ID,
                internal_sku="ORS-001",
                name="ORS Sachet",
                track_inventory=True,
                track_batches=False,
                track_expiry=False,
                is_active=True,
            ),
            Product(
                id=ZERO_PRODUCT_ID,
                tenant_id=TENANT_ID,
                internal_sku="MASK-001",
                name="Face Mask",
                track_inventory=True,
                track_batches=False,
                track_expiry=False,
                is_active=True,
            ),
            Product(
                id="service-product",
                tenant_id=TENANT_ID,
                internal_sku="SVC-001",
                name="Service Fee",
                track_inventory=False,
                is_active=True,
            ),
            Product(
                id="other-tenant-product",
                tenant_id=OTHER_TENANT_ID,
                internal_sku="OTHER",
                name="Other Product",
            ),
            Warehouse(
                id=WAREHOUSE_ID,
                tenant_id=TENANT_ID,
                branch_id=BRANCH_ID,
                code="MAIN",
                name="Main Warehouse",
                is_active=True,
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
                code="OTHER",
                name="Other Tenant Warehouse",
            ),
            StockBalance(
                id="stock-batch",
                tenant_id=TENANT_ID,
                branch_id=BRANCH_ID,
                warehouse_id=WAREHOUSE_ID,
                product_id=BATCH_PRODUCT_ID,
                quantity_on_hand=Decimal("12.0000"),
                quantity_reserved=Decimal("2.0000"),
                quantity_available=Decimal("10.0000"),
            ),
            StockBalance(
                id="stock-loose",
                tenant_id=TENANT_ID,
                branch_id=BRANCH_ID,
                warehouse_id=WAREHOUSE_ID,
                product_id=NON_BATCH_PRODUCT_ID,
                quantity_on_hand=Decimal("5.0000"),
                quantity_reserved=Decimal("1.0000"),
                quantity_available=Decimal("4.0000"),
            ),
            StockBalance(
                id="stock-other-branch",
                tenant_id=TENANT_ID,
                branch_id=OTHER_BRANCH_ID,
                warehouse_id=OTHER_BRANCH_WAREHOUSE_ID,
                product_id=NON_BATCH_PRODUCT_ID,
                quantity_on_hand=Decimal("99.0000"),
                quantity_reserved=Decimal("0.0000"),
                quantity_available=Decimal("99.0000"),
            ),
            InventoryBatch(
                id=BATCH_ID,
                tenant_id=TENANT_ID,
                warehouse_id=WAREHOUSE_ID,
                product_id=BATCH_PRODUCT_ID,
                batch_number="BATCH-A",
                expiry_date=datetime(2027, 1, 31).date(),
                quantity_on_hand=Decimal("10.0000"),
                quantity_reserved=Decimal("2.0000"),
            ),
            InventoryBatch(
                id=EXPIRED_BATCH_ID,
                tenant_id=TENANT_ID,
                warehouse_id=WAREHOUSE_ID,
                product_id=BATCH_PRODUCT_ID,
                batch_number="BATCH-OLD",
                expiry_date=datetime(2026, 1, 31).date(),
                quantity_on_hand=Decimal("2.0000"),
                quantity_reserved=Decimal("0.0000"),
            ),
            InventoryBatch(
                id=ZERO_BATCH_ID,
                tenant_id=TENANT_ID,
                warehouse_id=WAREHOUSE_ID,
                product_id=BATCH_PRODUCT_ID,
                batch_number="BATCH-ZERO",
                expiry_date=datetime(2028, 1, 31).date(),
                quantity_on_hand=Decimal("0.0000"),
                quantity_reserved=Decimal("0.0000"),
            ),
        ]
    )
    db.session.commit()


def stock_count_payload(**overrides):
    payload = {
        "warehouse_id": WAREHOUSE_ID,
        "idempotency_key": "stock-count-key-1",
        "notes": "Monthly physical count.",
    }
    payload.update(overrides)
    return payload


def error_message(response) -> str:
    error = response.get_json()["error"]
    if isinstance(error, dict):
        return error["message"]
    return error


def test_stock_count_requires_inventory_count_permission(
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

    response = app_context.test_client().post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(),
    )

    assert response.status_code == 403
    assert captured["kwargs"]["permission"] == "inventory.count"


def test_stock_count_create_snapshots_physical_on_hand_and_batches(client):
    response = client.post("/api/inventory/stock-counts", json=stock_count_payload())

    assert response.status_code == 201
    item = response.get_json()["item"]
    assert item["count_number"].startswith("SC-")
    assert item["status"] == "open"
    assert item["warehouse"] == {
        "id": WAREHOUSE_ID,
        "code": "MAIN",
        "name": "Main Warehouse",
    }
    assert item["summary"]["total_items"] == 3

    lines = {
        (line["product"]["id"], line["batch"]["id"] if line["batch"] else None): line
        for line in item["items"]
    }
    assert lines[(BATCH_PRODUCT_ID, BATCH_ID)]["snapshot_quantity"] == "10.0000"
    assert lines[(BATCH_PRODUCT_ID, EXPIRED_BATCH_ID)]["snapshot_quantity"] == "2.0000"
    assert lines[(BATCH_PRODUCT_ID, EXPIRED_BATCH_ID)]["batch"]["is_expired"] is True
    assert lines[(NON_BATCH_PRODUCT_ID, None)]["snapshot_quantity"] == "5.0000"
    assert (BATCH_PRODUCT_ID, ZERO_BATCH_ID) not in lines
    assert StockBalance.query.filter_by(id="stock-batch").one().quantity_on_hand == Decimal("12.0000")
    assert InventoryMovement.query.count() == 0


def test_stock_count_rejects_cross_scope_inputs(client):
    response = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(warehouse_id=OTHER_BRANCH_WAREHOUSE_ID),
    )
    assert response.status_code == 400
    assert "warehouse_id" in error_message(response)

    response = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            idempotency_key="cross-product",
            product_ids=["other-tenant-product"],
        ),
    )
    assert response.status_code == 400
    assert "products" in error_message(response)

    response = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            idempotency_key="service-product",
            product_ids=["service-product"],
        ),
    )
    assert response.status_code == 400
    assert "inventory-tracked" in error_message(response)


def test_stock_count_partial_scope_can_snapshot_zero_system_non_batch_product(client):
    response = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            product_ids=[ZERO_PRODUCT_ID],
        ),
    )

    assert response.status_code == 201
    item = response.get_json()["item"]
    assert item["scope_type"] == "selected"
    assert item["summary"]["total_items"] == 1
    assert item["items"][0]["product"]["id"] == ZERO_PRODUCT_ID
    assert item["items"][0]["snapshot_quantity"] == "0.0000"


def test_stock_count_idempotency_and_open_warehouse_conflict(client):
    first = client.post("/api/inventory/stock-counts", json=stock_count_payload())
    replay = client.post("/api/inventory/stock-counts", json=stock_count_payload())

    assert first.status_code == 201
    assert replay.status_code == 201
    assert first.get_json()["item"]["id"] == replay.get_json()["item"]["id"]
    assert StockCount.query.count() == 1

    response = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(idempotency_key="second-open-count"),
    )
    assert response.status_code == 409
    assert "open stock count" in error_message(response)


def test_stock_count_entry_derives_expected_variance_after_movements(client):
    created = client.post("/api/inventory/stock-counts", json=stock_count_payload())
    count_id = created.get_json()["item"]["id"]
    item = next(
        line
        for line in created.get_json()["item"]["items"]
        if line["product"]["id"] == NON_BATCH_PRODUCT_ID
    )

    count = db.session.get(StockCount, count_id)
    db.session.add(
        InventoryMovement(
            id="movement-sale-after-snapshot",
            tenant_id=TENANT_ID,
            branch_id=BRANCH_ID,
            warehouse_id=WAREHOUSE_ID,
            product_id=NON_BATCH_PRODUCT_ID,
            movement_type="sale",
            quantity=Decimal("-2.0000"),
            reference_type="sale",
            reference_id="sale-a",
            created_by=USER_ID,
            created_at=count.snapshot_at,
            updated_at=count.snapshot_at,
        )
    )
    db.session.flush()
    movement = db.session.get(InventoryMovement, "movement-sale-after-snapshot")
    movement.created_at = datetime.now(timezone.utc)
    movement.updated_at = movement.created_at
    db.session.commit()

    response = client.put(
        f"/api/inventory/stock-counts/{count_id}/items/{item['id']}",
        json={
            "counted_quantity": "3.0000",
            "system_quantity": "999",
            "variance_quantity": "999",
            "notes": "Shelf counted.",
        },
    )

    assert response.status_code == 200
    updated = next(
        line
        for line in response.get_json()["item"]["items"]
        if line["id"] == item["id"]
    )
    assert updated["snapshot_quantity"] == "5.0000"
    assert updated["expected_quantity"] == "3.0000"
    assert updated["counted_quantity"] == "3.0000"
    assert updated["variance_quantity"] == "0.0000"
    assert updated["counted_by"]["id"] == USER_ID
    assert updated["counted_at"] is not None


def test_stock_count_rejects_negative_count_and_accepts_zero(client):
    created = client.post("/api/inventory/stock-counts", json=stock_count_payload())
    count_id = created.get_json()["item"]["id"]
    item_id = created.get_json()["item"]["items"][0]["id"]

    response = client.put(
        f"/api/inventory/stock-counts/{count_id}/items/{item_id}",
        json={"counted_quantity": "-1"},
    )
    assert response.status_code == 400
    assert "counted_quantity" in error_message(response)

    response = client.put(
        f"/api/inventory/stock-counts/{count_id}/items/{item_id}",
        json={"counted_quantity": "0"},
    )
    assert response.status_code == 200
    assert response.get_json()["item"]["items"][0]["counted_quantity"] == "0.0000"


def test_stock_count_complete_requires_all_items_and_does_not_mutate_stock(client):
    created = client.post("/api/inventory/stock-counts", json=stock_count_payload())
    count_id = created.get_json()["item"]["id"]

    response = client.post(f"/api/inventory/stock-counts/{count_id}/complete")
    assert response.status_code == 400
    assert "All stock count items" in error_message(response)

    for item in created.get_json()["item"]["items"]:
        response = client.put(
            f"/api/inventory/stock-counts/{count_id}/items/{item['id']}",
            json={"counted_quantity": item["expected_quantity"]},
        )
        assert response.status_code == 200

    before_stock = StockBalance.query.filter_by(id="stock-batch").one().quantity_on_hand
    before_batch = InventoryBatch.query.filter_by(id=BATCH_ID).one().quantity_on_hand
    before_movements = InventoryMovement.query.count()

    response = client.post(f"/api/inventory/stock-counts/{count_id}/complete")

    assert response.status_code == 200
    item = response.get_json()["item"]
    assert item["status"] == "completed"
    assert item["completed_by"]["id"] == USER_ID
    assert StockBalance.query.filter_by(id="stock-batch").one().quantity_on_hand == before_stock
    assert InventoryBatch.query.filter_by(id=BATCH_ID).one().quantity_on_hand == before_batch
    assert InventoryMovement.query.count() == before_movements

    response = client.post(f"/api/inventory/stock-counts/{count_id}/complete")
    assert response.status_code == 409
    response = client.put(
        f"/api/inventory/stock-counts/{count_id}/items/{created.get_json()['item']['items'][0]['id']}",
        json={"counted_quantity": "1"},
    )
    assert response.status_code == 409


def test_stock_count_cancel_unblocks_new_warehouse_count(client):
    created = client.post("/api/inventory/stock-counts", json=stock_count_payload())
    count_id = created.get_json()["item"]["id"]

    response = client.post(f"/api/inventory/stock-counts/{count_id}/cancel")
    assert response.status_code == 200
    assert response.get_json()["item"]["status"] == "cancelled"

    response = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(idempotency_key="after-cancel"),
    )
    assert response.status_code == 201


def test_stock_count_list_and_detail_are_branch_scoped(client):
    current = client.post("/api/inventory/stock-counts", json=stock_count_payload())
    count_id = current.get_json()["item"]["id"]
    db.session.add(
        StockCount(
            id="other-branch-count",
            tenant_id=TENANT_ID,
            branch_id=OTHER_BRANCH_ID,
            warehouse_id=OTHER_BRANCH_WAREHOUSE_ID,
            count_number="SC-OTHER",
            idempotency_key="other-branch-key",
            request_fingerprint="other",
            scope_type="full",
            status="open",
            snapshot_at=datetime.now(timezone.utc),
            started_at=datetime.now(timezone.utc),
            started_by=USER_ID,
        )
    )
    db.session.commit()

    response = client.get("/api/inventory/stock-counts")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["pagination"]["total"] == 1
    assert payload["items"][0]["id"] == count_id

    response = client.get(f"/api/inventory/stock-counts/{count_id}")
    assert response.status_code == 200
    assert response.get_json()["item"]["id"] == count_id


def test_stock_count_list_validates_filters(client):
    response = client.get("/api/inventory/stock-counts?page=0")
    assert response.status_code == 400
    assert "page" in error_message(response)

    response = client.get("/api/inventory/stock-counts?status=posted")
    assert response.status_code == 400
    assert "status" in error_message(response)

    response = client.get(
        f"/api/inventory/stock-counts?warehouse_id={OTHER_BRANCH_WAREHOUSE_ID}"
    )
    assert response.status_code == 400
    assert "warehouse_id" in error_message(response)
