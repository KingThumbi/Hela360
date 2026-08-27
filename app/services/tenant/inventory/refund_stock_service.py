from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from app.models import InventoryBatch, InventoryMovement, Product, StockBalance


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


class RefundStockRestorationError(ValueError):
    pass


@dataclass(frozen=True)
class RefundStockRestorationLine:
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
        raise RefundStockRestorationError(
            f"No stock balance found for product_id={product_id}."
        )

    return stock_balance


def _restore_stock_balance(
    stock_balance: StockBalance,
    quantity: Decimal,
    *,
    now: datetime,
) -> None:
    new_on_hand = q4(d(stock_balance.quantity_on_hand) + quantity)
    stock_balance.quantity_on_hand = new_on_hand
    stock_balance.quantity_available = _available_from(
        new_on_hand,
        stock_balance.quantity_reserved,
    )
    stock_balance.updated_at = now


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
    sale_item_id: str,
) -> dict[str | None, Decimal]:
    rows = (
        session.query(
            InventoryMovement.batch_id,
            InventoryMovement.quantity,
        )
        .filter(
            InventoryMovement.tenant_id == tenant_id,
            InventoryMovement.sale_item_id == sale_item_id,
            InventoryMovement.reference_type == "sale_refund",
            InventoryMovement.quantity > 0,
        )
        .with_for_update()
        .all()
    )

    totals: dict[str | None, Decimal] = defaultdict(lambda: Decimal("0.0000"))
    for batch_id, quantity in rows:
        totals[str(batch_id) if batch_id else None] += q4(quantity)

    return dict(totals)


def restore_refund_stock(
    session,
    *,
    tenant_id: str,
    branch_id: str,
    warehouse_id: str,
    sale_id: str,
    sale_item_id: str,
    product: Product,
    quantity: Decimal,
    refund_id: str,
    refund_number: str,
    created_by: str,
    note: str | None = None,
    now: datetime | None = None,
) -> tuple[RefundStockRestorationLine, ...]:
    quantity = q4(quantity)

    if quantity <= Decimal("0.0000"):
        raise RefundStockRestorationError(
            "Refund stock quantity must be greater than zero."
        )

    if not product.track_inventory:
        return ()

    now = now or utcnow()
    product_id = str(product.id)

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
        raise RefundStockRestorationError(
            f"Original stock allocation is not traceable for sale_item_id={sale_item_id}."
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
        sale_item_id=sale_item_id,
    )

    remaining_by_batch = {
        batch_id: q4(original_qty - already_restored.get(batch_id, Decimal("0.0000")))
        for batch_id, original_qty in original_by_batch.items()
    }
    remaining_total = q4(
        sum(remaining_by_batch.values(), Decimal("0.0000"))
    )

    if quantity > remaining_total:
        raise RefundStockRestorationError(
            f"Refund stock quantity {quantity} exceeds traceable remaining quantity {remaining_total} for sale_item_id={sale_item_id}."
        )

    stock_balance = _lock_stock_balance(
        session,
        tenant_id=tenant_id,
        branch_id=branch_id,
        warehouse_id=warehouse_id,
        product_id=product_id,
    )

    remaining_to_restore = quantity
    restored_lines: list[RefundStockRestorationLine] = []

    for batch_id in original_by_batch:
        if remaining_to_restore <= Decimal("0.0000"):
            break

        batch_remaining = remaining_by_batch[batch_id]
        if batch_remaining <= Decimal("0.0000"):
            continue

        restored = min(batch_remaining, remaining_to_restore)

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
                raise RefundStockRestorationError(
                    f"Original inventory batch {batch_id} was not found for sale_item_id={sale_item_id}."
                )

            batch.quantity_on_hand = q4(d(batch.quantity_on_hand) + restored)
            batch.updated_at = now

        movement = InventoryMovement(
            tenant_id=tenant_id,
            branch_id=branch_id,
            warehouse_id=warehouse_id,
            product_id=product_id,
            batch_id=batch_id,
            sale_item_id=sale_item_id,
            movement_type="sale_refund_return",
            quantity=restored,
            unit_cost=cost_by_batch.get(batch_id),
            reference_type="sale_refund",
            reference_id=refund_id,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )

        if hasattr(movement, "notes"):
            movement.notes = (
                f"Stock returned from refund {refund_number} for sale {sale_id}"
                + (f": {note}" if note else "")
            )

        session.add(movement)
        restored_lines.append(
            RefundStockRestorationLine(
                batch_id=batch_id,
                quantity=restored,
                unit_cost=cost_by_batch.get(batch_id),
            )
        )
        remaining_to_restore = q4(remaining_to_restore - restored)

    if remaining_to_restore != Decimal("0.0000"):
        raise RefundStockRestorationError(
            f"Unable to restore requested stock for sale_item_id={sale_item_id}."
        )

    _restore_stock_balance(stock_balance, quantity, now=now)

    return tuple(restored_lines)
