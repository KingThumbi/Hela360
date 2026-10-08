from __future__ import annotations

from types import SimpleNamespace

import pytest
from flask import Flask

from app.api.errors import register_error_handlers
from app.api.finance_accounts import bp as finance_accounts_bp
from app.auth.exceptions import PermissionDeniedError
from app.extensions import db
from app.models import Branch, ChartOfAccount, Tenant


@pytest.fixture()
def app_context():
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TESTING=True,
    )
    db.init_app(app)
    app.register_blueprint(finance_accounts_bp, url_prefix="/api")
    register_error_handlers(app)

    with app.app_context():
        Tenant.__table__.create(db.engine)
        Branch.__table__.create(db.engine)
        ChartOfAccount.__table__.create(db.engine)

        db.session.add_all(
            [
                Tenant(
                    id="tenant-1",
                    legal_name="Tenant 1",
                    display_name="Tenant 1",
                    base_currency="KES",
                ),
                Tenant(
                    id="tenant-2",
                    legal_name="Tenant 2",
                    display_name="Tenant 2",
                    base_currency="KES",
                ),
                Branch(
                    id="branch-1",
                    tenant_id="tenant-1",
                    code="MAIN",
                    name="Main",
                    is_head_office=True,
                    is_active=True,
                ),
                Branch(
                    id="branch-2",
                    tenant_id="tenant-1",
                    code="ALT",
                    name="Alt",
                    is_active=True,
                ),
            ]
        )
        db.session.commit()

        yield app

        db.session.remove()
        ChartOfAccount.__table__.drop(db.engine)
        Branch.__table__.drop(db.engine)
        Tenant.__table__.drop(db.engine)


@pytest.fixture()
def client(app_context, monkeypatch: pytest.MonkeyPatch):
    identity = SimpleNamespace(
        user_id="user-1",
        tenant_id="tenant-1",
        branch_id="branch-1",
    )
    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.get_current_identity",
        lambda: identity,
    )
    monkeypatch.setattr(
        "app.auth.jwt.get_current_identity",
        lambda: identity,
    )
    monkeypatch.setattr(
        "app.api.finance_accounts._current_identity",
        lambda: identity,
    )
    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.authorization_service.authorize",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "app.services.tenant.finance.chart_of_accounts_service.audit_service.log",
        lambda **kwargs: None,
    )
    return app_context.test_client()


def add_account(
    tenant_id: str,
    code: str,
    name: str,
    *,
    branch_id: str | None = None,
    account_type: str = "asset",
    normal_balance: str = "debit",
    parent_id: str | None = None,
    is_active: bool = True,
    is_system_account: bool = False,
) -> ChartOfAccount:
    account = ChartOfAccount(
        tenant_id=tenant_id,
        branch_id=branch_id,
        account_code=code,
        account_name=name,
        account_type=account_type,
        normal_balance=normal_balance,
        parent_id=parent_id,
        is_active=is_active,
        is_system_account=is_system_account,
        currency="KES",
    )
    db.session.add(account)
    db.session.flush()
    return account


def test_list_is_tenant_and_branch_scoped(client):
    global_account = add_account("tenant-1", "1000", "Cash")
    own_branch = add_account(
        "tenant-1", "1010", "Main Cash", branch_id="branch-1"
    )
    other_branch = add_account(
        "tenant-1", "1020", "Other Cash", branch_id="branch-2"
    )
    hidden_tenant = add_account("tenant-2", "1000", "Hidden Cash")
    db.session.commit()

    response = client.get("/api/finance/accounts")

    assert response.status_code == 200
    ids = {item["id"] for item in response.json["items"]}
    assert ids == {global_account.id, own_branch.id}
    assert other_branch.id not in ids
    assert hidden_tenant.id not in ids


def test_detail_hides_other_branch(client):
    account = add_account(
        "tenant-1", "1020", "Other Branch", branch_id="branch-2"
    )
    db.session.commit()

    response = client.get(f"/api/finance/accounts/{account.id}")
    assert response.status_code == 404


def test_create_defaults_currency_to_tenant_base_currency(client):
    response = client.post(
        "/api/finance/accounts",
        json={
            "account_code": "6100",
            "account_name": "Consumables",
            "account_type": "expense",
            "branch_id": "branch-1",
        },
    )

    assert response.status_code == 201
    assert response.json["item"]["currency"] == "KES"
    assert response.json["item"]["normal_balance"] == "debit"
    assert response.json["item"]["branch_id"] == "branch-1"


def test_branch_user_cannot_create_tenant_wide_account(client):
    response = client.post(
        "/api/finance/accounts",
        json={
            "account_code": "2000",
            "account_name": "Accounts Payable",
            "account_type": "liability",
            "branch_id": None,
        },
    )
    assert response.status_code == 403


def test_deactivation_of_parent_with_active_child_is_rejected(client):
    parent = add_account(
        "tenant-1",
        "6000",
        "Operating Expenses",
        branch_id="branch-1",
        account_type="expense",
    )
    add_account(
        "tenant-1",
        "6100",
        "Consumables",
        branch_id="branch-1",
        account_type="expense",
        parent_id=parent.id,
    )
    db.session.commit()

    response = client.patch(
        f"/api/finance/accounts/{parent.id}",
        json={"is_active": False},
    )

    assert response.status_code == 400
    assert "active child" in response.json["error"]


def test_branch_user_cannot_update_tenant_wide_account(client):
    account = add_account(
        "tenant-1",
        "1000",
        "Cash",
    )
    db.session.commit()

    response = client.patch(
        f"/api/finance/accounts/{account.id}",
        json={"account_name": "Renamed Cash"},
    )

    assert response.status_code == 403
    assert "tenant-wide" in response.json["error"]


def test_system_account_structure_is_protected(client):
    account = add_account(
        "tenant-1",
        "1000",
        "Cash",
        branch_id="branch-1",
        is_system_account=True,
    )
    db.session.commit()

    response = client.patch(
        f"/api/finance/accounts/{account.id}",
        json={"account_type": "expense"},
    )
    assert response.status_code == 400


def test_missing_permission_is_rejected(app_context, monkeypatch: pytest.MonkeyPatch):
    identity = SimpleNamespace(
        user_id="user-1",
        tenant_id="tenant-1",
        branch_id=None,
    )
    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.get_current_identity",
        lambda: identity,
    )
    monkeypatch.setattr(
        "app.auth.jwt.get_current_identity",
        lambda: identity,
    )
    monkeypatch.setattr(
        "app.api.finance_accounts._current_identity",
        lambda: identity,
    )
    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.authorization_service.authorize",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            PermissionDeniedError("Permission denied.")
        ),
    )

    response = app_context.test_client().get("/api/finance/accounts")
    assert response.status_code == 403
    assert response.json["error"]["code"] == "AUTHORIZATION_DENIED"
