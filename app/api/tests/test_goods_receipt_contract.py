from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from flask import Flask

from app.api.errors import register_error_handlers
from app.api.inventory import bp as inventory_bp
from app.extensions import db
from app.models import (
    Branch,
    GoodsReceipt,
    GoodsReceiptItem,
    InventoryBatch,
    InventoryMovement,
    Product,
    ProductUnit,
    StockBalance,
    Supplier,
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
SUPPLIER_ID = "supplier-a"
PRODUCT_ID = "product-a"
SECOND_PRODUCT_ID = "product-b"
NON_INVENTORY_PRODUCT_ID = "product-service"
BASE_UNIT_ID = "unit-tablet"
PACK_UNIT_ID = "unit-box"
PACK_PRODUCT_UNIT_ID = "product-a-box"


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
        UnitOfMeasure.__table__.create(db.engine)
        Product.__table__.create(db.engine)
        ProductUnit.__table__.create(db.engine)
        Supplier.__table__.create(db.engine)
        Warehouse.__table__.create(db.engine)
        InventoryBatch.__table__.create(db.engine)
        StockBalance.__table__.create(db.engine)
        InventoryMovement.__table__.create(db.engine)
        GoodsReceipt.__table__.create(db.engine)
        GoodsReceiptItem.__table__.create(db.engine)
        seed_data()

        yield app

        db.session.remove()
        GoodsReceiptItem.__table__.drop(db.engine)
        GoodsReceipt.__table__.drop(db.engine)
        InventoryMovement.__table__.drop(db.engine)
        StockBalance.__table__.drop(db.engine)
        InventoryBatch.__table__.drop(db.engine)
        Warehouse.__table__.drop(db.engine)
        Supplier.__table__.drop(db.engine)
        ProductUnit.__table__.drop(db.engine)
        Product.__table__.drop(db.engine)
        UnitOfMeasure.__table__.drop(db.engine)
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
                first_name="Receiving",
                last_name="User",
                email="receiver@example.test",
                username="receiver",
                password_hash="hash",
            ),
            Product(
                id=PRODUCT_ID,
                tenant_id=TENANT_ID,
                internal_sku="AMOX-500",
                name="Amoxicillin 500mg",
                track_inventory=True,
                track_batches=True,
                track_expiry=True,
                is_active=True,
            ),
            UnitOfMeasure(
                id=BASE_UNIT_ID,
                tenant_id=TENANT_ID,
                code="TAB",
                name="Tablet",
                base_factor=Decimal("1.000000"),
            ),
            UnitOfMeasure(
                id=PACK_UNIT_ID,
                tenant_id=TENANT_ID,
                code="BOX",
                name="Box",
                base_factor=Decimal("1.000000"),
            ),
            ProductUnit(
                id=PACK_PRODUCT_UNIT_ID,
                tenant_id=TENANT_ID,
                product_id=PRODUCT_ID,
                unit_id=PACK_UNIT_ID,
                conversion_factor_to_base=Decimal("10.000000"),
                is_base=False,
                can_sell=True,
                can_receive=True,
                is_active=True,
            ),
            Product(
                id=SECOND_PRODUCT_ID,
                tenant_id=TENANT_ID,
                internal_sku="ORS-001",
                name="ORS Sachet",
                track_inventory=True,
                track_batches=False,
                track_expiry=False,
                is_active=True,
            ),
            Product(
                id=NON_INVENTORY_PRODUCT_ID,
                tenant_id=TENANT_ID,
                internal_sku="SVC-001",
                name="Service Fee",
                track_inventory=False,
                is_active=True,
            ),
            Product(
                id="inactive-product",
                tenant_id=TENANT_ID,
                internal_sku="OLD-001",
                name="Inactive Product",
                track_inventory=True,
                is_active=False,
            ),
            Product(
                id="other-tenant-product",
                tenant_id=OTHER_TENANT_ID,
                internal_sku="OTHER",
                name="Other Tenant Product",
            ),
            Supplier(
                id=SUPPLIER_ID,
                tenant_id=TENANT_ID,
                supplier_code="SUP-A",
                name="Supplier A",
                is_active=True,
            ),
            Supplier(
                id="inactive-supplier",
                tenant_id=TENANT_ID,
                supplier_code="SUP-OLD",
                name="Inactive Supplier",
                is_active=False,
            ),
            Supplier(
                id="other-tenant-supplier",
                tenant_id=OTHER_TENANT_ID,
                supplier_code="SUP-B",
                name="Other Supplier",
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
        ]
    )
    db.session.commit()


def payload(**overrides):
    base = {
        "warehouse_id": WAREHOUSE_ID,
        "supplier_id": SUPPLIER_ID,
        "supplier_reference": "DN-100",
        "idempotency_key": "receipt-key-1",
        "received_at": "2026-08-09T10:00:00+00:00",
        "notes": "Delivery note checked.",
        "items": [
            {
                "product_id": PRODUCT_ID,
                "quantity": "10",
                "batch_number": "BATCH-1",
                "manufacture_date": "2026-01-01",
                "expiry_date": "2027-01-31",
                "unit_cost": "5.50",
                "supplier_batch_reference": "SUP-B1",
            }
        ],
    }
    base.update(overrides)
    return base


def make_history_receipt(
    *,
    receipt_id: str,
    receipt_number: str,
    received_at: datetime,
    tenant_id: str = TENANT_ID,
    branch_id: str = BRANCH_ID,
    warehouse_id: str = WAREHOUSE_ID,
    supplier_id: str | None = SUPPLIER_ID,
    supplier_reference: str | None = "DN-HIST",
    received_by: str = USER_ID,
    line_count: int = 1,
):
    receipt = GoodsReceipt(
        id=receipt_id,
        tenant_id=tenant_id,
        branch_id=branch_id,
        warehouse_id=warehouse_id,
        supplier_id=supplier_id,
        receipt_number=receipt_number,
        supplier_reference=supplier_reference,
        idempotency_key=f"{receipt_id}-key",
        request_fingerprint=f"{receipt_id}-fingerprint",
        received_at=received_at,
        status="received",
        received_by=received_by,
        created_at=received_at,
        updated_at=received_at,
    )
    db.session.add(receipt)
    db.session.flush()

    db.session.add(
        GoodsReceiptItem(
            id=f"{receipt_id}-item-1",
            goods_receipt_id=receipt_id,
            product_id=PRODUCT_ID if tenant_id == TENANT_ID else "other-tenant-product",
            line_number=1,
            quantity=Decimal("10.0000"),
            batch_number=f"{receipt_id}-batch",
            expiry_date=date(2027, 1, 31),
            unit_cost=Decimal("5.50"),
            created_at=received_at,
            updated_at=received_at,
        )
    )

    if line_count > 1:
        db.session.add(
            GoodsReceiptItem(
                id=f"{receipt_id}-item-2",
                goods_receipt_id=receipt_id,
                product_id=SECOND_PRODUCT_ID,
                line_number=2,
                quantity=Decimal("3.0000"),
                unit_cost=Decimal("1.50"),
                created_at=received_at,
                updated_at=received_at,
            )
        )

    db.session.commit()
    return receipt


def error_message(response) -> str:
    error = response.get_json()["error"]
    if isinstance(error, dict):
        return error["message"]
    return error


def test_goods_receipt_create_persists_inventory_truth(client):
    response = client.post("/api/inventory/goods-receipts", json=payload())

    assert response.status_code == 201
    item = response.get_json()["item"]
    assert item["receipt_number"].startswith("GRN-2026-")
    assert item["status"] == "received"
    assert item["warehouse"] == {
        "id": WAREHOUSE_ID,
        "code": "MAIN",
        "name": "Main Warehouse",
    }
    assert item["supplier"] == {
        "id": SUPPLIER_ID,
        "supplier_code": "SUP-A",
        "name": "Supplier A",
    }
    assert item["items"][0]["quantity"] == "10.0000"
    assert item["items"][0]["unit_cost"] == "5.50"

    receipt = GoodsReceipt.query.one()
    receipt_item = GoodsReceiptItem.query.one()
    stock = StockBalance.query.one()
    batch = InventoryBatch.query.one()
    movement = InventoryMovement.query.one()

    assert receipt.tenant_id == TENANT_ID
    assert receipt.branch_id == BRANCH_ID
    assert receipt.received_by == USER_ID
    assert receipt_item.goods_receipt_id == receipt.id
    assert stock.quantity_on_hand == Decimal("10.0000")
    assert stock.quantity_available == Decimal("10.0000")
    assert stock.quantity_reserved == Decimal("0.0000")
    assert stock.avg_unit_cost == Decimal("5.50")
    assert batch.quantity_on_hand == Decimal("10.0000")
    assert batch.batch_number == "BATCH-1"
    assert batch.expiry_date == date(2027, 1, 31)
    assert movement.quantity == Decimal("10.0000")
    assert movement.movement_type == "goods_receipt"
    assert movement.reference_type == "goods_receipt"
    assert movement.reference_id == receipt.id
    assert movement.batch_id == batch.id


def test_goods_receipt_converts_product_unit_receipt_to_base_stock(client):
    response = client.post(
        "/api/inventory/goods-receipts",
        json=payload(
            idempotency_key="receipt-key-box",
            items=[
                {
                    "product_id": PRODUCT_ID,
                    "product_unit_id": PACK_PRODUCT_UNIT_ID,
                    "quantity": "2",
                    "batch_number": "BOX-BATCH-1",
                    "manufacture_date": "2026-01-01",
                    "expiry_date": "2027-01-31",
                    "unit_cost": "50.00",
                }
            ],
        ),
    )

    assert response.status_code == 201
    line = response.get_json()["item"]["items"][0]
    assert line["quantity"] == "2.0000"
    assert line["base_quantity"] == "20.0000"
    assert line["product_unit_id"] == PACK_PRODUCT_UNIT_ID
    assert line["unit_code"] == "BOX"
    assert line["conversion_factor_to_base"] == "10.000000"
    assert line["unit_cost"] == "50.00"
    assert line["base_unit_cost"] == "5.00"

    receipt_item = GoodsReceiptItem.query.one()
    stock = StockBalance.query.one()
    batch = InventoryBatch.query.one()
    movement = InventoryMovement.query.one()

    assert receipt_item.quantity == Decimal("2.0000")
    assert receipt_item.base_quantity == Decimal("20.0000")
    assert stock.quantity_on_hand == Decimal("20.0000")
    assert stock.avg_unit_cost == Decimal("5.00")
    assert batch.quantity_on_hand == Decimal("20.0000")
    assert batch.unit_cost == Decimal("5.00")
    assert movement.quantity == Decimal("20.0000")
    assert movement.unit_cost == Decimal("5.00")


def test_goods_receipt_requires_inventory_receive_permission(
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
        "/api/inventory/goods-receipts",
        json=payload(),
    )

    assert response.status_code == 403
    assert captured["kwargs"]["permission"] == "inventory.receive"
    assert GoodsReceipt.query.count() == 0


@pytest.mark.parametrize(
    ("override", "expected"),
    [
        ({"warehouse_id": OTHER_BRANCH_WAREHOUSE_ID}, "warehouse_id"),
        ({"warehouse_id": OTHER_TENANT_WAREHOUSE_ID}, "warehouse_id"),
        ({"supplier_id": "other-tenant-supplier"}, "supplier_id"),
        (
            {
                "items": [
                    {
                        "product_id": "other-tenant-product",
                        "quantity": "1",
                        "unit_cost": "1.00",
                    }
                ]
            },
            "products",
        ),
    ],
)
def test_goods_receipt_rejects_cross_scope_inputs(client, override, expected):
    response = client.post(
        "/api/inventory/goods-receipts",
        json=payload(**override),
    )

    assert response.status_code == 400
    assert expected in error_message(response)
    assert GoodsReceipt.query.count() == 0


@pytest.mark.parametrize(
    ("line_override", "expected"),
    [
        ({"quantity": "0"}, "quantity"),
        ({"quantity": "-1"}, "quantity"),
        ({"quantity": "abc"}, "quantity"),
        ({"unit_cost": "-1"}, "unit_cost"),
        ({"unit_cost": "abc"}, "unit_cost"),
    ],
)
def test_goods_receipt_validates_quantity_and_cost(client, line_override, expected):
    line = {
        "product_id": PRODUCT_ID,
        "quantity": "10",
        "batch_number": "BATCH-1",
        "expiry_date": "2027-01-31",
        "unit_cost": "5.50",
        **line_override,
    }

    response = client.post(
        "/api/inventory/goods-receipts",
        json=payload(items=[line]),
    )

    assert response.status_code == 400
    assert expected in error_message(response)
    assert GoodsReceipt.query.count() == 0


def test_goods_receipt_rejects_non_inventory_and_inactive_products(client):
    response = client.post(
        "/api/inventory/goods-receipts",
        json=payload(
            items=[
                {
                    "product_id": NON_INVENTORY_PRODUCT_ID,
                    "quantity": "1",
                    "unit_cost": "1.00",
                }
            ]
        ),
    )

    assert response.status_code == 400
    assert "inventory-tracked" in error_message(response)

    response = client.post(
        "/api/inventory/goods-receipts",
        json=payload(
            idempotency_key="receipt-key-inactive",
            items=[
                {
                    "product_id": "inactive-product",
                    "quantity": "1",
                    "unit_cost": "1.00",
                }
            ],
        ),
    )

    assert response.status_code == 400
    assert "active" in error_message(response)
    assert GoodsReceipt.query.count() == 0


def test_goods_receipt_enforces_batch_and_expiry_policy(client):
    response = client.post(
        "/api/inventory/goods-receipts",
        json=payload(
            items=[
                {
                    "product_id": PRODUCT_ID,
                    "quantity": "1",
                    "unit_cost": "1.00",
                }
            ]
        ),
    )

    assert response.status_code == 400
    assert "batch_number" in error_message(response)

    response = client.post(
        "/api/inventory/goods-receipts",
        json=payload(
            idempotency_key="receipt-key-expiry",
            items=[
                {
                    "product_id": PRODUCT_ID,
                    "quantity": "1",
                    "batch_number": "BATCH-1",
                    "unit_cost": "1.00",
                }
            ],
        ),
    )

    assert response.status_code == 400
    assert "expiry_date" in error_message(response)

    response = client.post(
        "/api/inventory/goods-receipts",
        json=payload(
            idempotency_key="receipt-key-expired",
            items=[
                {
                    "product_id": PRODUCT_ID,
                    "quantity": "1",
                    "batch_number": "BATCH-1",
                    "expiry_date": "2026-08-08",
                    "unit_cost": "1.00",
                }
            ],
        ),
    )

    assert response.status_code == 400
    assert "Expired" in error_message(response)
    assert GoodsReceipt.query.count() == 0


def test_goods_receipt_rejects_inactive_supplier(client):
    response = client.post(
        "/api/inventory/goods-receipts",
        json=payload(supplier_id="inactive-supplier"),
    )

    assert response.status_code == 400
    assert "active supplier" in error_message(response)
    assert GoodsReceipt.query.count() == 0


def test_goods_receipt_increments_existing_batch_and_weighted_average_cost(client):
    first = client.post(
        "/api/inventory/goods-receipts",
        json=payload(
            idempotency_key="first",
            items=[
                {
                    "product_id": PRODUCT_ID,
                    "quantity": "10",
                    "batch_number": "BATCH-1",
                    "manufacture_date": "2026-01-01",
                    "expiry_date": "2027-01-31",
                    "unit_cost": "2.00",
                }
            ],
        ),
    )
    second = client.post(
        "/api/inventory/goods-receipts",
        json=payload(
            idempotency_key="second",
            items=[
                {
                    "product_id": PRODUCT_ID,
                    "quantity": "10",
                    "batch_number": "BATCH-1",
                    "manufacture_date": "2026-01-01",
                    "expiry_date": "2027-01-31",
                    "unit_cost": "2.00",
                }
            ],
        ),
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert GoodsReceipt.query.count() == 2
    assert GoodsReceiptItem.query.count() == 2
    assert InventoryMovement.query.count() == 2
    assert InventoryBatch.query.count() == 1
    assert StockBalance.query.one().quantity_on_hand == Decimal("20.0000")
    assert StockBalance.query.one().avg_unit_cost == Decimal("2.00")
    assert InventoryBatch.query.one().quantity_on_hand == Decimal("20.0000")


def test_goods_receipt_rejects_existing_batch_metadata_conflict(client):
    assert client.post("/api/inventory/goods-receipts", json=payload()).status_code == 201

    response = client.post(
        "/api/inventory/goods-receipts",
        json=payload(
            idempotency_key="conflict-key",
            items=[
                {
                    "product_id": PRODUCT_ID,
                    "quantity": "1",
                    "batch_number": "BATCH-1",
                    "manufacture_date": "2026-01-01",
                    "expiry_date": "2028-01-31",
                    "unit_cost": "5.50",
                }
            ],
        ),
    )

    assert response.status_code == 409
    assert "conflicting expiry" in error_message(response)
    assert GoodsReceipt.query.count() == 1
    assert StockBalance.query.one().quantity_on_hand == Decimal("10.0000")


def test_goods_receipt_rejects_duplicate_product_batch_lines(client):
    line = {
        "product_id": PRODUCT_ID,
        "quantity": "1",
        "batch_number": "BATCH-1",
        "expiry_date": "2027-01-31",
        "unit_cost": "1.00",
    }

    response = client.post(
        "/api/inventory/goods-receipts",
        json=payload(items=[line, line]),
    )

    assert response.status_code == 400
    assert "Duplicate" in error_message(response)
    assert GoodsReceipt.query.count() == 0


def test_goods_receipt_supports_multiple_products(client):
    response = client.post(
        "/api/inventory/goods-receipts",
        json=payload(
            items=[
                {
                    "product_id": PRODUCT_ID,
                    "quantity": "2",
                    "batch_number": "BATCH-1",
                    "manufacture_date": "2026-01-01",
                    "expiry_date": "2027-01-31",
                    "unit_cost": "5.00",
                },
                {
                    "product_id": SECOND_PRODUCT_ID,
                    "quantity": "3",
                    "unit_cost": "1.50",
                },
            ],
        ),
    )

    assert response.status_code == 201
    assert GoodsReceiptItem.query.count() == 2
    assert StockBalance.query.count() == 2
    assert InventoryBatch.query.count() == 1
    assert InventoryMovement.query.count() == 2


def test_goods_receipt_idempotency_replays_same_request_without_double_stock(client):
    first = client.post("/api/inventory/goods-receipts", json=payload())
    second = client.post("/api/inventory/goods-receipts", json=payload())

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.get_json()["item"]["id"] == second.get_json()["item"]["id"]
    assert GoodsReceipt.query.count() == 1
    assert GoodsReceiptItem.query.count() == 1
    assert InventoryMovement.query.count() == 1
    assert StockBalance.query.one().quantity_on_hand == Decimal("10.0000")


def test_goods_receipt_idempotency_rejects_conflicting_payload(client):
    assert client.post("/api/inventory/goods-receipts", json=payload()).status_code == 201

    response = client.post(
        "/api/inventory/goods-receipts",
        json=payload(
            items=[
                {
                    "product_id": PRODUCT_ID,
                    "quantity": "11",
                    "batch_number": "BATCH-1",
                    "manufacture_date": "2026-01-01",
                    "expiry_date": "2027-01-31",
                    "unit_cost": "5.50",
                }
            ],
        ),
    )

    assert response.status_code == 409
    assert "idempotency_key" in error_message(response)
    assert StockBalance.query.one().quantity_on_hand == Decimal("10.0000")


def test_goods_receipt_rolls_back_on_downstream_failure(client, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("forced downstream failure")

    monkeypatch.setattr(
        "app.services.tenant.inventory.goods_receipt_service.GoodsReceiptService._apply_stock_balance_receipt",
        fail,
    )

    response = client.post("/api/inventory/goods-receipts", json=payload())

    assert response.status_code == 500
    assert GoodsReceipt.query.count() == 0
    assert GoodsReceiptItem.query.count() == 0
    assert StockBalance.query.count() == 0
    assert InventoryBatch.query.count() == 0
    assert InventoryMovement.query.count() == 0


def test_goods_receipt_detail_readback_requires_receive_permission(client):
    created = client.post("/api/inventory/goods-receipts", json=payload())
    receipt_id = created.get_json()["item"]["id"]

    response = client.get(f"/api/inventory/goods-receipts/{receipt_id}")

    assert response.status_code == 200
    assert response.get_json()["item"]["id"] == receipt_id
    assert response.get_json()["item"]["items"][0]["unit_cost"] == "5.50"


def test_goods_receipt_history_requires_receive_permission(
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

    response = app_context.test_client().get("/api/inventory/goods-receipts")

    assert response.status_code == 403
    assert captured["kwargs"]["permission"] == "inventory.receive"


def test_goods_receipt_history_is_branch_and_tenant_scoped(client):
    make_history_receipt(
        receipt_id="receipt-current",
        receipt_number="GRN-CURRENT",
        received_at=datetime(2026, 8, 10, 10, 0, 0),
    )
    make_history_receipt(
        receipt_id="receipt-other-branch",
        receipt_number="GRN-OTHER-BRANCH",
        received_at=datetime(2026, 8, 11, 10, 0, 0),
        branch_id=OTHER_BRANCH_ID,
        warehouse_id=OTHER_BRANCH_WAREHOUSE_ID,
    )
    make_history_receipt(
        receipt_id="receipt-other-tenant",
        receipt_number="GRN-OTHER-TENANT",
        received_at=datetime(2026, 8, 12, 10, 0, 0),
        tenant_id=OTHER_TENANT_ID,
        branch_id=OTHER_BRANCH_ID,
        warehouse_id=OTHER_TENANT_WAREHOUSE_ID,
        supplier_id="other-tenant-supplier",
    )

    response = client.get("/api/inventory/goods-receipts")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["pagination"]["total"] == 1
    assert [item["id"] for item in payload["items"]] == ["receipt-current"]


def test_goods_receipt_history_projection_is_summary_only(client):
    make_history_receipt(
        receipt_id="receipt-summary",
        receipt_number="GRN-SUMMARY",
        received_at=datetime(2026, 8, 10, 10, 0, 0),
        line_count=2,
    )

    response = client.get("/api/inventory/goods-receipts")

    assert response.status_code == 200
    item = response.get_json()["items"][0]
    assert item["receipt_number"] == "GRN-SUMMARY"
    assert item["warehouse"] == {
        "id": WAREHOUSE_ID,
        "code": "MAIN",
        "name": "Main Warehouse",
    }
    assert item["supplier"] == {
        "id": SUPPLIER_ID,
        "supplier_code": "SUP-A",
        "name": "Supplier A",
    }
    assert item["supplier_reference"] == "DN-HIST"
    assert item["item_count"] == 2
    assert item["total_cost"] == "59.50"
    assert item["received_by"] == {
        "id": USER_ID,
        "name": "Receiving User",
        "username": "receiver",
    }
    assert item["status"] == "received"
    assert "items" not in item
    assert "notes" not in item
    assert "idempotency_key" not in item


def test_goods_receipt_history_supports_null_supplier(client):
    make_history_receipt(
        receipt_id="receipt-no-supplier",
        receipt_number="GRN-NO-SUPPLIER",
        received_at=datetime(2026, 8, 10, 10, 0, 0),
        supplier_id=None,
        supplier_reference=None,
    )

    response = client.get("/api/inventory/goods-receipts")

    assert response.status_code == 200
    item = response.get_json()["items"][0]
    assert item["supplier"] is None
    assert item["supplier_reference"] is None


def test_goods_receipt_history_paginates_and_orders_newest_first(client):
    make_history_receipt(
        receipt_id="receipt-old",
        receipt_number="GRN-OLD",
        received_at=datetime(2026, 8, 9, 10, 0, 0),
    )
    make_history_receipt(
        receipt_id="receipt-new-b",
        receipt_number="GRN-NEW-B",
        received_at=datetime(2026, 8, 10, 10, 0, 0),
    )
    make_history_receipt(
        receipt_id="receipt-new-a",
        receipt_number="GRN-NEW-A",
        received_at=datetime(2026, 8, 10, 10, 0, 0),
    )

    response = client.get("/api/inventory/goods-receipts?page=1&per_page=2")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["pagination"] == {
        "page": 1,
        "per_page": 2,
        "total": 3,
        "pages": 2,
        "has_prev": False,
        "has_next": True,
    }
    assert [item["id"] for item in payload["items"]] == [
        "receipt-new-b",
        "receipt-new-a",
    ]


@pytest.mark.parametrize(
    ("query", "expected_id"),
    [
        ("GRN-SEARCH", "receipt-search-number"),
        ("EXT-REF-22", "receipt-search-reference"),
        ("Supplier A", "receipt-search-supplier-name"),
        ("SUP-A", "receipt-search-supplier-code"),
    ],
)
def test_goods_receipt_history_searches_safe_fields(client, query, expected_id):
    make_history_receipt(
        receipt_id="receipt-search-number",
        receipt_number="GRN-SEARCH",
        received_at=datetime(2026, 8, 10, 10, 0, 0),
        supplier_reference="NO-MATCH-1",
        supplier_id=None,
    )
    make_history_receipt(
        receipt_id="receipt-search-reference",
        receipt_number="GRN-REF",
        received_at=datetime(2026, 8, 9, 10, 0, 0),
        supplier_reference="EXT-REF-22",
        supplier_id=None,
    )
    make_history_receipt(
        receipt_id="receipt-search-supplier-name",
        receipt_number="GRN-SUPPLIER-NAME",
        received_at=datetime(2026, 8, 8, 10, 0, 0),
        supplier_reference="NO-MATCH-2",
    )
    make_history_receipt(
        receipt_id="receipt-search-supplier-code",
        receipt_number="GRN-SUPPLIER-CODE",
        received_at=datetime(2026, 8, 7, 10, 0, 0),
        supplier_reference="NO-MATCH-3",
    )

    response = client.get(f"/api/inventory/goods-receipts?search={query}")

    assert response.status_code == 200
    ids = [item["id"] for item in response.get_json()["items"]]
    assert expected_id in ids


def test_goods_receipt_history_filters_by_inclusive_received_dates(client):
    make_history_receipt(
        receipt_id="receipt-before",
        receipt_number="GRN-BEFORE",
        received_at=datetime(2026, 8, 8, 23, 59, 59),
    )
    make_history_receipt(
        receipt_id="receipt-start",
        receipt_number="GRN-START",
        received_at=datetime(2026, 8, 9, 0, 0, 0),
    )
    make_history_receipt(
        receipt_id="receipt-end",
        receipt_number="GRN-END",
        received_at=datetime(2026, 8, 10, 23, 59, 59),
    )
    make_history_receipt(
        receipt_id="receipt-after",
        receipt_number="GRN-AFTER",
        received_at=datetime(2026, 8, 11, 0, 0, 0),
    )

    response = client.get(
        "/api/inventory/goods-receipts?date_from=2026-08-09&date_to=2026-08-10"
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.get_json()["items"]] == [
        "receipt-end",
        "receipt-start",
    ]


def test_goods_receipt_history_validates_filters(client):
    response = client.get("/api/inventory/goods-receipts?page=0")
    assert response.status_code == 400
    assert "page" in error_message(response)

    response = client.get("/api/inventory/goods-receipts?date_from=not-a-date")
    assert response.status_code == 400
    assert "date_from" in error_message(response)

    response = client.get(
        "/api/inventory/goods-receipts?date_from=2026-08-11&date_to=2026-08-10"
    )
    assert response.status_code == 400
    assert "date_from" in error_message(response)

    response = client.get(
        f"/api/inventory/goods-receipts?warehouse_id={OTHER_BRANCH_WAREHOUSE_ID}"
    )
    assert response.status_code == 400
    assert "warehouse_id" in error_message(response)

    response = client.get(
        "/api/inventory/goods-receipts?supplier_id=other-tenant-supplier"
    )
    assert response.status_code == 400
    assert "supplier_id" in error_message(response)


def test_goods_receipt_history_filters_by_warehouse_and_supplier(client):
    make_history_receipt(
        receipt_id="receipt-match",
        receipt_number="GRN-MATCH",
        received_at=datetime(2026, 8, 10, 10, 0, 0),
    )
    make_history_receipt(
        receipt_id="receipt-no-supplier",
        receipt_number="GRN-NO-SUPPLIER",
        received_at=datetime(2026, 8, 9, 10, 0, 0),
        supplier_id=None,
    )

    response = client.get(
        f"/api/inventory/goods-receipts?warehouse_id={WAREHOUSE_ID}&supplier_id={SUPPLIER_ID}"
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.get_json()["items"]] == ["receipt-match"]


def test_goods_receipt_updates_inventory_read_and_movement_views(client):
    created = client.post("/api/inventory/goods-receipts", json=payload())
    receipt_id = created.get_json()["item"]["id"]

    stock_response = client.get("/api/inventory")
    movement_response = client.get("/api/inventory/movements")

    assert stock_response.status_code == 200
    stock = stock_response.get_json()["items"][0]
    assert stock["quantity_on_hand"] == "10.0000"
    assert stock["sellable_quantity"] == "10.0000"
    assert stock["batch_count"] == 1
    assert stock["earliest_sellable_expiry_date"] == "2027-01-31"

    assert movement_response.status_code == 200
    movement = movement_response.get_json()["items"][0]
    assert movement["movement_type"] == "goods_receipt"
    assert movement["quantity"] == "10.0000"
    assert movement["reference"] == {
        "type": "goods_receipt",
        "id": receipt_id,
    }
