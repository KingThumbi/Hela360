"""
Route contract tests for Hela360 Office Master Catalogue reads.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.platform_auth import decorators as platform_decorators
from flask import Flask

from app.api import office_catalogue
from app.api.errors import register_error_handlers
from app.auth.exceptions import PermissionDeniedError


@pytest.fixture
def app():
    app = Flask(__name__)

    app.register_blueprint(
        office_catalogue.bp,
        url_prefix="/api",
    )

    register_error_handlers(app)

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



@pytest.fixture(autouse=True)
def platform_office_read_access(
    monkeypatch: pytest.MonkeyPatch,
):
    """
    Default Office Catalogue contract authorization.

    Platform authentication transport and persisted IAM behavior are covered
    independently by app/platform_auth tests. These route contract tests focus
    on endpoint behavior after a valid Platform request reaches the route.
    """

    class Identity:
        platform_user_id = "platform-user-1"
        session_id = "platform-session-1"
        authorization = None

    identity = Identity()

    monkeypatch.setattr(
        platform_decorators,
        "resolve_platform_identity",
        lambda: identity,
    )

    monkeypatch.setattr(
        platform_decorators
        .PlatformAuthorizationService,
        "require_permission",
        lambda _self, _user_id, _permission: None,
    )

    return identity


@pytest.fixture
def deny_platform_permission(
    monkeypatch: pytest.MonkeyPatch,
):
    """
    Deny one explicit Platform permission while retaining a valid
    authenticated Hela360 Office identity.
    """

    def deny(
        denied_permission: str,
    ):
        def require_permission(
            _self,
            _platform_user_id,
            permission,
        ):
            if permission == denied_permission:
                raise PermissionDeniedError(
                    "Platform permission required: "
                    + permission
                )

            return None

        monkeypatch.setattr(
            platform_decorators
            .PlatformAuthorizationService,
            "require_permission",
            require_permission,
        )

    return deny


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


def test_platform_user_without_catalogue_read_is_denied(
    client,
    deny_platform_permission,
) -> None:
    deny_platform_permission(
        "platform.catalogue.read"
    )

    response = client.get(
        "/api/office/catalogue/master-items"
    )

    assert response.status_code == 403
    assert (
        response.get_json()["error"]["code"]
        == "AUTHORIZATION_DENIED"
    )

def test_platform_admin_receives_master_items(
    client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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


def test_platform_user_without_catalogue_read_cannot_read_master_item_detail(
    client,
    deny_platform_permission,
) -> None:
    deny_platform_permission(
        "platform.catalogue.read"
    )

    response = client.get(
        "/api/office/catalogue/master-items/master-1"
    )

    assert response.status_code == 403
    assert (
        response.get_json()["error"]["code"]
        == "AUTHORIZATION_DENIED"
    )

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


def test_platform_user_without_suppliers_read_cannot_read_supplier_evidence(
    client,
    deny_platform_permission,
) -> None:
    deny_platform_permission(
        "platform.suppliers.read"
    )

    response = client.get(
        "/api/office/catalogue/master-items/"
        "master-1/supplier-evidence"
    )

    assert response.status_code == 403
    assert (
        response.get_json()["error"]["code"]
        == "AUTHORIZATION_DENIED"
    )



def test_platform_user_without_catalogue_read_cannot_read_supplier_evidence(
    client,
    deny_platform_permission,
) -> None:
    deny_platform_permission(
        "platform.catalogue.read"
    )

    response = client.get(
        "/api/office/catalogue/master-items/"
        "master-1/supplier-evidence"
    )

    assert response.status_code == 403
    assert (
        response.get_json()["error"]["code"]
        == "AUTHORIZATION_DENIED"
    )

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


def test_platform_user_without_suppliers_read_cannot_list_catalogue_suppliers(
    client,
    deny_platform_permission,
) -> None:
    deny_platform_permission(
        "platform.suppliers.read"
    )

    response = client.get(
        "/api/office/catalogue/suppliers"
    )

    assert response.status_code == 403
    assert (
        response.get_json()["error"]["code"]
        == "AUTHORIZATION_DENIED"
    )

def test_invalid_catalogue_supplier_filter_returns_400(
    client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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


def test_platform_user_without_suppliers_read_cannot_read_catalogue_supplier_detail(
    client,
    deny_platform_permission,
) -> None:
    deny_platform_permission(
        "platform.suppliers.read"
    )

    response = client.get(
        "/api/office/catalogue/suppliers/supplier-1"
    )

    assert response.status_code == 403
    assert (
        response.get_json()["error"]["code"]
        == "AUTHORIZATION_DENIED"
    )

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


def test_office_catalogue_data_quality_route_is_registered(
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
        == "/api/office/catalogue/data-quality"
        and "GET" in methods
        for rule, methods in rules
    )


def test_platform_admin_receives_catalogue_data_quality(
    client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary = {
        "catalogue": {
            "total": 10,
            "approved": 8,
            "draft": 2,
            "active": 9,
            "inactive": 1,
        },
        "enrichment": {
            "categorized": 4,
            "uncategorized": 6,
            "classified": 3,
            "unclassified": 7,
            "dosage_form_populated": 5,
            "dosage_form_missing": 5,
            "complete_pack_definition": 2,
            "incomplete_pack_definition": 8,
            "generic_name_populated": 4,
            "generic_name_missing": 6,
            "manufacturer_populated": 1,
            "manufacturer_missing": 9,
        },
        "provenance": {
            "with_supplier_mapping": 3,
            "without_supplier_mapping": 7,
            "with_price_evidence": 3,
            "without_price_evidence": 7,
            "with_comparable_evidence": 3,
            "with_dated_comparable_evidence": 2,
        },
    }

    monkeypatch.setattr(
        office_catalogue
        .PlatformCatalogueDataQualityService,
        "get_summary",
        lambda _self: summary,
    )

    response = client.get(
        "/api/office/catalogue/data-quality"
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload == {
        "ok": True,
        "summary": summary,
    }


def test_platform_user_without_catalogue_read_cannot_read_data_quality(
    client,
    deny_platform_permission,
) -> None:
    deny_platform_permission(
        "platform.catalogue.read"
    )

    response = client.get(
        "/api/office/catalogue/data-quality"
    )

    assert response.status_code == 403
    assert (
        response.get_json()["error"]["code"]
        == "AUTHORIZATION_DENIED"
    )

def test_office_catalogue_categories_route_is_registered(
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
        == "/api/office/catalogue/categories"
        and "GET" in methods
        for rule, methods in rules
    )


def test_platform_admin_receives_catalogue_categories(
    client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary = {
        "total_items": 10,
        "categorized_items": 4,
        "uncategorized_items": 6,
        "category_count": 1,
        "categories": [
            {
                "name": "Medicines",
                "item_count": 4,
                "approved_count": 3,
                "draft_count": 1,
                "active_count": 4,
                "inactive_count": 0,
                "subcategories": [
                    {
                        "name": "Oral Solids",
                        "item_count": 4,
                    },
                ],
            },
        ],
    }

    monkeypatch.setattr(
        office_catalogue
        .PlatformCatalogueCategoryQueryService,
        "get_summary",
        lambda _self: summary,
    )

    response = client.get(
        "/api/office/catalogue/categories"
    )

    assert response.status_code == 200

    assert response.get_json() == {
        "ok": True,
        "summary": summary,
    }


def test_platform_user_without_catalogue_read_cannot_read_categories(
    client,
    deny_platform_permission,
) -> None:
    deny_platform_permission(
        "platform.catalogue.read"
    )

    response = client.get(
        "/api/office/catalogue/categories"
    )

    assert response.status_code == 403
    assert (
        response.get_json()["error"]["code"]
        == "AUTHORIZATION_DENIED"
    )

def test_office_catalogue_brands_route_is_registered(
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
        == "/api/office/catalogue/brands"
        and "GET" in methods
        for rule, methods in rules
    )


def test_platform_admin_receives_catalogue_brands(
    client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary = {
        "total_items": 10,
        "branded_items": 4,
        "unbranded_items": 6,
        "brand_count": 1,
        "brands": [
            {
                "name": "Example Brand",
                "item_count": 4,
                "approved_count": 3,
                "draft_count": 1,
                "active_count": 4,
                "inactive_count": 0,
            },
        ],
    }

    monkeypatch.setattr(
        office_catalogue
        .PlatformCatalogueBrandQueryService,
        "get_summary",
        lambda _self: summary,
    )

    response = client.get(
        "/api/office/catalogue/brands"
    )

    assert response.status_code == 200

    assert response.get_json() == {
        "ok": True,
        "summary": summary,
    }


def test_platform_user_without_catalogue_read_cannot_read_brands(
    client,
    deny_platform_permission,
) -> None:
    deny_platform_permission(
        "platform.catalogue.read"
    )

    response = client.get(
        "/api/office/catalogue/brands"
    )

    assert response.status_code == 403
    assert (
        response.get_json()["error"]["code"]
        == "AUTHORIZATION_DENIED"
    )
