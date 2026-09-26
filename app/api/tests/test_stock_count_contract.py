from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError
from flask import Flask

from app.api.errors import register_error_handlers
from app.api.inventory import bp as inventory_bp
from app.extensions import db
from app.models.audit import AuditLog
from app.models import (
    Branch,
    InventoryBatch,
    InventoryMovement,
    Product,
    ProductUnit,
    StockBalance,
    StockAdjustment,
    StockCount,
    StockCountItem,
    StockCountScopeProduct,
    Tenant,
    UnitOfMeasure,
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
EMPTY_BATCH_PRODUCT_ID = "product-empty-batch"
BATCH_ID = "batch-current"
EXPIRED_BATCH_ID = "batch-expired"
ZERO_BATCH_ID = "batch-zero"

UNIT_BOX_ID = "unit-box"
NON_BATCH_BOX_UNIT_ID = "product-unit-loose-box"
EMPTY_BATCH_BOX_UNIT_ID = "product-unit-empty-box"


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
        AuditLog.__table__.create(db.engine)
        UnitOfMeasure.__table__.create(db.engine)
        Product.__table__.create(db.engine)
        ProductUnit.__table__.create(db.engine)
        Warehouse.__table__.create(db.engine)
        InventoryBatch.__table__.create(db.engine)
        StockBalance.__table__.create(db.engine)
        InventoryMovement.__table__.create(db.engine)
        StockCount.__table__.create(db.engine)
        StockAdjustment.__table__.create(db.engine)
        StockCountScopeProduct.__table__.create(
            db.engine
        )
        StockCountItem.__table__.create(db.engine)
        seed_data()

        yield app

        db.session.remove()
        StockCountItem.__table__.drop(db.engine)
        StockCountScopeProduct.__table__.drop(
            db.engine
        )
        StockAdjustment.__table__.drop(db.engine)
        StockCount.__table__.drop(db.engine)
        InventoryMovement.__table__.drop(db.engine)
        StockBalance.__table__.drop(db.engine)
        InventoryBatch.__table__.drop(db.engine)
        Warehouse.__table__.drop(db.engine)
        ProductUnit.__table__.drop(db.engine)
        Product.__table__.drop(db.engine)
        UnitOfMeasure.__table__.drop(db.engine)
        AuditLog.__table__.drop(db.engine)
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
            UnitOfMeasure(
                id=UNIT_BOX_ID,
                tenant_id=TENANT_ID,
                code="BOX",
                name="Box",
                base_factor=Decimal("1.000000"),
            ),
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
                id=EMPTY_BATCH_PRODUCT_ID,
                tenant_id=TENANT_ID,
                internal_sku="EMPTY-BATCH-001",
                name="Empty Batch Product",
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
            ProductUnit(
                id=NON_BATCH_BOX_UNIT_ID,
                tenant_id=TENANT_ID,
                product_id=NON_BATCH_PRODUCT_ID,
                unit_id=UNIT_BOX_ID,
                conversion_factor_to_base=Decimal(
                    "10.000000"
                ),
                is_base=False,
                can_sell=True,
                can_receive=True,
                is_active=True,
            ),
            ProductUnit(
                id=EMPTY_BATCH_BOX_UNIT_ID,
                tenant_id=TENANT_ID,
                product_id=EMPTY_BATCH_PRODUCT_ID,
                unit_id=UNIT_BOX_ID,
                conversion_factor_to_base=Decimal(
                    "5.000000"
                ),
                is_base=False,
                can_sell=True,
                can_receive=True,
                is_active=True,
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
    response = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            count_mode="visible",
        ),
    )

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

    audit = AuditLog.query.filter_by(
        action="INVENTORY_COUNT_STARTED",
        entity_type="stock_count",
        entity_id=item["id"],
    ).one()

    assert audit.module_code == "INVENTORY"
    assert audit.tenant_id == TENANT_ID
    assert audit.branch_id == BRANCH_ID
    assert audit.user_id == USER_ID
    assert audit.new_values == {
        "status": "open",
    }
    assert audit.details["count_number"] == item["count_number"]
    assert audit.details["warehouse_id"] == WAREHOUSE_ID
    assert audit.details["scope_type"] == "full"
    assert audit.details["count_mode"] == "visible"


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
            count_mode="visible",
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
    created = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            count_mode="visible",
        ),
    )
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

    persisted_items = (
        StockCountItem.query
        .filter_by(
            stock_count_id=count_id,
        )
        .order_by(
            StockCountItem.line_number.asc()
        )
        .all()
    )

    for item in persisted_items:
        response = client.put(
            f"/api/inventory/stock-counts/{count_id}/items/{item.id}",
            json={
                "counted_quantity": str(
                    item.expected_quantity
                ),
            },
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

    audit = AuditLog.query.filter_by(
        action="INVENTORY_COUNT_COMPLETED",
        entity_type="stock_count",
        entity_id=count_id,
    ).one()

    assert audit.module_code == "INVENTORY"
    assert audit.tenant_id == TENANT_ID
    assert audit.branch_id == BRANCH_ID
    assert audit.user_id == USER_ID
    assert audit.old_values == {
        "status": "open",
    }
    assert audit.new_values == {
        "status": "completed",
    }
    assert audit.details["warehouse_id"] == WAREHOUSE_ID

    response = client.post(f"/api/inventory/stock-counts/{count_id}/complete")
    assert response.status_code == 409
    response = client.put(
        f"/api/inventory/stock-counts/{count_id}/items/{created.get_json()['item']['items'][0]['id']}",
        json={"counted_quantity": "1"},
    )
    assert response.status_code == 409


def test_stock_count_cancel_and_audit_rollback_together_when_commit_fails(
    client,
    monkeypatch,
):
    created = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(),
    )
    assert created.status_code == 201

    count_id = created.get_json()["item"]["id"]

    real_commit = db.session.commit

    def failing_commit():
        raise RuntimeError("forced commit failure")

    monkeypatch.setattr(
        db.session,
        "commit",
        failing_commit,
    )

    response = client.post(
        f"/api/inventory/stock-counts/{count_id}/cancel",
    )

    assert response.status_code == 500

    monkeypatch.setattr(
        db.session,
        "commit",
        real_commit,
    )

    db.session.rollback()

    count = StockCount.query.filter_by(
        id=count_id,
    ).one()

    assert count.status == "open"
    assert count.cancelled_at is None
    assert count.cancelled_by is None

    audit = AuditLog.query.filter_by(
        action="INVENTORY_COUNT_CANCELLED",
        entity_type="stock_count",
        entity_id=count_id,
    ).one_or_none()

    assert audit is None


def test_stock_count_cancel_unblocks_new_warehouse_count(client):
    created = client.post("/api/inventory/stock-counts", json=stock_count_payload())
    count_id = created.get_json()["item"]["id"]

    response = client.post(f"/api/inventory/stock-counts/{count_id}/cancel")
    assert response.status_code == 200

    item = response.get_json()["item"]

    assert item["status"] == "cancelled"
    assert item["cancelled_by"]["id"] == USER_ID

    audit = AuditLog.query.filter_by(
        action="INVENTORY_COUNT_CANCELLED",
        entity_type="stock_count",
        entity_id=count_id,
    ).one()

    assert audit.module_code == "INVENTORY"
    assert audit.tenant_id == TENANT_ID
    assert audit.branch_id == BRANCH_ID
    assert audit.user_id == USER_ID
    assert audit.old_values == {
        "status": "open",
    }
    assert audit.new_values == {
        "status": "cancelled",
    }
    assert audit.details["warehouse_id"] == WAREHOUSE_ID

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


def test_stock_count_list_filters_operational_lifecycle(
    client,
):
    now = datetime.now(timezone.utc)

    def add_count(
        *,
        count_id: str,
        status: str,
        variance: Decimal | None = None,
    ) -> StockCount:
        count = StockCount(
            id=count_id,
            tenant_id=TENANT_ID,
            branch_id=BRANCH_ID,
            warehouse_id=WAREHOUSE_ID,
            count_number=f"SC-{count_id.upper()}",
            idempotency_key=f"key-{count_id}",
            request_fingerprint=f"fingerprint-{count_id}",
            scope_type="full",
            count_mode="visible",
            status=status,
            snapshot_at=now,
            started_at=now,
            started_by=USER_ID,
            completed_at=(
                now
                if status == "completed"
                else None
            ),
            completed_by=(
                USER_ID
                if status == "completed"
                else None
            ),
            cancelled_at=(
                now
                if status == "cancelled"
                else None
            ),
            cancelled_by=(
                USER_ID
                if status == "cancelled"
                else None
            ),
        )
        db.session.add(count)
        db.session.flush()

        if variance is not None:
            db.session.add(
                StockCountItem(
                    id=f"item-{count_id}",
                    stock_count_id=count_id,
                    product_id=NON_BATCH_PRODUCT_ID,
                    batch_id=None,
                    source_type="snapshot",
                    line_number=1,
                    snapshot_quantity=Decimal("10"),
                    expected_quantity=Decimal("10"),
                    counted_quantity=(
                        Decimal("10") + variance
                    ),
                    variance_quantity=variance,
                    counted_at=now,
                    counted_by=USER_ID,
                )
            )

        return count

    add_count(
        count_id="lifecycle-counting",
        status="open",
    )
    add_count(
        count_id="lifecycle-awaiting",
        status="completed",
        variance=Decimal("-2"),
    )
    add_count(
        count_id="lifecycle-completed",
        status="completed",
        variance=Decimal("0"),
    )
    add_count(
        count_id="lifecycle-posted",
        status="completed",
        variance=Decimal("3"),
    )
    add_count(
        count_id="lifecycle-cancelled",
        status="cancelled",
    )

    db.session.add(
        StockAdjustment(
            id="adjustment-lifecycle-posted",
            tenant_id=TENANT_ID,
            branch_id=BRANCH_ID,
            warehouse_id=WAREHOUSE_ID,
            adjustment_number="SA-LIFECYCLE-POSTED",
            reason_code="stock_count",
            reason="Lifecycle filter test",
            source_type="stock_count",
            source_id="lifecycle-posted",
            status="posted",
            idempotency_key="adjustment-lifecycle-key",
            request_fingerprint="adjustment-lifecycle-fingerprint",
            posted_at=now,
            posted_by=USER_ID,
        )
    )

    db.session.commit()

    expected = {
        "counting": "lifecycle-counting",
        "awaiting_posting": "lifecycle-awaiting",
        "posted": "lifecycle-posted",
        "completed": "lifecycle-completed",
        "cancelled": "lifecycle-cancelled",
    }

    for lifecycle, expected_id in expected.items():
        response = client.get(
            "/api/inventory/stock-counts"
            f"?lifecycle={lifecycle}"
        )

        assert response.status_code == 200

        payload = response.get_json()

        assert payload["pagination"]["total"] == 1
        assert [
            item["id"]
            for item in payload["items"]
        ] == [expected_id]


def test_stock_count_list_validates_filters(client):
    response = client.get("/api/inventory/stock-counts?page=0")
    assert response.status_code == 400
    assert "page" in error_message(response)

    response = client.get("/api/inventory/stock-counts?status=posted")
    assert response.status_code == 400
    assert "status" in error_message(response)

    response = client.get(
        "/api/inventory/stock-counts?lifecycle=unknown"
    )
    assert response.status_code == 400
    assert "lifecycle" in error_message(response)

    response = client.get(
        "/api/inventory/stock-counts"
        "?status=open&lifecycle=counting"
    )
    assert response.status_code == 400
    assert "status and lifecycle" in error_message(
        response
    )

    response = client.get(
        f"/api/inventory/stock-counts?warehouse_id={OTHER_BRANCH_WAREHOUSE_ID}"
    )
    assert response.status_code == 400
    assert "warehouse_id" in error_message(response)


# ============================================================================
# Blind counting and discovered physical stock
# ============================================================================


def test_stock_count_defaults_to_blind_mode(client):
    response = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(),
    )

    assert response.status_code == 201

    count_id = response.get_json()["item"]["id"]
    count = db.session.get(StockCount, count_id)

    assert count is not None
    assert count.count_mode == "blind"


def test_stock_count_can_explicitly_use_visible_mode(client):
    response = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            count_mode="visible",
        ),
    )

    assert response.status_code == 201

    count_id = response.get_json()["item"]["id"]
    count = db.session.get(StockCount, count_id)

    assert count is not None
    assert count.count_mode == "visible"


def test_stock_count_mode_participates_in_idempotency_fingerprint(client):
    first = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            count_mode="blind",
        ),
    )

    assert first.status_code == 201

    replay_with_different_mode = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            count_mode="visible",
        ),
    )

    assert replay_with_different_mode.status_code == 409
    assert "idempotency_key" in error_message(
        replay_with_different_mode
    )


def test_snapshot_stock_count_items_are_marked_as_snapshot(client):
    response = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(),
    )

    assert response.status_code == 201

    count_id = response.get_json()["item"]["id"]

    items = (
        StockCountItem.query
        .filter_by(
            stock_count_id=count_id,
        )
        .all()
    )

    assert items
    assert {
        item.source_type
        for item in items
    } == {"snapshot"}


def test_discovered_batches_can_be_recorded_in_parts(client):
    from app.schemas import (
        AddDiscoveredStockCountItemRequest,
    )
    from app.services.tenant.inventory import (
        StockCountService,
    )

    created = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(),
    )

    assert created.status_code == 201

    count_id = created.get_json()["item"]["id"]

    service = StockCountService(db.session)

    observations = [
        {
            "batch_number": "BATCH-X",
            "expiry_date": "2027-05-31",
            "counted_quantity": "100",
        },
        {
            "batch_number": "BATCH-Y",
            "expiry_date": "2028-06-30",
            "counted_quantity": "50",
        },
        {
            "batch_number": "BATCH-Z",
            "expiry_date": "2029-01-31",
            "counted_quantity": "50",
        },
    ]

    created_items = []

    for observation in observations:
        request = (
            AddDiscoveredStockCountItemRequest
            .from_payload(
                {
                    "product_id": BATCH_PRODUCT_ID,
                    **observation,
                }
            )
        )

        item = service.add_discovered_item(
            tenant_id=TENANT_ID,
            branch_id=BRANCH_ID,
            count_id=count_id,
            counted_by=USER_ID,
            request=request,
        )

        created_items.append(item)

    persisted = (
        StockCountItem.query
        .filter_by(
            stock_count_id=count_id,
            product_id=BATCH_PRODUCT_ID,
            source_type="discovered",
        )
        .order_by(
            StockCountItem.line_number.asc()
        )
        .all()
    )

    assert len(persisted) == 3

    assert [
        item.observed_batch_number
        for item in persisted
    ] == [
        "BATCH-X",
        "BATCH-Y",
        "BATCH-Z",
    ]

    assert [
        item.observed_expiry_date.isoformat()
        for item in persisted
    ] == [
        "2027-05-31",
        "2028-06-30",
        "2029-01-31",
    ]

    assert [
        item.counted_quantity
        for item in persisted
    ] == [
        Decimal("100.0000"),
        Decimal("50.0000"),
        Decimal("50.0000"),
    ]

    assert all(
        item.batch_id is None
        for item in persisted
    )

    assert all(
        item.snapshot_quantity
        == Decimal("0.0000")
        for item in persisted
    )

    assert all(
        item.expected_quantity
        == Decimal("0.0000")
        for item in persisted
    )

    assert [
        item.variance_quantity
        for item in persisted
    ] == [
        Decimal("100.0000"),
        Decimal("50.0000"),
        Decimal("50.0000"),
    ]

    assert sum(
        (
            item.counted_quantity
            for item in persisted
        ),
        Decimal("0"),
    ) == Decimal("200.0000")

    assert all(
        item.counted_by == USER_ID
        for item in created_items
    )


def test_discovered_batch_identity_rejects_case_only_duplicate(client):
    from app.errors import ConflictError
    from app.schemas import (
        AddDiscoveredStockCountItemRequest,
    )
    from app.services.tenant.inventory import (
        StockCountService,
    )

    created = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(),
    )

    count_id = created.get_json()["item"]["id"]
    service = StockCountService(db.session)

    first = (
        AddDiscoveredStockCountItemRequest
        .from_payload(
            {
                "product_id": BATCH_PRODUCT_ID,
                "batch_number": "BATCH-Y",
                "expiry_date": "2028-06-30",
                "counted_quantity": "50",
            }
        )
    )

    service.add_discovered_item(
        tenant_id=TENANT_ID,
        branch_id=BRANCH_ID,
        count_id=count_id,
        counted_by=USER_ID,
        request=first,
    )

    duplicate = (
        AddDiscoveredStockCountItemRequest
        .from_payload(
            {
                "product_id": BATCH_PRODUCT_ID,
                "batch_number": "batch-y",
                "expiry_date": "2028-06-30",
                "counted_quantity": "25",
            }
        )
    )

    with pytest.raises(
        ConflictError,
        match="already has a stock count line",
    ):
        service.add_discovered_item(
            tenant_id=TENANT_ID,
            branch_id=BRANCH_ID,
            count_id=count_id,
            counted_by=USER_ID,
            request=duplicate,
        )


def test_discovered_item_cannot_duplicate_snapshot_batch(client):
    from app.errors import ConflictError
    from app.schemas import (
        AddDiscoveredStockCountItemRequest,
    )
    from app.services.tenant.inventory import (
        StockCountService,
    )

    created = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(),
    )

    count_id = created.get_json()["item"]["id"]

    request = (
        AddDiscoveredStockCountItemRequest
        .from_payload(
            {
                "product_id": BATCH_PRODUCT_ID,
                "batch_number": "BATCH-A",
                "expiry_date": "2027-01-31",
                "counted_quantity": "10",
            }
        )
    )

    with pytest.raises(
        ConflictError,
        match="already has a stock count line",
    ):
        StockCountService(
            db.session
        ).add_discovered_item(
            tenant_id=TENANT_ID,
            branch_id=BRANCH_ID,
            count_id=count_id,
            counted_by=USER_ID,
            request=request,
        )


def test_discovered_item_requires_open_stock_count(client):
    from app.errors import ConflictError
    from app.schemas import (
        AddDiscoveredStockCountItemRequest,
    )
    from app.services.tenant.inventory import (
        StockCountService,
    )

    created = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(),
    )

    count_id = created.get_json()["item"]["id"]

    count = db.session.get(
        StockCount,
        count_id,
    )
    count.status = "completed"
    db.session.commit()

    request = (
        AddDiscoveredStockCountItemRequest
        .from_payload(
            {
                "product_id": BATCH_PRODUCT_ID,
                "batch_number": "BATCH-Y",
                "expiry_date": "2028-06-30",
                "counted_quantity": "50",
            }
        )
    )

    with pytest.raises(
        ConflictError,
        match="not open",
    ):
        StockCountService(
            db.session
        ).add_discovered_item(
            tenant_id=TENANT_ID,
            branch_id=BRANCH_ID,
            count_id=count_id,
            counted_by=USER_ID,
            request=request,
        )


@pytest.mark.parametrize(
    (
        "product_id",
        "payload",
        "expected_message",
    ),
    [
        (
            BATCH_PRODUCT_ID,
            {
                "expiry_date": "2028-06-30",
                "counted_quantity": "50",
            },
            "batch_number is required",
        ),
        (
            BATCH_PRODUCT_ID,
            {
                "batch_number": "BATCH-Y",
                "counted_quantity": "50",
            },
            "expiry_date is required",
        ),
        (
            NON_BATCH_PRODUCT_ID,
            {
                "batch_number": "NOT-ALLOWED",
                "counted_quantity": "5",
            },
            "batch_number is not allowed",
        ),
        (
            NON_BATCH_PRODUCT_ID,
            {
                "expiry_date": "2028-06-30",
                "counted_quantity": "5",
            },
            "expiry_date is not allowed",
        ),
    ],
)
def test_discovered_item_enforces_product_batch_expiry_policy(
    client,
    product_id,
    payload,
    expected_message,
):
    from app.errors import ValidationError
    from app.schemas import (
        AddDiscoveredStockCountItemRequest,
    )
    from app.services.tenant.inventory import (
        StockCountService,
    )

    created = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(),
    )

    count_id = created.get_json()["item"]["id"]

    request = (
        AddDiscoveredStockCountItemRequest
        .from_payload(
            {
                "product_id": product_id,
                **payload,
            }
        )
    )

    with pytest.raises(
        ValidationError,
        match=expected_message,
    ):
        StockCountService(
            db.session
        ).add_discovered_item(
            tenant_id=TENANT_ID,
            branch_id=BRANCH_ID,
            count_id=count_id,
            counted_by=USER_ID,
            request=request,
        )


@pytest.mark.parametrize(
    (
        "product_id",
        "expected_message",
    ),
    [
        (
            "service-product",
            "inventory-tracked",
        ),
        (
            "other-tenant-product",
            "belong to this tenant",
        ),
    ],
)
def test_discovered_item_preserves_product_scope_rules(
    client,
    product_id,
    expected_message,
):
    from app.errors import ValidationError
    from app.schemas import (
        AddDiscoveredStockCountItemRequest,
    )
    from app.services.tenant.inventory import (
        StockCountService,
    )

    created = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(),
    )

    count_id = created.get_json()["item"]["id"]

    request = (
        AddDiscoveredStockCountItemRequest
        .from_payload(
            {
                "product_id": product_id,
                "counted_quantity": "1",
            }
        )
    )

    with pytest.raises(
        ValidationError,
        match=expected_message,
    ):
        StockCountService(
            db.session
        ).add_discovered_item(
            tenant_id=TENANT_ID,
            branch_id=BRANCH_ID,
            count_id=count_id,
            counted_by=USER_ID,
            request=request,
        )


def test_non_batch_product_cannot_create_duplicate_discovered_line(client):
    from app.errors import ConflictError
    from app.schemas import (
        AddDiscoveredStockCountItemRequest,
    )
    from app.services.tenant.inventory import (
        StockCountService,
    )

    created = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(),
    )

    count_id = created.get_json()["item"]["id"]

    request = (
        AddDiscoveredStockCountItemRequest
        .from_payload(
            {
                "product_id": NON_BATCH_PRODUCT_ID,
                "counted_quantity": "5",
            }
        )
    )

    with pytest.raises(
        ConflictError,
        match="existing line",
    ):
        StockCountService(
            db.session
        ).add_discovered_item(
            tenant_id=TENANT_ID,
            branch_id=BRANCH_ID,
            count_id=count_id,
            counted_by=USER_ID,
            request=request,
        )


# ============================================================================
# Blind Stock Count serialization
# ============================================================================


def test_open_blind_count_hides_system_quantities_and_variance(client):
    response = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            count_mode="blind",
        ),
    )

    assert response.status_code == 201

    item = response.get_json()["item"]

    assert item["count_mode"] == "blind"
    assert item["status"] == "open"

    assert "variance_items" not in item["summary"]
    assert (
        "positive_variance_items"
        not in item["summary"]
    )
    assert (
        "negative_variance_items"
        not in item["summary"]
    )

    for line in item["items"]:
        assert line["source_type"] == "snapshot"

        assert (
            "snapshot_quantity"
            not in line
        )
        assert (
            "expected_quantity"
            not in line
        )
        assert (
            "variance_quantity"
            not in line
        )

        assert "counted_quantity" in line


def test_open_visible_count_exposes_system_quantities_and_variance(client):
    response = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            count_mode="visible",
        ),
    )

    assert response.status_code == 201

    item = response.get_json()["item"]

    assert item["count_mode"] == "visible"

    assert "variance_items" in item["summary"]
    assert (
        "positive_variance_items"
        in item["summary"]
    )
    assert (
        "negative_variance_items"
        in item["summary"]
    )

    for line in item["items"]:
        assert "snapshot_quantity" in line
        assert "expected_quantity" in line
        assert "variance_quantity" in line


def test_completed_blind_count_reveals_system_quantities_and_variance(client):
    created = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            count_mode="blind",
        ),
    )

    assert created.status_code == 201

    count_id = (
        created.get_json()["item"]["id"]
    )

    count = db.session.get(
        StockCount,
        count_id,
    )

    lines = (
        StockCountItem.query
        .filter_by(
            stock_count_id=count_id,
        )
        .order_by(
            StockCountItem.line_number.asc()
        )
        .all()
    )

    for line in lines:
        response = client.put(
            (
                f"/api/inventory/stock-counts/"
                f"{count_id}/items/{line.id}"
            ),
            json={
                "counted_quantity":
                    str(
                        line.expected_quantity
                    ),
            },
        )

        assert response.status_code == 200

    response = client.post(
        (
            f"/api/inventory/stock-counts/"
            f"{count_id}/complete"
        )
    )

    assert response.status_code == 200

    item = response.get_json()["item"]

    assert item["count_mode"] == "blind"
    assert item["status"] == "completed"

    assert "variance_items" in item["summary"]
    assert (
        "positive_variance_items"
        in item["summary"]
    )
    assert (
        "negative_variance_items"
        in item["summary"]
    )

    for line in item["items"]:
        assert "snapshot_quantity" in line
        assert "expected_quantity" in line
        assert "variance_quantity" in line

    assert count is not None


def test_blind_count_remains_blind_after_entering_quantity(client):
    created = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            count_mode="blind",
        ),
    )

    assert created.status_code == 201

    count_id = (
        created.get_json()["item"]["id"]
    )

    line = (
        StockCountItem.query
        .filter_by(
            stock_count_id=count_id,
        )
        .order_by(
            StockCountItem.line_number.asc()
        )
        .first()
    )

    assert line is not None

    response = client.put(
        (
            f"/api/inventory/stock-counts/"
            f"{count_id}/items/{line.id}"
        ),
        json={
            "counted_quantity": "7",
        },
    )

    assert response.status_code == 200

    item = response.get_json()["item"]

    updated = next(
        candidate
        for candidate in item["items"]
        if candidate["id"] == str(line.id)
    )

    assert (
        updated["counted_quantity"]
        == "7.0000"
    )

    assert "snapshot_quantity" not in updated
    assert "expected_quantity" not in updated
    assert "variance_quantity" not in updated

    assert "variance_items" not in item["summary"]


# ============================================================================
# Discovered Stock Count API
# ============================================================================


def test_discovered_stock_count_api_records_batch_expiry_line(client):
    created = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(),
    )

    assert created.status_code == 201

    count_id = created.get_json()["item"]["id"]

    response = client.post(
        (
            f"/api/inventory/stock-counts/"
            f"{count_id}/items/discovered"
        ),
        json={
            "product_id": BATCH_PRODUCT_ID,
            "batch_number": "BATCH-Y",
            "expiry_date": "2028-06-30",
            "counted_quantity": "50",
            "notes": "Found during physical count.",
        },
    )

    assert response.status_code == 201

    payload = response.get_json()

    assert payload["ok"] is True

    item = payload["item"]

    assert item["count_mode"] == "blind"
    assert item["status"] == "open"

    discovered = next(
        line
        for line in item["items"]
        if line["source_type"] == "discovered"
    )

    assert discovered["product"]["id"] == BATCH_PRODUCT_ID
    assert discovered["batch"] is None
    assert discovered["observed_batch_number"] == "BATCH-Y"
    assert discovered["observed_expiry_date"] == "2028-06-30"
    assert discovered["counted_quantity"] == "50.0000"
    assert discovered["counted_by"]["id"] == USER_ID

    # Open blind counts must not disclose reconciliation quantities.
    assert "snapshot_quantity" not in discovered
    assert "expected_quantity" not in discovered
    assert "variance_quantity" not in discovered


def test_discovered_stock_count_api_accepts_multiple_batches_for_product(client):
    created = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(),
    )

    count_id = created.get_json()["item"]["id"]

    observations = [
        ("BATCH-X", "2027-05-31", "100"),
        ("BATCH-Y", "2028-06-30", "50"),
        ("BATCH-Z", "2029-01-31", "50"),
    ]

    for batch_number, expiry_date, quantity in observations:
        response = client.post(
            (
                f"/api/inventory/stock-counts/"
                f"{count_id}/items/discovered"
            ),
            json={
                "product_id": BATCH_PRODUCT_ID,
                "batch_number": batch_number,
                "expiry_date": expiry_date,
                "counted_quantity": quantity,
            },
        )

        assert response.status_code == 201

    persisted = (
        StockCountItem.query
        .filter_by(
            stock_count_id=count_id,
            product_id=BATCH_PRODUCT_ID,
            source_type="discovered",
        )
        .all()
    )

    assert len(persisted) == 3

    total = sum(
        (
            item.counted_quantity
            for item in persisted
        ),
        Decimal("0"),
    )

    assert total == Decimal("200.0000")


def test_discovered_stock_count_api_rejects_duplicate_batch_identity(client):
    created = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(),
    )

    count_id = created.get_json()["item"]["id"]

    first = client.post(
        (
            f"/api/inventory/stock-counts/"
            f"{count_id}/items/discovered"
        ),
        json={
            "product_id": BATCH_PRODUCT_ID,
            "batch_number": "BATCH-Y",
            "expiry_date": "2028-06-30",
            "counted_quantity": "50",
        },
    )

    assert first.status_code == 201

    duplicate = client.post(
        (
            f"/api/inventory/stock-counts/"
            f"{count_id}/items/discovered"
        ),
        json={
            "product_id": BATCH_PRODUCT_ID,
            "batch_number": "batch-y",
            "expiry_date": "2028-06-30",
            "counted_quantity": "10",
        },
    )

    assert duplicate.status_code == 409
    assert "already has a stock count line" in error_message(
        duplicate
    )


@pytest.mark.parametrize(
    (
        "payload",
        "expected_message",
    ),
    [
        (
            {
                "product_id": BATCH_PRODUCT_ID,
                "expiry_date": "2028-06-30",
                "counted_quantity": "50",
            },
            "batch_number is required",
        ),
        (
            {
                "product_id": BATCH_PRODUCT_ID,
                "batch_number": "BATCH-Y",
                "counted_quantity": "50",
            },
            "expiry_date is required",
        ),
        (
            {
                "product_id": BATCH_PRODUCT_ID,
                "batch_number": "BATCH-Y",
                "expiry_date": "2028-06-30",
                "counted_quantity": "-1",
            },
            "counted_quantity",
        ),
    ],
)
def test_discovered_stock_count_api_validates_payload(
    client,
    payload,
    expected_message,
):
    created = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(),
    )

    count_id = created.get_json()["item"]["id"]

    response = client.post(
        (
            f"/api/inventory/stock-counts/"
            f"{count_id}/items/discovered"
        ),
        json=payload,
    )

    assert response.status_code == 400
    assert expected_message in error_message(response)


def test_discovered_stock_count_api_rejects_completed_count(client):
    created = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(),
    )

    count_id = created.get_json()["item"]["id"]

    count = db.session.get(
        StockCount,
        count_id,
    )

    count.status = "completed"
    db.session.commit()

    response = client.post(
        (
            f"/api/inventory/stock-counts/"
            f"{count_id}/items/discovered"
        ),
        json={
            "product_id": BATCH_PRODUCT_ID,
            "batch_number": "BATCH-Y",
            "expiry_date": "2028-06-30",
            "counted_quantity": "50",
        },
    )

    assert response.status_code == 409
    assert "not open" in error_message(response)


def test_discovered_stock_count_api_requires_inventory_count_permission(
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
        (
            "/api/inventory/stock-counts/"
            "any-count/items/discovered"
        ),
        json={
            "product_id": BATCH_PRODUCT_ID,
            "batch_number": "BATCH-Y",
            "expiry_date": "2028-06-30",
            "counted_quantity": "50",
        },
    )

    assert response.status_code == 403

    assert (
        captured["kwargs"]["permission"]
        == "inventory.count"
    )


# ============================================================================
# Selected Stock Count discovered-item scope
# ============================================================================


def test_selected_stock_count_rejects_discovered_product_outside_scope(
    client,
):
    created = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            product_ids=[
                BATCH_PRODUCT_ID,
            ],
        ),
    )

    assert created.status_code == 201
    count_id = created.get_json()["item"]["id"]

    response = client.post(
        (
            f"/api/inventory/stock-counts/"
            f"{count_id}/items/discovered"
        ),
        json={
            "product_id": NON_BATCH_PRODUCT_ID,
            "counted_quantity": "5",
        },
    )

    assert response.status_code == 400
    assert (
        "selected" in
        error_message(response).lower()
    )
    assert (
        "scope" in
        error_message(response).lower()
    )

    assert (
        StockCountItem.query
        .filter_by(
            stock_count_id=count_id,
            product_id=NON_BATCH_PRODUCT_ID,
            source_type="discovered",
        )
        .count()
        == 0
    )


def test_selected_stock_count_allows_new_batch_for_in_scope_product(
    client,
):
    created = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            product_ids=[
                BATCH_PRODUCT_ID,
            ],
        ),
    )

    assert created.status_code == 201
    count_id = created.get_json()["item"]["id"]

    response = client.post(
        (
            f"/api/inventory/stock-counts/"
            f"{count_id}/items/discovered"
        ),
        json={
            "product_id": BATCH_PRODUCT_ID,
            "batch_number": "SELECTED-FOUND-001",
            "expiry_date": "2029-12-31",
            "counted_quantity": "7",
        },
    )

    assert response.status_code == 201

    item = response.get_json()["item"]

    discovered = next(
        line
        for line in item["items"]
        if (
            line["source_type"] == "discovered"
            and
            line["observed_batch_number"]
            == "SELECTED-FOUND-001"
        )
    )

    assert (
        discovered["product"]["id"]
        == BATCH_PRODUCT_ID
    )
    assert (
        discovered["counted_quantity"]
        == "7.0000"
    )
    assert discovered["batch"] is None


# ============================================================================
# Persisted selected Product scope
# ============================================================================


def test_selected_stock_count_persists_exact_product_scope(
    client,
):
    created = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            product_ids=[
                BATCH_PRODUCT_ID,
                NON_BATCH_PRODUCT_ID,
            ],
        ),
    )

    assert created.status_code == 201
    count_id = created.get_json()["item"]["id"]

    scope_product_ids = {
        row.product_id
        for row in (
            StockCountScopeProduct.query
            .filter_by(
                stock_count_id=count_id,
            )
            .all()
        )
    }

    assert scope_product_ids == {
        BATCH_PRODUCT_ID,
        NON_BATCH_PRODUCT_ID,
    }


def test_full_stock_count_does_not_create_selected_scope_rows(
    client,
):
    created = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(),
    )

    assert created.status_code == 201
    count_id = created.get_json()["item"]["id"]

    assert (
        StockCountScopeProduct.query
        .filter_by(
            stock_count_id=count_id,
        )
        .count()
        == 0
    )


def test_selected_scope_membership_is_independent_of_snapshot_lines(
    client,
):
    created = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            product_ids=[
                BATCH_PRODUCT_ID,
            ],
        ),
    )

    assert created.status_code == 201
    count_id = created.get_json()["item"]["id"]

    # Simulate a count where physical snapshot lines are not the source
    # of truth for selected Product membership.
    (
        StockCountItem.query
        .filter_by(
            stock_count_id=count_id,
        )
        .delete(
            synchronize_session=False
        )
    )
    db.session.commit()

    response = client.post(
        (
            f"/api/inventory/stock-counts/"
            f"{count_id}/items/discovered"
        ),
        json={
            "product_id": BATCH_PRODUCT_ID,
            "batch_number": "SCOPE-FOUND-001",
            "expiry_date": "2030-06-30",
            "counted_quantity": "4",
        },
    )

    assert response.status_code == 201

    discovered = next(
        line
        for line in response.get_json()["item"]["items"]
        if line["source_type"] == "discovered"
    )

    assert (
        discovered["product"]["id"]
        == BATCH_PRODUCT_ID
    )
    assert (
        discovered["observed_batch_number"]
        == "SCOPE-FOUND-001"
    )


# ============================================================================
# Selected Product with no known system batch
# ============================================================================


def test_selected_batch_product_without_system_batch_can_start_count(
    client,
):
    response = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            product_ids=[
                EMPTY_BATCH_PRODUCT_ID,
            ],
        ),
    )

    assert response.status_code == 201

    item = response.get_json()["item"]

    assert item["scope_type"] == "selected"
    assert item["items"] == []

    scope_product = (
        StockCountScopeProduct.query
        .filter_by(
            stock_count_id=item["id"],
            product_id=EMPTY_BATCH_PRODUCT_ID,
        )
        .one()
    )

    assert scope_product.no_stock_confirmed_at is None
    assert scope_product.no_stock_confirmed_by is None


def test_selected_empty_batch_product_requires_explicit_no_stock_confirmation(
    client,
):
    created = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            product_ids=[
                EMPTY_BATCH_PRODUCT_ID,
            ],
        ),
    )

    assert created.status_code == 201
    count_id = created.get_json()["item"]["id"]

    completed = client.post(
        (
            f"/api/inventory/stock-counts/"
            f"{count_id}/complete"
        )
    )

    assert completed.status_code == 400

    message = error_message(completed).lower()

    assert "selected product" in message
    assert "no stock" in message


def test_selected_empty_batch_product_can_confirm_no_stock_and_complete(
    client,
):
    created = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            product_ids=[
                EMPTY_BATCH_PRODUCT_ID,
            ],
        ),
    )

    assert created.status_code == 201
    count_id = created.get_json()["item"]["id"]

    confirmed = client.post(
        (
            f"/api/inventory/stock-counts/"
            f"{count_id}/scope-products/"
            f"{EMPTY_BATCH_PRODUCT_ID}/confirm-no-stock"
        )
    )

    assert confirmed.status_code == 200

    scope_product = (
        StockCountScopeProduct.query
        .filter_by(
            stock_count_id=count_id,
            product_id=EMPTY_BATCH_PRODUCT_ID,
        )
        .one()
    )

    assert scope_product.no_stock_confirmed_at is not None
    assert scope_product.no_stock_confirmed_by == USER_ID

    completed = client.post(
        (
            f"/api/inventory/stock-counts/"
            f"{count_id}/complete"
        )
    )

    assert completed.status_code == 200
    assert completed.get_json()["item"]["status"] == "completed"


def test_no_stock_confirmation_rejects_product_with_physical_lines(
    client,
):
    created = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            product_ids=[
                BATCH_PRODUCT_ID,
            ],
        ),
    )

    assert created.status_code == 201
    count_id = created.get_json()["item"]["id"]

    response = client.post(
        (
            f"/api/inventory/stock-counts/"
            f"{count_id}/scope-products/"
            f"{BATCH_PRODUCT_ID}/confirm-no-stock"
        )
    )

    assert response.status_code == 409
    assert "count lines" in error_message(response).lower()


def test_discovered_line_clears_prior_no_stock_confirmation(
    client,
):
    created = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            product_ids=[
                EMPTY_BATCH_PRODUCT_ID,
            ],
        ),
    )

    assert created.status_code == 201
    count_id = created.get_json()["item"]["id"]

    confirmed = client.post(
        (
            f"/api/inventory/stock-counts/"
            f"{count_id}/scope-products/"
            f"{EMPTY_BATCH_PRODUCT_ID}/confirm-no-stock"
        )
    )

    assert confirmed.status_code == 200

    discovered = client.post(
        (
            f"/api/inventory/stock-counts/"
            f"{count_id}/items/discovered"
        ),
        json={
            "product_id": EMPTY_BATCH_PRODUCT_ID,
            "batch_number": "PHYSICAL-FOUND-001",
            "expiry_date": "2030-12-31",
            "counted_quantity": "3",
        },
    )

    assert discovered.status_code == 201

    scope_product = (
        StockCountScopeProduct.query
        .filter_by(
            stock_count_id=count_id,
            product_id=EMPTY_BATCH_PRODUCT_ID,
        )
        .one()
    )

    assert scope_product.no_stock_confirmed_at is None
    assert scope_product.no_stock_confirmed_by is None

    lines = (
        StockCountItem.query
        .filter_by(
            stock_count_id=count_id,
            product_id=EMPTY_BATCH_PRODUCT_ID,
            source_type="discovered",
        )
        .all()
    )

    assert len(lines) == 1


# ============================================================================
# Selected Product scope serialization
# ============================================================================


def test_selected_empty_batch_product_serializes_as_unresolved_scope(
    client,
):
    created = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            product_ids=[
                EMPTY_BATCH_PRODUCT_ID,
            ],
        ),
    )

    assert created.status_code == 201

    item = created.get_json()["item"]

    assert item["items"] == []
    assert len(item["scope_products"]) == 1

    scope_product = item["scope_products"][0]

    assert (
        scope_product["product"]["id"]
        == EMPTY_BATCH_PRODUCT_ID
    )
    assert (
        scope_product["resolution_status"]
        == "unresolved"
    )
    assert scope_product["physical_line_count"] == 0
    assert scope_product["no_stock_confirmed_at"] is None
    assert scope_product["no_stock_confirmed_by"] is None


def test_selected_product_with_snapshot_lines_serializes_physical_lines(
    client,
):
    created = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            product_ids=[
                BATCH_PRODUCT_ID,
            ],
        ),
    )

    assert created.status_code == 201

    item = created.get_json()["item"]

    scope_product = next(
        scope
        for scope in item["scope_products"]
        if (
            scope["product"]["id"]
            == BATCH_PRODUCT_ID
        )
    )

    assert (
        scope_product["resolution_status"]
        == "physical_lines"
    )
    assert scope_product["physical_line_count"] > 0
    assert scope_product["no_stock_confirmed_at"] is None
    assert scope_product["no_stock_confirmed_by"] is None


def test_confirm_no_stock_serializes_scope_resolution_and_audit_user(
    client,
):
    created = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            product_ids=[
                EMPTY_BATCH_PRODUCT_ID,
            ],
        ),
    )

    assert created.status_code == 201
    count_id = created.get_json()["item"]["id"]

    confirmed = client.post(
        (
            f"/api/inventory/stock-counts/"
            f"{count_id}/scope-products/"
            f"{EMPTY_BATCH_PRODUCT_ID}/confirm-no-stock"
        )
    )

    assert confirmed.status_code == 200

    scope_product = (
        confirmed
        .get_json()["item"]["scope_products"][0]
    )

    assert (
        scope_product["resolution_status"]
        == "no_stock_confirmed"
    )
    assert scope_product["physical_line_count"] == 0
    assert scope_product["no_stock_confirmed_at"] is not None
    assert (
        scope_product["no_stock_confirmed_by"]["id"]
        == USER_ID
    )


def test_discovered_stock_changes_scope_resolution_to_physical_lines(
    client,
):
    created = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            product_ids=[
                EMPTY_BATCH_PRODUCT_ID,
            ],
        ),
    )

    assert created.status_code == 201
    count_id = created.get_json()["item"]["id"]

    confirmed = client.post(
        (
            f"/api/inventory/stock-counts/"
            f"{count_id}/scope-products/"
            f"{EMPTY_BATCH_PRODUCT_ID}/confirm-no-stock"
        )
    )

    assert confirmed.status_code == 200

    discovered = client.post(
        (
            f"/api/inventory/stock-counts/"
            f"{count_id}/items/discovered"
        ),
        json={
            "product_id": EMPTY_BATCH_PRODUCT_ID,
            "batch_number": "SERIALIZED-FOUND-001",
            "expiry_date": "2031-06-30",
            "counted_quantity": "2",
        },
    )

    assert discovered.status_code == 201

    scope_product = (
        discovered
        .get_json()["item"]["scope_products"][0]
    )

    assert (
        scope_product["resolution_status"]
        == "physical_lines"
    )
    assert scope_product["physical_line_count"] == 1
    assert scope_product["no_stock_confirmed_at"] is None
    assert scope_product["no_stock_confirmed_by"] is None


def test_full_stock_count_serializes_empty_scope_products(
    client,
):
    created = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(),
    )

    assert created.status_code == 201
    assert (
        created.get_json()["item"]["scope_products"]
        == []
    )



def test_stock_count_db_rejects_second_unbatched_item_same_product(
    client,
):
    created = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(),
    )

    assert created.status_code == 201

    count_id = created.get_json()["item"]["id"]

    existing = (
        StockCountItem.query
        .filter_by(
            stock_count_id=count_id,
            product_id=NON_BATCH_PRODUCT_ID,
            batch_id=None,
        )
        .one()
    )

    duplicate = StockCountItem(
        stock_count_id=count_id,
        product_id=NON_BATCH_PRODUCT_ID,
        batch_id=None,
        source_type="discovered",
        line_number=existing.line_number + 1000,
        snapshot_quantity=Decimal("0.0000"),
        expected_quantity=Decimal("0.0000"),
        counted_quantity=Decimal("1.0000"),
        variance_quantity=Decimal("1.0000"),
        counted_at=datetime.now(timezone.utc),
        counted_by=USER_ID,
    )

    db.session.add(duplicate)

    with pytest.raises(IntegrityError):
        db.session.commit()

    db.session.rollback()


def test_stock_count_db_rejects_second_open_count_same_warehouse(
    app_context,
):
    first = StockCount(
        tenant_id=TENANT_ID,
        branch_id=BRANCH_ID,
        warehouse_id=WAREHOUSE_ID,
        count_number="SC-OPEN-001",
        idempotency_key="stock-count-open-001",
        request_fingerprint="a" * 64,
        scope_type="full",
        count_mode="blind",
        status="open",
        snapshot_at=datetime.now(timezone.utc),
        started_at=datetime.now(timezone.utc),
        started_by=USER_ID,
    )

    second = StockCount(
        tenant_id=TENANT_ID,
        branch_id=BRANCH_ID,
        warehouse_id=WAREHOUSE_ID,
        count_number="SC-OPEN-002",
        idempotency_key="stock-count-open-002",
        request_fingerprint="b" * 64,
        scope_type="full",
        count_mode="blind",
        status="open",
        snapshot_at=datetime.now(timezone.utc),
        started_at=datetime.now(timezone.utc),
        started_by=USER_ID,
    )

    db.session.add(first)
    db.session.commit()

    db.session.add(second)

    with pytest.raises(IntegrityError):
        db.session.commit()

    db.session.rollback()


def test_stock_count_db_allows_completed_history_with_open_count(
    app_context,
):
    completed = StockCount(
        tenant_id=TENANT_ID,
        branch_id=BRANCH_ID,
        warehouse_id=WAREHOUSE_ID,
        count_number="SC-HISTORY-001",
        idempotency_key="stock-count-history-001",
        request_fingerprint="c" * 64,
        scope_type="full",
        count_mode="blind",
        status="completed",
        snapshot_at=datetime.now(timezone.utc),
        started_at=datetime.now(timezone.utc),
        started_by=USER_ID,
        completed_at=datetime.now(timezone.utc),
        completed_by=USER_ID,
    )

    open_count = StockCount(
        tenant_id=TENANT_ID,
        branch_id=BRANCH_ID,
        warehouse_id=WAREHOUSE_ID,
        count_number="SC-OPEN-003",
        idempotency_key="stock-count-open-003",
        request_fingerprint="d" * 64,
        scope_type="full",
        count_mode="blind",
        status="open",
        snapshot_at=datetime.now(timezone.utc),
        started_at=datetime.now(timezone.utc),
        started_by=USER_ID,
    )

    db.session.add_all([completed, open_count])
    db.session.commit()

    rows = (
        db.session.query(StockCount)
        .filter(
            StockCount.tenant_id == TENANT_ID,
            StockCount.warehouse_id == WAREHOUSE_ID,
        )
        .all()
    )

    assert len(rows) == 2
    assert {row.status for row in rows} == {
        "completed",
        "open",
    }
def test_stock_count_item_converts_product_unit_quantity_to_base(client):
    create_response = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            count_mode="visible",
            idempotency_key=(
                "stock-count-product-unit-update"
            ),
        ),
    )

    assert create_response.status_code == 201

    count = create_response.get_json()["item"]

    line = next(
        item
        for item in count["items"]
        if item["product"]["id"]
        == NON_BATCH_PRODUCT_ID
    )

    response = client.put(
        (
            f"/api/inventory/stock-counts/"
            f"{count['id']}/items/{line['id']}"
        ),
        json={
            "counted_quantity": "2",
            "product_unit_id":
                NON_BATCH_BOX_UNIT_ID,
        },
    )

    assert response.status_code == 200

    updated = response.get_json()["item"]

    line = next(
        item
        for item in updated["items"]
        if item["product"]["id"]
        == NON_BATCH_PRODUCT_ID
    )

    assert line["expected_quantity"] == "5.0000"
    assert line["counted_quantity"] == "20.0000"
    assert line["counted_unit_quantity"] == "2.0000"
    assert (
        line["counted_product_unit_id"]
        == NON_BATCH_BOX_UNIT_ID
    )
    assert line["counted_unit_code"] == "BOX"
    assert line["counted_unit_name"] == "Box"
    assert (
        line["counted_conversion_factor_to_base"]
        == "10.000000"
    )
    assert line["variance_quantity"] == "15.0000"

    persisted = db.session.get(
        StockCountItem,
        line["id"],
    )

    assert persisted is not None
    assert persisted.counted_quantity == Decimal(
        "20.0000"
    )
    assert persisted.counted_unit_quantity == Decimal(
        "2.0000"
    )
    assert (
        persisted.counted_product_unit_id
        == NON_BATCH_BOX_UNIT_ID
    )
    assert (
        persisted.counted_unit_code_snapshot
        == "BOX"
    )
    assert (
        persisted.counted_unit_name_snapshot
        == "Box"
    )
    assert (
        persisted.counted_conversion_factor_to_base
        == Decimal("10.000000")
    )
    assert persisted.variance_quantity == Decimal(
        "15.0000"
    )


def test_discovered_stock_count_item_converts_product_unit_quantity_to_base(
    client,
):
    create_response = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            count_mode="visible",
            idempotency_key=(
                "stock-count-product-unit-discovered"
            ),
        ),
    )

    assert create_response.status_code == 201

    count = create_response.get_json()["item"]

    response = client.post(
        (
            f"/api/inventory/stock-counts/"
            f"{count['id']}/items/discovered"
        ),
        json={
            "product_id":
                EMPTY_BATCH_PRODUCT_ID,
            "product_unit_id":
                EMPTY_BATCH_BOX_UNIT_ID,
            "counted_quantity": "2",
            "batch_number": "NEW-BOX-BATCH",
            "expiry_date": "2028-12-31",
        },
    )

    assert response.status_code == 201

    updated = response.get_json()["item"]

    line = next(
        item
        for item in updated["items"]
        if (
            item["product"]["id"]
            == EMPTY_BATCH_PRODUCT_ID
            and item["source_type"]
            == "discovered"
        )
    )

    assert line["expected_quantity"] == "0.0000"
    assert line["counted_quantity"] == "10.0000"
    assert line["counted_unit_quantity"] == "2.0000"
    assert (
        line["counted_product_unit_id"]
        == EMPTY_BATCH_BOX_UNIT_ID
    )
    assert line["counted_unit_code"] == "BOX"
    assert line["counted_unit_name"] == "Box"
    assert (
        line["counted_conversion_factor_to_base"]
        == "5.000000"
    )
    assert line["variance_quantity"] == "10.0000"

    persisted = StockCountItem.query.filter_by(
        stock_count_id=count["id"],
        product_id=EMPTY_BATCH_PRODUCT_ID,
        source_type="discovered",
    ).one()

    assert persisted.counted_quantity == Decimal(
        "10.0000"
    )
    assert persisted.counted_unit_quantity == Decimal(
        "2.0000"
    )
    assert (
        persisted.counted_product_unit_id
        == EMPTY_BATCH_BOX_UNIT_ID
    )
    assert (
        persisted.counted_unit_code_snapshot
        == "BOX"
    )
    assert (
        persisted.counted_unit_name_snapshot
        == "Box"
    )
    assert (
        persisted.counted_conversion_factor_to_base
        == Decimal("5.000000")
    )


def test_stock_count_item_rejects_product_unit_from_different_product(
    client,
):
    create_response = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            count_mode="visible",
            idempotency_key=(
                "stock-count-product-unit-mismatch"
            ),
        ),
    )

    assert create_response.status_code == 201

    count = create_response.get_json()["item"]

    line = next(
        item
        for item in count["items"]
        if item["product"]["id"]
        == NON_BATCH_PRODUCT_ID
    )

    response = client.put(
        (
            f"/api/inventory/stock-counts/"
            f"{count['id']}/items/{line['id']}"
        ),
        json={
            "counted_quantity": "2",
            "product_unit_id":
                EMPTY_BATCH_BOX_UNIT_ID,
        },
    )

    assert response.status_code == 400
    assert (
        "product_unit_id not found for this product"
        in error_message(response)
    )

def test_stock_count_base_quantity_entry_preserves_base_provenance(client):
    create_response = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            count_mode="visible",
            idempotency_key=(
                "stock-count-base-entry-provenance"
            ),
        ),
    )

    assert create_response.status_code == 201

    count = create_response.get_json()["item"]

    line = next(
        item
        for item in count["items"]
        if item["product"]["id"]
        == NON_BATCH_PRODUCT_ID
    )

    response = client.put(
        (
            f"/api/inventory/stock-counts/"
            f"{count['id']}/items/{line['id']}"
        ),
        json={
            "counted_quantity": "7",
        },
    )

    assert response.status_code == 200

    updated = response.get_json()["item"]

    serialized_line = next(
        item
        for item in updated["items"]
        if item["id"] == line["id"]
    )

    assert (
        serialized_line["counted_quantity"]
        == "7.0000"
    )
    assert (
        serialized_line["counted_unit_quantity"]
        == "7.0000"
    )
    assert (
        serialized_line["counted_product_unit_id"]
        is None
    )
    assert serialized_line["counted_unit_code"] is None
    assert serialized_line["counted_unit_name"] is None
    assert (
        serialized_line[
            "counted_conversion_factor_to_base"
        ]
        == "1.000000"
    )

    persisted = db.session.get(
        StockCountItem,
        line["id"],
    )

    assert persisted is not None
    assert persisted.counted_quantity == Decimal(
        "7.0000"
    )
    assert persisted.counted_unit_quantity == Decimal(
        "7.0000"
    )
    assert persisted.counted_product_unit_id is None
    assert persisted.counted_unit_code_snapshot is None
    assert persisted.counted_unit_name_snapshot is None
    assert (
        persisted.counted_conversion_factor_to_base
        == Decimal("1.000000")
    )


# ============================================================================
# Superseded Stock Count lifecycle
# ============================================================================


def _create_completed_count_for_supersede(client) -> str:
    created = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            count_mode="visible",
        ),
    )

    assert created.status_code == 201

    count_id = created.get_json()["item"]["id"]

    count = db.session.get(
        StockCount,
        count_id,
    )

    lines = (
        StockCountItem.query
        .filter_by(
            stock_count_id=count_id,
        )
        .order_by(
            StockCountItem.line_number.asc(),
        )
        .all()
    )

    for line in lines:
        line.counted_quantity = (
            line.expected_quantity
        )
        line.counted_unit_quantity = (
            line.expected_quantity
        )
        line.counted_conversion_factor_to_base = (
            Decimal("1.000000")
        )
        line.variance_quantity = Decimal("0.0000")
        line.counted_at = datetime.now(
            timezone.utc
        )
        line.counted_by = USER_ID

    count.status = "completed"
    count.completed_at = datetime.now(
        timezone.utc
    )
    count.completed_by = USER_ID

    db.session.commit()

    return count_id


def test_completed_unposted_stock_count_can_be_superseded(
    client,
):
    count_id = _create_completed_count_for_supersede(
        client
    )

    response = client.post(
        f"/api/inventory/stock-counts/{count_id}/supersede",
        json={
            "reason": (
                "Superseded by a newer physical recount."
            ),
        },
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["ok"] is True

    item = payload["item"]

    assert item["status"] == "superseded"
    assert item["superseded_at"] is not None
    assert item["superseded_by"]["id"] == USER_ID
    assert (
        item["superseded_reason"]
        == "Superseded by a newer physical recount."
    )
    assert item["adjustment"] is None

    persisted = db.session.get(
        StockCount,
        count_id,
    )

    assert persisted.status == "superseded"
    assert persisted.superseded_at is not None
    assert persisted.superseded_by == USER_ID
    assert (
        persisted.superseded_reason
        == "Superseded by a newer physical recount."
    )

    audit = AuditLog.query.filter_by(
        action="INVENTORY_COUNT_SUPERSEDED",
        entity_type="stock_count",
        entity_id=count_id,
    ).one()

    assert audit.module_code == "INVENTORY"
    assert audit.tenant_id == TENANT_ID
    assert audit.branch_id == BRANCH_ID
    assert audit.user_id == USER_ID
    assert audit.old_values == {
        "status": "completed",
    }
    assert audit.new_values == {
        "status": "superseded",
    }
    assert (
        audit.details["reason"]
        == "Superseded by a newer physical recount."
    )


def test_supersede_stock_count_requires_reason(
    client,
):
    count_id = _create_completed_count_for_supersede(
        client
    )

    response = client.post(
        f"/api/inventory/stock-counts/{count_id}/supersede",
        json={
            "reason": "   ",
        },
    )

    assert response.status_code == 400

    payload = response.get_json()

    assert payload["ok"] is False
    assert (
        "Supersede reason is required"
        in payload["error"]["message"]
    )

    persisted = db.session.get(
        StockCount,
        count_id,
    )

    assert persisted.status == "completed"
    assert persisted.superseded_at is None


def test_open_stock_count_cannot_be_superseded(
    client,
):
    created = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(),
    )

    assert created.status_code == 201

    count_id = created.get_json()["item"]["id"]

    response = client.post(
        f"/api/inventory/stock-counts/{count_id}/supersede",
        json={
            "reason": "Premature supersede attempt.",
        },
    )

    assert response.status_code == 409

    payload = response.get_json()

    assert payload["ok"] is False
    assert (
        "Only a completed Stock Count can be superseded"
        in payload["error"]["message"]
    )

    persisted = db.session.get(
        StockCount,
        count_id,
    )

    assert persisted.status == "open"


def test_adjusted_stock_count_cannot_be_superseded(
    client,
):
    count_id = _create_completed_count_for_supersede(
        client
    )

    now = datetime.now(
        timezone.utc
    )

    adjustment = StockAdjustment(
        tenant_id=TENANT_ID,
        branch_id=BRANCH_ID,
        warehouse_id=WAREHOUSE_ID,
        adjustment_number="SA-SUPERSEDE-TEST",
        reason_code="stock_count",
        reason="Existing posted adjustment",
        source_type="stock_count",
        source_id=count_id,
        status="posted",
        idempotency_key=(
            "supersede-existing-adjustment"
        ),
        request_fingerprint=(
            "supersede-existing-adjustment-fingerprint"
        ),
        posted_at=now,
        posted_by=USER_ID,
        created_at=now,
        updated_at=now,
    )

    db.session.add(adjustment)
    db.session.commit()

    response = client.post(
        f"/api/inventory/stock-counts/{count_id}/supersede",
        json={
            "reason": "Should not be allowed.",
        },
    )

    assert response.status_code == 409

    payload = response.get_json()

    assert payload["ok"] is False
    assert (
        "with an adjustment cannot be superseded"
        in payload["error"]["message"]
    )

    persisted = db.session.get(
        StockCount,
        count_id,
    )

    assert persisted.status == "completed"
    assert persisted.superseded_at is None


def test_superseded_lifecycle_filter_returns_only_superseded_counts(
    client,
):
    superseded_id = (
        _create_completed_count_for_supersede(
            client
        )
    )

    response = client.post(
        f"/api/inventory/stock-counts/{superseded_id}/supersede",
        json={
            "reason": "Lifecycle filter test.",
        },
    )

    assert response.status_code == 200

    filtered = client.get(
        "/api/inventory/stock-counts"
        "?lifecycle=superseded"
    )

    assert filtered.status_code == 200

    payload = filtered.get_json()

    assert payload["ok"] is True
    assert payload["pagination"]["total"] == 1
    assert len(payload["items"]) == 1
    assert (
        payload["items"][0]["id"]
        == superseded_id
    )
    assert (
        payload["items"][0]["status"]
        == "superseded"
    )
    assert (
        payload["items"][0]["superseded_reason"]
        == "Lifecycle filter test."
    )


# ============================================================================
# Stock Count recount lineage
# ============================================================================


def _superseded_count_for_recount(
    client,
) -> str:
    count_id = (
        _create_completed_count_for_supersede(
            client
        )
    )

    response = client.post(
        f"/api/inventory/stock-counts/{count_id}/supersede",
        json={
            "reason": (
                "Superseded before targeted recount."
            ),
        },
    )

    assert response.status_code == 200
    assert (
        response.get_json()["item"]["status"]
        == "superseded"
    )

    return count_id


def test_recount_can_be_created_from_superseded_stock_count(
    client,
):
    source_id = _superseded_count_for_recount(
        client
    )

    response = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            idempotency_key="recount-valid",
            product_ids=[
                NON_BATCH_PRODUCT_ID,
            ],
            count_mode="blind",
            recount_of_stock_count_id=(
                source_id
            ),
            notes=(
                "Targeted verification after "
                "superseded count."
            ),
        ),
    )

    assert response.status_code == 201

    item = response.get_json()["item"]

    assert item["status"] == "open"
    assert item["scope_type"] == "selected"
    assert item["count_mode"] == "blind"

    assert item["recount_of"] == {
        "id": source_id,
        "count_number": (
            db.session.get(
                StockCount,
                source_id,
            ).count_number
        ),
        "status": "superseded",
    }

    assert item["recounts"] == []

    assert len(item["scope_products"]) == 1
    assert (
        item["scope_products"][0]
        ["product"]["id"]
        == NON_BATCH_PRODUCT_ID
    )

    assert len(item["items"]) == 1
    assert (
        item["items"][0]
        ["product"]["id"]
        == NON_BATCH_PRODUCT_ID
    )

    # Blind-count secrecy remains intact.
    #
    # Open blind counts omit system quantity
    # fields entirely rather than exposing
    # them as null values.
    assert (
        "snapshot_quantity"
        not in item["items"][0]
    )
    assert (
        "expected_quantity"
        not in item["items"][0]
    )
    assert (
        "variance_quantity"
        not in item["items"][0]
    )

    persisted = db.session.get(
        StockCount,
        item["id"],
    )

    assert (
        persisted.recount_of_stock_count_id
        == source_id
    )

    audit = AuditLog.query.filter_by(
        action="INVENTORY_COUNT_STARTED",
        entity_type="stock_count",
        entity_id=item["id"],
    ).one()

    assert (
        audit.details[
            "recount_of_stock_count_id"
        ]
        == source_id
    )

    assert (
        audit.details[
            "recount_of_count_number"
        ]
        == item["recount_of"][
            "count_number"
        ]
    )

    source_response = client.get(
        f"/api/inventory/stock-counts/{source_id}"
    )

    assert source_response.status_code == 200

    source_item = (
        source_response
        .get_json()["item"]
    )

    assert len(source_item["recounts"]) == 1
    assert (
        source_item["recounts"][0]["id"]
        == item["id"]
    )
    assert (
        source_item["recounts"][0]
        ["count_number"]
        == item["count_number"]
    )
    assert (
        source_item["recounts"][0]["status"]
        == "open"
    )


def test_recount_requires_superseded_source(
    client,
):
    source_id = (
        _create_completed_count_for_supersede(
            client
        )
    )

    response = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            idempotency_key=(
                "recount-completed-source"
            ),
            product_ids=[
                NON_BATCH_PRODUCT_ID,
            ],
            count_mode="blind",
            recount_of_stock_count_id=(
                source_id
            ),
        ),
    )

    assert response.status_code == 409

    assert (
        "only be created from a superseded"
        in error_message(response).lower()
    )

    assert (
        StockCount.query
        .filter_by(
            recount_of_stock_count_id=source_id,
        )
        .count()
        == 0
    )


def test_recount_must_be_blind(
    client,
):
    source_id = _superseded_count_for_recount(
        client
    )

    response = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            idempotency_key=(
                "recount-visible-mode"
            ),
            product_ids=[
                NON_BATCH_PRODUCT_ID,
            ],
            count_mode="visible",
            recount_of_stock_count_id=(
                source_id
            ),
        ),
    )

    assert response.status_code == 400

    assert (
        "recounts must use blind count mode"
        in error_message(response).lower()
    )


def test_recount_requires_selected_products(
    client,
):
    source_id = _superseded_count_for_recount(
        client
    )

    response = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            idempotency_key=(
                "recount-full-warehouse"
            ),
            count_mode="blind",
            recount_of_stock_count_id=(
                source_id
            ),
        ),
    )

    assert response.status_code == 400

    assert (
        "require at least one selected product"
        in error_message(response).lower()
    )


def test_recount_rejects_product_not_in_source_count(
    client,
):
    source_id = _superseded_count_for_recount(
        client
    )

    response = client.post(
        "/api/inventory/stock-counts",
        json=stock_count_payload(
            idempotency_key=(
                "recount-invalid-product"
            ),
            product_ids=[
                ZERO_PRODUCT_ID,
            ],
            count_mode="blind",
            recount_of_stock_count_id=(
                source_id
            ),
        ),
    )

    assert response.status_code == 400

    assert (
        "recount products must exist "
        "in the source stock count"
        in error_message(response).lower()
    )

    assert (
        StockCount.query
        .filter_by(
            recount_of_stock_count_id=source_id,
        )
        .count()
        == 0
    )
