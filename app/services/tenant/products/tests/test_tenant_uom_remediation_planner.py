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
from app.services.tenant.products.tenant_uom_remediation_planner import (
    LINK_EXISTING_UOM,
    NO_ACTION,
    PRESERVE_HISTORICAL_UNIT,
    REVIEW_LEGACY_UNIT,
    REVIEW_OPERATIONAL_UNIT,
    SPLIT_CURRENT_PRODUCTS,
    TenantUOMRemediationPlanner,
)


@pytest.fixture()
def app():
    app = create_app()
    app.config.update(TESTING=True)
    return app


def _tenant(name: str) -> Tenant:
    suffix = uuid4().hex[:8].upper()

    tenant = Tenant(
        legal_name=name,
        display_name=name,
        business_code=f"UR{suffix}",
        workspace_slug=(
            f"uom-remediation-{uuid4().hex}"
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


def test_safe_alias_produces_link_plan(app):
    with app.app_context():
        _prepare_catalogue()

        tenant = _tenant(
            "Safe Remediation Tenant"
        )

        unit = _unit(
            tenant=tenant,
            code="TAB",
            name="Tablet",
        )

        _product(
            tenant=tenant,
            unit=unit,
            sku="SAFE-001",
            name="Paracetamol Tablets 500mg",
        )

        plan = TenantUOMRemediationPlanner(
            db.session
        ).plan_unit(
            tenant_id=str(tenant.id),
            uom_id=str(unit.id),
        )

        assert (
            plan.recommended_action
            == LINK_EXISTING_UOM
        )
        assert plan.suggested_canonical_code == "TAB"
        assert plan.can_apply_automatically is True
        assert plan.requires_human_approval is False

        db.session.rollback()


def test_mixed_unit_requires_product_split(app):
    with app.app_context():
        _prepare_catalogue()

        tenant = _tenant(
            "Mixed Remediation Tenant"
        )

        unit = _unit(
            tenant=tenant,
            code="TAB",
            name="Tablet",
        )

        _product(
            tenant=tenant,
            unit=unit,
            sku="TAB-001",
            name="Paracetamol Tablets",
        )

        _product(
            tenant=tenant,
            unit=unit,
            sku="CAP-001",
            name="Flugone Capsules",
        )

        plan = TenantUOMRemediationPlanner(
            db.session
        ).plan_unit(
            tenant_id=str(tenant.id),
            uom_id=str(unit.id),
        )

        assert (
            plan.recommended_action
            == SPLIT_CURRENT_PRODUCTS
        )
        assert plan.requires_human_approval is True
        assert plan.can_apply_automatically is False
        assert len(plan.product_plans) == 2

        assert all(
            item.recommended_action
            == REVIEW_OPERATIONAL_UNIT
            for item in plan.product_plans
        )

        suggestions = {
            item.internal_sku: (
                item.suggested_canonical_code,
                item.suggestion_confidence,
            )
            for item in plan.product_plans
        }

        assert suggestions["TAB-001"] == (
            "TAB",
            "high",
        )
        assert suggestions["CAP-001"] == (
            "CAP",
            "high",
        )

        evidence = {
            item.internal_sku:
            item.semantic_evidence
            for item in plan.product_plans
        }

        assert evidence["TAB-001"]
        assert evidence["CAP-001"]

        db.session.rollback()


def test_dosage_form_requires_operational_review(app):
    with app.app_context():
        _prepare_catalogue()

        tenant = _tenant(
            "Dosage Remediation Tenant"
        )

        unit = _unit(
            tenant=tenant,
            code="Syrup",
            name="Syrup",
        )

        _product(
            tenant=tenant,
            unit=unit,
            sku="SYP-001",
            name="Cough Syrup 100ml",
        )

        plan = TenantUOMRemediationPlanner(
            db.session
        ).plan_unit(
            tenant_id=str(tenant.id),
            uom_id=str(unit.id),
        )

        assert (
            plan.recommended_action
            == REVIEW_OPERATIONAL_UNIT
        )
        assert plan.suggested_canonical_code is None
        assert plan.requires_human_approval is True
        assert plan.can_apply_automatically is False

        assert (
            plan.product_plans[0]
            .suggested_canonical_code
            is None
        )
        assert (
            plan.product_plans[0]
            .suggestion_confidence
            is None
        )

        db.session.rollback()


def test_product_specific_code_requires_legacy_review(app):
    with app.app_context():
        _prepare_catalogue()

        tenant = _tenant(
            "Legacy Remediation Tenant"
        )

        unit = _unit(
            tenant=tenant,
            code="M084-TAB",
            name="M084 Tablet",
        )

        _product(
            tenant=tenant,
            unit=unit,
            sku="M084-001",
            name="M084 Paracetamol Tablet",
        )

        plan = TenantUOMRemediationPlanner(
            db.session
        ).plan_unit(
            tenant_id=str(tenant.id),
            uom_id=str(unit.id),
        )

        assert (
            plan.recommended_action
            == REVIEW_LEGACY_UNIT
        )
        assert plan.requires_human_approval is True

        db.session.rollback()


def test_existing_canonical_link_is_no_action(app):
    with app.app_context():
        _prepare_catalogue()

        tenant = _tenant(
            "Linked Remediation Tenant"
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
            sku="BOT-001",
            name="Cough Syrup 100ml Bottle",
        )

        plan = TenantUOMRemediationPlanner(
            db.session
        ).plan_unit(
            tenant_id=str(tenant.id),
            uom_id=str(unit.id),
        )

        assert plan.recommended_action == NO_ACTION
        assert plan.can_apply_automatically is False
        assert plan.requires_human_approval is False

        db.session.rollback()


def test_plan_tenant_excludes_linked_by_default(app):
    with app.app_context():
        _prepare_catalogue()

        tenant = _tenant(
            "Tenant Plan Scope"
        )

        linked = _unit(
            tenant=tenant,
            code="Bottle",
            name="Bottle",
            canonical_code="BOT",
        )

        unresolved = _unit(
            tenant=tenant,
            code="Syrup",
            name="Syrup",
        )

        _product(
            tenant=tenant,
            unit=linked,
            sku="LINKED-001",
            name="Bottle Product",
        )

        _product(
            tenant=tenant,
            unit=unresolved,
            sku="UNRESOLVED-001",
            name="Syrup Product",
        )

        result = TenantUOMRemediationPlanner(
            db.session
        ).plan_tenant(
            tenant_id=str(tenant.id)
        )

        assert result.total_count == 1
        assert (
            result.plans[0].source_uom_id
            == str(unresolved.id)
        )

        db.session.rollback()
