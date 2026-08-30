from __future__ import annotations

from copy import deepcopy
from uuid import uuid4

import pytest

from sqlalchemy.orm import Session

from app import create_app
from app.extensions import db
from app.models import (
    CatalogueSupplier,
    MasterItem,
    MasterItemSupplierMapping,
    SupplierItemPrice,
)
from app.services.platform.master_catalogue_seed_service import (
    MasterCatalogueSeedError,
    MasterCatalogueSeedService,
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


def _suffix() -> str:
    return uuid4().hex[:10]


def _payload(
    *,
    suffix: str,
) -> dict:
    return {
        "schema_version": 1,
        "source_workbook":
            "test-source.xlsx",

        "master_items": [
            {
                "master_code":
                    f"TEST-HMI-{suffix}",

                "canonical_name":
                    "Test Medicine 500mg",

                "brand_name":
                    "Test Brand",

                "generic_name":
                    "Test Generic",

                "strength":
                    "500mg",

                "dosage_form":
                    "Tablet",

                "pack_quantity":
                    10,

                "pack_unit":
                    "tablet",

                "pack_type":
                    "blister",

                "item_class":
                    "Medicine",

                "category_name":
                    "Test Category",

                "subcategory_name":
                    None,

                "manufacturer":
                    None,

                "country_of_origin":
                    None,

                "cold_chain":
                    None,

                "restricted_item":
                    None,

                "requires_prescription":
                    None,

                "tax_classification":
                    None,

                "review_status":
                    "approved",

                "is_active":
                    True,

                "reviewer_notes":
                    None,
            }
        ],

        "supplier_offers": [
            {
                "source_mapping_id":
                    f"TEST-MSM-{suffix}-1",

                "master_code":
                    f"TEST-HMI-{suffix}",

                "supplier_name":
                    f"Test Supplier {suffix}",

                "supplier_country":
                    None,

                "supplier_item_code":
                    None,

                "supplier_item_name":
                    "TEST MEDICINE 500MG",

                "source_description":
                    "Test listing",

                "price_type":
                    "Wholesale Price",

                "amount":
                    100,

                "currency":
                    "KES",

                "discount_percent":
                    None,

                "vat_source":
                    None,

                "effective_date":
                    "2026-08-30",

                "source_document":
                    "test-price-list.pdf",

                "source_location":
                    "p.1",

                "is_comparable_procurement":
                    True,
            }
        ],
    }


def test_first_import_creates_entities(
    catalogue_session,
) -> None:
    suffix = _suffix()
    payload = _payload(
        suffix=suffix
    )

    result = (
        MasterCatalogueSeedService(
            catalogue_session
        )
        .import_payload(
            payload
        )
    )

    assert result.master_items.created == 1
    assert result.suppliers.created == 1
    assert result.mappings.created == 1
    assert result.prices.created == 1

    assert (
        catalogue_session.query(
            MasterItem
        )
        .filter_by(
            master_code=(
                f"TEST-HMI-{suffix}"
            )
        )
        .count()
        == 1
    )

    assert (
        catalogue_session.query(
            SupplierItemPrice
        )
        .filter_by(
            source_offer_key=(
                f"TEST-MSM-{suffix}-1"
            )
        )
        .count()
        == 1
    )


def test_second_identical_import_is_idempotent(
    catalogue_session,
) -> None:
    suffix = _suffix()
    payload = _payload(
        suffix=suffix
    )

    service = MasterCatalogueSeedService(
        catalogue_session
    )

    service.import_payload(
        payload
    )

    second = service.import_payload(
        payload
    )

    assert second.master_items.created == 0
    assert second.master_items.updated == 0
    assert second.master_items.unchanged == 1

    assert second.suppliers.created == 0
    assert second.suppliers.updated == 0
    assert second.suppliers.unchanged == 1

    assert second.mappings.created == 0
    assert second.mappings.updated == 0
    assert second.mappings.unchanged == 1

    assert second.prices.created == 0
    assert second.prices.updated == 0
    assert second.prices.unchanged == 1


def test_changed_master_metadata_updates_same_item(
    catalogue_session,
) -> None:
    suffix = _suffix()
    payload = _payload(
        suffix=suffix
    )

    service = MasterCatalogueSeedService(
        catalogue_session
    )

    service.import_payload(
        payload
    )

    changed = deepcopy(
        payload
    )

    changed[
        "master_items"
    ][0][
        "canonical_name"
    ] = "Updated Test Medicine"

    result = service.import_payload(
        changed
    )

    assert result.master_items.created == 0
    assert result.master_items.updated == 1

    items = (
        catalogue_session.query(
            MasterItem
        )
        .filter_by(
            master_code=(
                f"TEST-HMI-{suffix}"
            )
        )
        .all()
    )

    assert len(items) == 1
    assert (
        items[0].canonical_name
        == "Updated Test Medicine"
    )


def test_changed_offer_updates_same_price(
    catalogue_session,
) -> None:
    suffix = _suffix()
    payload = _payload(
        suffix=suffix
    )

    service = MasterCatalogueSeedService(
        catalogue_session
    )

    service.import_payload(
        payload
    )

    changed = deepcopy(
        payload
    )

    changed[
        "supplier_offers"
    ][0]["amount"] = 125

    result = service.import_payload(
        changed
    )

    assert result.prices.created == 0
    assert result.prices.updated == 1

    prices = (
        catalogue_session.query(
            SupplierItemPrice
        )
        .filter_by(
            source_offer_key=(
                f"TEST-MSM-{suffix}-1"
            )
        )
        .all()
    )

    assert len(prices) == 1
    assert float(
        prices[0].amount
    ) == 125.0


def test_unknown_master_reference_is_rejected_before_sync(
    catalogue_session,
) -> None:
    suffix = _suffix()
    payload = _payload(
        suffix=suffix
    )

    payload[
        "supplier_offers"
    ][0][
        "master_code"
    ] = "DOES-NOT-EXIST"

    with pytest.raises(
        MasterCatalogueSeedError,
        match="unknown master_code",
    ):
        MasterCatalogueSeedService(
            catalogue_session
        ).import_payload(
            payload
        )

    assert (
        catalogue_session.query(
            MasterItem
        )
        .filter_by(
            master_code=(
                f"TEST-HMI-{suffix}"
            )
        )
        .count()
        == 0
    )


def test_duplicate_source_offer_key_is_rejected(
    catalogue_session,
) -> None:
    suffix = _suffix()
    payload = _payload(
        suffix=suffix
    )

    duplicate = deepcopy(
        payload[
            "supplier_offers"
        ][0]
    )

    duplicate["amount"] = 200

    payload[
        "supplier_offers"
    ].append(
        duplicate
    )

    with pytest.raises(
        MasterCatalogueSeedError,
        match=(
            "Duplicate source offer key"
        ),
    ):
        MasterCatalogueSeedService(
            catalogue_session
        ).import_payload(
            payload
        )


def test_unknown_evidence_remains_null(
    catalogue_session,
) -> None:
    suffix = _suffix()
    payload = _payload(
        suffix=suffix
    )

    MasterCatalogueSeedService(
        catalogue_session
    ).import_payload(
        payload
    )

    item = (
        catalogue_session.query(
            MasterItem
        )
        .filter_by(
            master_code=(
                f"TEST-HMI-{suffix}"
            )
        )
        .one()
    )

    price = (
        catalogue_session.query(
            SupplierItemPrice
        )
        .filter_by(
            source_offer_key=(
                f"TEST-MSM-{suffix}-1"
            )
        )
        .one()
    )

    assert item.cold_chain is None
    assert item.restricted_item is None
    assert (
        item.requires_prescription
        is None
    )
    assert (
        item.tax_classification
        is None
    )
    assert price.vat_source is None


def test_repeated_no_code_listing_shares_mapping_but_keeps_prices(
    catalogue_session,
) -> None:
    suffix = _suffix()
    payload = _payload(
        suffix=suffix
    )

    second = deepcopy(
        payload[
            "supplier_offers"
        ][0]
    )

    second[
        "source_mapping_id"
    ] = f"TEST-MSM-{suffix}-2"

    second["amount"] = 150
    second[
        "effective_date"
    ] = "2026-08-31"

    payload[
        "supplier_offers"
    ].append(
        second
    )

    result = (
        MasterCatalogueSeedService(
            catalogue_session
        )
        .import_payload(
            payload
        )
    )

    assert result.mappings.created == 1
    assert result.prices.created == 2

    supplier = (
        catalogue_session.query(
            CatalogueSupplier
        )
        .filter(
            CatalogueSupplier.name
            == f"Test Supplier {suffix}"
        )
        .one()
    )

    mappings = (
        catalogue_session.query(
            MasterItemSupplierMapping
        )
        .filter_by(
            catalogue_supplier_id=(
                supplier.id
            )
        )
        .all()
    )

    assert len(mappings) == 1

    prices = (
        catalogue_session.query(
            SupplierItemPrice
        )
        .filter_by(
            supplier_mapping_id=(
                mappings[0].id
            )
        )
        .all()
    )

    assert len(prices) == 2

    assert {
        price.source_offer_key
        for price in prices
    } == {
        f"TEST-MSM-{suffix}-1",
        f"TEST-MSM-{suffix}-2",
    }
