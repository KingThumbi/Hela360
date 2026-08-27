from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from flask import Flask

from app.api.errors import register_error_handlers
from app.api.sales import bp as sales_bp
from app.extensions import db
from app.models import (
    Branch,
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
from app.models.pos import SaleRefund, SaleRefundItem
from app.services.tenant.pos.refund_service import (
    RefundError,
    RefundService,
)

SESSION_ID = "98989898-9898-4989-8989-989898989898"
OTHER_SESSION_ID = "78787878-7878-4787-8787-787878787878"
SHIFT_ID = "a1111111-a111-4111-8111-a11111111111"


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
        SaleRefund.__table__.create(db.engine)
        SaleRefundItem.__table__.create(db.engine)

        db.session.add_all(
            [
                Tenant(
                    id="tenant-1",
                    legal_name="Tenant 1",
                    display_name="Tenant 1",
                ),
                Branch(
                    id="branch-1",
                    tenant_id="tenant-1",
                    code="BR-1",
                    name="Branch 1",
                ),
                Branch(
                    id="branch-2",
                    tenant_id="tenant-1",
                    code="BR-2",
                    name="Branch 2",
                ),
                User(
                    id="user-1",
                    tenant_id="tenant-1",
                    branch_id="branch-1",
                    first_name="Cashier",
                    email="cashier@example.test",
                    username="cashier",
                    password_hash="hash",
                ),
                Product(
                    id="product-1",
                    tenant_id="tenant-1",
                    internal_sku="SKU-001",
                    name="Paracetamol",
                ),
                Warehouse(
                    id="warehouse-1",
                    tenant_id="tenant-1",
                    branch_id="branch-1",
                    code="WH-1",
                    name="Main Warehouse",
                ),
                Till(
                    id="till-1",
                    tenant_id="tenant-1",
                    branch_id="branch-1",
                    code="TILL-1",
                    name="Front Till",
                ),
                PaymentMethod(
                    id="payment-method-1",
                    tenant_id="tenant-1",
                    code="cash",
                    name="Cash",
                    method_type="cash",
                ),
            ]
        )
        db.session.commit()

        yield app

        db.session.remove()
        SaleRefundItem.__table__.drop(db.engine)
        SaleRefund.__table__.drop(db.engine)
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
        User.__table__.drop(db.engine)
        Branch.__table__.drop(db.engine)
        Tenant.__table__.drop(db.engine)


@pytest.fixture()
def identity():
    return SimpleNamespace(
        user_id="user-1",
        tenant_id="tenant-1",
        branch_id="branch-1",
        session_id=SESSION_ID,
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


def add_open_shift(
    *,
    active_session_id: str = SESSION_ID,
) -> TillShift:
    now = datetime.now(timezone.utc)

    shift = TillShift(
        id=SHIFT_ID,
        tenant_id="tenant-1",
        branch_id="branch-1",
        till_id="till-1",
        cashier_id="user-1",
        active_session_id=active_session_id,
        status="open",
        opening_float=Decimal("50.00"),
        opened_at=now,
        created_at=now,
        updated_at=now,
    )

    db.session.add(shift)
    db.session.commit()

    return shift


def add_paid_sale(branch_id: str = "branch-1") -> Sale:
    now = datetime.now(timezone.utc)
    sale = Sale(
        id="sale-1",
        tenant_id="tenant-1",
        branch_id=branch_id,
        till_id="till-1",
        warehouse_id="warehouse-1",
        sale_number="SALE-001",
        sale_date=now,
        status="paid",
        subtotal=Decimal("100.00"),
        discount_amount=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("100.00"),
        paid_amount=Decimal("100.00"),
        balance_due=Decimal("0.00"),
        cashier_id="user-1",
        created_at=now,
        updated_at=now,
    )
    item = SaleItem(
        id="sale-item-1",
        sale_id="sale-1",
        product_id="product-1",
        quantity=Decimal("2.0000"),
        unit_price=Decimal("50.00"),
        discount_amount=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        line_total=Decimal("100.00"),
    )
    payment = SalePayment(
        id="sale-payment-1",
        sale_id="sale-1",
        payment_method_id="payment-method-1",
        amount=Decimal("100.00"),
        reference_number="RCPT-001",
        paid_at=now,
        received_by="user-1",
    )
    db.session.add_all([sale, item, payment])
    db.session.commit()
    return sale


def test_sales_checkout_requires_authenticated_branch(
    client,
    identity: SimpleNamespace,
):
    identity.branch_id = None

    response = client.post(
        "/api/sales/checkout",
        json={
            "warehouse_id": "warehouse-1",
            "till_id": "till-1",
            "items": [
                {
                    "product_id": "product-1",
                    "quantity": "1",
                    "unit_price": "10.00",
                }
            ],
            "payments": [
                {
                    "payment_method_id": "payment-method-1",
                    "amount": "10.00",
                }
            ],
        },
    )

    assert response.status_code == 400
    assert response.json == {
        "ok": False,
        "error": "Authenticated user is not assigned to a branch.",
    }


def test_refund_service_accepts_shift_owned_by_current_session(
    app_context,
    identity: SimpleNamespace,
):
    shift = add_open_shift(
        active_session_id=SESSION_ID,
    )

    service = RefundService(db.session)

    resolved = service._require_open_till_shift(
        identity,
    )

    assert resolved.id == shift.id
    assert resolved.active_session_id == SESSION_ID


def test_refund_service_rejects_shift_owned_by_another_session(
    app_context,
    identity: SimpleNamespace,
):
    add_open_shift(
        active_session_id=OTHER_SESSION_ID,
    )

    service = RefundService(db.session)

    with pytest.raises(RefundError) as exc_info:
        service._require_open_till_shift(
            identity,
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.message == (
        "This till shift is active on another session."
    )


def test_sales_refund_route_processes_partial_refund(
    client,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "app.services.tenant.pos.refund_service.RefundService._require_open_till_shift",
        lambda self, identity: SimpleNamespace(
            id="a1111111-a111-4111-8111-a11111111111"
        ),
    )
    add_paid_sale()

    response = client.post(
        "/api/sales/sale-1/refund",
        json={
            "items": [
                {
                    "sale_item_id": "sale-item-1",
                    "quantity": "1",
                    "return_to_stock": False,
                }
            ],
            "reason": "Customer return",
        },
    )

    assert response.status_code == 201
    assert response.json["ok"] is True
    assert response.json["refund"]["status"] == "posted"
    assert response.json["refund"]["refund_total_amount"] == "50.00"
    assert response.json["refund"]["stock_returned"] is False

    sale = db.session.get(Sale, "sale-1")
    refund_payments = (
        db.session.query(SalePayment)
        .filter(SalePayment.sale_id == "sale-1")
        .order_by(SalePayment.amount.asc())
        .all()
    )

    assert sale.status == "partially_refunded"
    assert sale.refund_status == "partially_refunded"
    assert sale.refunded_amount == Decimal("50.00")
    assert len(refund_payments) == 2
    assert refund_payments[0].amount == Decimal("-50.00")


def test_sales_refund_route_enforces_branch_isolation(client):
    add_paid_sale(branch_id="branch-2")

    response = client.post(
        "/api/sales/sale-1/refund",
        json={
            "items": [
                {
                    "sale_item_id": "sale-item-1",
                    "quantity": "1",
                }
            ],
        },
    )

    assert response.status_code == 403
    assert response.json == {
        "ok": False,
        "error": "You cannot refund sales from another branch.",
    }
