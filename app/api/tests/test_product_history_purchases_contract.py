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
    GoodsReceipt,
    GoodsReceiptItem,
    Product,
    Supplier,
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

SUPPLIER_ID = "supplier-a"
SECOND_SUPPLIER_ID = "supplier-b"


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
        Supplier.__table__.create(db.engine)
        GoodsReceipt.__table__.create(db.engine)
        GoodsReceiptItem.__table__.create(db.engine)

        seed_data()

        yield app

        db.session.remove()

        GoodsReceiptItem.__table__.drop(db.engine)
        GoodsReceipt.__table__.drop(db.engine)
        Supplier.__table__.drop(db.engine)
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


def receipt(
    receipt_id: str,
    *,
    receipt_number: str,
    product_id: str = PRODUCT_ID,
    tenant_id: str = TENANT_ID,
    branch_id: str = BRANCH_ID,
    warehouse_id: str = WAREHOUSE_ID,
    supplier_id: str | None = SUPPLIER_ID,
    status: str = "posted",
    posted_at: datetime | None = None,
    received_at: datetime | None = None,
    quantity: Decimal = Decimal("2.0000"),
    base_quantity: Decimal = Decimal("20.0000"),
    unit_cost: Decimal = Decimal("100.00"),
    base_unit_cost: Decimal = Decimal("10.00"),
    line_number: int = 1,
):
    posted_at = posted_at or datetime(
        2026,
        8,
        10,
        12,
        0,
        tzinfo=timezone.utc,
    )
    received_at = received_at or posted_at

    header = GoodsReceipt(
        id=receipt_id,
        tenant_id=tenant_id,
        branch_id=branch_id,
        warehouse_id=warehouse_id,
        supplier_id=supplier_id,
        receipt_number=receipt_number,
        supplier_reference=f"DN-{receipt_id}",
        supplier_invoice_number=f"INV-{receipt_id}",
        supplier_invoice_date=date(2026, 8, 9),
        invoice_currency="KES",
        idempotency_key=f"idem-{receipt_id}",
        request_fingerprint=f"fingerprint-{receipt_id}",
        created_by=USER_ID,
        received_at=received_at,
        received_by=USER_ID,
        status=status,
        posted_at=(
            posted_at
            if status == "posted"
            else None
        ),
        posted_by=(
            USER_ID
            if status == "posted"
            else None
        ),
    )

    line = GoodsReceiptItem(
        id=f"item-{receipt_id}-{line_number}",
        goods_receipt_id=receipt_id,
        product_id=product_id,
        line_number=line_number,
        quantity=quantity,
        base_quantity=base_quantity,
        unit_code_snapshot="BOX",
        unit_name_snapshot="Box",
        conversion_factor_to_base=Decimal("10.000000"),
        batch_number=f"BATCH-{receipt_id}",
        manufacture_date=date(2026, 1, 1),
        expiry_date=date(2027, 12, 31),
        unit_cost=unit_cost,
        base_unit_cost=base_unit_cost,
    )

    db.session.add_all([header, line])


def seed_data():
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
                first_name="Receiving",
                last_name="User",
                email="receiver@example.test",
                username="receiver",
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
                code="OTHER",
                name="Other Branch Warehouse",
            ),
            Supplier(
                id=SUPPLIER_ID,
                tenant_id=TENANT_ID,
                supplier_code="SUP-A",
                name="Supplier A",
            ),
            Supplier(
                id=SECOND_SUPPLIER_ID,
                tenant_id=TENANT_ID,
                supplier_code="SUP-B",
                name="Supplier B",
            ),
        ]
    )

    receipt(
        "receipt-new",
        receipt_number="GRN-NEW",
        posted_at=datetime(
            2026,
            8,
            10,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )
    receipt(
        "receipt-old",
        receipt_number="GRN-OLD",
        posted_at=datetime(
            2026,
            8,
            8,
            10,
            0,
            tzinfo=timezone.utc,
        ),
        unit_cost=Decimal("90.00"),
        base_unit_cost=Decimal("9.00"),
    )
    receipt(
        "receipt-other-product",
        receipt_number="GRN-OTHER-PRODUCT",
        product_id=SECOND_PRODUCT_ID,
    )
    receipt(
        "receipt-unposted",
        receipt_number="GRN-UNPOSTED",
        status="received",
    )
    receipt(
        "receipt-other-branch",
        receipt_number="GRN-OTHER-BRANCH",
        branch_id=OTHER_BRANCH_ID,
        warehouse_id=OTHER_BRANCH_WAREHOUSE_ID,
    )

    db.session.commit()


def test_purchase_history_is_product_branch_and_posted_scoped(
    client,
):
    response = client.get(
        f"/api/products/{PRODUCT_ID}/history/purchases"
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["ok"] is True

    ids = [
        item["receipt"]["id"]
        for item in payload["items"]
    ]

    assert ids == [
        "receipt-new",
        "receipt-old",
    ]

    assert "receipt-unposted" not in ids
    assert "receipt-other-product" not in ids
    assert "receipt-other-branch" not in ids


def test_purchase_history_preserves_historical_uom_and_cost(
    client,
):
    response = client.get(
        f"/api/products/{PRODUCT_ID}/history/purchases"
    )

    assert response.status_code == 200

    item = response.get_json()["items"][0]

    assert item["quantity"] == "2.0000"
    assert item["base_quantity"] == "20.0000"

    assert item["uom"] == {
        "code": "BOX",
        "name": "Box",
        "conversion_factor_to_base": "10.000000",
    }

    assert item["unit_cost"] == "100.00"
    assert item["base_unit_cost"] == "10.00"

    assert item["receipt"]["receipt_number"] == "GRN-NEW"
    assert item["receipt"]["supplier_invoice_number"] == (
        "INV-receipt-new"
    )

    assert item["supplier"] == {
        "id": SUPPLIER_ID,
        "supplier_code": "SUP-A",
        "name": "Supplier A",
    }

    assert item["warehouse"] == {
        "id": WAREHOUSE_ID,
        "code": "MAIN",
        "name": "Main Warehouse",
    }


def test_purchase_history_filters_supplier_and_warehouse(
    client,
):
    receipt(
        "receipt-second-supplier",
        receipt_number="GRN-SUP-B",
        supplier_id=SECOND_SUPPLIER_ID,
        warehouse_id=SECOND_WAREHOUSE_ID,
        posted_at=datetime(
            2026,
            8,
            11,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )
    db.session.commit()

    response = client.get(
        (
            f"/api/products/{PRODUCT_ID}/history/purchases"
            f"?supplier_id={SECOND_SUPPLIER_ID}"
            f"&warehouse_id={SECOND_WAREHOUSE_ID}"
        )
    )

    assert response.status_code == 200

    ids = [
        item["receipt"]["id"]
        for item in response.get_json()["items"]
    ]

    assert ids == [
        "receipt-second-supplier",
    ]


def test_purchase_history_filters_posted_dates(client):
    response = client.get(
        (
            f"/api/products/{PRODUCT_ID}/history/purchases"
            "?date_from=2026-08-10"
            "&date_to=2026-08-10"
        )
    )

    assert response.status_code == 200

    ids = [
        item["receipt"]["id"]
        for item in response.get_json()["items"]
    ]

    assert ids == ["receipt-new"]


def test_purchase_history_is_paginated(client):
    response = client.get(
        (
            f"/api/products/{PRODUCT_ID}/history/purchases"
            "?page=1&per_page=1"
        )
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert [
        item["receipt"]["id"]
        for item in payload["items"]
    ] == ["receipt-new"]

    assert payload["pagination"] == {
        "page": 1,
        "per_page": 1,
        "total": 2,
        "pages": 2,
        "has_prev": False,
        "has_next": True,
    }


def test_purchase_history_rejects_cross_tenant_product(
    client,
):
    response = client.get(
        (
            "/api/products/other-tenant-product/"
            "history/purchases"
        )
    )

    assert response.status_code == 404
    assert response.get_json() == {
        "ok": False,
        "error": "Product not found.",
    }


def test_purchase_history_requires_branch(
    client,
    identity: SimpleNamespace,
):
    identity.branch_id = None

    response = client.get(
        f"/api/products/{PRODUCT_ID}/history/purchases"
    )

    assert response.status_code == 400
    assert "branch" in response.get_json()["error"]


def test_purchase_price_trend_is_complete_chronological_and_posted(
    client,
):
    response = client.get(
        (
            f"/api/products/{PRODUCT_ID}"
            "/history/purchases/price-trend"
        )
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["ok"] is True
    assert "pagination" not in payload

    items = payload["items"]

    assert [
        item["source"]["id"]
        for item in items
    ] == [
        "receipt-old",
        "receipt-new",
    ]

    assert [
        item["value"]
        for item in items
    ] == [
        "9.00",
        "10.00",
    ]

    assert items[0]["source"] == {
        "type": "goods_receipt",
        "id": "receipt-old",
        "number": "GRN-OLD",
    }

    assert all(
        item["source"]["id"]
        != "receipt-unposted"
        for item in items
    )


def test_purchase_price_trend_filters_date_and_warehouse(
    client,
):
    receipt(
        "receipt-front-trend",
        receipt_number="GRN-FRONT-TREND",
        warehouse_id=SECOND_WAREHOUSE_ID,
        posted_at=datetime(
            2026,
            8,
            13,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        unit_cost=Decimal("110.00"),
        base_unit_cost=Decimal("11.00"),
    )
    db.session.commit()

    response = client.get(
        (
            f"/api/products/{PRODUCT_ID}"
            "/history/purchases/price-trend"
            "?date_from=2026-08-13"
            "&date_to=2026-08-13"
            f"&warehouse_id={SECOND_WAREHOUSE_ID}"
        )
    )

    assert response.status_code == 200

    items = response.get_json()["items"]

    assert [
        item["source"]["id"]
        for item in items
    ] == ["receipt-front-trend"]

    assert items[0]["value"] == "11.00"


def test_purchase_price_trend_rejects_cross_tenant_product(
    client,
):
    response = client.get(
        (
            "/api/products/other-tenant-product/"
            "history/purchases/price-trend"
        )
    )

    assert response.status_code == 404
    assert response.get_json() == {
        "ok": False,
        "error": "Product not found.",
    }


def test_purchase_price_trend_requires_branch(
    client,
    identity: SimpleNamespace,
):
    identity.branch_id = None

    response = client.get(
        (
            f"/api/products/{PRODUCT_ID}"
            "/history/purchases/price-trend"
        )
    )

    assert response.status_code == 400
    assert "branch" in response.get_json()["error"]


def test_purchase_history_requires_inventory_read(
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
        f"/api/products/{PRODUCT_ID}/history/purchases"
    )

    assert response.status_code == 403
    assert captured["kwargs"]["permission"] == "inventory.read"
