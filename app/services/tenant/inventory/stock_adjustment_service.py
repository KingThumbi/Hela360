from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timezone
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json

from sqlalchemy import func

from app.errors import ConflictError, NotFoundError, ValidationError
from app.models import (
    InventoryBatch,
    InventoryMovement,
    Product,
    StockAdjustment,
    StockAdjustmentItem,
    StockBalance,
    StockCount,
    StockCountItem,
    User,
    Warehouse,
)
from app.schemas import (
    CreateStockAdjustmentFromCountRequest,
    CreateStockAdjustmentRequest,
)
from app.serializers import (
    serialize_stock_adjustment_summary,
)


FOURPLACES = Decimal("0.0001")
POSTED_STATUS = "posted"
MANUAL_SOURCE = "manual"
STOCK_COUNT_SOURCE = "stock_count"


class StockAdjustmentQueryError(ValueError):
    pass


@dataclass(frozen=True)
class StockAdjustmentListFilters:
    page: int = 1
    per_page: int = 25
    warehouse_id: str | None = None
    reason_code: str | None = None
    source_type: str | None = None
    date_from: date | None = None
    date_to: date | None = None

    @classmethod
    def from_query(cls, args) -> "StockAdjustmentListFilters":
        source_type = _optional_text(args.get("source_type"))
        if source_type and source_type not in {MANUAL_SOURCE, STOCK_COUNT_SOURCE}:
            raise StockAdjustmentQueryError("source_type is not supported.")

        return cls(
            page=_positive_int(args.get("page"), "page", 1),
            per_page=_positive_int(args.get("per_page"), "per_page", 25),
            warehouse_id=_optional_text(args.get("warehouse_id")),
            reason_code=_optional_text(args.get("reason_code")),
            source_type=source_type,
            date_from=_parse_date(args.get("date_from"), "date_from"),
            date_to=_parse_date(args.get("date_to"), "date_to"),
        )


@dataclass(frozen=True)
class AdjustmentLine:
    product_id: str
    batch_id: str | None
    quantity_delta: Decimal
    reason: str | None = None
    stock_count_item_id: str | None = None


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


def _available_from(on_hand, reserved) -> Decimal:
    return _q4(_d(on_hand) - _d(reserved))


def _optional_text(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _positive_int(value, field_name: str, default: int) -> int:
    if value in (None, ""):
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise StockAdjustmentQueryError(
            f"{field_name} must be a positive integer."
        ) from exc
    if parsed <= 0:
        raise StockAdjustmentQueryError(f"{field_name} must be a positive integer.")
    return parsed


def _parse_date(value, field_name: str) -> date | None:
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise StockAdjustmentQueryError(
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


def _fingerprint(payload) -> str:
    encoded = json.dumps(
        _json_safe(payload),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class StockAdjustmentService:
    def __init__(self, session):
        self.session = session

    def create_manual_adjustment(
        self,
        *,
        tenant_id: str,
        branch_id: str | None,
        posted_by: str,
        request: CreateStockAdjustmentRequest,
    ) -> StockAdjustment:
        if not branch_id:
            raise ValidationError("Authenticated user is not assigned to a branch.")

        fingerprint = _fingerprint(
            {
                "source_type": MANUAL_SOURCE,
                **asdict(request),
            }
        )
        existing = self._existing_by_idempotency_key(
            tenant_id=tenant_id,
            idempotency_key=request.idempotency_key,
        )
        if existing:
            if existing.request_fingerprint != fingerprint:
                raise ConflictError(
                    "idempotency_key was already used for a different stock adjustment."
                )
            return existing

        lines = [
            AdjustmentLine(
                product_id=item.product_id,
                batch_id=item.batch_id,
                quantity_delta=item.quantity_delta,
                reason=item.reason,
            )
            for item in request.items
        ]

        return self._post_adjustment(
            tenant_id=tenant_id,
            branch_id=branch_id,
            warehouse_id=request.warehouse_id,
            posted_by=posted_by,
            idempotency_key=request.idempotency_key,
            request_fingerprint=fingerprint,
            reason_code=request.reason_code,
            reason=request.reason,
            notes=request.notes,
            source_type=MANUAL_SOURCE,
            source_id=None,
            lines=lines,
        )

    def create_adjustment_from_stock_count(
        self,
        *,
        tenant_id: str,
        branch_id: str | None,
        count_id: str,
        posted_by: str,
        request: CreateStockAdjustmentFromCountRequest,
    ) -> StockAdjustment:
        if not branch_id:
            raise ValidationError("Authenticated user is not assigned to a branch.")

        fingerprint = _fingerprint(
            {
                "source_type": STOCK_COUNT_SOURCE,
                "stock_count_id": count_id,
                **asdict(request),
            }
        )
        existing = self._existing_by_idempotency_key(
            tenant_id=tenant_id,
            idempotency_key=request.idempotency_key,
        )
        if existing:
            if existing.request_fingerprint != fingerprint:
                raise ConflictError(
                    "idempotency_key was already used for a different stock adjustment."
                )
            return existing

        try:
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
            if count.status != "completed":
                raise ConflictError("Only completed Stock Counts can be adjusted.")

            self._ensure_source_not_adjusted(
                tenant_id=tenant_id,
                source_type=STOCK_COUNT_SOURCE,
                source_id=str(count.id),
            )

            rows = (
                self.session.query(StockCountItem)
                .filter(
                    StockCountItem.stock_count_id == count.id,
                    StockCountItem.variance_quantity.isnot(None),
                    StockCountItem.variance_quantity != 0,
                )
                .order_by(StockCountItem.line_number.asc())
                .all()
            )
            if not rows:
                raise ConflictError("Stock Count has no variance to adjust.")

            lines = [
                AdjustmentLine(
                    product_id=str(item.product_id),
                    batch_id=str(item.batch_id) if item.batch_id else None,
                    quantity_delta=_q4(item.variance_quantity),
                    reason=f"Variance from Stock Count {count.count_number}.",
                    stock_count_item_id=str(item.id),
                )
                for item in rows
            ]

            return self._post_adjustment(
                tenant_id=tenant_id,
                branch_id=branch_id,
                warehouse_id=str(count.warehouse_id),
                posted_by=posted_by,
                idempotency_key=request.idempotency_key,
                request_fingerprint=fingerprint,
                reason_code=request.reason_code,
                reason=request.reason,
                notes=request.notes,
                source_type=STOCK_COUNT_SOURCE,
                source_id=str(count.id),
                lines=lines,
            )
        except Exception:
            self.session.rollback()
            raise

    def get_stock_adjustment(
        self,
        *,
        tenant_id: str,
        branch_id: str | None,
        adjustment_id: str,
    ) -> StockAdjustment:
        if not branch_id:
            raise ValidationError("Authenticated user is not assigned to a branch.")

        adjustment = (
            self.session.query(StockAdjustment)
            .filter(
                StockAdjustment.id == adjustment_id,
                StockAdjustment.tenant_id == tenant_id,
                StockAdjustment.branch_id == branch_id,
            )
            .first()
        )
        if not adjustment:
            raise NotFoundError("Stock adjustment not found.")
        return adjustment

    def list_stock_adjustments(
        self,
        *,
        tenant_id: str,
        branch_id: str | None,
        filters: StockAdjustmentListFilters,
    ) -> tuple[list[dict], dict]:
        if not branch_id:
            raise StockAdjustmentQueryError(
                "Authenticated user is not assigned to a branch."
            )
        if filters.date_from and filters.date_to and filters.date_from > filters.date_to:
            raise StockAdjustmentQueryError("date_from must be before or equal to date_to.")
        if filters.warehouse_id:
            self._require_warehouse(
                tenant_id=tenant_id,
                branch_id=branch_id,
                warehouse_id=filters.warehouse_id,
            )

        item_counts = (
            self.session.query(
                StockAdjustmentItem.stock_adjustment_id.label("adjustment_id"),
                func.count(StockAdjustmentItem.id).label("item_count"),
            )
            .group_by(StockAdjustmentItem.stock_adjustment_id)
            .subquery()
        )
        query = (
            self.session.query(
                StockAdjustment,
                Warehouse,
                StockCount,
                User.id.label("posted_by_id"),
                User.first_name.label("posted_by_first_name"),
                User.last_name.label("posted_by_last_name"),
                User.username.label("posted_by_username"),
                func.coalesce(item_counts.c.item_count, 0).label("item_count"),
            )
            .join(Warehouse, Warehouse.id == StockAdjustment.warehouse_id)
            .outerjoin(
                StockCount,
                (StockAdjustment.source_type == STOCK_COUNT_SOURCE)
                & (StockCount.id == StockAdjustment.source_id),
            )
            .outerjoin(User, User.id == StockAdjustment.posted_by)
            .outerjoin(item_counts, item_counts.c.adjustment_id == StockAdjustment.id)
            .filter(
                StockAdjustment.tenant_id == tenant_id,
                StockAdjustment.branch_id == branch_id,
                Warehouse.tenant_id == tenant_id,
                Warehouse.branch_id == branch_id,
            )
        )
        if filters.warehouse_id:
            query = query.filter(StockAdjustment.warehouse_id == filters.warehouse_id)
        if filters.reason_code:
            query = query.filter(StockAdjustment.reason_code == filters.reason_code)
        if filters.source_type:
            query = query.filter(StockAdjustment.source_type == filters.source_type)
        if filters.date_from:
            query = query.filter(StockAdjustment.posted_at >= _day_start(filters.date_from))
        if filters.date_to:
            query = query.filter(StockAdjustment.posted_at <= _day_end(filters.date_to))

        total = query.count()
        rows = (
            query.order_by(StockAdjustment.posted_at.desc(), StockAdjustment.id.desc())
            .offset((filters.page - 1) * filters.per_page)
            .limit(filters.per_page)
            .all()
        )

        return [
            serialize_stock_adjustment_summary(
                adjustment,
                warehouse=warehouse,
                source_count=source_count,
                posted_by={
                    "id": posted_by_id,
                    "first_name": posted_by_first_name,
                    "last_name": posted_by_last_name,
                    "username": posted_by_username,
                }
                if posted_by_id
                else None,
                item_count=int(item_count or 0),
            )
            for (
                adjustment,
                warehouse,
                source_count,
                posted_by_id,
                posted_by_first_name,
                posted_by_last_name,
                posted_by_username,
                item_count,
            ) in rows
        ], _pagination(filters.page, filters.per_page, total)

    def serialization_context(self, adjustment: StockAdjustment) -> dict:
        warehouse = (
            self.session.query(Warehouse)
            .filter(Warehouse.id == adjustment.warehouse_id)
            .first()
        )
        source_count = (
            self.session.query(StockCount)
            .filter(StockCount.id == adjustment.source_id)
            .first()
            if adjustment.source_type == STOCK_COUNT_SOURCE and adjustment.source_id
            else None
        )
        posted_by = self._user_context(adjustment.posted_by)
        items = (
            self.session.query(StockAdjustmentItem, Product, InventoryBatch)
            .join(Product, Product.id == StockAdjustmentItem.product_id)
            .outerjoin(InventoryBatch, InventoryBatch.id == StockAdjustmentItem.batch_id)
            .filter(StockAdjustmentItem.stock_adjustment_id == adjustment.id)
            .order_by(StockAdjustmentItem.line_number.asc())
            .all()
        )
        return {
            "warehouse": warehouse,
            "posted_by": posted_by,
            "source_count": source_count,
            "items": items,
        }

    def _post_adjustment(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        warehouse_id: str,
        posted_by: str,
        idempotency_key: str,
        request_fingerprint: str,
        reason_code: str,
        reason: str | None,
        notes: str | None,
        source_type: str,
        source_id: str | None,
        lines: list[AdjustmentLine],
    ) -> StockAdjustment:
        now = _now()
        try:
            warehouse = self._require_warehouse(
                tenant_id=tenant_id,
                branch_id=branch_id,
                warehouse_id=warehouse_id,
            )
            self._validate_duplicate_lines(lines)
            products = self._load_products(
                tenant_id=tenant_id,
                product_ids=[line.product_id for line in lines],
            )

            adjustment = StockAdjustment(
                tenant_id=tenant_id,
                branch_id=branch_id,
                warehouse_id=str(warehouse.id),
                adjustment_number="PENDING",
                reason_code=reason_code,
                reason=reason,
                source_type=source_type,
                source_id=source_id,
                status=POSTED_STATUS,
                idempotency_key=idempotency_key,
                request_fingerprint=request_fingerprint,
                posted_at=now,
                posted_by=posted_by,
                notes=notes,
                created_at=now,
                updated_at=now,
            )
            self.session.add(adjustment)
            self.session.flush()
            adjustment.adjustment_number = self._adjustment_number(adjustment, now)

            for line_number, line in enumerate(lines, start=1):
                product = products[line.product_id]
                self._validate_line(
                    tenant_id=tenant_id,
                    warehouse_id=str(warehouse.id),
                    product=product,
                    line=line,
                )
                batch = self._apply_batch_adjustment(
                    tenant_id=tenant_id,
                    warehouse_id=str(warehouse.id),
                    product=product,
                    line=line,
                    now=now,
                )
                stock_balance = self._apply_stock_balance_adjustment(
                    tenant_id=tenant_id,
                    branch_id=branch_id,
                    warehouse_id=str(warehouse.id),
                    product=product,
                    quantity_delta=line.quantity_delta,
                    now=now,
                )
                item = StockAdjustmentItem(
                    stock_adjustment_id=str(adjustment.id),
                    product_id=str(product.id),
                    batch_id=str(batch.id) if batch else None,
                    stock_count_item_id=line.stock_count_item_id,
                    line_number=line_number,
                    quantity_delta=_q4(line.quantity_delta),
                    reason=line.reason,
                    created_at=now,
                    updated_at=now,
                )
                self.session.add(item)
                self.session.flush()
                self.session.add(
                    InventoryMovement(
                        tenant_id=tenant_id,
                        branch_id=branch_id,
                        warehouse_id=str(warehouse.id),
                        product_id=str(product.id),
                        batch_id=str(batch.id) if batch else None,
                        movement_type="stock_adjustment",
                        quantity=_q4(line.quantity_delta),
                        unit_cost=stock_balance.avg_unit_cost,
                        reference_type="stock_adjustment",
                        reference_id=str(adjustment.id),
                        notes=f"Stock adjusted on {adjustment.adjustment_number}.",
                        created_by=posted_by,
                        created_at=now,
                        updated_at=now,
                    )
                )

            self.session.commit()
            return adjustment
        except Exception:
            self.session.rollback()
            raise

    def _existing_by_idempotency_key(
        self,
        *,
        tenant_id: str,
        idempotency_key: str,
    ) -> StockAdjustment | None:
        return (
            self.session.query(StockAdjustment)
            .filter(
                StockAdjustment.tenant_id == tenant_id,
                StockAdjustment.idempotency_key == idempotency_key,
            )
            .first()
        )

    def _ensure_source_not_adjusted(
        self,
        *,
        tenant_id: str,
        source_type: str,
        source_id: str,
    ) -> None:
        existing = (
            self.session.query(StockAdjustment)
            .filter(
                StockAdjustment.tenant_id == tenant_id,
                StockAdjustment.source_type == source_type,
                StockAdjustment.source_id == source_id,
            )
            .with_for_update()
            .first()
        )
        if existing:
            raise ConflictError("Stock Count has already been adjusted.")

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

    def _load_products(
        self,
        *,
        tenant_id: str,
        product_ids: list[str],
    ) -> dict[str, Product]:
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
            if not product.is_active:
                raise ValidationError("Stock adjustment products must be active.")
            if not product.track_inventory:
                raise ValidationError("Stock adjustment products must be inventory-tracked.")
        return by_id

    def _validate_duplicate_lines(self, lines: list[AdjustmentLine]) -> None:
        seen: set[tuple[str, str | None]] = set()
        for line in lines:
            key = (line.product_id, line.batch_id)
            if key in seen:
                raise ValidationError("Duplicate product and batch adjustment lines are not allowed.")
            seen.add(key)

    def _validate_line(
        self,
        *,
        tenant_id: str,
        warehouse_id: str,
        product: Product,
        line: AdjustmentLine,
    ) -> None:
        delta = _q4(line.quantity_delta)
        if delta == Decimal("0.0000"):
            raise ValidationError("quantity_delta must not be zero.")

        if product.track_batches or product.track_expiry:
            if not line.batch_id:
                raise ValidationError("batch_id is required for batch-tracked products.")
            batch = (
                self.session.query(InventoryBatch)
                .filter(
                    InventoryBatch.id == line.batch_id,
                    InventoryBatch.tenant_id == tenant_id,
                    InventoryBatch.warehouse_id == warehouse_id,
                    InventoryBatch.product_id == product.id,
                )
                .first()
            )
            if not batch:
                raise ValidationError("batch_id is not valid for this product and warehouse.")
        elif line.batch_id:
            raise ValidationError("batch_id is only allowed for batch-tracked products.")

    def _apply_batch_adjustment(
        self,
        *,
        tenant_id: str,
        warehouse_id: str,
        product: Product,
        line: AdjustmentLine,
        now: datetime,
    ) -> InventoryBatch | None:
        if not (product.track_batches or product.track_expiry):
            return None

        batch = (
            self.session.query(InventoryBatch)
            .filter(
                InventoryBatch.id == line.batch_id,
                InventoryBatch.tenant_id == tenant_id,
                InventoryBatch.warehouse_id == warehouse_id,
                InventoryBatch.product_id == product.id,
            )
            .with_for_update()
            .first()
        )
        if not batch:
            raise ValidationError("batch_id is not valid for this product and warehouse.")

        new_on_hand = _q4(_d(batch.quantity_on_hand) + _d(line.quantity_delta))
        if new_on_hand < Decimal("0.0000"):
            raise ConflictError("Stock adjustment would make batch quantity negative.")
        if new_on_hand < _q4(batch.quantity_reserved):
            raise ConflictError("Stock adjustment would reduce batch stock below reserved quantity.")

        batch.quantity_on_hand = new_on_hand
        batch.updated_at = now
        return batch

    def _apply_stock_balance_adjustment(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        warehouse_id: str,
        product: Product,
        quantity_delta: Decimal,
        now: datetime,
    ) -> StockBalance:
        stock_balance = (
            self.session.query(StockBalance)
            .filter(
                StockBalance.tenant_id == tenant_id,
                StockBalance.branch_id == branch_id,
                StockBalance.warehouse_id == warehouse_id,
                StockBalance.product_id == product.id,
            )
            .with_for_update()
            .first()
        )
        if not stock_balance:
            if _q4(quantity_delta) < Decimal("0.0000"):
                raise ConflictError("Stock adjustment would make stock quantity negative.")
            stock_balance = StockBalance(
                tenant_id=tenant_id,
                branch_id=branch_id,
                warehouse_id=warehouse_id,
                product_id=str(product.id),
                quantity_on_hand=Decimal("0.0000"),
                quantity_reserved=Decimal("0.0000"),
                quantity_available=Decimal("0.0000"),
                avg_unit_cost=Decimal("0.00"),
                created_at=now,
                updated_at=now,
            )
            self.session.add(stock_balance)
            self.session.flush()

        new_on_hand = _q4(_d(stock_balance.quantity_on_hand) + _d(quantity_delta))
        if new_on_hand < Decimal("0.0000"):
            raise ConflictError("Stock adjustment would make stock quantity negative.")
        if new_on_hand < _q4(stock_balance.quantity_reserved):
            raise ConflictError("Stock adjustment would reduce stock below reserved quantity.")

        stock_balance.quantity_on_hand = new_on_hand
        stock_balance.quantity_available = _available_from(
            new_on_hand,
            stock_balance.quantity_reserved,
        )
        stock_balance.updated_at = now
        return stock_balance

    def _adjustment_number(
        self,
        adjustment: StockAdjustment,
        posted_at: datetime,
    ) -> str:
        return f"SA-{posted_at.year}-{str(adjustment.id)[:8].upper()}"

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
