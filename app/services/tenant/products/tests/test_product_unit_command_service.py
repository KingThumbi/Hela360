from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app import create_app
from app.extensions import db
from app.models import (
    Branch,
    GoodsReceipt,
    GoodsReceiptItem,
    Product,
    ProductUnit,
    Sale,
    SaleItem,
    Tenant,
    Till,
    UnitOfMeasure,
    User,
    Warehouse,
)
from app.services.tenant.products.product_unit_command_service import (
    ProductUnitCommandService,
    ProductUnitConflictError,
    ProductUnitNotFoundError,
    ProductUnitValidationError,
)


@pytest.fixture()
def app():
    app = create_app()

    app.config.update(
        TESTING=True,
    )

    return app


def _tenant(
    *,
    name: str,
) -> Tenant:
    suffix = uuid4().hex[:10]

    tenant = Tenant(
        legal_name=name,
        display_name=name,
        workspace_slug=f"pu-{suffix}",
    )

    db.session.add(tenant)
    db.session.flush()

    return tenant


def _unit(
    *,
    tenant: Tenant,
    code: str,
    name: str,
) -> UnitOfMeasure:
    unit = UnitOfMeasure(
        tenant_id=str(tenant.id),
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
        track_batches=False,
        track_expiry=False,
        requires_prescription=False,
        allow_negative_stock=False,
        reorder_level=Decimal("0"),
        reorder_qty=Decimal("0"),
        is_active=True,
    )

    db.session.add(product)
    db.session.flush()

    return product


def test_create_product_unit_persists_complete_configuration(app):
    with app.app_context():
        tenant = _tenant(
            name="ProductUnit Create Tenant"
        )

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
            sku="PU-CREATE-001",
            name="Create Test Product",
        )

        service = ProductUnitCommandService(
            db.session
        )

        created = service.create(
            tenant_id=str(tenant.id),
            product_id=str(product.id),
            unit_id=str(box.id),
            conversion_factor_to_base="10",
            can_sell=False,
            can_receive=True,
            sale_price="250.50",
            minimum_sale_price="225.00",
        )

        assert created.tenant_id == str(tenant.id)
        assert created.product_id == str(product.id)
        assert created.unit_id == str(box.id)

        assert Decimal(
            str(created.conversion_factor_to_base)
        ) == Decimal("10")

        assert created.is_base is False
        assert created.is_active is True
        assert created.can_sell is False
        assert created.can_receive is True

        assert Decimal(
            str(created.sale_price)
        ) == Decimal("250.50")

        assert Decimal(
            str(created.minimum_sale_price)
        ) == Decimal("225.00")

        db.session.rollback()


def test_create_product_unit_defaults_operational_flags(app):
    with app.app_context():
        tenant = _tenant(
            name="ProductUnit Defaults Tenant"
        )

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
            sku="PU-CREATE-002",
            name="Defaults Test Product",
        )

        service = ProductUnitCommandService(
            db.session
        )

        created = service.create(
            tenant_id=str(tenant.id),
            product_id=str(product.id),
            unit_id=str(pack.id),
            conversion_factor_to_base="5",
        )

        assert created.is_base is False
        assert created.is_active is True
        assert created.can_sell is True
        assert created.can_receive is True
        assert created.sale_price is None
        assert created.minimum_sale_price is None

        db.session.rollback()


def test_create_product_unit_rejects_duplicate_product_unit(app):
    with app.app_context():
        tenant = _tenant(
            name="ProductUnit Duplicate Tenant"
        )

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
            sku="PU-CREATE-003",
            name="Duplicate Test Product",
        )

        existing = ProductUnit(
            tenant_id=str(tenant.id),
            product_id=str(product.id),
            unit_id=str(pack.id),
            conversion_factor_to_base=Decimal("5"),
            is_base=False,
            can_sell=True,
            can_receive=True,
            is_active=True,
        )

        db.session.add(existing)
        db.session.flush()

        service = ProductUnitCommandService(
            db.session
        )

        with pytest.raises(
            ProductUnitConflictError,
            match="already configured",
        ):
            service.create(
                tenant_id=str(tenant.id),
                product_id=str(product.id),
                unit_id=str(pack.id),
                conversion_factor_to_base="5",
            )

        db.session.rollback()


@pytest.mark.parametrize(
    "factor",
    [
        "0",
        "-1",
        "not-a-number",
        None,
    ],
)
def test_create_product_unit_rejects_invalid_factor(
    app,
    factor,
):
    with app.app_context():
        tenant = _tenant(
            name=f"ProductUnit Factor {uuid4().hex[:6]}"
        )

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
            sku=f"PU-FACTOR-{uuid4().hex[:8]}",
            name="Factor Test Product",
        )

        service = ProductUnitCommandService(
            db.session
        )

        with pytest.raises(
            ProductUnitValidationError
        ):
            service.create(
                tenant_id=str(tenant.id),
                product_id=str(product.id),
                unit_id=str(pack.id),
                conversion_factor_to_base=factor,
            )

        db.session.rollback()


@pytest.mark.parametrize(
    "field,value",
    [
        ("can_sell", 1),
        ("can_sell", "true"),
        ("can_receive", 0),
        ("can_receive", "false"),
    ],
)
def test_create_product_unit_rejects_non_boolean_flags(
    app,
    field,
    value,
):
    with app.app_context():
        tenant = _tenant(
            name=f"ProductUnit Flag {uuid4().hex[:6]}"
        )

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
            sku=f"PU-FLAG-{uuid4().hex[:8]}",
            name="Flag Test Product",
        )

        kwargs = {
            "tenant_id": str(tenant.id),
            "product_id": str(product.id),
            "unit_id": str(pack.id),
            "conversion_factor_to_base": "5",
            field: value,
        }

        service = ProductUnitCommandService(
            db.session
        )

        with pytest.raises(
            ProductUnitValidationError,
            match=field,
        ):
            service.create(**kwargs)

        db.session.rollback()


@pytest.mark.parametrize(
    "field,value",
    [
        ("sale_price", "-0.01"),
        ("minimum_sale_price", "-0.01"),
        ("sale_price", "invalid"),
        ("minimum_sale_price", "invalid"),
    ],
)
def test_create_product_unit_rejects_invalid_prices(
    app,
    field,
    value,
):
    with app.app_context():
        tenant = _tenant(
            name=f"ProductUnit Price {uuid4().hex[:6]}"
        )

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
            sku=f"PU-PRICE-{uuid4().hex[:8]}",
            name="Price Validation Product",
        )

        kwargs = {
            "tenant_id": str(tenant.id),
            "product_id": str(product.id),
            "unit_id": str(pack.id),
            "conversion_factor_to_base": "5",
            field: value,
        }

        service = ProductUnitCommandService(
            db.session
        )

        with pytest.raises(
            ProductUnitValidationError,
            match=field,
        ):
            service.create(**kwargs)

        db.session.rollback()


def test_create_product_unit_rejects_minimum_price_above_sale_price(
    app,
):
    with app.app_context():
        tenant = _tenant(
            name="ProductUnit Price Floor Tenant"
        )

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
            sku="PU-PRICE-FLOOR-001",
            name="Price Floor Product",
        )

        service = ProductUnitCommandService(
            db.session
        )

        with pytest.raises(
            ProductUnitValidationError,
            match="minimum_sale_price cannot exceed sale_price",
        ):
            service.create(
                tenant_id=str(tenant.id),
                product_id=str(product.id),
                unit_id=str(pack.id),
                conversion_factor_to_base="5",
                sale_price="100",
                minimum_sale_price="101",
            )

        db.session.rollback()


def test_create_product_unit_accepts_blank_optional_prices(app):
    with app.app_context():
        tenant = _tenant(
            name="ProductUnit Blank Price Tenant"
        )

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
            sku="PU-BLANK-PRICE-001",
            name="Blank Price Product",
        )

        service = ProductUnitCommandService(
            db.session
        )

        created = service.create(
            tenant_id=str(tenant.id),
            product_id=str(product.id),
            unit_id=str(pack.id),
            conversion_factor_to_base="5",
            sale_price="",
            minimum_sale_price="",
        )

        assert created.sale_price is None
        assert created.minimum_sale_price is None

        db.session.rollback()


def test_create_product_unit_rejects_unknown_product(app):
    with app.app_context():
        tenant = _tenant(
            name="ProductUnit Missing Product Tenant"
        )

        pack = _unit(
            tenant=tenant,
            code="PACK",
            name="Pack",
        )

        service = ProductUnitCommandService(
            db.session
        )

        with pytest.raises(
            ProductUnitNotFoundError,
            match="Product not found",
        ):
            service.create(
                tenant_id=str(tenant.id),
                product_id=str(uuid4()),
                unit_id=str(pack.id),
                conversion_factor_to_base="5",
            )

        db.session.rollback()


def test_create_product_unit_rejects_unknown_uom(app):
    with app.app_context():
        tenant = _tenant(
            name="ProductUnit Missing UOM Tenant"
        )

        each = _unit(
            tenant=tenant,
            code="EA",
            name="Each",
        )

        product = _product(
            tenant=tenant,
            unit=each,
            sku="PU-MISSING-UOM-001",
            name="Missing UOM Product",
        )

        service = ProductUnitCommandService(
            db.session
        )

        with pytest.raises(
            ProductUnitNotFoundError,
            match="Unit of measure not found",
        ):
            service.create(
                tenant_id=str(tenant.id),
                product_id=str(product.id),
                unit_id=str(uuid4()),
                conversion_factor_to_base="5",
            )

        db.session.rollback()


def test_create_product_unit_enforces_tenant_boundary(app):
    with app.app_context():
        tenant_a = _tenant(
            name="ProductUnit Tenant A"
        )

        tenant_b = _tenant(
            name="ProductUnit Tenant B"
        )

        each_a = _unit(
            tenant=tenant_a,
            code="EA",
            name="Each",
        )

        pack_b = _unit(
            tenant=tenant_b,
            code="PACK",
            name="Pack",
        )

        product_a = _product(
            tenant=tenant_a,
            unit=each_a,
            sku="PU-TENANT-001",
            name="Tenant Boundary Product",
        )

        service = ProductUnitCommandService(
            db.session
        )

        with pytest.raises(
            ProductUnitNotFoundError,
            match="Unit of measure not found",
        ):
            service.create(
                tenant_id=str(tenant_a.id),
                product_id=str(product_a.id),
                unit_id=str(pack_b.id),
                conversion_factor_to_base="5",
            )

        rows = (
            db.session.query(ProductUnit)
            .filter(
                ProductUnit.product_id
                == str(product_a.id)
            )
            .all()
        )

        assert rows == []

        db.session.rollback()


def _product_unit(
    *,
    tenant: Tenant,
    product: Product,
    unit: UnitOfMeasure,
    factor: Decimal = Decimal("1"),
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


def test_update_product_unit_changes_editable_fields(app):
    with app.app_context():
        tenant = _tenant(
            name="ProductUnit Update Tenant"
        )

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
            sku="PU-UPDATE-001",
            name="Update Product",
        )

        product_unit = _product_unit(
            tenant=tenant,
            product=product,
            unit=pack,
            factor=Decimal("5"),
            sale_price=Decimal("100"),
            minimum_sale_price=Decimal("90"),
        )

        service = ProductUnitCommandService(
            db.session
        )

        updated = service.update(
            tenant_id=str(tenant.id),
            product_id=str(product.id),
            product_unit_id=str(product_unit.id),
            changes={
                "conversion_factor_to_base": "10",
                "can_sell": False,
                "can_receive": False,
                "sale_price": "250.50",
                "minimum_sale_price": "225.00",
            },
        )

        assert Decimal(
            str(updated.conversion_factor_to_base)
        ) == Decimal("10")

        assert updated.can_sell is False
        assert updated.can_receive is False

        assert Decimal(
            str(updated.sale_price)
        ) == Decimal("250.50")

        assert Decimal(
            str(updated.minimum_sale_price)
        ) == Decimal("225.00")

        db.session.rollback()


@pytest.mark.parametrize(
    "field,value",
    [
        ("tenant_id", "other-tenant"),
        ("product_id", "other-product"),
        ("unit_id", "other-unit"),
        ("unit_code", "BOX"),
        ("unit_name", "Box"),
        ("is_base", True),
        ("is_active", False),
    ],
)
def test_update_product_unit_rejects_protected_fields(
    app,
    field,
    value,
):
    with app.app_context():
        tenant = _tenant(
            name=f"PU Protected {uuid4().hex[:6]}"
        )

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
            sku=f"PU-PROTECTED-{uuid4().hex[:8]}",
            name="Protected ProductUnit",
        )

        product_unit = _product_unit(
            tenant=tenant,
            product=product,
            unit=pack,
            factor=Decimal("5"),
        )

        service = ProductUnitCommandService(
            db.session
        )

        with pytest.raises(
            ProductUnitValidationError,
            match="cannot be changed",
        ):
            service.update(
                tenant_id=str(tenant.id),
                product_id=str(product.id),
                product_unit_id=str(product_unit.id),
                changes={
                    field: value,
                },
            )

        db.session.rollback()


def test_update_product_unit_rejects_unsupported_field(app):
    with app.app_context():
        tenant = _tenant(
            name="PU Unsupported Field Tenant"
        )

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
            sku="PU-UNSUPPORTED-001",
            name="Unsupported Field Product",
        )

        product_unit = _product_unit(
            tenant=tenant,
            product=product,
            unit=pack,
            factor=Decimal("5"),
        )

        service = ProductUnitCommandService(
            db.session
        )

        with pytest.raises(
            ProductUnitValidationError,
            match="Unsupported product unit fields",
        ):
            service.update(
                tenant_id=str(tenant.id),
                product_id=str(product.id),
                product_unit_id=str(product_unit.id),
                changes={
                    "made_up_field": "value",
                },
            )

        db.session.rollback()


def test_update_base_product_unit_factor_must_remain_one(app):
    with app.app_context():
        tenant = _tenant(
            name="PU Base Factor Tenant"
        )

        each = _unit(
            tenant=tenant,
            code="EA",
            name="Each",
        )

        product = _product(
            tenant=tenant,
            unit=each,
            sku="PU-BASE-001",
            name="Base Factor Product",
        )

        product_unit = _product_unit(
            tenant=tenant,
            product=product,
            unit=each,
            factor=Decimal("1"),
            is_base=True,
        )

        service = ProductUnitCommandService(
            db.session
        )

        with pytest.raises(
            ProductUnitValidationError,
            match="must remain 1",
        ):
            service.update(
                tenant_id=str(tenant.id),
                product_id=str(product.id),
                product_unit_id=str(product_unit.id),
                changes={
                    "conversion_factor_to_base": "2",
                },
            )

        assert Decimal(
            str(product_unit.conversion_factor_to_base)
        ) == Decimal("1")

        db.session.rollback()


def test_update_non_base_factor_allowed_without_history(app):
    with app.app_context():
        tenant = _tenant(
            name="PU Factor Change Tenant"
        )

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
            sku="PU-FACTOR-CHANGE-001",
            name="Factor Change Product",
        )

        product_unit = _product_unit(
            tenant=tenant,
            product=product,
            unit=pack,
            factor=Decimal("5"),
        )

        service = ProductUnitCommandService(
            db.session
        )

        updated = service.update(
            tenant_id=str(tenant.id),
            product_id=str(product.id),
            product_unit_id=str(product_unit.id),
            changes={
                "conversion_factor_to_base": "10",
            },
        )

        assert Decimal(
            str(updated.conversion_factor_to_base)
        ) == Decimal("10")

        db.session.rollback()


@pytest.mark.parametrize(
    "field,value",
    [
        ("can_sell", 1),
        ("can_sell", "false"),
        ("can_receive", 0),
        ("can_receive", "true"),
    ],
)
def test_update_product_unit_rejects_non_boolean_flags(
    app,
    field,
    value,
):
    with app.app_context():
        tenant = _tenant(
            name=f"PU Update Flag {uuid4().hex[:6]}"
        )

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
            sku=f"PU-UP-FLAG-{uuid4().hex[:8]}",
            name="Update Flag Product",
        )

        product_unit = _product_unit(
            tenant=tenant,
            product=product,
            unit=pack,
            factor=Decimal("5"),
        )

        service = ProductUnitCommandService(
            db.session
        )

        with pytest.raises(
            ProductUnitValidationError,
            match=field,
        ):
            service.update(
                tenant_id=str(tenant.id),
                product_id=str(product.id),
                product_unit_id=str(product_unit.id),
                changes={
                    field: value,
                },
            )

        db.session.rollback()


@pytest.mark.parametrize(
    "field,value",
    [
        ("sale_price", "-0.01"),
        ("minimum_sale_price", "-0.01"),
        ("sale_price", "invalid"),
        ("minimum_sale_price", "invalid"),
    ],
)
def test_update_product_unit_rejects_invalid_prices(
    app,
    field,
    value,
):
    with app.app_context():
        tenant = _tenant(
            name=f"PU Update Price {uuid4().hex[:6]}"
        )

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
            sku=f"PU-UP-PRICE-{uuid4().hex[:8]}",
            name="Update Price Product",
        )

        product_unit = _product_unit(
            tenant=tenant,
            product=product,
            unit=pack,
            factor=Decimal("5"),
            sale_price=Decimal("100"),
            minimum_sale_price=Decimal("90"),
        )

        service = ProductUnitCommandService(
            db.session
        )

        with pytest.raises(
            ProductUnitValidationError,
            match=field,
        ):
            service.update(
                tenant_id=str(tenant.id),
                product_id=str(product.id),
                product_unit_id=str(product_unit.id),
                changes={
                    field: value,
                },
            )

        db.session.rollback()


def test_update_product_unit_rejects_price_floor_violation(app):
    with app.app_context():
        tenant = _tenant(
            name="PU Update Floor Tenant"
        )

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
            sku="PU-UP-FLOOR-001",
            name="Update Floor Product",
        )

        product_unit = _product_unit(
            tenant=tenant,
            product=product,
            unit=pack,
            factor=Decimal("5"),
            sale_price=Decimal("100"),
            minimum_sale_price=Decimal("90"),
        )

        service = ProductUnitCommandService(
            db.session
        )

        with pytest.raises(
            ProductUnitValidationError,
            match="minimum_sale_price cannot exceed sale_price",
        ):
            service.update(
                tenant_id=str(tenant.id),
                product_id=str(product.id),
                product_unit_id=str(product_unit.id),
                changes={
                    "minimum_sale_price": "101",
                },
            )

        db.session.rollback()


def test_update_product_unit_accepts_blank_optional_prices(app):
    with app.app_context():
        tenant = _tenant(
            name="PU Update Blank Price Tenant"
        )

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
            sku="PU-UP-BLANK-001",
            name="Update Blank Price Product",
        )

        product_unit = _product_unit(
            tenant=tenant,
            product=product,
            unit=pack,
            factor=Decimal("5"),
            sale_price=Decimal("100"),
            minimum_sale_price=Decimal("90"),
        )

        service = ProductUnitCommandService(
            db.session
        )

        updated = service.update(
            tenant_id=str(tenant.id),
            product_id=str(product.id),
            product_unit_id=str(product_unit.id),
            changes={
                "sale_price": "",
                "minimum_sale_price": "",
            },
        )

        assert updated.sale_price is None
        assert updated.minimum_sale_price is None

        db.session.rollback()


def test_update_product_unit_enforces_tenant_and_product_scope(app):
    with app.app_context():
        tenant_a = _tenant(
            name="PU Update Tenant A"
        )

        tenant_b = _tenant(
            name="PU Update Tenant B"
        )

        each_a = _unit(
            tenant=tenant_a,
            code="EA",
            name="Each",
        )

        pack_a = _unit(
            tenant=tenant_a,
            code="PACK",
            name="Pack",
        )

        product_a = _product(
            tenant=tenant_a,
            unit=each_a,
            sku="PU-SCOPE-A",
            name="Scope Product A",
        )

        product_unit = _product_unit(
            tenant=tenant_a,
            product=product_a,
            unit=pack_a,
            factor=Decimal("5"),
        )

        service = ProductUnitCommandService(
            db.session
        )

        with pytest.raises(
            ProductUnitNotFoundError,
            match="Product unit not found",
        ):
            service.update(
                tenant_id=str(tenant_b.id),
                product_id=str(product_a.id),
                product_unit_id=str(product_unit.id),
                changes={
                    "can_sell": False,
                },
            )

        assert product_unit.can_sell is True

        db.session.rollback()


def _user(
    *,
    tenant: Tenant,
    name: str,
) -> User:
    user = User(
        tenant_id=str(tenant.id),
        first_name=name,
        password_hash="test-password-hash",
        is_active=True,
    )

    db.session.add(user)
    db.session.flush()

    return user


def _branch_and_warehouse(
    *,
    tenant: Tenant,
) -> tuple[Branch, Warehouse]:
    suffix = uuid4().hex[:8].upper()

    branch = Branch(
        tenant_id=str(tenant.id),
        code=f"BR{suffix}",
        name=f"ProductUnit Branch {suffix}",
        is_active=True,
    )

    db.session.add(branch)
    db.session.flush()

    warehouse = Warehouse(
        tenant_id=str(tenant.id),
        branch_id=str(branch.id),
        code=f"WH{suffix}",
        name=f"ProductUnit Warehouse {suffix}",
        warehouse_type="main",
        is_active=True,
    )

    db.session.add(warehouse)
    db.session.flush()

    return branch, warehouse


def _goods_receipt_history(
    *,
    tenant: Tenant,
    branch: Branch,
    warehouse: Warehouse,
    product: Product,
    product_unit: ProductUnit,
    unit: UnitOfMeasure,
    user: User,
) -> GoodsReceiptItem:
    now = datetime.now(timezone.utc)
    suffix = uuid4().hex

    receipt = GoodsReceipt(
        tenant_id=str(tenant.id),
        branch_id=str(branch.id),
        warehouse_id=str(warehouse.id),
        supplier_id=None,
        receipt_number=f"GRN-PU-{suffix[:12]}",
        supplier_reference="PRODUCT-UNIT-HISTORY",
        idempotency_key=f"product-unit-history-{suffix}",
        request_fingerprint=(suffix * 2)[:64],
        created_by=str(user.id),
        received_at=now,
        received_by=str(user.id),
        status="received",
    )

    db.session.add(receipt)
    db.session.flush()

    item = GoodsReceiptItem(
        goods_receipt_id=str(receipt.id),
        product_id=str(product.id),
        product_unit_id=str(product_unit.id),
        batch_id=None,
        line_number=1,
        quantity=Decimal("2.0000"),
        received_quantity=Decimal("2.0000"),
        accepted_quantity=Decimal("2.0000"),
        rejected_quantity=Decimal("0.0000"),
        bonus_quantity=Decimal("0.0000"),
        base_quantity=Decimal("10.0000"),
        unit_code_snapshot=unit.code,
        unit_name_snapshot=unit.name,
        conversion_factor_to_base=(
            product_unit.conversion_factor_to_base
        ),
        batch_number="PU-HISTORY-BATCH",
        unit_cost=Decimal("25.00"),
        base_unit_cost=Decimal("5.00"),
    )

    db.session.add(item)
    db.session.flush()

    return item


def _sale_history(
    *,
    tenant: Tenant,
    branch: Branch,
    warehouse: Warehouse,
    product: Product,
    product_unit: ProductUnit,
    unit: UnitOfMeasure,
    user: User,
) -> SaleItem:
    now = datetime.now(timezone.utc)
    suffix = uuid4().hex[:10].upper()

    till = Till(
        tenant_id=str(tenant.id),
        branch_id=str(branch.id),
        warehouse_id=str(warehouse.id),
        code=f"TILL{suffix}",
        name=f"ProductUnit Till {suffix}",
        is_active=True,
    )

    db.session.add(till)
    db.session.flush()

    sale = Sale(
        tenant_id=str(tenant.id),
        branch_id=str(branch.id),
        till_id=str(till.id),
        warehouse_id=str(warehouse.id),
        customer_id=None,
        sale_number=f"SALE-PU-{suffix}",
        sale_date=now,
        sale_channel="pos",
        status="paid",
        subtotal=Decimal("100.00"),
        discount_amount=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("100.00"),
        paid_amount=Decimal("100.00"),
        balance_due=Decimal("0.00"),
        cashier_id=str(user.id),
        refunded_amount=Decimal("0.00"),
        refund_status="not_refunded",
    )

    db.session.add(sale)
    db.session.flush()

    item = SaleItem(
        sale_id=str(sale.id),
        product_id=str(product.id),
        product_unit_id=str(product_unit.id),
        batch_id=None,
        quantity=Decimal("2.0000"),
        base_quantity=Decimal("10.0000"),
        unit_price=Decimal("50.00"),
        unit_code_snapshot=unit.code,
        unit_name_snapshot=unit.name,
        conversion_factor_to_base=(
            product_unit.conversion_factor_to_base
        ),
        discount_amount=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        line_total=Decimal("100.00"),
        cost_of_sale=Decimal("60.00"),
        is_returned=False,
    )

    db.session.add(item)
    db.session.flush()

    return item


def test_update_factor_blocked_after_goods_receipt_history(app):
    with app.app_context():
        tenant = _tenant(
            name="PU Goods Receipt History Tenant"
        )

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
            sku="PU-GR-HISTORY-001",
            name="Goods Receipt History Product",
        )

        product_unit = _product_unit(
            tenant=tenant,
            product=product,
            unit=pack,
            factor=Decimal("5"),
        )

        user = _user(
            tenant=tenant,
            name="Receipt User",
        )

        branch, warehouse = _branch_and_warehouse(
            tenant=tenant
        )

        _goods_receipt_history(
            tenant=tenant,
            branch=branch,
            warehouse=warehouse,
            product=product,
            product_unit=product_unit,
            unit=pack,
            user=user,
        )

        service = ProductUnitCommandService(
            db.session
        )

        with pytest.raises(
            ProductUnitValidationError,
            match="cannot be changed",
        ):
            service.update(
                tenant_id=str(tenant.id),
                product_id=str(product.id),
                product_unit_id=str(product_unit.id),
                changes={
                    "conversion_factor_to_base": "10",
                },
            )

        assert Decimal(
            str(product_unit.conversion_factor_to_base)
        ) == Decimal("5")

        db.session.rollback()


def test_update_factor_blocked_after_sale_history(app):
    with app.app_context():
        tenant = _tenant(
            name="PU Sale History Tenant"
        )

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
            sku="PU-SALE-HISTORY-001",
            name="Sale History Product",
        )

        product_unit = _product_unit(
            tenant=tenant,
            product=product,
            unit=pack,
            factor=Decimal("5"),
        )

        user = _user(
            tenant=tenant,
            name="Sale User",
        )

        branch, warehouse = _branch_and_warehouse(
            tenant=tenant
        )

        _sale_history(
            tenant=tenant,
            branch=branch,
            warehouse=warehouse,
            product=product,
            product_unit=product_unit,
            unit=pack,
            user=user,
        )

        service = ProductUnitCommandService(
            db.session
        )

        with pytest.raises(
            ProductUnitValidationError,
            match="cannot be changed",
        ):
            service.update(
                tenant_id=str(tenant.id),
                product_id=str(product.id),
                product_unit_id=str(product_unit.id),
                changes={
                    "conversion_factor_to_base": "10",
                },
            )

        assert Decimal(
            str(product_unit.conversion_factor_to_base)
        ) == Decimal("5")

        db.session.rollback()


def test_update_same_factor_allowed_after_operational_history(app):
    with app.app_context():
        tenant = _tenant(
            name="PU Same Factor History Tenant"
        )

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
            sku="PU-SAME-HISTORY-001",
            name="Same Factor History Product",
        )

        product_unit = _product_unit(
            tenant=tenant,
            product=product,
            unit=pack,
            factor=Decimal("5"),
        )

        user = _user(
            tenant=tenant,
            name="History User",
        )

        branch, warehouse = _branch_and_warehouse(
            tenant=tenant
        )

        _goods_receipt_history(
            tenant=tenant,
            branch=branch,
            warehouse=warehouse,
            product=product,
            product_unit=product_unit,
            unit=pack,
            user=user,
        )

        service = ProductUnitCommandService(
            db.session
        )

        updated = service.update(
            tenant_id=str(tenant.id),
            product_id=str(product.id),
            product_unit_id=str(product_unit.id),
            changes={
                "conversion_factor_to_base": "5",
                "can_sell": False,
            },
        )

        assert Decimal(
            str(updated.conversion_factor_to_base)
        ) == Decimal("5")

        assert updated.can_sell is False

        db.session.rollback()


def test_archive_non_base_product_unit(app):
    with app.app_context():
        tenant = _tenant(
            name="PU Archive Tenant"
        )

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
            sku="PU-ARCHIVE-001",
            name="Archive ProductUnit Product",
        )

        product_unit = _product_unit(
            tenant=tenant,
            product=product,
            unit=pack,
            factor=Decimal("5"),
            is_active=True,
        )

        service = ProductUnitCommandService(
            db.session
        )

        result = service.archive(
            tenant_id=str(tenant.id),
            product_id=str(product.id),
            product_unit_id=str(product_unit.id),
        )

        assert result.changed is True
        assert result.product_unit.id == product_unit.id
        assert product_unit.is_active is False

        db.session.rollback()


def test_archive_product_unit_is_idempotent(app):
    with app.app_context():
        tenant = _tenant(
            name="PU Archive Idempotent Tenant"
        )

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
            sku="PU-ARCHIVE-IDEMPOTENT-001",
            name="Archive Idempotent Product",
        )

        product_unit = _product_unit(
            tenant=tenant,
            product=product,
            unit=pack,
            factor=Decimal("5"),
            is_active=False,
        )

        service = ProductUnitCommandService(
            db.session
        )

        result = service.archive(
            tenant_id=str(tenant.id),
            product_id=str(product.id),
            product_unit_id=str(product_unit.id),
        )

        assert result.changed is False
        assert result.product_unit.id == product_unit.id
        assert product_unit.is_active is False

        db.session.rollback()


def test_archive_rejects_base_product_unit(app):
    with app.app_context():
        tenant = _tenant(
            name="PU Base Archive Tenant"
        )

        each = _unit(
            tenant=tenant,
            code="EA",
            name="Each",
        )

        product = _product(
            tenant=tenant,
            unit=each,
            sku="PU-BASE-ARCHIVE-001",
            name="Base Archive Product",
        )

        product_unit = _product_unit(
            tenant=tenant,
            product=product,
            unit=each,
            factor=Decimal("1"),
            is_base=True,
            is_active=True,
        )

        service = ProductUnitCommandService(
            db.session
        )

        with pytest.raises(
            ProductUnitValidationError,
            match="base product unit cannot be archived",
        ):
            service.archive(
                tenant_id=str(tenant.id),
                product_id=str(product.id),
                product_unit_id=str(product_unit.id),
            )

        assert product_unit.is_active is True

        db.session.rollback()


def test_restore_archived_product_unit(app):
    with app.app_context():
        tenant = _tenant(
            name="PU Restore Tenant"
        )

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
            sku="PU-RESTORE-001",
            name="Restore ProductUnit Product",
        )

        product_unit = _product_unit(
            tenant=tenant,
            product=product,
            unit=pack,
            factor=Decimal("5"),
            is_active=False,
        )

        service = ProductUnitCommandService(
            db.session
        )

        result = service.restore(
            tenant_id=str(tenant.id),
            product_id=str(product.id),
            product_unit_id=str(product_unit.id),
        )

        assert result.changed is True
        assert result.product_unit.id == product_unit.id
        assert product_unit.is_active is True

        db.session.rollback()


def test_restore_product_unit_is_idempotent(app):
    with app.app_context():
        tenant = _tenant(
            name="PU Restore Idempotent Tenant"
        )

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
            sku="PU-RESTORE-IDEMPOTENT-001",
            name="Restore Idempotent Product",
        )

        product_unit = _product_unit(
            tenant=tenant,
            product=product,
            unit=pack,
            factor=Decimal("5"),
            is_active=True,
        )

        service = ProductUnitCommandService(
            db.session
        )

        result = service.restore(
            tenant_id=str(tenant.id),
            product_id=str(product.id),
            product_unit_id=str(product_unit.id),
        )

        assert result.changed is False
        assert result.product_unit.id == product_unit.id
        assert product_unit.is_active is True

        db.session.rollback()


def test_archive_and_restore_preserve_historical_product_unit_identity(app):
    with app.app_context():
        tenant = _tenant(
            name="PU Historical Lifecycle Tenant"
        )

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
            sku="PU-HIST-LIFECYCLE-001",
            name="Historical Lifecycle Product",
        )

        product_unit = _product_unit(
            tenant=tenant,
            product=product,
            unit=pack,
            factor=Decimal("5"),
        )

        user = _user(
            tenant=tenant,
            name="Historical Lifecycle User",
        )

        branch, warehouse = _branch_and_warehouse(
            tenant=tenant
        )

        item = _goods_receipt_history(
            tenant=tenant,
            branch=branch,
            warehouse=warehouse,
            product=product,
            product_unit=product_unit,
            unit=pack,
            user=user,
        )

        original_id = str(product_unit.id)
        original_unit_id = str(product_unit.unit_id)
        original_factor = Decimal(
            str(product_unit.conversion_factor_to_base)
        )

        service = ProductUnitCommandService(
            db.session
        )

        archived = service.archive(
            tenant_id=str(tenant.id),
            product_id=str(product.id),
            product_unit_id=str(product_unit.id),
        )

        assert archived.changed is True
        assert product_unit.is_active is False

        assert str(product_unit.id) == original_id
        assert str(product_unit.unit_id) == original_unit_id
        assert Decimal(
            str(product_unit.conversion_factor_to_base)
        ) == original_factor

        assert str(item.product_unit_id) == original_id

        restored = service.restore(
            tenant_id=str(tenant.id),
            product_id=str(product.id),
            product_unit_id=str(product_unit.id),
        )

        assert restored.changed is True
        assert product_unit.is_active is True

        assert str(product_unit.id) == original_id
        assert str(product_unit.unit_id) == original_unit_id
        assert Decimal(
            str(product_unit.conversion_factor_to_base)
        ) == original_factor

        assert str(item.product_unit_id) == original_id

        db.session.rollback()


def test_archive_product_unit_enforces_tenant_scope(app):
    with app.app_context():
        tenant_a = _tenant(
            name="PU Archive Tenant A"
        )

        tenant_b = _tenant(
            name="PU Archive Tenant B"
        )

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
            sku="PU-ARCHIVE-SCOPE-001",
            name="Archive Scope Product",
        )

        product_unit = _product_unit(
            tenant=tenant_a,
            product=product,
            unit=pack,
            factor=Decimal("5"),
        )

        service = ProductUnitCommandService(
            db.session
        )

        with pytest.raises(
            ProductUnitNotFoundError,
            match="Product unit not found",
        ):
            service.archive(
                tenant_id=str(tenant_b.id),
                product_id=str(product.id),
                product_unit_id=str(product_unit.id),
            )

        assert product_unit.is_active is True

        db.session.rollback()
