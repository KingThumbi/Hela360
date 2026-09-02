"""
Route contract tests for Hela360 Office Master Catalogue reads.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from flask import Flask

from app.api import office_catalogue


@pytest.fixture
def app():
    app = Flask(__name__)

    app.register_blueprint(
        office_catalogue.bp,
        url_prefix="/api",
    )

    return app


@pytest.fixture
def client(app):
    return app.test_client()


def identity():
    return SimpleNamespace(
        user_id="user-1",
        tenant_id="tenant-1",
        branch_id=None,
    )


def pagination():
    return {
        "page": 1,
        "per_page": 25,
        "total": 1,
        "pages": 1,
        "has_prev": False,
        "has_next": False,
    }


def master_item():
    return {
        "id": "master-1",
        "master_code": "HMI-000001",
        "canonical_name": "Paracetamol 500mg Tablets",
        "brand_name": None,
        "generic_name": "Paracetamol",
        "strength": "500mg",
        "dosage_form": "Tablet",
        "pack_quantity": "100",
        "pack_unit": "tablet",
        "pack_type": "box",
        "item_class": "medicine",
        "category_name": "Analgesics",
        "subcategory_name": None,
        "manufacturer": None,
        "country_of_origin": "Kenya",
        "cold_chain": False,
        "restricted_item": False,
        "requires_prescription": False,
        "tax_classification": None,
        "review_status": "draft",
        "is_active": False,
    }


def test_office_master_items_route_is_registered(
    app,
) -> None:
    rules = {
        (
            rule.rule,
            tuple(sorted(rule.methods)),
        )
        for rule in app.url_map.iter_rules()
    }

    assert any(
        rule
        == "/api/office/catalogue/master-items"
        and "GET" in methods
        for rule, methods in rules
    )


def test_non_platform_user_is_denied(
    client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        office_catalogue,
        "get_current_identity",
        identity,
    )

    monkeypatch.setattr(
        office_catalogue,
        "_has_office_access",
        lambda _identity: False,
    )

    response = client.get(
        "/api/office/catalogue/master-items"
    )

    assert response.status_code == 403
    assert response.get_json()["ok"] is False


def test_platform_admin_receives_master_items(
    client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        office_catalogue,
        "get_current_identity",
        identity,
    )

    monkeypatch.setattr(
        office_catalogue,
        "_has_office_access",
        lambda _identity: True,
    )

    monkeypatch.setattr(
        office_catalogue.PlatformMasterItemQueryService,
        "list_items",
        lambda _self, *, filters: (
            [master_item()],
            pagination(),
        ),
    )

    response = client.get(
        "/api/office/catalogue/master-items"
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["ok"] is True
    assert payload["count"] == 1
    assert payload["pagination"]["total"] == 1
    assert payload["items"][0]["master_code"] == (
        "HMI-000001"
    )
    assert "adoption" not in payload["items"][0]


def test_invalid_office_filter_returns_400(
    client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        office_catalogue,
        "get_current_identity",
        identity,
    )

    monkeypatch.setattr(
        office_catalogue,
        "_has_office_access",
        lambda _identity: True,
    )

    response = client.get(
        "/api/office/catalogue/master-items"
        "?is_active=not-a-boolean"
    )

    assert response.status_code == 400

    payload = response.get_json()

    assert payload["ok"] is False
    assert (
        payload["error"]
        == "is_active must be true or false."
    )


def test_office_master_item_detail_route_is_registered(
    app,
) -> None:
    rules = {
        rule.rule
        for rule in app.url_map.iter_rules()
    }

    assert (
        "/api/office/catalogue/master-items/"
        "<master_item_id>"
        in rules
    )


def test_platform_admin_receives_master_item_detail(
    client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        office_catalogue,
        "get_current_identity",
        identity,
    )

    monkeypatch.setattr(
        office_catalogue,
        "_has_office_access",
        lambda _identity: True,
    )

    monkeypatch.setattr(
        office_catalogue.PlatformMasterItemQueryService,
        "get_item",
        lambda _self, *, master_item_id: (
            master_item()
            if master_item_id == "master-1"
            else None
        ),
    )

    response = client.get(
        "/api/office/catalogue/master-items/master-1"
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["ok"] is True
    assert payload["item"]["id"] == "master-1"
    assert "adoption" not in payload["item"]


def test_office_master_item_detail_returns_404(
    client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        office_catalogue,
        "get_current_identity",
        identity,
    )

    monkeypatch.setattr(
        office_catalogue,
        "_has_office_access",
        lambda _identity: True,
    )

    monkeypatch.setattr(
        office_catalogue.PlatformMasterItemQueryService,
        "get_item",
        lambda _self, *, master_item_id: None,
    )

    response = client.get(
        "/api/office/catalogue/master-items/missing"
    )

    assert response.status_code == 404

    payload = response.get_json()

    assert payload == {
        "ok": False,
        "error": "Master item not found.",
    }


def test_non_platform_user_cannot_read_master_item_detail(
    client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        office_catalogue,
        "get_current_identity",
        identity,
    )

    monkeypatch.setattr(
        office_catalogue,
        "_has_office_access",
        lambda _identity: False,
    )

    response = client.get(
        "/api/office/catalogue/master-items/master-1"
    )

    assert response.status_code == 403
