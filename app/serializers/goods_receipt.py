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


def _nullable_decimal(value) -> str | None:
    return str(value) if value is not None else None


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

        "supplier_invoice_number": receipt.supplier_invoice_number,
        "supplier_invoice_date": _date(receipt.supplier_invoice_date),
        "payment_terms": receipt.payment_terms,
        "invoice_currency": receipt.invoice_currency,

        "supplier_subtotal": _nullable_decimal(receipt.supplier_subtotal),
        "supplier_discount_total": _nullable_decimal(
            receipt.supplier_discount_total
        ),
        "supplier_tax_total": _nullable_decimal(receipt.supplier_tax_total),
        "supplier_invoice_total": _nullable_decimal(
            receipt.supplier_invoice_total
        ),

        "calculated_subtotal": _nullable_decimal(
            receipt.calculated_subtotal
        ),
        "calculated_tax_total": _nullable_decimal(
            receipt.calculated_tax_total
        ),
        "calculated_total": _nullable_decimal(
            receipt.calculated_total
        ),
        "reconciliation_difference": _nullable_decimal(
            receipt.reconciliation_difference
        ),

        "created_by": receipt.created_by,
        "receiving_started_at": _timestamp(
            receipt.receiving_started_at
        ),
        "receiving_started_by": receipt.receiving_started_by,
        "under_review_at": _timestamp(receipt.under_review_at),
        "under_review_by": receipt.under_review_by,
        "approved_at": _timestamp(receipt.approved_at),
        "approved_by": receipt.approved_by,
        "posted_at": _timestamp(receipt.posted_at),
        "posted_by": receipt.posted_by,
        "cancelled_at": _timestamp(receipt.cancelled_at),
        "cancelled_by": receipt.cancelled_by,

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

                "invoiced_quantity": _nullable_decimal(
                    item.invoiced_quantity
                ),
                "received_quantity": _nullable_decimal(
                    item.received_quantity
                ),
                "accepted_quantity": _nullable_decimal(
                    item.accepted_quantity
                ),
                "rejected_quantity": _nullable_decimal(
                    item.rejected_quantity
                ),
                "bonus_quantity": _nullable_decimal(
                    item.bonus_quantity
                ),

                "base_quantity": _decimal(
                    getattr(item, "base_quantity", None)
                ),
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

                "supplier_item_code": item.supplier_item_code,
                "supplier_description": item.supplier_description,

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
                "base_unit_cost": _decimal(
                    getattr(item, "base_unit_cost", None)
                ),

                "supplier_unit_price": _nullable_decimal(
                    item.supplier_unit_price
                ),
                "discount_percent": _nullable_decimal(
                    item.discount_percent
                ),
                "discount_amount": _nullable_decimal(
                    item.discount_amount
                ),
                "tax_rate": _nullable_decimal(item.tax_rate),
                "tax_amount": _nullable_decimal(item.tax_amount),
                "net_unit_cost": _nullable_decimal(item.net_unit_cost),
                "line_total": _nullable_decimal(item.line_total),

                "discrepancy_status": item.discrepancy_status,
                "discrepancy_reason": item.discrepancy_reason,

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
