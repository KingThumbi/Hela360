from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
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


class StockAllocationError(ValueError):
    pass


@dataclass(frozen=True)
class StockAllocationLine:
    batch_id: str | None
    quantity: Decimal
    unit_cost: Decimal | None


@dataclass(frozen=True)
class StockAllocationResult:
    product_id: str
    warehouse_id: str
    quantity: Decimal
    allocations: tuple[StockAllocationLine, ...]

    @property
    def single_batch_id(self) -> str | None:
        if len(self.allocations) != 1:
            return None
        return self.allocations[0].batch_id


def _available_from(on_hand, reserved) -> Decimal:
    return q4(d(on_hand) - d(reserved))


def _batch_is_sellable(
    batch: InventoryBatch,
    *,
    product: Product,
    operational_date: date,
) -> bool:
    if (batch.status or "").lower() != "available":
        return False

    if (
        _available_from(batch.quantity_on_hand, batch.quantity_reserved)
        <= Decimal("0.0000")
    ):
        return False

    if batch.expiry_date is not None and batch.expiry_date < operational_date:
        return False

    if product.track_expiry and batch.expiry_date is None:
        return False

    return True


def _batch_sort_key(batch: InventoryBatch):
    return (
        batch.expiry_date is None,
        batch.expiry_date or date.max,
        batch.received_at or datetime.min.replace(tzinfo=timezone.utc),
        str(batch.id),
    )


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
        raise StockAllocationError(
            f"No stock balance found for product_id={product_id}."
        )

    return stock_balance


def _lock_batches(
    session,
    *,
    tenant_id: str,
    warehouse_id: str,
    product_id: str,
) -> list[InventoryBatch]:
    return (
        session.query(InventoryBatch)
        .filter(
            InventoryBatch.tenant_id == tenant_id,
            InventoryBatch.warehouse_id == warehouse_id,
            InventoryBatch.product_id == product_id,
        )
        .with_for_update()
        .all()
    )


def _add_sale_movement(
    session,
    *,
    tenant_id: str,
    branch_id: str,
    warehouse_id: str,
    product_id: str,
    batch_id: str | None,
    quantity: Decimal,
    unit_cost: Decimal | None,
    sale_id: str,
    sale_item_id: str | None,
    created_by: str,
    now: datetime,
) -> None:
    movement = InventoryMovement(
        tenant_id=tenant_id,
        branch_id=branch_id,
        warehouse_id=warehouse_id,
        product_id=product_id,
        batch_id=batch_id,
        sale_item_id=sale_item_id,
        movement_type="sale",
        quantity=q4(-quantity),
        unit_cost=unit_cost,
        reference_type="sale",
        reference_id=sale_id,
        created_by=created_by,
        created_at=now,
        updated_at=now,
    )

    if hasattr(movement, "notes"):
        movement.notes = "Stock deducted during sales checkout."

    session.add(movement)


def _deduct_stock_balance(stock_balance: StockBalance, quantity: Decimal) -> None:
    new_on_hand = q4(d(stock_balance.quantity_on_hand) - quantity)
    if new_on_hand < Decimal("0.0000"):
        raise StockAllocationError(
            f"Insufficient stock for product_id={stock_balance.product_id}."
        )

    stock_balance.quantity_on_hand = new_on_hand
    stock_balance.quantity_available = _available_from(
        new_on_hand,
        stock_balance.quantity_reserved,
    )
    stock_balance.updated_at = utcnow()


def _allocate_stock_balance_only(
    session,
    *,
    tenant_id: str,
    branch_id: str,
    warehouse_id: str,
    product: Product,
    stock_balance: StockBalance,
    quantity: Decimal,
    sale_id: str,
    sale_item_id: str | None = None,
    created_by: str,
    now: datetime,
) -> StockAllocationResult:
    _deduct_stock_balance(stock_balance, quantity)

    unit_cost = stock_balance.avg_unit_cost
    _add_sale_movement(
        session,
        tenant_id=tenant_id,
        branch_id=branch_id,
        warehouse_id=warehouse_id,
        product_id=str(product.id),
        batch_id=None,
        quantity=quantity,
        unit_cost=unit_cost,
        sale_id=sale_id,
        sale_item_id=sale_item_id,
        created_by=created_by,
        now=now,
    )

    return StockAllocationResult(
        product_id=str(product.id),
        warehouse_id=warehouse_id,
        quantity=quantity,
        allocations=(
            StockAllocationLine(
                batch_id=None,
                quantity=quantity,
                unit_cost=unit_cost,
            ),
        ),
    )


def allocate_sale_stock(
    session,
    *,
    tenant_id: str,
    branch_id: str,
    warehouse_id: str,
    product: Product,
    quantity: Decimal,
    sale_id: str,
    sale_item_id: str | None = None,
    created_by: str,
    operational_date: date | None = None,
    now: datetime | None = None,
) -> StockAllocationResult:
    quantity = q4(quantity)

    if not product.track_inventory:
        return StockAllocationResult(
            product_id=str(product.id),
            warehouse_id=warehouse_id,
            quantity=quantity,
            allocations=(),
        )

    now = now or utcnow()
    operational_date = operational_date or now.date()
    product_id = str(product.id)

    stock_balance = _lock_stock_balance(
        session,
        tenant_id=tenant_id,
        branch_id=branch_id,
        warehouse_id=warehouse_id,
        product_id=product_id,
    )

    available = q4(d(stock_balance.quantity_available))
    if available < quantity:
        raise StockAllocationError(
            f"Insufficient stock for product_id={product_id}. "
            f"Available={available}, requested={quantity}."
        )

    if not product.track_batches and not product.track_expiry:
        return _allocate_stock_balance_only(
            session,
            tenant_id=tenant_id,
            branch_id=branch_id,
            warehouse_id=warehouse_id,
            product=product,
            stock_balance=stock_balance,
            quantity=quantity,
            sale_id=sale_id,
            sale_item_id=sale_item_id,
            created_by=created_by,
            now=now,
        )

    batches = _lock_batches(
        session,
        tenant_id=tenant_id,
        warehouse_id=warehouse_id,
        product_id=product_id,
    )
    eligible_batches = sorted(
        (
            batch
            for batch in batches
            if _batch_is_sellable(
                batch,
                product=product,
                operational_date=operational_date,
            )
        ),
        key=_batch_sort_key,
    )

    sellable_quantity = q4(
        sum(
            (
                _available_from(batch.quantity_on_hand, batch.quantity_reserved)
                for batch in eligible_batches
            ),
            Decimal("0.0000"),
        )
    )
    if sellable_quantity < quantity:
        raise StockAllocationError(
            f"Insufficient sellable batch stock for product_id={product_id}. "
            f"Available={sellable_quantity}, requested={quantity}."
        )

    remaining = quantity
    allocation_lines: list[StockAllocationLine] = []

    for batch in eligible_batches:
        if remaining <= Decimal("0.0000"):
            break

        batch_available = _available_from(
            batch.quantity_on_hand,
            batch.quantity_reserved,
        )
        allocated = min(batch_available, remaining)
        batch.quantity_on_hand = q4(d(batch.quantity_on_hand) - allocated)
        batch.updated_at = now

        allocation_lines.append(
            StockAllocationLine(
                batch_id=str(batch.id),
                quantity=allocated,
                unit_cost=batch.unit_cost,
            )
        )
        _add_sale_movement(
            session,
            tenant_id=tenant_id,
            branch_id=branch_id,
            warehouse_id=warehouse_id,
            product_id=product_id,
            batch_id=str(batch.id),
            quantity=allocated,
            unit_cost=batch.unit_cost,
            sale_id=sale_id,
            sale_item_id=sale_item_id,
            created_by=created_by,
            now=now,
        )

        remaining = q4(remaining - allocated)

    if remaining != Decimal("0.0000"):
        raise StockAllocationError(
            f"Unable to allocate requested stock for product_id={product_id}."
        )

    _deduct_stock_balance(stock_balance, quantity)

    return StockAllocationResult(
        product_id=product_id,
        warehouse_id=warehouse_id,
        quantity=quantity,
        allocations=tuple(allocation_lines),
    )
