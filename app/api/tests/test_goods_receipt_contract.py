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
        created_by=received_by,
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
    response = client.post(
        "/api/inventory/goods-receipts",
        json=payload(),
    )

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

    assert receipt.tenant_id == TENANT_ID
    assert receipt.branch_id == BRANCH_ID
    assert receipt.received_by == USER_ID
    assert receipt.status == "received"

    assert receipt_item.goods_receipt_id == receipt.id
    assert receipt_item.batch_id is None

    # Receiving alone must not mutate inventory.
    assert StockBalance.query.count() == 0
    assert InventoryBatch.query.count() == 0
    assert InventoryMovement.query.count() == 0



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

    body = response.get_json()["item"]
    receipt_id = body["id"]
    line = body["items"][0]

    assert line["quantity"] == "2.0000"
    assert line["base_quantity"] == "20.0000"
    assert line["product_unit_id"] == PACK_PRODUCT_UNIT_ID
    assert line["unit_code"] == "BOX"
    assert line["conversion_factor_to_base"] == "10.000000"
    assert line["unit_cost"] == "50.00"
    assert line["base_unit_cost"] == "5.00"

    receipt_item = GoodsReceiptItem.query.one()
    assert receipt_item.base_quantity == Decimal("20.0000")

    # Conversion is persisted before stock posting.
    assert StockBalance.query.count() == 0
    assert InventoryBatch.query.count() == 0
    assert InventoryMovement.query.count() == 0

    assert client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/approve"
    ).status_code == 200

    assert client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/post"
    ).status_code == 200

    stock = StockBalance.query.one()
    batch = InventoryBatch.query.one()
    movement = InventoryMovement.query.one()

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

    assert first.status_code == 201
    first_id = first.get_json()["item"]["id"]

    assert client.post(
        f"/api/inventory/goods-receipts/{first_id}/approve"
    ).status_code == 200
    assert client.post(
        f"/api/inventory/goods-receipts/{first_id}/post"
    ).status_code == 200

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

    assert second.status_code == 201
    second_id = second.get_json()["item"]["id"]

    # Second receipt remains non-stock-affecting until posted.
    assert StockBalance.query.one().quantity_on_hand == Decimal("10.0000")
    assert InventoryMovement.query.count() == 1

    assert client.post(
        f"/api/inventory/goods-receipts/{second_id}/approve"
    ).status_code == 200
    assert client.post(
        f"/api/inventory/goods-receipts/{second_id}/post"
    ).status_code == 200

    assert GoodsReceipt.query.count() == 2
    assert GoodsReceiptItem.query.count() == 2
    assert InventoryMovement.query.count() == 2
    assert InventoryBatch.query.count() == 1

    stock = StockBalance.query.one()
    batch = InventoryBatch.query.one()

    assert stock.quantity_on_hand == Decimal("20.0000")
    assert stock.avg_unit_cost == Decimal("2.00")
    assert batch.quantity_on_hand == Decimal("20.0000")



def test_goods_receipt_rejects_existing_batch_metadata_conflict(client):
    first = client.post(
        "/api/inventory/goods-receipts",
        json=payload(),
    )

    assert first.status_code == 201
    first_id = first.get_json()["item"]["id"]

    assert client.post(
        f"/api/inventory/goods-receipts/{first_id}/approve"
    ).status_code == 200
    assert client.post(
        f"/api/inventory/goods-receipts/{first_id}/post"
    ).status_code == 200

    second = client.post(
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

    # Evidence may be recorded even when it conflicts with existing stock.
    assert second.status_code == 201
    second_id = second.get_json()["item"]["id"]

    assert client.post(
        f"/api/inventory/goods-receipts/{second_id}/approve"
    ).status_code == 200

    response = client.post(
        f"/api/inventory/goods-receipts/{second_id}/post"
    )

    assert response.status_code == 409
    assert "conflicting expiry" in error_message(response)

    assert GoodsReceipt.query.count() == 2
    assert db.session.get(GoodsReceipt, second_id).status == "approved"
    assert StockBalance.query.one().quantity_on_hand == Decimal("10.0000")
    assert InventoryBatch.query.one().quantity_on_hand == Decimal("10.0000")
    assert InventoryMovement.query.count() == 1



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
    receipt_id = response.get_json()["item"]["id"]

    assert GoodsReceiptItem.query.count() == 2
    assert StockBalance.query.count() == 0
    assert InventoryBatch.query.count() == 0
    assert InventoryMovement.query.count() == 0

    assert client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/approve"
    ).status_code == 200
    assert client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/post"
    ).status_code == 200

    assert StockBalance.query.count() == 2
    assert InventoryBatch.query.count() == 1
    assert InventoryMovement.query.count() == 2



def test_goods_receipt_idempotency_replays_same_request_without_double_stock(client):
    first = client.post(
        "/api/inventory/goods-receipts",
        json=payload(),
    )
    second = client.post(
        "/api/inventory/goods-receipts",
        json=payload(),
    )

    assert first.status_code == 201
    assert second.status_code == 201

    first_id = first.get_json()["item"]["id"]
    second_id = second.get_json()["item"]["id"]

    assert first_id == second_id
    assert GoodsReceipt.query.count() == 1
    assert GoodsReceiptItem.query.count() == 1

    # Replaying creation does not create stock.
    assert StockBalance.query.count() == 0
    assert InventoryBatch.query.count() == 0
    assert InventoryMovement.query.count() == 0

    assert client.post(
        f"/api/inventory/goods-receipts/{first_id}/approve"
    ).status_code == 200
    assert client.post(
        f"/api/inventory/goods-receipts/{first_id}/post"
    ).status_code == 200

    assert InventoryMovement.query.count() == 1
    assert StockBalance.query.one().quantity_on_hand == Decimal("10.0000")



def test_goods_receipt_idempotency_rejects_conflicting_payload(client):
    assert client.post(
        "/api/inventory/goods-receipts",
        json=payload(),
    ).status_code == 201

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

    assert GoodsReceipt.query.count() == 1
    assert GoodsReceiptItem.query.count() == 1
    assert StockBalance.query.count() == 0
    assert InventoryBatch.query.count() == 0
    assert InventoryMovement.query.count() == 0



def test_goods_receipt_rolls_back_on_downstream_failure(client, monkeypatch):
    created = client.post(
        "/api/inventory/goods-receipts",
        json=payload(
            idempotency_key="receipt-post-rollback",
        ),
    )

    assert created.status_code == 201
    receipt_id = created.get_json()["item"]["id"]

    assert client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/approve"
    ).status_code == 200

    def fail(*args, **kwargs):
        raise RuntimeError("forced downstream failure")

    monkeypatch.setattr(
        "app.services.tenant.inventory.goods_receipt_service."
        "GoodsReceiptService._apply_stock_balance_receipt",
        fail,
    )

    response = client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/post"
    )

    assert response.status_code == 500

    # Receipt evidence was committed before posting and must survive.
    assert GoodsReceipt.query.count() == 1
    assert GoodsReceiptItem.query.count() == 1

    receipt = GoodsReceipt.query.one()
    assert receipt.status == "approved"
    assert receipt.posted_at is None
    assert receipt.posted_by is None

    # Posting itself is atomic.
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
    created = client.post(
        "/api/inventory/goods-receipts",
        json=payload(),
    )

    assert created.status_code == 201
    receipt_id = created.get_json()["item"]["id"]

    # Received-but-unposted goods are not inventory truth.
    stock_response = client.get("/api/inventory")
    movement_response = client.get("/api/inventory/movements")

    assert stock_response.status_code == 200
    assert stock_response.get_json()["items"] == []

    assert movement_response.status_code == 200
    assert movement_response.get_json()["items"] == []

    assert client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/approve"
    ).status_code == 200
    assert client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/post"
    ).status_code == 200

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



def test_goods_receipt_persists_supplier_invoice_evidence(client):
    request_payload = payload(
        idempotency_key="receipt-supplier-evidence-1",
        supplier_reference="DN-1001",
        supplier_invoice_number="INV-2026-001",
        supplier_invoice_date="2026-08-10",
        payment_terms="Cash",
        invoice_currency="kes",
        supplier_subtotal="100.00",
        supplier_discount_total="5.00",
        supplier_tax_total="15.20",
        supplier_invoice_total="110.20",
        items=[
            {
                "product_id": PRODUCT_ID,
                "quantity": "10",
                "invoiced_quantity": "12",
                "received_quantity": "10",
                "accepted_quantity": "9",
                "rejected_quantity": "1",
                "bonus_quantity": "2",
                "batch_number": "EVIDENCE-BATCH-1",
                "manufacture_date": "2026-01-01",
                "expiry_date": "2027-01-31",
                "unit_cost": "10.00",
                "supplier_item_code": "SUP-ITEM-001",
                "supplier_description": "Supplier description snapshot",
                "supplier_unit_price": "10.00",
                "discount_percent": "5",
                "discount_amount": "5.00",
                "tax_rate": "16",
                "tax_amount": "15.20",
                "net_unit_cost": "9.50",
                "line_total": "110.20",
                "discrepancy_status": "discrepant",
                "discrepancy_reason": "Short and rejected quantity",
                "supplier_batch_reference": "SUP-BATCH-1",
            }
        ],
    )

    response = client.post(
        "/api/inventory/goods-receipts",
        json=request_payload,
    )

    assert response.status_code == 201

    body = response.get_json()["item"]

    assert body["supplier_reference"] == "DN-1001"
    assert body["supplier_invoice_number"] == "INV-2026-001"
    assert body["supplier_invoice_date"] == "2026-08-10"
    assert body["payment_terms"] == "Cash"
    assert body["invoice_currency"] == "KES"
    assert body["supplier_subtotal"] == "100.00"
    assert body["supplier_discount_total"] == "5.00"
    assert body["supplier_tax_total"] == "15.20"
    assert body["supplier_invoice_total"] == "110.20"

    # Hela360 independently reconstructs the supplier-document maths.
    assert body["calculated_subtotal"] == "115.00"
    assert body["calculated_tax_total"] == "18.40"
    assert body["calculated_total"] == "133.40"
    assert body["reconciliation_difference"] == "-23.20"

    line = body["items"][0]

    assert line["quantity"] == "10.0000"
    assert line["invoiced_quantity"] == "12.0000"
    assert line["received_quantity"] == "10.0000"
    assert line["accepted_quantity"] == "9.0000"
    assert line["rejected_quantity"] == "1.0000"
    assert line["bonus_quantity"] == "2.0000"

    assert line["supplier_item_code"] == "SUP-ITEM-001"
    assert (
        line["supplier_description"]
        == "Supplier description snapshot"
    )

    assert line["supplier_unit_price"] == "10.00"
    assert line["discount_percent"] == "5.0000"
    assert line["discount_amount"] == "5.00"
    assert line["tax_rate"] == "16.0000"
    assert line["tax_amount"] == "15.20"
    assert line["net_unit_cost"] == "9.50"
    assert line["line_total"] == "110.20"

    assert line["discrepancy_status"] == "discrepant"
    assert (
        line["discrepancy_reason"]
        == "Short and rejected quantity"
    )

    receipt = GoodsReceipt.query.one()
    receipt_item = GoodsReceiptItem.query.one()

    assert receipt.supplier_invoice_number == "INV-2026-001"
    assert receipt.invoice_currency == "KES"
    assert receipt.supplier_invoice_total == Decimal("110.20")

    assert receipt_item.invoiced_quantity == Decimal("12.0000")
    assert receipt_item.received_quantity == Decimal("10.0000")
    assert receipt_item.accepted_quantity == Decimal("9.0000")
    assert receipt_item.rejected_quantity == Decimal("1.0000")
    assert receipt_item.bonus_quantity == Decimal("2.0000")

    # Supplier-document evidence does not affect stock until posting.
    assert StockBalance.query.count() == 0
    assert InventoryBatch.query.count() == 0
    assert InventoryMovement.query.count() == 0


def test_goods_receipt_reconciliation_matches_supplier_total(client):
    request_payload = payload(
        idempotency_key="receipt-reconciliation-match",
        supplier_invoice_number="INV-MATCH-001",
        supplier_invoice_total="116.00",
        items=[
            {
                "product_id": PRODUCT_ID,
                "quantity": "10",
                "invoiced_quantity": "10",
                "batch_number": "RECON-MATCH-1",
                "manufacture_date": "2026-01-01",
                "expiry_date": "2027-01-31",
                "unit_cost": "10.00",
                "supplier_unit_price": "10.00",
                "tax_rate": "16",
            }
        ],
    )

    response = client.post(
        "/api/inventory/goods-receipts",
        json=request_payload,
    )

    assert response.status_code == 201

    body = response.get_json()["item"]

    assert body["supplier_invoice_total"] == "116.00"
    assert body["calculated_subtotal"] == "100.00"
    assert body["calculated_tax_total"] == "16.00"
    assert body["calculated_total"] == "116.00"
    assert body["reconciliation_difference"] == "0.00"

    # Reconciliation is commercial evidence, not an inventory mutation.
    assert StockBalance.query.count() == 0
    assert InventoryBatch.query.count() == 0
    assert InventoryMovement.query.count() == 0


def test_goods_receipt_reconciliation_excludes_bonus_from_billed_quantity(
    client,
):
    request_payload = payload(
        idempotency_key="receipt-reconciliation-bonus",
        supplier_invoice_total="100.00",
        items=[
            {
                "product_id": PRODUCT_ID,
                "quantity": "12",
                "invoiced_quantity": "10",
                "received_quantity": "12",
                "accepted_quantity": "12",
                "bonus_quantity": "2",
                "batch_number": "RECON-BONUS-1",
                "manufacture_date": "2026-01-01",
                "expiry_date": "2027-01-31",
                "unit_cost": "10.00",
                "supplier_unit_price": "10.00",
            }
        ],
    )

    response = client.post(
        "/api/inventory/goods-receipts",
        json=request_payload,
    )

    assert response.status_code == 201

    body = response.get_json()["item"]

    assert body["calculated_subtotal"] == "100.00"
    assert body["calculated_tax_total"] == "0.00"
    assert body["calculated_total"] == "100.00"
    assert body["reconciliation_difference"] == "0.00"

    line = body["items"][0]
    assert line["quantity"] == "12.0000"
    assert line["invoiced_quantity"] == "10.0000"
    assert line["bonus_quantity"] == "2.0000"

    # Bonus and billed quantities remain evidence until explicit posting.
    assert StockBalance.query.count() == 0
    assert InventoryBatch.query.count() == 0
    assert InventoryMovement.query.count() == 0


def test_goods_receipt_rejects_discount_above_gross_line_value(client):
    response = client.post(
        "/api/inventory/goods-receipts",
        json=payload(
            idempotency_key="receipt-invalid-discount",
            items=[
                {
                    "product_id": PRODUCT_ID,
                    "quantity": "1",
                    "invoiced_quantity": "1",
                    "batch_number": "INVALID-DISCOUNT-1",
                    "manufacture_date": "2026-01-01",
                    "expiry_date": "2027-01-31",
                    "unit_cost": "10.00",
                    "supplier_unit_price": "10.00",
                    "discount_amount": "11.00",
                }
            ],
        ),
    )

    assert response.status_code == 400
    assert (
        "discount_amount cannot exceed"
        in error_message(response)
    )

    assert GoodsReceipt.query.count() == 0
    assert GoodsReceiptItem.query.count() == 0
    assert StockBalance.query.count() == 0
    assert InventoryMovement.query.count() == 0


def test_goods_receipt_inventory_posting_boundary_is_idempotent(client):
    response = client.post(
        "/api/inventory/goods-receipts",
        json=payload(
            idempotency_key="receipt-post-boundary-idempotent",
        ),
    )

    assert response.status_code == 201

    receipt = GoodsReceipt.query.one()

    assert StockBalance.query.count() == 0
    assert InventoryBatch.query.count() == 0
    assert InventoryMovement.query.count() == 0

    from app.extensions import db
    from app.services.tenant.inventory.goods_receipt_service import (
        GoodsReceiptService,
    )

    service = GoodsReceiptService(db.session)

    service._post_receipt_inventory(
        receipt=receipt,
        posted_by=USER_ID,
        now=receipt.updated_at,
    )
    db.session.commit()

    stock = StockBalance.query.one()
    batch = InventoryBatch.query.one()

    assert stock.quantity_on_hand == Decimal("10.0000")
    assert batch.quantity_on_hand == Decimal("10.0000")
    assert InventoryMovement.query.count() == 1

    service._post_receipt_inventory(
        receipt=receipt,
        posted_by=USER_ID,
        now=receipt.updated_at,
    )
    db.session.commit()

    assert StockBalance.query.one().quantity_on_hand == Decimal("10.0000")
    assert InventoryBatch.query.one().quantity_on_hand == Decimal("10.0000")
    assert InventoryMovement.query.count() == 1



def test_goods_receipt_can_be_approved_after_receipt(client):
    created = client.post(
        "/api/inventory/goods-receipts",
        json=payload(
            idempotency_key="receipt-workflow-approve",
        ),
    )

    assert created.status_code == 201
    receipt_id = created.get_json()["item"]["id"]

    response = client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/approve"
    )

    assert response.status_code == 200

    body = response.get_json()["item"]

    assert body["status"] == "approved"
    assert body["approved_at"] is not None
    assert body["approved_by"] == USER_ID
    assert body["posted_at"] is None
    assert body["posted_by"] is None

    receipt = GoodsReceipt.query.one()

    assert receipt.status == "approved"
    assert receipt.approved_by == USER_ID

    # Approval alone has no inventory effect.
    assert StockBalance.query.count() == 0
    assert InventoryBatch.query.count() == 0
    assert InventoryMovement.query.count() == 0



def test_goods_receipt_approval_is_idempotent(client):
    created = client.post(
        "/api/inventory/goods-receipts",
        json=payload(
            idempotency_key="receipt-workflow-approve-idempotent",
        ),
    )

    receipt_id = created.get_json()["item"]["id"]

    first = client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/approve"
    )
    second = client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/approve"
    )

    assert first.status_code == 200
    assert second.status_code == 200

    receipt = GoodsReceipt.query.one()

    assert receipt.status == "approved"
    assert StockBalance.query.count() == 0
    assert InventoryBatch.query.count() == 0
    assert InventoryMovement.query.count() == 0



def test_goods_receipt_requires_approval_before_explicit_post(client):
    created = client.post(
        "/api/inventory/goods-receipts",
        json=payload(
            idempotency_key="receipt-workflow-post-needs-approval",
        ),
    )

    receipt_id = created.get_json()["item"]["id"]

    response = client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/post"
    )

    assert response.status_code == 409
    assert (
        "Only approved goods receipts can be posted."
        in error_message(response)
    )

    receipt = GoodsReceipt.query.one()

    assert receipt.status == "received"
    assert StockBalance.query.count() == 0
    assert InventoryBatch.query.count() == 0
    assert InventoryMovement.query.count() == 0



def test_goods_receipt_can_be_explicitly_posted_after_approval(client):
    created = client.post(
        "/api/inventory/goods-receipts",
        json=payload(
            idempotency_key="receipt-workflow-post",
        ),
    )

    receipt_id = created.get_json()["item"]["id"]

    approved = client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/approve"
    )
    assert approved.status_code == 200

    response = client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/post"
    )

    assert response.status_code == 200

    body = response.get_json()["item"]

    assert body["status"] == "posted"
    assert body["approved_at"] is not None
    assert body["approved_by"] == USER_ID
    assert body["posted_at"] is not None
    assert body["posted_by"] == USER_ID

    receipt = GoodsReceipt.query.one()

    assert receipt.status == "posted"
    assert receipt.posted_by == USER_ID

    # Existing compatibility posting must not be duplicated.
    assert InventoryMovement.query.count() == 1
    assert StockBalance.query.one().quantity_on_hand == Decimal(
        "10.0000"
    )
    assert InventoryBatch.query.one().quantity_on_hand == Decimal(
        "10.0000"
    )


def test_goods_receipt_explicit_post_is_idempotent(client):
    created = client.post(
        "/api/inventory/goods-receipts",
        json=payload(
            idempotency_key="receipt-workflow-post-idempotent",
        ),
    )

    receipt_id = created.get_json()["item"]["id"]

    assert client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/approve"
    ).status_code == 200

    first = client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/post"
    )
    second = client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/post"
    )

    assert first.status_code == 200
    assert second.status_code == 200

    assert InventoryMovement.query.count() == 1
    assert StockBalance.query.one().quantity_on_hand == Decimal(
        "10.0000"
    )
    assert InventoryBatch.query.one().quantity_on_hand == Decimal(
        "10.0000"
    )


def test_goods_receipt_cannot_be_approved_after_posting(client):
    created = client.post(
        "/api/inventory/goods-receipts",
        json=payload(
            idempotency_key="receipt-workflow-no-backward-transition",
        ),
    )

    receipt_id = created.get_json()["item"]["id"]

    assert client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/approve"
    ).status_code == 200

    assert client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/post"
    ).status_code == 200

    response = client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/approve"
    )

    assert response.status_code == 409
    assert (
        "Posted goods receipt cannot be approved again."
        in error_message(response)
    )

    assert GoodsReceipt.query.one().status == "posted"
    assert InventoryMovement.query.count() == 1


def test_goods_receipt_approve_requires_inventory_approve_permission(
    app_context,
    identity,
    monkeypatch,
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

    def fake_authorize(*args, **kwargs):
        captured["kwargs"] = kwargs

    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.authorization_service.authorize",
        fake_authorize,
    )

    client = app_context.test_client()

    client.post(
        "/api/inventory/goods-receipts/not-found/approve"
    )

    assert captured["kwargs"]["permission"] == "inventory.approve"


def test_goods_receipt_post_requires_inventory_post_permission(
    app_context,
    identity,
    monkeypatch,
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

    def fake_authorize(*args, **kwargs):
        captured["kwargs"] = kwargs

    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.authorization_service.authorize",
        fake_authorize,
    )

    client = app_context.test_client()

    client.post(
        "/api/inventory/goods-receipts/not-found/post"
    )

    assert captured["kwargs"]["permission"] == "inventory.post"


def test_goods_receipt_multi_line_posting_is_atomic(client, monkeypatch):
    created = client.post(
        "/api/inventory/goods-receipts",
        json=payload(
            idempotency_key="receipt-post-multi-line-atomicity",
            items=[
                {
                    "product_id": PRODUCT_ID,
                    "quantity": "10",
                    "batch_number": "ATOMIC-BATCH-1",
                    "manufacture_date": "2026-01-01",
                    "expiry_date": "2027-01-31",
                    "unit_cost": "5.50",
                },
                {
                    "product_id": SECOND_PRODUCT_ID,
                    "quantity": "3",
                    "unit_cost": "1.50",
                },
            ],
        ),
    )

    assert created.status_code == 201
    receipt_id = created.get_json()["item"]["id"]

    assert client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/approve"
    ).status_code == 200

    from app.services.tenant.inventory.goods_receipt_service import (
        GoodsReceiptService,
    )

    original = GoodsReceiptService._apply_stock_balance_receipt
    calls = {"count": 0}

    def fail_on_second_line(self, *args, **kwargs):
        calls["count"] += 1

        if calls["count"] == 2:
            raise RuntimeError(
                "forced second-line posting failure"
            )

        return original(
            self,
            *args,
            **kwargs,
        )

    monkeypatch.setattr(
        GoodsReceiptService,
        "_apply_stock_balance_receipt",
        fail_on_second_line,
    )

    response = client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/post"
    )

    assert response.status_code == 500

    receipt = db.session.get(
        GoodsReceipt,
        receipt_id,
    )

    assert receipt.status == "approved"
    assert receipt.approved_at is not None
    assert receipt.posted_at is None
    assert receipt.posted_by is None

    # Posting is atomic: line 1 must not survive when line 2 fails.
    assert StockBalance.query.count() == 0
    assert InventoryBatch.query.count() == 0
    assert InventoryMovement.query.count() == 0

    # Receipt evidence survives the failed posting attempt.
    assert GoodsReceipt.query.count() == 1
    assert GoodsReceiptItem.query.count() == 2


def test_goods_receipt_can_be_placed_under_review(client):
    created = client.post(
        "/api/inventory/goods-receipts",
        json=payload(
            idempotency_key="receipt-workflow-review",
        ),
    )

    assert created.status_code == 201
    receipt_id = created.get_json()["item"]["id"]

    response = client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/review"
    )

    assert response.status_code == 200

    body = response.get_json()["item"]

    assert body["status"] == "under_review"
    assert body["under_review_at"] is not None
    assert body["under_review_by"] == USER_ID
    assert body["approved_at"] is None
    assert body["posted_at"] is None
    assert body["cancelled_at"] is None

    receipt = db.session.get(
        GoodsReceipt,
        receipt_id,
    )

    assert receipt.status == "under_review"
    assert receipt.under_review_by == USER_ID

    assert StockBalance.query.count() == 0
    assert InventoryBatch.query.count() == 0
    assert InventoryMovement.query.count() == 0


def test_goods_receipt_review_is_idempotent(client):
    created = client.post(
        "/api/inventory/goods-receipts",
        json=payload(
            idempotency_key="receipt-workflow-review-idempotent",
        ),
    )

    receipt_id = created.get_json()["item"]["id"]

    first = client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/review"
    )
    second = client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/review"
    )

    assert first.status_code == 200
    assert second.status_code == 200

    receipt = db.session.get(
        GoodsReceipt,
        receipt_id,
    )

    assert receipt.status == "under_review"

    assert StockBalance.query.count() == 0
    assert InventoryBatch.query.count() == 0
    assert InventoryMovement.query.count() == 0


def test_goods_receipt_can_be_approved_from_under_review(client):
    created = client.post(
        "/api/inventory/goods-receipts",
        json=payload(
            idempotency_key="receipt-workflow-review-approve",
        ),
    )

    receipt_id = created.get_json()["item"]["id"]

    assert client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/review"
    ).status_code == 200

    response = client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/approve"
    )

    assert response.status_code == 200
    assert response.get_json()["item"]["status"] == "approved"

    receipt = db.session.get(
        GoodsReceipt,
        receipt_id,
    )

    assert receipt.status == "approved"
    assert receipt.under_review_at is not None
    assert receipt.approved_at is not None

    assert StockBalance.query.count() == 0
    assert InventoryMovement.query.count() == 0


def test_goods_receipt_can_be_cancelled_from_received(client):
    created = client.post(
        "/api/inventory/goods-receipts",
        json=payload(
            idempotency_key="receipt-workflow-cancel-received",
        ),
    )

    receipt_id = created.get_json()["item"]["id"]

    response = client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/cancel"
    )

    assert response.status_code == 200

    body = response.get_json()["item"]

    assert body["status"] == "cancelled"
    assert body["cancelled_at"] is not None
    assert body["cancelled_by"] == USER_ID

    assert StockBalance.query.count() == 0
    assert InventoryBatch.query.count() == 0
    assert InventoryMovement.query.count() == 0


def test_goods_receipt_can_be_cancelled_from_under_review(client):
    created = client.post(
        "/api/inventory/goods-receipts",
        json=payload(
            idempotency_key="receipt-workflow-cancel-review",
        ),
    )

    receipt_id = created.get_json()["item"]["id"]

    assert client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/review"
    ).status_code == 200

    response = client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/cancel"
    )

    assert response.status_code == 200
    assert response.get_json()["item"]["status"] == "cancelled"

    assert StockBalance.query.count() == 0
    assert InventoryMovement.query.count() == 0


def test_goods_receipt_can_be_cancelled_from_approved(client):
    created = client.post(
        "/api/inventory/goods-receipts",
        json=payload(
            idempotency_key="receipt-workflow-cancel-approved",
        ),
    )

    receipt_id = created.get_json()["item"]["id"]

    assert client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/approve"
    ).status_code == 200

    response = client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/cancel"
    )

    assert response.status_code == 200
    assert response.get_json()["item"]["status"] == "cancelled"

    receipt = db.session.get(
        GoodsReceipt,
        receipt_id,
    )

    assert receipt.approved_at is not None
    assert receipt.cancelled_at is not None

    assert StockBalance.query.count() == 0
    assert InventoryMovement.query.count() == 0


def test_goods_receipt_cancellation_is_idempotent(client):
    created = client.post(
        "/api/inventory/goods-receipts",
        json=payload(
            idempotency_key="receipt-workflow-cancel-idempotent",
        ),
    )

    receipt_id = created.get_json()["item"]["id"]

    first = client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/cancel"
    )
    second = client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/cancel"
    )

    assert first.status_code == 200
    assert second.status_code == 200

    receipt = db.session.get(
        GoodsReceipt,
        receipt_id,
    )

    assert receipt.status == "cancelled"

    assert StockBalance.query.count() == 0
    assert InventoryMovement.query.count() == 0


def test_cancelled_goods_receipt_cannot_be_approved(client):
    created = client.post(
        "/api/inventory/goods-receipts",
        json=payload(
            idempotency_key="receipt-workflow-cancel-no-approve",
        ),
    )

    receipt_id = created.get_json()["item"]["id"]

    assert client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/cancel"
    ).status_code == 200

    response = client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/approve"
    )

    assert response.status_code == 409

    assert (
        "Only received or under-review goods receipts can be approved."
        in error_message(response)
    )

    assert db.session.get(
        GoodsReceipt,
        receipt_id,
    ).status == "cancelled"


def test_cancelled_goods_receipt_cannot_be_posted(client):
    created = client.post(
        "/api/inventory/goods-receipts",
        json=payload(
            idempotency_key="receipt-workflow-cancel-no-post",
        ),
    )

    receipt_id = created.get_json()["item"]["id"]

    assert client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/cancel"
    ).status_code == 200

    response = client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/post"
    )

    assert response.status_code == 409
    assert (
        "Only approved goods receipts can be posted."
        in error_message(response)
    )

    assert StockBalance.query.count() == 0
    assert InventoryMovement.query.count() == 0


def test_posted_goods_receipt_cannot_be_cancelled(client):
    created = client.post(
        "/api/inventory/goods-receipts",
        json=payload(
            idempotency_key="receipt-workflow-post-no-cancel",
        ),
    )

    receipt_id = created.get_json()["item"]["id"]

    assert client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/approve"
    ).status_code == 200

    assert client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/post"
    ).status_code == 200

    response = client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/cancel"
    )

    assert response.status_code == 409
    assert (
        "Posted goods receipt cannot be cancelled."
        in error_message(response)
    )

    receipt = db.session.get(
        GoodsReceipt,
        receipt_id,
    )

    assert receipt.status == "posted"
    assert receipt.cancelled_at is None

    assert StockBalance.query.one().quantity_on_hand == Decimal(
        "10.0000"
    )
    assert InventoryMovement.query.count() == 1


def test_goods_receipt_review_requires_inventory_approve_permission(
    app_context,
    identity,
    monkeypatch,
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

    def fake_authorize(*args, **kwargs):
        captured["kwargs"] = kwargs

        from app.auth.exceptions import PermissionDeniedError

        raise PermissionDeniedError("denied")

    monkeypatch.setattr(
        "app.services.tenant.auth.decorators."
        "authorization_service.authorize",
        fake_authorize,
    )

    from app.api.inventory import review_goods_receipt

    with pytest.raises(Exception):
        review_goods_receipt("receipt-id")

    assert captured["kwargs"]["permission"] == "inventory.approve"


def test_goods_receipt_cancel_requires_inventory_approve_permission(
    app_context,
    identity,
    monkeypatch,
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

    def fake_authorize(*args, **kwargs):
        captured["kwargs"] = kwargs

        from app.auth.exceptions import PermissionDeniedError

        raise PermissionDeniedError("denied")

    monkeypatch.setattr(
        "app.services.tenant.auth.decorators."
        "authorization_service.authorize",
        fake_authorize,
    )

    from app.api.inventory import cancel_goods_receipt

    with pytest.raises(Exception):
        cancel_goods_receipt("receipt-id")

    assert captured["kwargs"]["permission"] == "inventory.approve"


def draft_payload(**overrides):
    base = {
        "warehouse_id": WAREHOUSE_ID,
        "idempotency_key": "receipt-draft-key-1",
        "supplier_id": SUPPLIER_ID,
        "supplier_reference": "DN-DRAFT-1",
        "notes": "Receiving not yet completed.",
    }
    base.update(overrides)
    return base


def test_goods_receipt_draft_can_be_created_without_lines(client):
    response = client.post(
        "/api/inventory/goods-receipts/drafts",
        json=draft_payload(),
    )

    assert response.status_code == 201

    body = response.get_json()["item"]

    assert body["status"] == "draft"
    assert body["receipt_number"].startswith("GRN-2026-")
    assert body["created_by"] == USER_ID
    assert body["receiving_started_at"] is None
    assert body["receiving_started_by"] is None
    assert body["received_at"] is None
    assert body["received_by"] is None
    assert body["items"] == []

    receipt = GoodsReceipt.query.one()

    assert receipt.status == "draft"
    assert receipt.created_by == USER_ID
    assert receipt.received_at is None
    assert receipt.received_by is None

    assert GoodsReceiptItem.query.count() == 0
    assert InventoryBatch.query.count() == 0
    assert StockBalance.query.count() == 0
    assert InventoryMovement.query.count() == 0


def test_goods_receipt_draft_supports_null_supplier(client):
    response = client.post(
        "/api/inventory/goods-receipts/drafts",
        json=draft_payload(
            idempotency_key="receipt-draft-no-supplier",
            supplier_id=None,
            supplier_reference=None,
        ),
    )

    assert response.status_code == 201

    body = response.get_json()["item"]

    assert body["status"] == "draft"
    assert body["supplier"] is None


def test_goods_receipt_draft_creation_is_idempotent(client):
    first = client.post(
        "/api/inventory/goods-receipts/drafts",
        json=draft_payload(),
    )
    second = client.post(
        "/api/inventory/goods-receipts/drafts",
        json=draft_payload(),
    )

    assert first.status_code == 201
    assert second.status_code == 201

    assert (
        first.get_json()["item"]["id"]
        == second.get_json()["item"]["id"]
    )

    assert GoodsReceipt.query.count() == 1
    assert GoodsReceiptItem.query.count() == 0


def test_goods_receipt_draft_idempotency_rejects_conflicting_payload(client):
    assert client.post(
        "/api/inventory/goods-receipts/drafts",
        json=draft_payload(),
    ).status_code == 201

    response = client.post(
        "/api/inventory/goods-receipts/drafts",
        json=draft_payload(
            notes="Different draft evidence.",
        ),
    )

    assert response.status_code == 409
    assert "idempotency_key" in error_message(response)

    assert GoodsReceipt.query.count() == 1


def test_goods_receipt_draft_requires_inventory_receive_permission(
    app_context,
    identity,
    monkeypatch,
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

    def fake_authorize(*args, **kwargs):
        captured["kwargs"] = kwargs

        from app.auth.exceptions import PermissionDeniedError

        raise PermissionDeniedError("denied")

    monkeypatch.setattr(
        "app.services.tenant.auth.decorators."
        "authorization_service.authorize",
        fake_authorize,
    )

    from app.api.inventory import create_goods_receipt_draft

    with pytest.raises(Exception):
        create_goods_receipt_draft()

    assert captured["kwargs"]["permission"] == "inventory.receive"


def test_goods_receipt_draft_can_begin_receiving(client):
    created = client.post(
        "/api/inventory/goods-receipts/drafts",
        json=draft_payload(
            idempotency_key="draft-begin-receiving",
        ),
    )

    assert created.status_code == 201
    receipt_id = created.get_json()["item"]["id"]

    response = client.post(
        f"/api/inventory/goods-receipts/"
        f"{receipt_id}/begin-receiving"
    )

    assert response.status_code == 200

    body = response.get_json()["item"]

    assert body["status"] == "receiving"
    assert body["receiving_started_at"] is not None
    assert body["receiving_started_by"] == USER_ID
    assert body["received_at"] is None
    assert body["received_by"] is None

    receipt = db.session.get(
        GoodsReceipt,
        receipt_id,
    )

    assert receipt.status == "receiving"
    assert receipt.receiving_started_at is not None
    assert receipt.receiving_started_by == USER_ID
    assert receipt.received_at is None
    assert receipt.received_by is None

    assert GoodsReceiptItem.query.count() == 0
    assert InventoryBatch.query.count() == 0
    assert StockBalance.query.count() == 0
    assert InventoryMovement.query.count() == 0


def test_goods_receipt_begin_receiving_is_idempotent(client):
    created = client.post(
        "/api/inventory/goods-receipts/drafts",
        json=draft_payload(
            idempotency_key="draft-begin-idempotent",
        ),
    )

    receipt_id = created.get_json()["item"]["id"]

    first = client.post(
        f"/api/inventory/goods-receipts/"
        f"{receipt_id}/begin-receiving"
    )
    second = client.post(
        f"/api/inventory/goods-receipts/"
        f"{receipt_id}/begin-receiving"
    )

    assert first.status_code == 200
    assert second.status_code == 200

    receipt = db.session.get(
        GoodsReceipt,
        receipt_id,
    )

    assert receipt.status == "receiving"

    assert InventoryBatch.query.count() == 0
    assert StockBalance.query.count() == 0
    assert InventoryMovement.query.count() == 0


def test_received_goods_receipt_cannot_begin_receiving(client):
    created = client.post(
        "/api/inventory/goods-receipts",
        json=payload(
            idempotency_key="received-cannot-begin",
        ),
    )

    assert created.status_code == 201
    receipt_id = created.get_json()["item"]["id"]

    response = client.post(
        f"/api/inventory/goods-receipts/"
        f"{receipt_id}/begin-receiving"
    )

    assert response.status_code == 409
    assert (
        "Only draft goods receipts can begin receiving."
        in error_message(response)
    )

    receipt = db.session.get(
        GoodsReceipt,
        receipt_id,
    )

    assert receipt.status == "received"
    assert receipt.receiving_started_at is None
    assert receipt.receiving_started_by is None

    assert StockBalance.query.count() == 0
    assert InventoryMovement.query.count() == 0


def test_cancelled_goods_receipt_cannot_begin_receiving(client):
    created = client.post(
        "/api/inventory/goods-receipts/drafts",
        json=draft_payload(
            idempotency_key="cancelled-cannot-begin",
        ),
    )

    receipt_id = created.get_json()["item"]["id"]

    assert client.post(
        f"/api/inventory/goods-receipts/{receipt_id}/cancel"
    ).status_code == 200

    response = client.post(
        f"/api/inventory/goods-receipts/"
        f"{receipt_id}/begin-receiving"
    )

    assert response.status_code == 409

    receipt = db.session.get(
        GoodsReceipt,
        receipt_id,
    )

    assert receipt.status == "cancelled"
    assert receipt.receiving_started_at is None

    assert InventoryMovement.query.count() == 0


def test_goods_receipt_begin_receiving_requires_inventory_receive_permission(
    app_context,
    identity,
    monkeypatch,
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

    def fake_authorize(*args, **kwargs):
        captured["kwargs"] = kwargs

        from app.auth.exceptions import PermissionDeniedError

        raise PermissionDeniedError("denied")

    monkeypatch.setattr(
        "app.services.tenant.auth.decorators."
        "authorization_service.authorize",
        fake_authorize,
    )

    from app.api.inventory import begin_goods_receipt_receiving

    with pytest.raises(Exception):
        begin_goods_receipt_receiving("receipt-id")

    assert captured["kwargs"]["permission"] == "inventory.receive"


def editable_receipt_payload(**overrides):
    base = payload(
        supplier_reference="DN-EDIT-100",
        notes="Editable goods receipt.",
    )

    # Creation-only fields do not belong to the editable aggregate.
    base.pop("idempotency_key", None)
    base.pop("received_at", None)

    base.update(overrides)
    return base


def test_draft_goods_receipt_can_replace_header_and_lines(client):
    created = client.post(
        "/api/inventory/goods-receipts/drafts",
        json=draft_payload(
            idempotency_key="draft-edit-header-lines",
        ),
    )

    assert created.status_code == 201
    receipt_id = created.get_json()["item"]["id"]

    response = client.patch(
        f"/api/inventory/goods-receipts/{receipt_id}",
        json=editable_receipt_payload(
            supplier_reference="DN-EDITED",
            supplier_invoice_number="INV-EDITED-001",
            supplier_invoice_date="2026-09-08",
            payment_terms="30 days",
            supplier_subtotal="55.00",
            supplier_discount_total="0.00",
            supplier_tax_total="0.00",
            supplier_invoice_total="55.00",
            notes="Physical receiving evidence saved.",
        ),
    )

    assert response.status_code == 200

    item = response.get_json()["item"]

    assert item["status"] == "draft"
    assert item["supplier_reference"] == "DN-EDITED"
    assert item["supplier_invoice_number"] == "INV-EDITED-001"
    assert item["payment_terms"] == "30 days"
    assert item["notes"] == "Physical receiving evidence saved."

    assert len(item["items"]) == 1
    assert item["items"][0]["product"]["id"] == PRODUCT_ID
    assert item["items"][0]["quantity"] == "10.0000"
    assert item["items"][0]["unit_cost"] == "5.50"

    receipt = db.session.get(GoodsReceipt, receipt_id)

    assert receipt.status == "draft"
    assert receipt.received_at is None
    assert receipt.received_by is None

    assert GoodsReceiptItem.query.count() == 1

    # Editing receipt evidence must never mutate inventory.
    assert InventoryBatch.query.count() == 0
    assert StockBalance.query.count() == 0
    assert InventoryMovement.query.count() == 0


def test_receiving_goods_receipt_can_be_edited(client):
    created = client.post(
        "/api/inventory/goods-receipts/drafts",
        json=draft_payload(
            idempotency_key="receiving-edit",
        ),
    )

    receipt_id = created.get_json()["item"]["id"]

    started = client.post(
        f"/api/inventory/goods-receipts/"
        f"{receipt_id}/begin-receiving"
    )

    assert started.status_code == 200

    response = client.patch(
        f"/api/inventory/goods-receipts/{receipt_id}",
        json=editable_receipt_payload(
            notes="Updated while physically receiving.",
        ),
    )

    assert response.status_code == 200

    item = response.get_json()["item"]

    assert item["status"] == "receiving"
    assert item["receiving_started_at"] is not None
    assert item["received_at"] is None
    assert item["notes"] == "Updated while physically receiving."
    assert len(item["items"]) == 1

    assert InventoryBatch.query.count() == 0
    assert StockBalance.query.count() == 0
    assert InventoryMovement.query.count() == 0


def test_goods_receipt_edit_replaces_existing_lines(client):
    created = client.post(
        "/api/inventory/goods-receipts/drafts",
        json=draft_payload(
            idempotency_key="replace-lines",
        ),
    )

    receipt_id = created.get_json()["item"]["id"]

    first = client.patch(
        f"/api/inventory/goods-receipts/{receipt_id}",
        json=editable_receipt_payload(),
    )

    assert first.status_code == 200
    assert GoodsReceiptItem.query.count() == 1

    response = client.patch(
        f"/api/inventory/goods-receipts/{receipt_id}",
        json=editable_receipt_payload(
            supplier_reference="DN-SECOND",
            items=[
                {
                    "product_id": SECOND_PRODUCT_ID,
                    "quantity": "4",
                    "unit_cost": "2.25",
                }
            ],
        ),
    )

    assert response.status_code == 200

    rows = (
        GoodsReceiptItem.query
        .order_by(GoodsReceiptItem.line_number.asc())
        .all()
    )

    assert len(rows) == 1
    assert rows[0].product_id == SECOND_PRODUCT_ID
    assert rows[0].line_number == 1
    assert rows[0].quantity == Decimal("4.0000")
    assert rows[0].unit_cost == Decimal("2.25")

    assert InventoryBatch.query.count() == 0
    assert StockBalance.query.count() == 0
    assert InventoryMovement.query.count() == 0


def test_goods_receipt_edit_can_save_empty_line_set(client):
    created = client.post(
        "/api/inventory/goods-receipts/drafts",
        json=draft_payload(
            idempotency_key="empty-edit-lines",
        ),
    )

    receipt_id = created.get_json()["item"]["id"]

    populated = client.patch(
        f"/api/inventory/goods-receipts/{receipt_id}",
        json=editable_receipt_payload(),
    )

    assert populated.status_code == 200
    assert GoodsReceiptItem.query.count() == 1

    response = client.patch(
        f"/api/inventory/goods-receipts/{receipt_id}",
        json=editable_receipt_payload(
            items=[],
            supplier_subtotal=None,
            supplier_discount_total=None,
            supplier_tax_total=None,
            supplier_invoice_total=None,
        ),
    )

    assert response.status_code == 200

    item = response.get_json()["item"]

    assert item["status"] == "draft"
    assert item["items"] == []
    assert GoodsReceiptItem.query.count() == 0

    assert InventoryBatch.query.count() == 0
    assert StockBalance.query.count() == 0
    assert InventoryMovement.query.count() == 0


def test_goods_receipt_edit_resolves_product_units_without_stock_effect(client):
    created = client.post(
        "/api/inventory/goods-receipts/drafts",
        json=draft_payload(
            idempotency_key="edit-unit-conversion",
        ),
    )

    receipt_id = created.get_json()["item"]["id"]

    response = client.patch(
        f"/api/inventory/goods-receipts/{receipt_id}",
        json=editable_receipt_payload(
            items=[
                {
                    "product_id": PRODUCT_ID,
                    "product_unit_id": PACK_PRODUCT_UNIT_ID,
                    "quantity": "2",
                    "batch_number": "EDIT-BOX-BATCH",
                    "manufacture_date": "2026-01-01",
                    "expiry_date": "2027-01-31",
                    "unit_cost": "50.00",
                }
            ],
        ),
    )

    assert response.status_code == 200

    line = response.get_json()["item"]["items"][0]

    assert line["quantity"] == "2.0000"
    assert line["base_quantity"] == "20.0000"
    assert line["product_unit_id"] == PACK_PRODUCT_UNIT_ID
    assert line["unit_code"] == "BOX"
    assert line["conversion_factor_to_base"] == "10.000000"
    assert line["base_unit_cost"] == "5.00"

    assert InventoryBatch.query.count() == 0
    assert StockBalance.query.count() == 0
    assert InventoryMovement.query.count() == 0


def test_goods_receipt_edit_rolls_back_on_invalid_replacement(client):
    created = client.post(
        "/api/inventory/goods-receipts/drafts",
        json=draft_payload(
            idempotency_key="edit-rollback",
        ),
    )

    receipt_id = created.get_json()["item"]["id"]

    initial = client.patch(
        f"/api/inventory/goods-receipts/{receipt_id}",
        json=editable_receipt_payload(
            supplier_reference="ORIGINAL-DN",
        ),
    )

    assert initial.status_code == 200

    original_line = GoodsReceiptItem.query.one()
    original_line_id = original_line.id

    response = client.patch(
        f"/api/inventory/goods-receipts/{receipt_id}",
        json=editable_receipt_payload(
            supplier_reference="SHOULD-ROLL-BACK",
            items=[
                {
                    "product_id": NON_INVENTORY_PRODUCT_ID,
                    "quantity": "3",
                    "unit_cost": "10.00",
                }
            ],
        ),
    )

    assert response.status_code == 400

    db.session.expire_all()

    receipt = db.session.get(GoodsReceipt, receipt_id)
    rows = GoodsReceiptItem.query.all()

    assert receipt.supplier_reference == "ORIGINAL-DN"
    assert len(rows) == 1
    assert rows[0].id == original_line_id
    assert rows[0].product_id == PRODUCT_ID

    assert InventoryBatch.query.count() == 0
    assert StockBalance.query.count() == 0
    assert InventoryMovement.query.count() == 0


def test_received_goods_receipt_cannot_be_edited(client):
    created = client.post(
        "/api/inventory/goods-receipts",
        json=payload(
            idempotency_key="received-edit-rejected",
        ),
    )

    assert created.status_code == 201
    receipt_id = created.get_json()["item"]["id"]

    response = client.patch(
        f"/api/inventory/goods-receipts/{receipt_id}",
        json=editable_receipt_payload(),
    )

    assert response.status_code == 409
    assert (
        "Only draft or receiving goods receipts can be edited."
        in error_message(response)
    )

    receipt = db.session.get(GoodsReceipt, receipt_id)
    assert receipt.status == "received"


def test_goods_receipt_edit_requires_inventory_receive_permission(
    app_context,
    identity,
    monkeypatch,
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
        captured["kwargs"] = kwargs

        from app.auth.exceptions import PermissionDeniedError

        raise PermissionDeniedError("denied")

    monkeypatch.setattr(
        "app.services.tenant.auth.decorators."
        "authorization_service.authorize",
        deny,
    )

    response = app_context.test_client().patch(
        "/api/inventory/goods-receipts/receipt-id",
        json=editable_receipt_payload(),
    )

    assert response.status_code == 403
    assert captured["kwargs"]["permission"] == "inventory.receive"


def test_receiving_goods_receipt_can_complete_receiving(client):
    created = client.post(
        "/api/inventory/goods-receipts/drafts",
        json=draft_payload(
            idempotency_key="complete-receiving-success",
        ),
    )

    assert created.status_code == 201
    receipt_id = created.get_json()["item"]["id"]

    updated = client.patch(
        f"/api/inventory/goods-receipts/{receipt_id}",
        json=editable_receipt_payload(),
    )

    assert updated.status_code == 200

    started = client.post(
        f"/api/inventory/goods-receipts/"
        f"{receipt_id}/begin-receiving"
    )

    assert started.status_code == 200
    assert started.get_json()["item"]["status"] == "receiving"

    response = client.post(
        f"/api/inventory/goods-receipts/"
        f"{receipt_id}/complete-receiving"
    )

    assert response.status_code == 200

    item = response.get_json()["item"]

    assert item["status"] == "received"
    assert item["received_at"] is not None
    assert item["received_by"]["id"] == USER_ID
    assert len(item["items"]) == 1

    receipt = db.session.get(GoodsReceipt, receipt_id)

    assert receipt.status == "received"
    assert receipt.received_at is not None
    assert receipt.received_by == USER_ID

    # Completing receiving records evidence only.
    assert InventoryBatch.query.count() == 0
    assert StockBalance.query.count() == 0
    assert InventoryMovement.query.count() == 0


def test_complete_goods_receipt_receiving_is_idempotent(client):
    created = client.post(
        "/api/inventory/goods-receipts/drafts",
        json=draft_payload(
            idempotency_key="complete-receiving-idempotent",
        ),
    )

    receipt_id = created.get_json()["item"]["id"]

    assert client.patch(
        f"/api/inventory/goods-receipts/{receipt_id}",
        json=editable_receipt_payload(),
    ).status_code == 200

    assert client.post(
        f"/api/inventory/goods-receipts/"
        f"{receipt_id}/begin-receiving"
    ).status_code == 200

    first = client.post(
        f"/api/inventory/goods-receipts/"
        f"{receipt_id}/complete-receiving"
    )

    assert first.status_code == 200

    first_item = first.get_json()["item"]

    second = client.post(
        f"/api/inventory/goods-receipts/"
        f"{receipt_id}/complete-receiving"
    )

    assert second.status_code == 200

    second_item = second.get_json()["item"]

    assert second_item["status"] == "received"
    assert (
        second_item["received_at"]
        == first_item["received_at"]
    )
    assert (
        second_item["received_by"]["id"]
        == first_item["received_by"]["id"]
        == USER_ID
    )

    assert InventoryBatch.query.count() == 0
    assert StockBalance.query.count() == 0
    assert InventoryMovement.query.count() == 0


def test_complete_goods_receipt_receiving_requires_lines(client):
    created = client.post(
        "/api/inventory/goods-receipts/drafts",
        json=draft_payload(
            idempotency_key="complete-receiving-empty",
        ),
    )

    receipt_id = created.get_json()["item"]["id"]

    started = client.post(
        f"/api/inventory/goods-receipts/"
        f"{receipt_id}/begin-receiving"
    )

    assert started.status_code == 200

    response = client.post(
        f"/api/inventory/goods-receipts/"
        f"{receipt_id}/complete-receiving"
    )

    assert response.status_code == 400
    assert "at least one line" in error_message(response)

    db.session.expire_all()

    receipt = db.session.get(GoodsReceipt, receipt_id)

    assert receipt.status == "receiving"
    assert receipt.received_at is None
    assert receipt.received_by is None

    assert InventoryBatch.query.count() == 0
    assert StockBalance.query.count() == 0
    assert InventoryMovement.query.count() == 0


def test_draft_goods_receipt_cannot_complete_receiving(client):
    created = client.post(
        "/api/inventory/goods-receipts/drafts",
        json=draft_payload(
            idempotency_key="complete-receiving-from-draft",
        ),
    )

    receipt_id = created.get_json()["item"]["id"]

    response = client.post(
        f"/api/inventory/goods-receipts/"
        f"{receipt_id}/complete-receiving"
    )

    assert response.status_code == 409
    assert (
        "Only a receiving goods receipt can complete receiving."
        in error_message(response)
    )

    receipt = db.session.get(GoodsReceipt, receipt_id)

    assert receipt.status == "draft"
    assert receipt.received_at is None
    assert receipt.received_by is None


def test_complete_receiving_revalidates_persisted_evidence(client):
    created = client.post(
        "/api/inventory/goods-receipts/drafts",
        json=draft_payload(
            idempotency_key="complete-receiving-revalidate",
        ),
    )

    receipt_id = created.get_json()["item"]["id"]

    updated = client.patch(
        f"/api/inventory/goods-receipts/{receipt_id}",
        json=editable_receipt_payload(),
    )

    assert updated.status_code == 200

    started = client.post(
        f"/api/inventory/goods-receipts/"
        f"{receipt_id}/begin-receiving"
    )

    assert started.status_code == 200

    # Simulate persisted evidence becoming invalid before finalization.
    receipt_item = GoodsReceiptItem.query.one()
    receipt_item.expiry_date = date(2020, 1, 1)
    db.session.commit()

    response = client.post(
        f"/api/inventory/goods-receipts/"
        f"{receipt_id}/complete-receiving"
    )

    assert response.status_code == 400
    assert "Expired stock" in error_message(response)

    db.session.expire_all()

    receipt = db.session.get(GoodsReceipt, receipt_id)

    assert receipt.status == "receiving"
    assert receipt.received_at is None
    assert receipt.received_by is None

    assert InventoryBatch.query.count() == 0
    assert StockBalance.query.count() == 0
    assert InventoryMovement.query.count() == 0


def test_complete_receiving_requires_inventory_receive_permission(
    app_context,
    identity,
    monkeypatch,
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
        captured["kwargs"] = kwargs

        from app.auth.exceptions import PermissionDeniedError

        raise PermissionDeniedError("denied")

    monkeypatch.setattr(
        "app.services.tenant.auth.decorators."
        "authorization_service.authorize",
        deny,
    )

    response = app_context.test_client().post(
        "/api/inventory/goods-receipts/"
        "receipt-id/complete-receiving"
    )

    assert response.status_code == 403
    assert captured["kwargs"]["permission"] == "inventory.receive"


def test_complete_receiving_rejects_existing_inventory_movement(client):
    created = client.post(
        "/api/inventory/goods-receipts/drafts",
        json=draft_payload(
            idempotency_key="complete-receiving-movement-guard",
        ),
    )

    assert created.status_code == 201
    receipt_id = created.get_json()["item"]["id"]

    updated = client.patch(
        f"/api/inventory/goods-receipts/{receipt_id}",
        json=editable_receipt_payload(),
    )

    assert updated.status_code == 200

    started = client.post(
        f"/api/inventory/goods-receipts/"
        f"{receipt_id}/begin-receiving"
    )

    assert started.status_code == 200

    # Simulate historical or otherwise inconsistent inventory evidence
    # already existing before the workflow completion transition.
    movement = InventoryMovement(
        tenant_id=TENANT_ID,
        branch_id=BRANCH_ID,
        warehouse_id=WAREHOUSE_ID,
        product_id=PRODUCT_ID,
        batch_id=None,
        movement_type="goods_receipt",
        quantity=Decimal("10.0000"),
        unit_cost=Decimal("5.50"),
        reference_type="goods_receipt",
        reference_id=receipt_id,
        notes="Pre-existing compatibility movement.",
        created_by=USER_ID,
    )
    db.session.add(movement)
    db.session.commit()

    response = client.post(
        f"/api/inventory/goods-receipts/"
        f"{receipt_id}/complete-receiving"
    )

    assert response.status_code == 409
    assert (
        "already has inventory movements"
        in error_message(response)
    )

    db.session.expire_all()

    receipt = db.session.get(GoodsReceipt, receipt_id)

    assert receipt.status == "receiving"
    assert receipt.received_at is None
    assert receipt.received_by is None

    # Existing evidence remains untouched; completion adds nothing.
    assert InventoryMovement.query.count() == 1
    assert StockBalance.query.count() == 0
    assert InventoryBatch.query.count() == 0


def test_stock_bearing_historical_goods_receipt_cannot_be_cancelled(client):
    received_at = datetime(
        2026,
        8,
        9,
        10,
        0,
        tzinfo=timezone.utc,
    )

    receipt = make_history_receipt(
        receipt_id="historical-stock-bearing-receipt",
        receipt_number="GRN-2026-HIST-STOCK",
        received_at=received_at,
    )

    movement = InventoryMovement(
        tenant_id=TENANT_ID,
        branch_id=BRANCH_ID,
        warehouse_id=WAREHOUSE_ID,
        product_id=PRODUCT_ID,
        batch_id=None,
        movement_type="goods_receipt",
        quantity=Decimal("10.0000"),
        unit_cost=Decimal("5.50"),
        reference_type="goods_receipt",
        reference_id=str(receipt.id),
        notes="Historical compatibility posting.",
        created_by=USER_ID,
    )
    db.session.add(movement)
    db.session.commit()

    response = client.post(
        f"/api/inventory/goods-receipts/"
        f"{receipt.id}/cancel"
    )

    assert response.status_code == 409
    assert (
        "already has inventory movements"
        in error_message(response)
    )

    db.session.expire_all()

    persisted = db.session.get(
        GoodsReceipt,
        str(receipt.id),
    )

    assert persisted.status == "received"
    assert persisted.cancelled_at is None
    assert persisted.cancelled_by is None
    assert InventoryMovement.query.count() == 1


def test_stock_bearing_historical_goods_receipt_cannot_be_cancelled(client):
    received_at = datetime(
        2026,
        8,
        9,
        10,
        0,
        tzinfo=timezone.utc,
    )

    receipt = make_history_receipt(
        receipt_id="historical-stock-bearing-receipt",
        receipt_number="GRN-2026-HIST-STOCK",
        received_at=received_at,
    )

    movement = InventoryMovement(
        tenant_id=TENANT_ID,
        branch_id=BRANCH_ID,
        warehouse_id=WAREHOUSE_ID,
        product_id=PRODUCT_ID,
        batch_id=None,
        movement_type="goods_receipt",
        quantity=Decimal("10.0000"),
        unit_cost=Decimal("5.50"),
        reference_type="goods_receipt",
        reference_id=str(receipt.id),
        notes="Historical compatibility posting.",
        created_by=USER_ID,
    )
    db.session.add(movement)
    db.session.commit()

    response = client.post(
        f"/api/inventory/goods-receipts/"
        f"{receipt.id}/cancel"
    )

    assert response.status_code == 409
    assert (
        "already has inventory movements"
        in error_message(response)
    )

    db.session.expire_all()

    persisted = db.session.get(
        GoodsReceipt,
        str(receipt.id),
    )

    assert persisted.status == "received"
    assert persisted.cancelled_at is None
    assert persisted.cancelled_by is None
    assert InventoryMovement.query.count() == 1
