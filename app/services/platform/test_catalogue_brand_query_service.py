from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app import create_app
from app.extensions import db
from app.models import MasterItem
from app.services.platform.catalogue_brand_query_service import (
    PlatformCatalogueBrandQueryService,
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


def test_brand_summary_reports_derived_brand_metrics(
    catalogue_session,
):
    service = PlatformCatalogueBrandQueryService(
        catalogue_session
    )

    baseline = service.get_summary()

    brand_name = "TEST OFFICE BRAND"

    catalogue_session.add_all(
        [
            MasterItem(
                master_code="TEST-BRAND-001",
                canonical_name=(
                    "Test Brand Approved Item"
                ),
                brand_name=brand_name,
                review_status="approved",
                is_active=True,
            ),
            MasterItem(
                master_code="TEST-BRAND-002",
                canonical_name=(
                    "Test Brand Draft Item"
                ),
                brand_name=brand_name,
                review_status="draft",
                is_active=False,
            ),
            MasterItem(
                master_code="TEST-BRAND-003",
                canonical_name=(
                    "Test Unbranded Item"
                ),
                brand_name=None,
                review_status="approved",
                is_active=True,
            ),
        ]
    )

    catalogue_session.flush()

    summary = service.get_summary()

    assert (
        summary["total_items"]
        == baseline["total_items"] + 3
    )

    assert (
        summary["branded_items"]
        == baseline["branded_items"] + 2
    )

    assert (
        summary["unbranded_items"]
        == baseline["unbranded_items"] + 1
    )

    brand = next(
        item
        for item in summary["brands"]
        if item["name"] == brand_name
    )

    assert brand == {
        "name": brand_name,
        "item_count": 2,
        "approved_count": 1,
        "draft_count": 1,
        "active_count": 1,
        "inactive_count": 1,
    }


def test_brand_summary_excludes_null_brand_from_brand_list(
    catalogue_session,
):
    service = PlatformCatalogueBrandQueryService(
        catalogue_session
    )

    catalogue_session.add(
        MasterItem(
            master_code="TEST-BRAND-NULL",
            canonical_name=(
                "Null Brand Item"
            ),
            brand_name=None,
            review_status="approved",
            is_active=True,
        )
    )

    catalogue_session.flush()

    summary = service.get_summary()

    assert all(
        brand["name"] is not None
        for brand in summary["brands"]
    )
