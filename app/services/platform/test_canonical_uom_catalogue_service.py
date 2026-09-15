from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app import create_app
from app.extensions import db
from app.models import (
    CanonicalUnitOfMeasure,
    UnitOfMeasure,
)
from app.services.platform.canonical_uom_catalogue_service import (
    CanonicalUOMCatalogueService,
)
from app.services.platform.canonical_uom_policy import (
    ALL_CANONICAL_UOM_CODES,
    CANONICAL_UOM_DEFINITIONS,
    get_canonical_uom,
)


@pytest.fixture()
def canonical_uom_session():
    app = create_app()

    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()

        session = Session(
            bind=connection,
            expire_on_commit=False,
        )

        try:
            session.execute(
                update(UnitOfMeasure)
                .where(
                    UnitOfMeasure.canonical_uom_id.isnot(None)
                )
                .values(
                    canonical_uom_id=None
                )
            )

            session.execute(
                delete(CanonicalUnitOfMeasure)
            )
            session.flush()

            yield session
        finally:
            session.close()
            transaction.rollback()
            connection.close()


def test_policy_contains_expected_canonical_units():
    assert len(CANONICAL_UOM_DEFINITIONS) == 22
    assert len(ALL_CANONICAL_UOM_CODES) == 22

    assert {
        "EA",
        "PC",
        "TAB",
        "CAP",
        "SACH",
        "SUPP",
        "PESS",
        "PAIR",
        "SET",
        "BOT",
        "TUBE",
        "VIAL",
        "AMP",
        "BAG",
        "INH",
        "ROLL",
        "STRIP",
        "BLISTER",
        "PACK",
        "BOX",
        "OUTER",
        "CARTON",
    } == ALL_CANONICAL_UOM_CODES


def test_first_synchronize_creates_catalogue(
    canonical_uom_session,
):
    service = CanonicalUOMCatalogueService(
        canonical_uom_session
    )

    result = service.synchronize()

    persisted_codes = set(
        canonical_uom_session.scalars(
            select(
                CanonicalUnitOfMeasure.code
            )
        ).all()
    )

    assert persisted_codes == ALL_CANONICAL_UOM_CODES

    assert result.processed_count == 22
    assert result.created_count == 22
    assert result.updated_count == 0
    assert result.unchanged_count == 0
    assert result.changed is True


def test_second_synchronize_is_idempotent(
    canonical_uom_session,
):
    service = CanonicalUOMCatalogueService(
        canonical_uom_session
    )

    service.synchronize()
    second = service.synchronize()

    assert second.processed_count == 22
    assert second.created_count == 0
    assert second.updated_count == 0
    assert second.unchanged_count == 22
    assert second.changed is False


def test_synchronize_repairs_governed_metadata(
    canonical_uom_session,
):
    service = CanonicalUOMCatalogueService(
        canonical_uom_session
    )

    service.synchronize()

    tablet = canonical_uom_session.scalar(
        select(CanonicalUnitOfMeasure)
        .where(
            CanonicalUnitOfMeasure.code
            == "TAB"
        )
    )

    assert tablet is not None

    tablet.name = "Wrong Tablet"
    tablet.unit_family = "wrong"
    tablet.description = "Wrong"
    tablet.is_packaging_unit = True
    tablet.is_active = False
    tablet.sort_order = 9999

    canonical_uom_session.flush()

    result = service.synchronize()

    definition = get_canonical_uom("TAB")

    assert definition is not None

    assert tablet.name == definition.name
    assert tablet.unit_family == (
        definition.unit_family
    )
    assert tablet.description == (
        definition.description
    )
    assert tablet.is_packaging_unit is False
    assert tablet.is_active is True
    assert tablet.sort_order == (
        definition.sort_order
    )

    item = next(
        item
        for item in result.units
        if item.code == "TAB"
    )

    assert item.created is False
    assert item.metadata_updated is True
    assert result.updated_count == 1


def test_unknown_canonical_row_is_preserved(
    canonical_uom_session,
):
    unknown_code = (
        "TEST-"
        + uuid4().hex[:8].upper()
    )

    unknown = CanonicalUnitOfMeasure(
        code=unknown_code,
        name="Unmanaged Test Unit",
        unit_family="test",
        description=(
            "Unmanaged row used to verify "
            "non-destructive synchronization."
        ),
        is_packaging_unit=False,
        is_active=True,
        sort_order=9999,
    )

    canonical_uom_session.add(unknown)
    canonical_uom_session.flush()

    service = CanonicalUOMCatalogueService(
        canonical_uom_session
    )

    service.synchronize()

    preserved = canonical_uom_session.scalar(
        select(CanonicalUnitOfMeasure)
        .where(
            CanonicalUnitOfMeasure.code
            == unknown_code
        )
    )

    assert preserved is not None
    assert preserved.id == unknown.id
    assert preserved.name == "Unmanaged Test Unit"


def test_canonical_units_requires_complete_catalogue(
    canonical_uom_session,
):
    service = CanonicalUOMCatalogueService(
        canonical_uom_session
    )

    with pytest.raises(
        RuntimeError,
        match="incomplete",
    ):
        service.canonical_units()


def test_canonical_units_returns_complete_catalogue(
    canonical_uom_session,
):
    service = CanonicalUOMCatalogueService(
        canonical_uom_session
    )

    service.synchronize()

    units = service.canonical_units()

    assert len(units) == 22
    assert {
        unit.code
        for unit in units
    } == ALL_CANONICAL_UOM_CODES


def test_packaging_flags_match_family(
    canonical_uom_session,
):
    service = CanonicalUOMCatalogueService(
        canonical_uom_session
    )

    service.synchronize()

    units = service.canonical_units()

    packaging_codes = {
        unit.code
        for unit in units
        if unit.is_packaging_unit
    }

    assert packaging_codes == {
        "STRIP",
        "BLISTER",
        "PACK",
        "BOX",
        "OUTER",
        "CARTON",
    }
