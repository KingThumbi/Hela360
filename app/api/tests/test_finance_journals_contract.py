from __future__ import annotations

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from flask import Flask
from werkzeug.exceptions import Forbidden

from app.api.finance_journals import bp as finance_journals_bp
from app.extensions import db
from app.models import (
    Branch,
    ChartOfAccount,
    JournalEntry,
    JournalEntryLine,
    NumberSequence,
    Tenant,
)
from app.services.tenant.finance import ChartOfAccountsError, ChartOfAccountsService


@pytest.fixture()
def app_context(monkeypatch: pytest.MonkeyPatch):
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TESTING=True,
    )
    db.init_app(app)
    app.register_blueprint(finance_journals_bp, url_prefix="/api")

    with app.app_context():
        tables = [
            Tenant.__table__,
            Branch.__table__,
            ChartOfAccount.__table__,
            NumberSequence.__table__,
            JournalEntry.__table__,
            JournalEntryLine.__table__,
        ]
        for table in tables:
            table.create(db.engine)

        db.session.add(
            Tenant(
                id="tenant-1",
                legal_name="Tenant 1",
                display_name="Tenant 1",
                base_currency="KES",
            )
        )
        db.session.add_all(
            [
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
                    name="Alternative",
                    is_active=True,
                ),
                Tenant(
                    id="tenant-2",
                    legal_name="Tenant 2",
                    display_name="Tenant 2",
                    base_currency="KES",
                ),
            ]
        )
        db.session.flush()
        db.session.add_all(
            [
                ChartOfAccount(
                    id="cash-1", tenant_id="tenant-1", branch_id=None,
                    account_code="1010", account_name="Cash on Hand",
                    account_type="asset", normal_balance="debit",
                    is_active=True, is_system_account=True, currency="KES",
                ),
                ChartOfAccount(
                    id="sales-1", tenant_id="tenant-1", branch_id=None,
                    account_code="4000", account_name="Sales Revenue",
                    account_type="revenue", normal_balance="credit",
                    is_active=True, is_system_account=True, currency="KES",
                ),
                ChartOfAccount(
                    id="expense-1", tenant_id="tenant-1", branch_id="branch-1",
                    account_code="6300", account_name="Rent",
                    account_type="expense", normal_balance="debit",
                    is_active=True, is_system_account=False, currency="KES",
                ),
                ChartOfAccount(
                    id="cash-2", tenant_id="tenant-2", branch_id=None,
                    account_code="1010", account_name="Other Tenant Cash",
                    account_type="asset", normal_balance="debit",
                    is_active=True, is_system_account=True, currency="KES",
                ),
            ]
        )
        db.session.commit()

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
            "app.api.finance_journals._current_identity",
            lambda: identity,
        )
        monkeypatch.setattr(
            "app.services.tenant.auth.decorators.authorization_service.authorize",
            lambda *args, **kwargs: None,
        )
        monkeypatch.setattr(
            "app.services.tenant.finance.journal_service.audit_service.log",
            lambda **kwargs: None,
        )

        yield app, identity

        db.session.remove()
        for table in reversed(tables):
            table.drop(db.engine)


@pytest.fixture()
def client(app_context):
    app, identity = app_context
    return app.test_client(), identity


def payload(*, amount="100.00", credit="100.00", branch_id="branch-1"):
    return {
        "branch_id": branch_id,
        "journal_date": date(2026, 10, 11).isoformat(),
        "description": "Manual journal test",
        "reference": "TEST-REF-1",
        "lines": [
            {"account_id": "cash-1", "debit": amount, "credit": "0.00"},
            {"account_id": "sales-1", "debit": "0.00", "credit": credit},
        ],
    }


def create_draft(client):
    response = client.post("/api/finance/journals", json=payload())
    assert response.status_code == 201, response.get_json()
    return response.get_json()["item"]


def test_create_list_and_branch_scope(client):
    http, identity = client
    entry = create_draft(http)
    assert entry["journal_number"] == "JV-00000001"
    assert entry["status"] == "draft"
    assert entry["total_debit"] == "100.00"
    assert entry["total_credit"] == "100.00"
    assert len(entry["lines"]) == 2

    response = http.get("/api/finance/journals")
    assert response.status_code == 200
    assert response.get_json()["count"] == 1

    identity.branch_id = "branch-2"
    response = http.get(f"/api/finance/journals/{entry['id']}")
    assert response.status_code == 404


def test_unbalanced_draft_cannot_post_but_can_be_corrected(client):
    http, _identity = client
    draft_response = http.post("/api/finance/journals", json=payload(credit="90.00"))
    assert draft_response.status_code == 201, draft_response.get_json()
    entry = draft_response.get_json()["item"]
    assert entry["total_debit"] == "100.00"
    assert entry["total_credit"] == "90.00"

    post_response = http.post(f"/api/finance/journals/{entry['id']}/post")
    assert post_response.status_code == 400
    assert "balance" in post_response.get_json()["error"].lower()

    corrected = payload(credit="100.00")
    patch_response = http.patch(
        f"/api/finance/journals/{entry['id']}",
        json={"lines": corrected["lines"]},
    )
    assert patch_response.status_code == 200, patch_response.get_json()

    posted = http.post(f"/api/finance/journals/{entry['id']}/post")
    assert posted.status_code == 200, posted.get_json()
    assert posted.get_json()["item"]["status"] == "posted"
    assert posted.get_json()["item"]["total_debit"] == posted.get_json()["item"]["total_credit"]


def test_posted_journal_is_immutable(client):
    http, _identity = client
    entry = create_draft(http)
    posted = http.post(f"/api/finance/journals/{entry['id']}/post")
    assert posted.status_code == 200

    response = http.patch(
        f"/api/finance/journals/{entry['id']}",
        json={"description": "Changed after posting"},
    )
    assert response.status_code == 409
    assert "immutable" in response.get_json()["error"].lower()


def test_reversal_creates_separate_posted_journal_and_cannot_repeat(client):
    http, _identity = client
    draft = create_draft(http)
    posted = http.post(f"/api/finance/journals/{draft['id']}/post")
    assert posted.status_code == 200

    response = http.post(
        f"/api/finance/journals/{draft['id']}/reverse",
        json={"journal_date": "2026-10-11", "reason": "Correction of original entry"},
    )
    assert response.status_code == 201, response.get_json()
    reversal = response.get_json()["item"]
    assert reversal["status"] == "posted"
    assert reversal["reversal_of_id"] == draft["id"]
    assert reversal["total_debit"] == "100.00"
    assert reversal["total_credit"] == "100.00"
    assert reversal["lines"][0]["debit"] == "0.00"
    assert reversal["lines"][0]["credit"] == "100.00"
    assert reversal["lines"][1]["debit"] == "100.00"
    assert reversal["lines"][1]["credit"] == "0.00"

    repeated = http.post(
        f"/api/finance/journals/{draft['id']}/reverse",
        json={"journal_date": "2026-10-11", "reason": "Duplicate attempt"},
    )
    assert repeated.status_code == 409


def test_invalid_account_or_line_shape_is_rejected(client):
    http, _identity = client
    bad_tenant = payload()
    bad_tenant["lines"][0]["account_id"] = "cash-2"
    response = http.post("/api/finance/journals", json=bad_tenant)
    assert response.status_code == 400
    assert "not found in this tenant" in response.get_json()["error"]

    bad_sides = payload()
    bad_sides["lines"][0]["credit"] = "1.00"
    response = http.post("/api/finance/journals", json=bad_sides)
    assert response.status_code == 400
    assert "debit or a positive credit" in response.get_json()["error"]


def test_inactive_or_wrong_branch_account_is_rejected(client):
    http, _identity = client
    account = ChartOfAccount(
        id="branch-2-expense", tenant_id="tenant-1", branch_id="branch-2",
        account_code="6400", account_name="Other Branch Expense",
        account_type="expense", normal_balance="debit", is_active=True,
        is_system_account=False, currency="KES",
    )
    db.session.add(account)
    db.session.commit()

    data = payload()
    data["lines"][0]["account_id"] = account.id
    response = http.post("/api/finance/journals", json=data)
    assert response.status_code == 400
    assert "another branch" in response.get_json()["error"]


def test_permission_denial_is_enforced_by_backend(client, monkeypatch):
    http, _identity = client
    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.authorization_service.authorize",
        lambda *args, **kwargs: (_ for _ in ()).throw(Forbidden()),
    )
    response = http.get("/api/finance/journals")
    assert response.status_code == 403


def test_posted_account_classification_cannot_be_rewritten(client):
    http, _identity = client
    data = payload()
    data["lines"][0]["account_id"] = "expense-1"
    response = http.post("/api/finance/journals", json=data)
    assert response.status_code == 201, response.get_json()
    draft = response.get_json()["item"]
    posted = http.post(f"/api/finance/journals/{draft['id']}/post")
    assert posted.status_code == 200

    with pytest.raises(ChartOfAccountsError, match="cannot have its code, type, normal balance"):
        ChartOfAccountsService(db.session).update_account(
            "tenant-1",
            "expense-1",
            fields={"account_type": "asset"},
            actor_user_id="user-1",
        )


def test_journal_total_cannot_overflow_header_numeric_range(client):
    http, _identity = client
    data = payload()
    maximum = "9999999999999999.99"
    data["lines"] = [
        {"account_id": "cash-1", "debit": maximum, "credit": "0.00"},
        {"account_id": "sales-1", "debit": "0.00", "credit": maximum},
        {"account_id": "expense-1", "debit": maximum, "credit": "0.00"},
        {"account_id": "sales-1", "debit": "0.00", "credit": maximum},
    ]

    response = http.post("/api/finance/journals", json=data)

    assert response.status_code == 400
    assert "total debit exceeds" in response.get_json()["error"].lower()
