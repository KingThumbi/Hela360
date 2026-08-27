from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timezone
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json

from sqlalchemy import func, or_

from app.errors import ConflictError, NotFoundError, ValidationError
from app.models import (
    GoodsReceipt,
    GoodsReceiptItem,
    InventoryBatch,
    InventoryMovement,
    Product,
    StockBalance,
    Supplier,
    User,
    Warehouse,
)
from app.schemas import CreateGoodsReceiptRequest
from app.serializers.goods_receipt import serialize_goods_receipt_summary
from app.services.tenant.inventory.product_unit_conversion_service import (
    ProductUnitConversionService,
)


FOURPLACES = Decimal("0.0001")
TWOPLACES = Decimal("0.01")


class GoodsReceiptQueryError(ValueError):
    pass


@dataclass(frozen=True)
class GoodsReceiptListFilters:
    page: int = 1
    per_page: int = 25
    search: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    warehouse_id: str | None = None
    supplier_id: str | None = None

    @classmethod
    def from_query(cls, args) -> "GoodsReceiptListFilters":
        return cls(
            page=_positive_int(args.get("page"), "page", 1),
            per_page=_positive_int(args.get("per_page"), "per_page", 25),
            search=_optional_text(args.get("search") or args.get("q")),
            date_from=_parse_date(args.get("date_from"), "date_from"),
            date_to=_parse_date(args.get("date_to"), "date_to"),
            warehouse_id=_optional_text(args.get("warehouse_id")),
            supplier_id=_optional_text(args.get("supplier_id")),
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


def _q2(value) -> Decimal:
    return _d(value).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _positive_int(value, field_name: str, default: int) -> int:
    if value in (None, ""):
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise GoodsReceiptQueryError(
            f"{field_name} must be a positive integer."
        ) from exc
    if parsed <= 0:
        raise GoodsReceiptQueryError(f"{field_name} must be a positive integer.")
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
        raise GoodsReceiptQueryError(
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


def _available_from(on_hand, reserved) -> Decimal:
    return _q4(_d(on_hand) - _d(reserved))


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


def _fingerprint(request: CreateGoodsReceiptRequest) -> str:
    payload = _json_safe(asdict(request))
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class GoodsReceiptService:
    def __init__(self, session):
        self.session = session

    def create_goods_receipt(
        self,
        *,
        tenant_id: str,
        branch_id: str | None,
        received_by: str,
        request: CreateGoodsReceiptRequest,
    ) -> GoodsReceipt:
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
                    "idempotency_key was already used for a different goods receipt."
                )
            return existing

        now = _now()
        received_at = request.received_at or now
        if received_at > now:
            raise ValidationError("received_at cannot be in the future.")

        try:
            warehouse = self._require_warehouse(
                tenant_id=tenant_id,
                branch_id=branch_id,
                warehouse_id=request.warehouse_id,
            )
            supplier = self._require_supplier(
                tenant_id=tenant_id,
                supplier_id=request.supplier_id,
            )
            products = self._load_products(
                tenant_id=tenant_id,
                product_ids=[item.product_id for item in request.items],
            )
            self._validate_lines(
                request=request,
                products=products,
                received_at=received_at,
            )
            unit_service = ProductUnitConversionService(self.session)

            receipt = GoodsReceipt(
                tenant_id=tenant_id,
                branch_id=branch_id,
                warehouse_id=str(warehouse.id),
                supplier_id=str(supplier.id) if supplier else None,
                receipt_number="PENDING",
                supplier_reference=request.supplier_reference,
                idempotency_key=request.idempotency_key,
                request_fingerprint=fingerprint,
                received_at=received_at,
                status="received",
                notes=request.notes,
                received_by=received_by,
                created_at=now,
                updated_at=now,
            )
            self.session.add(receipt)
            self.session.flush()
            receipt.receipt_number = self._receipt_number(receipt, received_at)

            for line_number, item in enumerate(request.items, start=1):
                product = products[item.product_id]
                unit_resolution = unit_service.resolve_for_receipt(
                    tenant_id=tenant_id,
                    product=product,
                    product_unit_id=item.product_unit_id,
                )
                base_quantity = unit_resolution.to_base_quantity(item.quantity)
                base_unit_cost = unit_resolution.to_base_unit_cost(item.unit_cost)
                batch = self._apply_batch_receipt(
                    tenant_id=tenant_id,
                    warehouse_id=str(warehouse.id),
                    product=product,
                    item=item,
                    quantity=base_quantity,
                    unit_cost=base_unit_cost,
                    received_at=received_at,
                    now=now,
                )
                self._apply_stock_balance_receipt(
                    tenant_id=tenant_id,
                    branch_id=branch_id,
                    warehouse_id=str(warehouse.id),
                    product=product,
                    quantity=base_quantity,
                    unit_cost=base_unit_cost,
                    now=now,
                )
                receipt_item = GoodsReceiptItem(
                    goods_receipt_id=str(receipt.id),
                    product_id=str(product.id),
                    product_unit_id=unit_resolution.product_unit_id,
                    batch_id=str(batch.id) if batch else None,
                    line_number=line_number,
                    quantity=_q4(item.quantity),
                    base_quantity=base_quantity,
                    unit_code_snapshot=unit_resolution.unit_code,
                    unit_name_snapshot=unit_resolution.unit_name,
                    conversion_factor_to_base=unit_resolution.conversion_factor_to_base,
                    batch_number=item.batch_number,
                    manufacture_date=item.manufacture_date,
                    expiry_date=item.expiry_date,
                    unit_cost=_q2(item.unit_cost),
                    base_unit_cost=base_unit_cost,
                    supplier_batch_reference=item.supplier_batch_reference,
                    created_at=now,
                    updated_at=now,
                )
                self.session.add(receipt_item)
                self.session.flush()
                self.session.add(
                    InventoryMovement(
                        tenant_id=tenant_id,
                        branch_id=branch_id,
                        warehouse_id=str(warehouse.id),
                        product_id=str(product.id),
                        batch_id=str(batch.id) if batch else None,
                        movement_type="goods_receipt",
                        quantity=base_quantity,
                        unit_cost=base_unit_cost,
                        reference_type="goods_receipt",
                        reference_id=str(receipt.id),
                        notes=f"Stock received on {receipt.receipt_number}.",
                        created_by=received_by,
                        created_at=now,
                        updated_at=now,
                    )
                )

            self.session.commit()
            return receipt
        except Exception:
            self.session.rollback()
            raise

    def get_goods_receipt(
        self,
        *,
        tenant_id: str,
        branch_id: str | None,
        receipt_id: str,
    ) -> GoodsReceipt:
        if not branch_id:
            raise ValidationError("Authenticated user is not assigned to a branch.")

        receipt = (
            self.session.query(GoodsReceipt)
            .filter(
                GoodsReceipt.id == receipt_id,
                GoodsReceipt.tenant_id == tenant_id,
                GoodsReceipt.branch_id == branch_id,
            )
            .first()
        )
        if not receipt:
            raise NotFoundError("Goods receipt not found.")
        return receipt

    def list_goods_receipts(
        self,
        *,
        tenant_id: str,
        branch_id: str | None,
        filters: GoodsReceiptListFilters,
    ) -> tuple[list[dict], dict]:
        if not branch_id:
            raise GoodsReceiptQueryError(
                "Authenticated user is not assigned to a branch."
            )

        if filters.date_from and filters.date_to and filters.date_from > filters.date_to:
            raise GoodsReceiptQueryError("date_from must be before or equal to date_to.")

        if filters.warehouse_id:
            self._require_warehouse(
                tenant_id=tenant_id,
                branch_id=branch_id,
                warehouse_id=filters.warehouse_id,
            )

        if filters.supplier_id:
            self._require_tenant_supplier(
                tenant_id=tenant_id,
                supplier_id=filters.supplier_id,
            )

        totals = (
            self.session.query(
                GoodsReceiptItem.goods_receipt_id.label("receipt_id"),
                func.count(GoodsReceiptItem.id).label("item_count"),
                func.coalesce(
                    func.sum(GoodsReceiptItem.quantity * GoodsReceiptItem.unit_cost),
                    0,
                ).label("total_cost"),
            )
            .group_by(GoodsReceiptItem.goods_receipt_id)
            .subquery()
        )

        query = (
            self.session.query(
                GoodsReceipt,
                Warehouse,
                Supplier,
                User.id.label("received_by_id"),
                User.first_name.label("received_by_first_name"),
                User.last_name.label("received_by_last_name"),
                User.username.label("received_by_username"),
                func.coalesce(totals.c.item_count, 0).label("item_count"),
                func.coalesce(totals.c.total_cost, 0).label("total_cost"),
            )
            .join(Warehouse, Warehouse.id == GoodsReceipt.warehouse_id)
            .outerjoin(Supplier, Supplier.id == GoodsReceipt.supplier_id)
            .outerjoin(User, User.id == GoodsReceipt.received_by)
            .outerjoin(totals, totals.c.receipt_id == GoodsReceipt.id)
            .filter(
                GoodsReceipt.tenant_id == tenant_id,
                GoodsReceipt.branch_id == branch_id,
                Warehouse.tenant_id == tenant_id,
                Warehouse.branch_id == branch_id,
            )
        )

        if filters.date_from:
            query = query.filter(GoodsReceipt.received_at >= _day_start(filters.date_from))
        if filters.date_to:
            query = query.filter(GoodsReceipt.received_at <= _day_end(filters.date_to))
        if filters.warehouse_id:
            query = query.filter(GoodsReceipt.warehouse_id == filters.warehouse_id)
        if filters.supplier_id:
            query = query.filter(GoodsReceipt.supplier_id == filters.supplier_id)
        if filters.search:
            pattern = f"%{filters.search}%"
            query = query.filter(
                or_(
                    GoodsReceipt.receipt_number.ilike(pattern),
                    GoodsReceipt.supplier_reference.ilike(pattern),
                    Supplier.name.ilike(pattern),
                    Supplier.supplier_code.ilike(pattern),
                )
            )

        total = query.count()
        rows = (
            query.order_by(
                GoodsReceipt.received_at.desc(),
                GoodsReceipt.id.desc(),
            )
            .offset((filters.page - 1) * filters.per_page)
            .limit(filters.per_page)
            .all()
        )

        return [
            serialize_goods_receipt_summary(
                receipt,
                warehouse=warehouse,
                supplier=supplier,
                received_by=(
                    {
                        "id": received_by_id,
                        "first_name": received_by_first_name,
                        "last_name": received_by_last_name,
                        "username": received_by_username,
                    }
                    if received_by_id
                    else None
                ),
                item_count=int(item_count or 0),
                total_cost=_q2(total_cost),
            )
            for (
                receipt,
                warehouse,
                supplier,
                received_by_id,
                received_by_first_name,
                received_by_last_name,
                received_by_username,
                item_count,
                total_cost,
            ) in rows
        ], _pagination(filters.page, filters.per_page, total)

    def serialization_context(
        self,
        receipt: GoodsReceipt,
    ) -> dict:
        warehouse = (
            self.session.query(Warehouse)
            .filter(Warehouse.id == receipt.warehouse_id)
            .first()
        )
        supplier = (
            self.session.query(Supplier)
            .filter(Supplier.id == receipt.supplier_id)
            .first()
            if receipt.supplier_id
            else None
        )
        received_by_row = (
            self.session.query(
                User.id,
                User.first_name,
                User.last_name,
                User.username,
            )
            .filter(User.id == receipt.received_by)
            .first()
        )
        received_by = (
            {
                "id": received_by_row.id,
                "first_name": received_by_row.first_name,
                "last_name": received_by_row.last_name,
                "username": received_by_row.username,
            }
            if received_by_row
            else None
        )
        items = (
            self.session.query(GoodsReceiptItem, Product, InventoryBatch)
            .join(Product, Product.id == GoodsReceiptItem.product_id)
            .outerjoin(InventoryBatch, InventoryBatch.id == GoodsReceiptItem.batch_id)
            .filter(GoodsReceiptItem.goods_receipt_id == receipt.id)
            .order_by(GoodsReceiptItem.line_number.asc())
            .all()
        )
        return {
            "warehouse": warehouse,
            "supplier": supplier,
            "received_by": received_by,
            "items": items,
        }

    def _existing_by_idempotency_key(
        self,
        *,
        tenant_id: str,
        idempotency_key: str,
    ) -> GoodsReceipt | None:
        return (
            self.session.query(GoodsReceipt)
            .filter(
                GoodsReceipt.tenant_id == tenant_id,
                GoodsReceipt.idempotency_key == idempotency_key,
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

    def _require_supplier(
        self,
        *,
        tenant_id: str,
        supplier_id: str | None,
    ) -> Supplier | None:
        if not supplier_id:
            return None

        supplier = (
            self.session.query(Supplier)
            .filter(
                Supplier.id == supplier_id,
                Supplier.tenant_id == tenant_id,
            )
            .first()
        )
        if not supplier:
            raise ValidationError("supplier_id is not valid for this tenant.")
        if not supplier.is_active:
            raise ValidationError("supplier_id must reference an active supplier.")
        return supplier

    def _require_tenant_supplier(
        self,
        *,
        tenant_id: str,
        supplier_id: str,
    ) -> Supplier:
        supplier = (
            self.session.query(Supplier)
            .filter(
                Supplier.id == supplier_id,
                Supplier.tenant_id == tenant_id,
            )
            .first()
        )
        if not supplier:
            raise GoodsReceiptQueryError("supplier_id is not valid for this tenant.")
        return supplier

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
        return by_id

    def _validate_lines(
        self,
        *,
        request: CreateGoodsReceiptRequest,
        products: dict[str, Product],
        received_at: datetime,
    ) -> None:
        seen: set[tuple[str, str | None]] = set()

        for item in request.items:
            product = products[item.product_id]
            if not product.is_active:
                raise ValidationError("Goods receipt products must be active.")
            if not product.track_inventory:
                raise ValidationError(
                    "Goods receipt products must be inventory-tracked."
                )

            key = (item.product_id, item.batch_number)
            if key in seen:
                raise ValidationError(
                    "Duplicate product and batch lines are not allowed."
                )
            seen.add(key)

            if product.track_batches or product.track_expiry:
                if not item.batch_number:
                    raise ValidationError(
                        "batch_number is required for batch-tracked products."
                    )
            elif item.batch_number or item.expiry_date or item.manufacture_date:
                raise ValidationError(
                    "Batch fields are only allowed for batch-tracked products."
                )

            if product.track_expiry and item.expiry_date is None:
                raise ValidationError(
                    "expiry_date is required for expiry-tracked products."
                )
            if item.expiry_date is not None and item.expiry_date < received_at.date():
                raise ValidationError("Expired stock cannot be received.")

    def _apply_batch_receipt(
        self,
        *,
        tenant_id: str,
        warehouse_id: str,
        product: Product,
        item,
        quantity: Decimal,
        unit_cost: Decimal,
        received_at: datetime,
        now: datetime,
    ) -> InventoryBatch | None:
        if not product.track_batches and not product.track_expiry:
            return None

        batch = (
            self.session.query(InventoryBatch)
            .filter(
                InventoryBatch.tenant_id == tenant_id,
                InventoryBatch.warehouse_id == warehouse_id,
                InventoryBatch.product_id == product.id,
                InventoryBatch.batch_number == item.batch_number,
            )
            .with_for_update()
            .first()
        )
        if batch:
            self._validate_batch_metadata(
                batch=batch,
                item=item,
                unit_cost=unit_cost,
            )
            batch.quantity_on_hand = _q4(_d(batch.quantity_on_hand) + quantity)
            batch.updated_at = now
            return batch

        batch = InventoryBatch(
            tenant_id=tenant_id,
            warehouse_id=warehouse_id,
            product_id=str(product.id),
            batch_number=item.batch_number,
            manufacture_date=item.manufacture_date,
            expiry_date=item.expiry_date,
            unit_cost=_q2(unit_cost),
            quantity_on_hand=_q4(quantity),
            quantity_reserved=Decimal("0.0000"),
            status="available",
            received_at=received_at,
            created_at=now,
            updated_at=now,
        )
        self.session.add(batch)
        self.session.flush()
        return batch

    def _validate_batch_metadata(
        self,
        *,
        batch: InventoryBatch,
        item,
        unit_cost: Decimal,
    ) -> None:
        if batch.expiry_date != item.expiry_date:
            raise ConflictError(
                "Existing batch has conflicting expiry metadata."
            )
        if batch.manufacture_date != item.manufacture_date:
            raise ConflictError(
                "Existing batch has conflicting manufacture metadata."
            )
        if _q2(batch.unit_cost) != _q2(unit_cost):
            raise ConflictError("Existing batch has conflicting cost metadata.")

    def _apply_stock_balance_receipt(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        warehouse_id: str,
        product: Product,
        quantity: Decimal,
        unit_cost: Decimal,
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

        old_quantity = _q4(stock_balance.quantity_on_hand)
        new_quantity = _q4(old_quantity + quantity)
        if old_quantity <= Decimal("0.0000"):
            stock_balance.avg_unit_cost = _q2(unit_cost)
        else:
            old_value = old_quantity * _q2(stock_balance.avg_unit_cost)
            received_value = _q4(quantity) * _q2(unit_cost)
            stock_balance.avg_unit_cost = _q2(
                (old_value + received_value) / new_quantity
            )

        stock_balance.quantity_on_hand = new_quantity
        stock_balance.quantity_available = _available_from(
            new_quantity,
            stock_balance.quantity_reserved,
        )
        stock_balance.updated_at = now
        return stock_balance

    def _receipt_number(
        self,
        receipt: GoodsReceipt,
        received_at: datetime,
    ) -> str:
        return f"GRN-{received_at.year}-{str(receipt.id)[:8].upper()}"
