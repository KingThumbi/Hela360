from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from uuid import UUID, uuid4

import sqlalchemy as sa
from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models import (
    Branch,
    Customer,
    InventoryBatch,
    InventoryMovement,
    PaymentMethod,
    Product,
    ProductCode,
    Sale,
    SaleItem,
    SalePayment,
    StockBalance,
    Till,
    TillShift,
    User,
    Warehouse,
)
from app.models.pos import SaleRefund, SaleRefundItem, SaleActionRequest
from app.services.tenant.pos.receipt_service import ReceiptService
from app.services.tenant.pos.till_shift_service import (
    shift_is_owned_by_session,
)
from app.services.tenant.pos.refund_service import RefundError, RefundService
from app.services.tenant.pos.dispensing_service import DispensingService
from app.services.tenant.pos.sales_query_service import (
    SalesListFilters,
    SalesQueryService,
)
from app.services.tenant.pos.sale_approval_service import ApprovalError, SaleApprovalService
from app.services.tenant.auth.decorators import (
    require_permission,
    _current_identity,
)
from app.services.tenant.inventory.sale_stock_service import allocate_sale_stock
from app.services.tenant.inventory.product_unit_conversion_service import (
    ProductUnitConversionService,
)

bp = Blueprint("sales", __name__)

TWOPLACES = Decimal("0.01")
FOURPLACES = Decimal("0.0001")
POS_AVAILABILITY_LIMIT = 50


def _json_error(message: str, status: int = 400):
    return jsonify({"ok": False, "error": message}), status


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def q2(value: Decimal) -> Decimal:
    return Decimal(str(value)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def q4(value: Decimal) -> Decimal:
    return Decimal(str(value)).quantize(FOURPLACES, rounding=ROUND_HALF_UP)


def _available_from(on_hand, reserved) -> Decimal:
    return q4(_to_decimal(on_hand, Decimal("0.0000")) - _to_decimal(reserved, Decimal("0.0000")))


def _batch_is_pos_sellable(
    batch: InventoryBatch,
    *,
    product: Product,
    operational_date: date,
) -> bool:
    if (batch.status or "").lower() != "available":
        return False
    if _available_from(batch.quantity_on_hand, batch.quantity_reserved) <= Decimal("0.0000"):
        return False
    if batch.expiry_date is not None and batch.expiry_date < operational_date:
        return False
    if product.track_expiry and batch.expiry_date is None:
        return False
    return True


def _to_decimal(value, default: Decimal = Decimal("0.00")) -> Decimal:
    if value is None:
        return default
    return Decimal(str(value))


def _to_str_decimal(value, default: str = "0.00") -> str:
    if value is None:
        return default
    return str(value)


def to_decimal(value, field_name: str, default: Decimal | None = None) -> Decimal:
    if value is None or value == "":
        if default is not None:
            return default
        raise ValueError(f"{field_name} is required.")

    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{field_name} must be a valid number.")


def non_negative_decimal(value, field_name: str, default: Decimal | None = None) -> Decimal:
    amount = to_decimal(value, field_name, default=default)
    if amount < 0:
        raise ValueError(f"{field_name} cannot be negative.")
    return amount


def positive_decimal(value, field_name: str) -> Decimal:
    amount = to_decimal(value, field_name)
    if amount <= 0:
        raise ValueError(f"{field_name} must be greater than zero.")
    return amount


def get_scoped_or_404(model, obj_id: str, tenant_id: str, name: str):
    obj = (
        db.session.query(model)
        .filter(model.id == obj_id, model.tenant_id == tenant_id)
        .first()
    )
    if not obj:
        raise ValueError(f"{name} not found.")
    return obj


def generate_sale_number() -> str:
    stamp = now_utc().strftime("%Y%m%d%H%M%S")
    suffix = uuid4().hex[:6].upper()
    return f"SALE-{stamp}-{suffix}"


def _sale_timestamp(sale: Sale) -> str | None:
    if getattr(sale, "sale_date", None):
        return sale.sale_date.isoformat()
    if getattr(sale, "sold_at", None):
        return sale.sold_at.isoformat()
    return None


def serialize_sale_item(item: SaleItem) -> dict:
    return {
        "id": str(item.id),
        "sale_id": str(item.sale_id),
        "product_id": str(item.product_id) if getattr(item, "product_id", None) else None,
        "product_name": getattr(item, "product_name", None),
        "sku": getattr(item, "sku", None),
        "quantity": _to_str_decimal(getattr(item, "quantity", None), "0.0000"),
        "base_quantity": _to_str_decimal(getattr(item, "base_quantity", None), "0.0000"),
        "product_unit_id": (
            str(item.product_unit_id)
            if getattr(item, "product_unit_id", None)
            else None
        ),
        "unit_code": getattr(item, "unit_code_snapshot", None),
        "unit_name": getattr(item, "unit_name_snapshot", None),
        "conversion_factor_to_base": _to_str_decimal(
            getattr(item, "conversion_factor_to_base", None),
            "1.000000",
        ),
        "unit_price": _to_str_decimal(getattr(item, "unit_price", None)),
        "discount_amount": _to_str_decimal(getattr(item, "discount_amount", None)),
        "tax_amount": _to_str_decimal(getattr(item, "tax_amount", None)),
        "line_total": _to_str_decimal(getattr(item, "line_total", None)),
        "created_at": item.created_at.isoformat() if getattr(item, "created_at", None) else None,
    }


def serialize_sale_payment(payment: SalePayment) -> dict:
    return {
        "id": str(payment.id),
        "sale_id": str(payment.sale_id),
        "payment_method_id": str(payment.payment_method_id) if getattr(payment, "payment_method_id", None) else None,
        "amount": _to_str_decimal(getattr(payment, "amount", None)),
        "reference": getattr(payment, "reference_number", None),
        "paid_at": payment.paid_at.isoformat() if getattr(payment, "paid_at", None) else None,
        "received_by": str(payment.received_by) if getattr(payment, "received_by", None) else None,
        "created_at": payment.created_at.isoformat() if getattr(payment, "created_at", None) else None,
        "notes": getattr(payment, "notes", None),
    }


def serialize_sale(sale: Sale, include_children: bool = True) -> dict:
    refund_count = (
        db.session.query(func.count(SaleRefund.id))
        .filter(
            SaleRefund.sale_id == str(sale.id),
            SaleRefund.tenant_id == str(sale.tenant_id),
            SaleRefund.status == "posted",
        )
        .scalar()
        or 0
    )

    refunded_amount = _to_decimal(getattr(sale, "refunded_amount", None))
    paid_amount = _to_decimal(getattr(sale, "paid_amount", None))
    refundable_amount = max(Decimal("0.00"), q2(paid_amount - refunded_amount))

    payload = {
        "id": str(sale.id),
        "tenant_id": str(sale.tenant_id),
        "sale_number": getattr(sale, "sale_number", None),
        "status": getattr(sale, "status", None),
        "branch_id": str(sale.branch_id) if getattr(sale, "branch_id", None) else None,
        "warehouse_id": str(sale.warehouse_id) if getattr(sale, "warehouse_id", None) else None,
        "till_id": str(sale.till_id) if getattr(sale, "till_id", None) else None,
        "till_shift_id": str(sale.till_shift_id) if getattr(sale, "till_shift_id", None) else None,
        "customer_id": str(sale.customer_id) if getattr(sale, "customer_id", None) else None,
        "cashier_id": str(sale.cashier_id) if getattr(sale, "cashier_id", None) else None,
        "subtotal": _to_str_decimal(getattr(sale, "subtotal", None)),
        "discount_amount": _to_str_decimal(getattr(sale, "discount_amount", None)),
        "tax_amount": _to_str_decimal(getattr(sale, "tax_amount", None)),
        "total_amount": _to_str_decimal(getattr(sale, "total_amount", None)),
        "paid_amount": _to_str_decimal(getattr(sale, "paid_amount", None)),
        "balance_due": _to_str_decimal(getattr(sale, "balance_due", None)),
        "refunded_amount": str(refunded_amount),
        "refund_status": getattr(sale, "refund_status", "not_refunded"),
        "refund_count": int(refund_count),
        "refundable_amount": str(refundable_amount),
        "sold_at": _sale_timestamp(sale),
        "created_at": sale.created_at.isoformat() if getattr(sale, "created_at", None) else None,
        "updated_at": sale.updated_at.isoformat() if getattr(sale, "updated_at", None) else None,
    }

    if include_children:
        sale_id = str(sale.id)

        sale_items = (
            db.session.query(SaleItem)
            .filter(SaleItem.sale_id == sale_id)
            .order_by(SaleItem.id.asc())
            .all()
        )
        sale_payments = (
            db.session.query(SalePayment)
            .filter(SalePayment.sale_id == sale_id)
            .order_by(SalePayment.id.asc())
            .all()
        )

        payload["items"] = [serialize_sale_item(item) for item in sale_items]
        payload["payments"] = [serialize_sale_payment(payment) for payment in sale_payments]

    return payload


def refundable_quantity_by_item(sale: Sale) -> dict[str, Decimal]:
    rows = (
        db.session.query(
            SaleRefundItem.sale_item_id,
            func.coalesce(func.sum(SaleRefundItem.quantity), 0),
        )
        .join(SaleRefund, SaleRefund.id == SaleRefundItem.refund_id)
        .filter(
            SaleRefund.sale_id == sale.id,
            SaleRefund.tenant_id == sale.tenant_id,
            SaleRefund.status == "posted",
        )
        .group_by(SaleRefundItem.sale_item_id)
        .all()
    )

    return {
        str(sale_item_id): _to_decimal(quantity)
        for sale_item_id, quantity in rows
    }


def serialize_refundable_sale(sale: Sale) -> dict:
    payload = serialize_sale(sale, include_children=True)
    refunded_by_item = refundable_quantity_by_item(sale)

    items = []
    for item in payload.get("items", []):
        sold_qty = _to_decimal(item["quantity"])
        refunded_qty = refunded_by_item.get(
            item["id"],
            Decimal("0.0000"),
        )
        remaining_qty = max(
            Decimal("0.0000"),
            q4(sold_qty - refunded_qty),
        )
        items.append(
            {
                **item,
                "refunded_quantity": str(q4(refunded_qty)),
                "remaining_refundable_quantity": str(remaining_qty),
                "is_refundable": remaining_qty > Decimal("0.0000"),
            }
        )

    payload["items"] = items
    return payload


def serialize_shift(shift: TillShift) -> dict:
    return {
        "id": str(shift.id),
        "tenant_id": str(shift.tenant_id),
        "branch_id": str(shift.branch_id) if getattr(shift, "branch_id", None) else None,
        "till_id": str(shift.till_id) if getattr(shift, "till_id", None) else None,
        "cashier_id": str(shift.cashier_id) if getattr(shift, "cashier_id", None) else None,
        "status": getattr(shift, "status", None),
        "opening_float": _to_str_decimal(getattr(shift, "opening_float", None)),
        "closing_cash": _to_str_decimal(getattr(shift, "closing_cash", None)),
        "notes": getattr(shift, "notes", None),
        "opened_at": shift.opened_at.isoformat() if getattr(shift, "opened_at", None) else None,
        "closed_at": shift.closed_at.isoformat() if getattr(shift, "closed_at", None) else None,
        "created_at": shift.created_at.isoformat() if getattr(shift, "created_at", None) else None,
        "updated_at": shift.updated_at.isoformat() if getattr(shift, "updated_at", None) else None,
    }

def serialize_sale_action_request(request_row: SaleActionRequest) -> dict:
    return {
        "id": str(request_row.id),
        "tenant_id": str(request_row.tenant_id),
        "sale_id": str(request_row.sale_id),
        "action_type": request_row.action_type,
        "status": request_row.status,
        "requested_by": str(request_row.requested_by) if request_row.requested_by else None,
        "approved_by": str(request_row.approved_by) if request_row.approved_by else None,
        "rejected_by": str(request_row.rejected_by) if request_row.rejected_by else None,
        "request_reason": request_row.request_reason,
        "decision_reason": request_row.decision_reason,
        "request_payload": request_row.request_payload,
        "requires_approval": bool(request_row.requires_approval),
        "approved_at": request_row.approved_at.isoformat() if request_row.approved_at else None,
        "rejected_at": request_row.rejected_at.isoformat() if request_row.rejected_at else None,
        "executed_at": request_row.executed_at.isoformat() if request_row.executed_at else None,
        "created_at": request_row.created_at.isoformat() if request_row.created_at else None,
        "updated_at": request_row.updated_at.isoformat() if request_row.updated_at else None,
    }

def _pagination_meta(page: int, per_page: int, total: int) -> dict:
    pages = (total + per_page - 1) // per_page if per_page else 1
    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages,
        "has_prev": page > 1,
        "has_next": page < pages,
    }


def _parse_date(value: str | None, field_name: str):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        raise ValueError(f"{field_name} must be a valid date in YYYY-MM-DD format.")


def _sale_datetime_column():
    if hasattr(Sale, "sale_date"):
        return Sale.sale_date
    if hasattr(Sale, "sold_at"):
        return Sale.sold_at
    return Sale.created_at


def _apply_sales_filters(query, tenant_id: str):
    sale_dt_col = _sale_datetime_column()

    query = query.filter(Sale.tenant_id == tenant_id)

    status = request.args.get("status")
    if status:
        query = query.filter(Sale.status == status.strip())

    branch_id = request.args.get("branch_id")
    if branch_id:
        query = query.filter(Sale.branch_id == branch_id.strip())

    warehouse_id = request.args.get("warehouse_id")
    if warehouse_id:
        query = query.filter(Sale.warehouse_id == warehouse_id.strip())

    till_id = request.args.get("till_id")
    if till_id:
        query = query.filter(Sale.till_id == till_id.strip())

    cashier_id = request.args.get("cashier_id")
    if cashier_id:
        query = query.filter(Sale.cashier_id == cashier_id.strip())

    customer_id = request.args.get("customer_id")
    if customer_id:
        query = query.filter(Sale.customer_id == customer_id.strip())

    sale_number = request.args.get("sale_number")
    q = request.args.get("q") or request.args.get("search")
    if sale_number:
        query = query.filter(Sale.sale_number.ilike(f"%{sale_number.strip()}%"))
    elif q:
        query = query.filter(Sale.sale_number.ilike(f"%{q.strip()}%"))

    date_from = _parse_date(request.args.get("date_from"), "date_from")
    date_to = _parse_date(request.args.get("date_to"), "date_to")

    if date_from:
        start_dt = datetime.combine(date_from, datetime.min.time()).replace(tzinfo=timezone.utc)
        query = query.filter(sale_dt_col >= start_dt)

    if date_to:
        end_dt = datetime.combine(date_to, datetime.max.time()).replace(tzinfo=timezone.utc)
        query = query.filter(sale_dt_col <= end_dt)

    return query


@bp.get("/sales")
@require_permission("sales.read")
def list_sales():
    """
    Return branch-scoped persisted Sale summaries for Sales History.
    """

    identity = _current_identity()
    filters = SalesListFilters.from_query(request.args)
    items, pagination = SalesQueryService(db.session).list_sales(
        tenant_id=identity.tenant_id,
        branch_id=identity.branch_id,
        filters=filters,
    )

    return jsonify(
        {
            "ok": True,
            "items": items,
            "pagination": pagination,
        }
    )


@bp.get("/sales/<sale_id>")
@require_permission("sales.refund")
def get_refundable_sale(sale_id: str):
    """
    Return one branch-scoped Sale projection for refund processing.
    """

    identity = _current_identity()
    tenant_id = identity.tenant_id
    branch_id = identity.branch_id

    if not branch_id:
        return _json_error(
            "Authenticated user is not assigned to a branch.",
            403,
        )

    sale = (
        db.session.query(Sale)
        .filter(
            Sale.tenant_id == tenant_id,
            sa.or_(
                Sale.id == sale_id,
                Sale.sale_number == sale_id,
            ),
        )
        .first()
    )

    if not sale:
        return _json_error("Sale not found.", 404)

    if str(sale.branch_id) != str(branch_id):
        return _json_error(
            "You cannot refund sales from another branch.",
            403,
        )

    return jsonify(
        {
            "ok": True,
            "item": serialize_refundable_sale(sale),
        }
    )


@bp.get("/sales/<sale_id>/receipt")
@require_permission("sales.read")
def get_sale_receipt(sale_id: str):
    """
    Return the canonical persisted receipt projection for one branch Sale.
    """

    receipt = ReceiptService(db.session).get_receipt(
        identity=_current_identity(),
        sale_id=sale_id,
    )

    return jsonify(
        {
            "ok": True,
            "receipt": receipt,
        }
    )


def _sales_summary(query):
    row = query.with_entities(
        sa.func.count(Sale.id),
        sa.func.coalesce(sa.func.sum(Sale.total_amount), 0),
        sa.func.coalesce(sa.func.sum(Sale.paid_amount), 0),
        sa.func.coalesce(sa.func.sum(Sale.balance_due), 0),
    ).first()

    return {
        "sale_count": int(row[0] or 0),
        "total_amount": _to_str_decimal(row[1]),
        "paid_amount": _to_str_decimal(row[2]),
        "balance_due": _to_str_decimal(row[3]),
    }


def resolve_product(
    tenant_id: str,
    item_payload: dict,
) -> tuple[Product, str | None, str | None]:
    product_id = item_payload.get("product_id")
    barcode = item_payload.get("barcode")

    if not product_id and not barcode:
        raise ValueError("Each item must include product_id or barcode.")

    if product_id:
        product = (
            db.session.query(Product)
            .filter(Product.id == product_id, Product.tenant_id == tenant_id)
            .first()
        )
        if not product:
            raise ValueError(f"Product not found for product_id={product_id}.")
        if not product.is_active:
            raise ValueError(
                f"Product is inactive and cannot be sold for product_id={product_id}."
            )
        return product, barcode, item_payload.get("product_unit_id")

    product_code = (
        db.session.query(ProductCode)
        .filter(
            ProductCode.tenant_id == tenant_id,
            ProductCode.code_value == barcode,
        )
        .first()
    )
    if not product_code:
        raise ValueError(f"Product not found for barcode={barcode}.")

    product = (
        db.session.query(Product)
        .filter(Product.id == product_code.product_id, Product.tenant_id == tenant_id)
        .first()
    )
    if not product:
        raise ValueError(f"Product not found for barcode={barcode}.")
    if not product.is_active:
        raise ValueError(f"Product is inactive and cannot be sold for barcode={barcode}.")

    return product, barcode, str(product_code.product_unit_id) if product_code.product_unit_id else None


def get_item_unit_price(
    product: Product,
    item_payload: dict,
    unit_resolution,
) -> Decimal:
    """
    Resolve the authoritative selling price for a POS line.

    Pricing rules
    -------------
    - The configured product/unit sale price is the marked/catalogue price.
    - When the client omits unit_price, the marked price is used.
    - The POS may submit a different selling price.
    - A submitted selling price may be above or below the marked price.
    - A selling price below the configured minimum sale price is rejected.
    - Product-unit pricing takes precedence over product-level pricing.

    The returned value is the actual transaction unit price persisted on
    SaleItem.
    """

    marked_sale_price = (
        unit_resolution.sale_price
        if unit_resolution.sale_price is not None
        else product.default_sale_price
    )

    minimum_sale_price = (
        unit_resolution.minimum_sale_price
        if unit_resolution.minimum_sale_price is not None
        else product.min_sale_price
    )

    if marked_sale_price is None:
        raise ValueError(
            "default_sale_price is required before "
            f"product_id={product.id} can be sold."
        )

    marked_unit_price = q2(
        non_negative_decimal(
            marked_sale_price,
            "default_sale_price",
        )
    )

    if minimum_sale_price is not None:
        resolved_minimum_sale_price = q2(
            non_negative_decimal(
                minimum_sale_price,
                "min_sale_price",
            )
        )

        if marked_unit_price < resolved_minimum_sale_price:
            raise ValueError(
                "default_sale_price cannot be below "
                "min_sale_price for "
                f"product_id={product.id}."
            )
    else:
        resolved_minimum_sale_price = None

    requested_price = item_payload.get("unit_price")

    if requested_price is None:
        return marked_unit_price

    selling_price = q2(
        non_negative_decimal(
            requested_price,
            "unit_price",
        )
    )

    if (
        resolved_minimum_sale_price is not None
        and selling_price < resolved_minimum_sale_price
    ):
        raise ValueError(
            "unit_price cannot be below min_sale_price "
            f"for product_id={product.id}."
        )

    return selling_price

def get_line_discount_amount(product: Product, item_payload: dict) -> Decimal:
    discount_amount = q2(
        non_negative_decimal(
            item_payload.get("discount_amount"),
            "discount_amount",
            default=Decimal("0.00"),
        )
    )
    if discount_amount != Decimal("0.00"):
        raise ValueError(
            f"discount_amount is not supported for POS checkout product_id={product.id}."
        )
    return discount_amount


def get_line_tax_amount(product: Product, item_payload: dict) -> Decimal:
    tax_amount = q2(
        non_negative_decimal(
            item_payload.get("tax_amount"),
            "tax_amount",
            default=Decimal("0.00"),
        )
    )
    if tax_amount != Decimal("0.00"):
        raise ValueError(
            f"tax_amount is not supported for POS checkout product_id={product.id}."
        )
    return tax_amount


def get_stock_balance(
    tenant_id: str,
    branch_id: str,
    warehouse_id: str,
    product_id: str,
) -> StockBalance | None:
    return (
        db.session.query(StockBalance)
        .filter(
            StockBalance.tenant_id == tenant_id,
            StockBalance.branch_id == branch_id,
            StockBalance.warehouse_id == warehouse_id,
            StockBalance.product_id == product_id,
        )
        .first()
    )


def require_sufficient_stock(
    tenant_id: str,
    branch_id: str,
    warehouse_id: str,
    product_id: str,
    quantity_needed: Decimal,
):
    stock_balance = get_stock_balance(tenant_id, branch_id, warehouse_id, product_id)

    if not stock_balance:
        raise ValueError(f"No stock balance found for product_id={product_id}.")

    current_qty = Decimal(str(getattr(stock_balance, "quantity_on_hand", 0)))
    if current_qty < quantity_needed:
        raise ValueError(
            f"Insufficient stock for product_id={product_id}. "
            f"Available={current_qty}, requested={quantity_needed}."
        )

    return stock_balance, current_qty


def update_stock_for_sale(
    tenant_id: str,
    branch_id: str,
    warehouse_id: str,
    sale_id: str,
    product: Product,
    quantity: Decimal,
    created_by: str,
):
    stock_balance, current_qty = require_sufficient_stock(
        tenant_id=tenant_id,
        branch_id=branch_id,
        warehouse_id=warehouse_id,
        product_id=str(product.id),
        quantity_needed=quantity,
    )

    new_qty_on_hand = q4(current_qty - quantity)
    current_reserved = Decimal(str(getattr(stock_balance, "quantity_reserved", 0)))
    new_qty_available = q4(new_qty_on_hand - current_reserved)

    stock_balance.quantity_on_hand = new_qty_on_hand

    if hasattr(stock_balance, "quantity_available"):
        stock_balance.quantity_available = new_qty_available

    if hasattr(stock_balance, "updated_at"):
        stock_balance.updated_at = now_utc()

    movement_time = now_utc()

    movement = InventoryMovement(
        id=str(uuid4()),
        tenant_id=tenant_id,
        branch_id=branch_id,
        warehouse_id=warehouse_id,
        product_id=product.id,
        movement_type="sale",
        quantity=q4(-quantity),
        reference_type="sale",
        reference_id=sale_id,
        created_by=created_by,
        created_at=movement_time,
        updated_at=movement_time,
    )

    if hasattr(movement, "unit_cost"):
        movement.unit_cost = getattr(product, "cost_price", None)
    if hasattr(movement, "notes"):
        movement.notes = "Stock deducted during sales checkout."

    db.session.add(movement)


def validate_payments(tenant_id: str, payments_payload: list[dict]) -> Decimal:
    total_paid = Decimal("0.00")

    for index, payment in enumerate(payments_payload, start=1):
        payment_method_id = payment.get("payment_method_id")
        if not payment_method_id:
            raise ValueError(f"payment_method_id is required for payment #{index}.")

        payment_method = (
            db.session.query(PaymentMethod)
            .filter(
                PaymentMethod.id == payment_method_id,
                PaymentMethod.tenant_id == tenant_id,
                PaymentMethod.is_active.is_(True),
            )
            .first()
        )
        if not payment_method:
            raise ValueError(f"Active payment method not found for payment #{index}.")

        amount = positive_decimal(payment.get("amount"), f"payments[{index}].amount")
        total_paid += amount

    return q2(total_paid)


def build_sale_item(
    tenant_id: str,
    item_payload: dict,
    customer: Customer | None = None,
    dispensing_service: DispensingService | None = None,
) -> tuple[SaleItem, dict]:
    """
    Build and validate a sale item without mutating inventory.

    Inventory allocation is intentionally performed separately after the
    Sale and SaleItem records have been added to the SQLAlchemy session and
    flushed. This preserves foreign-key ordering between:

        Sale -> SaleItem -> InventoryMovement

    and keeps commercial line construction separate from inventory mutation.
    """

    product, barcode_used, barcode_product_unit_id = resolve_product(
        tenant_id,
        item_payload,
    )

    quantity = q4(
        positive_decimal(
            item_payload.get("quantity"),
            "quantity",
        )
    )

    product_unit_id = (
        item_payload.get("product_unit_id")
        or barcode_product_unit_id
    )

    unit_resolution = ProductUnitConversionService(
        db.session
    ).resolve_for_sale(
        tenant_id=tenant_id,
        product=product,
        product_unit_id=product_unit_id,
    )

    base_quantity = unit_resolution.to_base_quantity(quantity)

    unit_price = q2(
        get_item_unit_price(
            product,
            item_payload,
            unit_resolution,
        )
    )

    discount_amount = get_line_discount_amount(
        product,
        item_payload,
    )

    tax_amount = get_line_tax_amount(
        product,
        item_payload,
    )

    dispensing_context = (
        dispensing_service
        or DispensingService(db.session)
    ).require_context_for_product(
        product=product,
        customer=customer,
        item_payload=item_payload,
    )

    line_subtotal = q2(quantity * unit_price)

    if discount_amount > line_subtotal:
        raise ValueError(
            "discount_amount cannot exceed line subtotal "
            f"for product_id={product.id}."
        )

    line_total = q2(
        line_subtotal
        - discount_amount
        + tax_amount
    )

    sale_item = SaleItem(
        id=str(uuid4()),
        product_id=product.id,
        product_unit_id=unit_resolution.product_unit_id,
        quantity=quantity,
        base_quantity=base_quantity,
        unit_price=unit_price,
        unit_code_snapshot=unit_resolution.unit_code,
        unit_name_snapshot=unit_resolution.unit_name,
        conversion_factor_to_base=(
            unit_resolution.conversion_factor_to_base
        ),
        discount_amount=discount_amount,
        tax_amount=tax_amount,
        line_total=line_total,
    )

    if hasattr(sale_item, "product_name"):
        sale_item.product_name = getattr(
            product,
            "name",
            None,
        )

    if hasattr(sale_item, "barcode"):
        sale_item.barcode = barcode_used

    if hasattr(sale_item, "sku"):
        sale_item.sku = getattr(
            product,
            "internal_sku",
            None,
        )

    if hasattr(sale_item, "line_subtotal"):
        sale_item.line_subtotal = line_subtotal

    calculated = {
        "product": product,
        "quantity": quantity,
        "base_quantity": base_quantity,
        "line_subtotal": line_subtotal,
        "discount_amount": discount_amount,
        "tax_amount": tax_amount,
        "line_total": line_total,
        "dispensing_context": dispensing_context,
    }

    return sale_item, calculated


def _require_open_shift(
    tenant_id: str,
    branch_id: str,
    till_id: str | None,
    cashier_id: str | None,
    session_id: str | None,
):
    if not till_id:
        raise ValueError("till_id is required for sales checkout.")
    if not cashier_id:
        raise ValueError("cashier_id is required for sales checkout.")

    active_till = (
        db.session.query(Till)
        .filter(
            Till.id == till_id,
            Till.tenant_id == tenant_id,
            Till.branch_id == branch_id,
            Till.is_active.is_(True),
        )
        .first()
    )
    if not active_till:
        raise ValueError("Active till not found for this branch.")

    shift = (
        db.session.query(TillShift)
        .filter(
            TillShift.tenant_id == tenant_id,
            TillShift.branch_id == branch_id,
            TillShift.till_id == till_id,
            TillShift.cashier_id == cashier_id,
            TillShift.status == "open",
            TillShift.closed_at.is_(None),
        )
        .order_by(
            TillShift.opened_at.desc(),
            TillShift.created_at.desc(),
        )
        .first()
    )
    if not shift:
        raise ValueError("No open shift found for this till and cashier.")

    if not shift_is_owned_by_session(
        shift,
        session_id,
    ):
        raise ValueError(
            "This till shift is active on another session."
        )

    return shift


def _sale_time_for_reporting():
    if hasattr(Sale, "sold_at"):
        return Sale.sold_at
    return Sale.sale_date if hasattr(Sale, "sale_date") else Sale.created_at


def _serialize_shift_report_summary(
    shift: TillShift,
    sale_count: int,
    total_amount,
    amount_paid,
    balance_due,
    payments_breakdown: list[dict],
):
    return {
        "shift": serialize_shift(shift),
        "summary": {
            "sale_count": sale_count,
            "total_amount": _to_str_decimal(total_amount),
            "amount_paid": _to_str_decimal(amount_paid),
            "balance_due": _to_str_decimal(balance_due),
            "opening_float": _to_str_decimal(getattr(shift, "opening_float", None)),
            "closing_cash": _to_str_decimal(getattr(shift, "closing_cash", None)),
        },
        "payments_breakdown": payments_breakdown,
    }


def _parse_product_ids(value: str | None) -> list[str]:
    if not value:
        raise ValueError("product_ids is required.")

    product_ids = [
        item.strip()
        for item in str(value).split(",")
        if item.strip()
    ]
    if not product_ids:
        raise ValueError("product_ids is required.")
    if len(product_ids) > POS_AVAILABILITY_LIMIT:
        raise ValueError(
            f"product_ids cannot contain more than {POS_AVAILABILITY_LIMIT} products."
        )
    return list(dict.fromkeys(product_ids))


def _require_pos_till(
    *,
    tenant_id: str,
    branch_id: str,
    till_id: str | None,
) -> tuple[Till, Warehouse]:
    if not till_id:
        raise ValueError("till_id is required.")

    till = (
        db.session.query(Till)
        .filter(
            Till.id == till_id,
            Till.tenant_id == tenant_id,
            Till.branch_id == branch_id,
            Till.is_active.is_(True),
        )
        .first()
    )
    if not till:
        raise ValueError("Active till not found for this branch.")
    if not till.warehouse_id:
        raise ValueError("Till is not configured with a warehouse.")

    warehouse = (
        db.session.query(Warehouse)
        .filter(
            Warehouse.id == till.warehouse_id,
            Warehouse.tenant_id == tenant_id,
            Warehouse.branch_id == branch_id,
            Warehouse.is_active.is_(True),
        )
        .first()
    )
    if not warehouse:
        raise ValueError("Till warehouse is not active for this branch.")

    return till, warehouse


def _stock_status(
    *,
    product: Product,
    sellable_quantity: Decimal | None,
    stock_balance: StockBalance | None,
) -> str:
    if not product.is_active:
        return "inactive"
    if not product.track_inventory:
        return "not_tracked"
    if not stock_balance or sellable_quantity is None or sellable_quantity <= Decimal("0.0000"):
        return "out_of_stock"
    return "in_stock"


def _pos_availability_item(
    *,
    product: Product,
    warehouse: Warehouse,
    stock_balance: StockBalance | None,
    batches: list[InventoryBatch],
    operational_date: date,
) -> dict:
    sellable_quantity: Decimal | None = None
    earliest_expiry = None
    expired_only = False
    low_stock = False

    if product.track_inventory and stock_balance:
        if product.track_batches or product.track_expiry:
            sellable_batches = [
                batch
                for batch in batches
                if _batch_is_pos_sellable(
                    batch,
                    product=product,
                    operational_date=operational_date,
                )
            ]
            sellable_quantity = q4(
                sum(
                    (
                        _available_from(
                            batch.quantity_on_hand,
                            batch.quantity_reserved,
                        )
                        for batch in sellable_batches
                    ),
                    Decimal("0.0000"),
                )
            )
            expiry_dates = [
                batch.expiry_date
                for batch in sellable_batches
                if batch.expiry_date is not None
            ]
            earliest_expiry = min(expiry_dates) if expiry_dates else None
            expired_physical = any(
                batch.expiry_date is not None
                and batch.expiry_date < operational_date
                and _available_from(
                    batch.quantity_on_hand,
                    batch.quantity_reserved,
                )
                > Decimal("0.0000")
                for batch in batches
            )
            expired_only = expired_physical and sellable_quantity <= Decimal("0.0000")
        else:
            sellable_quantity = q4(_to_decimal(stock_balance.quantity_available))

        reorder_level = _to_decimal(product.reorder_level, Decimal("0.0000"))
        low_stock = (
            reorder_level > Decimal("0.0000")
            and sellable_quantity is not None
            and Decimal("0.0000") < sellable_quantity <= reorder_level
        )

    status = _stock_status(
        product=product,
        sellable_quantity=sellable_quantity,
        stock_balance=stock_balance,
    )

    return {
        "product_id": str(product.id),
        "warehouse_id": str(warehouse.id),
        "track_inventory": bool(product.track_inventory),
        "track_batches": bool(product.track_batches),
        "track_expiry": bool(product.track_expiry),
        "requires_prescription": bool(product.requires_prescription),
        "is_active": bool(product.is_active),
        "status": status,
        "sellable_quantity": str(sellable_quantity) if sellable_quantity is not None else None,
        "is_low_stock": low_stock,
        "is_out_of_stock": status == "out_of_stock",
        "expired_only": expired_only,
        "earliest_sellable_expiry_date": earliest_expiry.isoformat()
        if earliest_expiry
        else None,
    }


@bp.get("/sales/availability")
@require_permission("sales.create")
def list_pos_availability():
    identity = _current_identity()

    try:
        tenant_id = identity.tenant_id
        branch_id = identity.branch_id
        if not branch_id:
            raise ValueError("Authenticated user is not assigned to a branch.")

        _, warehouse = _require_pos_till(
            tenant_id=tenant_id,
            branch_id=branch_id,
            till_id=request.args.get("till_id"),
        )
        product_ids = _parse_product_ids(request.args.get("product_ids"))

        products = (
            db.session.query(Product)
            .filter(
                Product.tenant_id == tenant_id,
                Product.id.in_(product_ids),
            )
            .all()
        )
        products_by_id = {str(product.id): product for product in products}

        stock_balances = (
            db.session.query(StockBalance)
            .filter(
                StockBalance.tenant_id == tenant_id,
                StockBalance.branch_id == branch_id,
                StockBalance.warehouse_id == str(warehouse.id),
                StockBalance.product_id.in_(product_ids),
            )
            .all()
        )
        stock_by_product_id = {
            str(stock.product_id): stock
            for stock in stock_balances
        }

        tracked_batch_product_ids = [
            product_id
            for product_id, product in products_by_id.items()
            if product.track_inventory
            and (product.track_batches or product.track_expiry)
        ]
        batches_by_product_id: dict[str, list[InventoryBatch]] = {}
        if tracked_batch_product_ids:
            batches = (
                db.session.query(InventoryBatch)
                .filter(
                    InventoryBatch.tenant_id == tenant_id,
                    InventoryBatch.warehouse_id == str(warehouse.id),
                    InventoryBatch.product_id.in_(tracked_batch_product_ids),
                )
                .all()
            )
            for batch in batches:
                batches_by_product_id.setdefault(str(batch.product_id), []).append(batch)

        today = now_utc().date()
        items = [
            _pos_availability_item(
                product=products_by_id[product_id],
                warehouse=warehouse,
                stock_balance=stock_by_product_id.get(product_id),
                batches=batches_by_product_id.get(product_id, []),
                operational_date=today,
            )
            for product_id in product_ids
            if product_id in products_by_id
        ]

        return jsonify(
            {
                "ok": True,
                "items": items,
            }
        )
    except ValueError as exc:
        return _json_error(str(exc), 400)


@bp.post("/sales/checkout")
@require_permission("sales.create")
def checkout_sale():
    """
    Complete a POS checkout for the authenticated user.

    Tenant, branch and cashier information are derived from the
    authenticated JWT rather than supplied by the client.

    Transaction ordering
    --------------------
    The checkout persists domain entities in foreign-key-safe order:

        Sale
            -> SaleItem
                -> InventoryMovement

    Inventory allocation occurs only after the corresponding SaleItem
    has been flushed to the database.

    The entire checkout remains atomic. Intermediate flushes synchronize
    the SQLAlchemy unit of work with PostgreSQL but do not commit the
    transaction.
    """

    identity = _current_identity()

    tenant_id = identity.tenant_id
    branch_id = identity.branch_id
    cashier_id = identity.user_id

    payload = request.get_json(silent=True) or {}

    try:
        requested_warehouse_id = payload.get("warehouse_id")
        till_id = payload.get("till_id")
        customer_id = payload.get("customer_id")
        items_payload = payload.get("items") or []
        payments_payload = payload.get("payments") or []
        notes = payload.get("notes")

        # ------------------------------------------------------------------
        # Validate authenticated context
        # ------------------------------------------------------------------

        if not branch_id:
            raise ValueError(
                "Authenticated user is not assigned to a branch."
            )

        # ------------------------------------------------------------------
        # Validate request
        # ------------------------------------------------------------------

        if not till_id:
            raise ValueError("till_id is required.")

        if not items_payload:
            raise ValueError(
                "At least one sale item is required."
            )

        # ------------------------------------------------------------------
        # Resolve scoped resources
        # ------------------------------------------------------------------

        branch = get_scoped_or_404(
            Branch,
            branch_id,
            tenant_id,
            "Branch",
        )

        till = get_scoped_or_404(
            Till,
            till_id,
            tenant_id,
            "Till",
        )

        if (
            str(till.branch_id) != str(branch_id)
            or not till.is_active
        ):
            raise ValueError(
                "Active till not found for this branch."
            )

        if not till.warehouse_id:
            raise ValueError(
                "Till is not configured with a warehouse."
            )

        warehouse = (
            db.session.query(Warehouse)
            .filter(
                Warehouse.id == till.warehouse_id,
                Warehouse.tenant_id == tenant_id,
                Warehouse.branch_id == branch_id,
                Warehouse.is_active.is_(True),
            )
            .first()
        )

        if not warehouse:
            raise ValueError(
                "Till warehouse is not active for this branch."
            )

        if (
            requested_warehouse_id
            and str(requested_warehouse_id) != str(warehouse.id)
        ):
            raise ValueError(
                "warehouse_id must match the selected till warehouse."
            )

        cashier = get_scoped_or_404(
            User,
            cashier_id,
            tenant_id,
            "Cashier",
        )

        customer = None

        if customer_id:
            customer = get_scoped_or_404(
                Customer,
                customer_id,
                tenant_id,
                "Customer",
            )

        # ------------------------------------------------------------------
        # Validate active till shift
        # ------------------------------------------------------------------

        active_shift = _require_open_shift(
            tenant_id=tenant_id,
            branch_id=branch_id,
            till_id=till_id,
            cashier_id=cashier_id,
            session_id=identity.session_id,
        )

        # ------------------------------------------------------------------
        # Validate payments
        # ------------------------------------------------------------------

        total_paid = validate_payments(
            tenant_id,
            payments_payload,
        )

        # ------------------------------------------------------------------
        # Prepare sale identifiers and services
        # ------------------------------------------------------------------

        sale_id = str(uuid4())
        sale_number = generate_sale_number()

        dispensing_service = DispensingService(
            db.session
        )

        prepared_items: list[
            tuple[SaleItem, dict]
        ] = []

        subtotal = Decimal("0.00")
        discount_total = Decimal("0.00")
        tax_total = Decimal("0.00")
        grand_total = Decimal("0.00")

        # ------------------------------------------------------------------
        # Build and validate sale items
        #
        # No inventory mutation occurs in this phase.
        # ------------------------------------------------------------------

        for item_payload in items_payload:
            sale_item, calc = build_sale_item(
                tenant_id=tenant_id,
                item_payload=item_payload,
                customer=customer,
                dispensing_service=dispensing_service,
            )

            prepared_items.append(
                (
                    sale_item,
                    calc,
                )
            )

            subtotal += calc["line_subtotal"]
            discount_total += calc["discount_amount"]
            tax_total += calc["tax_amount"]
            grand_total += calc["line_total"]

        subtotal = q2(subtotal)
        discount_total = q2(discount_total)
        tax_total = q2(tax_total)
        grand_total = q2(grand_total)

        # ------------------------------------------------------------------
        # Finalize payment state
        # ------------------------------------------------------------------

        balance_due = q2(
            grand_total - total_paid
        )

        sale_status = (
            "paid"
            if balance_due <= Decimal("0.00")
            else "partially_paid"
        )

        current_time = now_utc()

        # ------------------------------------------------------------------
        # Persist sale aggregate root
        # ------------------------------------------------------------------

        sale = Sale(
            id=sale_id,
            tenant_id=tenant_id,
            branch_id=branch.id,
            warehouse_id=warehouse.id,
            till_id=till.id,
            till_shift_id=active_shift.id,
            customer_id=(
                customer.id
                if customer
                else None
            ),
            cashier_id=cashier.id,
            sale_number=sale_number,
            sale_date=current_time,
            sale_channel="pos",
            status=sale_status,
            subtotal=subtotal,
            discount_amount=discount_total,
            tax_amount=tax_total,
            total_amount=grand_total,
            paid_amount=total_paid,
            balance_due=balance_due,
            created_at=current_time,
            updated_at=current_time,
        )

        if hasattr(sale, "notes"):
            sale.notes = notes

        db.session.add(sale)

        # SaleItem.sale_id references sales.id.
        # Flush the aggregate root before persisting child rows.
        db.session.flush()

        # ------------------------------------------------------------------
        # Persist sale items and allocate inventory
        # ------------------------------------------------------------------

        dispensing_records = []

        for sale_item, calc in prepared_items:
            sale_item.sale_id = sale_id

            db.session.add(sale_item)

            # InventoryMovement.sale_item_id references sale_items.id.
            # Ensure the sale item exists before inventory allocation
            # generates movement rows.
            db.session.flush()

            stock_allocation = allocate_sale_stock(
                db.session,
                tenant_id=tenant_id,
                branch_id=branch_id,
                warehouse_id=str(warehouse.id),
                product=calc["product"],
                quantity=calc["base_quantity"],
                sale_id=sale_id,
                sale_item_id=str(sale_item.id),
                created_by=cashier_id,
            )

            # Preserve direct batch attribution where the allocation
            # originated entirely from one inventory batch.
            sale_item.batch_id = (
                stock_allocation.single_batch_id
            )

            # --------------------------------------------------------------
            # Controlled-drug / prescription dispensing trace
            # --------------------------------------------------------------

            if calc["dispensing_context"] is not None:
                dispensing_records.append(
                    dispensing_service.build_record(
                        tenant_id=tenant_id,
                        branch_id=branch_id,
                        customer=customer,
                        sale_id=sale_id,
                        sale_item=sale_item,
                        product=calc["product"],
                        context=calc["dispensing_context"],
                        dispensed_by=cashier_id,
                    )
                )

        # ------------------------------------------------------------------
        # Persist dispensing records
        # ------------------------------------------------------------------

        for dispensing_record in dispensing_records:
            db.session.add(
                dispensing_record
            )

        # ------------------------------------------------------------------
        # Persist payments
        # ------------------------------------------------------------------

        for payment in payments_payload:
            db.session.add(
                SalePayment(
                    id=str(uuid4()),
                    sale_id=sale_id,
                    payment_method_id=(
                        payment["payment_method_id"]
                    ),
                    amount=q2(
                        positive_decimal(
                            payment["amount"],
                            "payment amount",
                        )
                    ),
                    reference_number=payment.get(
                        "reference"
                    ),
                    paid_at=now_utc(),
                    received_by=cashier.id,
                )
            )

        # ------------------------------------------------------------------
        # Commit complete checkout atomically
        # ------------------------------------------------------------------

        db.session.commit()

        # ------------------------------------------------------------------
        # Return authoritative persisted sale
        # ------------------------------------------------------------------

        created_sale = (
            db.session.query(Sale)
            .filter(
                Sale.id == sale_id,
                Sale.tenant_id == tenant_id,
            )
            .first()
        )

        return (
            jsonify(
                {
                    "ok": True,
                    "message": (
                        "Sale checkout completed successfully."
                    ),
                    "item": serialize_sale(
                        created_sale,
                        include_children=True,
                    ),
                    "shift_id": str(
                        active_shift.id
                    ),
                }
            ),
            201,
        )

    except ValueError as exc:
        db.session.rollback()

        return _json_error(
            str(exc),
            400,
        )

    except SQLAlchemyError as exc:
        db.session.rollback()

        return _json_error(
            (
                "Database error occurred while "
                f"processing checkout: {exc}"
            ),
            500,
        )

    except Exception as exc:
        db.session.rollback()

        return _json_error(
            (
                "Unexpected error occurred while "
                f"processing checkout: {exc}"
            ),
            500,
        )
    
def get_sale_items_for_sale(sale_id: str) -> list[SaleItem]:
    return (
        db.session.query(SaleItem)
        .filter(sa.cast(SaleItem.sale_id, sa.String) == str(sale_id))
        .order_by(SaleItem.id.asc())
        .all()
    )


def restore_stock_for_void(
    tenant_id: str,
    branch_id: str,
    warehouse_id: str,
    sale_id: str,
    product_id,
    quantity: Decimal,
    created_by: str,
):
    stock_balance = get_stock_balance(
        tenant_id=tenant_id,
        branch_id=str(branch_id),
        warehouse_id=str(warehouse_id),
        product_id=str(product_id),
    )
    if not stock_balance:
        raise ValueError(f"No stock balance found for product_id={product_id}.")

    current_qty = Decimal(str(getattr(stock_balance, "quantity_on_hand", 0)))
    new_qty_on_hand = q4(current_qty + quantity)
    current_reserved = Decimal(str(getattr(stock_balance, "quantity_reserved", 0)))
    new_qty_available = q4(new_qty_on_hand - current_reserved)

    stock_balance.quantity_on_hand = new_qty_on_hand

    if hasattr(stock_balance, "quantity_available"):
        stock_balance.quantity_available = new_qty_available
    if hasattr(stock_balance, "updated_at"):
        stock_balance.updated_at = now_utc()

    movement_time = now_utc()
    movement = InventoryMovement(
        id=str(uuid4()),
        tenant_id=tenant_id,
        branch_id=branch_id,
        warehouse_id=warehouse_id,
        product_id=product_id,
        movement_type="sale_void",
        quantity=q4(quantity),
        reference_type="sale_void",
        reference_id=sale_id,
        created_by=created_by,
        created_at=movement_time,
        updated_at=movement_time,
    )

    if hasattr(movement, "notes"):
        movement.notes = "Stock restored during sale void."

    db.session.add(movement)

@bp.post("/sales/<sale_id>/refund")
@require_permission("sales.refund")
def create_sale_refund(sale_id: str):
    """
    Create a partial or full refund for a completed sale.
    """

    identity = _current_identity()

    tenant_id = identity.tenant_id
    branch_id = identity.branch_id
    user_id = identity.user_id

    payload = request.get_json(silent=True) or {}

    try:
        sale = (
            db.session.query(Sale)
            .filter(
                Sale.id == sale_id,
                Sale.tenant_id == tenant_id,
            )
            .first()
        )

        if not sale:
            return _json_error("Sale not found.", 404)

        if str(sale.branch_id) != str(branch_id):
            return _json_error(
                "You cannot refund sales from another branch.",
                403,
            )

        refund = RefundService(db.session).create_refund(
            identity=identity,
            sale_id=sale_id,
            payload=payload,
        )

        db.session.commit()

        return (
            jsonify(
                {
                    "ok": True,
                    "message": "Refund processed successfully.",
                    "refund": {
                        "id": str(refund.id),
                        "refund_number": refund.refund_number,
                        "status": refund.status,
                        "till_shift_id": str(refund.till_shift_id)
                        if refund.till_shift_id
                        else None,
                        "refund_total_amount": str(refund.refund_total_amount),
                        "stock_returned": refund.stock_returned,
                    },
                }
            ),
            201,
        )

    except RefundError as exc:
        db.session.rollback()
        return _json_error(exc.message, exc.status_code)

    except SQLAlchemyError as exc:
        db.session.rollback()
        return _json_error(
            f"Database error while processing refund: {exc}",
            500,
        )

    except Exception as exc:
        db.session.rollback()
        return _json_error(
            f"Unexpected error while processing refund: {exc}",
            500,
        )


@bp.get("/customers")
@require_permission("customers.view")
def list_customers():
    """
    List customers belonging to the authenticated tenant.
    """

    identity = _current_identity()
    tenant_id = identity.tenant_id

    query = Customer.query.filter_by(
        tenant_id=tenant_id,
    )

    search = (request.args.get("search") or "").strip()
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(
                Customer.first_name.ilike(like),
                Customer.last_name.ilike(like),
                Customer.other_names.ilike(like),
                Customer.phone.ilike(like),
                Customer.email.ilike(like),
                Customer.customer_number.ilike(like),
                Customer.id_number.ilike(like),
            )
        )

    is_active = request.args.get("is_active")
    if is_active is not None:
        query = query.filter(
            Customer.is_active == _to_bool(is_active)
        )

    customers = query.order_by(
        Customer.first_name.asc(),
        Customer.last_name.asc(),
    ).all()

    return jsonify(
        {
            "ok": True,
            "count": len(customers),
            "items": [
                _serialize_customer(customer)
                for customer in customers
            ],
        }
    )


@bp.get("/customers/<customer_id>")
@require_permission("customers.view")
def get_customer(customer_id: str):
    """
    Retrieve a single customer belonging to the authenticated tenant.
    """

    identity = _current_identity()
    tenant_id = identity.tenant_id

    customer = Customer.query.filter_by(
        id=customer_id,
        tenant_id=tenant_id,
    ).first()

    if customer is None:
        return _json_error(
            "Customer not found.",
            404,
        )

    return jsonify(
        {
            "ok": True,
            "item": _serialize_customer(customer),
        }
    )


@bp.post("/customers")
@require_permission("customers.create")
def create_customer():
    """
    Create a customer within the authenticated tenant.
    """

    identity = _current_identity()
    tenant_id = identity.tenant_id

    data = request.get_json(silent=True) or {}

    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip() or None
    other_names = (data.get("other_names") or "").strip() or None
    phone = (data.get("phone") or "").strip() or None
    email = (data.get("email") or "").strip().lower() or None

    if not first_name:
        return _json_error(
            "first_name is required."
        )

    if phone:
        existing_phone = Customer.query.filter_by(
            tenant_id=tenant_id,
            phone=phone,
        ).first()

        if existing_phone is not None:
            return _json_error(
                "A customer with that phone already exists.",
                409,
            )

    if email:
        existing_email = Customer.query.filter_by(
            tenant_id=tenant_id,
            email=email,
        ).first()

        if existing_email is not None:
            return _json_error(
                "A customer with that email already exists.",
                409,
            )

    customer_number = (
        data.get("customer_number") or ""
    ).strip()

    if not customer_number:
        customer_number = _generate_customer_number(
            tenant_id,
        )

    existing_number = Customer.query.filter_by(
        tenant_id=tenant_id,
        customer_number=customer_number,
    ).first()

    if existing_number is not None:
        return _json_error(
            "A customer with that customer_number already exists.",
            409,
        )

    customer = Customer(
        tenant_id=tenant_id,
        customer_number=customer_number,
        first_name=first_name,
        last_name=last_name,
        other_names=other_names,
        phone=phone,
        email=email,
        gender=(data.get("gender") or "").strip() or None,
        date_of_birth=data.get("date_of_birth") or None,
        id_number=(data.get("id_number") or "").strip() or None,
        address=(data.get("address") or "").strip() or None,
        city=(data.get("city") or "").strip() or None,
        loyalty_points=0,
        is_active=_to_bool(
            data.get("is_active"),
            True,
        ),
    )

    try:
        db.session.add(customer)
        db.session.commit()

    except Exception as exc:
        db.session.rollback()

        return _json_error(
            f"Failed to create customer: {exc}",
            500,
        )

    return (
        jsonify(
            {
                "ok": True,
                "message": "Customer created successfully.",
                "item": _serialize_customer(customer),
            }
        ),
        201,
    )
