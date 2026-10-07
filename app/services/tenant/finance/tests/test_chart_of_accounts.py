from __future__ import annotations

import pytest
from flask import Flask

from app.auth.permissions import Permissions
from app.extensions import db
from app.models import Branch, ChartOfAccount, Permission, Tenant
from app.services.platform.permission_catalogue_service import (
    PermissionCatalogueService,
)
from app.services.tenant.finance import ChartOfAccountsService, DEFAULT_CHART


@pytest.fixture()
def app_context(monkeypatch: pytest.MonkeyPatch):
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TESTING=True,
    )
    db.init_app(app)

    with app.app_context():
        Tenant.__table__.create(db.engine)
        Branch.__table__.create(db.engine)
        ChartOfAccount.__table__.create(db.engine)
        Permission.__table__.create(db.engine)

        db.session.add(
            Tenant(
                id="tenant-1",
                legal_name="Tenant 1",
                display_name="Tenant 1",
                base_currency="KES",
            )
        )
        db.session.commit()

        monkeypatch.setattr(
            "app.services.tenant.finance.chart_of_accounts_service.audit_service.log",
            lambda **kwargs: None,
        )

        yield app

        db.session.remove()
        Permission.__table__.drop(db.engine)
        ChartOfAccount.__table__.drop(db.engine)
        Branch.__table__.drop(db.engine)
        Tenant.__table__.drop(db.engine)


def test_default_chart_is_complete_and_idempotent(app_context):
    service = ChartOfAccountsService(db.session)

    first = service.seed_default_chart("tenant-1")
    db.session.commit()

    second = service.seed_default_chart("tenant-1")
    db.session.commit()

    assert len(first.created) == len(DEFAULT_CHART)
    assert len(second.created) == 0
    assert len(second.unchanged) == len(DEFAULT_CHART)
    assert (
        ChartOfAccount.query.filter_by(tenant_id="tenant-1").count()
        == len(DEFAULT_CHART)
    )

    parent_codes = {
        account.account_code: account.parent.account_code
        for account in ChartOfAccount.query.filter(
            ChartOfAccount.tenant_id == "tenant-1",
            ChartOfAccount.parent_id.isnot(None),
        )
    }
    assert parent_codes["1010"] == "1000"
    assert parent_codes["6100"] == "6000"


def test_incompatible_existing_account_causes_seed_conflict(app_context):
    db.session.add(
        ChartOfAccount(
            tenant_id="tenant-1",
            account_code="1000",
            account_name="Business-defined Cash",
            account_type="expense",
            normal_balance="debit",
            is_active=True,
            is_system_account=False,
            currency="KES",
        )
    )
    db.session.commit()

    with pytest.raises(Exception) as exc_info:
        ChartOfAccountsService(db.session).seed_default_chart("tenant-1")

    assert "conflict" in str(exc_info.value).lower()


def test_permission_catalogue_contains_all_minimum_finance_permissions(app_context):
    result = PermissionCatalogueService(db.session).synchronize()
    db.session.commit()

    required = {
        Permissions.FINANCE_DASHBOARD_READ,
        Permissions.FINANCE_ACCOUNTS_READ,
        Permissions.FINANCE_ACCOUNTS_CREATE,
        Permissions.FINANCE_ACCOUNTS_UPDATE,
        Permissions.FINANCE_JOURNALS_READ,
        Permissions.FINANCE_JOURNALS_CREATE,
        Permissions.FINANCE_JOURNALS_POST,
        Permissions.FINANCE_JOURNALS_REVERSE,
        Permissions.FINANCE_AR_READ,
        Permissions.FINANCE_AR_ADJUST,
        Permissions.FINANCE_AP_READ,
        Permissions.FINANCE_AP_ADJUST,
        Permissions.FINANCE_EXPENSES_READ,
        Permissions.FINANCE_EXPENSES_CREATE,
        Permissions.FINANCE_EXPENSES_APPROVE,
        Permissions.FINANCE_EXPENSES_POST,
        Permissions.FINANCE_REPORTS_READ,
    }

    assert required.issubset(set(result.created))


def test_create_string_false_does_not_activate_account(app_context):
    service = ChartOfAccountsService(db.session)

    account = service.create_account(
        "tenant-1",
        account_code="9991",
        account_name="Inactive Test Account",
        account_type="asset",
        is_active="false",
    )

    assert account.is_active is False


def test_update_string_false_deactivates_account(app_context):
    service = ChartOfAccountsService(db.session)

    account = service.create_account(
        "tenant-1",
        account_code="9992",
        account_name="Update Boolean Test",
        account_type="asset",
        is_active=True,
    )
    db.session.commit()

    service.update_account(
        "tenant-1",
        account.id,
        fields={"is_active": "false"},
    )

    assert account.is_active is False


def test_account_type_and_normal_balance_are_coherent(app_context):
    service = ChartOfAccountsService(db.session)

    with pytest.raises(Exception):
        service.create_account(
            "tenant-1",
            account_code="9990",
            account_name="Bad",
            account_type="liability",
            normal_balance="debit",
        )
