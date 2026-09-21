from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from app import create_app
from app.errors import ValidationError
from app.extensions import db
from app.models import (
    Product,
    ProductUnit,
    Tenant,
    UnitOfMeasure,
)
from app.services.tenant.inventory.product_unit_conversion_service import (
    ProductUnitConversionService,
)


@pytest.fixture()
def app():
    app = create_app()
    app.config.update(TESTING=True)
    return app


def _tenant(*, name: str) -> Tenant:
    suffix = uuid4().hex[:10]

    tenant = Tenant(
        legal_name=name,
        display_name=name,
        workspace_slug=f"pu-conversion-{suffix}",
    )

    db.session.add(tenant)
    db.session.flush()

    return tenant


def _unit(
    *,
    tenant: Tenant,
    code: str,
    name: str,
    base_factor: Decimal = Decimal("1"),
) -> UnitOfMeasure:
    unit = UnitOfMeasure(
        tenant_id=str(tenant.id),
        code=code,
        name=name,
        base_factor=base_factor,
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
    default_sale_price: Decimal | None = None,
    min_sale_price: Decimal | None = None,
) -> Product:
    product = Product(
        tenant_id=str(tenant.id),
        unit_id=str(unit.id),
        internal_sku=sku,
        name=name,
        product_type="stockable",
        track_inventory=True,
        track_batches=False,
        track_expiry=False,
        requires_prescription=False,
        allow_negative_stock=False,
        reorder_level=Decimal("0"),
        reorder_qty=Decimal("0"),
        default_sale_price=default_sale_price,
        min_sale_price=min_sale_price,
        is_active=True,
    )

    db.session.add(product)
    db.session.flush()

    return product


def _product_unit(
    *,
    tenant: Tenant,
    product: Product,
    unit: UnitOfMeasure,
    factor: Decimal,
    is_base: bool = False,
    can_sell: bool = True,
    can_receive: bool = True,
    sale_price: Decimal | None = None,
    minimum_sale_price: Decimal | None = None,
    is_active: bool = True,
) -> ProductUnit:
    product_unit = ProductUnit(
        tenant_id=str(tenant.id),
        product_id=str(product.id),
        unit_id=str(unit.id),
        conversion_factor_to_base=factor,
        is_base=is_base,
        can_sell=can_sell,
        can_receive=can_receive,
        sale_price=sale_price,
        minimum_sale_price=minimum_sale_price,
        is_active=is_active,
    )

    db.session.add(product_unit)
    db.session.flush()

    return product_unit


def test_explicit_product_unit_resolves_product_specific_conversion(app):
    with app.app_context():
        tenant = _tenant(name="Explicit Conversion Tenant")

        each = _unit(
            tenant=tenant,
            code="EA",
            name="Each",
        )

        box = _unit(
            tenant=tenant,
            code="BOX",
            name="Box",
        )

        product = _product(
            tenant=tenant,
            unit=each,
            sku="CONVERT-001",
            name="Explicit Conversion Product",
        )

        product_unit = _product_unit(
            tenant=tenant,
            product=product,
            unit=box,
            factor=Decimal("10"),
            sale_price=Decimal("500"),
            minimum_sale_price=Decimal("450"),
        )

        service = ProductUnitConversionService(db.session)

        resolution = service.resolve_for_sale(
            tenant_id=str(tenant.id),
            product=product,
            product_unit_id=str(product_unit.id),
        )

        assert resolution.product_unit_id == str(product_unit.id)
        assert resolution.unit_id == str(box.id)
        assert resolution.unit_code == "BOX"
        assert resolution.unit_name == "Box"
        assert (
            resolution.conversion_factor_to_base
            == Decimal("10.000000")
        )
        assert (
            resolution.to_base_quantity(Decimal("2"))
            == Decimal("20.0000")
        )
        assert (
            resolution.to_base_unit_cost(Decimal("500"))
            == Decimal("50.00")
        )
        assert resolution.sale_price == Decimal("500.00")
        assert (
            resolution.minimum_sale_price
            == Decimal("450.00")
        )

        db.session.rollback()


def test_sale_rejects_product_unit_that_cannot_sell(app):
    with app.app_context():
        tenant = _tenant(name="Cannot Sell Tenant")

        each = _unit(
            tenant=tenant,
            code="EA",
            name="Each",
        )

        pack = _unit(
            tenant=tenant,
            code="PACK",
            name="Pack",
        )

        product = _product(
            tenant=tenant,
            unit=each,
            sku="CONVERT-002",
            name="Cannot Sell Product",
        )

        product_unit = _product_unit(
            tenant=tenant,
            product=product,
            unit=pack,
            factor=Decimal("5"),
            can_sell=False,
        )

        service = ProductUnitConversionService(db.session)

        with pytest.raises(
            ValidationError,
            match="not sellable",
        ):
            service.resolve_for_sale(
                tenant_id=str(tenant.id),
                product=product,
                product_unit_id=str(product_unit.id),
            )

        db.session.rollback()


def test_receipt_rejects_product_unit_that_cannot_receive(app):
    with app.app_context():
        tenant = _tenant(name="Cannot Receive Tenant")

        each = _unit(
            tenant=tenant,
            code="EA",
            name="Each",
        )

        carton = _unit(
            tenant=tenant,
            code="CARTON",
            name="Carton",
        )

        product = _product(
            tenant=tenant,
            unit=each,
            sku="CONVERT-003",
            name="Cannot Receive Product",
        )

        product_unit = _product_unit(
            tenant=tenant,
            product=product,
            unit=carton,
            factor=Decimal("24"),
            can_receive=False,
        )

        service = ProductUnitConversionService(db.session)

        with pytest.raises(
            ValidationError,
            match="not receivable",
        ):
            service.resolve_for_receipt(
                tenant_id=str(tenant.id),
                product=product,
                product_unit_id=str(product_unit.id),
            )

        db.session.rollback()


def test_explicit_product_unit_is_product_scoped(app):
    with app.app_context():
        tenant = _tenant(name="Product Scope Tenant")

        each = _unit(
            tenant=tenant,
            code="EA",
            name="Each",
        )

        pack = _unit(
            tenant=tenant,
            code="PACK",
            name="Pack",
        )

        product_a = _product(
            tenant=tenant,
            unit=each,
            sku="CONVERT-A",
            name="Product A",
        )

        product_b = _product(
            tenant=tenant,
            unit=each,
            sku="CONVERT-B",
            name="Product B",
        )

        product_unit = _product_unit(
            tenant=tenant,
            product=product_a,
            unit=pack,
            factor=Decimal("10"),
        )

        service = ProductUnitConversionService(db.session)

        with pytest.raises(
            ValidationError,
            match="not found for this product",
        ):
            service.resolve_for_sale(
                tenant_id=str(tenant.id),
                product=product_b,
                product_unit_id=str(product_unit.id),
            )

        db.session.rollback()


def test_explicit_product_unit_is_tenant_scoped(app):
    with app.app_context():
        tenant_a = _tenant(name="Conversion Tenant A")
        tenant_b = _tenant(name="Conversion Tenant B")

        each = _unit(
            tenant=tenant_a,
            code="EA",
            name="Each",
        )

        pack = _unit(
            tenant=tenant_a,
            code="PACK",
            name="Pack",
        )

        product = _product(
            tenant=tenant_a,
            unit=each,
            sku="CONVERT-TENANT",
            name="Tenant Scoped Product",
        )

        product_unit = _product_unit(
            tenant=tenant_a,
            product=product,
            unit=pack,
            factor=Decimal("10"),
        )

        service = ProductUnitConversionService(db.session)

        with pytest.raises(
            ValidationError,
            match="not found for this product",
        ):
            service.resolve_for_sale(
                tenant_id=str(tenant_b.id),
                product=product,
                product_unit_id=str(product_unit.id),
            )

        db.session.rollback()


def test_inactive_product_unit_cannot_be_resolved(app):
    with app.app_context():
        tenant = _tenant(name="Inactive ProductUnit Tenant")

        each = _unit(
            tenant=tenant,
            code="EA",
            name="Each",
        )

        pack = _unit(
            tenant=tenant,
            code="PACK",
            name="Pack",
        )

        product = _product(
            tenant=tenant,
            unit=each,
            sku="CONVERT-INACTIVE",
            name="Inactive ProductUnit Product",
        )

        product_unit = _product_unit(
            tenant=tenant,
            product=product,
            unit=pack,
            factor=Decimal("10"),
            is_active=False,
        )

        service = ProductUnitConversionService(db.session)

        with pytest.raises(
            ValidationError,
            match="not found for this product",
        ):
            service.resolve_for_sale(
                tenant_id=str(tenant.id),
                product=product,
                product_unit_id=str(product_unit.id),
            )

        db.session.rollback()


def test_omitted_product_unit_uses_active_base_product_unit(app):
    with app.app_context():
        tenant = _tenant(name="Base ProductUnit Tenant")

        each = _unit(
            tenant=tenant,
            code="EA",
            name="Each",
        )

        product = _product(
            tenant=tenant,
            unit=each,
            sku="CONVERT-BASE",
            name="Base ProductUnit Product",
            default_sale_price=Decimal("95"),
            min_sale_price=Decimal("80"),
        )

        base_product_unit = _product_unit(
            tenant=tenant,
            product=product,
            unit=each,
            factor=Decimal("1"),
            is_base=True,
            sale_price=Decimal("100"),
            minimum_sale_price=Decimal("90"),
        )

        service = ProductUnitConversionService(db.session)

        resolution = service.resolve_for_sale(
            tenant_id=str(tenant.id),
            product=product,
            product_unit_id=None,
        )

        assert resolution.product_unit_id == str(
            base_product_unit.id
        )
        assert resolution.is_base is True
        assert (
            resolution.conversion_factor_to_base
            == Decimal("1.000000")
        )
        assert resolution.sale_price == Decimal("100.00")
        assert (
            resolution.minimum_sale_price
            == Decimal("90.00")
        )

        db.session.rollback()


def test_product_without_active_base_product_unit_is_rejected(app):
    with app.app_context():
        tenant = _tenant(
            name="Missing Base ProductUnit Tenant"
        )

        legacy_unit = _unit(
            tenant=tenant,
            code="LEGACY",
            name="Legacy Unit",
            base_factor=Decimal("999"),
        )

        product = _product(
            tenant=tenant,
            unit=legacy_unit,
            sku="CONVERT-NO-BASE",
            name="Product Without Base ProductUnit",
            default_sale_price=Decimal("75"),
            min_sale_price=Decimal("60"),
        )

        service = ProductUnitConversionService(db.session)

        with pytest.raises(
            ValidationError,
            match=(
                "Active base ProductUnit not found "
                "for this product."
            ),
        ):
            service.resolve_for_sale(
                tenant_id=str(tenant.id),
                product=product,
                product_unit_id=None,
            )

        db.session.rollback()


def test_product_unit_conversion_rejects_non_positive_factor(app):
    with app.app_context():
        tenant = _tenant(name="Invalid Factor Tenant")

        each = _unit(
            tenant=tenant,
            code="EA",
            name="Each",
        )

        pack = _unit(
            tenant=tenant,
            code="PACK",
            name="Pack",
        )

        product = _product(
            tenant=tenant,
            unit=each,
            sku="CONVERT-INVALID",
            name="Invalid Factor Product",
        )

        product_unit = _product_unit(
            tenant=tenant,
            product=product,
            unit=pack,
            factor=Decimal("0"),
        )

        service = ProductUnitConversionService(db.session)

        with pytest.raises(
            ValidationError,
            match="greater than zero",
        ):
            service.resolve_for_sale(
                tenant_id=str(tenant.id),
                product=product,
                product_unit_id=str(product_unit.id),
            )

        db.session.rollback()
