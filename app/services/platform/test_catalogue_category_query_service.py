from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app import create_app
from app.extensions import db
from app.models import MasterItem
from app.services.platform.catalogue_category_query_service import (
    PlatformCatalogueCategoryQueryService,
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


def test_category_summary_reports_derived_category_metrics(
    catalogue_session,
):
    service = PlatformCatalogueCategoryQueryService(
        catalogue_session
    )

    baseline = service.get_summary()

    category_name = (
        "TEST OFFICE CATEGORY"
    )

    catalogue_session.add_all(
        [
            MasterItem(
                master_code="TEST-CATEGORY-001",
                canonical_name=(
                    "Test Category Approved Item"
                ),
                category_name=category_name,
                subcategory_name=(
                    "Test Subcategory A"
                ),
                review_status="approved",
                is_active=True,
            ),
            MasterItem(
                master_code="TEST-CATEGORY-002",
                canonical_name=(
                    "Test Category Draft Item"
                ),
                category_name=category_name,
                subcategory_name=(
                    "Test Subcategory B"
                ),
                review_status="draft",
                is_active=False,
            ),
            MasterItem(
                master_code="TEST-CATEGORY-003",
                canonical_name=(
                    "Test Uncategorized Item"
                ),
                category_name=None,
                subcategory_name=None,
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
        summary["categorized_items"]
        == baseline["categorized_items"] + 2
    )

    assert (
        summary["uncategorized_items"]
        == baseline["uncategorized_items"] + 1
    )

    category = next(
        item
        for item in summary["categories"]
        if item["name"] == category_name
    )

    assert category == {
        "name": category_name,
        "item_count": 2,
        "approved_count": 1,
        "draft_count": 1,
        "active_count": 1,
        "inactive_count": 1,
        "subcategories": [
            {
                "name": "Test Subcategory A",
                "item_count": 1,
            },
            {
                "name": "Test Subcategory B",
                "item_count": 1,
            },
        ],
    }


def test_category_summary_excludes_null_category_from_category_list(
    catalogue_session,
):
    service = PlatformCatalogueCategoryQueryService(
        catalogue_session
    )

    catalogue_session.add(
        MasterItem(
            master_code="TEST-CATEGORY-NULL",
            canonical_name=(
                "Null Category Item"
            ),
            category_name=None,
            subcategory_name=None,
            review_status="approved",
            is_active=True,
        )
    )

    catalogue_session.flush()

    summary = service.get_summary()

    assert all(
        category["name"] is not None
        for category in summary["categories"]
    )
