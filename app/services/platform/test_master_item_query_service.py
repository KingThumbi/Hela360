"""
Tests for the Hela360 Office Master Item query contract.
"""

from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.errors import ValidationError
from app.services.platform.master_item_query_service import (
    PlatformMasterItemListFilters,
    PlatformMasterItemQueryService,
)


def test_default_filters_are_platform_read_defaults():
    filters = PlatformMasterItemListFilters.from_query(
        {}
    )

    assert filters.page == 1
    assert filters.per_page == 25
    assert filters.search is None
    assert filters.review_status is None
    assert filters.is_active is None
    assert filters.item_class is None
    assert filters.category is None
    assert filters.dosage_form is None


def test_platform_filters_accept_governance_state():
    filters = PlatformMasterItemListFilters.from_query(
        {
            "page": "2",
            "per_page": "50",
            "search": "paracetamol",
            "review_status": "draft",
            "is_active": "false",
            "item_class": "medicine",
            "category": "Analgesics",
            "dosage_form": "Tablet",
        }
    )

    assert filters.page == 2
    assert filters.per_page == 50
    assert filters.search == "paracetamol"
    assert filters.review_status == "draft"
    assert filters.is_active is False
    assert filters.item_class == "medicine"
    assert filters.category == "Analgesics"
    assert filters.dosage_form == "Tablet"


def test_invalid_is_active_filter_is_rejected():
    with pytest.raises(
        ValidationError,
        match="is_active must be true or false",
    ):
        PlatformMasterItemListFilters.from_query(
            {
                "is_active": "maybe",
            }
        )


def test_per_page_cannot_exceed_100():
    with pytest.raises(
        ValidationError,
        match="per_page must not exceed 100",
    ):
        PlatformMasterItemListFilters.from_query(
            {
                "per_page": "101",
            }
        )


def test_master_item_serialization_contains_no_tenant_adoption():
    item = SimpleNamespace(
        id="master-1",
        master_code="HMI-000001",
        canonical_name="Paracetamol 500mg Tablets",
        brand_name=None,
        generic_name="Paracetamol",
        strength="500mg",
        dosage_form="Tablet",
        pack_quantity=Decimal("100"),
        pack_unit="tablet",
        pack_type="box",
        item_class="medicine",
        category_name="Analgesics",
        subcategory_name=None,
        manufacturer=None,
        country_of_origin="Kenya",
        cold_chain=False,
        restricted_item=False,
        requires_prescription=False,
        tax_classification=None,
        review_status="draft",
        is_active=False,
    )

    result = (
        PlatformMasterItemQueryService
        ._serialize_item(item)
    )

    assert result["id"] == "master-1"
    assert result["master_code"] == "HMI-000001"
    assert result["pack_quantity"] == "100"
    assert result["review_status"] == "draft"
    assert result["is_active"] is False
    assert "adoption" not in result
    assert "tenant_id" not in result


class _FakeQuery:
    def __init__(
        self,
        item,
    ):
        self.item = item

    def filter(
        self,
        *_args,
    ):
        return self

    def first(self):
        return self.item


class _FakeSession:
    def __init__(
        self,
        item,
    ):
        self.item = item

    def query(
        self,
        _model,
    ):
        return _FakeQuery(
            self.item
        )


def test_get_item_returns_platform_projection():
    item = SimpleNamespace(
        id="master-detail-1",
        master_code="HMI-DETAIL-001",
        canonical_name="Detail Item",
        brand_name="Example Brand",
        generic_name="Example Generic",
        strength="10mg",
        dosage_form="Tablet",
        pack_quantity=Decimal("30"),
        pack_unit="tablet",
        pack_type="box",
        item_class="medicine",
        category_name="Example Category",
        subcategory_name="Example Subcategory",
        manufacturer="Example Manufacturer",
        country_of_origin="Kenya",
        cold_chain=False,
        restricted_item=False,
        requires_prescription=True,
        tax_classification="standard",
        review_status="draft",
        is_active=False,
    )

    service = PlatformMasterItemQueryService(
        _FakeSession(item)
    )

    result = service.get_item(
        master_item_id="master-detail-1"
    )

    assert result is not None
    assert result["id"] == "master-detail-1"
    assert result["review_status"] == "draft"
    assert result["is_active"] is False
    assert result["requires_prescription"] is True
    assert "adoption" not in result
    assert "tenant_id" not in result


def test_get_item_returns_none_when_missing():
    service = PlatformMasterItemQueryService(
        _FakeSession(None)
    )

    result = service.get_item(
        master_item_id="missing-master-item"
    )

    assert result is None


def test_get_item_requires_identifier():
    service = PlatformMasterItemQueryService(
        _FakeSession(None)
    )

    with pytest.raises(
        ValidationError,
        match="Master item id is required",
    ):
        service.get_item(
            master_item_id=""
        )
