from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timezone
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json

from sqlalchemy import func, inspect

from app.errors import ConflictError, NotFoundError, ValidationError
from app.models import (
    InventoryBatch,
    InventoryMovement,
    Product,
    StockBalance,
    StockAdjustment,
    StockCount,
    StockCountItem,
    User,
    Warehouse,
)
from app.schemas import (
    AddDiscoveredStockCountItemRequest,
    CreateStockCountRequest,
    UpdateStockCountItemRequest,
)
from app.serializers import serialize_stock_count, serialize_stock_count_summary


FOURPLACES = Decimal("0.0001")
OPEN_STATUS = "open"
COMPLETED_STATUS = "completed"
CANCELLED_STATUS = "cancelled"


class StockCountQueryError(ValueError):
    pass


@dataclass(frozen=True)
class StockCountListFilters:
    page: int = 1
    per_page: int = 25
    status: str | None = None
    warehouse_id: str | None = None
    date_from: date | None = None
    date_to: date | None = None

    @classmethod
    def from_query(cls, args) -> "StockCountListFilters":
        status = _optional_text(args.get("status"))
        if status and status not in {OPEN_STATUS, COMPLETED_STATUS, CANCELLED_STATUS}:
            raise StockCountQueryError("status is not supported.")

        return cls(
            page=_positive_int(args.get("page"), "page", 1),
            per_page=_positive_int(args.get("per_page"), "per_page", 25),
            status=status,
            warehouse_id=_optional_text(args.get("warehouse_id")),
            date_from=_parse_date(args.get("date_from"), "date_from"),
            date_to=_parse_date(args.get("date_to"), "date_to"),
        )


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _d(value) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _q4(value) -> Decimal:
    return _d(value).quantize(FOURPLACES, rounding=ROUND_HALF_UP)


def _positive_int(value, field_name: str, default: int) -> int:
    if value in (None, ""):
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise StockCountQueryError(
            f"{field_name} must be a positive integer."
        ) from exc
    if parsed <= 0:
        raise StockCountQueryError(f"{field_name} must be a positive integer.")
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
        raise StockCountQueryError(
            f"{field_name} must be a valid date in YYYY-MM-DD format."
        ) from exc


def _day_start(value: date) -> datetime:
    return datetime.combine(value, time.min)


def _day_end(value: date) -> datetime:
    return datetime.combine(value, time.max)


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


def _json_safe(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    return value


def _fingerprint(request: CreateStockCountRequest) -> str:
    payload = _json_safe(asdict(request))
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class StockCountService:
    def __init__(self, session):
        self.session = session

    def create_stock_count(
        self,
        *,
        tenant_id: str,
        branch_id: str | None,
        started_by: str,
        request: CreateStockCountRequest,
    ) -> StockCount:
        if not branch_id:
            raise ValidationError("Authenticated user is not assigned to a branch.")

        fingerprint = _fingerprint(request)
        existing = self._existing_by_idempotency_key(
            tenant_id=tenant_id,
            idempotency_key=request.idempotency_key,
        )
        if existing:
            if existing.request_fingerprint != fingerprint:
                raise ConflictError(
                    "idempotency_key was already used for a different stock count."
                )
            return existing

        now = _now()
        try:
            warehouse = self._require_warehouse(
                tenant_id=tenant_id,
                branch_id=branch_id,
                warehouse_id=request.warehouse_id,
            )
            self._ensure_no_open_count(
                tenant_id=tenant_id,
                branch_id=branch_id,
                warehouse_id=str(warehouse.id),
            )
            products = self._load_products(
                tenant_id=tenant_id,
                product_ids=list(request.product_ids),
            )
            rows = self._snapshot_rows(
                tenant_id=tenant_id,
                branch_id=branch_id,
                warehouse_id=str(warehouse.id),
                selected_products=products,
            )
            if not rows:
                raise ValidationError("Stock count scope has no countable stock lines.")

            count = StockCount(
                tenant_id=tenant_id,
                branch_id=branch_id,
                warehouse_id=str(warehouse.id),
                count_number="PENDING",
                idempotency_key=request.idempotency_key,
                request_fingerprint=fingerprint,
                scope_type="selected" if request.product_ids else "full",
                count_mode=request.count_mode,
                status=OPEN_STATUS,
                snapshot_at=now,
                started_at=now,
                started_by=started_by,
                notes=request.notes,
                created_at=now,
                updated_at=now,
            )
            self.session.add(count)
            self.session.flush()
            count.count_number = self._count_number(count, now)

            for line_number, row in enumerate(rows, start=1):
                self.session.add(
                    StockCountItem(
                        stock_count_id=str(count.id),
                        product_id=str(row["product"].id),
                        batch_id=str(row["batch"].id) if row["batch"] else None,
                        source_type="snapshot",
                        line_number=line_number,
                        snapshot_quantity=_q4(row["quantity"]),
                        expected_quantity=_q4(row["quantity"]),
                        created_at=now,
                        updated_at=now,
                    )
                )

            self.session.commit()
            return count
        except Exception:
            self.session.rollback()
            raise

    def add_discovered_item(
        self,
        *,
        tenant_id: str,
        branch_id: str | None,
        count_id: str,
        counted_by: str,
        request: AddDiscoveredStockCountItemRequest,
    ) -> StockCountItem:
        """
        Add a physical stock line discovered during an open stock count.

        Discovered lines represent stock physically observed by the counter
        that was not represented by an appropriate snapshot line.

        For batch- or expiry-tracked products, physical identity is determined
        by product + normalized batch number + expiry date within the count.

        Non-batch/non-expiry products must use their existing snapshot line
        rather than creating arbitrary duplicate discovered lines.
        """

        if not branch_id:
            raise ValidationError(
                "Authenticated user is not assigned to a branch."
            )

        now = _now()

        try:
            count = self._locked_count(
                tenant_id=tenant_id,
                branch_id=branch_id,
                count_id=count_id,
            )
            self._ensure_open(count)

            products = self._load_products(
                tenant_id=tenant_id,
                product_ids=[request.product_id],
            )
            product = products[request.product_id]

            tracks_batches = bool(product.track_batches)
            tracks_expiry = bool(product.track_expiry)

            batch_number = (
                request.batch_number.strip()
                if request.batch_number
                else None
            )
            expiry_date = request.expiry_date

            if tracks_batches and not batch_number:
                raise ValidationError(
                    "batch_number is required for this product."
                )

            if tracks_expiry and expiry_date is None:
                raise ValidationError(
                    "expiry_date is required for this product."
                )

            if not tracks_batches and batch_number:
                raise ValidationError(
                    "batch_number is not allowed for a product "
                    "that does not track batches."
                )

            if not tracks_expiry and expiry_date is not None:
                raise ValidationError(
                    "expiry_date is not allowed for a product "
                    "that does not track expiry."
                )

            existing_lines = (
                self.session.query(StockCountItem)
                .filter(
                    StockCountItem.stock_count_id == str(count.id),
                    StockCountItem.product_id == str(product.id),
                )
                .with_for_update()
                .all()
            )

            if not tracks_batches and not tracks_expiry:
                if existing_lines:
                    raise ConflictError(
                        "This product already has a stock count line. "
                        "Update the existing line instead."
                    )

            else:
                normalized_batch = (
                    batch_number.casefold()
                    if batch_number
                    else None
                )

                for existing in existing_lines:
                    existing_batch = (
                        existing.observed_batch_number
                        if existing.source_type == "discovered"
                        else None
                    )
                    existing_expiry = (
                        existing.observed_expiry_date
                        if existing.source_type == "discovered"
                        else None
                    )

                    if existing.source_type == "snapshot" and existing.batch_id:
                        system_batch = (
                            self.session.query(InventoryBatch)
                            .filter(
                                InventoryBatch.id == existing.batch_id,
                                InventoryBatch.tenant_id == tenant_id,
                                InventoryBatch.product_id == str(product.id),
                                InventoryBatch.warehouse_id
                                == str(count.warehouse_id),
                            )
                            .first()
                        )

                        if system_batch:
                            existing_batch = system_batch.batch_number
                            existing_expiry = system_batch.expiry_date

                    existing_normalized_batch = (
                        existing_batch.strip().casefold()
                        if existing_batch
                        else None
                    )

                    if (
                        existing_normalized_batch == normalized_batch
                        and existing_expiry == expiry_date
                    ):
                        raise ConflictError(
                            "This product batch and expiry already has a "
                            "stock count line. Update the existing line instead."
                        )

            max_line_number = (
                self.session.query(
                    func.max(StockCountItem.line_number)
                )
                .filter(
                    StockCountItem.stock_count_id == str(count.id)
                )
                .scalar()
                or 0
            )

            counted_quantity = _q4(
                request.counted_quantity
            )

            item = StockCountItem(
                stock_count_id=str(count.id),
                product_id=str(product.id),
                batch_id=None,
                source_type="discovered",
                observed_batch_number=batch_number,
                observed_expiry_date=expiry_date,
                line_number=int(max_line_number) + 1,
                snapshot_quantity=Decimal("0.0000"),
                expected_quantity=Decimal("0.0000"),
                counted_quantity=counted_quantity,
                variance_quantity=counted_quantity,
                counted_at=now,
                counted_by=counted_by,
                notes=request.notes,
                created_at=now,
                updated_at=now,
            )

            self.session.add(item)
            self.session.commit()

            return item

        except Exception:
            self.session.rollback()
            raise

    def list_stock_counts(
        self,
        *,
        tenant_id: str,
        branch_id: str | None,
        filters: StockCountListFilters,
    ) -> tuple[list[dict], dict]:
        if not branch_id:
            raise StockCountQueryError("Authenticated user is not assigned to a branch.")
        if filters.date_from and filters.date_to and filters.date_from > filters.date_to:
            raise StockCountQueryError("date_from must be before or equal to date_to.")
        if filters.warehouse_id:
            self._require_warehouse(
                tenant_id=tenant_id,
                branch_id=branch_id,
                warehouse_id=filters.warehouse_id,
            )

        query = (
            self.session.query(
                StockCount,
                Warehouse,
                User.id.label("started_by_id"),
                User.first_name.label("started_by_first_name"),
                User.last_name.label("started_by_last_name"),
                User.username.label("started_by_username"),
            )
            .join(Warehouse, Warehouse.id == StockCount.warehouse_id)
            .outerjoin(User, User.id == StockCount.started_by)
            .filter(
                StockCount.tenant_id == tenant_id,
                StockCount.branch_id == branch_id,
                Warehouse.tenant_id == tenant_id,
                Warehouse.branch_id == branch_id,
            )
        )
        if filters.status:
            query = query.filter(StockCount.status == filters.status)
        if filters.warehouse_id:
            query = query.filter(StockCount.warehouse_id == filters.warehouse_id)
        if filters.date_from:
            query = query.filter(StockCount.started_at >= _day_start(filters.date_from))
        if filters.date_to:
            query = query.filter(StockCount.started_at <= _day_end(filters.date_to))

        total = query.count()
        rows = (
            query.order_by(StockCount.started_at.desc(), StockCount.id.desc())
            .offset((filters.page - 1) * filters.per_page)
            .limit(filters.per_page)
            .all()
        )
        count_ids = [str(count.id) for count, *_ in rows]
        counts_by_id = self._item_counts(count_ids)
        adjustments_by_count_id = self._adjustments_by_count_ids(
            tenant_id=tenant_id,
            count_ids=count_ids,
        )

        return [
            serialize_stock_count_summary(
                count,
                warehouse=warehouse,
                started_by={
                    "id": started_by_id,
                    "first_name": started_by_first_name,
                    "last_name": started_by_last_name,
                    "username": started_by_username,
                }
                if started_by_id
                else None,
                item_counts=counts_by_id.get(str(count.id), self._empty_item_counts()),
                adjustment=adjustments_by_count_id.get(str(count.id)),
            )
            for (
                count,
                warehouse,
                started_by_id,
                started_by_first_name,
                started_by_last_name,
                started_by_username,
            ) in rows
        ], _pagination(filters.page, filters.per_page, total)

    def get_stock_count(
        self,
        *,
        tenant_id: str,
        branch_id: str | None,
        count_id: str,
    ) -> StockCount:
        if not branch_id:
            raise ValidationError("Authenticated user is not assigned to a branch.")

        count = (
            self.session.query(StockCount)
            .filter(
                StockCount.id == count_id,
                StockCount.tenant_id == tenant_id,
                StockCount.branch_id == branch_id,
            )
            .first()
        )
        if not count:
            raise NotFoundError("Stock count not found.")
        return count

    def update_stock_count_item(
        self,
        *,
        tenant_id: str,
        branch_id: str | None,
        count_id: str,
        item_id: str,
        counted_by: str,
        request: UpdateStockCountItemRequest,
    ) -> StockCount:
        if not branch_id:
            raise ValidationError("Authenticated user is not assigned to a branch.")

        now = _now()
        try:
            count = self._locked_count(
                tenant_id=tenant_id,
                branch_id=branch_id,
                count_id=count_id,
            )
            self._ensure_open(count)
            item = self._locked_item(count_id=str(count.id), item_id=item_id)

            expected = self._expected_quantity(
                count=count,
                item=item,
                counted_at=now,
            )
            item.expected_quantity = expected
            item.counted_quantity = _q4(request.counted_quantity)
            item.variance_quantity = _q4(item.counted_quantity - expected)
            item.counted_at = now
            item.counted_by = counted_by
            item.notes = request.notes
            item.updated_at = now
            count.updated_at = now

            self.session.commit()
            return count
        except Exception:
            self.session.rollback()
            raise

    def complete_stock_count(
        self,
        *,
        tenant_id: str,
        branch_id: str | None,
        count_id: str,
        completed_by: str,
    ) -> StockCount:
        if not branch_id:
            raise ValidationError("Authenticated user is not assigned to a branch.")

        now = _now()
        try:
            count = self._locked_count(
                tenant_id=tenant_id,
                branch_id=branch_id,
                count_id=count_id,
            )
            self._ensure_open(count)
            uncounted = (
                self.session.query(func.count(StockCountItem.id))
                .filter(
                    StockCountItem.stock_count_id == count.id,
                    StockCountItem.counted_quantity.is_(None),
                )
                .scalar()
            )
            if uncounted:
                raise ValidationError("All stock count items must be counted before completion.")

            count.status = COMPLETED_STATUS
            count.completed_at = now
            count.completed_by = completed_by
            count.updated_at = now
            self.session.commit()
            return count
        except Exception:
            self.session.rollback()
            raise

    def cancel_stock_count(
        self,
        *,
        tenant_id: str,
        branch_id: str | None,
        count_id: str,
        cancelled_by: str,
    ) -> StockCount:
        if not branch_id:
            raise ValidationError("Authenticated user is not assigned to a branch.")

        now = _now()
        try:
            count = self._locked_count(
                tenant_id=tenant_id,
                branch_id=branch_id,
                count_id=count_id,
            )
            self._ensure_open(count)
            count.status = CANCELLED_STATUS
            count.cancelled_at = now
            count.cancelled_by = cancelled_by
            count.updated_at = now
            self.session.commit()
            return count
        except Exception:
            self.session.rollback()
            raise

    def serialization_context(self, count: StockCount) -> dict:
        warehouse = (
            self.session.query(Warehouse)
            .filter(Warehouse.id == count.warehouse_id)
            .first()
        )
        return {
            "warehouse": warehouse,
            "started_by": self._user_context(count.started_by),
            "completed_by": self._user_context(count.completed_by),
            "cancelled_by": self._user_context(count.cancelled_by),
            "items": self._item_context(str(count.id)),
            "adjustment": self._adjustment_for_count(
                tenant_id=str(count.tenant_id),
                count_id=str(count.id),
            ),
        }

    def _adjustments_by_count_ids(
        self,
        *,
        tenant_id: str,
        count_ids: list[str],
    ) -> dict[str, StockAdjustment]:
        if not count_ids:
            return {}
        if not self._stock_adjustments_available():
            return {}

        adjustments = (
            self.session.query(StockAdjustment)
            .filter(
                StockAdjustment.tenant_id == tenant_id,
                StockAdjustment.source_type == "stock_count",
                StockAdjustment.source_id.in_(count_ids),
            )
            .all()
        )
        return {
            str(adjustment.source_id): adjustment
            for adjustment in adjustments
            if adjustment.source_id
        }

    def _adjustment_for_count(
        self,
        *,
        tenant_id: str,
        count_id: str,
    ) -> StockAdjustment | None:
        if not self._stock_adjustments_available():
            return None

        return (
            self.session.query(StockAdjustment)
            .filter(
                StockAdjustment.tenant_id == tenant_id,
                StockAdjustment.source_type == "stock_count",
                StockAdjustment.source_id == count_id,
            )
            .first()
        )

    def _stock_adjustments_available(self) -> bool:
        return inspect(self.session.get_bind()).has_table("stock_adjustments")

    def _existing_by_idempotency_key(
        self,
        *,
        tenant_id: str,
        idempotency_key: str,
    ) -> StockCount | None:
        return (
            self.session.query(StockCount)
            .filter(
                StockCount.tenant_id == tenant_id,
                StockCount.idempotency_key == idempotency_key,
            )
            .first()
        )

    def _require_warehouse(
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
            raise ValidationError("warehouse_id is not valid for this branch.")
        return warehouse

    def _ensure_no_open_count(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        warehouse_id: str,
    ) -> None:
        existing = (
            self.session.query(StockCount)
            .filter(
                StockCount.tenant_id == tenant_id,
                StockCount.branch_id == branch_id,
                StockCount.warehouse_id == warehouse_id,
                StockCount.status == OPEN_STATUS,
            )
            .first()
        )
        if existing:
            raise ConflictError("An open stock count already exists for this warehouse.")

    def _load_products(
        self,
        *,
        tenant_id: str,
        product_ids: list[str],
    ) -> dict[str, Product]:
        if not product_ids:
            return {}
        products = (
            self.session.query(Product)
            .filter(
                Product.tenant_id == tenant_id,
                Product.id.in_(set(product_ids)),
            )
            .all()
        )
        by_id = {str(product.id): product for product in products}
        missing = sorted(set(product_ids) - set(by_id))
        if missing:
            raise ValidationError("All products must belong to this tenant.")
        for product in by_id.values():
            if not product.track_inventory:
                raise ValidationError("Stock count products must be inventory-tracked.")
        return by_id

    def _snapshot_rows(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        warehouse_id: str,
        selected_products: dict[str, Product],
    ) -> list[dict]:
        query = (
            self.session.query(StockBalance, Product)
            .join(Product, Product.id == StockBalance.product_id)
            .filter(
                StockBalance.tenant_id == tenant_id,
                StockBalance.branch_id == branch_id,
                StockBalance.warehouse_id == warehouse_id,
                Product.tenant_id == tenant_id,
                Product.track_inventory.is_(True),
            )
        )
        if selected_products:
            query = query.filter(StockBalance.product_id.in_(selected_products.keys()))

        rows: list[dict] = []
        seen_products: set[str] = set()
        for stock, product in query.order_by(Product.name.asc(), Product.internal_sku.asc()).all():
            product_id = str(product.id)
            seen_products.add(product_id)
            if product.track_batches or product.track_expiry:
                rows.extend(
                    self._batch_rows(
                        tenant_id=tenant_id,
                        warehouse_id=warehouse_id,
                        product=product,
                        stock_quantity=_q4(stock.quantity_on_hand),
                    )
                )
            elif _q4(stock.quantity_on_hand) != Decimal("0.0000") or selected_products:
                rows.append(
                    {
                        "product": product,
                        "batch": None,
                        "quantity": _q4(stock.quantity_on_hand),
                    }
                )

        for product_id, product in selected_products.items():
            if product_id in seen_products:
                continue
            if product.track_batches or product.track_expiry:
                raise ValidationError(
                    "Batch-tracked products without system batches require a later adjustment discovery workflow."
                )
            rows.append(
                {
                    "product": product,
                    "batch": None,
                    "quantity": Decimal("0.0000"),
                }
            )

        return rows

    def _batch_rows(
        self,
        *,
        tenant_id: str,
        warehouse_id: str,
        product: Product,
        stock_quantity: Decimal,
    ) -> list[dict]:
        batches = (
            self.session.query(InventoryBatch)
            .filter(
                InventoryBatch.tenant_id == tenant_id,
                InventoryBatch.warehouse_id == warehouse_id,
                InventoryBatch.product_id == product.id,
                InventoryBatch.quantity_on_hand != 0,
            )
            .order_by(
                InventoryBatch.expiry_date.asc().nullslast(),
                InventoryBatch.batch_number.asc(),
                InventoryBatch.id.asc(),
            )
            .all()
        )
        batch_total = _q4(sum(_d(batch.quantity_on_hand) for batch in batches))
        if batch_total != stock_quantity:
            raise ConflictError(
                "Batch quantities do not match StockBalance quantity_on_hand."
            )
        return [
            {
                "product": product,
                "batch": batch,
                "quantity": _q4(batch.quantity_on_hand),
            }
            for batch in batches
        ]

    def _count_number(self, count: StockCount, counted_at: datetime) -> str:
        return f"SC-{counted_at.year}-{str(count.id)[:8].upper()}"

    def _locked_count(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        count_id: str,
    ) -> StockCount:
        count = (
            self.session.query(StockCount)
            .filter(
                StockCount.id == count_id,
                StockCount.tenant_id == tenant_id,
                StockCount.branch_id == branch_id,
            )
            .with_for_update()
            .first()
        )
        if not count:
            raise NotFoundError("Stock count not found.")
        return count

    def _locked_item(
        self,
        *,
        count_id: str,
        item_id: str,
    ) -> StockCountItem:
        item = (
            self.session.query(StockCountItem)
            .filter(
                StockCountItem.id == item_id,
                StockCountItem.stock_count_id == count_id,
            )
            .with_for_update()
            .first()
        )
        if not item:
            raise NotFoundError("Stock count item not found.")
        return item

    def _ensure_open(self, count: StockCount) -> None:
        if count.status != OPEN_STATUS:
            raise ConflictError("Stock count is not open.")

    def _expected_quantity(
        self,
        *,
        count: StockCount,
        item: StockCountItem,
        counted_at: datetime,
    ) -> Decimal:
        query = (
            self.session.query(func.coalesce(func.sum(InventoryMovement.quantity), 0))
            .filter(
                InventoryMovement.tenant_id == count.tenant_id,
                InventoryMovement.branch_id == count.branch_id,
                InventoryMovement.warehouse_id == count.warehouse_id,
                InventoryMovement.product_id == item.product_id,
                InventoryMovement.created_at > count.snapshot_at,
                InventoryMovement.created_at <= counted_at,
            )
        )
        if item.batch_id:
            query = query.filter(InventoryMovement.batch_id == item.batch_id)
        else:
            query = query.filter(InventoryMovement.batch_id.is_(None))

        movement_delta = _q4(query.scalar() or Decimal("0"))
        return _q4(item.snapshot_quantity + movement_delta)

    def _item_context(
        self,
        count_id: str,
    ) -> list[tuple[StockCountItem, Product, InventoryBatch | None, dict | None]]:
        rows = (
            self.session.query(StockCountItem, Product, InventoryBatch)
            .join(Product, Product.id == StockCountItem.product_id)
            .outerjoin(InventoryBatch, InventoryBatch.id == StockCountItem.batch_id)
            .filter(StockCountItem.stock_count_id == count_id)
            .order_by(StockCountItem.line_number.asc())
            .all()
        )
        return [
            (
                item,
                product,
                batch,
                self._user_context(item.counted_by),
            )
            for item, product, batch in rows
        ]

    def _user_context(self, user_id: str | None) -> dict | None:
        if not user_id:
            return None
        row = (
            self.session.query(
                User.id,
                User.first_name,
                User.last_name,
                User.username,
            )
            .filter(User.id == user_id)
            .first()
        )
        if not row:
            return None
        return {
            "id": row.id,
            "first_name": row.first_name,
            "last_name": row.last_name,
            "username": row.username,
        }

    def _empty_item_counts(self) -> dict:
        return {
            "total_items": 0,
            "counted_items": 0,
            "variance_items": 0,
            "positive_variance_items": 0,
            "negative_variance_items": 0,
        }

    def _item_counts(self, count_ids: list[str]) -> dict[str, dict]:
        if not count_ids:
            return {}
        rows = (
            self.session.query(
                StockCountItem.stock_count_id,
                StockCountItem.counted_quantity,
                StockCountItem.variance_quantity,
            )
            .filter(StockCountItem.stock_count_id.in_(count_ids))
            .all()
        )
        counts: dict[str, dict] = {
            count_id: self._empty_item_counts()
            for count_id in count_ids
        }
        for count_id, counted_quantity, variance_quantity in rows:
            payload = counts[str(count_id)]
            payload["total_items"] += 1
            if counted_quantity is not None:
                payload["counted_items"] += 1
            variance = _q4(variance_quantity or Decimal("0"))
            if variance != Decimal("0.0000"):
                payload["variance_items"] += 1
                if variance > Decimal("0.0000"):
                    payload["positive_variance_items"] += 1
                else:
                    payload["negative_variance_items"] += 1
        return counts
