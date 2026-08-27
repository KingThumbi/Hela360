from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import or_

from app.models import InventoryBatch, InventoryMovement, Product, StockBalance, User, Warehouse


FOURPLACES = Decimal("0.0001")
ALLOWED_STOCK_STATUSES = {
    "in_stock",
    "out_of_stock",
    "low_stock",
    "expired_stock",
}


class InventoryQueryError(ValueError):
    pass


@dataclass(frozen=True)
class InventoryListFilters:
    page: int = 1
    per_page: int = 25
    search: str | None = None
    warehouse_id: str | None = None
    stock_status: str | None = None
    expires_before: date | None = None

    @classmethod
    def from_query(cls, args) -> "InventoryListFilters":
        stock_status = _optional_text(args.get("stock_status"))
        if stock_status and stock_status not in ALLOWED_STOCK_STATUSES:
            raise InventoryQueryError("stock_status is not supported.")

        return cls(
            page=_positive_int(args.get("page"), "page", 1),
            per_page=_positive_int(args.get("per_page"), "per_page", 25),
            search=_optional_text(args.get("search") or args.get("q")),
            warehouse_id=_optional_text(args.get("warehouse_id")),
            stock_status=stock_status,
            expires_before=_parse_date(args.get("expires_before"), "expires_before"),
        )


@dataclass(frozen=True)
class InventoryMovementListFilters:
    page: int = 1
    per_page: int = 25
    date_from: date | None = None
    date_to: date | None = None
    product_id: str | None = None
    warehouse_id: str | None = None
    movement_type: str | None = None
    reference_type: str | None = None
    reference_id: str | None = None

    @classmethod
    def from_query(cls, args) -> "InventoryMovementListFilters":
        return cls(
            page=_positive_int(args.get("page"), "page", 1),
            per_page=_positive_int(args.get("per_page"), "per_page", 25),
            date_from=_parse_date(args.get("date_from"), "date_from"),
            date_to=_parse_date(args.get("date_to"), "date_to"),
            product_id=_optional_text(args.get("product_id")),
            warehouse_id=_optional_text(args.get("warehouse_id")),
            movement_type=_optional_text(args.get("movement_type")),
            reference_type=_optional_text(args.get("reference_type")),
            reference_id=_optional_text(args.get("reference_id")),
        )


def _positive_int(value, field_name: str, default: int) -> int:
    if value in (None, ""):
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise InventoryQueryError(f"{field_name} must be a positive integer.") from exc
    if parsed <= 0:
        raise InventoryQueryError(f"{field_name} must be a positive integer.")
    return parsed


def _optional_text(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _parse_date(value, field_name: str) -> date | None:
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise InventoryQueryError(
            f"{field_name} must be a valid date in YYYY-MM-DD format."
        ) from exc


def _decimal(value) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _q4(value) -> Decimal:
    return _decimal(value).quantize(FOURPLACES, rounding=ROUND_HALF_UP)


def _date(value) -> str | None:
    return value.isoformat() if value else None


def _timestamp(value) -> str | None:
    return value.isoformat() if value else None


def _day_start(value: date) -> datetime:
    return datetime.combine(value, time.min)


def _day_end(value: date) -> datetime:
    return datetime.combine(value, time.max)


def _available_from(on_hand, reserved) -> Decimal:
    return _q4(_decimal(on_hand) - _decimal(reserved))


def _pagination(page: int, per_page: int, total: int) -> dict:
    pages = (total + per_page - 1) // per_page if total else 0
    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages,
        "has_prev": page > 1,
        "has_next": page < pages,
    }


def _batch_is_expired(batch: InventoryBatch, operational_date: date) -> bool:
    return batch.expiry_date is not None and batch.expiry_date < operational_date


def _batch_is_sellable(
    batch: InventoryBatch,
    *,
    product: Product,
    operational_date: date,
) -> bool:
    if (batch.status or "").lower() != "available":
        return False
    if _available_from(batch.quantity_on_hand, batch.quantity_reserved) <= Decimal("0"):
        return False
    if _batch_is_expired(batch, operational_date):
        return False
    if product.track_expiry and batch.expiry_date is None:
        return False
    return True


def _batch_sort_tuple(batch_payload: dict):
    is_expired = bool(batch_payload["is_expired"])
    expiry_date = batch_payload["expiry_date"]
    return (
        is_expired,
        expiry_date is None,
        expiry_date or "9999-12-31",
        batch_payload["batch_number"] or "",
        batch_payload["id"],
    )


class InventoryQueryService:
    def __init__(self, session):
        self.session = session

    def list_stock(
        self,
        *,
        tenant_id: str,
        branch_id: str | None,
        filters: InventoryListFilters,
        operational_date: date | None = None,
    ) -> tuple[list[dict], dict]:
        if not branch_id:
            raise InventoryQueryError("Authenticated user is not assigned to a branch.")

        if filters.warehouse_id:
            self._require_branch_warehouse(
                tenant_id=tenant_id,
                branch_id=branch_id,
                warehouse_id=filters.warehouse_id,
            )

        query = (
            self.session.query(StockBalance, Product, Warehouse)
            .join(Product, Product.id == StockBalance.product_id)
            .join(Warehouse, Warehouse.id == StockBalance.warehouse_id)
            .filter(
                StockBalance.tenant_id == tenant_id,
                StockBalance.branch_id == branch_id,
                Warehouse.tenant_id == tenant_id,
                Warehouse.branch_id == branch_id,
            )
        )

        if filters.warehouse_id:
            query = query.filter(StockBalance.warehouse_id == filters.warehouse_id)

        if filters.search:
            pattern = f"%{filters.search}%"
            query = query.filter(
                or_(
                    Product.name.ilike(pattern),
                    Product.internal_sku.ilike(pattern),
                    Product.generic_name.ilike(pattern),
                    Product.supplier_sku.ilike(pattern),
                )
            )

        rows = query.order_by(
            Product.name.asc(),
            Product.internal_sku.asc(),
            Warehouse.code.asc(),
            StockBalance.id.asc(),
        ).all()

        today = operational_date or date.today()
        stock_ids = [str(stock.id) for stock, _, _ in rows]
        batches_by_stock = self._batches_by_stock(
            tenant_id=tenant_id,
            stock_rows=rows,
        )

        serialized = [
            self._serialize_stock(
                stock=stock,
                product=product,
                warehouse=warehouse,
                batches=batches_by_stock.get(str(stock.id), []),
                operational_date=today,
                expires_before=filters.expires_before,
            )
            for stock, product, warehouse in rows
            if str(stock.id) in stock_ids
        ]

        serialized = [
            item
            for item in serialized
            if self._matches_derived_filters(item, filters)
        ]

        total = len(serialized)
        start = (filters.page - 1) * filters.per_page
        end = start + filters.per_page
        return serialized[start:end], _pagination(filters.page, filters.per_page, total)

    def list_stock_batches(
        self,
        *,
        tenant_id: str,
        branch_id: str | None,
        stock_balance_id: str,
        include_zero: bool = False,
        operational_date: date | None = None,
    ) -> dict:
        if not branch_id:
            raise InventoryQueryError("Authenticated user is not assigned to a branch.")

        row = (
            self.session.query(StockBalance, Product, Warehouse)
            .join(Product, Product.id == StockBalance.product_id)
            .join(Warehouse, Warehouse.id == StockBalance.warehouse_id)
            .filter(
                StockBalance.id == stock_balance_id,
                StockBalance.tenant_id == tenant_id,
                StockBalance.branch_id == branch_id,
                Warehouse.tenant_id == tenant_id,
                Warehouse.branch_id == branch_id,
            )
            .first()
        )
        if not row:
            raise InventoryQueryError("Stock balance not found.")

        stock, product, warehouse = row
        today = operational_date or date.today()
        batches = (
            self.session.query(InventoryBatch)
            .filter(
                InventoryBatch.tenant_id == tenant_id,
                InventoryBatch.warehouse_id == stock.warehouse_id,
                InventoryBatch.product_id == stock.product_id,
            )
            .all()
        )
        payload = [
            self._serialize_batch(
                batch=batch,
                product=product,
                operational_date=today,
            )
            for batch in batches
            if include_zero or _decimal(batch.quantity_on_hand) != Decimal("0")
        ]
        payload.sort(key=_batch_sort_tuple)

        return {
            "stock": self._serialize_stock(
                stock=stock,
                product=product,
                warehouse=warehouse,
                batches=batches,
                operational_date=today,
                expires_before=None,
            ),
            "items": payload,
        }

    def list_movements(
        self,
        *,
        tenant_id: str,
        branch_id: str | None,
        filters: InventoryMovementListFilters,
    ) -> tuple[list[dict], dict]:
        if not branch_id:
            raise InventoryQueryError("Authenticated user is not assigned to a branch.")

        if filters.date_from and filters.date_to and filters.date_from > filters.date_to:
            raise InventoryQueryError("date_from must be before or equal to date_to.")

        if filters.warehouse_id:
            self._require_branch_warehouse(
                tenant_id=tenant_id,
                branch_id=branch_id,
                warehouse_id=filters.warehouse_id,
            )

        if filters.product_id:
            self._require_tenant_product(
                tenant_id=tenant_id,
                product_id=filters.product_id,
            )

        query = (
            self.session.query(
                InventoryMovement,
                Product,
                Warehouse,
                InventoryBatch,
                User.id.label("performed_by_id"),
                User.first_name.label("performed_by_first_name"),
                User.last_name.label("performed_by_last_name"),
                User.username.label("performed_by_username"),
            )
            .join(Product, Product.id == InventoryMovement.product_id)
            .join(Warehouse, Warehouse.id == InventoryMovement.warehouse_id)
            .outerjoin(InventoryBatch, InventoryBatch.id == InventoryMovement.batch_id)
            .outerjoin(User, User.id == InventoryMovement.created_by)
            .filter(
                InventoryMovement.tenant_id == tenant_id,
                InventoryMovement.branch_id == branch_id,
                Product.tenant_id == tenant_id,
                Warehouse.tenant_id == tenant_id,
                Warehouse.branch_id == branch_id,
            )
        )

        if filters.date_from:
            query = query.filter(InventoryMovement.created_at >= _day_start(filters.date_from))
        if filters.date_to:
            query = query.filter(InventoryMovement.created_at <= _day_end(filters.date_to))
        if filters.product_id:
            query = query.filter(InventoryMovement.product_id == filters.product_id)
        if filters.warehouse_id:
            query = query.filter(InventoryMovement.warehouse_id == filters.warehouse_id)
        if filters.movement_type:
            query = query.filter(InventoryMovement.movement_type == filters.movement_type)
        if filters.reference_type:
            query = query.filter(InventoryMovement.reference_type == filters.reference_type)
        if filters.reference_id:
            query = query.filter(InventoryMovement.reference_id == filters.reference_id)

        total = query.count()
        rows = (
            query.order_by(
                InventoryMovement.created_at.desc(),
                InventoryMovement.id.desc(),
            )
            .offset((filters.page - 1) * filters.per_page)
            .limit(filters.per_page)
            .all()
        )

        return [
            self._serialize_movement(
                movement=movement,
                product=product,
                warehouse=warehouse,
                batch=batch,
                performed_by={
                    "id": performed_by_id,
                    "first_name": performed_by_first_name,
                    "last_name": performed_by_last_name,
                    "username": performed_by_username,
                },
            )
            for (
                movement,
                product,
                warehouse,
                batch,
                performed_by_id,
                performed_by_first_name,
                performed_by_last_name,
                performed_by_username,
            ) in rows
        ], _pagination(filters.page, filters.per_page, total)

    def _require_branch_warehouse(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        warehouse_id: str,
    ) -> Warehouse:
        warehouse = (
            self.session.query(Warehouse)
            .filter(
                Warehouse.id == warehouse_id,
                Warehouse.tenant_id == tenant_id,
                Warehouse.branch_id == branch_id,
                Warehouse.is_active.is_(True),
            )
            .first()
        )
        if not warehouse:
            raise InventoryQueryError("warehouse_id is not valid for this branch.")
        return warehouse

    def _require_tenant_product(
        self,
        *,
        tenant_id: str,
        product_id: str,
    ) -> Product:
        product = (
            self.session.query(Product)
            .filter(
                Product.id == product_id,
                Product.tenant_id == tenant_id,
            )
            .first()
        )
        if not product:
            raise InventoryQueryError("product_id is not valid for this tenant.")
        return product

    def _batches_by_stock(
        self,
        *,
        tenant_id: str,
        stock_rows,
    ) -> dict[str, list[InventoryBatch]]:
        key_by_product_warehouse = {
            (str(stock.product_id), str(stock.warehouse_id)): str(stock.id)
            for stock, _, _ in stock_rows
        }
        if not key_by_product_warehouse:
            return {}

        product_ids = {product_id for product_id, _ in key_by_product_warehouse}
        warehouse_ids = {warehouse_id for _, warehouse_id in key_by_product_warehouse}
        batches = (
            self.session.query(InventoryBatch)
            .filter(
                InventoryBatch.tenant_id == tenant_id,
                InventoryBatch.product_id.in_(product_ids),
                InventoryBatch.warehouse_id.in_(warehouse_ids),
            )
            .all()
        )

        grouped: dict[str, list[InventoryBatch]] = {}
        for batch in batches:
            stock_id = key_by_product_warehouse.get(
                (str(batch.product_id), str(batch.warehouse_id))
            )
            if stock_id:
                grouped.setdefault(stock_id, []).append(batch)
        return grouped

    def _serialize_stock(
        self,
        *,
        stock: StockBalance,
        product: Product,
        warehouse: Warehouse,
        batches: list[InventoryBatch],
        operational_date: date,
        expires_before: date | None,
    ) -> dict:
        non_zero_batches = [
            batch
            for batch in batches
            if _decimal(batch.quantity_on_hand) != Decimal("0")
        ]
        expired_batches = [
            batch
            for batch in non_zero_batches
            if _batch_is_expired(batch, operational_date)
        ]
        sellable_batches = [
            batch
            for batch in non_zero_batches
            if _batch_is_sellable(
                batch,
                product=product,
                operational_date=operational_date,
            )
        ]
        expiring_batches = [
            batch
            for batch in sellable_batches
            if expires_before is not None
            and batch.expiry_date is not None
            and batch.expiry_date <= expires_before
        ]

        available = _q4(stock.quantity_available)
        reorder_level = _q4(product.reorder_level)
        is_out_of_stock = available <= Decimal("0")
        is_low_stock = not is_out_of_stock and reorder_level > Decimal("0") and available <= reorder_level

        earliest_sellable_expiry = min(
            (
                batch.expiry_date
                for batch in sellable_batches
                if batch.expiry_date is not None
            ),
            default=None,
        )

        return {
            "id": str(stock.id),
            "product": {
                "id": str(product.id),
                "internal_sku": product.internal_sku,
                "supplier_sku": product.supplier_sku,
                "name": product.name,
                "generic_name": product.generic_name,
                "track_inventory": bool(product.track_inventory),
                "track_batches": bool(product.track_batches),
                "track_expiry": bool(product.track_expiry),
                "requires_prescription": bool(product.requires_prescription),
                "reorder_level": str(_q4(product.reorder_level)),
                "reorder_qty": str(_q4(product.reorder_qty)),
                "is_active": bool(product.is_active),
            },
            "warehouse": {
                "id": str(warehouse.id),
                "branch_id": str(warehouse.branch_id),
                "code": warehouse.code,
                "name": warehouse.name,
                "warehouse_type": warehouse.warehouse_type,
                "is_active": bool(warehouse.is_active),
            },
            "quantity_on_hand": str(_q4(stock.quantity_on_hand)),
            "quantity_reserved": str(_q4(stock.quantity_reserved)),
            "quantity_available": str(available),
            "sellable_quantity": str(
                _q4(
                    sum(
                        _available_from(batch.quantity_on_hand, batch.quantity_reserved)
                        for batch in sellable_batches
                    )
                )
            ),
            "expired_quantity": str(
                _q4(
                    sum(_decimal(batch.quantity_on_hand) for batch in expired_batches)
                )
            ),
            "batch_count": len(non_zero_batches),
            "expired_batch_count": len(expired_batches),
            "expiring_batch_count": len(expiring_batches),
            "earliest_sellable_expiry_date": _date(earliest_sellable_expiry),
            "has_expired_stock": len(expired_batches) > 0,
            "has_expiring_stock": len(expiring_batches) > 0,
            "is_low_stock": is_low_stock,
            "is_out_of_stock": is_out_of_stock,
            "created_at": _timestamp(stock.created_at),
            "updated_at": _timestamp(stock.updated_at),
        }

    def _serialize_batch(
        self,
        *,
        batch: InventoryBatch,
        product: Product,
        operational_date: date,
    ) -> dict:
        quantity_available = _available_from(
            batch.quantity_on_hand,
            batch.quantity_reserved,
        )
        is_expired = _batch_is_expired(batch, operational_date)
        is_sellable = _batch_is_sellable(
            batch,
            product=product,
            operational_date=operational_date,
        )
        days_to_expiry = (
            (batch.expiry_date - operational_date).days
            if batch.expiry_date is not None
            else None
        )

        return {
            "id": str(batch.id),
            "batch_number": batch.batch_number,
            "expiry_date": _date(batch.expiry_date),
            "manufacture_date": _date(batch.manufacture_date),
            "received_at": _timestamp(batch.received_at),
            "quantity_on_hand": str(_q4(batch.quantity_on_hand)),
            "quantity_reserved": str(_q4(batch.quantity_reserved)),
            "quantity_available": str(quantity_available),
            "status": batch.status,
            "is_expired": is_expired,
            "is_sellable": is_sellable,
            "days_to_expiry": days_to_expiry,
            "created_at": _timestamp(batch.created_at),
            "updated_at": _timestamp(batch.updated_at),
        }

    def _serialize_movement(
        self,
        *,
        movement: InventoryMovement,
        product: Product,
        warehouse: Warehouse,
        batch: InventoryBatch | None,
        performed_by: dict,
    ) -> dict:
        name = None
        if performed_by["id"]:
            name = " ".join(
                part
                for part in [
                    performed_by["first_name"],
                    performed_by["last_name"],
                ]
                if part
            ) or None

        return {
            "id": str(movement.id),
            "movement_type": movement.movement_type,
            "quantity": str(_q4(movement.quantity)),
            "product": {
                "id": str(product.id),
                "internal_sku": product.internal_sku,
                "name": product.name,
                "generic_name": product.generic_name,
            },
            "warehouse": {
                "id": str(warehouse.id),
                "code": warehouse.code,
                "name": warehouse.name,
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
            "sale_item_id": str(movement.sale_item_id) if movement.sale_item_id else None,
            "reference": {
                "type": movement.reference_type,
                "id": str(movement.reference_id),
            },
            "performed_by": (
                {
                    "id": str(performed_by["id"]),
                    "name": name,
                    "username": performed_by["username"],
                }
                if performed_by["id"]
                else None
            ),
            "created_at": _timestamp(movement.created_at),
        }

    def _matches_derived_filters(
        self,
        item: dict,
        filters: InventoryListFilters,
    ) -> bool:
        if filters.stock_status == "in_stock" and item["is_out_of_stock"]:
            return False
        if filters.stock_status == "out_of_stock" and not item["is_out_of_stock"]:
            return False
        if filters.stock_status == "low_stock" and not item["is_low_stock"]:
            return False
        if filters.stock_status == "expired_stock" and not item["has_expired_stock"]:
            return False
        if filters.expires_before is not None and not item["has_expiring_stock"]:
            return False
        return True
