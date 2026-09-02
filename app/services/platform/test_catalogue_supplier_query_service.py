"""
Tests for Hela360 Office Catalogue Supplier query service.
"""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app import create_app
from app.errors import ValidationError
from app.extensions import db
from app.models import (
    CatalogueSupplier,
    MasterItem,
    MasterItemSupplierMapping,
    SupplierItemPrice,
)
from app.services.platform.catalogue_supplier_query_service import (
    CatalogueSupplierListFilters,
    PlatformCatalogueSupplierQueryService,
)


@pytest.fixture()
def catalogue_session():
    app = create_app()

    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()

        session = Session(
            bind=connection,
            expire_on_commit=False,
        )

        try:
            yield session
        finally:
            session.close()
            transaction.rollback()
            connection.close()


def _seed_supplier_data(session):
    master_item = MasterItem(
        master_code="TEST-HMI-SUPPLIER",
        canonical_name="Supplier Test Medicine",
        review_status="draft",
        is_active=True,
    )

    comparable_supplier = CatalogueSupplier(
        name="Comparable Supplier",
        normalized_name="comparable supplier",
        country="Kenya",
        is_active=True,
    )

    evidence_supplier = CatalogueSupplier(
        name="Evidence Supplier",
        normalized_name="evidence supplier",
        country=None,
        is_active=True,
    )

    inactive_supplier = CatalogueSupplier(
        name="Inactive Supplier",
        normalized_name="inactive supplier",
        country="Kenya",
        is_active=False,
    )

    session.add_all(
        [
            master_item,
            comparable_supplier,
            evidence_supplier,
            inactive_supplier,
        ]
    )

    session.flush()

    comparable_mapping = MasterItemSupplierMapping(
        master_item_id=master_item.id,
        catalogue_supplier_id=(
            comparable_supplier.id
        ),
        supplier_item_code="COMP-001",
        supplier_item_name=(
            "SUPPLIER TEST MEDICINE"
        ),
        is_active=True,
    )

    evidence_mapping = MasterItemSupplierMapping(
        master_item_id=master_item.id,
        catalogue_supplier_id=(
            evidence_supplier.id
        ),
        supplier_item_code="EVID-001",
        supplier_item_name=(
            "SUPPLIER TEST MEDICINE"
        ),
        source_description=(
            "Source selling price"
        ),
        is_active=True,
    )

    session.add_all(
        [
            comparable_mapping,
            evidence_mapping,
        ]
    )

    session.flush()

    session.add_all(
        [
            SupplierItemPrice(
                supplier_mapping_id=(
                    comparable_mapping.id
                ),
                source_offer_key=(
                    "TEST-COMP-1"
                ),
                price_type="Wholesale Price",
                amount=Decimal("100.00"),
                currency="KES",
                effective_date=date(
                    2026,
                    8,
                    1,
                ),
                is_comparable_procurement=True,
            ),
            SupplierItemPrice(
                supplier_mapping_id=(
                    comparable_mapping.id
                ),
                source_offer_key=(
                    "TEST-COMP-2"
                ),
                price_type="Wholesale Price",
                amount=Decimal("95.00"),
                currency="KES",
                effective_date=date(
                    2026,
                    9,
                    1,
                ),
                is_comparable_procurement=True,
            ),
            SupplierItemPrice(
                supplier_mapping_id=(
                    evidence_mapping.id
                ),
                source_offer_key=(
                    "TEST-EVIDENCE-1"
                ),
                price_type="Listed Price",
                amount=Decimal("130.00"),
                currency="KES",
                effective_date=None,
                is_comparable_procurement=False,
            ),
        ]
    )

    session.flush()


def test_default_filters():
    filters = (
        CatalogueSupplierListFilters
        .from_query({})
    )

    assert filters.page == 1
    assert filters.per_page == 25
    assert filters.search is None
    assert filters.is_active is None


def test_invalid_is_active_filter_is_rejected():
    with pytest.raises(
        ValidationError,
        match="is_active must be true or false",
    ):
        CatalogueSupplierListFilters.from_query(
            {
                "is_active": "maybe",
            }
        )


def test_per_page_cannot_exceed_100():
    with pytest.raises(
        ValidationError,
        match="per_page must not exceed 100",
    ):
        CatalogueSupplierListFilters.from_query(
            {
                "per_page": "101",
            }
        )


def test_supplier_metrics_projection(
    catalogue_session,
):
    _seed_supplier_data(
        catalogue_session
    )

    items, pagination = (
        PlatformCatalogueSupplierQueryService(
            catalogue_session
        ).list_suppliers(
            filters=CatalogueSupplierListFilters()
        )
    )

    by_name = {
        item["name"]: item
        for item in items
        if item["name"] in {
            "Comparable Supplier",
            "Evidence Supplier",
            "Inactive Supplier",
        }
    }

    comparable = (
        by_name["Comparable Supplier"]
    )

    assert comparable["mapping_count"] == 1
    assert (
        comparable["price_observation_count"]
        == 2
    )
    assert (
        comparable[
            "comparable_observation_count"
        ]
        == 2
    )
    assert (
        comparable[
            "non_comparable_observation_count"
        ]
        == 0
    )
    assert (
        comparable["latest_effective_date"]
        == "2026-09-01"
    )
    assert (
        comparable["procurement_comparable"]
        is True
    )

    evidence = (
        by_name["Evidence Supplier"]
    )

    assert evidence["mapping_count"] == 1
    assert (
        evidence["price_observation_count"]
        == 1
    )
    assert (
        evidence[
            "comparable_observation_count"
        ]
        == 0
    )
    assert (
        evidence[
            "non_comparable_observation_count"
        ]
        == 1
    )
    assert (
        evidence["latest_effective_date"]
        is None
    )
    assert (
        evidence["procurement_comparable"]
        is False
    )

    inactive = (
        by_name["Inactive Supplier"]
    )

    assert inactive["mapping_count"] == 0
    assert (
        inactive["price_observation_count"]
        == 0
    )

    assert pagination["total"] >= 3


def test_active_filter(
    catalogue_session,
):
    _seed_supplier_data(
        catalogue_session
    )

    items, _pagination = (
        PlatformCatalogueSupplierQueryService(
            catalogue_session
        ).list_suppliers(
            filters=(
                CatalogueSupplierListFilters(
                    is_active=False,
                )
            )
        )
    )

    names = {
        item["name"]
        for item in items
    }

    assert "Inactive Supplier" in names
    assert "Comparable Supplier" not in names


def test_search_filter(
    catalogue_session,
):
    _seed_supplier_data(
        catalogue_session
    )

    items, _pagination = (
        PlatformCatalogueSupplierQueryService(
            catalogue_session
        ).list_suppliers(
            filters=(
                CatalogueSupplierListFilters(
                    search="Comparable Supplier",
                )
            )
        )
    )

    assert any(
        item["name"]
        == "Comparable Supplier"
        for item in items
    )
