from __future__ import annotations

from types import SimpleNamespace

import pytest
from flask import Flask

from app.api.errors import register_error_handlers
from app.api.payment_methods import bp as payment_methods_bp
from app.api.sales import validate_payments
from app.auth.exceptions import PermissionDeniedError
from app.extensions import db
from app.models import PaymentMethod, Tenant


@pytest.fixture()
def app_context():
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TESTING=True,
    )
    db.init_app(app)
    app.register_blueprint(payment_methods_bp, url_prefix="/api")

    with app.app_context():
        Tenant.__table__.create(db.engine)
        PaymentMethod.__table__.create(db.engine)

        db.session.add_all(
            [
                Tenant(
                    id="tenant-1",
                    legal_name="Tenant 1",
                    display_name="Tenant 1",
                ),
                Tenant(
                    id="tenant-2",
                    legal_name="Tenant 2",
                    display_name="Tenant 2",
                ),
            ]
        )
        db.session.commit()

        yield app

        db.session.remove()
        PaymentMethod.__table__.drop(db.engine)
        Tenant.__table__.drop(db.engine)


@pytest.fixture()
def identity():
    return SimpleNamespace(
        user_id="user-1",
        tenant_id="tenant-1",
        branch_id="branch-1",
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
        "app.api.payment_methods._current_identity",
        lambda: identity,
    )
    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.authorization_service.authorize",
        lambda *args, **kwargs: None,
    )

    return app_context.test_client()


def add_payment_method(
    tenant_id: str,
    code: str,
    name: str,
    *,
    method_type: str = "cash",
    is_active: bool = True,
) -> PaymentMethod:
    payment_method = PaymentMethod(
        tenant_id=tenant_id,
        code=code,
        name=name,
        method_type=method_type,
        is_active=is_active,
    )
    db.session.add(payment_method)
    db.session.flush()
    return payment_method


def test_payment_methods_list_returns_active_tenant_methods_in_order(client):
    mpesa = add_payment_method(
        "tenant-1",
        "mpesa",
        "M-Pesa",
        method_type="mpesa",
    )
    card = add_payment_method("tenant-1", "card", "Card", method_type="card")
    cash = add_payment_method("tenant-1", "cash", "Cash")
    add_payment_method(
        "tenant-1",
        "bank",
        "Bank Transfer",
        method_type="bank",
        is_active=False,
    )
    add_payment_method("tenant-2", "cash", "Tenant Two Cash")
    db.session.commit()

    response = client.get("/api/payment-methods")

    assert response.status_code == 200
    assert response.json == {
        "ok": True,
        "items": [
            {
                "id": card.id,
                "code": "card",
                "name": "Card",
                "method_type": "card",
                "is_active": True,
            },
            {
                "id": cash.id,
                "code": "cash",
                "name": "Cash",
                "method_type": "cash",
                "is_active": True,
            },
            {
                "id": mpesa.id,
                "code": "mpesa",
                "name": "M-Pesa",
                "method_type": "mpesa",
                "is_active": True,
            },
        ],
    }


def test_payment_methods_list_requires_authentication(
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

    response = app_context.test_client().get("/api/payment-methods")

    assert response.status_code == 401


def test_payment_methods_list_enforces_sales_create_permission(
    app_context,
    identity: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
):
    register_error_handlers(app_context)

    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.get_current_identity",
        lambda: identity,
    )
    monkeypatch.setattr(
        "app.auth.jwt.get_current_identity",
        lambda: identity,
    )
    monkeypatch.setattr(
        "app.api.payment_methods._current_identity",
        lambda: identity,
    )
    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.authorization_service.authorize",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            PermissionDeniedError("Permission denied.")
        ),
    )

    response = app_context.test_client().get("/api/payment-methods")

    assert response.status_code == 403
    assert response.json["error"]["code"] == "AUTHORIZATION_DENIED"


def test_returned_payment_method_id_is_accepted_by_checkout_validation(client):
    payment_method = add_payment_method("tenant-1", "cash", "Cash")
    db.session.commit()

    response = client.get("/api/payment-methods")
    returned_id = response.json["items"][0]["id"]

    total_paid = validate_payments(
        "tenant-1",
        [
            {
                "payment_method_id": returned_id,
                "amount": "25.50",
            }
        ],
    )

    assert returned_id == payment_method.id
    assert str(total_paid) == "25.50"


def test_checkout_validation_rejects_inactive_payment_method(client):
    payment_method = add_payment_method(
        "tenant-1",
        "cash",
        "Cash",
        is_active=False,
    )
    db.session.commit()

    with pytest.raises(
        ValueError,
        match="Active payment method not found for payment #1.",
    ):
        validate_payments(
            "tenant-1",
            [
                {
                    "payment_method_id": payment_method.id,
                    "amount": "10.00",
                }
            ],
        )
