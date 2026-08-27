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
    ProductDeletionBlockedError,
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


# ============================================================================
# Permanent deletion policy
# ============================================================================


def test_active_unused_product_requires_archive_before_deletion(app):
    with app.app_context():
        tenant = _tenant(
            name="Delete Active Tenant",
            workspace_slug="delete-active",
        )

        product = _product(
            tenant_id=tenant.id,
            sku="DELETE-ACTIVE-001",
            name="Active Product",
        )

        service = ProductCommandService(db.session)

        eligibility = service.get_deletion_eligibility(
            tenant_id=str(tenant.id),
            product_id=str(product.id),
        )

        assert eligibility.can_delete is False
        assert eligibility.requires_archive is True
        assert eligibility.blockers == ()

        with pytest.raises(
            ProductDeletionBlockedError,
            match="must be archived",
        ):
            service.delete_permanently(
                tenant_id=str(tenant.id),
                product_id=str(product.id),
            )

        assert (
            db.session.get(Product, product.id)
            is not None
        )

        db.session.rollback()


def test_archived_unused_product_is_deletion_eligible(app):
    with app.app_context():
        tenant = _tenant(
            name="Delete Eligible Tenant",
            workspace_slug="delete-eligible",
        )

        product = _product(
            tenant_id=tenant.id,
            sku="DELETE-ELIGIBLE-001",
            name="Archived Product",
        )
        product.is_active = False
        db.session.flush()

        service = ProductCommandService(db.session)

        eligibility = service.get_deletion_eligibility(
            tenant_id=str(tenant.id),
            product_id=str(product.id),
        )

        assert eligibility.can_delete is True
        assert eligibility.requires_archive is False
        assert eligibility.blockers == ()

        db.session.rollback()


def test_permanent_delete_removes_owned_product_records(app):
    from app.models import ProductCode

    with app.app_context():
        tenant = _tenant(
            name="Delete Owned Records Tenant",
            workspace_slug="delete-owned-records",
        )

        unit = UnitOfMeasure(
            tenant_id=tenant.id,
            code="TAB",
            name="Tablet",
            base_factor=Decimal("1"),
        )
        db.session.add(unit)
        db.session.flush()

        product = _product(
            tenant_id=tenant.id,
            sku="DELETE-OWNED-001",
            name="Owned Record Product",
        )
        product.is_active = False
        db.session.flush()

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

        product_code = ProductCode(
            tenant_id=tenant.id,
            product_id=product.id,
            product_unit_id=product_unit.id,
            code_type="barcode",
            code_value="DELETE-OWNED-BARCODE",
            is_primary=True,
            generated_by_system=False,
        )
        db.session.add(product_code)
        db.session.flush()

        product_id = product.id
        product_unit_id = product_unit.id
        product_code_id = product_code.id

        service = ProductCommandService(db.session)

        deleted = service.delete_permanently(
            tenant_id=str(tenant.id),
            product_id=str(product.id),
        )

        assert deleted.id == product_id
        assert db.session.get(Product, product_id) is None
        assert db.session.get(
            ProductUnit,
            product_unit_id,
        ) is None
        assert db.session.get(
            ProductCode,
            product_code_id,
        ) is None

        db.session.rollback()


def test_zero_stock_balance_is_cleaned_during_permanent_delete(app):
    from app.models import Branch, StockBalance, Warehouse

    with app.app_context():
        tenant = _tenant(
            name="Delete Zero Balance Tenant",
            workspace_slug="delete-zero-balance",
        )

        branch = Branch(
            tenant_id=tenant.id,
            code="MAIN",
            name="Main",
            is_head_office=True,
            is_active=True,
        )
        db.session.add(branch)
        db.session.flush()

        warehouse = Warehouse(
            tenant_id=tenant.id,
            branch_id=branch.id,
            code="WH-1",
            name="Warehouse",
            warehouse_type="main",
            is_active=True,
        )
        db.session.add(warehouse)
        db.session.flush()

        product = _product(
            tenant_id=tenant.id,
            sku="DELETE-ZERO-001",
            name="Zero Balance Product",
        )
        product.is_active = False
        db.session.flush()

        balance = StockBalance(
            tenant_id=tenant.id,
            branch_id=branch.id,
            warehouse_id=warehouse.id,
            product_id=product.id,
            quantity_on_hand=Decimal("0"),
            quantity_reserved=Decimal("0"),
            quantity_available=Decimal("0"),
            avg_unit_cost=Decimal("0"),
        )
        db.session.add(balance)
        db.session.flush()

        balance_id = balance.id
        product_id = product.id

        service = ProductCommandService(db.session)

        eligibility = service.get_deletion_eligibility(
            tenant_id=str(tenant.id),
            product_id=str(product.id),
        )

        assert eligibility.can_delete is True

        service.delete_permanently(
            tenant_id=str(tenant.id),
            product_id=str(product.id),
        )

        assert db.session.get(Product, product_id) is None
        assert db.session.get(
            StockBalance,
            balance_id,
        ) is None

        db.session.rollback()


@pytest.mark.parametrize(
    (
        "quantity_on_hand",
        "quantity_reserved",
        "quantity_available",
    ),
    [
        ("1", "0", "1"),
        ("0", "1", "0"),
        ("0", "0", "1"),
    ],
)
def test_non_zero_stock_balance_blocks_permanent_delete(
    app,
    quantity_on_hand,
    quantity_reserved,
    quantity_available,
):
    from app.models import Branch, StockBalance, Warehouse

    with app.app_context():
        tenant = _tenant(
            name="Delete Stock Block Tenant",
            workspace_slug=(
                "delete-stock-block-"
                f"{quantity_on_hand}-"
                f"{quantity_reserved}-"
                f"{quantity_available}"
            ).replace(".", "-"),
        )

        branch = Branch(
            tenant_id=tenant.id,
            code="MAIN",
            name="Main",
            is_head_office=True,
            is_active=True,
        )
        db.session.add(branch)
        db.session.flush()

        warehouse = Warehouse(
            tenant_id=tenant.id,
            branch_id=branch.id,
            code="WH-1",
            name="Warehouse",
            warehouse_type="main",
            is_active=True,
        )
        db.session.add(warehouse)
        db.session.flush()

        product = _product(
            tenant_id=tenant.id,
            sku="DELETE-STOCK-001",
            name="Stocked Product",
        )
        product.is_active = False
        db.session.flush()

        db.session.add(
            StockBalance(
                tenant_id=tenant.id,
                branch_id=branch.id,
                warehouse_id=warehouse.id,
                product_id=product.id,
                quantity_on_hand=Decimal(
                    quantity_on_hand
                ),
                quantity_reserved=Decimal(
                    quantity_reserved
                ),
                quantity_available=Decimal(
                    quantity_available
                ),
                avg_unit_cost=Decimal("0"),
            )
        )
        db.session.flush()

        service = ProductCommandService(db.session)

        eligibility = service.get_deletion_eligibility(
            tenant_id=str(tenant.id),
            product_id=str(product.id),
        )

        assert eligibility.can_delete is False
        assert eligibility.requires_archive is False
        assert (
            eligibility.blockers[0].code
            == "non_zero_stock_balances"
        )
        assert eligibility.blockers[0].count == 1

        with pytest.raises(
            ProductDeletionBlockedError
        ) as exc_info:
            service.delete_permanently(
                tenant_id=str(tenant.id),
                product_id=str(product.id),
            )

        assert (
            exc_info.value.blockers[0].code
            == "non_zero_stock_balances"
        )

        assert (
            db.session.get(Product, product.id)
            is not None
        )

        db.session.rollback()


def test_deletion_eligibility_cannot_cross_tenant_boundary(app):
    with app.app_context():
        tenant_a = _tenant(
            name="Delete Tenant A",
            workspace_slug="delete-tenant-a",
        )
        tenant_b = _tenant(
            name="Delete Tenant B",
            workspace_slug="delete-tenant-b",
        )

        product = _product(
            tenant_id=tenant_a.id,
            sku="DELETE-TENANT-001",
            name="Tenant A Product",
        )
        product.is_active = False
        db.session.flush()

        service = ProductCommandService(db.session)

        with pytest.raises(
            ProductNotFoundError,
            match="Product not found",
        ):
            service.get_deletion_eligibility(
                tenant_id=str(tenant_b.id),
                product_id=str(product.id),
            )

        with pytest.raises(
            ProductNotFoundError,
            match="Product not found",
        ):
            service.delete_permanently(
                tenant_id=str(tenant_b.id),
                product_id=str(product.id),
            )

        assert (
            db.session.get(Product, product.id)
            is not None
        )

        db.session.rollback()
