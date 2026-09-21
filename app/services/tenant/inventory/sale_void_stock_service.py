from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from app.models import (
    InventoryBatch,
    InventoryMovement,
    Product,
    StockBalance,
)


FOURPLACES = Decimal("0.0001")


def d(value) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def q4(value) -> Decimal:
    return d(value).quantize(FOURPLACES, rounding=ROUND_HALF_UP)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SaleVoidStockRestorationError(ValueError):
    pass


@dataclass(frozen=True)
class SaleVoidStockRestorationLine:
    batch_id: str | None
    quantity: Decimal
    unit_cost: Decimal | None


def _available_from(on_hand, reserved) -> Decimal:
    return q4(d(on_hand) - d(reserved))


def _lock_stock_balance(
    session,
    *,
    tenant_id: str,
    branch_id: str,
    warehouse_id: str,
    product_id: str,
) -> StockBalance:
    stock_balance = (
        session.query(StockBalance)
        .filter(
            StockBalance.tenant_id == tenant_id,
            StockBalance.branch_id == branch_id,
            StockBalance.warehouse_id == warehouse_id,
            StockBalance.product_id == product_id,
        )
        .with_for_update()
        .first()
    )

    if not stock_balance:
        raise SaleVoidStockRestorationError(
            f"No stock balance found for product_id={product_id}."
        )

    return stock_balance


def _original_sale_movements(
    session,
    *,
    tenant_id: str,
    branch_id: str,
    warehouse_id: str,
    sale_id: str,
    sale_item_id: str,
    product_id: str,
) -> list[InventoryMovement]:
    return (
        session.query(InventoryMovement)
        .filter(
            InventoryMovement.tenant_id == tenant_id,
            InventoryMovement.branch_id == branch_id,
            InventoryMovement.warehouse_id == warehouse_id,
            InventoryMovement.sale_item_id == sale_item_id,
            InventoryMovement.product_id == product_id,
            InventoryMovement.reference_type == "sale",
            InventoryMovement.reference_id == sale_id,
            InventoryMovement.quantity < 0,
        )
        .order_by(
            InventoryMovement.created_at.asc(),
            InventoryMovement.id.asc(),
        )
        .with_for_update()
        .all()
    )


def _already_restored_by_batch(
    session,
    *,
    tenant_id: str,
    branch_id: str,
    warehouse_id: str,
    sale_id: str,
    sale_item_id: str,
    product_id: str,
) -> dict[str | None, Decimal]:
    """
    Return stock already restored from the original sale allocation.

    Refund returns and any prior sale-void restoration both count because
    inventory must never be restored twice.
    """
    rows = (
        session.query(
            InventoryMovement.batch_id,
            InventoryMovement.quantity,
        )
        .filter(
            InventoryMovement.tenant_id == tenant_id,
            InventoryMovement.branch_id == branch_id,
            InventoryMovement.warehouse_id == warehouse_id,
            InventoryMovement.sale_item_id == sale_item_id,
            InventoryMovement.product_id == product_id,
            InventoryMovement.quantity > 0,
            InventoryMovement.reference_type.in_(
                (
                    "sale_refund",
                    "sale_void",
                )
            ),
        )
        .with_for_update()
        .all()
    )

    totals: dict[str | None, Decimal] = defaultdict(
        lambda: Decimal("0.0000")
    )

    for batch_id, quantity in rows:
        key = str(batch_id) if batch_id else None
        totals[key] += q4(quantity)

    return dict(totals)


def restore_sale_void_stock(
    session,
    *,
    tenant_id: str,
    branch_id: str,
    warehouse_id: str,
    sale_id: str,
    sale_item_id: str,
    product_id: str,
    created_by: str,
    note: str | None = None,
    now: datetime | None = None,
) -> tuple[SaleVoidStockRestorationLine, ...]:
    """
    Restore the remaining inventory allocation for one voided SaleItem.

    Inventory truth comes from the original negative sale movements rather
    than the SaleItem's display quantity or the product's current UOM setup.

    Any stock already restored by posted refunds is subtracted first.
    Batch-tracked sales are therefore restored to the exact original batches.

    The caller owns the surrounding transaction. This function never commits.
    """
    now = now or utcnow()

    sale_movements = _original_sale_movements(
        session,
        tenant_id=tenant_id,
        branch_id=branch_id,
        warehouse_id=warehouse_id,
        sale_id=sale_id,
        sale_item_id=sale_item_id,
        product_id=product_id,
    )

    if not sale_movements:
        product = (
            session.query(Product)
            .filter(
                Product.id == product_id,
                Product.tenant_id == tenant_id,
            )
            .first()
        )

        if not product:
            raise SaleVoidStockRestorationError(
                f"Product {product_id} was not found."
            )

        if not bool(product.track_inventory):
            return ()

        raise SaleVoidStockRestorationError(
            "Original stock allocation is not traceable for "
            f"sale_item_id={sale_item_id}."
        )

    original_by_batch: dict[str | None, Decimal] = defaultdict(
        lambda: Decimal("0.0000")
    )
    cost_by_batch: dict[str | None, Decimal | None] = {}

    for movement in sale_movements:
        batch_id = str(movement.batch_id) if movement.batch_id else None
        original_by_batch[batch_id] += q4(abs(d(movement.quantity)))
        cost_by_batch[batch_id] = movement.unit_cost

    already_restored = _already_restored_by_batch(
        session,
        tenant_id=tenant_id,
        branch_id=branch_id,
        warehouse_id=warehouse_id,
        sale_id=sale_id,
        sale_item_id=sale_item_id,
        product_id=product_id,
    )

    remaining_by_batch: dict[str | None, Decimal] = {}

    for batch_id, original_quantity in original_by_batch.items():
        restored_quantity = q4(
            already_restored.get(
                batch_id,
                Decimal("0.0000"),
            )
        )

        remaining = q4(original_quantity - restored_quantity)

        if remaining < Decimal("0.0000"):
            raise SaleVoidStockRestorationError(
                "Previously restored stock exceeds the original sale "
                f"allocation for sale_item_id={sale_item_id}, "
                f"batch_id={batch_id}."
            )

        remaining_by_batch[batch_id] = remaining

    quantity_to_restore = q4(
        sum(
            remaining_by_batch.values(),
            Decimal("0.0000"),
        )
    )

    if quantity_to_restore == Decimal("0.0000"):
        return ()

    stock_balance = _lock_stock_balance(
        session,
        tenant_id=tenant_id,
        branch_id=branch_id,
        warehouse_id=warehouse_id,
        product_id=product_id,
    )

    restored_lines: list[SaleVoidStockRestorationLine] = []

    for batch_id, quantity in remaining_by_batch.items():
        if quantity <= Decimal("0.0000"):
            continue

        if batch_id is not None:
            batch = (
                session.query(InventoryBatch)
                .filter(
                    InventoryBatch.id == batch_id,
                    InventoryBatch.tenant_id == tenant_id,
                    InventoryBatch.warehouse_id == warehouse_id,
                    InventoryBatch.product_id == product_id,
                )
                .with_for_update()
                .first()
            )

            if not batch:
                raise SaleVoidStockRestorationError(
                    f"Original inventory batch {batch_id} was not found "
                    f"for sale_item_id={sale_item_id}."
                )

            batch.quantity_on_hand = q4(
                d(batch.quantity_on_hand) + quantity
            )
            batch.updated_at = now

        movement = InventoryMovement(
            tenant_id=tenant_id,
            branch_id=branch_id,
            warehouse_id=warehouse_id,
            product_id=product_id,
            batch_id=batch_id,
            sale_item_id=sale_item_id,
            movement_type="sale_void",
            quantity=quantity,
            unit_cost=cost_by_batch.get(batch_id),
            reference_type="sale_void",
            reference_id=sale_id,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )

        if hasattr(movement, "notes"):
            movement.notes = (
                f"Stock restored during sale void for sale {sale_id}"
                + (f": {note}" if note else "")
            )

        session.add(movement)

        restored_lines.append(
            SaleVoidStockRestorationLine(
                batch_id=batch_id,
                quantity=quantity,
                unit_cost=cost_by_batch.get(batch_id),
            )
        )

    new_on_hand = q4(
        d(stock_balance.quantity_on_hand) + quantity_to_restore
    )

    stock_balance.quantity_on_hand = new_on_hand
    stock_balance.quantity_available = _available_from(
        new_on_hand,
        stock_balance.quantity_reserved,
    )
    stock_balance.updated_at = now

    return tuple(restored_lines)


__all__ = [
    "SaleVoidStockRestorationError",
    "SaleVoidStockRestorationLine",
    "restore_sale_void_stock",
]
