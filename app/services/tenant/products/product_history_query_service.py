from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func

from app.models import (
    Customer,
    GoodsReceipt,
    GoodsReceiptItem,
    InventoryBatch,
    InventoryMovement,
    Product,
    ProductUnit,
    Sale,
    SaleItem,
    StockBalance,
    Supplier,
    Warehouse,
    StockAdjustment,
    StockAdjustmentItem,
    StockCount,
    StockCountItem,
    User,
)
from app.serializers.stock_count import serialize_stock_count_item


ZERO_QTY = Decimal("0.0000")


@dataclass(frozen=True)
class ProductSalesHistoryFilters:
    page: int = 1
    per_page: int = 25
    date_from: datetime | None = None
    date_to: datetime | None = None
    status: str | None = None
    customer_id: str | None = None
    warehouse_id: str | None = None


@dataclass(frozen=True)
class ProductPurchaseHistoryFilters:
    page: int = 1
    per_page: int = 25
    date_from: date | None = None
    date_to: date | None = None
    warehouse_id: str | None = None
    supplier_id: str | None = None




@dataclass(frozen=True)
class ProductStockCountHistoryFilters:
    page: int = 1
    per_page: int = 25
    date_from: date | None = None
    date_to: date | None = None
    warehouse_id: str | None = None

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

    def list_purchases(
        self,
        *,
        tenant_id: str,
        branch_id: str | None,
        product_id: str,
        filters: ProductPurchaseHistoryFilters,
    ) -> tuple[list[dict], dict] | None:
        if not branch_id:
            raise ValueError(
                "Authenticated user is not assigned to a branch."
            )

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

        if (
            filters.date_from
            and filters.date_to
            and filters.date_from > filters.date_to
        ):
            raise ValueError(
                "date_from must be before or equal to date_to."
            )

        if filters.warehouse_id:
            warehouse = (
                self.session.query(Warehouse)
                .filter(
                    Warehouse.id == filters.warehouse_id,
                    Warehouse.tenant_id == tenant_id,
                    Warehouse.branch_id == branch_id,
                )
                .first()
            )
            if warehouse is None:
                raise ValueError(
                    "warehouse_id is not valid for this branch."
                )

        if filters.supplier_id:
            supplier = (
                self.session.query(Supplier)
                .filter(
                    Supplier.id == filters.supplier_id,
                    Supplier.tenant_id == tenant_id,
                )
                .first()
            )
            if supplier is None:
                raise ValueError(
                    "supplier_id is not valid for this tenant."
                )

        query = (
            self.session.query(
                GoodsReceiptItem,
                GoodsReceipt,
                Warehouse,
                Supplier,
            )
            .join(
                GoodsReceipt,
                GoodsReceipt.id
                == GoodsReceiptItem.goods_receipt_id,
            )
            .join(
                Warehouse,
                Warehouse.id == GoodsReceipt.warehouse_id,
            )
            .outerjoin(
                Supplier,
                Supplier.id == GoodsReceipt.supplier_id,
            )
            .filter(
                GoodsReceiptItem.product_id == product_id,
                GoodsReceipt.tenant_id == tenant_id,
                GoodsReceipt.branch_id == branch_id,
                GoodsReceipt.status == "posted",
                GoodsReceipt.posted_at.isnot(None),
                Warehouse.tenant_id == tenant_id,
                Warehouse.branch_id == branch_id,
            )
        )

        if filters.date_from:
            query = query.filter(
                GoodsReceipt.posted_at
                >= datetime.combine(
                    filters.date_from,
                    time.min,
                )
            )

        if filters.date_to:
            query = query.filter(
                GoodsReceipt.posted_at
                <= datetime.combine(
                    filters.date_to,
                    time.max,
                )
            )

        if filters.warehouse_id:
            query = query.filter(
                GoodsReceipt.warehouse_id
                == filters.warehouse_id
            )

        if filters.supplier_id:
            query = query.filter(
                GoodsReceipt.supplier_id
                == filters.supplier_id
            )

        total = query.count()

        rows = (
            query.order_by(
                GoodsReceipt.posted_at.desc(),
                GoodsReceipt.id.desc(),
                GoodsReceiptItem.line_number.asc(),
                GoodsReceiptItem.id.asc(),
            )
            .offset(
                (filters.page - 1)
                * filters.per_page
            )
            .limit(filters.per_page)
            .all()
        )

        pages = (
            (total + filters.per_page - 1)
            // filters.per_page
            if total
            else 0
        )

        items = [
            {
                "receipt_item_id": str(receipt_item.id),
                "receipt": {
                    "id": str(receipt.id),
                    "receipt_number": receipt.receipt_number,
                    "status": receipt.status,
                    "received_at": (
                        receipt.received_at.isoformat()
                        if receipt.received_at
                        else None
                    ),
                    "posted_at": (
                        receipt.posted_at.isoformat()
                        if receipt.posted_at
                        else None
                    ),
                    "supplier_reference": (
                        receipt.supplier_reference
                    ),
                    "supplier_invoice_number": (
                        receipt.supplier_invoice_number
                    ),
                    "supplier_invoice_date": (
                        receipt.supplier_invoice_date.isoformat()
                        if receipt.supplier_invoice_date
                        else None
                    ),
                    "invoice_currency": (
                        receipt.invoice_currency
                    ),
                },
                "warehouse": {
                    "id": str(warehouse.id),
                    "code": warehouse.code,
                    "name": warehouse.name,
                },
                "supplier": (
                    {
                        "id": str(supplier.id),
                        "supplier_code": (
                            supplier.supplier_code
                        ),
                        "name": supplier.name,
                    }
                    if supplier
                    else None
                ),
                "line_number": receipt_item.line_number,
                "quantity": str(receipt_item.quantity),
                "base_quantity": str(
                    receipt_item.base_quantity
                ),
                "uom": {
                    "code": (
                        receipt_item.unit_code_snapshot
                    ),
                    "name": (
                        receipt_item.unit_name_snapshot
                    ),
                    "conversion_factor_to_base": str(
                        receipt_item
                        .conversion_factor_to_base
                    ),
                },
                "unit_cost": str(receipt_item.unit_cost),
                "base_unit_cost": str(
                    receipt_item.base_unit_cost
                ),
                "batch": {
                    "id": (
                        str(receipt_item.batch_id)
                        if receipt_item.batch_id
                        else None
                    ),
                    "batch_number": (
                        receipt_item.batch_number
                    ),
                    "manufacture_date": (
                        receipt_item.manufacture_date.isoformat()
                        if receipt_item.manufacture_date
                        else None
                    ),
                    "expiry_date": (
                        receipt_item.expiry_date.isoformat()
                        if receipt_item.expiry_date
                        else None
                    ),
                },
            }
            for (
                receipt_item,
                receipt,
                warehouse,
                supplier,
            ) in rows
        ]

        return items, {
            "page": filters.page,
            "per_page": filters.per_page,
            "total": total,
            "pages": pages,
            "has_prev": filters.page > 1,
            "has_next": filters.page < pages,
        }

    def list_sales(
        self,
        *,
        tenant_id: str,
        branch_id: str | None,
        product_id: str,
        filters: ProductSalesHistoryFilters,
    ) -> tuple[list[dict], dict] | None:
        if not branch_id:
            raise ValueError(
                "Authenticated user is not assigned to a branch."
            )

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

        if (
            filters.date_from
            and filters.date_to
            and filters.date_from > filters.date_to
        ):
            raise ValueError(
                "date_from must be before or equal to date_to."
            )

        if filters.warehouse_id:
            warehouse = (
                self.session.query(Warehouse)
                .filter(
                    Warehouse.id == filters.warehouse_id,
                    Warehouse.tenant_id == tenant_id,
                    Warehouse.branch_id == branch_id,
                )
                .first()
            )

            if warehouse is None:
                raise ValueError(
                    "warehouse_id is not valid for this branch."
                )

        if filters.customer_id:
            customer = (
                self.session.query(Customer)
                .filter(
                    Customer.id == filters.customer_id,
                    Customer.tenant_id == tenant_id,
                )
                .first()
            )

            if customer is None:
                raise ValueError(
                    "customer_id is not valid."
                )

        query = (
            self.session.query(
                SaleItem,
                Sale,
                Warehouse,
                Customer,
                InventoryBatch,
            )
            .join(
                Sale,
                Sale.id == SaleItem.sale_id,
            )
            .join(
                Warehouse,
                Warehouse.id == Sale.warehouse_id,
            )
            .outerjoin(
                Customer,
                (Customer.id == Sale.customer_id)
                & (Customer.tenant_id == Sale.tenant_id),
            )
            .outerjoin(
                InventoryBatch,
                InventoryBatch.id == SaleItem.batch_id,
            )
            .filter(
                SaleItem.product_id == product_id,
                Sale.tenant_id == tenant_id,
                Sale.branch_id == branch_id,
                Warehouse.tenant_id == tenant_id,
                Warehouse.branch_id == branch_id,
            )
        )

        if filters.date_from:
            query = query.filter(
                Sale.sale_date >= filters.date_from
            )

        if filters.date_to:
            query = query.filter(
                Sale.sale_date <= filters.date_to
            )

        if filters.status:
            query = query.filter(
                Sale.status == filters.status
            )

        if filters.customer_id:
            query = query.filter(
                Sale.customer_id == filters.customer_id
            )

        if filters.warehouse_id:
            query = query.filter(
                Sale.warehouse_id == filters.warehouse_id
            )

        total = query.count()

        rows = (
            query.order_by(
                Sale.sale_date.desc(),
                Sale.id.desc(),
                SaleItem.id.asc(),
            )
            .offset(
                (filters.page - 1)
                * filters.per_page
            )
            .limit(filters.per_page)
            .all()
        )

        pages = (
            (total + filters.per_page - 1)
            // filters.per_page
            if total
            else 0
        )

        items = []

        for (
            sale_item,
            sale,
            warehouse,
            customer,
            batch,
        ) in rows:
            conversion_factor = Decimal(
                sale_item.conversion_factor_to_base or 1
            )

            normalized_unit_price = None

            if conversion_factor > 0:
                normalized_unit_price = (
                    Decimal(sale_item.unit_price)
                    / conversion_factor
                ).quantize(
                    Decimal("0.000001"),
                    rounding=ROUND_HALF_UP,
                )

            items.append(
                {
                    "sale_item_id": str(sale_item.id),
                    "sale": {
                        "id": str(sale.id),
                        "sale_number": sale.sale_number,
                        "sale_date": (
                            sale.sale_date.isoformat()
                            if sale.sale_date
                            else None
                        ),
                        "status": sale.status,
                        "sale_channel": sale.sale_channel,
                        "refund_status": sale.refund_status,
                        "refunded_amount": str(
                            sale.refunded_amount
                        ),
                    },
                    "warehouse": {
                        "id": str(warehouse.id),
                        "code": warehouse.code,
                        "name": warehouse.name,
                    },
                    "customer": (
                        {
                            "id": str(customer.id),
                            "customer_number": (
                                customer.customer_number
                            ),
                            "first_name": customer.first_name,
                            "last_name": customer.last_name,
                            "other_names": customer.other_names,
                            "phone": customer.phone,
                        }
                        if customer
                        else None
                    ),
                    "quantity": str(sale_item.quantity),
                    "base_quantity": str(
                        sale_item.base_quantity
                    ),
                    "uom": {
                        "code": (
                            sale_item.unit_code_snapshot
                        ),
                        "name": (
                            sale_item.unit_name_snapshot
                        ),
                        "conversion_factor_to_base": str(
                            sale_item
                            .conversion_factor_to_base
                        ),
                    },
                    "unit_price": str(
                        sale_item.unit_price
                    ),
                    "normalized_base_unit_price": (
                        str(normalized_unit_price)
                        if normalized_unit_price
                        is not None
                        else None
                    ),
                    "discount_amount": str(
                        sale_item.discount_amount
                    ),
                    "tax_amount": str(
                        sale_item.tax_amount
                    ),
                    "line_total": str(
                        sale_item.line_total
                    ),
                    "is_returned": bool(
                        sale_item.is_returned
                    ),
                    "batch": (
                        {
                            "id": str(batch.id),
                            "batch_number": (
                                batch.batch_number
                            ),
                            "expiry_date": (
                                batch.expiry_date.isoformat()
                                if batch.expiry_date
                                else None
                            ),
                        }
                        if batch
                        else (
                            {
                                "id": str(
                                    sale_item.batch_id
                                ),
                                "batch_number": None,
                                "expiry_date": None,
                            }
                            if sale_item.batch_id
                            else None
                        )
                    ),
                }
            )

        return items, {
            "page": filters.page,
            "per_page": filters.per_page,
            "total": total,
            "pages": pages,
            "has_prev": filters.page > 1,
            "has_next": filters.page < pages,
        }

    def list_stock_counts(
        self,
        *,
        tenant_id: str,
        branch_id: str | None,
        product_id: str,
        filters: ProductStockCountHistoryFilters,
    ) -> tuple[list[dict], dict] | None:
        """
        Return physical Stock Count evidence for one Product.

        Each result represents one StockCountItem rather than one
        StockCount header. This preserves batch-level and UOM-level
        historical evidence and permits exact linkage to the
        StockAdjustmentItem that posted the variance.

        Open blind counts deliberately hide system-derived quantities,
        matching the canonical Stock Count serializer contract.
        """
        if not branch_id:
            raise ValueError(
                "Authenticated user is not assigned to a branch."
            )

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

        if (
            filters.date_from
            and filters.date_to
            and filters.date_from > filters.date_to
        ):
            raise ValueError(
                "date_from must be before or equal to date_to."
            )

        if filters.warehouse_id:
            warehouse = (
                self.session.query(Warehouse)
                .filter(
                    Warehouse.id == filters.warehouse_id,
                    Warehouse.tenant_id == tenant_id,
                    Warehouse.branch_id == branch_id,
                )
                .first()
            )

            if warehouse is None:
                raise ValueError(
                    "warehouse_id is not valid for this branch."
                )

        query = (
            self.session.query(
                StockCountItem,
                StockCount,
                Warehouse,
                InventoryBatch,
                User.id.label("counted_by_id"),
                User.first_name.label(
                    "counted_by_first_name"
                ),
                User.last_name.label(
                    "counted_by_last_name"
                ),
                User.username.label(
                    "counted_by_username"
                ),
                StockAdjustment,
                StockAdjustmentItem,
            )
            .join(
                StockCount,
                StockCount.id
                == StockCountItem.stock_count_id,
            )
            .join(
                Warehouse,
                Warehouse.id
                == StockCount.warehouse_id,
            )
            .outerjoin(
                InventoryBatch,
                InventoryBatch.id
                == StockCountItem.batch_id,
            )
            .outerjoin(
                User,
                User.id
                == StockCountItem.counted_by,
            )
            .outerjoin(
                StockAdjustment,
                (
                    StockAdjustment.tenant_id
                    == tenant_id
                )
                & (
                    StockAdjustment.branch_id
                    == branch_id
                )
                & (
                    StockAdjustment.source_type
                    == "stock_count"
                )
                & (
                    StockAdjustment.source_id
                    == StockCount.id
                ),
            )
            .outerjoin(
                StockAdjustmentItem,
                (
                    StockAdjustmentItem.stock_adjustment_id
                    == StockAdjustment.id
                )
                & (
                    StockAdjustmentItem.stock_count_item_id
                    == StockCountItem.id
                ),
            )
            .filter(
                StockCountItem.product_id
                == product_id,
                StockCount.tenant_id
                == tenant_id,
                StockCount.branch_id
                == branch_id,
                Warehouse.tenant_id
                == tenant_id,
                Warehouse.branch_id
                == branch_id,
            )
        )

        if filters.warehouse_id:
            query = query.filter(
                StockCount.warehouse_id
                == filters.warehouse_id
            )

        if filters.date_from:
            query = query.filter(
                StockCount.started_at
                >= datetime.combine(
                    filters.date_from,
                    time.min,
                )
            )

        if filters.date_to:
            query = query.filter(
                StockCount.started_at
                <= datetime.combine(
                    filters.date_to,
                    time.max,
                )
            )

        total = query.count()

        pages = (
            (total + filters.per_page - 1)
            // filters.per_page
            if total
            else 0
        )

        rows = (
            query.order_by(
                StockCount.started_at.desc(),
                StockCount.id.desc(),
                StockCountItem.line_number.asc(),
            )
            .offset(
                (filters.page - 1)
                * filters.per_page
            )
            .limit(filters.per_page)
            .all()
        )

        count_ids = {
            count.id
            for (
                _count_item,
                count,
                _warehouse,
                _batch,
                _counted_by_id,
                _counted_by_first_name,
                _counted_by_last_name,
                _counted_by_username,
                _adjustment,
                _adjustment_item,
            ) in rows
        }

        variance_count_ids = set()

        if count_ids:
            variance_count_ids = {
                stock_count_id
                for (stock_count_id,) in (
                    self.session.query(
                        StockCountItem.stock_count_id
                    )
                    .filter(
                        StockCountItem.stock_count_id.in_(
                            count_ids
                        ),
                        StockCountItem.variance_quantity
                        != ZERO_QTY,
                    )
                    .distinct()
                    .all()
                )
            }

        items = []

        for (
            count_item,
            count,
            warehouse,
            batch,
            counted_by_id,
            counted_by_first_name,
            counted_by_last_name,
            counted_by_username,
            adjustment,
            adjustment_item,
        ) in rows:
            open_blind = (
                count.status == "open"
                and count.count_mode == "blind"
            )

            counted_by_context = (
                {
                    "id": str(counted_by_id),
                    "first_name":
                        counted_by_first_name,
                    "last_name":
                        counted_by_last_name,
                    "username":
                        counted_by_username,
                }
                if counted_by_id
                else None
            )

            line = serialize_stock_count_item(
                count_item,
                product=product,
                batch=batch,
                counted_by=counted_by_context,
                expose_system_quantities=(
                    not open_blind
                ),
            )

            if count.status == "open":
                lifecycle = "counting"
            elif count.status == "cancelled":
                lifecycle = "cancelled"
            elif count.status == "superseded":
                lifecycle = "superseded"
            elif count.status == "completed":
                if (
                    adjustment is not None
                    and adjustment.status == "posted"
                ):
                    lifecycle = "posted"
                elif count.id in variance_count_ids:
                    lifecycle = "awaiting_posting"
                else:
                    lifecycle = "completed"
            else:
                lifecycle = count.status

            adjustment_payload = None

            if adjustment is not None:
                adjustment_payload = {
                    "id": str(adjustment.id),
                    "adjustment_number":
                        adjustment.adjustment_number,
                    "status":
                        adjustment.status,
                    "posted_at": (
                        adjustment.posted_at.isoformat()
                        if adjustment.posted_at
                        else None
                    ),
                    "quantity_delta": (
                        str(
                            adjustment_item.quantity_delta
                        )
                        if adjustment_item
                        else None
                    ),
                }

            items.append(
                {
                    "stock_count": {
                        "id": str(count.id),
                        "count_number":
                            count.count_number,
                        "status":
                            count.status,
                        "lifecycle":
                            lifecycle,
                        "count_mode":
                            count.count_mode,
                        "scope_type":
                            count.scope_type,
                        "snapshot_at": (
                            count.snapshot_at.isoformat()
                            if count.snapshot_at
                            else None
                        ),
                        "started_at": (
                            count.started_at.isoformat()
                            if count.started_at
                            else None
                        ),
                        "completed_at": (
                            count.completed_at.isoformat()
                            if count.completed_at
                            else None
                        ),
                    },
                    "warehouse": {
                        "id": str(warehouse.id),
                        "code": warehouse.code,
                        "name": warehouse.name,
                    },
                    "line": line,
                    "adjustment":
                        adjustment_payload,
                }
            )

        return items, {
            "page": filters.page,
            "per_page": filters.per_page,
            "total": total,
            "pages": pages,
            "has_prev": filters.page > 1,
            "has_next": filters.page < pages,
        }
