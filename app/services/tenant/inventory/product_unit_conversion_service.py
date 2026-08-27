from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from app.errors import ValidationError
from app.models import Product, ProductUnit, UnitOfMeasure


FOURPLACES = Decimal("0.0001")
SIXPLACES = Decimal("0.000001")
TWOPLACES = Decimal("0.01")


def _d(value) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _q4(value) -> Decimal:
    return _d(value).quantize(FOURPLACES, rounding=ROUND_HALF_UP)


def _q6(value) -> Decimal:
    return _d(value).quantize(SIXPLACES, rounding=ROUND_HALF_UP)


def _q2(value) -> Decimal:
    return _d(value).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


@dataclass(frozen=True, slots=True)
class ProductUnitResolution:
    product_unit_id: str | None
    unit_id: str | None
    unit_code: str | None
    unit_name: str | None
    conversion_factor_to_base: Decimal
    is_base: bool
    sale_price: Decimal | None = None
    minimum_sale_price: Decimal | None = None

    def to_base_quantity(self, quantity: Decimal) -> Decimal:
        return _q4(_d(quantity) * self.conversion_factor_to_base)

    def to_base_unit_cost(self, unit_cost: Decimal) -> Decimal:
        factor = self.conversion_factor_to_base
        if factor <= Decimal("0"):
            raise ValidationError("conversion_factor_to_base must be greater than zero.")
        return _q2(_d(unit_cost) / factor)


class ProductUnitConversionService:
    def __init__(self, session):
        self.session = session

    def resolve_for_sale(
        self,
        *,
        tenant_id: str,
        product: Product,
        product_unit_id: str | None,
    ) -> ProductUnitResolution:
        resolution = self.resolve(
            tenant_id=tenant_id,
            product=product,
            product_unit_id=product_unit_id,
        )
        if product_unit_id:
            product_unit = self._require_product_unit(
                tenant_id=tenant_id,
                product=product,
                product_unit_id=product_unit_id,
            )
            if not product_unit.can_sell:
                raise ValidationError("product_unit_id is not sellable for this product.")
        return resolution

    def resolve_for_receipt(
        self,
        *,
        tenant_id: str,
        product: Product,
        product_unit_id: str | None,
    ) -> ProductUnitResolution:
        resolution = self.resolve(
            tenant_id=tenant_id,
            product=product,
            product_unit_id=product_unit_id,
        )
        if product_unit_id:
            product_unit = self._require_product_unit(
                tenant_id=tenant_id,
                product=product,
                product_unit_id=product_unit_id,
            )
            if not product_unit.can_receive:
                raise ValidationError("product_unit_id is not receivable for this product.")
        return resolution

    def _require_product_unit(
        self,
        *,
        tenant_id: str,
        product: Product,
        product_unit_id: str,
    ) -> ProductUnit:
        product_unit = (
            self.session.query(ProductUnit)
            .filter(
                ProductUnit.id == product_unit_id,
                ProductUnit.tenant_id == tenant_id,
                ProductUnit.product_id == str(product.id),
                ProductUnit.is_active.is_(True),
            )
            .first()
        )
        if not product_unit:
            raise ValidationError("product_unit_id not found for this product.")
        return product_unit

    def resolve(
        self,
        *,
        tenant_id: str,
        product: Product,
        product_unit_id: str | None,
    ) -> ProductUnitResolution:
        if product_unit_id:
            product_unit = self._require_product_unit(
                tenant_id=tenant_id,
                product=product,
                product_unit_id=product_unit_id,
            )
            return self._from_product_unit(product_unit)

        product_unit = (
            self.session.query(ProductUnit)
            .filter(
                ProductUnit.tenant_id == tenant_id,
                ProductUnit.product_id == str(product.id),
                ProductUnit.is_base.is_(True),
                ProductUnit.is_active.is_(True),
            )
            .first()
        )
        if product_unit:
            return self._from_product_unit(product_unit)

        unit = (
            self.session.query(UnitOfMeasure)
            .filter(
                UnitOfMeasure.id == product.unit_id,
                UnitOfMeasure.tenant_id == tenant_id,
            )
            .first()
            if product.unit_id
            else None
        )
        return ProductUnitResolution(
            product_unit_id=None,
            unit_id=str(unit.id) if unit else None,
            unit_code=unit.code if unit else None,
            unit_name=unit.name if unit else None,
            conversion_factor_to_base=Decimal("1.000000"),
            is_base=True,
            sale_price=_q2(product.default_sale_price) if product.default_sale_price is not None else None,
            minimum_sale_price=_q2(product.min_sale_price) if product.min_sale_price is not None else None,
        )

    def _from_product_unit(self, product_unit: ProductUnit) -> ProductUnitResolution:
        if _d(product_unit.conversion_factor_to_base) <= Decimal("0"):
            raise ValidationError("conversion_factor_to_base must be greater than zero.")

        unit = self.session.get(UnitOfMeasure, product_unit.unit_id)
        return ProductUnitResolution(
            product_unit_id=str(product_unit.id),
            unit_id=str(product_unit.unit_id),
            unit_code=unit.code if unit else None,
            unit_name=unit.name if unit else None,
            conversion_factor_to_base=_q6(product_unit.conversion_factor_to_base),
            is_base=bool(product_unit.is_base),
            sale_price=_q2(product_unit.sale_price) if product_unit.sale_price is not None else None,
            minimum_sale_price=(
                _q2(product_unit.minimum_sale_price)
                if product_unit.minimum_sale_price is not None
                else None
            ),
        )
