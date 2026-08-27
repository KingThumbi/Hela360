from __future__ import annotations

from decimal import Decimal

import pytest

from app import create_app
from app.extensions import db
from app.models import (
    Product,
    ProductUnit,
    Tenant,
    UnitOfMeasure,
)
from app.services.tenant.products import (
    ProductCommandService,
    ProductNotFoundError,
    ProductValidationError,
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
    workspace_slug: str,
) -> Tenant:
    tenant = Tenant(
        legal_name=name,
        display_name=name,
        workspace_slug=workspace_slug,
    )

    db.session.add(tenant)
    db.session.flush()

    return tenant


def _product(
    *,
    tenant_id: str,
    sku: str,
    name: str,
    is_active: bool = True,
) -> Product:
    product = Product(
        tenant_id=tenant_id,
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
        is_active=is_active,
    )

    db.session.add(product)
    db.session.flush()

    return product


def test_archive_product_is_idempotent(app):
    with app.app_context():
        tenant = _tenant(
            name="Product Lifecycle Tenant",
            workspace_slug="product-lifecycle",
        )

        product = _product(
            tenant_id=tenant.id,
            sku="SKU-001",
            name="Archive Test Product",
        )

        service = ProductCommandService(
            db.session
        )

        first = service.archive(
            tenant_id=str(tenant.id),
            product_id=str(product.id),
        )

        assert first.changed is True
        assert first.product.is_active is False

        second = service.archive(
            tenant_id=str(tenant.id),
            product_id=str(product.id),
        )

        assert second.changed is False
        assert second.product.is_active is False

        db.session.rollback()


def test_restore_product_is_idempotent(app):
    with app.app_context():
        tenant = _tenant(
            name="Restore Lifecycle Tenant",
            workspace_slug="restore-lifecycle",
        )

        product = _product(
            tenant_id=tenant.id,
            sku="SKU-002",
            name="Restore Test Product",
            is_active=False,
        )

        service = ProductCommandService(
            db.session
        )

        first = service.restore(
            tenant_id=str(tenant.id),
            product_id=str(product.id),
        )

        assert first.changed is True
        assert first.product.is_active is True

        second = service.restore(
            tenant_id=str(tenant.id),
            product_id=str(product.id),
        )

        assert second.changed is False
        assert second.product.is_active is True

        db.session.rollback()


def test_product_lifecycle_preserves_product_unit_state(app):
    with app.app_context():
        tenant = _tenant(
            name="Product Unit Lifecycle Tenant",
            workspace_slug="product-unit-lifecycle",
        )

        unit = UnitOfMeasure(
            tenant_id=tenant.id,
            code="EA",
            name="Each",
            base_factor=Decimal("1"),
        )

        db.session.add(unit)
        db.session.flush()

        product = _product(
            tenant_id=tenant.id,
            sku="SKU-003",
            name="Unit Preservation Product",
        )

        product_unit = ProductUnit(
            tenant_id=tenant.id,
            product_id=product.id,
            unit_id=unit.id,
            conversion_factor_to_base=Decimal("1"),
            is_base=True,
            can_sell=True,
            can_receive=True,
            is_active=True,
        )

        db.session.add(product_unit)
        db.session.flush()

        service = ProductCommandService(
            db.session
        )

        service.archive(
            tenant_id=str(tenant.id),
            product_id=str(product.id),
        )

        assert product.is_active is False
        assert product_unit.is_active is True

        service.restore(
            tenant_id=str(tenant.id),
            product_id=str(product.id),
        )

        assert product.is_active is True
        assert product_unit.is_active is True

        db.session.rollback()


def test_product_cannot_cross_tenant_boundary(app):
    with app.app_context():
        tenant_a = _tenant(
            name="Tenant A",
            workspace_slug="tenant-a-products",
        )

        tenant_b = _tenant(
            name="Tenant B",
            workspace_slug="tenant-b-products",
        )

        product = _product(
            tenant_id=tenant_a.id,
            sku="SKU-004",
            name="Tenant A Product",
        )

        service = ProductCommandService(
            db.session
        )

        with pytest.raises(
            ProductNotFoundError,
            match="Product not found",
        ):
            service.archive(
                tenant_id=str(tenant_b.id),
                product_id=str(product.id),
            )

        assert product.is_active is True

        db.session.rollback()


def test_update_product_changes_approved_master_data(app):
    with app.app_context():
        tenant = _tenant(
            name="Product Edit Tenant",
            workspace_slug="product-edit",
        )

        product = Product(
            tenant_id=tenant.id,
            internal_sku="EDIT-001",
            name="Old Product Name",
            supplier_sku="OLD-SUPPLIER",
            default_sale_price=Decimal("100.00"),
            cost_price=Decimal("70.00"),
            reorder_level=Decimal("2.0000"),
            reorder_qty=Decimal("5.0000"),
            requires_prescription=False,
            allow_negative_stock=False,
            is_active=True,
        )

        db.session.add(product)
        db.session.flush()

        service = ProductCommandService(
            db.session
        )

        updated = service.update(
            tenant_id=str(tenant.id),
            product_id=str(product.id),
            changes={
                "name": "Updated Product Name",
                "supplier_sku": "SUPPLIER-002",
                "default_sale_price": "125.50",
                "cost_price": "80.25",
                "reorder_level": "4",
                "reorder_qty": "12",
                "requires_prescription": True,
                "allow_negative_stock": True,
                "manufacturer": "Example Manufacturer",
            },
        )

        assert updated.id == product.id
        assert updated.name == "Updated Product Name"
        assert updated.supplier_sku == "SUPPLIER-002"
        assert updated.default_sale_price == Decimal("125.50")
        assert updated.cost_price == Decimal("80.25")
        assert updated.reorder_level == Decimal("4")
        assert updated.reorder_qty == Decimal("12")
        assert updated.requires_prescription is True
        assert updated.allow_negative_stock is True
        assert updated.manufacturer == "Example Manufacturer"
        assert updated.is_active is True

        db.session.rollback()


@pytest.mark.parametrize(
    "field,value",
    [
        ("internal_sku", "CHANGED-SKU"),
        ("product_type", "service"),
        ("track_inventory", False),
        ("track_batches", True),
        ("track_expiry", True),
        ("unit_id", "another-unit"),
        ("codes", []),
        ("is_active", False),
    ],
)
def test_update_product_rejects_structural_and_lifecycle_fields(
    app,
    field,
    value,
):
    with app.app_context():
        tenant = _tenant(
            name=f"Protected Field {field}",
            workspace_slug=(
                "protected-"
                + field.replace("_", "-")
            ),
        )

        product = Product(
            tenant_id=tenant.id,
            internal_sku=f"PROTECTED-{field}",
            name="Protected Product",
            is_active=True,
        )

        db.session.add(product)
        db.session.flush()

        service = ProductCommandService(
            db.session
        )

        with pytest.raises(
            ProductValidationError
        ):
            service.update(
                tenant_id=str(tenant.id),
                product_id=str(product.id),
                changes={
                    field: value,
                },
            )

        db.session.rollback()


def test_update_product_rejects_negative_commercial_values(app):
    with app.app_context():
        tenant = _tenant(
            name="Negative Product Value Tenant",
            workspace_slug="negative-product-value",
        )

        product = Product(
            tenant_id=tenant.id,
            internal_sku="NEGATIVE-001",
            name="Negative Test Product",
            is_active=True,
        )

        db.session.add(product)
        db.session.flush()

        service = ProductCommandService(
            db.session
        )

        with pytest.raises(
            ProductValidationError
        ):
            service.update(
                tenant_id=str(tenant.id),
                product_id=str(product.id),
                changes={
                    "default_sale_price": "-1",
                },
            )

        db.session.rollback()


def test_update_product_cannot_cross_tenant_boundary(app):
    with app.app_context():
        tenant_a = _tenant(
            name="Product Edit Tenant A",
            workspace_slug="product-edit-a",
        )

        tenant_b = _tenant(
            name="Product Edit Tenant B",
            workspace_slug="product-edit-b",
        )

        product = Product(
            tenant_id=tenant_a.id,
            internal_sku="CROSS-TENANT-EDIT",
            name="Tenant A Product",
            is_active=True,
        )

        db.session.add(product)
        db.session.flush()

        service = ProductCommandService(
            db.session
        )

        with pytest.raises(
            ProductNotFoundError
        ):
            service.update(
                tenant_id=str(tenant_b.id),
                product_id=str(product.id),
                changes={
                    "name": "Illegal Change",
                },
            )

        assert product.name == "Tenant A Product"

        db.session.rollback()
