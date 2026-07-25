from __future__ import annotations

from datetime import datetime, timezone
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
from app.services.tenant.pos.refund_service import RefundError, RefundService
from app.services.tenant.pos.sale_approval_service import ApprovalError, SaleApprovalService

bp = Blueprint("sales", __name__)

TWOPLACES = Decimal("0.01")
FOURPLACES = Decimal("0.0001")


def _json_error(message: str, status: int = 400):
    return jsonify({"ok": False, "error": message}), status


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def q2(value: Decimal) -> Decimal:
    return Decimal(str(value)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def q4(value: Decimal) -> Decimal:
    return Decimal(str(value)).quantize(FOURPLACES, rounding=ROUND_HALF_UP)


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


def _get_tenant_id() -> str | None:
    tenant_id = (
        request.args.get("tenant_id")
        or request.headers.get("X-Tenant-ID")
        or (request.get_json(silent=True) or {}).get("tenant_id")
    )
    return str(tenant_id).strip() if tenant_id else None


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


def resolve_product(tenant_id: str, item_payload: dict) -> tuple[Product, str | None]:
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
        return product, barcode

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

    return product, barcode


def get_item_unit_price(product: Product, item_payload: dict) -> Decimal:
    if item_payload.get("unit_price") is not None:
        return non_negative_decimal(item_payload.get("unit_price"), "unit_price")

    for field in ("default_sale_price", "selling_price", "sale_price", "retail_price", "price"):
        if hasattr(product, field):
            value = getattr(product, field)
            if value is not None:
                return non_negative_decimal(value, field)

    raise ValueError(
        f"unit_price is required for product {product.id} because no sale price field was found or populated."
    )


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
            )
            .first()
        )
        if not payment_method:
            raise ValueError(f"Payment method not found for payment #{index}.")

        amount = positive_decimal(payment.get("amount"), f"payments[{index}].amount")
        total_paid += amount

    return q2(total_paid)


def build_sale_item(
    tenant_id: str,
    branch_id: str,
    warehouse_id: str,
    sale_id: str,
    item_payload: dict,
) -> tuple[SaleItem, dict]:
    product, barcode_used = resolve_product(tenant_id, item_payload)

    quantity = q4(positive_decimal(item_payload.get("quantity"), "quantity"))
    unit_price = q2(get_item_unit_price(product, item_payload))
    discount_amount = q2(
        non_negative_decimal(item_payload.get("discount_amount"), "discount_amount", default=Decimal("0.00"))
    )
    tax_amount = q2(
        non_negative_decimal(item_payload.get("tax_amount"), "tax_amount", default=Decimal("0.00"))
    )

    line_subtotal = q2(quantity * unit_price)
    if discount_amount > line_subtotal:
        raise ValueError(f"discount_amount cannot exceed line subtotal for product_id={product.id}.")

    line_total = q2(line_subtotal - discount_amount + tax_amount)

    require_sufficient_stock(
        tenant_id=tenant_id,
        branch_id=branch_id,
        warehouse_id=warehouse_id,
        product_id=str(product.id),
        quantity_needed=quantity,
    )

    sale_item = SaleItem(
        id=str(uuid4()),
        sale_id=sale_id,
        product_id=product.id,
        quantity=quantity,
        unit_price=unit_price,
        discount_amount=discount_amount,
        tax_amount=tax_amount,
    )

    if hasattr(sale_item, "product_name"):
        sale_item.product_name = getattr(product, "name", None)
    if hasattr(sale_item, "barcode"):
        sale_item.barcode = barcode_used
    if hasattr(sale_item, "sku"):
        sale_item.sku = getattr(product, "internal_sku", None)
    if hasattr(sale_item, "line_subtotal"):
        sale_item.line_subtotal = line_subtotal
    if hasattr(sale_item, "line_total"):
        sale_item.line_total = line_total

    calculated = {
        "product": product,
        "quantity": quantity,
        "line_subtotal": line_subtotal,
        "discount_amount": discount_amount,
        "tax_amount": tax_amount,
        "line_total": line_total,
    }
    return sale_item, calculated


def _require_open_shift(tenant_id: str, till_id: str | None, cashier_id: str | None):
    if not till_id:
        raise ValueError("till_id is required for sales checkout.")
    if not cashier_id:
        raise ValueError("cashier_id is required for sales checkout.")

    shift = (
        db.session.query(TillShift)
        .filter(
            TillShift.tenant_id == tenant_id,
            TillShift.till_id == till_id,
            TillShift.cashier_id == cashier_id,
            TillShift.status == "open",
            TillShift.closed_at.is_(None),
        )
        .order_by(TillShift.opened_at.desc(), TillShift.created_at.desc())
        .first()
    )
    if not shift:
        raise ValueError("No open shift found for this till and cashier.")
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


@bp.post("/sales/checkout")
def checkout_sale():
    tenant_id = _get_tenant_id()
    if not tenant_id:
        return _json_error(
            "tenant_id is required. Pass it as query param, JSON field, or X-Tenant-ID header.",
            400,
        )

    payload = request.get_json(silent=True) or {}

    try:
        branch_id = payload.get("branch_id")
        warehouse_id = payload.get("warehouse_id")
        till_id = payload.get("till_id")
        customer_id = payload.get("customer_id")
        cashier_id = payload.get("cashier_id")
        items_payload = payload.get("items") or []
        payments_payload = payload.get("payments") or []
        notes = payload.get("notes")

        if not branch_id:
            raise ValueError("branch_id is required.")
        if not warehouse_id:
            raise ValueError("warehouse_id is required.")
        if not till_id:
            raise ValueError("till_id is required.")
        if not cashier_id:
            raise ValueError("cashier_id is required.")
        if not items_payload:
            raise ValueError("At least one sale item is required.")

        branch = get_scoped_or_404(Branch, branch_id, tenant_id, "Branch")
        warehouse = get_scoped_or_404(Warehouse, warehouse_id, tenant_id, "Warehouse")
        till = get_scoped_or_404(Till, till_id, tenant_id, "Till")
        cashier = get_scoped_or_404(User, cashier_id, tenant_id, "Cashier")

        customer = None
        if customer_id:
            customer = get_scoped_or_404(Customer, customer_id, tenant_id, "Customer")

        active_shift = _require_open_shift(tenant_id=tenant_id, till_id=till_id, cashier_id=cashier_id)
        total_paid = validate_payments(tenant_id, payments_payload)

        sale_id = str(uuid4())
        sale_number = generate_sale_number()

        sale_items: list[SaleItem] = []
        calculated_items: list[dict] = []

        subtotal = Decimal("0.00")
        discount_total = Decimal("0.00")
        tax_total = Decimal("0.00")
        grand_total = Decimal("0.00")

        for item_payload in items_payload:
            sale_item, calc = build_sale_item(
                tenant_id=tenant_id,
                branch_id=branch_id,
                warehouse_id=warehouse_id,
                sale_id=sale_id,
                item_payload=item_payload,
            )
            sale_items.append(sale_item)
            calculated_items.append(calc)

            subtotal += calc["line_subtotal"]
            discount_total += calc["discount_amount"]
            tax_total += calc["tax_amount"]
            grand_total += calc["line_total"]

        subtotal = q2(subtotal)
        discount_total = q2(discount_total)
        tax_total = q2(tax_total)
        grand_total = q2(grand_total)
        balance_due = q2(grand_total - total_paid)

        sale_status = "paid" if balance_due <= Decimal("0.00") else "partially_paid"
        current_time = now_utc()

        sale = Sale(
            id=sale_id,
            tenant_id=tenant_id,
            branch_id=branch.id,
            warehouse_id=warehouse.id,
            till_id=till.id,
            customer_id=customer.id if customer else None,
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

        for sale_item in sale_items:
            db.session.add(sale_item)

        for payment in payments_payload:
            payment_time = now_utc()
            sale_payment = SalePayment(
                id=str(uuid4()),
                sale_id=sale_id,
                payment_method_id=payment["payment_method_id"],
                amount=q2(positive_decimal(payment["amount"], "payment amount")),
                reference_number=payment.get("reference"),
                paid_at=payment_time,
                received_by=cashier.id,
            )
            db.session.add(sale_payment)

        for calc in calculated_items:
            update_stock_for_sale(
                tenant_id=tenant_id,
                branch_id=branch_id,
                warehouse_id=warehouse_id,
                sale_id=sale_id,
                product=calc["product"],
                quantity=calc["quantity"],
                created_by=cashier.id,
            )

        db.session.commit()

        created_sale = (
            db.session.query(Sale)
            .filter(Sale.id == sale_id, Sale.tenant_id == tenant_id)
            .first()
        )

        return jsonify(
            {
                "ok": True,
                "message": "Sale checkout completed successfully.",
                "item": serialize_sale(created_sale, include_children=True),
                "shift_id": str(active_shift.id),
            }
        ), 201

    except ValueError as exc:
        db.session.rollback()
        return _json_error(str(exc), 400)
    except SQLAlchemyError as exc:
        db.session.rollback()
        return _json_error(f"Database error occurred while processing checkout: {exc}", 500)
    except Exception as exc:
        db.session.rollback()
        return _json_error(f"Unexpected error occurred while processing checkout: {exc}", 500)


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


@bp.post("/sales/<sale_id>/void")
def void_sale(sale_id):
    tenant_id = _get_tenant_id()
    if not tenant_id:
        return _json_error(
            "tenant_id is required. Pass it as query param, JSON field, or X-Tenant-ID header.",
            400,
        )

    payload = request.get_json(silent=True) or {}

    try:
        sale = (
            db.session.query(Sale)
            .filter(Sale.id == sale_id, Sale.tenant_id == tenant_id)
            .first()
        )
        if not sale:
            return _json_error("Sale not found.", 404)

        current_status = (getattr(sale, "status", "") or "").strip().lower()
        if current_status == "voided":
            return _json_error("Sale is already voided.", 409)

        branch_id = getattr(sale, "branch_id", None)
        warehouse_id = getattr(sale, "warehouse_id", None)
        cashier_id = getattr(sale, "cashier_id", None)

        if not branch_id:
            raise ValueError("Sale branch_id is missing.")
        if not warehouse_id:
            raise ValueError("Sale warehouse_id is missing.")
        if not cashier_id:
            raise ValueError("Sale cashier_id is missing.")

        reason = (payload.get("reason") or "").strip()
        sale_items = get_sale_items_for_sale(str(sale.id))
        if not sale_items:
            return _json_error("Sale has no items to void.", 400)

        for item in sale_items:
            quantity = Decimal(str(getattr(item, "quantity", 0)))
            product_id = getattr(item, "product_id", None)
            if not product_id:
                raise ValueError(f"Sale item {item.id} has no product_id.")

            restore_stock_for_void(
                tenant_id=tenant_id,
                branch_id=str(branch_id),
                warehouse_id=str(warehouse_id),
                sale_id=str(sale.id),
                product_id=product_id,
                quantity=quantity,
                created_by=str(cashier_id),
            )

        sale.status = "voided"
        if hasattr(sale, "updated_at"):
            sale.updated_at = now_utc()

        if hasattr(sale, "notes"):
            existing_notes = (getattr(sale, "notes", None) or "").strip()
            void_note = "Sale voided"
            if reason:
                void_note = f"{void_note}: {reason}"
            sale.notes = f"{existing_notes}\n{void_note}".strip() if existing_notes else void_note

        db.session.commit()

        refreshed_sale = (
            db.session.query(Sale)
            .filter(Sale.id == sale_id, Sale.tenant_id == tenant_id)
            .first()
        )

        return jsonify(
            {
                "ok": True,
                "message": "Sale voided successfully.",
                "item": serialize_sale(refreshed_sale, include_children=True),
            }
        ), 200

    except ValueError as exc:
        db.session.rollback()
        return _json_error(str(exc), 400)
    except SQLAlchemyError as exc:
        db.session.rollback()
        return _json_error(f"Database error occurred while voiding sale: {exc}", 500)
    except Exception as exc:
        db.session.rollback()
        return _json_error(f"Unexpected error occurred while voiding sale: {exc}", 500)


@bp.get("/sales")
def list_sales():
    tenant_id = _get_tenant_id()
    if not tenant_id:
        return _json_error(
            "tenant_id is required. Pass it as query param, JSON field, or X-Tenant-ID header.",
            400,
        )

    try:
        page = request.args.get("page", 1, type=int) or 1
        per_page = request.args.get("per_page", 20, type=int) or 20

        if page < 1:
            raise ValueError("page must be greater than or equal to 1.")
        if per_page < 1:
            raise ValueError("per_page must be greater than or equal to 1.")
        if per_page > 100:
            per_page = 100

        query = _apply_sales_filters(db.session.query(Sale), tenant_id)
        summary = _sales_summary(query)
        sale_dt_col = _sale_datetime_column()

        sales = (
            query.order_by(sale_dt_col.desc(), Sale.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        total = summary["sale_count"]

        return jsonify(
            {
                "ok": True,
                "items": [serialize_sale(sale, include_children=False) for sale in sales],
                "pagination": _pagination_meta(page, per_page, total),
                "summary": summary,
                "filters": {
                    "tenant_id": tenant_id,
                    "status": request.args.get("status"),
                    "branch_id": request.args.get("branch_id"),
                    "warehouse_id": request.args.get("warehouse_id"),
                    "till_id": request.args.get("till_id"),
                    "cashier_id": request.args.get("cashier_id"),
                    "customer_id": request.args.get("customer_id"),
                    "sale_number": request.args.get("sale_number"),
                    "q": request.args.get("q") or request.args.get("search"),
                    "date_from": request.args.get("date_from"),
                    "date_to": request.args.get("date_to"),
                },
            }
        ), 200

    except ValueError as exc:
        return _json_error(str(exc), 400)
    except SQLAlchemyError as exc:
        return _json_error(f"Database error occurred while fetching sales: {exc}", 500)
    except Exception as exc:
        return _json_error(f"Unexpected error occurred while fetching sales: {exc}", 500)


@bp.get("/sales/<sale_id>")
def get_sale(sale_id):
    tenant_id = _get_tenant_id()
    if not tenant_id:
        return _json_error(
            "tenant_id is required. Pass it as query param, JSON field, or X-Tenant-ID header.",
            400,
        )

    try:
        sale = (
            db.session.query(Sale)
            .filter(Sale.id == sale_id, Sale.tenant_id == tenant_id)
            .first()
        )
        if not sale:
            return _json_error("Sale not found.", 404)

        return jsonify({"ok": True, "item": serialize_sale(sale, include_children=True)}), 200

    except SQLAlchemyError as exc:
        return _json_error(f"Database error occurred while fetching sale: {exc}", 500)
    except Exception as exc:
        return _json_error(f"Unexpected error occurred while fetching sale: {exc}", 500)


@bp.get("/shifts/<shift_id>/report")
def shift_report(shift_id):
    tenant_id = _get_tenant_id()
    if not tenant_id:
        return _json_error("tenant_id is required.", 400)

    try:
        UUID(str(shift_id))
    except ValueError:
        return _json_error("shift_id must be a valid UUID.", 400)

    try:
        shift = (
            db.session.query(TillShift)
            .filter(TillShift.id == shift_id, TillShift.tenant_id == tenant_id)
            .first()
        )
        if not shift:
            return _json_error("Shift not found.", 404)

        sale_dt_col = _sale_time_for_reporting()
        window_end = shift.closed_at or now_utc()

        shift_till_id = str(shift.till_id) if shift.till_id else None
        shift_cashier_id = str(shift.cashier_id) if shift.cashier_id else None

        sales_query = (
            db.session.query(Sale)
            .filter(
                Sale.tenant_id == tenant_id,
                Sale.till_id == shift_till_id,
                Sale.cashier_id == shift_cashier_id,
                sale_dt_col >= shift.opened_at,
                sale_dt_col <= window_end,
            )
        )

        sales = sales_query.order_by(sale_dt_col.asc(), Sale.created_at.asc()).all()

        summary_row = (
            db.session.query(
                sa.func.count(Sale.id),
                sa.func.coalesce(sa.func.sum(Sale.total_amount), 0),
                sa.func.coalesce(sa.func.sum(Sale.paid_amount), 0),
                sa.func.coalesce(sa.func.sum(Sale.balance_due), 0),
            )
            .filter(
                Sale.tenant_id == tenant_id,
                Sale.till_id == shift_till_id,
                Sale.cashier_id == shift_cashier_id,
                sale_dt_col >= shift.opened_at,
                sale_dt_col <= window_end,
            )
            .one()
        )

        payment_rows = (
            db.session.query(
                SalePayment.payment_method_id,
                sa.func.coalesce(sa.func.sum(SalePayment.amount), 0).label("total_amount"),
                sa.func.count(SalePayment.id).label("payment_count"),
            )
            .join(Sale, Sale.id == SalePayment.sale_id)
            .filter(
                Sale.tenant_id == tenant_id,
                Sale.till_id == shift_till_id,
                Sale.cashier_id == shift_cashier_id,
                sale_dt_col >= shift.opened_at,
                sale_dt_col <= window_end,
            )
            .group_by(SalePayment.payment_method_id)
            .all()
        )

        payments_breakdown = [
            {
                "payment_method_id": str(row.payment_method_id) if row.payment_method_id else None,
                "payment_count": int(row.payment_count or 0),
                "amount": _to_str_decimal(row.total_amount),
            }
            for row in payment_rows
        ]

        return jsonify(
            {
                "ok": True,
                "item": _serialize_shift_report_summary(
                    shift=shift,
                    sale_count=int(summary_row[0] or 0),
                    total_amount=summary_row[1],
                    amount_paid=summary_row[2],
                    balance_due=summary_row[3],
                    payments_breakdown=payments_breakdown,
                ),
                "sales": [serialize_sale(sale, include_children=True) for sale in sales],
            }
        ), 200

    except SQLAlchemyError as exc:
        return _json_error(f"Database error occurred while generating shift report: {exc}", 500)
    except Exception as exc:
        return _json_error(f"Unexpected error occurred while generating shift report: {exc}", 500)


@bp.post("/sales/<sale_id>/refunds")
def create_sale_refund(sale_id):
    tenant_id = _get_tenant_id()
    if not tenant_id:
        return _json_error("tenant_id is required.", 400)

    data = request.get_json(silent=True) or {}

    try:
        refund = RefundService(db.session).create_refund(
            tenant_id=tenant_id,
            sale_id=sale_id,
            payload=data,
        )
        db.session.commit()

        return jsonify(
            {
                "ok": True,
                "item": {
                    "id": refund.id,
                    "sale_id": refund.sale_id,
                    "refund_number": refund.refund_number,
                    "status": refund.status,
                    "refund_subtotal": _to_str_decimal(refund.refund_subtotal),
                    "refund_discount_amount": _to_str_decimal(refund.refund_discount_amount),
                    "refund_tax_amount": _to_str_decimal(refund.refund_tax_amount),
                    "refund_total_amount": _to_str_decimal(refund.refund_total_amount),
                    "stock_returned": bool(refund.stock_returned),
                    "reason": refund.reason,
                    "notes": refund.notes,
                    "created_at": refund.created_at.isoformat() if refund.created_at else None,
                    "updated_at": refund.updated_at.isoformat() if refund.updated_at else None,
                },
                "message": "Refund created successfully.",
            }
        ), 201

    except RefundError as exc:
        db.session.rollback()
        return _json_error(exc.message, exc.status_code)
    except SQLAlchemyError as exc:
        db.session.rollback()
        current_app.logger.exception("Database error occurred while creating refund: %s", exc)
        return _json_error("Database error occurred while creating refund.", 500)
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("Unexpected error occurred while creating refund: %s", exc)
        return _json_error("Unexpected error occurred while creating refund.", 500)

@bp.post("/sales/<sale_id>/refund-requests")
def create_refund_request(sale_id):
    tenant_id = _get_tenant_id()
    if not tenant_id:
        return _json_error("tenant_id is required.", 400)

    payload = request.get_json(silent=True) or {}
    requested_by = payload.get("requested_by")

    if not requested_by:
        return _json_error("requested_by is required.", 400)

    try:
        request_row = SaleApprovalService(db.session).create_refund_request(
            tenant_id=tenant_id,
            sale_id=sale_id,
            requested_by=requested_by,
            payload=payload,
        )
        db.session.commit()
        return jsonify({"ok": True, "item": serialize_sale_action_request(request_row)}), 201

    except ApprovalError as exc:
        db.session.rollback()
        return _json_error(exc.message, exc.status_code)
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("Unexpected error occurred while creating refund request: %s", exc)
        return _json_error("Unexpected error occurred while creating refund request.", 500)

@bp.post("/sales/<sale_id>/void-request")
def create_void_request(sale_id):
    tenant_id = _get_tenant_id()
    if not tenant_id:
        return _json_error("tenant_id is required.", 400)

    payload = request.get_json(silent=True) or {}
    requested_by = payload.get("requested_by")

    if not requested_by:
        return _json_error("requested_by is required.", 400)

    try:
        request_row = SaleApprovalService(db.session).create_void_request(
            tenant_id=tenant_id,
            sale_id=sale_id,
            requested_by=requested_by,
            payload=payload,
        )
        db.session.commit()
        return jsonify({"ok": True, "item": serialize_sale_action_request(request_row)}), 201

    except ApprovalError as exc:
        db.session.rollback()
        return _json_error(exc.message, exc.status_code)
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("Unexpected error occurred while creating void request: %s", exc)
        return _json_error("Unexpected error occurred while creating void request.", 500)

@bp.get("/sales/<sale_id>/refunds")
def list_sale_refunds(sale_id):
    tenant_id = _get_tenant_id()
    if not tenant_id:
        return _json_error("tenant_id is required.", 400)

    sale = (
        db.session.query(Sale)
        .filter(Sale.id == sale_id, Sale.tenant_id == tenant_id)
        .first()
    )
    if not sale:
        return _json_error("Sale not found.", 404)

    refunds = (
        db.session.query(SaleRefund)
        .filter(SaleRefund.sale_id == sale_id, SaleRefund.tenant_id == tenant_id)
        .order_by(SaleRefund.created_at.desc())
        .all()
    )

    items = [
        {
            "id": refund.id,
            "sale_id": refund.sale_id,
            "refund_number": refund.refund_number,
            "status": refund.status,
            "refund_subtotal": _to_str_decimal(refund.refund_subtotal),
            "refund_discount_amount": _to_str_decimal(refund.refund_discount_amount),
            "refund_tax_amount": _to_str_decimal(refund.refund_tax_amount),
            "refund_total_amount": _to_str_decimal(refund.refund_total_amount),
            "stock_returned": bool(refund.stock_returned),
            "reason": refund.reason,
            "notes": refund.notes,
            "created_at": refund.created_at.isoformat() if refund.created_at else None,
            "updated_at": refund.updated_at.isoformat() if refund.updated_at else None,
        }
        for refund in refunds
    ]

    return jsonify(
        {
            "ok": True,
            "sale_id": sale_id,
            "count": len(items),
            "items": items,
        }
    ), 200


@bp.get("/sale-refunds/<refund_id>")
def get_sale_refund(refund_id):
    tenant_id = _get_tenant_id()
    if not tenant_id:
        return _json_error("tenant_id is required.", 400)

    refund = (
        db.session.query(SaleRefund)
        .filter(SaleRefund.id == refund_id, SaleRefund.tenant_id == tenant_id)
        .first()
    )
    if not refund:
        return _json_error("Refund not found.", 404)

    refund_items = (
        db.session.query(SaleRefundItem)
        .filter(SaleRefundItem.refund_id == refund.id, SaleRefundItem.tenant_id == tenant_id)
        .order_by(SaleRefundItem.created_at.asc())
        .all()
    )

    items = [
        {
            "id": item.id,
            "refund_id": item.refund_id,
            "sale_id": item.sale_id,
            "sale_item_id": item.sale_item_id,
            "product_id": item.product_id,
            "batch_id": item.batch_id,
            "quantity": _to_str_decimal(item.quantity, "0.0000"),
            "unit_price": _to_str_decimal(item.unit_price),
            "discount_amount": _to_str_decimal(item.discount_amount),
            "tax_amount": _to_str_decimal(item.tax_amount),
            "line_total": _to_str_decimal(item.line_total),
            "return_to_stock": bool(item.return_to_stock),
            "condition_note": item.condition_note,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        for item in refund_items
    ]

    return jsonify(
        {
            "ok": True,
            "item": {
                "id": refund.id,
                "sale_id": refund.sale_id,
                "refund_number": refund.refund_number,
                "status": refund.status,
                "refund_subtotal": _to_str_decimal(refund.refund_subtotal),
                "refund_discount_amount": _to_str_decimal(refund.refund_discount_amount),
                "refund_tax_amount": _to_str_decimal(refund.refund_tax_amount),
                "refund_total_amount": _to_str_decimal(refund.refund_total_amount),
                "stock_returned": bool(refund.stock_returned),
                "reason": refund.reason,
                "notes": refund.notes,
                "created_at": refund.created_at.isoformat() if refund.created_at else None,
                "updated_at": refund.updated_at.isoformat() if refund.updated_at else None,
                "items": items,
            },
        }
    ), 200


@bp.get("/sale-refunds/<refund_id>/receipt")
def get_sale_refund_receipt(refund_id):
    tenant_id = _get_tenant_id()
    if not tenant_id:
        return _json_error("tenant_id is required.", 400)

    refund = (
        db.session.query(SaleRefund)
        .filter(SaleRefund.id == refund_id, SaleRefund.tenant_id == tenant_id)
        .first()
    )
    if not refund:
        return _json_error("Refund not found.", 404)

    sale = (
        db.session.query(Sale)
        .filter(Sale.id == refund.sale_id, Sale.tenant_id == tenant_id)
        .first()
    )

    refund_items = (
        db.session.query(SaleRefundItem)
        .filter(SaleRefundItem.refund_id == refund.id, SaleRefundItem.tenant_id == tenant_id)
        .order_by(SaleRefundItem.created_at.asc())
        .all()
    )

    payment_rows = (
        db.session.query(SalePayment)
        .filter(
            SalePayment.sale_id == refund.sale_id,
            SalePayment.reference_number == refund.refund_number,
        )
        .order_by(SalePayment.paid_at.asc())
        .all()
    )

    receipt_items = [
        {
            "sale_item_id": item.sale_item_id,
            "product_id": item.product_id,
            "batch_id": item.batch_id,
            "quantity": _to_str_decimal(item.quantity, "0.0000"),
            "unit_price": _to_str_decimal(item.unit_price),
            "discount_amount": _to_str_decimal(item.discount_amount),
            "tax_amount": _to_str_decimal(item.tax_amount),
            "line_total": _to_str_decimal(item.line_total),
            "return_to_stock": bool(item.return_to_stock),
            "condition_note": item.condition_note,
        }
        for item in refund_items
    ]

    payments = [
        {
            "payment_method_id": p.payment_method_id,
            "amount": _to_str_decimal(p.amount),
            "reference_number": p.reference_number,
            "paid_at": p.paid_at.isoformat() if p.paid_at else None,
            "received_by": p.received_by,
        }
        for p in payment_rows
    ]

    return jsonify(
        {
            "ok": True,
            "item": {
                "receipt_type": "sale_refund",
                "refund_id": refund.id,
                "refund_number": refund.refund_number,
                "refund_status": refund.status,
                "sale_id": refund.sale_id,
                "sale_number": sale.sale_number if sale else None,
                "sale_date": _sale_timestamp(sale) if sale else None,
                "refund_date": refund.created_at.isoformat() if refund.created_at else None,
                "branch_id": refund.branch_id,
                "warehouse_id": refund.warehouse_id,
                "till_id": refund.till_id,
                "cashier_id": refund.cashier_id,
                "customer_id": refund.customer_id,
                "reason": refund.reason,
                "notes": refund.notes,
                "stock_returned": bool(refund.stock_returned),
                "refund_subtotal": _to_str_decimal(refund.refund_subtotal),
                "refund_discount_amount": _to_str_decimal(refund.refund_discount_amount),
                "refund_tax_amount": _to_str_decimal(refund.refund_tax_amount),
                "refund_total_amount": _to_str_decimal(refund.refund_total_amount),
                "items": receipt_items,
                "payments": payments,
            },
        }
    ), 200

@bp.get("/sales/<sale_id>/action-requests")
def list_sale_action_requests(sale_id):
    tenant_id = _get_tenant_id()
    if not tenant_id:
        return _json_error("tenant_id is required.", 400)

    rows = (
        db.session.query(SaleActionRequest)
        .filter(
            SaleActionRequest.tenant_id == tenant_id,
            SaleActionRequest.sale_id == sale_id,
        )
        .order_by(SaleActionRequest.created_at.desc())
        .all()
    )

    return jsonify({
        "ok": True,
        "sale_id": sale_id,
        "count": len(rows),
        "items": [serialize_sale_action_request(row) for row in rows],
    }), 200

@bp.post("/action-requests/<request_id>/approve")
def approve_action_request(request_id):
    tenant_id = _get_tenant_id()
    if not tenant_id:
        return _json_error("tenant_id is required.", 400)

    payload = request.get_json(silent=True) or {}
    approved_by = payload.get("approved_by")
    decision_reason = payload.get("decision_reason")

    if not approved_by:
        return _json_error("approved_by is required.", 400)

    try:
        result = SaleApprovalService(db.session).approve_request(
            tenant_id=tenant_id,
            request_id=request_id,
            approved_by=approved_by,
            decision_reason=decision_reason,
        )
        db.session.commit()

        response = {
            "ok": True,
            "message": "Request approved and executed successfully.",
            "request": serialize_sale_action_request(result["request"]),
        }

        if result["result_type"] == "refund":
            refund = result["result"]
            response["item"] = {
                "type": "refund",
                "id": refund.id,
                "sale_id": refund.sale_id,
                "refund_number": refund.refund_number,
                "status": refund.status,
                "refund_total_amount": _to_str_decimal(refund.refund_total_amount),
            }
        else:
            sale = result["result"]
            response["item"] = {
                "type": "sale",
                "id": sale.id,
                "status": sale.status,
            }

        return jsonify(response), 200

    except ApprovalError as exc:
        db.session.rollback()
        return _json_error(exc.message, exc.status_code)
    except RefundError as exc:
        db.session.rollback()
        return _json_error(exc.message, exc.status_code)
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("Unexpected error occurred while approving action request: %s", exc)
        return _json_error("Unexpected error occurred while approving action request.", 500)  

@bp.post("/action-requests/<request_id>/reject")
def reject_action_request(request_id):
    tenant_id = _get_tenant_id()
    if not tenant_id:
        return _json_error("tenant_id is required.", 400)

    payload = request.get_json(silent=True) or {}
    rejected_by = payload.get("rejected_by")
    decision_reason = payload.get("decision_reason")

    if not rejected_by:
        return _json_error("rejected_by is required.", 400)

    try:
        request_row = SaleApprovalService(db.session).reject_request(
            tenant_id=tenant_id,
            request_id=request_id,
            rejected_by=rejected_by,
            decision_reason=decision_reason,
        )
        db.session.commit()
        return jsonify({
            "ok": True,
            "message": "Request rejected successfully.",
            "item": serialize_sale_action_request(request_row),
        }), 200

    except ApprovalError as exc:
        db.session.rollback()
        return _json_error(exc.message, exc.status_code)
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("Unexpected error occurred while rejecting action request: %s", exc)
        return _json_error("Unexpected error occurred while rejecting action request.", 500)              