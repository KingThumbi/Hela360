from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from flask import Flask

from app.api.errors import register_error_handlers
from app.api.sales import bp as sales_bp
from app.auth.exceptions import PermissionDeniedError
from app.extensions import db
from app.models import (
    Branch,
    Customer,
    Product,
    Sale,
    Tenant,
    Till,
    TillShift,
    User,
    Warehouse,
)


TENANT_ID = "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa"
OTHER_TENANT_ID = "bbbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb"
BRANCH_ID = "cccccccc-cccc-4ccc-cccc-cccccccccccc"
OTHER_BRANCH_ID = "dddddddd-dddd-4ddd-dddd-dddddddddddd"
USER_ID = "eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee"
CUSTOMER_ID = "f1f1f1f1-f1f1-4f1f-8f1f-f1f1f1f1f1f1"
WAREHOUSE_ID = "a8888888-a888-4888-8888-a88888888888"
TILL_ID = "a9999999-a999-4999-8999-a99999999999"
SHIFT_ID = "abababab-abab-4aba-abab-abababababab"


@pytest.fixture()
def app_context():
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TESTING=True,
    )
    db.init_app(app)
    app.register_blueprint(sales_bp, url_prefix="/api")
    register_error_handlers(app)

    with app.app_context():
        Tenant.__table__.create(db.engine)
        Branch.__table__.create(db.engine)
        User.__table__.create(db.engine)
        Customer.__table__.create(db.engine)
        Product.__table__.create(db.engine)
        Warehouse.__table__.create(db.engine)
        Till.__table__.create(db.engine)
        TillShift.__table__.create(db.engine)
        Sale.__table__.create(db.engine)

        seed_reference_data()
        seed_sales()

        yield app

        db.session.remove()
        Sale.__table__.drop(db.engine)
        TillShift.__table__.drop(db.engine)
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
        "app.api.sales._current_identity",
        lambda: identity,
    )
    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.authorization_service.authorize",
        lambda *args, **kwargs: None,
    )

    return app_context.test_client()


def seed_reference_data():
    db.session.add_all(
        [
            Tenant(
                id=TENANT_ID,
                legal_name="Tenant 1",
                display_name="Tenant 1",
            ),
            Tenant(
                id=OTHER_TENANT_ID,
                legal_name="Tenant 2",
                display_name="Tenant 2",
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
                first_name="Amina",
                last_name="Cashier",
                email="amina@example.test",
                username="amina",
                password_hash="hash",
            ),
            Customer(
                id=CUSTOMER_ID,
                tenant_id=TENANT_ID,
                customer_number="CUST-001",
                first_name="Jane",
                last_name="Doe",
                phone="+254700000003",
            ),
            Product(
                id="product-1",
                tenant_id=TENANT_ID,
                internal_sku="SKU-001",
                name="Product 1",
            ),
            Warehouse(
                id=WAREHOUSE_ID,
                tenant_id=TENANT_ID,
                branch_id=BRANCH_ID,
                code="WH-1",
                name="Main Warehouse",
            ),
            Till(
                id=TILL_ID,
                tenant_id=TENANT_ID,
                branch_id=BRANCH_ID,
                warehouse_id=WAREHOUSE_ID,
                code="TILL-1",
                name="Front Till",
            ),
            TillShift(
                id=SHIFT_ID,
                tenant_id=TENANT_ID,
                branch_id=BRANCH_ID,
                till_id=TILL_ID,
                cashier_id=USER_ID,
                status="closed",
                opening_float=Decimal("100.00"),
                opened_at=datetime(2026, 8, 9, 8, 0, tzinfo=timezone.utc),
                closed_at=datetime(2026, 8, 9, 16, 0, tzinfo=timezone.utc),
            ),
        ]
    )
    db.session.commit()


def seed_sales():
    db.session.add_all(
        [
            make_sale(
                sale_id="sale-old",
                sale_number="SALE-OLD",
                sale_date=datetime(2026, 8, 7, 9, 0, tzinfo=timezone.utc),
                total=Decimal("100.00"),
                customer_id=CUSTOMER_ID,
            ),
            make_sale(
                sale_id="sale-new",
                sale_number="SALE-NEW",
                sale_date=datetime(2026, 8, 9, 11, 0, tzinfo=timezone.utc),
                total=Decimal("250.00"),
                customer_id=None,
            ),
            make_sale(
                sale_id="sale-refunded",
                sale_number="SALE-REF",
                sale_date=datetime(2026, 8, 8, 12, 0, tzinfo=timezone.utc),
                total=Decimal("150.00"),
                customer_id=CUSTOMER_ID,
                status="refunded",
                refund_status="refunded",
                refunded_amount=Decimal("150.00"),
            ),
            make_sale(
                sale_id="sale-other-branch",
                sale_number="SALE-BRANCH",
                sale_date=datetime(2026, 8, 9, 12, 0, tzinfo=timezone.utc),
                total=Decimal("999.00"),
                branch_id=OTHER_BRANCH_ID,
                customer_id=None,
            ),
            make_sale(
                sale_id="sale-other-tenant",
                sale_number="SALE-TENANT",
                sale_date=datetime(2026, 8, 9, 13, 0, tzinfo=timezone.utc),
                total=Decimal("999.00"),
                tenant_id=OTHER_TENANT_ID,
                customer_id=None,
            ),
        ]
    )
    db.session.commit()


def make_sale(
    *,
    sale_id: str,
    sale_number: str,
    sale_date: datetime,
    total: Decimal,
    customer_id: str | None,
    tenant_id: str = TENANT_ID,
    branch_id: str = BRANCH_ID,
    status: str = "paid",
    refund_status: str = "not_refunded",
    refunded_amount: Decimal = Decimal("0.00"),
) -> Sale:
    return Sale(
        id=sale_id,
        tenant_id=tenant_id,
        branch_id=branch_id,
        till_id=TILL_ID,
        till_shift_id=SHIFT_ID,
        warehouse_id=WAREHOUSE_ID,
        customer_id=customer_id,
        sale_number=sale_number,
        sale_date=sale_date,
        status=status,
        subtotal=total,
        discount_amount=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        total_amount=total,
        paid_amount=total,
        balance_due=Decimal("0.00"),
        cashier_id=USER_ID,
        refund_status=refund_status,
        refunded_amount=refunded_amount,
        created_at=sale_date,
        updated_at=sale_date,
    )


def test_sales_history_requires_authentication(
    app_context,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.get_current_identity",
        lambda: None,
    )

    response = app_context.test_client().get("/api/sales")

    assert response.status_code == 401


def test_sales_history_enforces_sales_read_permission(
    app_context,
    identity: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.get_current_identity",
        lambda: identity,
    )
    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.authorization_service.authorize",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            PermissionDeniedError()
        ),
    )

    response = app_context.test_client().get("/api/sales")

    assert response.status_code == 403


def test_sales_history_uses_sales_read_permission(
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
        "app.api.sales._current_identity",
        lambda: identity,
    )

    def authorize(*args, **kwargs):
        captured["permission"] = kwargs.get("permission")

    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.authorization_service.authorize",
        authorize,
    )

    response = app_context.test_client().get("/api/sales")

    assert response.status_code == 200
    assert captured["permission"] == "sales.read"


def test_sales_history_returns_current_branch_newest_first(client):
    response = client.get("/api/sales")

    assert response.status_code == 200
    assert response.json["ok"] is True
    assert response.json["pagination"] == {
        "page": 1,
        "per_page": 25,
        "total": 3,
        "pages": 1,
        "has_prev": False,
        "has_next": False,
    }
    assert [item["sale_number"] for item in response.json["items"]] == [
        "SALE-NEW",
        "SALE-REF",
        "SALE-OLD",
    ]
    assert all(
        item["sale_number"] not in {"SALE-BRANCH", "SALE-TENANT"}
        for item in response.json["items"]
    )


def test_sales_history_projects_sale_summary(client):
    response = client.get("/api/sales?search=SALE-OLD")

    assert response.status_code == 200
    item = response.json["items"][0]
    assert item["id"] == "sale-old"
    assert item["sale_number"] == "SALE-OLD"
    assert item["status"] == "paid"
    assert item["customer"] == {
        "id": CUSTOMER_ID,
        "customer_number": "CUST-001",
        "full_name": "Jane Doe",
        "phone": "+254700000003",
    }
    assert item["cashier"] == {
        "id": USER_ID,
        "name": "Amina Cashier",
        "username": "amina",
    }
    assert item["till"] == {
        "id": TILL_ID,
        "code": "TILL-1",
        "name": "Front Till",
    }
    assert item["total_amount"] == "100.00"
    assert item["paid_amount"] == "100.00"
    assert item["balance_due"] == "0.00"
    assert item["refund_status"] == "not_refunded"


def test_sales_history_paginates_server_side(client):
    response = client.get("/api/sales?page=2&per_page=2")

    assert response.status_code == 200
    assert response.json["pagination"] == {
        "page": 2,
        "per_page": 2,
        "total": 3,
        "pages": 2,
        "has_prev": True,
        "has_next": False,
    }
    assert [item["sale_number"] for item in response.json["items"]] == [
        "SALE-OLD",
    ]


def test_sales_history_filters_by_sale_number_customer_and_status(client):
    sale_search = client.get("/api/sales?search=SALE-REF")
    customer_search = client.get("/api/sales?search=Jane")
    status_search = client.get("/api/sales?status=refunded")

    assert [item["sale_number"] for item in sale_search.json["items"]] == [
        "SALE-REF"
    ]
    assert [item["sale_number"] for item in customer_search.json["items"]] == [
        "SALE-REF",
        "SALE-OLD",
    ]
    assert [item["sale_number"] for item in status_search.json["items"]] == [
        "SALE-REF"
    ]


def test_sales_history_filters_by_inclusive_sale_dates(client):
    response = client.get("/api/sales?date_from=2026-08-08&date_to=2026-08-08")

    assert response.status_code == 200
    assert [item["sale_number"] for item in response.json["items"]] == [
        "SALE-REF"
    ]


def test_sales_history_rejects_invalid_filters(client):
    bad_page = client.get("/api/sales?page=0")
    bad_date = client.get("/api/sales?date_from=not-a-date")
    bad_status = client.get("/api/sales?status=cancelled")

    assert bad_page.status_code == 400
    assert bad_page.json["error"]["message"] == "page must be a positive integer."
    assert bad_date.status_code == 400
    assert (
        bad_date.json["error"]["message"]
        == "date_from must be a valid date in YYYY-MM-DD format."
    )
    assert bad_status.status_code == 400
    assert bad_status.json["error"]["message"] == "status is not supported."


def test_sales_history_returns_empty_result_for_no_matches(client):
    response = client.get("/api/sales?search=missing")

    assert response.status_code == 200
    assert response.json["items"] == []
    assert response.json["pagination"]["total"] == 0
