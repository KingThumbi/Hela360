# app/api_sales.py
from __future__ import annotations

from datetime import datetime, time, timezone
from decimal import Decimal, InvalidOperation

import sqlalchemy as sa
from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import Sale, SaleItem, SalePayment, TillShift

api_sales = Blueprint("api_sales", __name__, url_prefix="/api")


# -------------------------
# Helpers
# -------------------------

def _json_error(message: str, status: int = 400):
    return jsonify({"ok": False, "error": message}), status


def _get_tenant_id() -> str | None:
    tenant_id = (
        request.args.get("tenant_id")
        or request.headers.get("X-Tenant-Id")
        or (request.get_json(silent=True) or {}).get("tenant_id")
    )
    if tenant_id:
        tenant_id = str(tenant_id).strip()
    return tenant_id or None


def _parse_decimal(value, field_name: str, default: Decimal | None = None) -> Decimal | None:
    if value is None or value == "":
        return default
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"Invalid decimal for '{field_name}'.")


def _parse_datetime(value: str | None, field_name: str) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        raise ValueError(
            f"Invalid datetime for '{field_name}'. Use ISO 8601, e.g. 2026-03-19T10:30:00+03:00"
        )


def _parse_date_start(value: str | None, field_name: str) -> datetime | None:
    if not value:
        return None
    try:
        d = datetime.fromisoformat(value).date()
        return datetime.combine(d, time.min).replace(tzinfo=timezone.utc)
    except ValueError:
        raise ValueError(f"Invalid date for '{field_name}'. Use YYYY-MM-DD.")


def _parse_date_end(value: str | None, field_name: str) -> datetime | None:
    if not value:
        return None
    try:
        d = datetime.fromisoformat(value).date()
        return datetime.combine(d, time.max).replace(tzinfo=timezone.utc)
    except ValueError:
        raise ValueError(f"Invalid date for '{field_name}'. Use YYYY-MM-DD.")


def _to_str_decimal(value) -> str:
    if value is None:
        return "0.00"
    return str(value)


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

# -------------------------
# Serializers
# -------------------------

def serialize_sale_item(item: SaleItem) -> dict:
    return {
        "id": str(item.id),
        "sale_id": str(item.sale_id),
        "product_id": str(item.product_id) if getattr(item, "product_id", None) else None,
        "product_name": getattr(item, "product_name", None),
        "sku": getattr(item, "sku", None),
        "quantity": _to_str_decimal(getattr(item, "quantity", None)),
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
        "payment_method_id": (
            str(payment.payment_method_id)
            if getattr(payment, "payment_method_id", None)
            else None
        ),
        "amount": _to_str_decimal(getattr(payment, "amount", None)),
        "reference": getattr(payment, "reference", None),
        "notes": getattr(payment, "notes", None),
        "created_at": payment.created_at.isoformat() if getattr(payment, "created_at", None) else None,
    }


def serialize_sale(sale: Sale, include_children: bool = True) -> dict:
    payload = {
        "id": str(sale.id),
        "tenant_id": str(sale.tenant_id),
        "sale_number": getattr(sale, "sale_number", None),
        "status": getattr(sale, "status", None),
        "branch_id": str(sale.branch_id) if getattr(sale, "branch_id", None) else None,
        "warehouse_id": str(sale.warehouse_id) if getattr(sale, "warehouse_id", None) else None,
        "till_id": str(getattr(sale, "till_id", None)) if getattr(sale, "till_id", None) else None,
        "cashier_id": str(getattr(sale, "cashier_id", None)) if getattr(sale, "cashier_id", None) else None,
        "customer_id": str(sale.customer_id) if getattr(sale, "customer_id", None) else None,
        "subtotal": str(getattr(sale, "subtotal", Decimal("0.00"))),
        "discount_amount": str(getattr(sale, "discount_amount", Decimal("0.00"))),
        "tax_amount": str(getattr(sale, "tax_amount", Decimal("0.00"))),
        "total_amount": str(getattr(sale, "total_amount", Decimal("0.00"))),
        "paid_amount": str(getattr(sale, "paid_amount", Decimal("0.00"))),
        "balance_due": str(getattr(sale, "balance_due", Decimal("0.00"))),
        "sold_at": sale.sale_date.isoformat() if getattr(sale, "sale_date", None) else None,
        "created_at": sale.created_at.isoformat() if getattr(sale, "created_at", None) else None,
        "updated_at": sale.updated_at.isoformat() if getattr(sale, "updated_at", None) else None,
    }

    if include_children:
        sale_id = str(sale.id)

        sale_items = (
            db.session.query(SaleItem)
            .filter(sa.cast(SaleItem.sale_id, sa.String) == sale_id)
            .order_by(SaleItem.id.asc())
            .all()
        )

        sale_payments = (
            db.session.query(SalePayment)
            .filter(sa.cast(SalePayment.sale_id, sa.String) == sale_id)
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


# -------------------------
# Query builders
# -------------------------

def _sale_datetime_column():
    # Prefer sold_at if present, else created_at
    if hasattr(Sale, "sold_at"):
        return Sale.sold_at
    return Sale.created_at


def _apply_sale_filters(query, tenant_id: str):
    sale_dt_col = _sale_datetime_column()

    query = query.filter(Sale.tenant_id == tenant_id)

    status = request.args.get("status")
    if status:
        query = query.filter(Sale.status == status.strip())

    branch_id = request.args.get("branch_id")
    if branch_id:
        query = query.filter(Sale.branch_id == branch_id.strip())

    till_id = request.args.get("till_id")
    if till_id:
        query = query.filter(Sale.till_id == till_id.strip())

    cashier_id = request.args.get("cashier_id")
    if cashier_id:
        query = query.filter(Sale.cashier_id == cashier_id.strip())

    customer_id = request.args.get("customer_id")
    if customer_id:
        query = query.filter(Sale.customer_id == customer_id.strip())

    q = request.args.get("q") or request.args.get("search")
    if q:
        q = q.strip()
        query = query.filter(Sale.sale_number.ilike(f"%{q}%"))

    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    if date_from:
        query = query.filter(sale_dt_col >= _parse_date_start(date_from, "date_from"))
    if date_to:
        query = query.filter(sale_dt_col <= _parse_date_end(date_to, "date_to"))

    return query


def _filtered_sales_summary(base_query):
    subq = base_query.with_entities(
        Sale.id.label("id"),
        Sale.total_amount.label("total_amount"),
        Sale.paid_amount.label("paid_amount"),
        Sale.balance_due.label("balance_due"),
    ).subquery()

    row = db.session.query(
        sa.func.count(subq.c.id),
        sa.func.coalesce(sa.func.sum(subq.c.total_amount), 0),
        sa.func.coalesce(sa.func.sum(subq.c.paid_amount), 0),
        sa.func.coalesce(sa.func.sum(subq.c.balance_due), 0),
    ).one()

    return {
        "sale_count": int(row[0] or 0),
        "total_amount": _to_str_decimal(row[1]),
        "paid_amount": _to_str_decimal(row[2]),
        "balance_due": _to_str_decimal(row[3]),
    }

# -------------------------
# Sales APIs
# -------------------------

@api_sales.get("/sales")
def list_sales():
    tenant_id = _get_tenant_id()
    if not tenant_id:
        return _json_error("tenant_id is required.", 400)

    try:
        page = max(int(request.args.get("page", 1)), 1)
        per_page = min(max(int(request.args.get("per_page", 20)), 1), 100)

        base_query = db.session.query(Sale)
        base_query = _apply_sale_filters(base_query, tenant_id)

        summary = _filtered_sales_summary(base_query)

        sale_dt_col = _sale_datetime_column()
        items = (
            base_query.order_by(sale_dt_col.desc(), Sale.created_at.desc(), Sale.id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        total = summary["sale_count"]

        return jsonify({
            "ok": True,
            "items": [serialize_sale(sale, include_children=False) for sale in items],
            "pagination": _pagination_meta(page, per_page, total),
            "summary": summary,
            "filters": {
                "tenant_id": tenant_id,
                "date_from": request.args.get("date_from"),
                "date_to": request.args.get("date_to"),
                "branch_id": request.args.get("branch_id"),
                "till_id": request.args.get("till_id"),
                "cashier_id": request.args.get("cashier_id"),
                "customer_id": request.args.get("customer_id"),
                "status": request.args.get("status"),
                "q": request.args.get("q") or request.args.get("search"),
            },
        }), 200

    except ValueError as exc:
        return _json_error(str(exc), 400)


@api_sales.get("/sales/<sale_id>")
def get_sale(sale_id):
    tenant_id = _get_tenant_id()
    if not tenant_id:
        return _json_error("tenant_id is required.", 400)

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

    return jsonify({
        "ok": True,
        "item": serialize_sale(sale, include_children=True),
    }), 200

# -------------------------
# Shift helpers
# -------------------------

def _find_open_shift(tenant_id: str, till_id: str | None = None, cashier_id: str | None = None):
    query = db.session.query(TillShift).filter(
        TillShift.tenant_id == tenant_id,
        TillShift.closed_at.is_(None),
        TillShift.status.in_(["open", "opened"]),
    )

    if till_id:
        query = query.filter(TillShift.till_id == till_id)
    if cashier_id:
        query = query.filter(TillShift.cashier_id == cashier_id)

    return query.order_by(TillShift.opened_at.desc(), TillShift.created_at.desc()).first()


# -------------------------
# Shift APIs
# -------------------------

@api_sales.post("/shifts/open")
def open_shift():
    data = request.get_json(silent=True) or {}
    tenant_id = _get_tenant_id()
    if not tenant_id:
        return _json_error("tenant_id is required.", 400)

    till_id = (data.get("till_id") or "").strip()
    cashier_id = (data.get("cashier_id") or "").strip()
    branch_id = (data.get("branch_id") or "").strip()

    if not till_id:
        return _json_error("till_id is required.", 400)
    if not cashier_id:
        return _json_error("cashier_id is required.", 400)
    if not branch_id:
        return _json_error("branch_id is required.", 400)

    try:
        opening_float = _parse_decimal(data.get("opening_float"), "opening_float", default=Decimal("0.00"))
        opened_at = _parse_datetime(data.get("opened_at"), "opened_at") or datetime.now(timezone.utc)
    except ValueError as exc:
        return _json_error(str(exc), 400)

    open_till_shift = _find_open_shift(tenant_id=tenant_id, till_id=till_id)
    if open_till_shift:
        return _json_error("This till already has an open shift.", 409)

    open_cashier_shift = _find_open_shift(tenant_id=tenant_id, cashier_id=cashier_id)
    if open_cashier_shift:
        return _json_error("This cashier already has an open shift.", 409)

    shift = TillShift(
        tenant_id=tenant_id,
        branch_id=branch_id,
        till_id=till_id,
        cashier_id=cashier_id,
        opening_float=opening_float,
        opened_at=opened_at,
        status="open",
    )

    db.session.add(shift)
    db.session.commit()

    return jsonify({
        "ok": True,
        "message": "Shift opened successfully.",
        "item": serialize_shift(shift),
    }), 201


@api_sales.post("/shifts/close")
def close_shift():
    data = request.get_json(silent=True) or {}
    tenant_id = _get_tenant_id()
    if not tenant_id:
        return _json_error("tenant_id is required.", 400)

    shift_id = (data.get("shift_id") or "").strip()
    till_id = (data.get("till_id") or "").strip()
    cashier_id = (data.get("cashier_id") or "").strip()
    notes = data.get("notes")

    try:
        closing_cash = _parse_decimal(data.get("closing_cash"), "closing_cash", default=Decimal("0.00"))
        closed_at = _parse_datetime(data.get("closed_at"), "closed_at") or datetime.now(timezone.utc)
    except ValueError as exc:
        return _json_error(str(exc), 400)

    query = db.session.query(TillShift).filter(TillShift.tenant_id == tenant_id)

    if shift_id:
        query = query.filter(TillShift.id == shift_id)
    else:
        query = query.filter(
            TillShift.closed_at.is_(None),
            TillShift.status.in_(["open", "opened"]),
        )
        if till_id:
            query = query.filter(TillShift.till_id == till_id)
        if cashier_id:
            query = query.filter(TillShift.cashier_id == cashier_id)

    shift = query.order_by(TillShift.opened_at.desc(), TillShift.created_at.desc()).first()
    if not shift:
        return _json_error("Open shift not found.", 404)

    if shift.closed_at is not None or getattr(shift, "status", None) in ("closed", "completed"):
        return _json_error("Shift is already closed.", 409)

    shift.closing_cash = closing_cash
    shift.notes = notes
    shift.closed_at = closed_at
    shift.status = "closed"

    db.session.commit()

    return jsonify({
        "ok": True,
        "message": "Shift closed successfully.",
        "item": serialize_shift(shift),
    }), 200


@api_sales.get("/shifts/current")
def current_shift():
    tenant_id = _get_tenant_id()
    if not tenant_id:
        return _json_error("tenant_id is required.", 400)

    till_id = (request.args.get("till_id") or "").strip() or None
    cashier_id = (request.args.get("cashier_id") or "").strip() or None

    if not till_id and not cashier_id:
        return _json_error("Provide till_id and/or cashier_id.", 400)

    shift = _find_open_shift(
        tenant_id=tenant_id,
        till_id=till_id,
        cashier_id=cashier_id,
    )

    if not shift:
        return jsonify({
            "ok": True,
            "item": None,
        }), 200

    return jsonify({
        "ok": True,
        "item": serialize_shift(shift),
    }), 200