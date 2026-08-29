from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from flask import Flask
from sqlalchemy import func

from app.api.errors import register_error_handlers
from app.api.inventory import bp as inventory_bp
from app.extensions import db
from app.models import (
    Branch,
    InventoryBatch,
    InventoryMovement,
    Permission,
    Product,
    Role,
    RolePermission,
    StockAdjustment,
    StockAdjustmentItem,
    StockBalance,
    StockCount,
    StockCountItem,
    Tenant,
    User,
    UserRole,
    Warehouse,
)


TENANT_ID = "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa"
OTHER_TENANT_ID = "bbbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb"
BRANCH_ID = "cccccccc-cccc-4ccc-cccc-cccccccccccc"
OTHER_BRANCH_ID = "dddddddd-dddd-4ddd-dddd-dddddddddddd"
USER_ID = "eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee"
WAREHOUSE_ID = "11111111-1111-4111-8111-111111111111"
OTHER_BRANCH_WAREHOUSE_ID = "22222222-2222-4222-8222-222222222222"
NON_BATCH_PRODUCT_ID = "33333333-3333-4333-8333-333333333333"
BATCH_PRODUCT_ID = "44444444-4444-4444-8444-444444444444"
SERVICE_PRODUCT_ID = "55555555-5555-4555-8555-555555555555"
BATCH_ID = "66666666-6666-4666-8666-666666666666"
EXPIRED_BATCH_ID = "77777777-7777-4777-8777-777777777777"
STOCK_COUNT_ID = "88888888-8888-4888-8888-888888888888"
OPEN_STOCK_COUNT_ID = "99999999-9999-4999-8999-999999999999"


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
        Product.__table__.create(db.engine)
        Warehouse.__table__.create(db.engine)
        InventoryBatch.__table__.create(db.engine)
        StockBalance.__table__.create(db.engine)
        InventoryMovement.__table__.create(db.engine)
        StockCount.__table__.create(db.engine)
        StockCountItem.__table__.create(db.engine)
        StockAdjustment.__table__.create(db.engine)
        StockAdjustmentItem.__table__.create(db.engine)

        now = datetime.now(timezone.utc)
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
                    code="BR-1",
                    name="Branch 1",
                ),
                Branch(
                    id=OTHER_BRANCH_ID,
                    tenant_id=TENANT_ID,
                    code="BR-2",
                    name="Branch 2",
                ),
                User(
                    id=USER_ID,
                    tenant_id=TENANT_ID,
                    branch_id=BRANCH_ID,
                    first_name="Adjuster",
                    email="adjuster@example.test",
                    username="adjuster",
                    password_hash="hash",
                ),
                Warehouse(
                    id=WAREHOUSE_ID,
                    tenant_id=TENANT_ID,
                    branch_id=BRANCH_ID,
                    code="WH-1",
                    name="Main",
                ),
                Warehouse(
                    id=OTHER_BRANCH_WAREHOUSE_ID,
                    tenant_id=TENANT_ID,
                    branch_id=OTHER_BRANCH_ID,
                    code="WH-2",
                    name="Other Branch",
                ),
                Product(
                    id=NON_BATCH_PRODUCT_ID,
                    tenant_id=TENANT_ID,
                    internal_sku="NB-1",
                    name="Non Batch",
                    default_sale_price=Decimal("10.00"),
                    min_sale_price=Decimal("1.00"),
                    track_inventory=True,
                    track_batches=False,
                    track_expiry=False,
                    cost_price=Decimal("2.00"),
                ),
                Product(
                    id=BATCH_PRODUCT_ID,
                    tenant_id=TENANT_ID,
                    internal_sku="BT-1",
                    name="Batch Product",
                    default_sale_price=Decimal("10.00"),
                    min_sale_price=Decimal("1.00"),
                    track_inventory=True,
                    track_batches=True,
                    track_expiry=True,
                    cost_price=Decimal("3.00"),
                ),
                Product(
                    id=SERVICE_PRODUCT_ID,
                    tenant_id=TENANT_ID,
                    internal_sku="SV-1",
                    name="Service Product",
                    default_sale_price=Decimal("10.00"),
                    min_sale_price=Decimal("1.00"),
                    track_inventory=False,
                ),
                InventoryBatch(
                    id=BATCH_ID,
                    tenant_id=TENANT_ID,
                    warehouse_id=WAREHOUSE_ID,
                    product_id=BATCH_PRODUCT_ID,
                    batch_number="B-1",
                    expiry_date=date.today().replace(year=date.today().year + 1),
                    unit_cost=Decimal("3.00"),
                    quantity_on_hand=Decimal("8.0000"),
                    quantity_reserved=Decimal("2.0000"),
                    status="available",
                ),
                InventoryBatch(
                    id=EXPIRED_BATCH_ID,
                    tenant_id=TENANT_ID,
                    warehouse_id=WAREHOUSE_ID,
                    product_id=BATCH_PRODUCT_ID,
                    batch_number="EXP-1",
                    expiry_date=date.today().replace(year=date.today().year - 1),
                    unit_cost=Decimal("3.00"),
                    quantity_on_hand=Decimal("4.0000"),
                    quantity_reserved=Decimal("0.0000"),
                    status="available",
                ),
                StockBalance(
                    id="abababab-abab-4aba-abab-abababababab",
                    tenant_id=TENANT_ID,
                    branch_id=BRANCH_ID,
                    warehouse_id=WAREHOUSE_ID,
                    product_id=NON_BATCH_PRODUCT_ID,
                    quantity_on_hand=Decimal("10.0000"),
                    quantity_reserved=Decimal("3.0000"),
                    quantity_available=Decimal("7.0000"),
                    avg_unit_cost=Decimal("2.00"),
                ),
                StockBalance(
                    id="bcbcbcbc-bcbc-4bcb-bcbc-bcbcbcbcbcbc",
                    tenant_id=TENANT_ID,
                    branch_id=BRANCH_ID,
                    warehouse_id=WAREHOUSE_ID,
                    product_id=BATCH_PRODUCT_ID,
                    quantity_on_hand=Decimal("12.0000"),
                    quantity_reserved=Decimal("2.0000"),
                    quantity_available=Decimal("10.0000"),
                    avg_unit_cost=Decimal("3.00"),
                ),
                StockCount(
                    id=STOCK_COUNT_ID,
                    tenant_id=TENANT_ID,
                    branch_id=BRANCH_ID,
                    warehouse_id=WAREHOUSE_ID,
                    count_number="SC-2026-TEST",
                    idempotency_key="count-key",
                    request_fingerprint="count-fingerprint",
                    scope_type="full",
                    status="completed",
                    snapshot_at=now,
                    started_at=now,
                    started_by=USER_ID,
                    completed_at=now,
                    completed_by=USER_ID,
                    created_at=now,
                    updated_at=now,
                ),
                StockCount(
                    id=OPEN_STOCK_COUNT_ID,
                    tenant_id=TENANT_ID,
                    branch_id=BRANCH_ID,
                    warehouse_id=WAREHOUSE_ID,
                    count_number="SC-2026-OPEN",
                    idempotency_key="open-count-key",
                    request_fingerprint="open-count-fingerprint",
                    scope_type="full",
                    status="open",
                    snapshot_at=now,
                    started_at=now,
                    started_by=USER_ID,
                    created_at=now,
                    updated_at=now,
                ),
                StockCountItem(
                    id="cdcdcdcd-cdcd-4cdc-8dcd-cdcdcdcdcdcd",
                    stock_count_id=STOCK_COUNT_ID,
                    product_id=NON_BATCH_PRODUCT_ID,
                    line_number=1,
                    snapshot_quantity=Decimal("10.0000"),
                    expected_quantity=Decimal("10.0000"),
                    counted_quantity=Decimal("12.0000"),
                    variance_quantity=Decimal("2.0000"),
                    counted_at=now,
                    counted_by=USER_ID,
                    created_at=now,
                    updated_at=now,
                ),
                StockCountItem(
                    id="dededede-dede-4ded-8ede-dededededede",
                    stock_count_id=STOCK_COUNT_ID,
                    product_id=BATCH_PRODUCT_ID,
                    batch_id=BATCH_ID,
                    line_number=2,
                    snapshot_quantity=Decimal("8.0000"),
                    expected_quantity=Decimal("8.0000"),
                    counted_quantity=Decimal("7.0000"),
                    variance_quantity=Decimal("-1.0000"),
                    counted_at=now,
                    counted_by=USER_ID,
                    created_at=now,
                    updated_at=now,
                ),
                StockCountItem(
                    id="efefefef-efef-4efe-8fef-efefefefefef",
                    stock_count_id=STOCK_COUNT_ID,
                    product_id=BATCH_PRODUCT_ID,
                    batch_id=EXPIRED_BATCH_ID,
                    line_number=3,
                    snapshot_quantity=Decimal("4.0000"),
                    expected_quantity=Decimal("4.0000"),
                    counted_quantity=Decimal("4.0000"),
                    variance_quantity=Decimal("0.0000"),
                    counted_at=now,
                    counted_by=USER_ID,
                    created_at=now,
                    updated_at=now,
                ),
            ]
        )
        db.session.commit()

        yield app

        db.session.remove()
        StockAdjustmentItem.__table__.drop(db.engine)
        StockAdjustment.__table__.drop(db.engine)
        StockCountItem.__table__.drop(db.engine)
        StockCount.__table__.drop(db.engine)
        InventoryMovement.__table__.drop(db.engine)
        StockBalance.__table__.drop(db.engine)
        InventoryBatch.__table__.drop(db.engine)
        Warehouse.__table__.drop(db.engine)
        Product.__table__.drop(db.engine)
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
        "app.services.tenant.auth.decorators.authorization_service.authorize",
        lambda *args, **kwargs: None,
    )
    return app_context.test_client()


def manual_payload(**overrides):
    payload = {
        "warehouse_id": WAREHOUSE_ID,
        "idempotency_key": "manual-adjustment-key",
        "reason_code": "correction",
        "reason": "Shelf correction",
        "items": [
            {
                "product_id": NON_BATCH_PRODUCT_ID,
                "quantity_delta": "2",
            }
        ],
    }
    payload.update(overrides)
    return payload


def count_payload(**overrides):
    payload = {
        "idempotency_key": "count-adjustment-key",
        "reason_code": "stock_count",
    }
    payload.update(overrides)
    return payload


def test_stock_adjustment_routes_require_inventory_adjust_permission(
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
        "app.services.tenant.auth.decorators.authorization_service.authorize",
        lambda *args, **kwargs: captured.update(kwargs),
    )

    response = app_context.test_client().get("/api/inventory/stock-adjustments")

    assert response.status_code == 200
    assert captured["permission"] == "inventory.adjust"


def test_manual_positive_non_batch_adjustment_posts_stock_and_movement(client):
    response = client.post("/api/inventory/stock-adjustments", json=manual_payload())

    assert response.status_code == 201
    assert response.json["item"]["source"]["type"] == "manual"
    assert response.json["item"]["items"][0]["quantity_delta"] == "2.0000"

    stock = StockBalance.query.filter_by(product_id=NON_BATCH_PRODUCT_ID).one()
    assert stock.quantity_on_hand == Decimal("12.0000")
    assert stock.quantity_available == Decimal("9.0000")
    assert stock.avg_unit_cost == Decimal("2.00")

    movement = InventoryMovement.query.filter_by(
        movement_type="stock_adjustment",
        product_id=NON_BATCH_PRODUCT_ID,
    ).one()
    assert movement.quantity == Decimal("2.0000")
    assert movement.reference_type == "stock_adjustment"
    assert StockAdjustment.query.count() == 1
    assert StockAdjustmentItem.query.count() == 1


def test_manual_negative_adjustment_preserves_reserved_stock_safety(client):
    response = client.post(
        "/api/inventory/stock-adjustments",
        json=manual_payload(
            idempotency_key="too-negative",
            items=[
                {
                    "product_id": NON_BATCH_PRODUCT_ID,
                    "quantity_delta": "-8",
                }
            ],
        ),
    )

    assert response.status_code == 409
    stock = StockBalance.query.filter_by(product_id=NON_BATCH_PRODUCT_ID).one()
    assert stock.quantity_on_hand == Decimal("10.0000")
    assert InventoryMovement.query.count() == 0
    assert StockAdjustment.query.count() == 0


def test_manual_batch_adjustment_requires_exact_batch_and_allows_expired(client):
    response = client.post(
        "/api/inventory/stock-adjustments",
        json=manual_payload(
            idempotency_key="expired-batch",
            items=[
                {
                    "product_id": BATCH_PRODUCT_ID,
                    "batch_id": EXPIRED_BATCH_ID,
                    "quantity_delta": "1.5",
                }
            ],
        ),
    )

    assert response.status_code == 201
    batch = db.session.get(InventoryBatch, EXPIRED_BATCH_ID)
    stock = StockBalance.query.filter_by(product_id=BATCH_PRODUCT_ID).one()
    assert batch.quantity_on_hand == Decimal("5.5000")
    assert stock.quantity_on_hand == Decimal("13.5000")
    movement = InventoryMovement.query.filter_by(batch_id=EXPIRED_BATCH_ID).one()
    assert movement.quantity == Decimal("1.5000")


def test_manual_adjustment_rejects_wrong_batch_and_non_inventory_product(client):
    wrong_batch = client.post(
        "/api/inventory/stock-adjustments",
        json=manual_payload(
            idempotency_key="wrong-batch",
            items=[
                {
                    "product_id": NON_BATCH_PRODUCT_ID,
                    "batch_id": BATCH_ID,
                    "quantity_delta": "1",
                }
            ],
        ),
    )
    service_product = client.post(
        "/api/inventory/stock-adjustments",
        json=manual_payload(
            idempotency_key="service-product",
            items=[
                {
                    "product_id": SERVICE_PRODUCT_ID,
                    "quantity_delta": "1",
                }
            ],
        ),
    )

    assert wrong_batch.status_code == 400
    assert service_product.status_code == 400
    assert StockAdjustment.query.count() == 0


def test_idempotency_replay_does_not_double_post_and_changed_payload_conflicts(client):
    first = client.post("/api/inventory/stock-adjustments", json=manual_payload())
    replay = client.post("/api/inventory/stock-adjustments", json=manual_payload())
    changed = client.post(
        "/api/inventory/stock-adjustments",
        json=manual_payload(reason="Changed reason"),
    )

    assert first.status_code == 201
    assert replay.status_code == 201
    assert replay.json["item"]["id"] == first.json["item"]["id"]
    assert changed.status_code == 409
    assert InventoryMovement.query.count() == 1
    assert StockBalance.query.filter_by(product_id=NON_BATCH_PRODUCT_ID).one().quantity_on_hand == Decimal("12.0000")


def test_stock_count_adjustment_derives_nonzero_variances_and_preserves_count(client):
    before_count_items = [
        (
            item.id,
            item.snapshot_quantity,
            item.expected_quantity,
            item.counted_quantity,
            item.variance_quantity,
        )
        for item in StockCountItem.query.order_by(StockCountItem.line_number).all()
    ]

    response = client.post(
        f"/api/inventory/stock-counts/{STOCK_COUNT_ID}/adjust",
        json=count_payload(),
    )
    detail = client.get(f"/api/inventory/stock-counts/{STOCK_COUNT_ID}")

    assert response.status_code == 201
    assert detail.status_code == 200
    assert detail.json["item"]["adjustment"] == {
        "id": response.json["item"]["id"],
        "adjustment_number": response.json["item"]["adjustment_number"],
    }
    item_deltas = [
        item["quantity_delta"]
        for item in response.json["item"]["items"]
    ]
    assert item_deltas == ["2.0000", "-1.0000"]
    assert StockAdjustmentItem.query.count() == 2
    assert InventoryMovement.query.count() == 2
    assert StockBalance.query.filter_by(product_id=NON_BATCH_PRODUCT_ID).one().quantity_on_hand == Decimal("12.0000")
    assert db.session.get(InventoryBatch, BATCH_ID).quantity_on_hand == Decimal("7.0000")

    after_count_items = [
        (
            item.id,
            item.snapshot_quantity,
            item.expected_quantity,
            item.counted_quantity,
            item.variance_quantity,
        )
        for item in StockCountItem.query.order_by(StockCountItem.line_number).all()
    ]
    assert after_count_items == before_count_items


def test_stock_count_adjustment_rejects_duplicate_and_open_count(client):
    first = client.post(
        f"/api/inventory/stock-counts/{STOCK_COUNT_ID}/adjust",
        json=count_payload(),
    )
    duplicate = client.post(
        f"/api/inventory/stock-counts/{STOCK_COUNT_ID}/adjust",
        json=count_payload(idempotency_key="another-key"),
    )
    open_count = client.post(
        f"/api/inventory/stock-counts/{OPEN_STOCK_COUNT_ID}/adjust",
        json=count_payload(idempotency_key="open-key"),
    )

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert open_count.status_code == 409
    assert InventoryMovement.query.count() == 2


def test_stock_adjustment_list_and_detail_are_branch_scoped(client):
    created = client.post("/api/inventory/stock-adjustments", json=manual_payload())
    response = client.get("/api/inventory/stock-adjustments")
    detail = client.get(
        f"/api/inventory/stock-adjustments/{created.json['item']['id']}"
    )

    assert response.status_code == 200
    assert response.json["pagination"]["total"] == 1
    assert response.json["items"][0]["adjustment_number"].startswith("SA-")
    assert detail.status_code == 200
    assert detail.json["item"]["items"][0]["product"]["id"] == NON_BATCH_PRODUCT_ID


# ============================================================================
# Discovered Stock Count batch reconciliation
# ============================================================================


def _completed_discovered_count(
    *,
    count_id: str,
    count_number: str,
    items: list[dict],
) -> StockCount:
    now = datetime.now(timezone.utc)

    count = StockCount(
        id=count_id,
        tenant_id=TENANT_ID,
        branch_id=BRANCH_ID,
        warehouse_id=WAREHOUSE_ID,
        count_number=count_number,
        idempotency_key=f"{count_id}-key",
        request_fingerprint=f"{count_id}-fingerprint",
        scope_type="full",
        count_mode="blind",
        status="completed",
        snapshot_at=now,
        started_at=now,
        started_by=USER_ID,
        completed_at=now,
        completed_by=USER_ID,
        created_at=now,
        updated_at=now,
    )
    db.session.add(count)
    db.session.flush()

    for line_number, values in enumerate(
        items,
        start=1,
    ):
        counted = Decimal(
            str(values["counted_quantity"])
        )

        db.session.add(
            StockCountItem(
                id=values["id"],
                stock_count_id=str(count.id),
                product_id=BATCH_PRODUCT_ID,
                batch_id=None,
                source_type="discovered",
                observed_batch_number=values[
                    "batch_number"
                ],
                observed_expiry_date=values[
                    "expiry_date"
                ],
                line_number=line_number,
                snapshot_quantity=Decimal(
                    "0.0000"
                ),
                expected_quantity=Decimal(
                    "0.0000"
                ),
                counted_quantity=counted,
                variance_quantity=counted,
                counted_at=now,
                counted_by=USER_ID,
                created_at=now,
                updated_at=now,
            )
        )

    db.session.commit()
    return count


def test_stock_count_adjustment_creates_canonical_discovered_batch(
    client,
):
    count_id = (
        "10101010-1010-4010-8010-101010101010"
    )
    expiry = date.today().replace(
        year=date.today().year + 2
    )

    _completed_discovered_count(
        count_id=count_id,
        count_number="SC-DISCOVERED-NEW",
        items=[
            {
                "id": (
                    "11111111-aaaa-4111-8111-"
                    "111111111111"
                ),
                "batch_number": "FOUND-001",
                "expiry_date": expiry,
                "counted_quantity": "6",
            }
        ],
    )

    response = client.post(
        (
            f"/api/inventory/stock-counts/"
            f"{count_id}/adjust"
        ),
        json=count_payload(
            idempotency_key=(
                "discovered-new-batch"
            )
        ),
    )

    assert response.status_code == 201

    batch = InventoryBatch.query.filter_by(
        tenant_id=TENANT_ID,
        warehouse_id=WAREHOUSE_ID,
        product_id=BATCH_PRODUCT_ID,
        batch_number="FOUND-001",
    ).one()

    assert batch.expiry_date == expiry
    assert batch.unit_cost is None
    assert (
        batch.quantity_on_hand
        == Decimal("6.0000")
    )

    item = StockAdjustmentItem.query.filter_by(
        stock_count_item_id=(
            "11111111-aaaa-4111-8111-"
            "111111111111"
        )
    ).one()

    assert item.batch_id == batch.id

    movement = InventoryMovement.query.filter_by(
        reference_id=response.json["item"]["id"]
    ).one()

    assert movement.batch_id == batch.id
    assert movement.quantity == Decimal("6.0000")


def test_stock_count_adjustment_resolves_existing_discovered_batch(
    client,
):
    count_id = (
        "20202020-2020-4020-8020-202020202020"
    )
    existing = db.session.get(
        InventoryBatch,
        BATCH_ID,
    )

    _completed_discovered_count(
        count_id=count_id,
        count_number="SC-DISCOVERED-EXISTING",
        items=[
            {
                "id": (
                    "22222222-aaaa-4222-8222-"
                    "222222222222"
                ),
                # Case difference is intentional.
                "batch_number": "b-1",
                "expiry_date": (
                    existing.expiry_date
                ),
                "counted_quantity": "3",
            }
        ],
    )

    response = client.post(
        (
            f"/api/inventory/stock-counts/"
            f"{count_id}/adjust"
        ),
        json=count_payload(
            idempotency_key=(
                "discovered-existing-batch"
            )
        ),
    )

    assert response.status_code == 201

    refreshed = db.session.get(
        InventoryBatch,
        BATCH_ID,
    )
    assert (
        refreshed.quantity_on_hand
        == Decimal("11.0000")
    )

    assert (
        InventoryBatch.query.filter(
            InventoryBatch.product_id
            == BATCH_PRODUCT_ID,
            func.lower(
                InventoryBatch.batch_number
            )
            == "b-1",
        ).count()
        == 1
    )


def test_stock_count_adjustment_rejects_discovered_expiry_conflict(
    client,
):
    count_id = (
        "30303030-3030-4030-8030-303030303030"
    )
    existing = db.session.get(
        InventoryBatch,
        BATCH_ID,
    )

    conflicting_expiry = existing.expiry_date.replace(
        year=existing.expiry_date.year + 1
    )

    _completed_discovered_count(
        count_id=count_id,
        count_number="SC-DISCOVERED-CONFLICT",
        items=[
            {
                "id": (
                    "33333333-aaaa-4333-8333-"
                    "333333333333"
                ),
                "batch_number": "B-1",
                "expiry_date": conflicting_expiry,
                "counted_quantity": "2",
            }
        ],
    )

    before_quantity = (
        existing.quantity_on_hand
    )
    before_batch_count = (
        InventoryBatch.query.count()
    )

    response = client.post(
        (
            f"/api/inventory/stock-counts/"
            f"{count_id}/adjust"
        ),
        json=count_payload(
            idempotency_key=(
                "discovered-expiry-conflict"
            )
        ),
    )

    assert response.status_code == 409

    payload = response.get_json()
    assert payload["ok"] is False
    assert payload["error"]["code"] == "CONFLICT"
    assert (
        "expiry" in
        payload["error"]["message"].lower()
    )

    assert StockAdjustment.query.filter_by(
        source_type="stock_count",
        source_id=count_id,
    ).count() == 0

    assert (
        InventoryBatch.query.count()
        == before_batch_count
    )
    assert (
        db.session.get(
            InventoryBatch,
            BATCH_ID,
        ).quantity_on_hand
        == before_quantity
    )


def test_stock_count_adjustment_posts_multiple_discovered_batches(
    client,
):
    count_id = (
        "40404040-4040-4040-8040-404040404040"
    )

    _completed_discovered_count(
        count_id=count_id,
        count_number="SC-DISCOVERED-MULTI",
        items=[
            {
                "id": (
                    "44444444-aaaa-4444-8444-"
                    "444444444441"
                ),
                "batch_number": "FOUND-X",
                "expiry_date": date(
                    2027,
                    5,
                    31,
                ),
                "counted_quantity": "100",
            },
            {
                "id": (
                    "44444444-aaaa-4444-8444-"
                    "444444444442"
                ),
                "batch_number": "FOUND-Y",
                "expiry_date": date(
                    2028,
                    6,
                    30,
                ),
                "counted_quantity": "50",
            },
            {
                "id": (
                    "44444444-aaaa-4444-8444-"
                    "444444444443"
                ),
                "batch_number": "FOUND-Z",
                "expiry_date": date(
                    2029,
                    1,
                    31,
                ),
                "counted_quantity": "50",
            },
        ],
    )

    response = client.post(
        (
            f"/api/inventory/stock-counts/"
            f"{count_id}/adjust"
        ),
        json=count_payload(
            idempotency_key=(
                "discovered-multiple-batches"
            )
        ),
    )

    assert response.status_code == 201

    batches = (
        InventoryBatch.query
        .filter(
            InventoryBatch.product_id
            == BATCH_PRODUCT_ID,
            InventoryBatch.batch_number.in_(
                [
                    "FOUND-X",
                    "FOUND-Y",
                    "FOUND-Z",
                ]
            ),
        )
        .order_by(
            InventoryBatch.batch_number.asc()
        )
        .all()
    )

    assert [
        batch.batch_number
        for batch in batches
    ] == [
        "FOUND-X",
        "FOUND-Y",
        "FOUND-Z",
    ]

    assert [
        batch.quantity_on_hand
        for batch in batches
    ] == [
        Decimal("100.0000"),
        Decimal("50.0000"),
        Decimal("50.0000"),
    ]

    adjustment_items = (
        StockAdjustmentItem.query
        .filter_by(
            stock_adjustment_id=(
                response.json["item"]["id"]
            )
        )
        .all()
    )

    assert len(adjustment_items) == 3
    assert all(
        item.batch_id
        for item in adjustment_items
    )
