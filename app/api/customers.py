from datetime import date

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import Customer
from app.api.utils import current_identity as _current_identity
from app.services.tenant.auth.decorators import require_permission

bp = Blueprint("customers", __name__)


def _json_error(message: str, status: int = 400):
    return jsonify({"ok": False, "error": message}), status


def _to_bool(value, default=False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _positive_int_arg(name: str, default: int):
    raw_value = request.args.get(name)

    if raw_value is None:
        return default, None

    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return None, f"{name} must be a positive integer."

    if value < 1:
        return None, f"{name} must be a positive integer."

    return value, None


def _optional_date(value):
    raw_value = (value or "").strip()

    if not raw_value:
        return None, None

    try:
        return date.fromisoformat(raw_value), None
    except ValueError:
        return None, "date_of_birth must use YYYY-MM-DD."


def _serialize_customer(customer: Customer) -> dict:
    return {
        "id": customer.id,
        "tenant_id": customer.tenant_id,
        "customer_number": customer.customer_number,
        "first_name": customer.first_name,
        "last_name": customer.last_name,
        "other_names": customer.other_names,
        "full_name": " ".join(
            part for part in [
                customer.first_name,
                customer.other_names,
                customer.last_name,
            ] if part
        ).strip(),
        "phone": customer.phone,
        "email": customer.email,
        "gender": customer.gender,
        "date_of_birth": customer.date_of_birth.isoformat() if customer.date_of_birth else None,
        "id_number": customer.id_number,
        "address": customer.address,
        "city": customer.city,
        "loyalty_points": str(customer.loyalty_points) if customer.loyalty_points is not None else "0",
        "is_active": customer.is_active,
        "created_at": customer.created_at.isoformat() if customer.created_at else None,
        "updated_at": customer.updated_at.isoformat() if customer.updated_at else None,
    }


def _generate_customer_number(tenant_id: str) -> str:
    count = Customer.query.filter_by(tenant_id=tenant_id).count() + 1
    return f"CUST-{count:05d}"


@bp.get("/customers")
@require_permission("customers.view")
def list_customers():
    identity = _current_identity()

    tenant_id = identity.tenant_id

    query = Customer.query.filter_by(tenant_id=tenant_id)

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

    page, page_error = _positive_int_arg("page", 1)
    if page_error:
        return _json_error(page_error)

    per_page, per_page_error = _positive_int_arg("per_page", 25)
    if per_page_error:
        return _json_error(per_page_error)

    total = query.count()

    items = query.order_by(
        Customer.first_name.asc(),
        Customer.last_name.asc(),
    ).offset((page - 1) * per_page).limit(per_page).all()

    return jsonify(
        {
            "ok": True,
            "count": total,
            "items": [
                _serialize_customer(item)
                for item in items
            ],
        }
    )


@bp.get("/customers/<customer_id>")
@require_permission("customers.view")
def get_customer(customer_id: str):
    identity = _current_identity()

    tenant_id = identity.tenant_id

    customer = Customer.query.filter_by(
        id=customer_id,
        tenant_id=tenant_id,
    ).first()

    if customer is None:
        return _json_error("Customer not found.", 404)

    return jsonify(
        {
            "ok": True,
            "item": _serialize_customer(customer),
        }
    )


@bp.post("/customers")
@require_permission("customers.create")
def create_customer():
    identity = _current_identity()

    tenant_id = identity.tenant_id

    data = request.get_json(silent=True) or {}

    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip() or None
    other_names = (data.get("other_names") or "").strip() or None
    phone = (data.get("phone") or "").strip() or None
    email = (data.get("email") or "").strip().lower() or None
    date_of_birth, date_error = _optional_date(
        data.get("date_of_birth")
    )

    if date_error:
        return _json_error(date_error)

    if not first_name:
        return _json_error("first_name is required.")

    if phone:
        existing_phone = Customer.query.filter_by(
            tenant_id=tenant_id,
            phone=phone,
        ).first()

        if existing_phone:
            return _json_error(
                "A customer with that phone already exists.",
                409,
            )

    if email:
        existing_email = Customer.query.filter_by(
            tenant_id=tenant_id,
            email=email,
        ).first()

        if existing_email:
            return _json_error(
                "A customer with that email already exists.",
                409,
            )

    customer_number = (
        data.get("customer_number") or ""
    ).strip()

    if not customer_number:
        customer_number = _generate_customer_number(
            tenant_id
        )

    existing_number = Customer.query.filter_by(
        tenant_id=tenant_id,
        customer_number=customer_number,
    ).first()

    if existing_number:
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
        date_of_birth=date_of_birth,
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
