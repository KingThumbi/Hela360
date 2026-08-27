from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from flask import Flask

from app.api.errors import register_error_handlers
from app.api.sales import bp as sales_bp
from app.extensions import db
from app.models import (
    Branch,
    Customer,
    DispensingRecord,
    InventoryBatch,
    InventoryMovement,
    PaymentMethod,
    Permission,
    Product,
    ProductUnit,
    Role,
    RolePermission,
    Sale,
    SaleItem,
    SalePayment,
    StockBalance,
    Tenant,
    UnitOfMeasure,
    Till,
    TillShift,
    User,
    UserPermission,
    UserRole,
    UserSession,
    RefreshToken,
    PasswordResetToken,
    Warehouse,
)
from app.models.pos import SaleRefund, SaleRefundItem


TENANT_ID = "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa"
BRANCH_ID = "bbbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb"
USER_ID = "cccccccc-cccc-4ccc-cccc-cccccccccccc"
CUSTOMER_ID = "dddddddd-dddd-4ddd-dddd-dddddddddddd"
WAREHOUSE_ID = "eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee"
TILL_ID = "ffffffff-ffff-4fff-ffff-ffffffffffff"
SHIFT_ID = "abababab-abab-4aba-abab-abababababab"
SESSION_ID = "98989898-9898-4989-8989-989898989898"
PAYMENT_METHOD_ID = "22222222-2222-4222-8222-222222222222"
ORDINARY_PRODUCT_ID = "33333333-3333-4333-8333-333333333333"
RX_PRODUCT_ID = "44444444-4444-4444-8444-444444444444"
SECOND_RX_PRODUCT_ID = "55555555-5555-4555-8555-555555555555"
ORDINARY_BATCH_ID = "66666666-6666-4666-8666-666666666666"
RX_BATCH_ID = "77777777-7777-4777-8777-777777777777"
SECOND_RX_BATCH_ID = "88888888-8888-4888-8888-888888888888"


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
        Role.__table__.create(db.engine)
        Permission.__table__.create(db.engine)
        RolePermission.__table__.create(db.engine)
        UserRole.__table__.create(db.engine)
        UserPermission.__table__.create(db.engine)
        UserSession.__table__.create(db.engine)
        RefreshToken.__table__.create(db.engine)
        PasswordResetToken.__table__.create(db.engine)
        Customer.__table__.create(db.engine)
        UnitOfMeasure.__table__.create(db.engine)
        Product.__table__.create(db.engine)
        ProductUnit.__table__.create(db.engine)
        Warehouse.__table__.create(db.engine)
        InventoryBatch.__table__.create(db.engine)
        Till.__table__.create(db.engine)
        TillShift.__table__.create(db.engine)
        PaymentMethod.__table__.create(db.engine)
        Sale.__table__.create(db.engine)
        SaleItem.__table__.create(db.engine)
        DispensingRecord.__table__.create(db.engine)
        SalePayment.__table__.create(db.engine)
        SaleRefund.__table__.create(db.engine)
        SaleRefundItem.__table__.create(db.engine)
        StockBalance.__table__.create(db.engine)
        InventoryMovement.__table__.create(db.engine)

        seed_reference_data()

        yield app

        db.session.remove()
        InventoryMovement.__table__.drop(db.engine)
        StockBalance.__table__.drop(db.engine)
        SaleRefundItem.__table__.drop(db.engine)
        SaleRefund.__table__.drop(db.engine)
        SalePayment.__table__.drop(db.engine)
        DispensingRecord.__table__.drop(db.engine)
        SaleItem.__table__.drop(db.engine)
        Sale.__table__.drop(db.engine)
        PaymentMethod.__table__.drop(db.engine)
        TillShift.__table__.drop(db.engine)
        Till.__table__.drop(db.engine)
        InventoryBatch.__table__.drop(db.engine)
        Warehouse.__table__.drop(db.engine)
        ProductUnit.__table__.drop(db.engine)
        Product.__table__.drop(db.engine)
        UnitOfMeasure.__table__.drop(db.engine)
        Customer.__table__.drop(db.engine)
        PasswordResetToken.__table__.drop(db.engine)
        RefreshToken.__table__.drop(db.engine)
        UserSession.__table__.drop(db.engine)
        UserPermission.__table__.drop(db.engine)
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


def seed_reference_data():
    expiry = date.today() + timedelta(days=30)
    db.session.add_all(
        [
            Tenant(
                id=TENANT_ID,
                legal_name="Tenant",
                display_name="Tenant",
            ),
            Branch(
                id=BRANCH_ID,
                tenant_id=TENANT_ID,
                code="BR-1",
                name="Branch 1",
            ),
            User(
                id=USER_ID,
                tenant_id=TENANT_ID,
                branch_id=BRANCH_ID,
                first_name="Cashier",
                email="cashier@example.test",
                username="cashier",
                password_hash="hash",
            ),
            Customer(
                id=CUSTOMER_ID,
                tenant_id=TENANT_ID,
                customer_number="CUST-001",
                first_name="Jane",
                last_name="Doe",
            ),
            UserSession(
                id=SESSION_ID,
                tenant_id=TENANT_ID,
                branch_id=BRANCH_ID,
                user_id=USER_ID,
                expires_at=(
                    datetime.now(timezone.utc)
                    + timedelta(hours=8)
                ),
                last_activity_at=datetime.now(
                    timezone.utc
                ),
            ),
            Product(
                id=ORDINARY_PRODUCT_ID,
                tenant_id=TENANT_ID,
                internal_sku="ORS-001",
                name="ORS Sachet",
                default_sale_price=Decimal("10.00"),
                track_inventory=True,
                track_batches=True,
                track_expiry=True,
                requires_prescription=False,
            ),
            Product(
                id=RX_PRODUCT_ID,
                tenant_id=TENANT_ID,
                internal_sku="AMOX-500",
                name="Amoxicillin 500mg",
                default_sale_price=Decimal("20.00"),
                track_inventory=True,
                track_batches=True,
                track_expiry=True,
                requires_prescription=True,
            ),
            Product(
                id=SECOND_RX_PRODUCT_ID,
                tenant_id=TENANT_ID,
                internal_sku="AZITH-250",
                name="Azithromycin 250mg",
                default_sale_price=Decimal("30.00"),
                track_inventory=True,
                track_batches=True,
                track_expiry=True,
                requires_prescription=True,
            ),
            Warehouse(
                id=WAREHOUSE_ID,
                tenant_id=TENANT_ID,
                branch_id=BRANCH_ID,
                code="WH-1",
                name="Main Warehouse",
            ),
            InventoryBatch(
                id=ORDINARY_BATCH_ID,
                tenant_id=TENANT_ID,
                warehouse_id=WAREHOUSE_ID,
                product_id=ORDINARY_PRODUCT_ID,
                batch_number="B-ORS",
                expiry_date=expiry,
                unit_cost=Decimal("1.00"),
                quantity_on_hand=Decimal("10.0000"),
                quantity_reserved=Decimal("0.0000"),
                status="available",
            ),
            InventoryBatch(
                id=RX_BATCH_ID,
                tenant_id=TENANT_ID,
                warehouse_id=WAREHOUSE_ID,
                product_id=RX_PRODUCT_ID,
                batch_number="B-RX",
                expiry_date=expiry,
                unit_cost=Decimal("2.00"),
                quantity_on_hand=Decimal("10.0000"),
                quantity_reserved=Decimal("0.0000"),
                status="available",
            ),
            InventoryBatch(
                id=SECOND_RX_BATCH_ID,
                tenant_id=TENANT_ID,
                warehouse_id=WAREHOUSE_ID,
                product_id=SECOND_RX_PRODUCT_ID,
                batch_number="B-RX-2",
                expiry_date=expiry,
                unit_cost=Decimal("3.00"),
                quantity_on_hand=Decimal("10.0000"),
                quantity_reserved=Decimal("0.0000"),
                status="available",
            ),
            StockBalance(
                tenant_id=TENANT_ID,
                branch_id=BRANCH_ID,
                warehouse_id=WAREHOUSE_ID,
                product_id=ORDINARY_PRODUCT_ID,
                quantity_on_hand=Decimal("10.0000"),
                quantity_available=Decimal("10.0000"),
                quantity_reserved=Decimal("0.0000"),
                avg_unit_cost=Decimal("1.00"),
            ),
            StockBalance(
                tenant_id=TENANT_ID,
                branch_id=BRANCH_ID,
                warehouse_id=WAREHOUSE_ID,
                product_id=RX_PRODUCT_ID,
                quantity_on_hand=Decimal("10.0000"),
                quantity_available=Decimal("10.0000"),
                quantity_reserved=Decimal("0.0000"),
                avg_unit_cost=Decimal("2.00"),
            ),
            StockBalance(
                tenant_id=TENANT_ID,
                branch_id=BRANCH_ID,
                warehouse_id=WAREHOUSE_ID,
                product_id=SECOND_RX_PRODUCT_ID,
                quantity_on_hand=Decimal("10.0000"),
                quantity_available=Decimal("10.0000"),
                quantity_reserved=Decimal("0.0000"),
                avg_unit_cost=Decimal("3.00"),
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
                active_session_id=SESSION_ID,
                status="open",
                opening_float=Decimal("50.00"),
                opened_at=datetime(2026, 8, 9, 8, 0, tzinfo=timezone.utc),
                created_at=datetime(2026, 8, 9, 8, 0, tzinfo=timezone.utc),
                updated_at=datetime(2026, 8, 9, 8, 0, tzinfo=timezone.utc),
            ),
            PaymentMethod(
                id=PAYMENT_METHOD_ID,
                tenant_id=TENANT_ID,
                code="cash",
                name="Cash",
                method_type="cash",
            ),
        ]
    )
    db.session.commit()


def prescription_payload(reference: str = "RX-001") -> dict:
    return {
        "prescription_reference": reference,
        "prescriber_name": "Dr Amina Njeri",
        "prescriber_registration_number": "KMPDC-12345",
        "prescription_date": "2026-08-09",
    }


def checkout_payload(
    *,
    customer_id: str | None = CUSTOMER_ID,
    items: list[dict] | None = None,
    amount: str = "20.00",
) -> dict:
    payload = {
        "till_id": TILL_ID,
        "warehouse_id": WAREHOUSE_ID,
        "items": items
        or [
            {
                "product_id": RX_PRODUCT_ID,
                "quantity": "1",
                "prescription": prescription_payload(),
            }
        ],
        "payments": [
            {
                "payment_method_id": PAYMENT_METHOD_ID,
                "amount": amount,
            }
        ],
    }
    if customer_id is not None:
        payload["customer_id"] = customer_id
    return payload


def test_ordinary_product_checkout_does_not_require_prescription(client):
    response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(
            customer_id=None,
            items=[
                {
                    "product_id": ORDINARY_PRODUCT_ID,
                    "quantity": "1",
                }
            ],
            amount="10.00",
        ),
    )

    assert response.status_code == 201, response.json
    assert db.session.query(DispensingRecord).count() == 0


def test_prescription_product_rejects_missing_prescription_context(client):
    response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(
            items=[
                {
                    "product_id": RX_PRODUCT_ID,
                    "quantity": "1",
                }
            ],
        ),
    )

    assert response.status_code == 400
    assert response.json["error"] == (
        "prescription is required for prescription products."
    )
    assert db.session.query(Sale).count() == 0
    assert db.session.query(DispensingRecord).count() == 0


def test_prescription_product_requires_customer(client):
    response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(customer_id=None),
    )

    assert response.status_code == 400
    assert response.json["error"] == (
        "customer_id is required when a sale contains prescription products."
    )
    assert db.session.query(Sale).count() == 0


def test_prescription_product_persists_sale_item_dispensing_record_and_stock(client):
    response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(),
    )

    assert response.status_code == 201, response.json
    sale_id = response.json["item"]["id"]
    sale_item_id = response.json["item"]["items"][0]["id"]

    record = db.session.query(DispensingRecord).one()
    assert record.tenant_id == TENANT_ID
    assert record.branch_id == BRANCH_ID
    assert record.customer_id == CUSTOMER_ID
    assert record.sale_id == sale_id
    assert record.sale_item_id == sale_item_id
    assert record.product_id == RX_PRODUCT_ID
    assert record.dispensed_quantity == Decimal("1.0000")
    assert record.prescription_reference == "RX-001"
    assert record.prescriber_name == "Dr Amina Njeri"
    assert record.prescriber_registration_number == "KMPDC-12345"
    assert record.prescription_date == date(2026, 8, 9)
    assert record.dispensed_by == USER_ID

    stock = (
        db.session.query(StockBalance)
        .filter(StockBalance.product_id == RX_PRODUCT_ID)
        .one()
    )
    assert stock.quantity_on_hand == Decimal("9.0000")
    assert db.session.query(InventoryMovement).count() == 1


def test_mixed_cart_requires_prescription_only_for_prescription_line(client):
    response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(
            items=[
                {
                    "product_id": ORDINARY_PRODUCT_ID,
                    "quantity": "1",
                },
                {
                    "product_id": RX_PRODUCT_ID,
                    "quantity": "1",
                    "prescription": prescription_payload(),
                },
            ],
            amount="30.00",
        ),
    )

    assert response.status_code == 201, response.json
    assert db.session.query(SaleItem).count() == 2
    assert db.session.query(DispensingRecord).count() == 1
    assert db.session.query(DispensingRecord).one().product_id == RX_PRODUCT_ID


def test_shared_prescription_reference_can_cover_multiple_sale_items(client):
    response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(
            items=[
                {
                    "product_id": RX_PRODUCT_ID,
                    "quantity": "1",
                    "prescription": prescription_payload("RX-SHARED"),
                },
                {
                    "product_id": SECOND_RX_PRODUCT_ID,
                    "quantity": "1",
                    "prescription": prescription_payload("RX-SHARED"),
                },
            ],
            amount="50.00",
        ),
    )

    assert response.status_code == 201, response.json
    records = (
        db.session.query(DispensingRecord)
        .order_by(DispensingRecord.product_id.asc())
        .all()
    )
    assert len(records) == 2
    assert {record.prescription_reference for record in records} == {"RX-SHARED"}
    assert {record.sale_item_id for record in records} == {
        item["id"] for item in response.json["item"]["items"]
    }


def test_malformed_prescription_date_is_rejected(client):
    prescription = prescription_payload()
    prescription["prescription_date"] = "09-08-2026"

    response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(
            items=[
                {
                    "product_id": RX_PRODUCT_ID,
                    "quantity": "1",
                    "prescription": prescription,
                }
            ],
        ),
    )

    assert response.status_code == 400
    assert response.json["error"] == (
        "prescription.prescription_date must be a valid date in YYYY-MM-DD format."
    )
    assert db.session.query(Sale).count() == 0


def test_dispensing_failure_rolls_back_sale_stock_and_payments(
    client,
    monkeypatch: pytest.MonkeyPatch,
):
    def fail_build_record(*args, **kwargs):
        raise ValueError("forced dispensing persistence failure")

    monkeypatch.setattr(
        "app.services.tenant.pos.dispensing_service.DispensingService.build_record",
        fail_build_record,
    )

    response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(),
    )

    assert response.status_code == 400
    assert response.json["error"] == "forced dispensing persistence failure"
    assert db.session.query(Sale).count() == 0
    assert db.session.query(SaleItem).count() == 0
    assert db.session.query(SalePayment).count() == 0
    assert db.session.query(DispensingRecord).count() == 0
    assert db.session.query(InventoryMovement).count() == 0
    stock = (
        db.session.query(StockBalance)
        .filter(StockBalance.product_id == RX_PRODUCT_ID)
        .one()
    )
    batch = db.session.get(InventoryBatch, RX_BATCH_ID)
    assert stock.quantity_on_hand == Decimal("10.0000")
    assert batch.quantity_on_hand == Decimal("10.0000")


def test_refund_keeps_dispensing_history_and_restores_stock(client):
    checkout = client.post(
        "/api/sales/checkout",
        json=checkout_payload(),
    )
    sale_id = checkout.json["item"]["id"]
    sale_item_id = checkout.json["item"]["items"][0]["id"]

    refund = client.post(
        f"/api/sales/{sale_id}/refund",
        json={
            "items": [
                {
                    "sale_item_id": sale_item_id,
                    "quantity": "1",
                }
            ],
        },
    )

    assert refund.status_code == 201, refund.json
    assert db.session.query(DispensingRecord).count() == 1
    assert db.session.query(SaleRefund).count() == 1
    stock = (
        db.session.query(StockBalance)
        .filter(StockBalance.product_id == RX_PRODUCT_ID)
        .one()
    )
    assert stock.quantity_on_hand == Decimal("10.0000")


def test_receipt_does_not_expose_prescription_details(client):
    checkout = client.post(
        "/api/sales/checkout",
        json=checkout_payload(),
    )
    sale_id = checkout.json["item"]["id"]

    receipt = client.get(f"/api/sales/{sale_id}/receipt")

    assert receipt.status_code == 200, receipt.json
    assert "prescription_reference" not in str(receipt.json)
    assert "prescriber_name" not in str(receipt.json)
    assert "dispensing" not in str(receipt.json).lower()
