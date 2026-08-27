from __future__ import annotations

from decimal import Decimal

from app.models import (
    InventoryBatch,
    Product,
    StockAdjustment,
    StockAdjustmentItem,
    StockCount,
    Warehouse,
)


def _timestamp(value) -> str | None:
    return value.isoformat() if value else None


def _date(value) -> str | None:
    return value.isoformat() if value else None


def _decimal(value) -> str:
    if isinstance(value, Decimal):
        return str(value)
    return str(value) if value is not None else "0"


def _user(value: dict | None) -> dict | None:
    if not value:
        return None
    return {
        "id": str(value["id"]),
        "name": " ".join(
            part
            for part in [
                value["first_name"],
                value["last_name"],
            ]
            if part
        )
        or None,
        "username": value["username"],
    }


def _source(
    adjustment: StockAdjustment,
    source_count: StockCount | None,
) -> dict:
    return {
        "type": adjustment.source_type,
        "id": str(adjustment.source_id) if adjustment.source_id else None,
        "stock_count": (
            {
                "id": str(source_count.id),
                "count_number": source_count.count_number,
            }
            if source_count
            else None
        ),
    }


def serialize_stock_adjustment_item(
    item: StockAdjustmentItem,
    *,
    product: Product,
    batch: InventoryBatch | None,
) -> dict:
    return {
        "id": str(item.id),
        "line_number": item.line_number,
        "product": {
            "id": str(product.id),
            "internal_sku": product.internal_sku,
            "name": product.name,
            "track_batches": bool(product.track_batches),
            "track_expiry": bool(product.track_expiry),
        },
        "batch": (
            {
                "id": str(batch.id),
                "batch_number": batch.batch_number,
                "expiry_date": _date(batch.expiry_date),
            }
            if batch
            else None
        ),
        "stock_count_item_id": (
            str(item.stock_count_item_id) if item.stock_count_item_id else None
        ),
        "quantity_delta": _decimal(item.quantity_delta),
        "reason": item.reason,
    }


def serialize_stock_adjustment(
    adjustment: StockAdjustment,
    *,
    warehouse: Warehouse,
    posted_by: dict | None,
    source_count: StockCount | None,
    items: list[tuple[StockAdjustmentItem, Product, InventoryBatch | None]],
) -> dict:
    return {
        "id": str(adjustment.id),
        "adjustment_number": adjustment.adjustment_number,
        "status": adjustment.status,
        "warehouse": {
            "id": str(warehouse.id),
            "code": warehouse.code,
            "name": warehouse.name,
        },
        "reason_code": adjustment.reason_code,
        "reason": adjustment.reason,
        "source": _source(adjustment, source_count),
        "posted_at": _timestamp(adjustment.posted_at),
        "posted_by": _user(posted_by),
        "notes": adjustment.notes,
        "items": [
            serialize_stock_adjustment_item(
                item,
                product=product,
                batch=batch,
            )
            for item, product, batch in items
        ],
        "created_at": _timestamp(adjustment.created_at),
        "updated_at": _timestamp(adjustment.updated_at),
    }


def serialize_stock_adjustment_summary(
    adjustment: StockAdjustment,
    *,
    warehouse: Warehouse,
    posted_by: dict | None,
    source_count: StockCount | None,
    item_count: int,
) -> dict:
    return {
        "id": str(adjustment.id),
        "adjustment_number": adjustment.adjustment_number,
        "status": adjustment.status,
        "warehouse": {
            "id": str(warehouse.id),
            "code": warehouse.code,
            "name": warehouse.name,
        },
        "reason_code": adjustment.reason_code,
        "reason": adjustment.reason,
        "source": _source(adjustment, source_count),
        "posted_at": _timestamp(adjustment.posted_at),
        "posted_by": _user(posted_by),
        "item_count": item_count,
        "notes": adjustment.notes,
        "created_at": _timestamp(adjustment.created_at),
        "updated_at": _timestamp(adjustment.updated_at),
    }
