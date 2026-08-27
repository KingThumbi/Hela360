from __future__ import annotations

from app.models import (
    GoodsReceipt,
    GoodsReceiptItem,
    InventoryBatch,
    Product,
    Supplier,
    Warehouse,
)


def _timestamp(value) -> str | None:
    return value.isoformat() if value else None


def _date(value) -> str | None:
    return value.isoformat() if value else None


def _decimal(value) -> str:
    return str(value) if value is not None else "0"


def serialize_goods_receipt(
    receipt: GoodsReceipt,
    *,
    warehouse: Warehouse,
    supplier: Supplier | None,
    received_by: dict | None,
    items: list[tuple[GoodsReceiptItem, Product, InventoryBatch | None]],
) -> dict:
    return {
        "id": str(receipt.id),
        "receipt_number": receipt.receipt_number,
        "warehouse": {
            "id": str(warehouse.id),
            "code": warehouse.code,
            "name": warehouse.name,
        },
        "supplier": (
            {
                "id": str(supplier.id),
                "supplier_code": supplier.supplier_code,
                "name": supplier.name,
            }
            if supplier
            else None
        ),
        "supplier_reference": receipt.supplier_reference,
        "received_at": _timestamp(receipt.received_at),
        "status": receipt.status,
        "notes": receipt.notes,
        "received_by": (
            {
                "id": str(received_by["id"]),
                "name": " ".join(
                    part
                    for part in [
                        received_by["first_name"],
                        received_by["last_name"],
                    ]
                    if part
                )
                or None,
                "username": received_by["username"],
            }
            if received_by
            else None
        ),
        "items": [
            {
                "id": str(item.id),
                "line_number": item.line_number,
                "product": {
                    "id": str(product.id),
                    "internal_sku": product.internal_sku,
                    "name": product.name,
                },
                "quantity": _decimal(item.quantity),
                "base_quantity": _decimal(getattr(item, "base_quantity", None)),
                "product_unit_id": (
                    str(item.product_unit_id)
                    if getattr(item, "product_unit_id", None)
                    else None
                ),
                "unit_code": getattr(item, "unit_code_snapshot", None),
                "unit_name": getattr(item, "unit_name_snapshot", None),
                "conversion_factor_to_base": _decimal(
                    getattr(item, "conversion_factor_to_base", None)
                ),
                "batch": (
                    {
                        "id": str(batch.id),
                        "batch_number": batch.batch_number,
                        "expiry_date": _date(batch.expiry_date),
                    }
                    if batch
                    else None
                ),
                "batch_number": item.batch_number,
                "manufacture_date": _date(item.manufacture_date),
                "expiry_date": _date(item.expiry_date),
                "unit_cost": _decimal(item.unit_cost),
                "base_unit_cost": _decimal(getattr(item, "base_unit_cost", None)),
                "supplier_batch_reference": item.supplier_batch_reference,
            }
            for item, product, batch in items
        ],
        "created_at": _timestamp(receipt.created_at),
        "updated_at": _timestamp(receipt.updated_at),
    }


def serialize_goods_receipt_summary(
    receipt: GoodsReceipt,
    *,
    warehouse: Warehouse,
    supplier: Supplier | None,
    received_by: dict | None,
    item_count: int,
    total_cost,
) -> dict:
    return {
        "id": str(receipt.id),
        "receipt_number": receipt.receipt_number,
        "received_at": _timestamp(receipt.received_at),
        "status": receipt.status,
        "warehouse": {
            "id": str(warehouse.id),
            "code": warehouse.code,
            "name": warehouse.name,
        },
        "supplier": (
            {
                "id": str(supplier.id),
                "supplier_code": supplier.supplier_code,
                "name": supplier.name,
            }
            if supplier
            else None
        ),
        "supplier_reference": receipt.supplier_reference,
        "item_count": item_count,
        "total_cost": _decimal(total_cost),
        "received_by": (
            {
                "id": str(received_by["id"]),
                "name": " ".join(
                    part
                    for part in [
                        received_by["first_name"],
                        received_by["last_name"],
                    ]
                    if part
                )
                or None,
                "username": received_by["username"],
            }
            if received_by
            else None
        ),
        "created_at": _timestamp(receipt.created_at),
        "updated_at": _timestamp(receipt.updated_at),
    }
