from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app import create_app
from app.extensions import db
from app.models import (
    Brand,
    MasterItem,
    Product,
    ProductCategory,
    ProductUnit,
    Tenant,
    UnitOfMeasure,
)
from app.services.common.audit_actions import (
    AuditAction,
)
from app.services.common.audit_modules import (
    AuditModule,
)
from app.services.tenant.catalogue import (
    MasterCatalogueAdoptionService,
    MasterItemAlreadyAdoptedError,
    MasterItemNotAvailableError,
)


@pytest.fixture()
def app():
    app = create_app()
    app.config.update(TESTING=True)
    return app


class AuditSpy:
    def __init__(self):
        self.calls = []

    def log(self, **kwargs):
        self.calls.append(kwargs)

        return SimpleNamespace(
            id=str(uuid4())
        )


def _tenant(
    *,
    name: str,
) -> Tenant:
    suffix = uuid4().hex[:8].upper()

    tenant = Tenant(
        legal_name=name,
        display_name=name,
        business_code=f"CA{suffix}",
        workspace_slug=(
            f"catalogue-adoption-{uuid4().hex}"
        ),
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
    brand_name: str | None = None,
    category_name: str | None = None,
    generic_name: str | None = None,
    manufacturer: str | None = None,
    country_of_origin: str | None = None,
    requires_prescription: bool | None = None,
) -> MasterItem:
    item = MasterItem(
        master_code=code,
        canonical_name=name,
        brand_name=brand_name,
        category_name=category_name,
        generic_name=generic_name,
        manufacturer=manufacturer,
        country_of_origin=country_of_origin,
        requires_prescription=(
            requires_prescription
        ),
        review_status=review_status,
        is_active=is_active,
    )

    db.session.add(item)
    db.session.flush()

    return item


def test_adoption_creates_linked_tenant_product(app):
    with app.app_context():
        tenant = _tenant(
            name="Basic Adoption Tenant"
        )

        item = _master_item(
            code="HMI-ADOPT-001",
            name="Amoxicillin 500 mg Capsules",
            generic_name="Amoxicillin",
            manufacturer="Example Pharma",
            country_of_origin="Kenya",
            requires_prescription=True,
        )

        audit = AuditSpy()

        service = MasterCatalogueAdoptionService(
            db.session,
            audit_service=audit,
        )

        result = service.adopt(
            tenant_id=str(tenant.id),
            master_item_id=str(item.id),
        )

        product = result.product

        assert product.tenant_id == str(tenant.id)
        assert product.master_item_id == str(item.id)
        assert (
            product.name
            == "Amoxicillin 500 mg Capsules"
        )
        assert product.generic_name == "Amoxicillin"
        assert product.manufacturer == "Example Pharma"
        assert product.country_of_origin == "Kenya"
        assert product.requires_prescription is True

        assert product.internal_sku != item.master_code
        assert product.default_sale_price is None
        assert product.cost_price is None
        assert product.tax_code is None

        db.session.rollback()


def test_adoption_uses_canonical_brand_and_category(app):
    with app.app_context():
        tenant = _tenant(
            name="Reference Adoption Tenant"
        )

        item = _master_item(
            code="HMI-ADOPT-002",
            name="Reference Product",
            brand_name="Example Brand",
            category_name="Antibiotics",
        )

        service = MasterCatalogueAdoptionService(
            db.session,
            audit_service=AuditSpy(),
        )

        result = service.adopt(
            tenant_id=str(tenant.id),
            master_item_id=str(item.id),
            internal_sku="MANUAL-REF-001",
        )

        brand = db.session.get(
            Brand,
            result.product.brand_id,
        )

        category = db.session.get(
            ProductCategory,
            result.product.category_id,
        )

        assert brand.name == "Example Brand"
        assert brand.tenant_id == str(tenant.id)

        assert category.name == "Antibiotics"
        assert category.tenant_id == str(tenant.id)

        db.session.rollback()


def test_explicit_name_brand_and_category_override_canonical(app):
    with app.app_context():
        tenant = _tenant(
            name="Override Adoption Tenant"
        )

        item = _master_item(
            code="HMI-ADOPT-003",
            name="Canonical Name",
            brand_name="Canonical Brand",
            category_name="Canonical Category",
        )

        service = MasterCatalogueAdoptionService(
            db.session,
            audit_service=AuditSpy(),
        )

        result = service.adopt(
            tenant_id=str(tenant.id),
            master_item_id=str(item.id),
            internal_sku="OVERRIDE-001",
            name="Tenant Product Name",
            brand_name="Tenant Brand",
            category_name="Tenant Category",
        )

        product = result.product

        assert product.name == "Tenant Product Name"

        brand = db.session.get(
            Brand,
            product.brand_id,
        )

        category = db.session.get(
            ProductCategory,
            product.category_id,
        )

        assert brand.name == "Tenant Brand"
        assert category.name == "Tenant Category"

        db.session.rollback()


def test_explicit_unit_creates_base_product_unit(app):
    with app.app_context():
        tenant = _tenant(
            name="Unit Adoption Tenant"
        )

        item = _master_item(
            code="HMI-ADOPT-004",
            name="Tablet Product",
        )

        service = MasterCatalogueAdoptionService(
            db.session,
            audit_service=AuditSpy(),
        )

        result = service.adopt(
            tenant_id=str(tenant.id),
            master_item_id=str(item.id),
            internal_sku="UNIT-001",
            unit_code="TAB",
            unit_name="Tablet",
        )

        assert result.product.unit_id is not None
        assert result.product_unit is not None

        unit = db.session.get(
            UnitOfMeasure,
            result.product.unit_id,
        )

        assert unit.code == "TAB"
        assert unit.name == "Tablet"

        product_unit = result.product_unit

        assert product_unit.product_id == result.product.id
        assert product_unit.unit_id == unit.id
        assert product_unit.is_base is True
        assert product_unit.can_sell is True
        assert product_unit.can_receive is True

        db.session.rollback()


def test_no_explicit_unit_does_not_infer_pack_unit(app):
    with app.app_context():
        tenant = _tenant(
            name="No Unit Adoption Tenant"
        )

        item = _master_item(
            code="HMI-ADOPT-005",
            name="No Unit Product",
        )

        item.pack_unit = "tablet"

        service = MasterCatalogueAdoptionService(
            db.session,
            audit_service=AuditSpy(),
        )

        result = service.adopt(
            tenant_id=str(tenant.id),
            master_item_id=str(item.id),
            internal_sku="NO-UNIT-001",
        )

        assert result.product.unit_id is None
        assert result.product_unit is None

        count = (
            db.session.query(ProductUnit)
            .filter(
                ProductUnit.product_id
                == result.product.id
            )
            .count()
        )

        assert count == 0

        db.session.rollback()


def test_same_master_item_cannot_be_adopted_twice_by_tenant(
    app,
):
    with app.app_context():
        tenant = _tenant(
            name="Duplicate Adoption Tenant"
        )

        item = _master_item(
            code="HMI-ADOPT-006",
            name="Duplicate Product",
        )

        service = MasterCatalogueAdoptionService(
            db.session,
            audit_service=AuditSpy(),
        )

        first = service.adopt(
            tenant_id=str(tenant.id),
            master_item_id=str(item.id),
            internal_sku="DUP-001",
        )

        with pytest.raises(
            MasterItemAlreadyAdoptedError,
        ) as exc_info:
            service.adopt(
                tenant_id=str(tenant.id),
                master_item_id=str(item.id),
                internal_sku="DUP-002",
            )

        assert (
            exc_info.value.product.id
            == first.product.id
        )

        db.session.rollback()


def test_same_master_item_can_be_adopted_by_different_tenants(
    app,
):
    with app.app_context():
        tenant_one = _tenant(
            name="Adoption Tenant One"
        )

        tenant_two = _tenant(
            name="Adoption Tenant Two"
        )

        item = _master_item(
            code="HMI-ADOPT-007",
            name="Shared Master Product",
        )

        service = MasterCatalogueAdoptionService(
            db.session,
            audit_service=AuditSpy(),
        )

        first = service.adopt(
            tenant_id=str(tenant_one.id),
            master_item_id=str(item.id),
            internal_sku="T1-001",
        )

        second = service.adopt(
            tenant_id=str(tenant_two.id),
            master_item_id=str(item.id),
            internal_sku="T2-001",
        )

        assert first.product.id != second.product.id
        assert (
            first.product.master_item_id
            == second.product.master_item_id
        )

        db.session.rollback()


@pytest.mark.parametrize(
    ("review_status", "is_active"),
    [
        ("draft", True),
        ("approved", False),
    ],
)
def test_unavailable_master_item_cannot_be_adopted(
    app,
    review_status,
    is_active,
):
    with app.app_context():
        tenant = _tenant(
            name="Unavailable Adoption Tenant"
        )

        item = _master_item(
            code=f"HMI-{uuid4().hex[:8]}",
            name="Unavailable Product",
            review_status=review_status,
            is_active=is_active,
        )

        service = MasterCatalogueAdoptionService(
            db.session,
            audit_service=AuditSpy(),
        )

        with pytest.raises(
            MasterItemNotAvailableError
        ):
            service.adopt(
                tenant_id=str(tenant.id),
                master_item_id=str(item.id),
                internal_sku="UNAVAILABLE-001",
            )

        db.session.rollback()


def test_adoption_records_transactional_audit(app):
    with app.app_context():
        tenant = _tenant(
            name="Audit Adoption Tenant"
        )

        item = _master_item(
            code="HMI-ADOPT-008",
            name="Audited Product",
        )

        audit = AuditSpy()

        service = MasterCatalogueAdoptionService(
            db.session,
            audit_service=audit,
        )

        result = service.adopt(
            tenant_id=str(tenant.id),
            master_item_id=str(item.id),
            internal_sku="AUDIT-001",
            user_id="user-1",
            branch_id="branch-1",
            session_id="session-1",
        )

        assert len(audit.calls) == 1

        call = audit.calls[0]

        assert call["module"] == AuditModule.CATALOGUE
        assert (
            call["action"]
            == AuditAction.MASTER_CATALOGUE_ITEM_ADOPTED
        )
        assert call["tenant_id"] == str(tenant.id)
        assert call["entity_id"] == result.product.id
        assert call["user_id"] == "user-1"
        assert call["branch_id"] == "branch-1"
        assert call["session_id"] == "session-1"
        assert call["commit"] is False

        assert (
            call["new_values"]["master_item_id"]
            == item.id
        )
        assert (
            call["new_values"]["product_id"]
            == result.product.id
        )
        assert (
            call["new_values"]["internal_sku"]
            == "AUDIT-001"
        )

        db.session.rollback()
