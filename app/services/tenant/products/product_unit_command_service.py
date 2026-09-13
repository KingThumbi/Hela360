"""
Hela360 Product Unit Command Service
====================================

Write-side application service for tenant-owned ProductUnit configuration.

ProductUnit defines how a reusable UnitOfMeasure applies to one specific
product, for example:

    Tablet  x1
    Strip   x10
    Box     x100

The Product base unit remains structural product identity. This service
manages additional receiving/selling representations without allowing an
ordinary edit to redefine the canonical inventory base unit.

Transaction ownership remains with the caller.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy.orm import Session

from app.models import (
    GoodsReceiptItem,
    Product,
    ProductUnit,
    SaleItem,
    UnitOfMeasure,
)


class ProductUnitCommandError(Exception):
    """Base exception for ProductUnit command failures."""


class ProductUnitNotFoundError(ProductUnitCommandError):
    """Raised when the product or ProductUnit cannot be resolved."""


class ProductUnitValidationError(ProductUnitCommandError):
    """Raised when ProductUnit configuration is invalid."""


class ProductUnitConflictError(ProductUnitCommandError):
    """Raised when the requested ProductUnit already exists."""


@dataclass(frozen=True)
class ProductUnitLifecycleResult:
    product_unit: ProductUnit
    changed: bool


_UNSET = object()


class ProductUnitCommandService:
    """
    Tenant-scoped ProductUnit write boundary.

    This service intentionally does NOT support changing:
    - tenant ownership
    - product ownership
    - unit identity after creation
    - base-unit identity
    """

    EDITABLE_FIELDS = frozenset(
        {
            "conversion_factor_to_base",
            "can_sell",
            "can_receive",
            "sale_price",
            "minimum_sale_price",
        }
    )

    PROTECTED_FIELDS = frozenset(
        {
            "tenant_id",
            "product_id",
            "unit_id",
            "unit_code",
            "unit_name",
            "is_base",
            "is_active",
        }
    )

    def __init__(self, session: Session):
        self.session = session

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

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
            raise ProductUnitNotFoundError(
                "Product not found."
            )

        return product

    def get_required_unit_of_measure(
        self,
        *,
        tenant_id: str,
        unit_id: str,
    ) -> UnitOfMeasure:
        unit = (
            self.session.query(UnitOfMeasure)
            .filter(
                UnitOfMeasure.id == unit_id,
                UnitOfMeasure.tenant_id == tenant_id,
            )
            .one_or_none()
        )

        if unit is None:
            raise ProductUnitNotFoundError(
                "Unit of measure not found."
            )

        return unit

    def get_required_product_unit(
        self,
        *,
        tenant_id: str,
        product_id: str,
        product_unit_id: str,
    ) -> ProductUnit:
        product_unit = (
            self.session.query(ProductUnit)
            .filter(
                ProductUnit.id == product_unit_id,
                ProductUnit.tenant_id == tenant_id,
                ProductUnit.product_id == product_id,
            )
            .one_or_none()
        )

        if product_unit is None:
            raise ProductUnitNotFoundError(
                "Product unit not found."
            )

        return product_unit

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create(
        self,
        *,
        tenant_id: str,
        product_id: str,
        unit_id: str,
        conversion_factor_to_base: Any,
        can_sell: bool = True,
        can_receive: bool = True,
        sale_price: Any = None,
        minimum_sale_price: Any = None,
    ) -> ProductUnit:
        self.get_required_product(
            tenant_id=tenant_id,
            product_id=product_id,
        )

        self.get_required_unit_of_measure(
            tenant_id=tenant_id,
            unit_id=unit_id,
        )

        existing = (
            self.session.query(ProductUnit)
            .filter(
                ProductUnit.tenant_id == tenant_id,
                ProductUnit.product_id == product_id,
                ProductUnit.unit_id == unit_id,
            )
            .one_or_none()
        )

        if existing is not None:
            raise ProductUnitConflictError(
                "This unit is already configured for the product."
            )

        factor = self._positive_decimal(
            conversion_factor_to_base,
            "conversion_factor_to_base",
        )

        sale_price_value = self._nullable_non_negative_decimal(
            sale_price,
            "sale_price",
        )

        minimum_sale_price_value = (
            self._nullable_non_negative_decimal(
                minimum_sale_price,
                "minimum_sale_price",
            )
        )

        self._validate_price_floor(
            sale_price=sale_price_value,
            minimum_sale_price=minimum_sale_price_value,
        )

        if not isinstance(can_sell, bool):
            raise ProductUnitValidationError(
                "can_sell must be a boolean."
            )

        if not isinstance(can_receive, bool):
            raise ProductUnitValidationError(
                "can_receive must be a boolean."
            )

        product_unit = ProductUnit(
            tenant_id=tenant_id,
            product_id=product_id,
            unit_id=unit_id,
            conversion_factor_to_base=factor,
            is_base=False,
            can_sell=can_sell,
            can_receive=can_receive,
            sale_price=sale_price_value,
            minimum_sale_price=minimum_sale_price_value,
            is_active=True,
        )

        self.session.add(product_unit)
        self.session.flush()

        return product_unit

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(
        self,
        *,
        tenant_id: str,
        product_id: str,
        product_unit_id: str,
        changes: dict[str, Any],
    ) -> ProductUnit:
        product_unit = self.get_required_product_unit(
            tenant_id=tenant_id,
            product_id=product_id,
            product_unit_id=product_unit_id,
        )

        if not isinstance(changes, dict):
            raise ProductUnitValidationError(
                "Product unit changes must be an object."
            )

        protected = sorted(
            field
            for field in changes
            if field in self.PROTECTED_FIELDS
        )

        if protected:
            raise ProductUnitValidationError(
                "These product unit fields cannot be changed here: "
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
            raise ProductUnitValidationError(
                "Unsupported product unit fields: "
                + ", ".join(unsupported)
                + "."
            )

        if "conversion_factor_to_base" in changes:
            proposed_factor = self._positive_decimal(
                changes["conversion_factor_to_base"],
                "conversion_factor_to_base",
            )

            if (
                product_unit.is_base
                and proposed_factor != Decimal("1")
            ):
                raise ProductUnitValidationError(
                    "The base product unit conversion factor must remain 1."
                )

            current_factor = Decimal(
                str(product_unit.conversion_factor_to_base)
            )

            if (
                proposed_factor != current_factor
                and self._has_operational_history(
                    product_unit_id=str(product_unit.id),
                )
            ):
                raise ProductUnitValidationError(
                    "conversion_factor_to_base cannot be changed "
                    "after the product unit has been used in a "
                    "goods receipt or sale."
                )

            product_unit.conversion_factor_to_base = (
                proposed_factor
            )

        for field in (
            "can_sell",
            "can_receive",
        ):
            if field not in changes:
                continue

            value = changes[field]

            if not isinstance(value, bool):
                raise ProductUnitValidationError(
                    f"{field} must be a boolean."
                )

            setattr(product_unit, field, value)

        if "sale_price" in changes:
            product_unit.sale_price = (
                self._nullable_non_negative_decimal(
                    changes["sale_price"],
                    "sale_price",
                )
            )

        if "minimum_sale_price" in changes:
            product_unit.minimum_sale_price = (
                self._nullable_non_negative_decimal(
                    changes["minimum_sale_price"],
                    "minimum_sale_price",
                )
            )

        self._validate_price_floor(
            sale_price=product_unit.sale_price,
            minimum_sale_price=(
                product_unit.minimum_sale_price
            ),
        )

        self.session.flush()

        return product_unit

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def archive(
        self,
        *,
        tenant_id: str,
        product_id: str,
        product_unit_id: str,
    ) -> ProductUnitLifecycleResult:
        product_unit = self.get_required_product_unit(
            tenant_id=tenant_id,
            product_id=product_id,
            product_unit_id=product_unit_id,
        )

        if product_unit.is_base:
            raise ProductUnitValidationError(
                "The base product unit cannot be archived."
            )

        if not product_unit.is_active:
            return ProductUnitLifecycleResult(
                product_unit=product_unit,
                changed=False,
            )

        product_unit.is_active = False
        self.session.flush()

        return ProductUnitLifecycleResult(
            product_unit=product_unit,
            changed=True,
        )

    def restore(
        self,
        *,
        tenant_id: str,
        product_id: str,
        product_unit_id: str,
    ) -> ProductUnitLifecycleResult:
        product_unit = self.get_required_product_unit(
            tenant_id=tenant_id,
            product_id=product_id,
            product_unit_id=product_unit_id,
        )

        if product_unit.is_active:
            return ProductUnitLifecycleResult(
                product_unit=product_unit,
                changed=False,
            )

        product_unit.is_active = True
        self.session.flush()

        return ProductUnitLifecycleResult(
            product_unit=product_unit,
            changed=True,
        )

    # ------------------------------------------------------------------
    # Historical integrity
    # ------------------------------------------------------------------

    def _has_operational_history(
        self,
        *,
        product_unit_id: str,
    ) -> bool:
        """
        Return True once a ProductUnit has participated in
        stock-bearing or sale history.

        ProductCode references are intentionally excluded because
        assigning a barcode/code is identifier configuration rather
        than transactional evidence.
        """
        goods_receipt_usage = (
            self.session.query(GoodsReceiptItem.id)
            .filter(
                GoodsReceiptItem.product_unit_id
                == product_unit_id
            )
            .first()
        )

        if goods_receipt_usage is not None:
            return True

        sale_usage = (
            self.session.query(SaleItem.id)
            .filter(
                SaleItem.product_unit_id
                == product_unit_id
            )
            .first()
        )

        return sale_usage is not None

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def _positive_decimal(
        value: Any,
        field_name: str,
    ) -> Decimal:
        try:
            decimal_value = Decimal(str(value))
        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ) as exc:
            raise ProductUnitValidationError(
                f"{field_name} must be a valid number."
            ) from exc

        if decimal_value <= 0:
            raise ProductUnitValidationError(
                f"{field_name} must be greater than zero."
            )

        return decimal_value

    @staticmethod
    def _nullable_non_negative_decimal(
        value: Any,
        field_name: str,
    ) -> Decimal | None:
        if value in (
            None,
            "",
        ):
            return None

        try:
            decimal_value = Decimal(str(value))
        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ) as exc:
            raise ProductUnitValidationError(
                f"{field_name} must be a valid number."
            ) from exc

        if decimal_value < 0:
            raise ProductUnitValidationError(
                f"{field_name} cannot be negative."
            )

        return decimal_value

    @staticmethod
    def _validate_price_floor(
        *,
        sale_price: Decimal | None,
        minimum_sale_price: Decimal | None,
    ) -> None:
        if (
            sale_price is not None
            and minimum_sale_price is not None
            and minimum_sale_price > sale_price
        ):
            raise ProductUnitValidationError(
                "minimum_sale_price cannot exceed sale_price."
            )
