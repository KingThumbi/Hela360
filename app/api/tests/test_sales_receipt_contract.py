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
    PaymentMethod,
    Product,
    ProductUnit,
    Sale,
    SaleItem,
    SalePayment,
    Tenant,
    UnitOfMeasure,
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
SALE_ID = "11111111-1111-4111-8111-111111111111"
WALK_IN_SALE_ID = "22222222-2222-4222-8222-222222222222"
OTHER_TENANT_SALE_ID = "33333333-3333-4333-8333-333333333333"
OTHER_BRANCH_SALE_ID = "44444444-4444-4444-8444-444444444444"
CUSTOMER_ID = "55555555-5555-4555-8555-555555555555"
PRODUCT_ID = "66666666-6666-4666-8666-666666666666"
SECOND_PRODUCT_ID = "77777777-7777-4777-8777-777777777777"
WAREHOUSE_ID = "88888888-8888-4888-8888-888888888888"
TILL_ID = "a9999999-a999-4999-8999-a99999999999"
SHIFT_ID = "abababab-abab-4aba-abab-abababababab"
CASH_PAYMENT_METHOD_ID = "12121212-1212-4121-8121-121212121212"
MPESA_PAYMENT_METHOD_ID = "23232323-2323-4232-8232-232323232323"


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
        UnitOfMeasure.__table__.create(db.engine)
        Product.__table__.create(db.engine)
        ProductUnit.__table__.create(db.engine)
        Warehouse.__table__.create(db.engine)
        Till.__table__.create(db.engine)
        TillShift.__table__.create(db.engine)
        PaymentMethod.__table__.create(db.engine)
        Sale.__table__.create(db.engine)
        SaleItem.__table__.create(db.engine)
        SalePayment.__table__.create(db.engine)

        seed_reference_data()
        seed_sales()

        yield app

        db.session.remove()
        SalePayment.__table__.drop(db.engine)
        SaleItem.__table__.drop(db.engine)
        Sale.__table__.drop(db.engine)
        PaymentMethod.__table__.drop(db.engine)
        TillShift.__table__.drop(db.engine)
        Till.__table__.drop(db.engine)
        Warehouse.__table__.drop(db.engine)
        ProductUnit.__table__.drop(db.engine)
        Product.__table__.drop(db.engine)
        UnitOfMeasure.__table__.drop(db.engine)
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
                legal_name="Hela Pharmacy Limited",
                display_name="Hela Pharmacy",
                phone="+254700000001",
                email="hello@example.test",
                base_currency="KES",
            ),
            Tenant(
                id=OTHER_TENANT_ID,
                legal_name="Other Tenant",
                display_name="Other Tenant",
            ),
            Branch(
                id=BRANCH_ID,
                tenant_id=TENANT_ID,
                code="CBD",
                name="CBD Branch",
                phone="+254700000002",
                email="cbd@example.test",
                address_line1="Moi Avenue",
                city="Nairobi",
                country="Kenya",
            ),
            Branch(
                id=OTHER_BRANCH_ID,
                tenant_id=TENANT_ID,
                code="WEST",
                name="West Branch",
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
            PaymentMethod(
                id=CASH_PAYMENT_METHOD_ID,
                tenant_id=TENANT_ID,
                code="cash",
                name="Cash",
                method_type="cash",
            ),
            PaymentMethod(
                id=MPESA_PAYMENT_METHOD_ID,
                tenant_id=TENANT_ID,
                code="mpesa",
                name="M-Pesa",
                method_type="mobile_money",
            ),
        ]
    )
    db.session.commit()


def seed_sales():
    now = datetime(2026, 8, 9, 10, 30, tzinfo=timezone.utc)
    db.session.add_all(
        [
            make_sale(
                sale_id=SALE_ID,
                sale_number="SALE-001",
                customer_id=CUSTOMER_ID,
                subtotal=Decimal("250.00"),
                total=Decimal("250.00"),
                paid=Decimal("250.00"),
                balance=Decimal("0.00"),
                sale_date=now,
            ),
            make_sale(
                sale_id=WALK_IN_SALE_ID,
                sale_number="SALE-002",
                customer_id=None,
                subtotal=Decimal("50.00"),
                total=Decimal("60.00"),
                paid=Decimal("40.00"),
                balance=Decimal("20.00"),
                sale_date=now,
            ),
            make_sale(
                sale_id=OTHER_TENANT_SALE_ID,
                sale_number="SALE-003",
                tenant_id=OTHER_TENANT_ID,
                customer_id=None,
                subtotal=Decimal("10.00"),
                total=Decimal("10.00"),
                paid=Decimal("10.00"),
                balance=Decimal("0.00"),
                sale_date=now,
            ),
            make_sale(
                sale_id=OTHER_BRANCH_SALE_ID,
                sale_number="SALE-004",
                branch_id=OTHER_BRANCH_ID,
                customer_id=None,
                subtotal=Decimal("10.00"),
                total=Decimal("10.00"),
                paid=Decimal("10.00"),
                balance=Decimal("0.00"),
                sale_date=now,
            ),
        ]
    )
    db.session.flush()
    db.session.add_all(
        [
            SaleItem(
                id="sale-item-1",
                sale_id=SALE_ID,
                product_id=PRODUCT_ID,
                quantity=Decimal("2.0000"),
                unit_price=Decimal("100.00"),
                discount_amount=Decimal("0.00"),
                tax_amount=Decimal("0.00"),
                line_total=Decimal("200.00"),
            ),
            SaleItem(
                id="sale-item-2",
                sale_id=SALE_ID,
                product_id=SECOND_PRODUCT_ID,
                quantity=Decimal("1.0000"),
                unit_price=Decimal("50.00"),
                discount_amount=Decimal("0.00"),
                tax_amount=Decimal("0.00"),
                line_total=Decimal("50.00"),
            ),
            SaleItem(
                id="sale-item-walk-in",
                sale_id=WALK_IN_SALE_ID,
                product_id=SECOND_PRODUCT_ID,
                quantity=Decimal("1.0000"),
                unit_price=Decimal("60.00"),
                discount_amount=Decimal("0.00"),
                tax_amount=Decimal("0.00"),
                line_total=Decimal("60.00"),
            ),
            SalePayment(
                id="sale-payment-cash",
                sale_id=SALE_ID,
                payment_method_id=CASH_PAYMENT_METHOD_ID,
                amount=Decimal("150.00"),
                reference_number="CASH-001",
                paid_at=datetime(2026, 8, 9, 10, 31, tzinfo=timezone.utc),
                received_by=USER_ID,
            ),
            SalePayment(
                id="sale-payment-mpesa",
                sale_id=SALE_ID,
                payment_method_id=MPESA_PAYMENT_METHOD_ID,
                amount=Decimal("100.00"),
                reference_number="MPESA-001",
                paid_at=datetime(2026, 8, 9, 10, 32, tzinfo=timezone.utc),
                received_by=USER_ID,
            ),
            SalePayment(
                id="sale-payment-partial",
                sale_id=WALK_IN_SALE_ID,
                payment_method_id=CASH_PAYMENT_METHOD_ID,
                amount=Decimal("40.00"),
                reference_number=None,
                paid_at=datetime(2026, 8, 9, 10, 33, tzinfo=timezone.utc),
                received_by=USER_ID,
            ),
        ]
    )
    db.session.commit()


def make_sale(
    *,
    sale_id: str,
    sale_number: str,
    subtotal: Decimal,
    total: Decimal,
    paid: Decimal,
    balance: Decimal,
    sale_date: datetime,
    tenant_id: str = TENANT_ID,
    branch_id: str = BRANCH_ID,
    customer_id: str | None,
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
        status="paid" if balance == Decimal("0.00") else "partially_paid",
        subtotal=subtotal,
        discount_amount=Decimal("0.00"),
        tax_amount=total - subtotal,
        total_amount=total,
        paid_amount=paid,
        balance_due=balance,
        cashier_id=USER_ID,
        created_at=sale_date,
        updated_at=sale_date,
    )


def test_receipt_endpoint_requires_authentication(
    app_context,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.get_current_identity",
        lambda: None,
    )

    response = app_context.test_client().get(
        f"/api/sales/{SALE_ID}/receipt"
    )

    assert response.status_code == 401


def test_receipt_endpoint_enforces_permission(
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

    response = app_context.test_client().get(
        f"/api/sales/{SALE_ID}/receipt"
    )

    assert response.status_code == 403


def test_receipt_endpoint_returns_persisted_sale_projection(client):
    response = client.get(f"/api/sales/{SALE_ID}/receipt")

    assert response.status_code == 200
    assert response.json["ok"] is True

    receipt = response.json["receipt"]
    assert receipt["sale"]["id"] == SALE_ID
    assert receipt["sale"]["sale_number"] == "SALE-001"
    assert receipt["seller"]["display_name"] == "Hela Pharmacy"
    assert receipt["seller"]["currency"] == "KES"
    assert receipt["branch"]["code"] == "CBD"
    assert receipt["customer"] == {
        "id": CUSTOMER_ID,
        "customer_number": "CUST-001",
        "full_name": "Jane Doe",
        "phone": "+254700000003",
    }
    assert receipt["cashier"]["name"] == "Amina Cashier"
    assert receipt["till"] == {
        "id": TILL_ID,
        "code": "TILL-1",
        "name": "Front Till",
    }
    assert receipt["till_shift"]["id"] == str(SHIFT_ID)
    assert receipt["totals"] == {
        "subtotal": "250.00",
        "discount_amount": "0.00",
        "tax_amount": "0.00",
        "total_amount": "250.00",
        "paid_amount": "250.00",
        "balance_due": "0.00",
        "currency": "KES",
    }


def test_receipt_endpoint_uses_sales_read_permission(
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

    response = app_context.test_client().get(
        f"/api/sales/{SALE_ID}/receipt"
    )

    assert response.status_code == 200
    assert captured["permission"] == "sales.read"


def test_receipt_endpoint_projects_lines_and_split_payments(client):
    response = client.get(f"/api/sales/{SALE_ID}/receipt")

    assert response.status_code == 200
    receipt = response.json["receipt"]

    assert receipt["items"] == [
        {
            "id": "sale-item-1",
            "product_id": PRODUCT_ID,
            "description": "Paracetamol 500mg",
            "sku": "PARA-500",
            "quantity": "2.0000",
            "unit_price": "100.00",
            "discount_amount": "0.00",
            "tax_amount": "0.00",
            "line_total": "200.00",
        },
        {
            "id": "sale-item-2",
            "product_id": SECOND_PRODUCT_ID,
            "description": "ORS Sachet",
            "sku": "ORS-001",
            "quantity": "1.0000",
            "unit_price": "50.00",
            "discount_amount": "0.00",
            "tax_amount": "0.00",
            "line_total": "50.00",
        },
    ]
    assert [
        payment["payment_method"]["name"]
        for payment in receipt["payments"]
    ] == ["Cash", "M-Pesa"]
    assert [
        payment["amount"]
        for payment in receipt["payments"]
    ] == ["150.00", "100.00"]
    assert [
        payment["reference"]
        for payment in receipt["payments"]
    ] == ["CASH-001", "MPESA-001"]


def test_receipt_endpoint_handles_walk_in_and_partial_payment(client):
    response = client.get(f"/api/sales/{WALK_IN_SALE_ID}/receipt")

    assert response.status_code == 200
    receipt = response.json["receipt"]
    assert receipt["customer"] is None
    assert receipt["totals"]["total_amount"] == "60.00"
    assert receipt["totals"]["paid_amount"] == "40.00"
    assert receipt["totals"]["balance_due"] == "20.00"


def test_receipt_endpoint_rejects_cross_tenant_sale(client):
    response = client.get(f"/api/sales/{OTHER_TENANT_SALE_ID}/receipt")

    assert response.status_code == 404
    assert response.json == {
        "ok": False,
        "error": {
            "code": "NOT_FOUND",
            "message": "Sale receipt not found.",
        },
    }


def test_receipt_endpoint_rejects_cross_branch_sale(client):
    response = client.get(f"/api/sales/{OTHER_BRANCH_SALE_ID}/receipt")

    assert response.status_code == 404
    assert response.json["error"]["message"] == "Sale receipt not found."


def test_receipt_endpoint_rejects_unknown_sale(client):
    response = client.get(
        "/api/sales/99999999-9999-4999-8999-999999999999/receipt"
    )

    assert response.status_code == 404
    assert response.json["error"]["message"] == "Sale receipt not found."
