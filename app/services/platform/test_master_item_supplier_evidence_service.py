"""
Tests for Hela360 Office Master Item supplier evidence projection.
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
from app.services.platform.master_item_supplier_evidence_service import (
    PlatformMasterItemSupplierEvidenceService,
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


def _seed_evidence(
    session,
):
    master_item = MasterItem(
        master_code="TEST-HMI-EVIDENCE",
        canonical_name="Evidence Medicine",
        review_status="draft",
        is_active=True,
    )

    supplier = CatalogueSupplier(
        name="Evidence Supplier",
        normalized_name=(
            "evidence supplier"
        ),
        country="Kenya",
        is_active=True,
    )

    session.add_all(
        [
            master_item,
            supplier,
        ]
    )

    session.flush()

    mapping = MasterItemSupplierMapping(
        master_item_id=master_item.id,
        catalogue_supplier_id=supplier.id,
        supplier_item_code="SUP-001",
        supplier_item_name=(
            "EVIDENCE MEDICINE"
        ),
        source_description=(
            "Supplier catalogue listing"
        ),
        is_active=True,
    )

    session.add(mapping)
    session.flush()

    older_comparable = SupplierItemPrice(
        supplier_mapping_id=mapping.id,
        source_offer_key=(
            "TEST-EVIDENCE-OFFER-1"
        ),
        price_type="Listed Price",
        amount=Decimal("100.00"),
        currency="KES",
        effective_date=date(
            2026,
            8,
            1,
        ),
        source_document=(
            "august-price-list.pdf"
        ),
        source_location="p.1",
        is_comparable_procurement=True,
    )

    latest_comparable = SupplierItemPrice(
        supplier_mapping_id=mapping.id,
        source_offer_key=(
            "TEST-EVIDENCE-OFFER-2"
        ),
        price_type="Wholesale Price",
        amount=Decimal("95.00"),
        currency="KES",
        effective_date=date(
            2026,
            9,
            1,
        ),
        source_document=(
            "september-price-list.pdf"
        ),
        source_location="p.2",
        is_comparable_procurement=True,
    )

    non_comparable = SupplierItemPrice(
        supplier_mapping_id=mapping.id,
        source_offer_key=(
            "TEST-EVIDENCE-OFFER-3"
        ),
        price_type="Listed Price",
        amount=Decimal("140.00"),
        currency="KES",
        effective_date=None,
        source_document=(
            "selling-price.pdf"
        ),
        source_location="p.3",
        is_comparable_procurement=False,
    )

    session.add_all(
        [
            older_comparable,
            latest_comparable,
            non_comparable,
        ]
    )

    session.flush()

    return master_item


def test_supplier_evidence_projection(
    catalogue_session,
):
    master_item = _seed_evidence(
        catalogue_session
    )

    result = (
        PlatformMasterItemSupplierEvidenceService(
            catalogue_session
        ).get_evidence(
            master_item_id=master_item.id
        )
    )

    assert result is not None

    assert result["master_item_id"] == (
        master_item.id
    )
    assert result["mapping_count"] == 1
    assert (
        result["price_observation_count"]
        == 3
    )
    assert (
        result["comparable_observation_count"]
        == 2
    )

    mapping = result["mappings"][0]

    assert (
        mapping["supplier"]["name"]
        == "Evidence Supplier"
    )

    assert (
        mapping["supplier_item_code"]
        == "SUP-001"
    )

    assert len(mapping["prices"]) == 3

    assert (
        mapping[
            "latest_comparable_price"
        ]["amount"]
        == "95.00"
    )

    assert (
        mapping[
            "latest_comparable_price"
        ]["effective_date"]
        == "2026-09-01"
    )


def test_non_comparable_price_does_not_win_latest(
    catalogue_session,
):
    master_item = _seed_evidence(
        catalogue_session
    )

    result = (
        PlatformMasterItemSupplierEvidenceService(
            catalogue_session
        ).get_evidence(
            master_item_id=master_item.id
        )
    )

    latest = (
        result["mappings"][0][
            "latest_comparable_price"
        ]
    )

    assert latest["amount"] == "95.00"
    assert (
        latest[
            "is_comparable_procurement"
        ]
        is True
    )


def test_missing_master_item_returns_none(
    catalogue_session,
):
    result = (
        PlatformMasterItemSupplierEvidenceService(
            catalogue_session
        ).get_evidence(
            master_item_id=(
                "missing-master-item"
            )
        )
    )

    assert result is None


def test_supplier_evidence_requires_master_item_id(
    catalogue_session,
):
    service = (
        PlatformMasterItemSupplierEvidenceService(
            catalogue_session
        )
    )

    with pytest.raises(
        ValidationError,
        match="Master item id is required",
    ):
        service.get_evidence(
            master_item_id=""
        )
