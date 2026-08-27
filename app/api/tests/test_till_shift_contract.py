from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID

import pytest
from sqlalchemy.exc import SQLAlchemyError
from flask import Flask

from app.api.errors import register_error_handlers
from app.api.sales import bp as sales_bp
from app.api.tills import bp as tills_bp
from app.api.warehouses import bp as warehouses_bp
from app.auth.exceptions import PermissionDeniedError
from app.extensions import db
from app.models import (
    Branch,
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
    UserRole,
    UserPermission,
    UserSession,
    RefreshToken,
    PasswordResetToken,
    Warehouse,
)
from app.models.pos import SaleRefund, SaleRefundItem
from app.models.security import TokenRevocationReason
from app.services.tenant.pos.till_shift_service import TillShiftService


TENANT_ID = "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa"
OTHER_TENANT_ID = "bbbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb"
BRANCH_ID = "cccccccc-cccc-4ccc-cccc-cccccccccccc"
OTHER_BRANCH_ID = "dddddddd-dddd-4ddd-dddd-dddddddddddd"
USER_ID = "eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee"
OTHER_USER_ID = "ffffffff-ffff-4fff-ffff-ffffffffffff"
SESSION_ID = "98989898-9898-4989-8989-989898989898"
OTHER_SESSION_ID = "78787878-7878-4787-8787-787878787878"
TILL_ID = "abababab-abab-4aba-abab-abababababab"
SECOND_TILL_ID = "acacacac-acac-4aca-acac-acacacacacac"
OTHER_TILL_ID = "bcbcbcbc-bcbc-4bcb-bcbc-bcbcbcbcbcbc"
INACTIVE_TILL_ID = "cdcdcdcd-cdcd-4cdc-cdcd-cdcdcdcdcdcd"
NO_WAREHOUSE_TILL_ID = "edededed-eded-4ede-eded-edededededed"
CROSS_BRANCH_WAREHOUSE_TILL_ID = "12121212-1212-4121-8121-121212121212"
CROSS_TENANT_WAREHOUSE_TILL_ID = "23232323-2323-4232-8232-232323232323"
INACTIVE_WAREHOUSE_TILL_ID = "34343434-3434-4343-8343-343434343434"
WAREHOUSE_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
PRODUCT_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
PAYMENT_METHOD_ID = "cccccccc-cccc-cccc-cccc-cccccccccccc"
CARD_PAYMENT_METHOD_ID = "dededede-dede-4ded-dede-dededededede"
BATCH_ID = "11111111-1111-4111-8111-111111111111"
SECOND_BATCH_ID = "22222222-2222-4222-8222-222222222222"
EXPIRED_BATCH_ID = "33333333-3333-4333-8333-333333333333"
OTHER_WAREHOUSE_ID = "44444444-4444-4444-8444-444444444444"
OTHER_BRANCH_WAREHOUSE_ID = "55555555-5555-4555-8555-555555555555"
OTHER_TENANT_WAREHOUSE_ID = "66666666-6666-4666-8666-666666666666"
INACTIVE_WAREHOUSE_ID = "77777777-7777-4777-8777-777777777777"


@pytest.fixture()
def app_context():
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TESTING=True,
    )
    db.init_app(app)
    app.register_blueprint(tills_bp, url_prefix="/api")
    app.register_blueprint(warehouses_bp, url_prefix="/api")
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
        UnitOfMeasure.__table__.create(db.engine)
        Product.__table__.create(db.engine)
        ProductUnit.__table__.create(db.engine)
        Warehouse.__table__.create(db.engine)
        InventoryBatch.__table__.create(db.engine)
        Till.__table__.create(db.engine)
        TillShift.__table__.create(db.engine)
        PaymentMethod.__table__.create(db.engine)
        Sale.__table__.create(db.engine)
        SaleRefund.__table__.create(db.engine)
        SaleRefundItem.__table__.create(db.engine)
        SaleItem.__table__.create(db.engine)
        SalePayment.__table__.create(db.engine)
        StockBalance.__table__.create(db.engine)
        InventoryMovement.__table__.create(db.engine)

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
                    first_name="Cashier",
                    email="cashier@example.test",
                    username="cashier",
                    password_hash="hash",
                ),
                UserSession(
                    id=SESSION_ID,
                    tenant_id=TENANT_ID,
                    branch_id=BRANCH_ID,
                    user_id=USER_ID,
                    expires_at=datetime.now(timezone.utc) + timedelta(hours=8),
                    last_activity_at=datetime.now(timezone.utc),
                ),
                User(
                    id=OTHER_USER_ID,
                    tenant_id=TENANT_ID,
                    branch_id=OTHER_BRANCH_ID,
                    first_name="Other",
                    email="other@example.test",
                    username="other",
                    password_hash="hash",
                ),
                Product(
                    id=PRODUCT_ID,
                    tenant_id=TENANT_ID,
                    internal_sku="SKU-001",
                    name="Paracetamol",
                    min_sale_price=Decimal("8.00"),
                    default_sale_price=Decimal("10.00"),
                    track_inventory=True,
                    track_batches=True,
                    track_expiry=True,
                ),
                Warehouse(
                    id=WAREHOUSE_ID,
                    tenant_id=TENANT_ID,
                    branch_id=BRANCH_ID,
                    code="WH-1",
                    name="Main Warehouse",
                ),
                Warehouse(
                    id=OTHER_WAREHOUSE_ID,
                    tenant_id=TENANT_ID,
                    branch_id=BRANCH_ID,
                    code="WH-2",
                    name="Overflow Warehouse",
                ),
                Warehouse(
                    id=OTHER_BRANCH_WAREHOUSE_ID,
                    tenant_id=TENANT_ID,
                    branch_id=OTHER_BRANCH_ID,
                    code="WH-3",
                    name="Other Branch Warehouse",
                ),
                Warehouse(
                    id=OTHER_TENANT_WAREHOUSE_ID,
                    tenant_id=OTHER_TENANT_ID,
                    branch_id=OTHER_BRANCH_ID,
                    code="WH-4",
                    name="Other Tenant Warehouse",
                ),
                Warehouse(
                    id=INACTIVE_WAREHOUSE_ID,
                    tenant_id=TENANT_ID,
                    branch_id=BRANCH_ID,
                    code="WH-5",
                    name="Inactive Warehouse",
                    is_active=False,
                ),
                InventoryBatch(
                    id=BATCH_ID,
                    tenant_id=TENANT_ID,
                    warehouse_id=WAREHOUSE_ID,
                    product_id=PRODUCT_ID,
                    batch_number="BATCH-001",
                    expiry_date=date.today() + timedelta(days=30),
                    unit_cost=Decimal("1.00"),
                    quantity_on_hand=Decimal("10.0000"),
                    quantity_reserved=Decimal("0.0000"),
                    status="available",
                ),
                Till(
                    id=TILL_ID,
                    tenant_id=TENANT_ID,
                    branch_id=BRANCH_ID,
                    warehouse_id=WAREHOUSE_ID,
                    code="TILL-1",
                    name="Front Till",
                ),
                Till(
                    id=SECOND_TILL_ID,
                    tenant_id=TENANT_ID,
                    branch_id=BRANCH_ID,
                    warehouse_id=WAREHOUSE_ID,
                    code="TILL-2",
                    name="Side Till",
                ),
                Till(
                    id=OTHER_TILL_ID,
                    tenant_id=TENANT_ID,
                    branch_id=OTHER_BRANCH_ID,
                    warehouse_id=OTHER_BRANCH_WAREHOUSE_ID,
                    code="TILL-3",
                    name="Back Till",
                ),
                Till(
                    id=INACTIVE_TILL_ID,
                    tenant_id=TENANT_ID,
                    branch_id=BRANCH_ID,
                    warehouse_id=WAREHOUSE_ID,
                    code="TILL-0",
                    name="Inactive Till",
                    is_active=False,
                ),
                PaymentMethod(
                    id=PAYMENT_METHOD_ID,
                    tenant_id=TENANT_ID,
                    code="cash",
                    name="Cash",
                    method_type="cash",
                ),
                PaymentMethod(
                    id=CARD_PAYMENT_METHOD_ID,
                    tenant_id=TENANT_ID,
                    code="card",
                    name="Card",
                    method_type="card",
                ),
                StockBalance(
                    id="dddddddd-dddd-dddd-dddd-dddddddddddd",
                    tenant_id=TENANT_ID,
                    branch_id=BRANCH_ID,
                    warehouse_id=WAREHOUSE_ID,
                    product_id=PRODUCT_ID,
                    quantity_on_hand=Decimal("10.0000"),
                    quantity_available=Decimal("10.0000"),
                    quantity_reserved=Decimal("0.0000"),
                    avg_unit_cost=Decimal("1.00"),
                ),
            ]
        )
        db.session.commit()

        yield app

        db.session.remove()
        InventoryMovement.__table__.drop(db.engine)
        StockBalance.__table__.drop(db.engine)
        SalePayment.__table__.drop(db.engine)
        SaleRefundItem.__table__.drop(db.engine)
        SaleItem.__table__.drop(db.engine)
        SaleRefund.__table__.drop(db.engine)
        Sale.__table__.drop(db.engine)
        PaymentMethod.__table__.drop(db.engine)
        TillShift.__table__.drop(db.engine)
        Till.__table__.drop(db.engine)
        InventoryBatch.__table__.drop(db.engine)
        Warehouse.__table__.drop(db.engine)
        ProductUnit.__table__.drop(db.engine)
        Product.__table__.drop(db.engine)
        UnitOfMeasure.__table__.drop(db.engine)
        PasswordResetToken.__table__.drop(db.engine)
        RefreshToken.__table__.drop(db.engine)
        UserSession.__table__.drop(db.engine)
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
        "app.api.tills._current_identity",
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


def add_user_session(
    *,
    session_id: str,
    user_id: str = USER_ID,
    tenant_id: str = TENANT_ID,
    branch_id: str = BRANCH_ID,
) -> UserSession:
    now = datetime.now(timezone.utc)

    session = UserSession(
        id=session_id,
        tenant_id=tenant_id,
        branch_id=branch_id,
        user_id=user_id,
        expires_at=now + timedelta(hours=8),
        last_activity_at=now,
    )

    db.session.add(session)
    db.session.commit()

    return session


def add_open_shift(
    *,
    shift_id: str = "edededed-eded-4ede-eded-edededededed",
    tenant_id: str = TENANT_ID,
    branch_id: str = BRANCH_ID,
    till_id: str = TILL_ID,
    cashier_id: str = USER_ID,
    active_session_id: str | None = SESSION_ID,
    opened_at: datetime | None = None,
) -> TillShift:
    now = opened_at or datetime.now(timezone.utc)
    shift = TillShift(
        id=shift_id,
        tenant_id=tenant_id,
        branch_id=branch_id,
        till_id=till_id,
        cashier_id=cashier_id,
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


def checkout_payload(
    *,
    product_id: str = PRODUCT_ID,
    warehouse_id: str | None = WAREHOUSE_ID,
    quantity: str = "1",
    payment_amount: str = "10.00",
    payment_method_id: str = PAYMENT_METHOD_ID,
) -> dict:
    payload = {
        "till_id": TILL_ID,
        "items": [
            {
                "product_id": product_id,
                "quantity": quantity,
            }
        ],
        "payments": [
            {
                "payment_method_id": payment_method_id,
                "amount": payment_amount,
            }
        ],
    }
    if warehouse_id is not None:
        payload["warehouse_id"] = warehouse_id

    return payload


def set_stock_balance(
    *,
    warehouse_id: str = WAREHOUSE_ID,
    branch_id: str = BRANCH_ID,
    product_id: str = PRODUCT_ID,
    on_hand: str,
    available: str | None = None,
) -> StockBalance:
    stock_balance = (
        db.session.query(StockBalance)
        .filter(
            StockBalance.warehouse_id == warehouse_id,
            StockBalance.product_id == product_id,
        )
        .first()
    )
    if stock_balance is None:
        stock_balance = StockBalance(
            tenant_id=TENANT_ID,
            branch_id=branch_id,
            warehouse_id=warehouse_id,
            product_id=product_id,
            quantity_reserved=Decimal("0.0000"),
            avg_unit_cost=Decimal("1.00"),
        )
        db.session.add(stock_balance)

    stock_balance.quantity_on_hand = Decimal(on_hand)
    stock_balance.quantity_available = Decimal(available or on_hand)
    stock_balance.quantity_reserved = Decimal("0.0000")
    return stock_balance


def replace_batches(*batches: InventoryBatch) -> None:
    db.session.query(InventoryBatch).delete()
    db.session.add_all(batches)


def make_batch(
    batch_id: str,
    *,
    warehouse_id: str = WAREHOUSE_ID,
    tenant_id: str = TENANT_ID,
    product_id: str = PRODUCT_ID,
    quantity: str,
    expiry_date: date | None = None,
    unit_cost: str = "1.00",
) -> InventoryBatch:
    return InventoryBatch(
        id=batch_id,
        tenant_id=tenant_id,
        warehouse_id=warehouse_id,
        product_id=product_id,
        batch_number=batch_id,
        expiry_date=expiry_date,
        unit_cost=Decimal(unit_cost),
        quantity_on_hand=Decimal(quantity),
        quantity_reserved=Decimal("0.0000"),
        status="available",
    )


def test_pos_availability_requires_sales_create_permission(
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
        "app.api.sales._current_identity",
        lambda: identity,
    )
    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.authorization_service.authorize",
        lambda *args, **kwargs: captured.update(kwargs),
    )

    response = app_context.test_client().get(
        f"/api/sales/availability?till_id={TILL_ID}&product_ids={PRODUCT_ID}"
    )

    assert response.status_code == 200
    assert captured["permission"] == "sales.create"


def test_pos_availability_uses_till_warehouse_sellable_stock(client):
    replace_batches(
        make_batch(
            BATCH_ID,
            quantity="2.0000",
            expiry_date=date.today() + timedelta(days=30),
        ),
        make_batch(
            EXPIRED_BATCH_ID,
            quantity="5.0000",
            expiry_date=date.today() - timedelta(days=1),
        ),
        make_batch(
            SECOND_BATCH_ID,
            warehouse_id=OTHER_WAREHOUSE_ID,
            quantity="9.0000",
            expiry_date=date.today() + timedelta(days=60),
        ),
    )
    set_stock_balance(on_hand="7.0000", available="7.0000")
    set_stock_balance(
        warehouse_id=OTHER_WAREHOUSE_ID,
        product_id=PRODUCT_ID,
        on_hand="9.0000",
        available="9.0000",
    )
    db.session.commit()

    response = client.get(
        f"/api/sales/availability?till_id={TILL_ID}&product_ids={PRODUCT_ID}"
    )

    assert response.status_code == 200
    item = response.json["items"][0]
    assert item["warehouse_id"] == WAREHOUSE_ID
    assert item["status"] == "in_stock"
    assert item["sellable_quantity"] == "2.0000"
    assert item["expired_only"] is False
    assert item["earliest_sellable_expiry_date"] == (
        date.today() + timedelta(days=30)
    ).isoformat()


def test_pos_availability_reports_expired_only_batch_stock(client):
    replace_batches(
        make_batch(
            EXPIRED_BATCH_ID,
            quantity="5.0000",
            expiry_date=date.today() - timedelta(days=1),
        )
    )
    set_stock_balance(on_hand="5.0000", available="5.0000")
    db.session.commit()

    response = client.get(
        f"/api/sales/availability?till_id={TILL_ID}&product_ids={PRODUCT_ID}"
    )

    assert response.status_code == 200
    item = response.json["items"][0]
    assert item["status"] == "out_of_stock"
    assert item["sellable_quantity"] == "0.0000"
    assert item["expired_only"] is True


def test_pos_availability_allows_non_inventory_products_without_stock(client):
    product = Product(
        id="99999999-9999-4999-8999-999999999999",
        tenant_id=TENANT_ID,
        internal_sku="SVC-001",
        name="Consultation",
        min_sale_price=Decimal("0.00"),
        default_sale_price=Decimal("5.00"),
        track_inventory=False,
        track_batches=False,
        track_expiry=False,
    )
    db.session.add(product)
    db.session.commit()

    response = client.get(
        f"/api/sales/availability?till_id={TILL_ID}&product_ids={product.id}"
    )

    assert response.status_code == 200
    item = response.json["items"][0]
    assert item["status"] == "not_tracked"
    assert item["sellable_quantity"] is None
    assert item["is_out_of_stock"] is False


def test_pos_availability_rejects_cross_branch_till(client):
    response = client.get(
        f"/api/sales/availability?till_id={OTHER_TILL_ID}&product_ids={PRODUCT_ID}"
    )

    assert response.status_code == 400
    assert response.json["error"] == "Active till not found for this branch."


def test_tills_list_requires_authentication(
    app_context,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.get_current_identity",
        lambda: None,
    )
    monkeypatch.setattr(
        "app.auth.jwt.get_current_identity",
        lambda: None,
    )

    response = app_context.test_client().get("/api/tills")

    assert response.status_code == 401


def test_tills_list_enforces_sales_create_permission(
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
        "app.api.tills._current_identity",
        lambda: identity,
    )
    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.authorization_service.authorize",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            PermissionDeniedError("Permission denied.")
        ),
    )

    response = app_context.test_client().get("/api/tills")

    assert response.status_code == 403
    assert response.json["error"]["code"] == "AUTHORIZATION_DENIED"


def test_tills_list_requires_branch_context(
    client,
    identity: SimpleNamespace,
):
    identity.branch_id = None

    response = client.get("/api/tills")

    assert response.status_code == 400
    assert response.json["error"]["code"] == "VALIDATION_ERROR"


def test_tills_list_returns_active_current_branch_tills_only(client):
    response = client.get("/api/tills")

    assert response.status_code == 200
    assert response.json == {
        "ok": True,
        "items": [
            {
                "id": TILL_ID,
                "branch_id": BRANCH_ID,
                "warehouse_id": WAREHOUSE_ID,
                "code": "TILL-1",
                "name": "Front Till",
                "is_active": True,
            },
            {
                "id": SECOND_TILL_ID,
                "branch_id": BRANCH_ID,
                "warehouse_id": WAREHOUSE_ID,
                "code": "TILL-2",
                "name": "Side Till",
                "is_active": True,
            }
        ],
    }


def test_tills_list_excludes_tills_without_valid_branch_warehouse(client):
    db.session.add_all(
        [
            Till(
                id=NO_WAREHOUSE_TILL_ID,
                tenant_id=TENANT_ID,
                branch_id=BRANCH_ID,
                code="TILL-4",
                name="No Warehouse Till",
            ),
            Till(
                id=CROSS_BRANCH_WAREHOUSE_TILL_ID,
                tenant_id=TENANT_ID,
                branch_id=BRANCH_ID,
                warehouse_id=OTHER_BRANCH_WAREHOUSE_ID,
                code="TILL-5",
                name="Cross Branch Warehouse Till",
            ),
            Till(
                id=CROSS_TENANT_WAREHOUSE_TILL_ID,
                tenant_id=TENANT_ID,
                branch_id=BRANCH_ID,
                warehouse_id=OTHER_TENANT_WAREHOUSE_ID,
                code="TILL-6",
                name="Cross Tenant Warehouse Till",
            ),
            Till(
                id=INACTIVE_WAREHOUSE_TILL_ID,
                tenant_id=TENANT_ID,
                branch_id=BRANCH_ID,
                warehouse_id=INACTIVE_WAREHOUSE_ID,
                code="TILL-7",
                name="Inactive Warehouse Till",
            ),
        ]
    )
    db.session.commit()

    response = client.get("/api/tills")

    assert response.status_code == 200
    assert [item["id"] for item in response.json["items"]] == [
        TILL_ID,
        SECOND_TILL_ID,
    ]


def test_warehouses_list_returns_active_current_branch_warehouses_only(client):
    response = client.get("/api/warehouses")

    assert response.status_code == 200
    assert response.json == {
        "ok": True,
        "items": [
            {
                "id": WAREHOUSE_ID,
                "branch_id": BRANCH_ID,
                "code": "WH-1",
                "name": "Main Warehouse",
                "warehouse_type": "main",
                "is_active": True,
            },
            {
                "id": OTHER_WAREHOUSE_ID,
                "branch_id": BRANCH_ID,
                "code": "WH-2",
                "name": "Overflow Warehouse",
                "warehouse_type": "main",
                "is_active": True,
            },
        ],
    }


def test_warehouses_list_requires_inventory_or_count_permission(
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
        "app.api.warehouses._current_identity",
        lambda: identity,
    )
    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.authorization_service.authorize",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            PermissionDeniedError("Permission denied.")
        ),
    )

    response = app_context.test_client().get("/api/warehouses")

    assert response.status_code == 403
    assert response.json["error"]["code"] == "AUTHORIZATION_DENIED"


def test_warehouses_list_allows_inventory_count_or_adjust_permission(
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

    response = app_context.test_client().get("/api/warehouses")

    assert response.status_code == 200
    assert captured["any_permissions"] == (
        "inventory.read",
        "inventory.count",
        "inventory.adjust",
    )


def test_open_till_shift_creates_shift_for_authenticated_cashier(client):
    response = client.post(
        "/api/till-shifts/open",
        json={
            "till_id": TILL_ID,
            "opening_float": "75.50",
        },
    )

    assert response.status_code == 201
    assert response.json["item"]["till_id"] == TILL_ID
    assert response.json["item"]["branch_id"] == BRANCH_ID
    assert response.json["item"]["cashier_id"] == USER_ID
    assert response.json["item"]["status"] == "open"
    assert response.json["item"]["opening_float"] == "75.50"


def test_open_till_shift_rejects_inactive_till(client):
    response = client.post(
        "/api/till-shifts/open",
        json={
            "till_id": INACTIVE_TILL_ID,
            "opening_float": "10.00",
        },
    )

    assert response.status_code == 404
    assert response.json["error"]["message"] == "Active till not found."


def test_open_till_shift_rejects_cross_branch_till(client):
    response = client.post(
        "/api/till-shifts/open",
        json={
            "till_id": OTHER_TILL_ID,
            "opening_float": "10.00",
        },
    )

    assert response.status_code == 404
    assert response.json["error"]["message"] == "Active till not found."


def test_open_till_shift_rejects_till_without_warehouse(client):
    db.session.add(
        Till(
            id=NO_WAREHOUSE_TILL_ID,
            tenant_id=TENANT_ID,
            branch_id=BRANCH_ID,
            code="TILL-4",
            name="No Warehouse Till",
        )
    )
    db.session.commit()

    response = client.post(
        "/api/till-shifts/open",
        json={
            "till_id": NO_WAREHOUSE_TILL_ID,
            "opening_float": "10.00",
        },
    )

    assert response.status_code == 400
    assert response.json["error"]["message"] == (
        "Till is not configured with a warehouse."
    )


@pytest.mark.parametrize(
    ("till_id", "warehouse_id"),
    [
        (CROSS_BRANCH_WAREHOUSE_TILL_ID, OTHER_BRANCH_WAREHOUSE_ID),
        (CROSS_TENANT_WAREHOUSE_TILL_ID, OTHER_TENANT_WAREHOUSE_ID),
        (INACTIVE_WAREHOUSE_TILL_ID, INACTIVE_WAREHOUSE_ID),
    ],
)
def test_open_till_shift_rejects_invalid_till_warehouse(
    client,
    till_id: str,
    warehouse_id: str,
):
    db.session.add(
        Till(
            id=till_id,
            tenant_id=TENANT_ID,
            branch_id=BRANCH_ID,
            warehouse_id=warehouse_id,
            code=till_id[:8],
            name="Invalid Warehouse Till",
        )
    )
    db.session.commit()

    response = client.post(
        "/api/till-shifts/open",
        json={
            "till_id": till_id,
            "opening_float": "10.00",
        },
    )

    assert response.status_code == 400
    assert response.json["error"]["message"] == (
        "Till warehouse is not active for this branch."
    )


def test_open_till_shift_rejects_conflicting_open_till_shift(client):
    add_open_shift()

    response = client.post(
        "/api/till-shifts/open",
        json={
            "till_id": TILL_ID,
            "opening_float": "10.00",
        },
    )

    assert response.status_code == 409
    assert response.json["error"]["message"] == (
        "This till already has an open shift."
    )


def test_open_till_shift_validates_opening_float(client):
    response = client.post(
        "/api/till-shifts/open",
        json={
            "till_id": TILL_ID,
            "opening_float": "-1.00",
        },
    )

    assert response.status_code == 400
    assert response.json["error"]["message"] == (
        "opening_float cannot be negative."
    )


def test_current_till_shift_returns_open_shift_for_cashier(client):
    shift = add_open_shift()

    response = client.get("/api/till-shifts/current")

    assert response.status_code == 200
    assert response.json["item"]["id"] == str(shift.id)
    assert response.json["item"]["till_id"] == TILL_ID



def test_current_till_shift_reports_current_session_ownership(client):
    shift = add_open_shift(
        active_session_id=SESSION_ID,
    )

    response = client.get(
        "/api/till-shifts/current"
    )

    assert response.status_code == 200
    assert response.json["item"]["id"] == str(shift.id)
    assert (
        response.json["item"]["owned_by_current_session"]
        is True
    )
    assert "active_session_id" not in response.json["item"]


def test_current_till_shift_reports_foreign_session_ownership(client):
    shift = add_open_shift(
        active_session_id=OTHER_SESSION_ID,
    )

    response = client.get(
        "/api/till-shifts/current"
    )

    assert response.status_code == 200
    assert response.json["item"]["id"] == str(shift.id)
    assert (
        response.json["item"]["owned_by_current_session"]
        is False
    )
    assert "active_session_id" not in response.json["item"]


def test_current_till_shift_returns_null_when_no_shift_is_open(client):
    response = client.get("/api/till-shifts/current")

    assert response.status_code == 200
    assert response.json == {
        "ok": True,
        "item": None,
    }


def test_takeover_till_shift_route_transfers_existing_shift(client):
    previous_session = add_user_session(
        session_id=OTHER_SESSION_ID,
    )

    shift = add_open_shift(
        active_session_id=OTHER_SESSION_ID,
    )

    response = client.post(
        f"/api/till-shifts/{shift.id}/takeover",
    )

    assert response.status_code == 200
    assert response.json["ok"] is True
    assert response.json["message"] == (
        "Till shift transferred to this session successfully."
    )
    assert response.json["item"]["id"] == shift.id
    assert (
        response.json["item"]["owned_by_current_session"]
        is True
    )
    assert "active_session_id" not in response.json["item"]

    db.session.expire_all()

    persisted_shift = db.session.get(
        TillShift,
        shift.id,
    )
    persisted_previous_session = db.session.get(
        UserSession,
        previous_session.id,
    )

    assert persisted_shift is not None
    assert persisted_shift.active_session_id == SESSION_ID

    assert persisted_previous_session is not None
    assert persisted_previous_session.is_revoked
    assert (
        persisted_previous_session.revoke_reason
        == TokenRevocationReason.SESSION_TAKEOVER
    )


def test_takeover_till_shift_route_is_idempotent_for_current_session(
    client,
):
    shift = add_open_shift(
        active_session_id=SESSION_ID,
    )

    response = client.post(
        f"/api/till-shifts/{shift.id}/takeover",
    )

    assert response.status_code == 200
    assert response.json["ok"] is True
    assert response.json["item"]["id"] == shift.id

    db.session.expire_all()

    persisted_shift = db.session.get(
        TillShift,
        shift.id,
    )
    current_session = db.session.get(
        UserSession,
        SESSION_ID,
    )

    assert persisted_shift is not None
    assert persisted_shift.active_session_id == SESSION_ID

    assert current_session is not None
    assert current_session.is_active
    assert current_session.revoked_at is None


def test_close_till_shift_rejects_shift_owned_by_another_session(client):
    shift = add_open_shift(
        active_session_id=OTHER_SESSION_ID,
    )

    response = client.post(
        f"/api/till-shifts/{shift.id}/close",
        json={
            "closing_cash": "50.00",
        },
    )

    assert response.status_code == 409
    assert response.json["error"]["message"] == (
        "This till shift is active on another session."
    )

    db.session.expire_all()

    persisted = db.session.get(
        TillShift,
        shift.id,
    )

    assert persisted is not None
    assert persisted.status == "open"
    assert persisted.closed_at is None
    assert persisted.active_session_id == OTHER_SESSION_ID


def test_close_till_shift_closes_shift_and_returns_reconciliation(client):
    opened_at = datetime.now(timezone.utc) - timedelta(minutes=10)
    shift = add_open_shift(opened_at=opened_at)
    sale = Sale(
        id="fafafafa-fafa-4afa-fafa-fafafafafafa",
        tenant_id=TENANT_ID,
        branch_id=BRANCH_ID,
        till_id=TILL_ID,
        till_shift_id=shift.id,
        warehouse_id=WAREHOUSE_ID,
        sale_number="SALE-001",
        sale_date=opened_at + timedelta(minutes=1),
        status="paid",
        subtotal=Decimal("20.00"),
        discount_amount=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("20.00"),
        paid_amount=Decimal("20.00"),
        balance_due=Decimal("0.00"),
        cashier_id=USER_ID,
        created_at=opened_at + timedelta(minutes=1),
        updated_at=opened_at + timedelta(minutes=1),
    )
    payment = SalePayment(
        id="abababab-cdcd-4efe-abab-abababababab",
        sale_id=sale.id,
        payment_method_id=PAYMENT_METHOD_ID,
        amount=Decimal("20.00"),
        paid_at=opened_at + timedelta(minutes=2),
        received_by=USER_ID,
    )
    other_shift = add_open_shift(
        shift_id="adadadad-adad-4ada-adad-adadadadadad",
        opened_at=opened_at,
    )
    other_sale = Sale(
        id="bfbfbfbf-bfbf-4bfb-bfbf-bfbfbfbfbfbf",
        tenant_id=TENANT_ID,
        branch_id=BRANCH_ID,
        till_id=TILL_ID,
        till_shift_id=other_shift.id,
        warehouse_id=WAREHOUSE_ID,
        sale_number="SALE-002",
        sale_date=opened_at + timedelta(minutes=1),
        status="paid",
        subtotal=Decimal("99.00"),
        discount_amount=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("99.00"),
        paid_amount=Decimal("99.00"),
        balance_due=Decimal("0.00"),
        cashier_id=USER_ID,
        created_at=opened_at + timedelta(minutes=1),
        updated_at=opened_at + timedelta(minutes=1),
    )
    other_payment = SalePayment(
        id="cacacaca-caca-4cac-caca-cacacacacaca",
        sale_id=other_sale.id,
        payment_method_id=PAYMENT_METHOD_ID,
        amount=Decimal("99.00"),
        paid_at=opened_at + timedelta(minutes=2),
        received_by=USER_ID,
    )
    card_sale = Sale(
        id="dcdcdcdc-dcdc-4dcd-dcdc-dcdcdcdcdcdc",
        tenant_id=TENANT_ID,
        branch_id=BRANCH_ID,
        till_id=TILL_ID,
        till_shift_id=shift.id,
        warehouse_id=WAREHOUSE_ID,
        sale_number="SALE-003",
        sale_date=opened_at + timedelta(minutes=1),
        status="paid",
        subtotal=Decimal("15.00"),
        discount_amount=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("15.00"),
        paid_amount=Decimal("15.00"),
        balance_due=Decimal("0.00"),
        cashier_id=USER_ID,
        created_at=opened_at + timedelta(minutes=1),
        updated_at=opened_at + timedelta(minutes=1),
    )
    card_payment = SalePayment(
        id="efefefef-efef-4efe-efef-efefefefefef",
        sale_id=card_sale.id,
        payment_method_id=CARD_PAYMENT_METHOD_ID,
        amount=Decimal("15.00"),
        paid_at=opened_at + timedelta(minutes=2),
        received_by=USER_ID,
    )
    db.session.add_all(
        [
            sale,
            payment,
            other_sale,
            other_payment,
            card_sale,
            card_payment,
        ]
    )
    db.session.commit()

    response = client.post(
        f"/api/till-shifts/{shift.id}/close",
        json={
            "closing_cash": "72.00",
        },
    )

    assert response.status_code == 200
    assert response.json["item"]["status"] == "closed"
    assert response.json["reconciliation"] == {
        "opening_float": "50.00",
        "cash_sales_total": "20.00",
        "cash_refunds_total": "0.00",
        "expected_cash": "70.00",
        "closing_cash": "72.00",
        "cash_difference": "2.00",
    }


def test_close_till_shift_rejects_already_closed_shift(client):
    shift = add_open_shift()

    client.post(
        f"/api/till-shifts/{shift.id}/close",
        json={
            "closing_cash": "50.00",
        },
    )

    response = client.post(
        f"/api/till-shifts/{shift.id}/close",
        json={
            "closing_cash": "50.00",
        },
    )

    assert response.status_code == 409
    assert response.json["error"]["message"] == (
        "Till shift is already closed."
    )


def test_close_till_shift_rejects_cross_branch_shift(client):
    shift = add_open_shift(
        shift_id="dfdfdfdf-dfdf-4dfd-dfdf-dfdfdfdfdfdf",
        branch_id=OTHER_BRANCH_ID,
        till_id=OTHER_TILL_ID,
        cashier_id=OTHER_USER_ID,
    )

    response = client.post(
        f"/api/till-shifts/{shift.id}/close",
        json={
            "closing_cash": "50.00",
        },
    )

    assert response.status_code == 404
    assert response.json["error"]["message"] == (
        "Open till shift not found."
    )


def test_checkout_rejects_closed_till_shift(client):
    shift = add_open_shift()
    shift.status = "closed"
    shift.closed_at = datetime.now(timezone.utc)
    db.session.commit()

    response = client.post(
        "/api/sales/checkout",
        json={
            "warehouse_id": WAREHOUSE_ID,
            "till_id": TILL_ID,
            "items": [
                {
                    "product_id": PRODUCT_ID,
                    "quantity": "1",
                    "unit_price": "10.00",
                }
            ],
            "payments": [
                {
                    "payment_method_id": PAYMENT_METHOD_ID,
                    "amount": "10.00",
                }
            ],
        },
    )

    assert response.status_code == 400
    assert response.json["error"] == (
        "No open shift found for this till and cashier."
    )


def test_checkout_accepts_valid_open_till_shift(client):
    shift = add_open_shift()

    response = client.post(
        "/api/sales/checkout",
        json={
            "warehouse_id": WAREHOUSE_ID,
            "till_id": TILL_ID,
            "items": [
                {
                    "product_id": PRODUCT_ID,
                    "quantity": "1",
                    "unit_price": "10.00",
                }
            ],
            "payments": [
                {
                    "payment_method_id": PAYMENT_METHOD_ID,
                    "amount": "10.00",
                }
            ],
        },
    )

    assert response.status_code == 201
    assert response.json["ok"] is True
    assert response.json["shift_id"] == str(shift.id)
    assert response.json["item"]["till_shift_id"] == str(shift.id)

    sale = db.session.get(Sale, response.json["item"]["id"])

    assert sale.till_shift_id == shift.id
    assert sale.branch_id == BRANCH_ID
    assert sale.warehouse_id == WAREHOUSE_ID
    assert sale.till_id == TILL_ID
    assert sale.cashier_id == USER_ID

    sale_item = (
        db.session.query(SaleItem)
        .filter(SaleItem.sale_id == response.json["item"]["id"])
        .one()
    )
    assert sale_item.unit_price == Decimal("10.00")
    assert sale_item.batch_id == BATCH_ID

    stock_balance = db.session.get(StockBalance, "dddddddd-dddd-dddd-dddd-dddddddddddd")
    batch = db.session.get(InventoryBatch, BATCH_ID)
    movement = db.session.query(InventoryMovement).one()

    assert stock_balance.quantity_on_hand == Decimal("9.0000")
    assert stock_balance.quantity_available == Decimal("9.0000")
    assert batch.quantity_on_hand == Decimal("9.0000")
    assert movement.batch_id == BATCH_ID
    assert movement.sale_item_id == sale_item.id
    assert movement.warehouse_id == WAREHOUSE_ID
    assert movement.quantity == Decimal("-1.0000")
    assert movement.reference_type == "sale"
    assert movement.reference_id == sale.id


def test_checkout_derives_warehouse_from_till_when_client_omits_warehouse(client):
    shift = add_open_shift()

    response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(warehouse_id=None),
    )

    assert response.status_code == 201
    assert response.json["item"]["warehouse_id"] == WAREHOUSE_ID

    sale = db.session.get(Sale, response.json["item"]["id"])
    movement = db.session.query(InventoryMovement).one()

    assert sale.till_shift_id == shift.id
    assert sale.warehouse_id == WAREHOUSE_ID
    assert movement.warehouse_id == WAREHOUSE_ID


def test_refund_restores_stock_balance_and_original_batch(client):
    add_open_shift()
    checkout_response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(quantity="2", payment_amount="20.00"),
    )
    sale_id = checkout_response.json["item"]["id"]
    sale_item_id = checkout_response.json["item"]["items"][0]["id"]

    response = client.post(
        f"/api/sales/{sale_id}/refund",
        json={
            "items": [
                {
                    "sale_item_id": sale_item_id,
                    "quantity": "2",
                }
            ],
            "reason": "Customer return",
        },
    )

    assert response.status_code == 201
    assert response.json["refund"]["stock_returned"] is True

    stock_balance = db.session.get(StockBalance, "dddddddd-dddd-dddd-dddd-dddddddddddd")
    batch = db.session.get(InventoryBatch, BATCH_ID)
    return_movement = (
        db.session.query(InventoryMovement)
        .filter(InventoryMovement.reference_type == "sale_refund")
        .one()
    )

    assert stock_balance.quantity_on_hand == Decimal("10.0000")
    assert stock_balance.quantity_available == Decimal("10.0000")
    assert batch.quantity_on_hand == Decimal("10.0000")
    assert return_movement.quantity == Decimal("2.0000")
    assert return_movement.batch_id == BATCH_ID
    assert return_movement.sale_item_id == sale_item_id
    assert return_movement.reference_id == response.json["refund"]["id"]


def test_refund_restores_partial_quantity(client):
    add_open_shift()
    checkout_response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(quantity="3", payment_amount="30.00"),
    )
    sale_id = checkout_response.json["item"]["id"]
    sale_item_id = checkout_response.json["item"]["items"][0]["id"]

    response = client.post(
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

    assert response.status_code == 201
    assert db.session.get(StockBalance, "dddddddd-dddd-dddd-dddd-dddddddddddd").quantity_on_hand == Decimal("8.0000")
    assert db.session.get(InventoryBatch, BATCH_ID).quantity_on_hand == Decimal("8.0000")


def test_refund_restores_original_multi_batch_allocations(client):
    add_open_shift()
    set_stock_balance(on_hand="5.0000")
    replace_batches(
        make_batch(
            BATCH_ID,
            quantity="2.0000",
            expiry_date=date.today() + timedelta(days=5),
            unit_cost="1.10",
        ),
        make_batch(
            SECOND_BATCH_ID,
            quantity="3.0000",
            expiry_date=date.today() + timedelta(days=30),
            unit_cost="1.20",
        ),
    )
    db.session.commit()

    checkout_response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(quantity="4", payment_amount="40.00"),
    )
    sale_id = checkout_response.json["item"]["id"]
    sale_item_id = checkout_response.json["item"]["items"][0]["id"]

    response = client.post(
        f"/api/sales/{sale_id}/refund",
        json={
            "items": [
                {
                    "sale_item_id": sale_item_id,
                    "quantity": "4",
                }
            ],
        },
    )

    assert response.status_code == 201
    assert db.session.get(InventoryBatch, BATCH_ID).quantity_on_hand == Decimal("2.0000")
    assert db.session.get(InventoryBatch, SECOND_BATCH_ID).quantity_on_hand == Decimal("3.0000")

    return_movements = {
        movement.batch_id: movement
        for movement in db.session.query(InventoryMovement)
        .filter(InventoryMovement.reference_type == "sale_refund")
        .all()
    }
    assert return_movements[BATCH_ID].quantity == Decimal("2.0000")
    assert return_movements[BATCH_ID].unit_cost == Decimal("1.10")
    assert return_movements[SECOND_BATCH_ID].quantity == Decimal("2.0000")
    assert return_movements[SECOND_BATCH_ID].unit_cost == Decimal("1.20")


def test_refund_restores_expired_original_batch_but_checkout_still_excludes_it(client):
    add_open_shift()
    set_stock_balance(on_hand="2.0000")
    batch = db.session.get(InventoryBatch, BATCH_ID)
    batch.quantity_on_hand = Decimal("2.0000")
    batch.expiry_date = date.today() + timedelta(days=1)
    db.session.commit()

    checkout_response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(quantity="1", payment_amount="10.00"),
    )
    sale_id = checkout_response.json["item"]["id"]
    sale_item_id = checkout_response.json["item"]["items"][0]["id"]

    batch.expiry_date = date.today() - timedelta(days=1)
    db.session.commit()

    response = client.post(
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

    assert response.status_code == 201
    assert db.session.get(InventoryBatch, BATCH_ID).quantity_on_hand == Decimal("2.0000")

    second_checkout = client.post(
        "/api/sales/checkout",
        json=checkout_payload(quantity="2", payment_amount="20.00"),
    )

    assert second_checkout.status_code == 400
    assert second_checkout.json["error"] == (
        f"Insufficient sellable batch stock for product_id={PRODUCT_ID}. "
        "Available=0.0000, requested=2.0000."
    )


def test_refund_non_inventory_product_creates_no_stock_restoration(client):
    product = db.session.get(Product, PRODUCT_ID)
    product.track_inventory = False
    product.track_batches = False
    product.track_expiry = False
    db.session.query(InventoryBatch).delete()
    db.session.query(StockBalance).delete()
    db.session.commit()
    add_open_shift()

    checkout_response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(),
    )
    assert checkout_response.status_code == 201, checkout_response.json
    sale_id = checkout_response.json["item"]["id"]
    sale_item_id = checkout_response.json["item"]["items"][0]["id"]

    response = client.post(
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

    assert response.status_code == 201
    assert response.json["refund"]["stock_returned"] is False
    assert db.session.query(InventoryMovement).count() == 0


def test_refund_repeated_partial_refunds_cannot_over_restore(client):
    add_open_shift()
    checkout_response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(quantity="5", payment_amount="50.00"),
    )
    sale_id = checkout_response.json["item"]["id"]
    sale_item_id = checkout_response.json["item"]["items"][0]["id"]

    first = client.post(
        f"/api/sales/{sale_id}/refund",
        json={
            "items": [
                {
                    "sale_item_id": sale_item_id,
                    "quantity": "3",
                }
            ],
        },
    )
    second = client.post(
        f"/api/sales/{sale_id}/refund",
        json={
            "items": [
                {
                    "sale_item_id": sale_item_id,
                    "quantity": "3",
                }
            ],
        },
    )

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json["error"] == (
        f"Requested refund quantity 3.0000 exceeds remaining refundable quantity 2.0000 for sale item {sale_item_id}."
    )
    assert db.session.get(StockBalance, "dddddddd-dddd-dddd-dddd-dddddddddddd").quantity_on_hand == Decimal("8.0000")
    assert db.session.get(InventoryBatch, BATCH_ID).quantity_on_hand == Decimal("8.0000")


def test_refund_full_after_partial_allows_only_remaining_quantity(client):
    add_open_shift()
    checkout_response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(quantity="4", payment_amount="40.00"),
    )
    sale_id = checkout_response.json["item"]["id"]
    sale_item_id = checkout_response.json["item"]["items"][0]["id"]

    first = client.post(
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
    second = client.post(
        f"/api/sales/{sale_id}/refund",
        json={
            "items": [
                {
                    "sale_item_id": sale_item_id,
                    "quantity": "3",
                }
            ],
        },
    )
    third = client.post(
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

    assert first.status_code == 201
    assert second.status_code == 201
    assert third.status_code == 409
    assert third.json["error"] == "This sale has already been fully refunded."
    assert db.session.get(Sale, sale_id).refund_status == "refunded"
    assert db.session.get(SaleItem, sale_item_id).is_returned is True


def test_refund_rejects_wrong_sale_item(client):
    add_open_shift()
    checkout_response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(),
    )
    assert checkout_response.status_code == 201, checkout_response.json
    sale_id = checkout_response.json["item"]["id"]

    response = client.post(
        f"/api/sales/{sale_id}/refund",
        json={
            "items": [
                {
                    "sale_item_id": "99999999-9999-4999-8999-999999999999",
                    "quantity": "1",
                }
            ],
        },
    )

    assert response.status_code == 400
    assert response.json["error"] == (
        "Sale item 99999999-9999-4999-8999-999999999999 does not belong to this sale."
    )


def test_refund_rejects_untraceable_legacy_inventory_movement(client):
    add_open_shift()
    checkout_response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(),
    )
    assert checkout_response.status_code == 201, checkout_response.json
    sale_id = checkout_response.json["item"]["id"]
    sale_item_id = checkout_response.json["item"]["items"][0]["id"]
    db.session.query(InventoryMovement).update({"sale_item_id": None})
    db.session.commit()

    response = client.post(
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

    assert response.status_code == 409
    assert response.json["error"] == (
        f"Original stock allocation is not traceable for sale_item_id={sale_item_id}."
    )
    assert db.session.query(SaleRefund).count() == 0
    assert db.session.get(StockBalance, "dddddddd-dddd-dddd-dddd-dddddddddddd").quantity_on_hand == Decimal("9.0000")
    assert db.session.get(InventoryBatch, BATCH_ID).quantity_on_hand == Decimal("9.0000")


def test_refund_missing_original_batch_rolls_back(client):
    add_open_shift()
    checkout_response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(),
    )
    assert checkout_response.status_code == 201, checkout_response.json
    sale_id = checkout_response.json["item"]["id"]
    sale_item_id = checkout_response.json["item"]["items"][0]["id"]
    db.session.query(InventoryBatch).delete()
    db.session.commit()

    response = client.post(
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

    assert response.status_code == 409
    assert response.json["error"] == (
        f"Original inventory batch {BATCH_ID} was not found for sale_item_id={sale_item_id}."
    )
    assert db.session.query(SaleRefund).count() == 0
    assert db.session.query(InventoryMovement).filter(
        InventoryMovement.reference_type == "sale_refund"
    ).count() == 0
    assert db.session.get(StockBalance, "dddddddd-dddd-dddd-dddd-dddddddddddd").quantity_on_hand == Decimal("9.0000")


def test_refund_rolls_back_inventory_when_late_flush_fails(
    client,
    monkeypatch: pytest.MonkeyPatch,
):
    add_open_shift()
    checkout_response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(),
    )
    assert checkout_response.status_code == 201, checkout_response.json
    sale_id = checkout_response.json["item"]["id"]
    sale_item_id = checkout_response.json["item"]["items"][0]["id"]
    original_flush = db.session.flush
    flush_count = 0

    def fail_second_flush(*args, **kwargs):
        nonlocal flush_count
        flush_count += 1
        if flush_count == 2:
            raise SQLAlchemyError("forced refund flush failure")
        return original_flush(*args, **kwargs)

    monkeypatch.setattr(db.session, "flush", fail_second_flush)

    response = client.post(
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

    assert response.status_code == 500
    assert db.session.query(SaleRefund).count() == 0
    assert db.session.get(StockBalance, "dddddddd-dddd-dddd-dddd-dddddddddddd").quantity_on_hand == Decimal("9.0000")
    assert db.session.get(InventoryBatch, BATCH_ID).quantity_on_hand == Decimal("9.0000")
    assert db.session.query(InventoryMovement).filter(
        InventoryMovement.reference_type == "sale_refund"
    ).count() == 0


def test_refund_lookup_returns_server_derived_remaining_quantities(client):
    add_open_shift()
    checkout_response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(quantity="3", payment_amount="30.00"),
    )
    sale_id = checkout_response.json["item"]["id"]
    sale_number = checkout_response.json["item"]["sale_number"]
    sale_item_id = checkout_response.json["item"]["items"][0]["id"]
    client.post(
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

    response = client.get(f"/api/sales/{sale_number}")

    assert response.status_code == 200
    assert response.json["item"]["id"] == sale_id
    assert response.json["item"]["items"][0]["refunded_quantity"] == "1.0000"
    assert response.json["item"]["items"][0]["remaining_refundable_quantity"] == "2.0000"
    assert response.json["item"]["items"][0]["is_refundable"] is True


def test_refund_lookup_enforces_sales_refund_permission(
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
        lambda *args, **kwargs: (_ for _ in ()).throw(
            PermissionDeniedError("Permission denied.")
        ),
    )

    response = app_context.test_client().get(f"/api/sales/{TILL_ID}")

    assert response.status_code == 403
    assert response.json["error"]["code"] == "AUTHORIZATION_DENIED"


def test_refund_lookup_enforces_branch_isolation(client):
    now = datetime.now(timezone.utc)
    sale = Sale(
        id="45454545-4545-4545-8545-454545454545",
        tenant_id=TENANT_ID,
        branch_id=OTHER_BRANCH_ID,
        warehouse_id=OTHER_BRANCH_WAREHOUSE_ID,
        till_id=OTHER_TILL_ID,
        sale_number="SALE-OTHER-BRANCH",
        sale_date=now,
        status="paid",
        subtotal=Decimal("10.00"),
        discount_amount=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("10.00"),
        paid_amount=Decimal("10.00"),
        balance_due=Decimal("0.00"),
        cashier_id=OTHER_USER_ID,
        created_at=now,
        updated_at=now,
    )
    db.session.add(sale)
    db.session.commit()

    response = client.get(f"/api/sales/{sale.id}")

    assert response.status_code == 403
    assert response.json["error"] == (
        "You cannot refund sales from another branch."
    )


def test_refund_persists_current_till_shift_and_preserves_sale_shift(client):
    sale_shift = add_open_shift(
        shift_id="a1010101-a101-4101-8101-a10101010101",
    )
    checkout_response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(),
    )
    assert checkout_response.status_code == 201, checkout_response.json
    sale_id = checkout_response.json["item"]["id"]
    sale_item_id = checkout_response.json["item"]["items"][0]["id"]
    client.post(
        f"/api/till-shifts/{sale_shift.id}/close",
        json={"closing_cash": "60.00"},
    )
    refund_shift = add_open_shift(
        shift_id="a2020202-a202-4202-8202-a20202020202",
        till_id=SECOND_TILL_ID,
    )

    response = client.post(
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

    refund = db.session.get(SaleRefund, response.json["refund"]["id"])
    sale = db.session.get(Sale, sale_id)

    assert response.status_code == 201
    assert response.json["refund"]["till_shift_id"] == str(refund_shift.id)
    assert refund.till_shift_id == refund_shift.id
    assert sale.till_shift_id == sale_shift.id


def test_refund_requires_open_till_shift(client):
    sale_shift = add_open_shift(
        shift_id="a3030303-a303-4303-8303-a30303030303",
    )
    checkout_response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(),
    )
    assert checkout_response.status_code == 201, checkout_response.json
    sale_id = checkout_response.json["item"]["id"]
    sale_item_id = checkout_response.json["item"]["items"][0]["id"]
    client.post(
        f"/api/till-shifts/{sale_shift.id}/close",
        json={"closing_cash": "60.00"},
    )

    response = client.post(
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

    assert response.status_code == 409
    assert response.json["error"] == (
        "Open till shift is required to process refunds."
    )
    assert db.session.query(SaleRefund).count() == 0


def test_same_shift_cash_refund_reduces_expected_cash(client):
    shift = add_open_shift(
        shift_id="a4040404-a404-4404-8404-a40404040404",
    )
    checkout_response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(),
    )
    assert checkout_response.status_code == 201, checkout_response.json
    sale_id = checkout_response.json["item"]["id"]
    sale_item_id = checkout_response.json["item"]["items"][0]["id"]

    refund_response = client.post(
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
    close_response = client.post(
        f"/api/till-shifts/{shift.id}/close",
        json={"closing_cash": "50.00"},
    )

    assert refund_response.status_code == 201
    assert close_response.status_code == 200, close_response.json
    assert close_response.json["reconciliation"] == {
        "opening_float": "50.00",
        "cash_sales_total": "10.00",
        "cash_refunds_total": "10.00",
        "expected_cash": "50.00",
        "closing_cash": "50.00",
        "cash_difference": "0.00",
    }


def test_refund_in_second_shift_reduces_second_shift_only(client):
    sale_shift = add_open_shift(
        shift_id="a5050505-a505-4505-8505-a50505050505",
    )
    checkout_response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(),
    )
    sale_id = checkout_response.json["item"]["id"]
    sale_item_id = checkout_response.json["item"]["items"][0]["id"]
    first_close = client.post(
        f"/api/till-shifts/{sale_shift.id}/close",
        json={"closing_cash": "60.00"},
    )
    refund_shift = add_open_shift(
        shift_id="a6060606-a606-4606-8606-a60606060606",
        till_id=SECOND_TILL_ID,
    )

    refund_response = client.post(
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
    second_close = client.post(
        f"/api/till-shifts/{refund_shift.id}/close",
        json={"closing_cash": "40.00"},
    )

    assert first_close.status_code == 200
    assert first_close.json["reconciliation"]["cash_sales_total"] == "10.00"
    assert first_close.json["reconciliation"]["cash_refunds_total"] == "0.00"
    assert first_close.json["reconciliation"]["expected_cash"] == "60.00"
    assert refund_response.status_code == 201
    assert second_close.status_code == 200, second_close.json
    assert second_close.json["reconciliation"] == {
        "opening_float": "50.00",
        "cash_sales_total": "0.00",
        "cash_refunds_total": "10.00",
        "expected_cash": "40.00",
        "closing_cash": "40.00",
        "cash_difference": "0.00",
    }


def test_non_cash_refund_does_not_reduce_expected_cash(client):
    shift = add_open_shift(
        shift_id="a7070707-a707-4707-8707-a70707070707",
    )
    checkout_response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(
            payment_method_id=CARD_PAYMENT_METHOD_ID,
        ),
    )
    assert checkout_response.status_code == 201, checkout_response.json
    sale_id = checkout_response.json["item"]["id"]
    sale_item_id = checkout_response.json["item"]["items"][0]["id"]

    refund_response = client.post(
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
    close_response = client.post(
        f"/api/till-shifts/{shift.id}/close",
        json={"closing_cash": "50.00"},
    )

    assert refund_response.status_code == 201
    assert close_response.status_code == 200
    assert close_response.json["reconciliation"] == {
        "opening_float": "50.00",
        "cash_sales_total": "0.00",
        "cash_refunds_total": "0.00",
        "expected_cash": "50.00",
        "closing_cash": "50.00",
        "cash_difference": "0.00",
    }


def test_checkout_rejects_client_warehouse_that_does_not_match_till(client):
    add_open_shift()

    response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(warehouse_id=OTHER_WAREHOUSE_ID),
    )

    assert response.status_code == 400
    assert response.json["error"] == (
        "warehouse_id must match the selected till warehouse."
    )
    assert db.session.query(Sale).count() == 0
    assert db.session.query(InventoryMovement).count() == 0


def test_checkout_rejects_shift_owned_by_another_session(client):
    add_open_shift(
        active_session_id=OTHER_SESSION_ID,
    )

    response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(),
    )

    assert response.status_code == 400
    assert response.json["error"] == (
        "This till shift is active on another session."
    )
    assert db.session.query(Sale).count() == 0
    assert db.session.query(InventoryMovement).count() == 0


def test_checkout_uses_default_sale_price_when_unit_price_is_omitted(client):
    add_open_shift()

    response = client.post(
        "/api/sales/checkout",
        json={
            "warehouse_id": WAREHOUSE_ID,
            "till_id": TILL_ID,
            "items": [
                {
                    "product_id": PRODUCT_ID,
                    "quantity": "2",
                }
            ],
            "payments": [
                {
                    "payment_method_id": PAYMENT_METHOD_ID,
                    "amount": "20.00",
                }
            ],
        },
    )

    assert response.status_code == 201
    assert response.json["item"]["subtotal"] == "20.00"
    assert response.json["item"]["total_amount"] == "20.00"
    assert response.json["item"]["items"][0]["unit_price"] == "10.00"


@pytest.mark.parametrize(
    ("unit_price", "payment_amount"),
    [
        ("8.00", "8.00"),
        ("9.00", "9.00"),
        ("9.99", "9.99"),
        ("10.00", "10.00"),
        ("10.01", "10.01"),
        ("12.00", "12.00"),
    ],
)
def test_checkout_allows_unit_price_at_or_above_minimum(
    client,
    unit_price: str,
    payment_amount: str,
):
    add_open_shift()

    response = client.post(
        "/api/sales/checkout",
        json={
            "warehouse_id": WAREHOUSE_ID,
            "till_id": TILL_ID,
            "items": [
                {
                    "product_id": PRODUCT_ID,
                    "quantity": "1",
                    "unit_price": unit_price,
                }
            ],
            "payments": [
                {
                    "payment_method_id": PAYMENT_METHOD_ID,
                    "amount": payment_amount,
                }
            ],
        },
    )

    assert response.status_code == 201
    assert (
        response.json["item"]["items"][0]["unit_price"]
        == unit_price
    )
    assert (
        response.json["item"]["total_amount"]
        == payment_amount
    )


@pytest.mark.parametrize(
    "unit_price",
    [
        "0.00",
        "7.99",
    ],
)
def test_checkout_rejects_unit_price_below_minimum(
    client,
    unit_price: str,
):
    add_open_shift()

    response = client.post(
        "/api/sales/checkout",
        json={
            "warehouse_id": WAREHOUSE_ID,
            "till_id": TILL_ID,
            "items": [
                {
                    "product_id": PRODUCT_ID,
                    "quantity": "1",
                    "unit_price": unit_price,
                }
            ],
            "payments": [
                {
                    "payment_method_id": PAYMENT_METHOD_ID,
                    "amount": "10.00",
                }
            ],
        },
    )

    assert response.status_code == 400
    assert (
        "unit_price cannot be below min_sale_price"
        in response.json["error"]
    )

    assert db.session.query(Sale).count() == 0
    assert db.session.query(SaleItem).count() == 0
    assert db.session.query(SalePayment).count() == 0
    assert db.session.query(InventoryMovement).count() == 0


def test_checkout_rejects_product_without_default_sale_price(client):
    add_open_shift()
    product = db.session.get(Product, PRODUCT_ID)
    product.default_sale_price = None
    db.session.commit()

    response = client.post(
        "/api/sales/checkout",
        json={
            "warehouse_id": WAREHOUSE_ID,
            "till_id": TILL_ID,
            "items": [
                {
                    "product_id": PRODUCT_ID,
                    "quantity": "1",
                }
            ],
            "payments": [
                {
                    "payment_method_id": PAYMENT_METHOD_ID,
                    "amount": "10.00",
                }
            ],
        },
    )

    assert response.status_code == 400
    assert response.json["error"] == (
        f"default_sale_price is required before product_id={PRODUCT_ID} can be sold."
    )
    assert db.session.query(Sale).count() == 0


def test_checkout_rejects_product_price_below_min_sale_price(client):
    add_open_shift()
    product = db.session.get(Product, PRODUCT_ID)
    product.default_sale_price = Decimal("7.99")
    db.session.commit()

    response = client.post(
        "/api/sales/checkout",
        json={
            "warehouse_id": WAREHOUSE_ID,
            "till_id": TILL_ID,
            "items": [
                {
                    "product_id": PRODUCT_ID,
                    "quantity": "1",
                }
            ],
            "payments": [
                {
                    "payment_method_id": PAYMENT_METHOD_ID,
                    "amount": "10.00",
                }
            ],
        },
    )

    assert response.status_code == 400
    assert response.json["error"] == (
        f"default_sale_price cannot be below min_sale_price for product_id={PRODUCT_ID}."
    )
    assert db.session.query(Sale).count() == 0


def test_checkout_rejects_inactive_product(client):
    add_open_shift()
    product = db.session.get(Product, PRODUCT_ID)
    product.is_active = False
    db.session.commit()

    response = client.post(
        "/api/sales/checkout",
        json={
            "warehouse_id": WAREHOUSE_ID,
            "till_id": TILL_ID,
            "items": [
                {
                    "product_id": PRODUCT_ID,
                    "quantity": "1",
                }
            ],
            "payments": [
                {
                    "payment_method_id": PAYMENT_METHOD_ID,
                    "amount": "10.00",
                }
            ],
        },
    )

    assert response.status_code == 400
    assert response.json["error"] == (
        f"Product is inactive and cannot be sold for product_id={PRODUCT_ID}."
    )
    assert db.session.query(Sale).count() == 0


def test_checkout_rejects_cross_tenant_product(client):
    add_open_shift()
    other_product_id = "bbbbbbbb-bbbb-4bbb-bbbb-cccccccccccc"
    db.session.add(
        Product(
            id=other_product_id,
            tenant_id=OTHER_TENANT_ID,
            internal_sku="SKU-OTHER",
            name="Other Tenant Product",
            default_sale_price=Decimal("10.00"),
        )
    )
    db.session.commit()

    response = client.post(
        "/api/sales/checkout",
        json={
            "warehouse_id": WAREHOUSE_ID,
            "till_id": TILL_ID,
            "items": [
                {
                    "product_id": other_product_id,
                    "quantity": "1",
                }
            ],
            "payments": [
                {
                    "payment_method_id": PAYMENT_METHOD_ID,
                    "amount": "10.00",
                }
            ],
        },
    )

    assert response.status_code == 400
    assert response.json["error"] == (
        f"Product not found for product_id={other_product_id}."
    )
    assert db.session.query(Sale).count() == 0


def test_checkout_rejects_positive_line_discount(client):
    add_open_shift()

    response = client.post(
        "/api/sales/checkout",
        json={
            "warehouse_id": WAREHOUSE_ID,
            "till_id": TILL_ID,
            "items": [
                {
                    "product_id": PRODUCT_ID,
                    "quantity": "1",
                    "discount_amount": "1.00",
                }
            ],
            "payments": [
                {
                    "payment_method_id": PAYMENT_METHOD_ID,
                    "amount": "10.00",
                }
            ],
        },
    )

    assert response.status_code == 400
    assert response.json["error"] == (
        f"discount_amount is not supported for POS checkout product_id={PRODUCT_ID}."
    )
    assert db.session.query(Sale).count() == 0


def test_checkout_rejects_positive_line_tax(client):
    add_open_shift()

    response = client.post(
        "/api/sales/checkout",
        json={
            "warehouse_id": WAREHOUSE_ID,
            "till_id": TILL_ID,
            "items": [
                {
                    "product_id": PRODUCT_ID,
                    "quantity": "1",
                    "tax_amount": "1.00",
                }
            ],
            "payments": [
                {
                    "payment_method_id": PAYMENT_METHOD_ID,
                    "amount": "10.00",
                }
            ],
        },
    )

    assert response.status_code == 400
    assert response.json["error"] == (
        f"tax_amount is not supported for POS checkout product_id={PRODUCT_ID}."
    )
    assert db.session.query(Sale).count() == 0


def test_checkout_calculates_balance_from_server_price(client):
    add_open_shift()

    response = client.post(
        "/api/sales/checkout",
        json={
            "warehouse_id": WAREHOUSE_ID,
            "till_id": TILL_ID,
            "items": [
                {
                    "product_id": PRODUCT_ID,
                    "quantity": "1",
                }
            ],
            "payments": [
                {
                    "payment_method_id": PAYMENT_METHOD_ID,
                    "amount": "9.00",
                }
            ],
        },
    )

    assert response.status_code == 201
    assert response.json["item"]["total_amount"] == "10.00"
    assert response.json["item"]["paid_amount"] == "9.00"
    assert response.json["item"]["balance_due"] == "1.00"
    assert response.json["item"]["status"] == "partially_paid"


def test_checkout_rejects_insufficient_stock(client):
    add_open_shift()

    response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(quantity="11", payment_amount="110.00"),
    )

    assert response.status_code == 400
    assert response.json["error"] == (
        f"Insufficient stock for product_id={PRODUCT_ID}. "
        "Available=10.0000, requested=11.0000."
    )
    assert db.session.query(Sale).count() == 0


def test_checkout_rejects_expired_only_batch_stock(client):
    add_open_shift()
    replace_batches(
        make_batch(
            EXPIRED_BATCH_ID,
            quantity="10.0000",
            expiry_date=date.today() - timedelta(days=1),
        )
    )
    db.session.commit()

    response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(),
    )

    assert response.status_code == 400
    assert response.json["error"] == (
        f"Insufficient sellable batch stock for product_id={PRODUCT_ID}. "
        "Available=0.0000, requested=1.0000."
    )
    assert db.session.get(InventoryBatch, EXPIRED_BATCH_ID).quantity_on_hand == Decimal("10.0000")
    assert db.session.query(InventoryMovement).count() == 0


def test_checkout_excludes_expired_stock_when_valid_stock_exists(client):
    add_open_shift()
    set_stock_balance(on_hand="10.0000")
    replace_batches(
        make_batch(
            EXPIRED_BATCH_ID,
            quantity="7.0000",
            expiry_date=date.today() - timedelta(days=1),
        ),
        make_batch(
            BATCH_ID,
            quantity="3.0000",
            expiry_date=date.today() + timedelta(days=20),
        ),
    )
    db.session.commit()

    response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(quantity="3", payment_amount="30.00"),
    )

    assert response.status_code == 201
    assert db.session.get(InventoryBatch, EXPIRED_BATCH_ID).quantity_on_hand == Decimal("7.0000")
    assert db.session.get(InventoryBatch, BATCH_ID).quantity_on_hand == Decimal("0.0000")

    movement = db.session.query(InventoryMovement).one()
    assert movement.batch_id == BATCH_ID
    assert movement.quantity == Decimal("-3.0000")


def test_checkout_allocates_across_batches_in_fefo_order(client):
    add_open_shift()
    set_stock_balance(on_hand="5.0000")
    replace_batches(
        make_batch(
            BATCH_ID,
            quantity="2.0000",
            expiry_date=date.today() + timedelta(days=5),
            unit_cost="1.10",
        ),
        make_batch(
            SECOND_BATCH_ID,
            quantity="3.0000",
            expiry_date=date.today() + timedelta(days=30),
            unit_cost="1.20",
        ),
    )
    db.session.commit()

    response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(quantity="4", payment_amount="40.00"),
    )

    assert response.status_code == 201
    assert db.session.get(InventoryBatch, BATCH_ID).quantity_on_hand == Decimal("0.0000")
    assert db.session.get(InventoryBatch, SECOND_BATCH_ID).quantity_on_hand == Decimal("1.0000")

    movements = {
        movement.batch_id: movement
        for movement in db.session.query(InventoryMovement).all()
    }
    assert movements[BATCH_ID].quantity == Decimal("-2.0000")
    assert movements[BATCH_ID].unit_cost == Decimal("1.10")
    assert movements[SECOND_BATCH_ID].quantity == Decimal("-2.0000")
    assert movements[SECOND_BATCH_ID].unit_cost == Decimal("1.20")

    sale_item = db.session.query(SaleItem).one()
    assert sale_item.batch_id is None


def test_checkout_rejects_when_only_other_branch_stock_exists(client):
    add_open_shift()
    set_stock_balance(on_hand="0.0000")
    set_stock_balance(
        warehouse_id=OTHER_BRANCH_WAREHOUSE_ID,
        branch_id=OTHER_BRANCH_ID,
        on_hand="10.0000",
    )
    replace_batches(
        make_batch(
            SECOND_BATCH_ID,
            warehouse_id=OTHER_BRANCH_WAREHOUSE_ID,
            quantity="10.0000",
            expiry_date=date.today() + timedelta(days=30),
        )
    )
    db.session.commit()

    response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(),
    )

    assert response.status_code == 400
    assert response.json["error"] == (
        f"Insufficient stock for product_id={PRODUCT_ID}. "
        "Available=0.0000, requested=1.0000."
    )
    assert db.session.query(Sale).count() == 0


def test_checkout_rejects_when_only_other_warehouse_stock_exists(client):
    add_open_shift()
    set_stock_balance(on_hand="0.0000")
    set_stock_balance(
        warehouse_id=OTHER_WAREHOUSE_ID,
        on_hand="10.0000",
    )
    replace_batches(
        make_batch(
            SECOND_BATCH_ID,
            warehouse_id=OTHER_WAREHOUSE_ID,
            quantity="10.0000",
            expiry_date=date.today() + timedelta(days=30),
        )
    )
    db.session.commit()

    response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(),
    )

    assert response.status_code == 400
    assert response.json["error"] == (
        f"Insufficient stock for product_id={PRODUCT_ID}. "
        "Available=0.0000, requested=1.0000."
    )
    assert db.session.query(Sale).count() == 0


def test_checkout_rejects_when_only_other_tenant_stock_exists(client):
    add_open_shift()
    set_stock_balance(on_hand="0.0000")
    db.session.add(
        StockBalance(
            tenant_id=OTHER_TENANT_ID,
            branch_id=OTHER_BRANCH_ID,
            warehouse_id=OTHER_TENANT_WAREHOUSE_ID,
            product_id=PRODUCT_ID,
            quantity_on_hand=Decimal("10.0000"),
            quantity_available=Decimal("10.0000"),
            quantity_reserved=Decimal("0.0000"),
            avg_unit_cost=Decimal("1.00"),
        )
    )
    replace_batches(
        make_batch(
            SECOND_BATCH_ID,
            tenant_id=OTHER_TENANT_ID,
            warehouse_id=OTHER_TENANT_WAREHOUSE_ID,
            quantity="10.0000",
            expiry_date=date.today() + timedelta(days=30),
        )
    )
    db.session.commit()

    response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(),
    )

    assert response.status_code == 400
    assert response.json["error"] == (
        f"Insufficient stock for product_id={PRODUCT_ID}. "
        "Available=0.0000, requested=1.0000."
    )
    assert db.session.query(Sale).count() == 0


def test_checkout_allows_non_inventory_product_without_stock(client):
    add_open_shift()
    product = db.session.get(Product, PRODUCT_ID)
    product.track_inventory = False
    product.track_batches = False
    product.track_expiry = False
    db.session.query(InventoryBatch).delete()
    db.session.query(StockBalance).delete()
    db.session.commit()

    response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(),
    )

    assert response.status_code == 201
    assert db.session.query(InventoryMovement).count() == 0


def test_checkout_rolls_back_inventory_when_commit_fails(
    client,
    monkeypatch: pytest.MonkeyPatch,
):
    add_open_shift()

    def fail_commit():
        raise SQLAlchemyError("forced commit failure")

    monkeypatch.setattr(db.session, "commit", fail_commit)

    response = client.post(
        "/api/sales/checkout",
        json=checkout_payload(),
    )

    assert response.status_code == 500
    assert db.session.get(StockBalance, "dddddddd-dddd-dddd-dddd-dddddddddddd").quantity_on_hand == Decimal("10.0000")
    assert db.session.get(InventoryBatch, BATCH_ID).quantity_on_hand == Decimal("10.0000")
    assert db.session.query(InventoryMovement).count() == 0


def test_checkout_rejects_cross_tenant_till_shift(client):
    add_open_shift(tenant_id=OTHER_TENANT_ID)

    response = client.post(
        "/api/sales/checkout",
        json={
            "warehouse_id": WAREHOUSE_ID,
            "till_id": TILL_ID,
            "items": [
                {
                    "product_id": PRODUCT_ID,
                    "quantity": "1",
                    "unit_price": "10.00",
                }
            ],
            "payments": [
                {
                    "payment_method_id": PAYMENT_METHOD_ID,
                    "amount": "10.00",
                }
            ],
        },
    )

    assert response.status_code == 400
    assert response.json["error"] == (
        "No open shift found for this till and cashier."
    )
    assert db.session.query(Sale).count() == 0


def test_checkout_rejects_cross_branch_till_shift(client):
    add_open_shift(branch_id=OTHER_BRANCH_ID)

    response = client.post(
        "/api/sales/checkout",
        json={
            "warehouse_id": WAREHOUSE_ID,
            "till_id": TILL_ID,
            "items": [
                {
                    "product_id": PRODUCT_ID,
                    "quantity": "1",
                    "unit_price": "10.00",
                }
            ],
            "payments": [
                {
                    "payment_method_id": PAYMENT_METHOD_ID,
                    "amount": "10.00",
                }
            ],
        },
    )

    assert response.status_code == 400
    assert response.json["error"] == (
        "No open shift found for this till and cashier."
    )
    assert db.session.query(Sale).count() == 0


def test_checkout_rejects_mismatched_till_shift(client):
    add_open_shift(till_id=SECOND_TILL_ID)

    response = client.post(
        "/api/sales/checkout",
        json={
            "warehouse_id": WAREHOUSE_ID,
            "till_id": TILL_ID,
            "items": [
                {
                    "product_id": PRODUCT_ID,
                    "quantity": "1",
                    "unit_price": "10.00",
                }
            ],
            "payments": [
                {
                    "payment_method_id": PAYMENT_METHOD_ID,
                    "amount": "10.00",
                }
            ],
        },
    )

    assert response.status_code == 400
    assert response.json["error"] == (
        "No open shift found for this till and cashier."
    )
    assert db.session.query(Sale).count() == 0


# ============================================================================
# Till shift session takeover
# ============================================================================


def test_takeover_shift_transfers_session_ownership(app_context):
    previous_session = add_user_session(
        session_id=OTHER_SESSION_ID,
    )
    shift = add_open_shift(
        active_session_id=OTHER_SESSION_ID,
    )

    service = TillShiftService(db.session)

    result = service.takeover_shift(
        tenant_id=TENANT_ID,
        branch_id=BRANCH_ID,
        cashier_id=USER_ID,
        session_id=SESSION_ID,
        shift_id=shift.id,
    )

    db.session.expire_all()

    persisted_shift = db.session.get(
        TillShift,
        shift.id,
    )
    persisted_previous_session = db.session.get(
        UserSession,
        previous_session.id,
    )

    assert result.id == shift.id
    assert persisted_shift is not None
    assert persisted_shift.status == "open"
    assert persisted_shift.closed_at is None
    assert persisted_shift.active_session_id == SESSION_ID

    assert persisted_previous_session is not None
    assert persisted_previous_session.is_revoked
    assert (
        persisted_previous_session.revoke_reason
        == TokenRevocationReason.SESSION_TAKEOVER
    )


def test_takeover_shift_revokes_previous_session_refresh_tokens(
    app_context,
):
    previous_session = add_user_session(
        session_id=OTHER_SESSION_ID,
    )
    shift = add_open_shift(
        active_session_id=OTHER_SESSION_ID,
    )

    now = datetime.now(timezone.utc)

    refresh_token = RefreshToken(
        id="67676767-6767-4767-8767-676767676767",
        tenant_id=TENANT_ID,
        user_id=USER_ID,
        session_id=previous_session.id,
        jwt_id="takeover-refresh-jti",
        token_family="takeover-refresh-family",
        expires_at=now + timedelta(hours=8),
    )

    db.session.add(refresh_token)
    db.session.commit()

    service = TillShiftService(db.session)

    service.takeover_shift(
        tenant_id=TENANT_ID,
        branch_id=BRANCH_ID,
        cashier_id=USER_ID,
        session_id=SESSION_ID,
        shift_id=shift.id,
    )

    db.session.expire_all()

    persisted_token = db.session.get(
        RefreshToken,
        refresh_token.id,
    )

    assert persisted_token is not None
    assert persisted_token.is_revoked
    assert (
        persisted_token.revoke_reason
        == TokenRevocationReason.SESSION_TAKEOVER
    )
    assert persisted_token.revoked_by_user_id == USER_ID


def test_takeover_shift_is_idempotent_for_current_owner(
    app_context,
):
    shift = add_open_shift(
        active_session_id=SESSION_ID,
    )

    service = TillShiftService(db.session)

    result = service.takeover_shift(
        tenant_id=TENANT_ID,
        branch_id=BRANCH_ID,
        cashier_id=USER_ID,
        session_id=SESSION_ID,
        shift_id=shift.id,
    )

    db.session.expire_all()

    persisted = db.session.get(
        TillShift,
        shift.id,
    )

    assert result.id == shift.id
    assert persisted is not None
    assert persisted.status == "open"
    assert persisted.closed_at is None
    assert persisted.active_session_id == SESSION_ID


def test_takeover_shift_rejects_unknown_requesting_session(
    app_context,
):
    shift = add_open_shift(
        active_session_id=OTHER_SESSION_ID,
    )

    service = TillShiftService(db.session)

    with pytest.raises(Exception) as exc_info:
        service.takeover_shift(
            tenant_id=TENANT_ID,
            branch_id=BRANCH_ID,
            cashier_id=USER_ID,
            session_id="56565656-5656-4565-8565-565656565656",
            shift_id=shift.id,
        )

    assert (
        "Authenticated session is not valid for this cashier."
        in str(exc_info.value)
    )

    db.session.expire_all()

    persisted = db.session.get(
        TillShift,
        shift.id,
    )

    assert persisted is not None
    assert persisted.active_session_id == OTHER_SESSION_ID

