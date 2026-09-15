from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from app import create_app
from app.extensions import db
from app.models import (
    CanonicalUnitOfMeasure,
    Product,
    ProductUnit,
    Tenant,
    UnitOfMeasure,
)
from app.services.platform.canonical_uom_catalogue_service import (
    CanonicalUOMCatalogueService,
)
from app.services.tenant.products.tenant_uom_audit_service import (
    CANONICALLY_LINKED,
    CUSTOM_UNMAPPED,
    DOSAGE_FORM_AS_UOM,
    LEGACY_PRODUCT_SPECIFIC,
    MIXED_PRODUCT_SEMANTICS,
    SAFE_TO_LINK,
    TenantUOMAuditService,
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
        business_code=f"UA{suffix}",
        workspace_slug=(
            f"uom-audit-{uuid4().hex}"
        ),
    )

    db.session.add(tenant)
    db.session.flush()

    return tenant


def _unit(
    *,
    tenant: Tenant,
    code: str,
    name: str,
    canonical_code: str | None = None,
) -> UnitOfMeasure:
    canonical_id = None

    if canonical_code:
        canonical = (
            db.session.query(
                CanonicalUnitOfMeasure
            )
            .filter(
                CanonicalUnitOfMeasure.code
                == canonical_code
            )
            .one()
        )

        canonical_id = str(canonical.id)

    unit = UnitOfMeasure(
        tenant_id=str(tenant.id),
        canonical_uom_id=canonical_id,
        code=code,
        name=name,
        base_factor=Decimal("1"),
    )

    db.session.add(unit)
    db.session.flush()

    return unit


def _product(
    *,
    tenant: Tenant,
    unit: UnitOfMeasure,
    sku: str,
    name: str,
) -> Product:
    product = Product(
        tenant_id=str(tenant.id),
        unit_id=str(unit.id),
        internal_sku=sku,
        name=name,
        product_type="stockable",
        track_inventory=True,
        track_batches=True,
        track_expiry=True,
        requires_prescription=False,
        allow_negative_stock=False,
        reorder_level=Decimal("0"),
        reorder_qty=Decimal("0"),
        is_active=True,
    )

    db.session.add(product)
    db.session.flush()

    product_unit = ProductUnit(
        tenant_id=str(tenant.id),
        product_id=str(product.id),
        unit_id=str(unit.id),
        conversion_factor_to_base=Decimal("1"),
        is_base=True,
        can_sell=True,
        can_receive=True,
        is_active=True,
    )

    db.session.add(product_unit)
    db.session.flush()

    return product


def _prepare_catalogue():
    CanonicalUOMCatalogueService(
        db.session
    ).synchronize()


def test_unambiguous_tablet_unit_is_safe_to_link(app):
    with app.app_context():
        _prepare_catalogue()

        tenant = _tenant(
            name="Safe Tablet Tenant"
        )

        unit = _unit(
            tenant=tenant,
            code="TAB",
            name="Tablet",
        )

        _product(
            tenant=tenant,
            unit=unit,
            sku="SAFE-TAB-001",
            name="Paracetamol Tablets 500mg",
        )

        item = TenantUOMAuditService(
            db.session
        ).audit_unit(
            tenant_id=str(tenant.id),
            uom_id=str(unit.id),
        )

        assert item.classification == SAFE_TO_LINK
        assert item.suggested_canonical_code == "TAB"
        assert item.safe_to_link is True
        assert item.requires_product_split is False
        assert item.product_count == 1

        db.session.rollback()


def test_mixed_tablet_and_capsule_usage_requires_split(app):
    with app.app_context():
        _prepare_catalogue()

        tenant = _tenant(
            name="Mixed Unit Tenant"
        )

        unit = _unit(
            tenant=tenant,
            code="TAB",
            name="Tablet",
        )

        _product(
            tenant=tenant,
            unit=unit,
            sku="MIX-TAB-001",
            name="Paracetamol Tablets 500mg",
        )

        _product(
            tenant=tenant,
            unit=unit,
            sku="MIX-CAP-001",
            name="Flugone Capsules 10s",
        )

        item = TenantUOMAuditService(
            db.session
        ).audit_unit(
            tenant_id=str(tenant.id),
            uom_id=str(unit.id),
        )

        assert (
            item.classification
            == MIXED_PRODUCT_SEMANTICS
        )
        assert item.safe_to_link is False
        assert item.requires_product_split is True
        assert item.suggested_canonical_code == "TAB"

        assert any(
            "MIX-CAP-001" in reason
            and "CAP" in reason
            for reason in item.reasons
        )

        db.session.rollback()


def test_dosage_form_unit_is_not_auto_mapped(app):
    with app.app_context():
        _prepare_catalogue()

        tenant = _tenant(
            name="Dosage Form Tenant"
        )

        unit = _unit(
            tenant=tenant,
            code="Syrup",
            name="Syrup",
        )

        _product(
            tenant=tenant,
            unit=unit,
            sku="SYRUP-001",
            name="Piriton Syrup 100ml",
        )

        item = TenantUOMAuditService(
            db.session
        ).audit_unit(
            tenant_id=str(tenant.id),
            uom_id=str(unit.id),
        )

        assert (
            item.classification
            == DOSAGE_FORM_AS_UOM
        )
        assert item.suggested_canonical_code is None
        assert item.safe_to_link is False

        db.session.rollback()


def test_product_specific_legacy_code_requires_review(app):
    with app.app_context():
        _prepare_catalogue()

        tenant = _tenant(
            name="Legacy Unit Tenant"
        )

        unit = _unit(
            tenant=tenant,
            code="M084-TAB",
            name="M084 Tablet",
        )

        _product(
            tenant=tenant,
            unit=unit,
            sku="M084-PARA",
            name="M084 Paracetamol Tablet",
        )

        item = TenantUOMAuditService(
            db.session
        ).audit_unit(
            tenant_id=str(tenant.id),
            uom_id=str(unit.id),
        )

        assert (
            item.classification
            == LEGACY_PRODUCT_SPECIFIC
        )
        assert item.safe_to_link is False

        db.session.rollback()


def test_unknown_custom_unit_remains_unmapped(app):
    with app.app_context():
        _prepare_catalogue()

        tenant = _tenant(
            name="Custom Unit Tenant"
        )

        unit = _unit(
            tenant=tenant,
            code="WHOLE",
            name="Whole",
        )

        _product(
            tenant=tenant,
            unit=unit,
            sku="CUSTOM-001",
            name="Custom Product",
        )

        item = TenantUOMAuditService(
            db.session
        ).audit_unit(
            tenant_id=str(tenant.id),
            uom_id=str(unit.id),
        )

        assert (
            item.classification
            == CUSTOM_UNMAPPED
        )
        assert item.suggested_canonical_code is None
        assert item.safe_to_link is False

        db.session.rollback()


def test_valid_existing_link_is_reported_as_linked(app):
    with app.app_context():
        _prepare_catalogue()

        tenant = _tenant(
            name="Linked Unit Tenant"
        )

        unit = _unit(
            tenant=tenant,
            code="Bottle",
            name="Bottle",
            canonical_code="BOT",
        )

        _product(
            tenant=tenant,
            unit=unit,
            sku="BOTTLE-001",
            name="Cough Syrup 100ml Bottle",
        )

        item = TenantUOMAuditService(
            db.session
        ).audit_unit(
            tenant_id=str(tenant.id),
            uom_id=str(unit.id),
        )

        assert (
            item.classification
            == CANONICALLY_LINKED
        )
        assert item.canonical_code == "BOT"
        assert item.suggested_canonical_code == "BOT"
        assert item.safe_to_link is False
        assert item.requires_product_split is False

        db.session.rollback()


def test_bad_existing_link_is_detected_as_mixed(app):
    with app.app_context():
        _prepare_catalogue()

        tenant = _tenant(
            name="Bad Linked Unit Tenant"
        )

        unit = _unit(
            tenant=tenant,
            code="TAB",
            name="Tablet",
            canonical_code="TAB",
        )

        _product(
            tenant=tenant,
            unit=unit,
            sku="BAD-LINK-001",
            name="Flugone Capsules 10s",
        )

        item = TenantUOMAuditService(
            db.session
        ).audit_unit(
            tenant_id=str(tenant.id),
            uom_id=str(unit.id),
        )

        assert (
            item.classification
            == MIXED_PRODUCT_SEMANTICS
        )
        assert item.canonical_code == "TAB"
        assert item.requires_product_split is True

        db.session.rollback()


def test_audit_tenant_is_tenant_isolated(app):
    with app.app_context():
        _prepare_catalogue()

        tenant_one = _tenant(
            name="Audit Tenant One"
        )

        tenant_two = _tenant(
            name="Audit Tenant Two"
        )

        unit_one = _unit(
            tenant=tenant_one,
            code="EA",
            name="Each",
        )

        _unit(
            tenant=tenant_two,
            code="TAB",
            name="Tablet",
        )

        result = TenantUOMAuditService(
            db.session
        ).audit_tenant(
            tenant_id=str(tenant_one.id),
        )

        assert result.total_count == 1
        assert result.items[0].uom_id == str(unit_one.id)
        assert (
            result.items[0].tenant_id
            == str(tenant_one.id)
        )

        db.session.rollback()
