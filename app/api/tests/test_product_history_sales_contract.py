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
    Customer,
    InventoryBatch,
    Product,
    Sale,
    SaleItem,
    Tenant,
    Till,
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

TILL_ID = "till-a"
SECOND_TILL_ID = "till-b"
OTHER_BRANCH_TILL_ID = "till-c"

CUSTOMER_ID = "customer-a"

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
    app.register_blueprint(
        products_bp,
        url_prefix="/api",
    )
    register_error_handlers(app)

    with app.app_context():
        Tenant.__table__.create(db.engine)
        Branch.__table__.create(db.engine)
        User.__table__.create(db.engine)
        Customer.__table__.create(db.engine)
        Product.__table__.create(db.engine)
        Warehouse.__table__.create(db.engine)
        Till.__table__.create(db.engine)
        InventoryBatch.__table__.create(db.engine)
        Sale.__table__.create(db.engine)
        SaleItem.__table__.create(db.engine)

        seed_data()

        yield app

        db.session.remove()

        SaleItem.__table__.drop(db.engine)
        Sale.__table__.drop(db.engine)
        InventoryBatch.__table__.drop(db.engine)
        Till.__table__.drop(db.engine)
        Warehouse.__table__.drop(db.engine)
        Product.__table__.drop(db.engine)
        Customer.__table__.drop(db.engine)
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


def add_sale(
    sale_id: str,
    *,
    sale_number: str,
    sale_date: datetime,
    product_id: str = PRODUCT_ID,
    tenant_id: str = TENANT_ID,
    branch_id: str = BRANCH_ID,
    warehouse_id: str = WAREHOUSE_ID,
    till_id: str = TILL_ID,
    customer_id: str | None = CUSTOMER_ID,
    status: str = "paid",
    refund_status: str = "not_refunded",
    refunded_amount: Decimal = Decimal("0.00"),
    quantity: Decimal = Decimal("2.0000"),
    base_quantity: Decimal = Decimal("20.0000"),
    unit_price: Decimal = Decimal("120.00"),
    batch_id: str | None = BATCH_ID,
):
    sale = Sale(
        id=sale_id,
        tenant_id=tenant_id,
        branch_id=branch_id,
        till_id=till_id,
        warehouse_id=warehouse_id,
        customer_id=customer_id,
        sale_number=sale_number,
        sale_date=sale_date,
        sale_channel="pos",
        status=status,
        subtotal=Decimal("240.00"),
        discount_amount=Decimal("10.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("230.00"),
        paid_amount=Decimal("230.00"),
        balance_due=Decimal("0.00"),
        cashier_id=USER_ID,
        refunded_amount=refunded_amount,
        refund_status=refund_status,
        created_at=sale_date,
        updated_at=sale_date,
    )

    line = SaleItem(
        id=f"item-{sale_id}",
        sale_id=sale_id,
        product_id=product_id,
        batch_id=batch_id,
        quantity=quantity,
        base_quantity=base_quantity,
        unit_price=unit_price,
        unit_code_snapshot="BOX",
        unit_name_snapshot="Box",
        conversion_factor_to_base=Decimal(
            "10.000000"
        ),
        discount_amount=Decimal("10.00"),
        tax_amount=Decimal("0.00"),
        line_total=Decimal("230.00"),
        cost_of_sale=None,
        is_returned=(
            refund_status == "refunded"
        ),
    )

    db.session.add_all([sale, line])


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
                first_name="Sales",
                last_name="User",
                email="sales@example.test",
                username="sales",
                password_hash="hash",
            ),
            Customer(
                id=CUSTOMER_ID,
                tenant_id=TENANT_ID,
                customer_number="CUST-001",
                first_name="Jane",
                last_name="Doe",
                phone="+254700000001",
            ),
            Product(
                id=PRODUCT_ID,
                tenant_id=TENANT_ID,
                internal_sku="PARA-500",
                name="Paracetamol 500mg",
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
            Till(
                id=TILL_ID,
                tenant_id=TENANT_ID,
                branch_id=BRANCH_ID,
                warehouse_id=WAREHOUSE_ID,
                code="TILL-A",
                name="Till A",
            ),
            Till(
                id=SECOND_TILL_ID,
                tenant_id=TENANT_ID,
                branch_id=BRANCH_ID,
                warehouse_id=SECOND_WAREHOUSE_ID,
                code="TILL-B",
                name="Till B",
            ),
            Till(
                id=OTHER_BRANCH_TILL_ID,
                tenant_id=TENANT_ID,
                branch_id=OTHER_BRANCH_ID,
                warehouse_id=OTHER_BRANCH_WAREHOUSE_ID,
                code="TILL-C",
                name="Till C",
            ),
            InventoryBatch(
                id=BATCH_ID,
                tenant_id=TENANT_ID,
                product_id=PRODUCT_ID,
                warehouse_id=WAREHOUSE_ID,
                batch_number="BATCH-001",
                expiry_date=date(2027, 12, 31),
                quantity_on_hand=Decimal("10.0000"),
                quantity_reserved=Decimal("0.0000"),
            ),
        ]
    )

    add_sale(
        "sale-new",
        sale_number="SALE-NEW",
        sale_date=datetime(
            2026,
            8,
            10,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )

    add_sale(
        "sale-old",
        sale_number="SALE-OLD",
        sale_date=datetime(
            2026,
            8,
            8,
            10,
            0,
            tzinfo=timezone.utc,
        ),
        unit_price=Decimal("100.00"),
    )

    add_sale(
        "sale-refunded",
        sale_number="SALE-REF",
        sale_date=datetime(
            2026,
            8,
            9,
            11,
            0,
            tzinfo=timezone.utc,
        ),
        status="refunded",
        refund_status="refunded",
        refunded_amount=Decimal("230.00"),
    )

    add_sale(
        "sale-other-product",
        sale_number="SALE-OTHER-PRODUCT",
        sale_date=datetime(
            2026,
            8,
            11,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        product_id=SECOND_PRODUCT_ID,
        batch_id=None,
    )

    add_sale(
        "sale-other-branch",
        sale_number="SALE-OTHER-BRANCH",
        sale_date=datetime(
            2026,
            8,
            12,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        branch_id=OTHER_BRANCH_ID,
        warehouse_id=OTHER_BRANCH_WAREHOUSE_ID,
        till_id=OTHER_BRANCH_TILL_ID,
        batch_id=None,
        customer_id=None,
    )

    db.session.commit()


def test_sales_history_is_product_and_branch_scoped(
    client,
):
    response = client.get(
        f"/api/products/{PRODUCT_ID}/history/sales"
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["ok"] is True

    ids = [
        item["sale"]["id"]
        for item in payload["items"]
    ]

    assert ids == [
        "sale-new",
        "sale-refunded",
        "sale-old",
    ]

    assert "sale-other-product" not in ids
    assert "sale-other-branch" not in ids


def test_sales_history_preserves_transaction_uom_and_price(
    client,
):
    response = client.get(
        f"/api/products/{PRODUCT_ID}/history/sales"
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

    assert item["unit_price"] == "120.00"
    assert (
        item["normalized_base_unit_price"]
        == "12.000000"
    )

    assert item["discount_amount"] == "10.00"
    assert item["line_total"] == "230.00"

    assert item["batch"] == {
        "id": BATCH_ID,
        "batch_number": "BATCH-001",
        "expiry_date": "2027-12-31",
    }


def test_sales_history_keeps_refunded_sale_as_evidence(
    client,
):
    response = client.get(
        (
            f"/api/products/{PRODUCT_ID}/history/sales"
            "?status=refunded"
        )
    )

    assert response.status_code == 200

    items = response.get_json()["items"]

    assert len(items) == 1
    assert items[0]["sale"]["id"] == "sale-refunded"
    assert items[0]["sale"]["status"] == "refunded"
    assert (
        items[0]["sale"]["refund_status"]
        == "refunded"
    )
    assert items[0]["is_returned"] is True


def test_sales_history_filters_sale_dates(client):
    response = client.get(
        (
            f"/api/products/{PRODUCT_ID}/history/sales"
            "?date_from=2026-08-09"
            "&date_to=2026-08-09"
        )
    )

    assert response.status_code == 200

    ids = [
        item["sale"]["id"]
        for item in response.get_json()["items"]
    ]

    assert ids == ["sale-refunded"]


def test_sales_history_filters_warehouse(client):
    add_sale(
        "sale-front-store",
        sale_number="SALE-FRONT",
        sale_date=datetime(
            2026,
            8,
            13,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        warehouse_id=SECOND_WAREHOUSE_ID,
        till_id=SECOND_TILL_ID,
        batch_id=None,
    )
    db.session.commit()

    response = client.get(
        (
            f"/api/products/{PRODUCT_ID}/history/sales"
            f"?warehouse_id={SECOND_WAREHOUSE_ID}"
        )
    )

    assert response.status_code == 200

    assert [
        item["sale"]["id"]
        for item in response.get_json()["items"]
    ] == ["sale-front-store"]


def test_sales_history_is_paginated(client):
    response = client.get(
        (
            f"/api/products/{PRODUCT_ID}/history/sales"
            "?page=1&per_page=1"
        )
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert [
        item["sale"]["id"]
        for item in payload["items"]
    ] == ["sale-new"]

    assert payload["pagination"] == {
        "page": 1,
        "per_page": 1,
        "total": 3,
        "pages": 3,
        "has_prev": False,
        "has_next": True,
    }


def test_sales_history_rejects_cross_tenant_product(
    client,
):
    response = client.get(
        (
            "/api/products/other-tenant-product/"
            "history/sales"
        )
    )

    assert response.status_code == 404
    assert response.get_json() == {
        "ok": False,
        "error": "Product not found.",
    }


def test_sales_history_requires_branch(
    client,
    identity: SimpleNamespace,
):
    identity.branch_id = None

    response = client.get(
        f"/api/products/{PRODUCT_ID}/history/sales"
    )

    assert response.status_code == 400
    assert "branch" in response.get_json()["error"]


def test_sales_price_trend_is_complete_chronological_and_normalized(
    client,
):
    response = client.get(
        (
            f"/api/products/{PRODUCT_ID}"
            "/history/sales/price-trend"
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
        "sale-old",
        "sale-refunded",
        "sale-new",
    ]

    assert [
        item["value"]
        for item in items
    ] == [
        "10.000000",
        "12.000000",
        "12.000000",
    ]

    assert items[0]["source"] == {
        "type": "sale",
        "id": "sale-old",
        "number": "SALE-OLD",
    }

    refunded = items[1]

    assert refunded["status"] == "refunded"
    assert refunded["refund_status"] == "refunded"
    assert refunded["is_returned"] is True


def test_sales_price_trend_filters_date_and_warehouse(
    client,
):
    add_sale(
        "sale-front-trend",
        sale_number="SALE-FRONT-TREND",
        sale_date=datetime(
            2026,
            8,
            13,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        warehouse_id=SECOND_WAREHOUSE_ID,
        till_id=SECOND_TILL_ID,
        batch_id=None,
        unit_price=Decimal("150.00"),
    )
    db.session.commit()

    response = client.get(
        (
            f"/api/products/{PRODUCT_ID}"
            "/history/sales/price-trend"
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
    ] == ["sale-front-trend"]

    assert items[0]["value"] == "15.000000"


def test_sales_price_trend_rejects_cross_tenant_product(
    client,
):
    response = client.get(
        (
            "/api/products/other-tenant-product/"
            "history/sales/price-trend"
        )
    )

    assert response.status_code == 404
    assert response.get_json() == {
        "ok": False,
        "error": "Product not found.",
    }


def test_sales_price_trend_requires_branch(
    client,
    identity: SimpleNamespace,
):
    identity.branch_id = None

    response = client.get(
        (
            f"/api/products/{PRODUCT_ID}"
            "/history/sales/price-trend"
        )
    )

    assert response.status_code == 400
    assert "branch" in response.get_json()["error"]


def test_sales_history_requires_sales_read(
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

    response = app_context.test_client().get(
        f"/api/products/{PRODUCT_ID}/history/sales"
    )

    assert response.status_code == 403
    assert (
        captured["kwargs"]["permission"]
        == "sales.read"
    )
