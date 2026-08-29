from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app import create_app
from app.errors import ValidationError
from app.extensions import db
from app.models import Product, Tenant
from app.services.tenant.products import (
    ProductIdentityService,
    ProductSkuConflictError,
)


@pytest.fixture()
def app():
    app = create_app()
    app.config.update(TESTING=True)
    return app


def _tenant(
    *,
    name: str,
    business_code: str,
) -> Tenant:
    tenant = Tenant(
        legal_name=name,
        display_name=name,
        business_code=business_code,
        workspace_slug=f"test-{uuid4().hex}",
    )

    db.session.add(tenant)
    db.session.flush()

    return tenant


def _product(
    *,
    tenant_id: str,
    sku: str,
    name: str,
) -> Product:
    product = Product(
        tenant_id=tenant_id,
        internal_sku=sku,
        name=name,
    )

    db.session.add(product)
    db.session.flush()

    return product


def test_supplied_sku_is_trimmed_and_preserved(app):
    with app.app_context():
        tenant = _tenant(
            name="Identity Preserve Tenant",
            business_code=f"IP{uuid4().hex[:6].upper()}",
        )

        service = ProductIdentityService(db.session)

        resolved = service.resolve_internal_sku(
            tenant_id=str(tenant.id),
            supplied_sku="  MANUAL-001  ",
        )

        assert resolved == "MANUAL-001"

        db.session.rollback()


def test_duplicate_supplied_sku_is_rejected_within_same_tenant(app):
    with app.app_context():
        tenant = _tenant(
            name="Identity Duplicate Tenant",
            business_code=f"ID{uuid4().hex[:6].upper()}",
        )

        _product(
            tenant_id=str(tenant.id),
            sku="DUPLICATE-001",
            name="Existing Product",
        )

        service = ProductIdentityService(db.session)

        with pytest.raises(
            ProductSkuConflictError,
            match="already exists",
        ):
            service.resolve_internal_sku(
                tenant_id=str(tenant.id),
                supplied_sku="DUPLICATE-001",
            )

        db.session.rollback()


def test_same_supplied_sku_is_allowed_for_different_tenants(app):
    with app.app_context():
        tenant_one = _tenant(
            name="Identity Tenant One",
            business_code=f"IO{uuid4().hex[:6].upper()}",
        )

        tenant_two = _tenant(
            name="Identity Tenant Two",
            business_code=f"IT{uuid4().hex[:6].upper()}",
        )

        _product(
            tenant_id=str(tenant_one.id),
            sku="SHARED-001",
            name="Tenant One Product",
        )

        service = ProductIdentityService(db.session)

        resolved = service.resolve_internal_sku(
            tenant_id=str(tenant_two.id),
            supplied_sku="SHARED-001",
        )

        assert resolved == "SHARED-001"

        db.session.rollback()


def test_blank_sku_is_generated_from_tenant_sequence(app):
    with app.app_context():
        tenant = _tenant(
            name="Identity Generated Tenant",
            business_code=f"IG{uuid4().hex[:6].upper()}",
        )

        generated_at = datetime(
            2026,
            8,
            29,
            12,
            0,
            tzinfo=UTC,
        )

        service = ProductIdentityService(db.session)

        resolved = service.resolve_internal_sku(
            tenant_id=str(tenant.id),
            supplied_sku=None,
            generated_at=generated_at,
        )

        assert resolved == (
            f"{tenant.business_code}-2026-000001"
        )

        db.session.rollback()


def test_generated_collision_is_skipped(app):
    with app.app_context():
        tenant = _tenant(
            name="Identity Collision Tenant",
            business_code=f"IC{uuid4().hex[:6].upper()}",
        )

        generated_at = datetime(
            2026,
            8,
            29,
            12,
            0,
            tzinfo=UTC,
        )

        first_candidate = (
            f"{tenant.business_code}-2026-000001"
        )

        _product(
            tenant_id=str(tenant.id),
            sku=first_candidate,
            name="Manual Collision Product",
        )

        service = ProductIdentityService(db.session)

        resolved = service.resolve_internal_sku(
            tenant_id=str(tenant.id),
            generated_at=generated_at,
        )

        assert resolved == (
            f"{tenant.business_code}-2026-000002"
        )

        db.session.rollback()


def test_generated_sku_allocation_exhaustion_raises_validation_error(
    app,
    monkeypatch: pytest.MonkeyPatch,
):
    with app.app_context():
        tenant = _tenant(
            name="Identity Exhaustion Tenant",
            business_code=f"IE{uuid4().hex[:6].upper()}",
        )

        collision_sku = "FORCED-COLLISION-001"

        _product(
            tenant_id=str(tenant.id),
            sku=collision_sku,
            name="Forced Collision Product",
        )

        service = ProductIdentityService(db.session)

        monkeypatch.setattr(
            service,
            "MAX_SKU_ALLOCATION_ATTEMPTS",
            3,
        )

        monkeypatch.setattr(
            service.sequence_service,
            "next_product_sku",
            lambda **kwargs: collision_sku,
        )

        with pytest.raises(
            ValidationError,
            match="Unable to allocate a unique product SKU",
        ):
            service.resolve_internal_sku(
                tenant_id=str(tenant.id),
            )

        db.session.rollback()
