from __future__ import annotations

from uuid import uuid4

import pytest

from app import create_app
from app.extensions import db
from app.models import (
    Brand,
    ProductCategory,
    Tenant,
    UnitOfMeasure,
)
from app.services.tenant.products import (
    ProductReferenceService,
)


@pytest.fixture()
def app():
    app = create_app()
    app.config.update(TESTING=True)
    return app


def _tenant(
    *,
    name: str,
) -> Tenant:
    suffix = uuid4().hex[:8].upper()

    tenant = Tenant(
        legal_name=name,
        display_name=name,
        business_code=f"PR{suffix}",
        workspace_slug=(
            f"product-reference-{uuid4().hex}"
        ),
    )

    db.session.add(tenant)
    db.session.flush()

    return tenant


def test_blank_brand_resolves_to_none(app):
    with app.app_context():
        tenant = _tenant(
            name="Blank Brand Tenant"
        )

        service = ProductReferenceService(
            db.session
        )

        assert (
            service.resolve_brand(
                tenant_id=str(tenant.id),
                brand_name="   ",
            )
            is None
        )

        db.session.rollback()


def test_brand_is_created_and_reused_within_tenant(app):
    with app.app_context():
        tenant = _tenant(
            name="Brand Resolve Tenant"
        )

        service = ProductReferenceService(
            db.session
        )

        first = service.resolve_brand(
            tenant_id=str(tenant.id),
            brand_name="  Pfizer  ",
        )

        second = service.resolve_brand(
            tenant_id=str(tenant.id),
            brand_name="Pfizer",
        )

        assert first.id == second.id
        assert first.name == "Pfizer"

        count = (
            db.session.query(Brand)
            .filter(
                Brand.tenant_id
                == str(tenant.id),
                Brand.name == "Pfizer",
            )
            .count()
        )

        assert count == 1

        db.session.rollback()


def test_same_brand_name_is_tenant_isolated(app):
    with app.app_context():
        tenant_one = _tenant(
            name="Brand Tenant One"
        )

        tenant_two = _tenant(
            name="Brand Tenant Two"
        )

        service = ProductReferenceService(
            db.session
        )

        first = service.resolve_brand(
            tenant_id=str(tenant_one.id),
            brand_name="Pfizer",
        )

        second = service.resolve_brand(
            tenant_id=str(tenant_two.id),
            brand_name="Pfizer",
        )

        assert first.id != second.id
        assert first.tenant_id != second.tenant_id

        db.session.rollback()


def test_category_is_created_and_reused_within_tenant(app):
    with app.app_context():
        tenant = _tenant(
            name="Category Resolve Tenant"
        )

        service = ProductReferenceService(
            db.session
        )

        first = service.resolve_category(
            tenant_id=str(tenant.id),
            category_name="  Antibiotics  ",
        )

        second = service.resolve_category(
            tenant_id=str(tenant.id),
            category_name="Antibiotics",
        )

        assert first.id == second.id
        assert first.name == "Antibiotics"

        count = (
            db.session.query(ProductCategory)
            .filter(
                ProductCategory.tenant_id
                == str(tenant.id),
                ProductCategory.name
                == "Antibiotics",
            )
            .count()
        )

        assert count == 1

        db.session.rollback()


def test_blank_unit_resolves_to_none(app):
    with app.app_context():
        tenant = _tenant(
            name="Blank Unit Tenant"
        )

        service = ProductReferenceService(
            db.session
        )

        assert (
            service.resolve_unit(
                tenant_id=str(tenant.id),
                unit_code=None,
                unit_name=None,
            )
            is None
        )

        db.session.rollback()


def test_unit_is_created_and_reused_by_code(app):
    with app.app_context():
        tenant = _tenant(
            name="Unit Resolve Tenant"
        )

        service = ProductReferenceService(
            db.session
        )

        first = service.resolve_unit(
            tenant_id=str(tenant.id),
            unit_code="  TAB  ",
            unit_name="  Tablet  ",
        )

        second = service.resolve_unit(
            tenant_id=str(tenant.id),
            unit_code="TAB",
            unit_name=None,
        )

        assert first.id == second.id
        assert first.code == "TAB"
        assert first.name == "Tablet"

        count = (
            db.session.query(UnitOfMeasure)
            .filter(
                UnitOfMeasure.tenant_id
                == str(tenant.id),
                UnitOfMeasure.code == "TAB",
            )
            .count()
        )

        assert count == 1

        db.session.rollback()


def test_new_unit_requires_code(app):
    with app.app_context():
        tenant = _tenant(
            name="Unit Code Tenant"
        )

        service = ProductReferenceService(
            db.session
        )

        with pytest.raises(
            ValueError,
            match=(
                "unit_code is required when "
                "creating a new unit"
            ),
        ):
            service.resolve_unit(
                tenant_id=str(tenant.id),
                unit_code=None,
                unit_name="Tablet",
            )

        db.session.rollback()


def test_new_unit_requires_name(app):
    with app.app_context():
        tenant = _tenant(
            name="Unit Name Tenant"
        )

        service = ProductReferenceService(
            db.session
        )

        with pytest.raises(
            ValueError,
            match=(
                "unit_name is required when "
                "creating a new unit"
            ),
        ):
            service.resolve_unit(
                tenant_id=str(tenant.id),
                unit_code="TAB",
                unit_name=None,
            )

        db.session.rollback()
