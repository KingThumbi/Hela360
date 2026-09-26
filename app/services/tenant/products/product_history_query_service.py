from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func

from app.models import (
    InventoryMovement,
    Product,
    ProductUnit,
    StockBalance,
)


ZERO_QTY = Decimal("0.0000")


@dataclass(frozen=True)
class ProductHistorySummary:
    product: Product
    product_units: tuple[ProductUnit, ...]
    quantity_on_hand: Decimal
    quantity_reserved: Decimal
    quantity_available: Decimal
    warehouse_count: int
    movement_count: int
    last_movement_at: datetime | None


class ProductHistoryQueryService:
    """
    Read-only Product Intelligence query service.

    This first slice deliberately exposes only authoritative current
    stock/UOM state and inventory-ledger activity metadata.
    """

    def __init__(self, session):
        self.session = session

    def get_summary(
        self,
        *,
        tenant_id: str,
        branch_id: str | None,
        product_id: str,
    ) -> ProductHistorySummary | None:
        product = (
            self.session.query(Product)
            .filter(
                Product.id == product_id,
                Product.tenant_id == tenant_id,
            )
            .first()
        )

        if product is None:
            return None

        product_units = tuple(
            self.session.query(ProductUnit)
            .filter(
                ProductUnit.tenant_id == tenant_id,
                ProductUnit.product_id == product_id,
            )
            .order_by(
                ProductUnit.is_base.desc(),
                ProductUnit.created_at.asc(),
                ProductUnit.id.asc(),
            )
            .all()
        )

        stock_query = (
            self.session.query(
                func.coalesce(
                    func.sum(StockBalance.quantity_on_hand),
                    ZERO_QTY,
                ),
                func.coalesce(
                    func.sum(StockBalance.quantity_reserved),
                    ZERO_QTY,
                ),
                func.coalesce(
                    func.sum(StockBalance.quantity_available),
                    ZERO_QTY,
                ),
                func.count(StockBalance.id),
            )
            .filter(
                StockBalance.tenant_id == tenant_id,
                StockBalance.product_id == product_id,
            )
        )

        if branch_id:
            stock_query = stock_query.filter(
                StockBalance.branch_id == branch_id,
            )

        (
            quantity_on_hand,
            quantity_reserved,
            quantity_available,
            warehouse_count,
        ) = stock_query.one()

        movement_query = (
            self.session.query(
                func.count(InventoryMovement.id),
                func.max(InventoryMovement.created_at),
            )
            .filter(
                InventoryMovement.tenant_id == tenant_id,
                InventoryMovement.product_id == product_id,
            )
        )

        if branch_id:
            movement_query = movement_query.filter(
                InventoryMovement.branch_id == branch_id,
            )

        movement_count, last_movement_at = movement_query.one()

        return ProductHistorySummary(
            product=product,
            product_units=product_units,
            quantity_on_hand=Decimal(
                quantity_on_hand or ZERO_QTY
            ),
            quantity_reserved=Decimal(
                quantity_reserved or ZERO_QTY
            ),
            quantity_available=Decimal(
                quantity_available or ZERO_QTY
            ),
            warehouse_count=int(warehouse_count or 0),
            movement_count=int(movement_count or 0),
            last_movement_at=last_movement_at,
        )
