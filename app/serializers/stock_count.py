from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.models import (
    InventoryBatch,
    Product,
    StockAdjustment,
    StockCount,
    StockCountItem,
    Warehouse,
)


OPEN_STATUS = "open"
BLIND_MODE = "blind"


def _timestamp(value) -> str | None:
    return value.isoformat() if value else None


def _date(value) -> str | None:
    return value.isoformat() if value else None


def _decimal(value) -> str | None:
    if value is None:
        return None

    if isinstance(value, Decimal):
        return str(value)

    return str(value)


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


def _is_expired(
    expiry_date: date | None,
) -> bool:
    return (
        expiry_date is not None
        and expiry_date < date.today()
    )


def _is_open_blind_count(
    count: StockCount,
) -> bool:
    """
    Return whether system quantities must remain concealed.

    Blind-count confidentiality applies only while the count is open.
    Once completed or cancelled, the stored comparison information may
    be exposed for review and audit.
    """

    return (
        count.status == OPEN_STATUS
        and count.count_mode == BLIND_MODE
    )


def stock_count_summary(
    *,
    total_items: int,
    counted_items: int,
    variance_items: int,
    positive_variance_items: int,
    negative_variance_items: int,
    expose_variance: bool = True,
) -> dict:
    summary = {
        "total_items": total_items,
        "counted_items": counted_items,
        "uncounted_items": max(
            total_items - counted_items,
            0,
        ),
    }

    if expose_variance:
        summary.update(
            {
                "variance_items": variance_items,
                "positive_variance_items":
                    positive_variance_items,
                "negative_variance_items":
                    negative_variance_items,
            }
        )

    return summary


def serialize_stock_count_item(
    item: StockCountItem,
    *,
    product: Product,
    batch: InventoryBatch | None,
    counted_by: dict | None,
    expose_system_quantities: bool = True,
) -> dict:
    """
    Serialize one physical Stock Count line.

    Snapshot lines refer to inventory known by the system when the count
    began. Discovered lines represent physical stock observed during the
    count that did not have an appropriate snapshot line.

    During an open blind count, system-derived quantities are deliberately
    omitted from the response so that the counter cannot anchor the physical
    count to the expected system quantity.
    """

    source_type = (
        item.source_type
        or "snapshot"
    )

    observed_batch_number = (
        item.observed_batch_number
        if source_type == "discovered"
        else None
    )

    observed_expiry_date = (
        item.observed_expiry_date
        if source_type == "discovered"
        else None
    )

    serialized = {
        "id": str(item.id),
        "line_number": item.line_number,
        "source_type": source_type,
        "product": {
            "id": str(product.id),
            "internal_sku": product.internal_sku,
            "name": product.name,
            "track_batches": bool(
                product.track_batches
            ),
            "track_expiry": bool(
                product.track_expiry
            ),
        },
        "batch": (
            {
                "id": str(batch.id),
                "batch_number":
                    batch.batch_number,
                "expiry_date":
                    _date(batch.expiry_date),
                "is_expired":
                    _is_expired(
                        batch.expiry_date
                    ),
            }
            if batch
            else None
        ),
        "observed_batch_number":
            observed_batch_number,
        "observed_expiry_date":
            _date(observed_expiry_date),
        "counted_quantity":
            _decimal(
                item.counted_quantity
            ),
        "counted_at":
            _timestamp(item.counted_at),
        "counted_by":
            _user(counted_by),
        "notes":
            item.notes,
    }

    if expose_system_quantities:
        serialized.update(
            {
                "snapshot_quantity":
                    _decimal(
                        item.snapshot_quantity
                    ),
                "expected_quantity":
                    _decimal(
                        item.expected_quantity
                    ),
                "variance_quantity":
                    _decimal(
                        item.variance_quantity
                    ),
            }
        )

    return serialized


def serialize_stock_count(
    count: StockCount,
    *,
    warehouse: Warehouse,
    started_by: dict | None,
    completed_by: dict | None,
    cancelled_by: dict | None,
    items: list[
        tuple[
            StockCountItem,
            Product,
            InventoryBatch | None,
            dict | None,
        ]
    ],
    adjustment: StockAdjustment | None = None,
) -> dict:
    open_blind = _is_open_blind_count(
        count
    )

    expose_system_quantities = (
        not open_blind
    )

    serialized_items = [
        serialize_stock_count_item(
            item,
            product=product,
            batch=batch,
            counted_by=counted_by,
            expose_system_quantities=(
                expose_system_quantities
            ),
        )
        for (
            item,
            product,
            batch,
            counted_by,
        ) in items
    ]

    counted_items = [
        item
        for item in items
        if item[0].counted_quantity
        is not None
    ]

    variance_items = [
        item
        for item in counted_items
        if (
            item[0].variance_quantity
            is not None
            and Decimal(
                item[0].variance_quantity
            )
            != Decimal("0")
        )
    ]

    positive_variance_items = [
        item
        for item in variance_items
        if Decimal(
            item[0].variance_quantity
        )
        > Decimal("0")
    ]

    negative_variance_items = [
        item
        for item in variance_items
        if Decimal(
            item[0].variance_quantity
        )
        < Decimal("0")
    ]

    return {
        "id": str(count.id),
        "count_number":
            count.count_number,
        "status":
            count.status,
        "scope_type":
            count.scope_type,
        "count_mode":
            count.count_mode,
        "warehouse": {
            "id": str(warehouse.id),
            "code": warehouse.code,
            "name": warehouse.name,
        },
        "snapshot_at":
            _timestamp(
                count.snapshot_at
            ),
        "started_at":
            _timestamp(
                count.started_at
            ),
        "started_by":
            _user(started_by),
        "completed_at":
            _timestamp(
                count.completed_at
            ),
        "completed_by":
            _user(completed_by),
        "cancelled_at":
            _timestamp(
                count.cancelled_at
            ),
        "cancelled_by":
            _user(cancelled_by),
        "notes":
            count.notes,
        "adjustment": (
            {
                "id": str(
                    adjustment.id
                ),
                "adjustment_number":
                    adjustment.adjustment_number,
            }
            if adjustment
            else None
        ),
        "summary":
            stock_count_summary(
                total_items=len(
                    serialized_items
                ),
                counted_items=len(
                    counted_items
                ),
                variance_items=len(
                    variance_items
                ),
                positive_variance_items=len(
                    positive_variance_items
                ),
                negative_variance_items=len(
                    negative_variance_items
                ),
                expose_variance=(
                    expose_system_quantities
                ),
            ),
        "items":
            serialized_items,
        "created_at":
            _timestamp(
                count.created_at
            ),
        "updated_at":
            _timestamp(
                count.updated_at
            ),
    }


def serialize_stock_count_summary(
    count: StockCount,
    *,
    warehouse: Warehouse,
    started_by: dict | None,
    item_counts: dict,
    adjustment: StockAdjustment | None = None,
) -> dict:
    open_blind = _is_open_blind_count(
        count
    )

    return {
        "id": str(count.id),
        "count_number":
            count.count_number,
        "status":
            count.status,
        "scope_type":
            count.scope_type,
        "count_mode":
            count.count_mode,
        "warehouse": {
            "id": str(warehouse.id),
            "code": warehouse.code,
            "name": warehouse.name,
        },
        "snapshot_at":
            _timestamp(
                count.snapshot_at
            ),
        "started_at":
            _timestamp(
                count.started_at
            ),
        "started_by":
            _user(started_by),
        "completed_at":
            _timestamp(
                count.completed_at
            ),
        "cancelled_at":
            _timestamp(
                count.cancelled_at
            ),
        "notes":
            count.notes,
        "adjustment": (
            {
                "id": str(
                    adjustment.id
                ),
                "adjustment_number":
                    adjustment.adjustment_number,
            }
            if adjustment
            else None
        ),
        "summary":
            stock_count_summary(
                **item_counts,
                expose_variance=(
                    not open_blind
                ),
            ),
        "created_at":
            _timestamp(
                count.created_at
            ),
        "updated_at":
            _timestamp(
                count.updated_at
            ),
    }
