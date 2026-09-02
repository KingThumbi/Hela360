from __future__ import annotations

from uuid import uuid4

import pytest
from flask import Flask

from app.extensions import db
from app.models import MasterItem, Product, Tenant
from app.services.tenant.catalogue import (
    MasterCatalogueListFilters,
    MasterCatalogueQueryService,
)


@pytest.fixture()
def app():
    app = Flask(__name__)

    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TESTING=True,
    )

    db.init_app(app)

    with app.app_context():
        Tenant.__table__.create(db.engine)
        MasterItem.__table__.create(db.engine)
        Product.__table__.create(db.engine)

        yield app

        db.session.remove()

        Product.__table__.drop(db.engine)
        MasterItem.__table__.drop(db.engine)
        Tenant.__table__.drop(db.engine)


def _tenant(
    *,
    name: str,
) -> Tenant:
    suffix = uuid4().hex[:8].upper()

    tenant = Tenant(
        legal_name=name,
        display_name=name,
        business_code=f"T{suffix}",
        workspace_slug=f"catalogue-{uuid4().hex}",
    )

    db.session.add(tenant)
    db.session.flush()

    return tenant


def _master_item(
    *,
    code: str,
    name: str,
    review_status: str = "approved",
    is_active: bool = True,
    generic_name: str | None = None,
    dosage_form: str | None = None,
    item_class: str | None = None,
    category_name: str | None = None,
) -> MasterItem:
    item = MasterItem(
        master_code=code,
        canonical_name=name,
        generic_name=generic_name,
        dosage_form=dosage_form,
        item_class=item_class,
        category_name=category_name,
        review_status=review_status,
        is_active=is_active,
    )

    db.session.add(item)
    db.session.flush()

    return item


def _product(
    *,
    tenant_id: str,
    master_item_id: str,
    sku: str,
    name: str,
    is_active: bool = True,
) -> Product:
    product = Product(
        tenant_id=tenant_id,
        master_item_id=master_item_id,
        internal_sku=sku,
        name=name,
        is_active=is_active,
    )

    db.session.add(product)
    db.session.flush()

    return product


def test_list_returns_only_approved_active_items(app):
    with app.app_context():
        tenant = _tenant(
            name="Catalogue Visibility Tenant"
        )

        visible = _master_item(
            code=f"HMI-{uuid4().hex[:8]}",
            name="Visible Item",
        )

        _master_item(
            code=f"HMI-{uuid4().hex[:8]}",
            name="Draft Item",
            review_status="draft",
        )

        _master_item(
            code=f"HMI-{uuid4().hex[:8]}",
            name="Inactive Item",
            is_active=False,
        )

        service = MasterCatalogueQueryService(
            db.session
        )

        items, pagination = service.list_items(
            tenant_id=str(tenant.id),
            filters=MasterCatalogueListFilters(),
        )

        assert [item["id"] for item in items] == [
            visible.id
        ]
        assert pagination["total"] == 1

        db.session.rollback()


def test_adoption_status_is_tenant_isolated(app):
    with app.app_context():
        tenant_one = _tenant(
            name="Catalogue Tenant One"
        )
        tenant_two = _tenant(
            name="Catalogue Tenant Two"
        )

        master_item = _master_item(
            code=f"HMI-{uuid4().hex[:8]}",
            name="Tenant Isolation Item",
        )

        product = _product(
            tenant_id=str(tenant_one.id),
            master_item_id=str(master_item.id),
            sku="TENANT-ONE-001",
            name="Tenant One Product",
        )

        service = MasterCatalogueQueryService(
            db.session
        )

        tenant_one_item = service.get_item(
            tenant_id=str(tenant_one.id),
            master_item_id=str(master_item.id),
        )

        tenant_two_item = service.get_item(
            tenant_id=str(tenant_two.id),
            master_item_id=str(master_item.id),
        )

        assert (
            tenant_one_item["adoption"]["is_adopted"]
            is True
        )
        assert (
            tenant_one_item["adoption"]["product_id"]
            == product.id
        )

        assert (
            tenant_two_item["adoption"]["is_adopted"]
            is False
        )
        assert (
            tenant_two_item["adoption"]["product_id"]
            is None
        )

        db.session.rollback()


def test_adoption_status_filters_available_and_adopted(app):
    with app.app_context():
        tenant = _tenant(
            name="Catalogue Filter Tenant"
        )

        adopted_item = _master_item(
            code=f"HMI-{uuid4().hex[:8]}",
            name="Adopted Item",
        )

        available_item = _master_item(
            code=f"HMI-{uuid4().hex[:8]}",
            name="Available Item",
        )

        _product(
            tenant_id=str(tenant.id),
            master_item_id=str(adopted_item.id),
            sku="ADOPTED-001",
            name="Adopted Tenant Product",
        )

        service = MasterCatalogueQueryService(
            db.session
        )

        adopted, _ = service.list_items(
            tenant_id=str(tenant.id),
            filters=MasterCatalogueListFilters(
                adoption_status="adopted"
            ),
        )

        available, _ = service.list_items(
            tenant_id=str(tenant.id),
            filters=MasterCatalogueListFilters(
                adoption_status="available"
            ),
        )

        assert [
            item["id"]
            for item in adopted
        ] == [adopted_item.id]

        assert [
            item["id"]
            for item in available
        ] == [available_item.id]

        db.session.rollback()


def test_inactive_tenant_product_remains_adopted(app):
    with app.app_context():
        tenant = _tenant(
            name="Catalogue Archived Product Tenant"
        )

        master_item = _master_item(
            code=f"HMI-{uuid4().hex[:8]}",
            name="Archived Product Master Item",
        )

        product = _product(
            tenant_id=str(tenant.id),
            master_item_id=str(master_item.id),
            sku="ARCHIVED-001",
            name="Archived Tenant Product",
            is_active=False,
        )

        service = MasterCatalogueQueryService(
            db.session
        )

        item = service.get_item(
            tenant_id=str(tenant.id),
            master_item_id=str(master_item.id),
        )

        assert item["adoption"]["is_adopted"] is True
        assert item["adoption"]["product_id"] == product.id
        assert (
            item["adoption"]["product_is_active"]
            is False
        )

        db.session.rollback()


def test_search_and_filters_apply_to_canonical_fields(app):
    with app.app_context():
        tenant = _tenant(
            name="Catalogue Search Tenant"
        )

        matching = _master_item(
            code=f"HMI-{uuid4().hex[:8]}",
            name="Amoxicillin 500 mg Capsules",
            generic_name="Amoxicillin",
            dosage_form="Capsule",
            item_class="medicine",
            category_name="Antibiotics",
        )

        _master_item(
            code=f"HMI-{uuid4().hex[:8]}",
            name="Paracetamol Tablets",
            generic_name="Paracetamol",
            dosage_form="Tablet",
            item_class="medicine",
            category_name="Analgesics",
        )

        service = MasterCatalogueQueryService(
            db.session
        )

        items, pagination = service.list_items(
            tenant_id=str(tenant.id),
            filters=MasterCatalogueListFilters(
                search="amoxicillin",
                item_class="medicine",
                category="Antibiotics",
                dosage_form="Capsule",
            ),
        )

        assert [
            item["id"]
            for item in items
        ] == [matching.id]

        assert pagination["total"] == 1

        db.session.rollback()


def test_list_paginates_deterministically(app):
    with app.app_context():
        tenant = _tenant(
            name="Catalogue Pagination Tenant"
        )

        for index in range(5):
            _master_item(
                code=(
                    f"HMI-{uuid4().hex[:8]}"
                ),
                name=f"Pagination Item {index}",
            )

        service = MasterCatalogueQueryService(
            db.session
        )

        items, pagination = service.list_items(
            tenant_id=str(tenant.id),
            filters=MasterCatalogueListFilters(
                page=2,
                per_page=2,
            ),
        )

        assert len(items) == 2
        assert pagination == {
            "page": 2,
            "per_page": 2,
            "total": 5,
            "pages": 3,
            "has_prev": True,
            "has_next": True,
        }

        db.session.rollback()


def test_get_item_returns_none_for_unavailable_master_item(app):
    with app.app_context():
        tenant = _tenant(
            name="Catalogue Detail Tenant"
        )

        draft_item = _master_item(
            code=f"HMI-{uuid4().hex[:8]}",
            name="Unapproved Item",
            review_status="draft",
        )

        service = MasterCatalogueQueryService(
            db.session
        )

        item = service.get_item(
            tenant_id=str(tenant.id),
            master_item_id=str(draft_item.id),
        )

        assert item is None

        db.session.rollback()


def test_filter_parser_accepts_q_alias_and_validates_status():
    filters = MasterCatalogueListFilters.from_query(
        {
            "q": "amoxicillin",
            "page": "2",
            "per_page": "10",
            "adoption_status": "available",
        }
    )

    assert filters.search == "amoxicillin"
    assert filters.page == 2
    assert filters.per_page == 10
    assert filters.adoption_status == "available"
