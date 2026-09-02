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
        session_id="session-1",
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


def supplier_evidence():
    return {
        "master_item_id": "master-1",
        "master_code": "HMI-000001",
        "canonical_name": (
            "Paracetamol 500mg Tablets"
        ),
        "mapping_count": 1,
        "price_observation_count": 2,
        "comparable_observation_count": 1,
        "mappings": [
            {
                "id": "mapping-1",
                "supplier": {
                    "id": "supplier-1",
                    "name": "Test Supplier",
                    "country": "Kenya",
                    "is_active": True,
                },
                "supplier_item_code": None,
                "supplier_item_name": (
                    "PARACETAMOL 500MG"
                ),
                "source_description": None,
                "is_active": True,
                "latest_comparable_price": {
                    "id": "price-1",
                    "source_offer_key": (
                        "offer-1"
                    ),
                    "price_type": (
                        "Wholesale Price"
                    ),
                    "amount": "95.00",
                    "currency": "KES",
                    "discount_percent": None,
                    "vat_source": "0%",
                    "effective_date": (
                        "2026-09-01"
                    ),
                    "source_document": (
                        "test.pdf"
                    ),
                    "source_location": "p.1",
                    "is_comparable_procurement": (
                        True
                    ),
                },
                "prices": [],
            }
        ],
    }


def test_office_supplier_evidence_route_is_registered(
    app,
) -> None:
    rules = {
        rule.rule
        for rule in app.url_map.iter_rules()
    }

    assert (
        "/api/office/catalogue/master-items/"
        "<master_item_id>/supplier-evidence"
        in rules
    )


def test_platform_admin_receives_supplier_evidence(
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
        office_catalogue
        .PlatformMasterItemSupplierEvidenceService,
        "get_evidence",
        lambda _self, *, master_item_id: (
            supplier_evidence()
            if master_item_id == "master-1"
            else None
        ),
    )

    response = client.get(
        "/api/office/catalogue/master-items/"
        "master-1/supplier-evidence"
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["ok"] is True
    assert (
        payload["evidence"]["mapping_count"]
        == 1
    )
    assert (
        payload["evidence"][
            "price_observation_count"
        ]
        == 2
    )
    assert (
        payload["evidence"]["mappings"][0][
            "latest_comparable_price"
        ]["amount"]
        == "95.00"
    )


def test_supplier_evidence_returns_404_for_missing_master(
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
        office_catalogue
        .PlatformMasterItemSupplierEvidenceService,
        "get_evidence",
        lambda _self, *, master_item_id: None,
    )

    response = client.get(
        "/api/office/catalogue/master-items/"
        "missing/supplier-evidence"
    )

    assert response.status_code == 404

    assert response.get_json() == {
        "ok": False,
        "error": "Master item not found.",
    }


def test_non_platform_user_cannot_read_supplier_evidence(
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
        "/api/office/catalogue/master-items/"
        "master-1/supplier-evidence"
    )

    assert response.status_code == 403


def catalogue_supplier():
    return {
        "id": "supplier-1",
        "name": "Comparable Supplier",
        "country": "Kenya",
        "is_active": True,
        "mapping_count": 10,
        "price_observation_count": 12,
        "comparable_observation_count": 11,
        "non_comparable_observation_count": 1,
        "latest_effective_date": "2026-09-01",
        "procurement_comparable": True,
    }


def test_office_catalogue_suppliers_route_is_registered(
    app,
) -> None:
    rules = {
        rule.rule
        for rule in app.url_map.iter_rules()
    }

    assert (
        "/api/office/catalogue/suppliers"
        in rules
    )


def test_platform_admin_receives_catalogue_suppliers(
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
        office_catalogue
        .PlatformCatalogueSupplierQueryService,
        "list_suppliers",
        lambda _self, *, filters: (
            [catalogue_supplier()],
            {
                "page": 1,
                "per_page": 25,
                "total": 1,
                "pages": 1,
                "has_prev": False,
                "has_next": False,
            },
        ),
    )

    response = client.get(
        "/api/office/catalogue/suppliers"
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["ok"] is True
    assert payload["count"] == 1
    assert (
        payload["suppliers"][0]["name"]
        == "Comparable Supplier"
    )
    assert (
        payload["suppliers"][0][
            "procurement_comparable"
        ]
        is True
    )


def test_non_platform_user_cannot_read_catalogue_suppliers(
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
        "/api/office/catalogue/suppliers"
    )

    assert response.status_code == 403


def test_invalid_catalogue_supplier_filter_returns_400(
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
        "/api/office/catalogue/suppliers"
        "?is_active=not-a-boolean"
    )

    assert response.status_code == 400

    assert response.get_json() == {
        "ok": False,
        "error": "is_active must be true or false.",
    }


def catalogue_supplier_detail():
    return {
        "id": "supplier-1",
        "name": "Comparable Supplier",
        "country": "Kenya",
        "is_active": True,
        "mapping_count": 1,
        "price_observation_count": 2,
        "comparable_observation_count": 2,
        "non_comparable_observation_count": 0,
        "latest_effective_date": "2026-09-01",
        "procurement_comparable": True,
        "mappings": [
            {
                "id": "mapping-1",
                "supplier_item_code": "COMP-001",
                "supplier_item_name": (
                    "SUPPLIER TEST MEDICINE"
                ),
                "source_description": None,
                "is_active": True,
                "master_item": {
                    "id": "master-item-1",
                    "master_code": "TEST-HMI-SUPPLIER",
                    "canonical_name": (
                        "Supplier Test Medicine"
                    ),
                    "review_status": "draft",
                    "is_active": True,
                },
                "price_observation_count": 2,
                "comparable_observation_count": 2,
                "non_comparable_observation_count": 0,
                "latest_comparable_price": {
                    "id": "price-2",
                    "source_offer_key": "TEST-COMP-2",
                    "price_type": "Wholesale Price",
                    "amount": "95.00",
                    "currency": "KES",
                    "discount_percent": None,
                    "vat_source": None,
                    "effective_date": "2026-09-01",
                    "source_document": None,
                    "source_location": None,
                    "is_comparable_procurement": True,
                },
            },
        ],
    }


def test_office_catalogue_supplier_detail_route_is_registered(
    app,
) -> None:
    rules = {
        rule.rule
        for rule in app.url_map.iter_rules()
    }

    assert (
        "/api/office/catalogue/suppliers/<supplier_id>"
        in rules
    )


def test_platform_admin_receives_catalogue_supplier_detail(
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
        office_catalogue
        .PlatformCatalogueSupplierQueryService,
        "get_supplier",
        lambda _self, *, supplier_id: (
            catalogue_supplier_detail()
        ),
    )

    response = client.get(
        "/api/office/catalogue/suppliers/supplier-1"
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["ok"] is True

    assert (
        payload["supplier"]["name"]
        == "Comparable Supplier"
    )

    assert (
        payload["supplier"]["mappings"][0][
            "latest_comparable_price"
        ]["amount"]
        == "95.00"
    )


def test_catalogue_supplier_detail_returns_404_when_missing(
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
        office_catalogue
        .PlatformCatalogueSupplierQueryService,
        "get_supplier",
        lambda _self, *, supplier_id: None,
    )

    response = client.get(
        "/api/office/catalogue/suppliers/missing"
    )

    assert response.status_code == 404

    assert response.get_json() == {
        "ok": False,
        "error": "Catalogue supplier not found.",
    }


def test_non_platform_user_cannot_read_catalogue_supplier_detail(
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
        "/api/office/catalogue/suppliers/supplier-1"
    )

    assert response.status_code == 403


def test_office_master_item_approval_route_is_registered(
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
        == "/api/office/catalogue/master-items/<master_item_id>/approve"
        and "POST" in methods
        for rule, methods in rules
    )


def test_platform_admin_can_approve_master_item(
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

    approved = SimpleNamespace(
        id="master-1",
        master_code="HMI-000001",
        canonical_name="Paracetamol 500mg Tablets",
        review_status="approved",
        is_active=True,
    )

    monkeypatch.setattr(
        office_catalogue
        .PlatformMasterItemGovernanceService,
        "approve_item",
        lambda _self, **_kwargs: SimpleNamespace(
            master_item=approved,
        ),
    )

    monkeypatch.setattr(
        office_catalogue.db.session,
        "commit",
        lambda: None,
    )

    response = client.post(
        "/api/office/catalogue/master-items/master-1/approve"
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["ok"] is True
    assert payload["item"]["review_status"] == "approved"


def test_non_platform_user_cannot_approve_master_item(
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

    response = client.post(
        "/api/office/catalogue/master-items/master-1/approve"
    )

    assert response.status_code == 403


def test_master_item_approval_returns_404_when_missing(
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

    def raise_missing(
        _self,
        **_kwargs,
    ):
        raise (
            office_catalogue
            .MasterItemGovernanceNotFoundError(
                "Master Item not found."
            )
        )

    monkeypatch.setattr(
        office_catalogue
        .PlatformMasterItemGovernanceService,
        "approve_item",
        raise_missing,
    )

    monkeypatch.setattr(
        office_catalogue.db.session,
        "rollback",
        lambda: None,
    )

    response = client.post(
        "/api/office/catalogue/master-items/missing/approve"
    )

    assert response.status_code == 404

    assert response.get_json() == {
        "ok": False,
        "error": "Master Item not found.",
    }


def test_master_item_approval_returns_409_for_invalid_transition(
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

    def raise_conflict(
        _self,
        **_kwargs,
    ):
        raise (
            office_catalogue
            .MasterItemApprovalConflictError(
                "Only draft Master Items can be approved."
            )
        )

    monkeypatch.setattr(
        office_catalogue
        .PlatformMasterItemGovernanceService,
        "approve_item",
        raise_conflict,
    )

    monkeypatch.setattr(
        office_catalogue.db.session,
        "rollback",
        lambda: None,
    )

    response = client.post(
        "/api/office/catalogue/master-items/master-1/approve"
    )

    assert response.status_code == 409

    assert response.get_json() == {
        "ok": False,
        "error": "Only draft Master Items can be approved.",
    }
