from __future__ import annotations

from datetime import date

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
from app.services.platform.catalogue_data_quality_service import (
    PlatformCatalogueDataQualityService,
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


def _master_item(
    *,
    code: str,
    review_status: str = "approved",
    category_name: str | None = None,
    item_class: str | None = None,
    dosage_form: str | None = None,
    pack_quantity=None,
    pack_unit: str | None = None,
    pack_type: str | None = None,
    generic_name: str | None = None,
    manufacturer: str | None = None,
    is_active: bool = True,
) -> MasterItem:
    return MasterItem(
        master_code=code,
        canonical_name=f"Test {code}",
        review_status=review_status,
        category_name=category_name,
        item_class=item_class,
        dosage_form=dosage_form,
        pack_quantity=pack_quantity,
        pack_unit=pack_unit,
        pack_type=pack_type,
        generic_name=generic_name,
        manufacturer=manufacturer,
        is_active=is_active,
    )


def test_data_quality_summary_reports_objective_counts(
    catalogue_session,
):
    service = PlatformCatalogueDataQualityService(
        catalogue_session
    )

    baseline = service.get_summary()

    complete = _master_item(
        code="DQ-COMPLETE",
        category_name="Analgesics",
        item_class="Medicine",
        dosage_form="Tablet",
        pack_quantity=100,
        pack_unit="tablet",
        pack_type="box",
        generic_name="Paracetamol",
        manufacturer="Example Pharma",
    )

    incomplete = _master_item(
        code="DQ-INCOMPLETE",
        review_status="draft",
        is_active=False,
    )

    catalogue_session.add_all([
        complete,
        incomplete,
    ])
    catalogue_session.flush()

    summary = service.get_summary()

    assert (
        summary["catalogue"]["total"]
        == baseline["catalogue"]["total"] + 2
    )

    assert (
        summary["catalogue"]["approved"]
        == baseline["catalogue"]["approved"] + 1
    )

    assert (
        summary["catalogue"]["draft"]
        == baseline["catalogue"]["draft"] + 1
    )

    assert (
        summary["catalogue"]["active"]
        == baseline["catalogue"]["active"] + 1
    )

    assert (
        summary["catalogue"]["inactive"]
        == baseline["catalogue"]["inactive"] + 1
    )

    assert (
        summary["enrichment"]["categorized"]
        == baseline["enrichment"]["categorized"] + 1
    )

    assert (
        summary["enrichment"]["uncategorized"]
        == baseline["enrichment"]["uncategorized"] + 1
    )

    assert (
        summary["enrichment"]["classified"]
        == baseline["enrichment"]["classified"] + 1
    )

    assert (
        summary["enrichment"]["unclassified"]
        == baseline["enrichment"]["unclassified"] + 1
    )

    assert (
        summary["enrichment"]["dosage_form_populated"]
        == (
            baseline["enrichment"]["dosage_form_populated"]
            + 1
        )
    )

    assert (
        summary["enrichment"]["dosage_form_missing"]
        == (
            baseline["enrichment"]["dosage_form_missing"]
            + 1
        )
    )

    assert (
        summary["enrichment"]["complete_pack_definition"]
        == (
            baseline["enrichment"]["complete_pack_definition"]
            + 1
        )
    )

    assert (
        summary["enrichment"]["incomplete_pack_definition"]
        == (
            baseline["enrichment"]["incomplete_pack_definition"]
            + 1
        )
    )

    assert (
        summary["enrichment"]["generic_name_populated"]
        == (
            baseline["enrichment"]["generic_name_populated"]
            + 1
        )
    )

    assert (
        summary["enrichment"]["generic_name_missing"]
        == (
            baseline["enrichment"]["generic_name_missing"]
            + 1
        )
    )

    assert (
        summary["enrichment"]["manufacturer_populated"]
        == (
            baseline["enrichment"]["manufacturer_populated"]
            + 1
        )
    )

    assert (
        summary["enrichment"]["manufacturer_missing"]
        == (
            baseline["enrichment"]["manufacturer_missing"]
            + 1
        )
    )


def test_data_quality_summary_reports_supplier_provenance(
    catalogue_session,
):
    service = PlatformCatalogueDataQualityService(
        catalogue_session
    )

    baseline = service.get_summary()

    mapped = _master_item(
        code="DQ-MAPPED",
    )

    unmapped = _master_item(
        code="DQ-UNMAPPED",
    )

    supplier = CatalogueSupplier(
        name="DQ Supplier",
        normalized_name="dq supplier",
        is_active=True,
    )

    catalogue_session.add_all([
        mapped,
        unmapped,
        supplier,
    ])
    catalogue_session.flush()

    mapping = MasterItemSupplierMapping(
        master_item_id=mapped.id,
        catalogue_supplier_id=supplier.id,
        supplier_item_code="DQ-001",
        supplier_item_name="DQ Mapped Item",
        is_active=True,
    )

    catalogue_session.add(mapping)
    catalogue_session.flush()

    price = SupplierItemPrice(
        supplier_mapping_id=mapping.id,
        source_offer_key="DQ-OFFER-001",
        price_type="Net",
        amount=100,
        currency="KES",
        effective_date=date(
            2026,
            9,
            3,
        ),
        is_comparable_procurement=True,
    )

    catalogue_session.add(price)
    catalogue_session.flush()

    summary = service.get_summary()

    assert (
        summary["provenance"]["with_supplier_mapping"]
        == (
            baseline["provenance"]["with_supplier_mapping"]
            + 1
        )
    )

    assert (
        summary["provenance"]["without_supplier_mapping"]
        == (
            baseline["provenance"]["without_supplier_mapping"]
            + 1
        )
    )

    assert (
        summary["provenance"]["with_price_evidence"]
        == (
            baseline["provenance"]["with_price_evidence"]
            + 1
        )
    )

    assert (
        summary["provenance"]["without_price_evidence"]
        == (
            baseline["provenance"]["without_price_evidence"]
            + 1
        )
    )

    assert (
        summary["provenance"]["with_comparable_evidence"]
        == (
            baseline["provenance"]["with_comparable_evidence"]
            + 1
        )
    )

    assert (
        summary["provenance"][
            "with_dated_comparable_evidence"
        ]
        == (
            baseline["provenance"][
                "with_dated_comparable_evidence"
            ]
            + 1
        )
    )
