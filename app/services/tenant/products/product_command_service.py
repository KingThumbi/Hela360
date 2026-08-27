"""
Hela360 Product Command Service
===============================

Command boundary for tenant-owned product master-data and lifecycle operations.

Responsibilities
----------------
• Resolve products strictly within tenant scope
• Update approved product master-data fields
• Archive and restore products
• Evaluate permanent-deletion eligibility
• Permanently delete only unused archived products
• Preserve operational, financial and audit history
• Keep lifecycle transitions separate from ordinary editing

Important
---------
Transaction ownership remains with the caller. This service flushes mutations
where appropriate but does not commit them.

Structural product identity is deliberately excluded from ordinary editing.
Fields such as internal SKU, product type, inventory tracking strategy, base
unit, product codes and lifecycle state require dedicated workflows.

Permanent deletion is intentionally exceptional. A product that has entered
operational history must be archived rather than physically deleted.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import (
    DispensingRecord,
    GoodsReceiptItem,
    InventoryBatch,
    InventoryMovement,
    Product,
    ProductCode,
    ProductUnit,
    SaleItem,
    SaleRefundItem,
    StockAdjustmentItem,
    StockBalance,
    StockCountItem,
)


class ProductCommandError(Exception):
    """Base exception for product command failures."""


class ProductNotFoundError(ProductCommandError):
    """Raised when a product cannot be resolved within the tenant."""


class ProductValidationError(ProductCommandError):
    """Raised when a product command contains invalid data."""


class ProductDeletionBlockedError(ProductCommandError):
    """Raised when permanent deletion is prohibited by product state or history."""

    def __init__(
        self,
        message: str,
        *,
        blockers: tuple["ProductDeletionDependency", ...] = (),
    ):
        super().__init__(message)
        self.blockers = blockers


@dataclass(frozen=True)
class ProductLifecycleResult:
    product: Product
    changed: bool


@dataclass(frozen=True)
class ProductDeletionDependency:
    """A dependency that prevents permanent product deletion."""

    code: str
    count: int


@dataclass(frozen=True)
class ProductDeletionEligibility:
    """
    Result of evaluating whether a product may be permanently deleted.

    ``requires_archive`` distinguishes lifecycle state from historical
    dependencies. An active but otherwise unused product must first pass
    through the explicit archive workflow.
    """

    product: Product
    can_delete: bool
    requires_archive: bool
    blockers: tuple[ProductDeletionDependency, ...]


@dataclass(frozen=True)
class ProductUpdate:
    """
    Approved ordinary product master-data changes.

    ``UNSET`` semantics are handled by ProductCommandService.update(), so this
    object is intentionally not used to distinguish omitted values from null.
    It documents the supported update surface.
    """

    supplier_sku: str | None = None
    name: str | None = None
    generic_name: str | None = None
    description: str | None = None
    category_id: str | None = None
    brand_id: str | None = None
    requires_prescription: bool | None = None
    allow_negative_stock: bool | None = None
    reorder_level: Decimal | None = None
    reorder_qty: Decimal | None = None
    min_sale_price: Decimal | None = None
    default_sale_price: Decimal | None = None
    cost_price: Decimal | None = None
    tax_code: str | None = None
    pack_size: str | None = None
    manufacturer: str | None = None
    country_of_origin: str | None = None
    image_url: str | None = None


_UNSET = object()


class ProductCommandService:
    """
    Product write-side application service.

    The caller owns transaction commit/rollback.
    """

    EDITABLE_FIELDS = frozenset(
        {
            "supplier_sku",
            "name",
            "generic_name",
            "description",
            "category_id",
            "brand_id",
            "requires_prescription",
            "allow_negative_stock",
            "reorder_level",
            "reorder_qty",
            "min_sale_price",
            "default_sale_price",
            "cost_price",
            "tax_code",
            "pack_size",
            "manufacturer",
            "country_of_origin",
            "image_url",
        }
    )

    PROTECTED_FIELDS = frozenset(
        {
            "tenant_id",
            "internal_sku",
            "product_type",
            "track_inventory",
            "track_batches",
            "track_expiry",
            "unit_id",
            "unit_code",
            "unit_name",
            "codes",
            "is_active",
        }
    )

    DECIMAL_FIELDS = frozenset(
        {
            "reorder_level",
            "reorder_qty",
            "min_sale_price",
            "default_sale_price",
            "cost_price",
        }
    )

    NULLABLE_TEXT_FIELDS = frozenset(
        {
            "supplier_sku",
            "generic_name",
            "description",
            "tax_code",
            "pack_size",
            "manufacturer",
            "country_of_origin",
            "image_url",
        }
    )

    HISTORICAL_DEPENDENCIES = (
        ("inventory_batches", InventoryBatch),
        ("inventory_movements", InventoryMovement),
        ("goods_receipt_items", GoodsReceiptItem),
        ("stock_count_items", StockCountItem),
        ("stock_adjustment_items", StockAdjustmentItem),
        ("sale_items", SaleItem),
        ("dispensing_records", DispensingRecord),
        ("sale_refund_items", SaleRefundItem),
    )

    def __init__(self, session: Session):
        self.session = session

    def get_required_product(
        self,
        *,
        tenant_id: str,
        product_id: str,
    ) -> Product:
        product = (
            self.session.query(Product)
            .filter(
                Product.id == product_id,
                Product.tenant_id == tenant_id,
            )
            .one_or_none()
        )

        if product is None:
            raise ProductNotFoundError("Product not found.")

        return product

    def update(
        self,
        *,
        tenant_id: str,
        product_id: str,
        changes: dict[str, Any],
    ) -> Product:
        """
        Apply approved ordinary master-data changes.

        Lifecycle and structural identity fields are intentionally rejected.
        """

        product = self.get_required_product(
            tenant_id=tenant_id,
            product_id=product_id,
        )

        if not isinstance(changes, dict):
            raise ProductValidationError(
                "Product changes must be an object."
            )

        protected = sorted(
            field
            for field in changes
            if field in self.PROTECTED_FIELDS
        )

        if protected:
            raise ProductValidationError(
                "These product fields cannot be changed here: "
                + ", ".join(protected)
                + "."
            )

        unsupported = sorted(
            field
            for field in changes
            if field not in self.EDITABLE_FIELDS
            and field not in self.PROTECTED_FIELDS
        )

        if unsupported:
            raise ProductValidationError(
                "Unsupported product fields: "
                + ", ".join(unsupported)
                + "."
            )

        if "name" in changes:
            raw_name = changes["name"]

            if raw_name is None:
                raise ProductValidationError(
                    "Product name is required."
                )

            name = str(raw_name).strip()

            if not name:
                raise ProductValidationError(
                    "Product name is required."
                )

            product.name = name

        for field in self.NULLABLE_TEXT_FIELDS:
            if field not in changes:
                continue

            raw_value = changes[field]

            if raw_value is None:
                setattr(product, field, None)
                continue

            value = str(raw_value).strip()
            setattr(product, field, value or None)

        for field in (
            "category_id",
            "brand_id",
        ):
            if field not in changes:
                continue

            value = changes[field]

            if value is None:
                setattr(product, field, None)
                continue

            normalized = str(value).strip()
            setattr(product, field, normalized or None)

        for field in (
            "requires_prescription",
            "allow_negative_stock",
        ):
            if field not in changes:
                continue

            value = changes[field]

            if not isinstance(value, bool):
                raise ProductValidationError(
                    f"{field} must be a boolean."
                )

            setattr(product, field, value)

        for field in self.DECIMAL_FIELDS:
            if field not in changes:
                continue

            value = changes[field]

            if value is None:
                if field in {
                    "reorder_level",
                    "reorder_qty",
                }:
                    setattr(product, field, Decimal("0"))
                else:
                    setattr(product, field, None)
                continue

            try:
                decimal_value = Decimal(str(value))
            except Exception as exc:
                raise ProductValidationError(
                    f"{field} must be a valid number."
                ) from exc

            if decimal_value < 0:
                raise ProductValidationError(
                    f"{field} cannot be negative."
                )

            setattr(product, field, decimal_value)

        self.session.flush()

        return product

    def archive(
        self,
        *,
        tenant_id: str,
        product_id: str,
    ) -> ProductLifecycleResult:
        product = self.get_required_product(
            tenant_id=tenant_id,
            product_id=product_id,
        )

        if not product.is_active:
            return ProductLifecycleResult(
                product=product,
                changed=False,
            )

        product.is_active = False
        self.session.flush()

        return ProductLifecycleResult(
            product=product,
            changed=True,
        )

    def restore(
        self,
        *,
        tenant_id: str,
        product_id: str,
    ) -> ProductLifecycleResult:
        product = self.get_required_product(
            tenant_id=tenant_id,
            product_id=product_id,
        )

        if product.is_active:
            return ProductLifecycleResult(
                product=product,
                changed=False,
            )

        product.is_active = True
        self.session.flush()

        return ProductLifecycleResult(
            product=product,
            changed=True,
        )

    def get_deletion_eligibility(
        self,
        *,
        tenant_id: str,
        product_id: str,
    ) -> ProductDeletionEligibility:
        """
        Evaluate whether a product may be permanently deleted.

        Historical operational records always block deletion.

        StockBalance is treated differently because it is current-state
        projection data rather than immutable transaction history. A zero
        balance may be cleaned up during deletion; any non-zero quantity or
        reservation blocks deletion.
        """

        product = self.get_required_product(
            tenant_id=tenant_id,
            product_id=product_id,
        )

        blockers: list[ProductDeletionDependency] = []

        for code, model in self.HISTORICAL_DEPENDENCIES:
            count = (
                self.session.query(model)
                .filter(model.product_id == product.id)
                .count()
            )

            if count:
                blockers.append(
                    ProductDeletionDependency(
                        code=code,
                        count=count,
                    )
                )

        non_zero_stock_balances = (
            self.session.query(StockBalance)
            .filter(
                StockBalance.product_id == product.id,
                or_(
                    StockBalance.quantity_on_hand != 0,
                    StockBalance.quantity_reserved != 0,
                    StockBalance.quantity_available != 0,
                ),
            )
            .count()
        )

        if non_zero_stock_balances:
            blockers.append(
                ProductDeletionDependency(
                    code="non_zero_stock_balances",
                    count=non_zero_stock_balances,
                )
            )

        blockers_tuple = tuple(blockers)
        requires_archive = bool(product.is_active)

        return ProductDeletionEligibility(
            product=product,
            can_delete=not requires_archive and not blockers_tuple,
            requires_archive=requires_archive,
            blockers=blockers_tuple,
        )

    def delete_permanently(
        self,
        *,
        tenant_id: str,
        product_id: str,
    ) -> Product:
        """
        Permanently delete an unused archived product.

        Product-owned configuration records and zero stock projections are
        cleaned up explicitly. Historical records are never cascaded or
        destroyed by this operation.

        The returned Product instance is marked for deletion in the current
        SQLAlchemy unit of work. The caller still owns commit/rollback.
        """

        eligibility = self.get_deletion_eligibility(
            tenant_id=tenant_id,
            product_id=product_id,
        )

        product = eligibility.product

        if eligibility.requires_archive:
            raise ProductDeletionBlockedError(
                "Active products must be archived before permanent deletion."
            )

        if eligibility.blockers:
            blocker_codes = ", ".join(
                blocker.code
                for blocker in eligibility.blockers
            )

            raise ProductDeletionBlockedError(
                "Product cannot be permanently deleted because historical "
                f"or stock dependencies exist: {blocker_codes}.",
                blockers=eligibility.blockers,
            )

        # -------------------------------------------------------------
        # Product-owned records
        # -------------------------------------------------------------
        #
        # Use ORM-managed deletes rather than bulk Query.delete().
        # Permanent deletion is an exceptional administrative operation,
        # so identity-map correctness is more important than bulk-delete
        # throughput.
        #
        # ProductCode must be removed before ProductUnit because codes may
        # reference product_units through product_unit_id.
        # -------------------------------------------------------------

        product_codes = (
            self.session.query(ProductCode)
            .filter(
                ProductCode.tenant_id == tenant_id,
                ProductCode.product_id == product.id,
            )
            .all()
        )

        for product_code in product_codes:
            self.session.delete(product_code)

        # Flush the code removals before deleting ProductUnit records that
        # may be referenced by product_codes.product_unit_id.
        self.session.flush()

        # -------------------------------------------------------------
        # Zero current-state projections
        # -------------------------------------------------------------

        zero_stock_balances = (
            self.session.query(StockBalance)
            .filter(
                StockBalance.tenant_id == tenant_id,
                StockBalance.product_id == product.id,
                StockBalance.quantity_on_hand == 0,
                StockBalance.quantity_reserved == 0,
                StockBalance.quantity_available == 0,
            )
            .all()
        )

        for stock_balance in zero_stock_balances:
            self.session.delete(stock_balance)

        # -------------------------------------------------------------
        # Product units
        # -------------------------------------------------------------

        product_units = (
            self.session.query(ProductUnit)
            .filter(
                ProductUnit.tenant_id == tenant_id,
                ProductUnit.product_id == product.id,
            )
            .all()
        )

        for product_unit in product_units:
            self.session.delete(product_unit)

        self.session.flush()

        # -------------------------------------------------------------
        # Product
        # -------------------------------------------------------------

        self.session.delete(product)
        self.session.flush()

        return product
