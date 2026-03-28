from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import Brand, Product, ProductCategory, ProductCode, UnitOfMeasure

bp = Blueprint("products", __name__)


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


def _to_decimal(value, field_name: str, required: bool = False, default=None):
    if value in (None, ""):
        if required:
            raise ValueError(f"{field_name} is required.")
        return default
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{field_name} must be a valid number.")


def _get_tenant_id():
    tenant_id = request.args.get("tenant_id") or request.headers.get("X-Tenant-ID")
    if not tenant_id:
        return None
    return tenant_id.strip()


def _serialize_product(product: Product) -> dict:
    category = ProductCategory.query.get(product.category_id) if product.category_id else None
    brand = Brand.query.get(product.brand_id) if product.brand_id else None
    unit = UnitOfMeasure.query.get(product.unit_id) if product.unit_id else None

    codes = ProductCode.query.filter_by(product_id=product.id).order_by(
        ProductCode.is_primary.desc(),
        ProductCode.created_at.asc(),
    ).all()

    return {
        "id": product.id,
        "tenant_id": product.tenant_id,
        "internal_sku": product.internal_sku,
        "supplier_sku": product.supplier_sku,
        "name": product.name,
        "generic_name": product.generic_name,
        "description": product.description,
        "product_type": product.product_type,
        "track_inventory": product.track_inventory,
        "track_batches": product.track_batches,
        "track_expiry": product.track_expiry,
        "requires_prescription": product.requires_prescription,
        "allow_negative_stock": product.allow_negative_stock,
        "reorder_level": str(product.reorder_level) if product.reorder_level is not None else None,
        "reorder_qty": str(product.reorder_qty) if product.reorder_qty is not None else None,
        "min_sale_price": str(product.min_sale_price) if product.min_sale_price is not None else None,
        "default_sale_price": str(product.default_sale_price) if product.default_sale_price is not None else None,
        "cost_price": str(product.cost_price) if product.cost_price is not None else None,
        "tax_code": product.tax_code,
        "pack_size": product.pack_size,
        "manufacturer": product.manufacturer,
        "country_of_origin": product.country_of_origin,
        "image_url": product.image_url,
        "is_active": product.is_active,
        "category": (
            {"id": category.id, "name": category.name, "code": category.code}
            if category else None
        ),
        "brand": (
            {"id": brand.id, "name": brand.name}
            if brand else None
        ),
        "unit": (
            {"id": unit.id, "code": unit.code, "name": unit.name}
            if unit else None
        ),
        "codes": [
            {
                "id": code.id,
                "code_type": code.code_type,
                "code_value": code.code_value,
                "is_primary": code.is_primary,
                "generated_by_system": code.generated_by_system,
            }
            for code in codes
        ],
        "created_at": product.created_at.isoformat() if product.created_at else None,
        "updated_at": product.updated_at.isoformat() if product.updated_at else None,
    }


def _get_or_create_brand(tenant_id: str, brand_name: str | None):
    if not brand_name:
        return None
    brand_name = brand_name.strip()
    if not brand_name:
        return None

    brand = Brand.query.filter_by(tenant_id=tenant_id, name=brand_name).first()
    if brand:
        return brand

    brand = Brand(
        tenant_id=tenant_id,
        name=brand_name,
        is_active=True,
    )
    db.session.add(brand)
    db.session.flush()
    return brand


def _get_or_create_category(tenant_id: str, category_name: str | None):
    if not category_name:
        return None
    category_name = category_name.strip()
    if not category_name:
        return None

    category = ProductCategory.query.filter_by(tenant_id=tenant_id, name=category_name).first()
    if category:
        return category

    category = ProductCategory(
        tenant_id=tenant_id,
        name=category_name,
        is_active=True,
    )
    db.session.add(category)
    db.session.flush()
    return category


def _get_or_create_unit(tenant_id: str, unit_code: str | None, unit_name: str | None):
    if not unit_code and not unit_name:
        return None

    if unit_code:
        existing = UnitOfMeasure.query.filter_by(
            tenant_id=tenant_id,
            code=unit_code.strip(),
        ).first()
        if existing:
            return existing

    if not unit_code:
        raise ValueError("unit_code is required when creating a new unit.")
    if not unit_name:
        raise ValueError("unit_name is required when creating a new unit.")

    unit = UnitOfMeasure(
        tenant_id=tenant_id,
        code=unit_code.strip(),
        name=unit_name.strip(),
        base_factor=Decimal("1"),
    )
    db.session.add(unit)
    db.session.flush()
    return unit


@bp.get("/products")
def list_products():
    tenant_id = _get_tenant_id()
    if not tenant_id:
        return _json_error("tenant_id is required. Pass it as query param or X-Tenant-ID header.", 400)

    query = Product.query.filter_by(tenant_id=tenant_id)

    search = (request.args.get("search") or "").strip()
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(
                Product.name.ilike(like),
                Product.internal_sku.ilike(like),
                Product.generic_name.ilike(like),
                Product.supplier_sku.ilike(like),
            )
        )

    is_active = request.args.get("is_active")
    if is_active is not None:
        query = query.filter(Product.is_active == _to_bool(is_active))

    product_type = (request.args.get("product_type") or "").strip()
    if product_type:
        query = query.filter(Product.product_type == product_type)

    items = query.order_by(Product.name.asc()).all()

    return jsonify({
        "ok": True,
        "count": len(items),
        "items": [_serialize_product(item) for item in items],
    })


@bp.get("/products/<product_id>")
def get_product(product_id: str):
    tenant_id = _get_tenant_id()
    if not tenant_id:
        return _json_error("tenant_id is required. Pass it as query param or X-Tenant-ID header.", 400)

    product = Product.query.filter_by(id=product_id, tenant_id=tenant_id).first()
    if not product:
        return _json_error("Product not found.", 404)

    return jsonify({
        "ok": True,
        "item": _serialize_product(product),
    })


@bp.post("/products")
def create_product():
    tenant_id = _get_tenant_id()
    if not tenant_id:
        return _json_error("tenant_id is required. Pass it as query param or X-Tenant-ID header.", 400)

    data = request.get_json(silent=True) or {}

    internal_sku = (data.get("internal_sku") or "").strip()
    name = (data.get("name") or "").strip()

    if not internal_sku:
        return _json_error("internal_sku is required.")
    if not name:
        return _json_error("name is required.")

    existing = Product.query.filter_by(tenant_id=tenant_id, internal_sku=internal_sku).first()
    if existing:
        return _json_error("A product with that internal_sku already exists.", 409)

    try:
        category_id = data.get("category_id")
        brand_id = data.get("brand_id")
        unit_id = data.get("unit_id")

        category = None
        brand = None
        unit = None

        if category_id:
            category = ProductCategory.query.filter_by(id=category_id, tenant_id=tenant_id).first()
            if not category:
                return _json_error("category_id not found for this tenant.", 404)
        else:
            category = _get_or_create_category(tenant_id, data.get("category_name"))

        if brand_id:
            brand = Brand.query.filter_by(id=brand_id, tenant_id=tenant_id).first()
            if not brand:
                return _json_error("brand_id not found for this tenant.", 404)
        else:
            brand = _get_or_create_brand(tenant_id, data.get("brand_name"))

        if unit_id:
            unit = UnitOfMeasure.query.filter_by(id=unit_id, tenant_id=tenant_id).first()
            if not unit:
                return _json_error("unit_id not found for this tenant.", 404)
        else:
            unit = _get_or_create_unit(
                tenant_id=tenant_id,
                unit_code=data.get("unit_code"),
                unit_name=data.get("unit_name"),
            )

        product = Product(
            tenant_id=tenant_id,
            category_id=category.id if category else None,
            brand_id=brand.id if brand else None,
            unit_id=unit.id if unit else None,
            internal_sku=internal_sku,
            supplier_sku=(data.get("supplier_sku") or "").strip() or None,
            name=name,
            generic_name=(data.get("generic_name") or "").strip() or None,
            description=(data.get("description") or "").strip() or None,
            product_type=(data.get("product_type") or "stockable").strip(),
            track_inventory=_to_bool(data.get("track_inventory"), True),
            track_batches=_to_bool(data.get("track_batches"), False),
            track_expiry=_to_bool(data.get("track_expiry"), False),
            requires_prescription=_to_bool(data.get("requires_prescription"), False),
            allow_negative_stock=_to_bool(data.get("allow_negative_stock"), False),
            reorder_level=_to_decimal(data.get("reorder_level"), "reorder_level", default=Decimal("0")),
            reorder_qty=_to_decimal(data.get("reorder_qty"), "reorder_qty", default=Decimal("0")),
            min_sale_price=_to_decimal(data.get("min_sale_price"), "min_sale_price"),
            default_sale_price=_to_decimal(data.get("default_sale_price"), "default_sale_price"),
            cost_price=_to_decimal(data.get("cost_price"), "cost_price"),
            tax_code=(data.get("tax_code") or "").strip() or None,
            pack_size=(data.get("pack_size") or "").strip() or None,
            manufacturer=(data.get("manufacturer") or "").strip() or None,
            country_of_origin=(data.get("country_of_origin") or "").strip() or None,
            image_url=(data.get("image_url") or "").strip() or None,
            is_active=_to_bool(data.get("is_active"), True),
        )
        db.session.add(product)
        db.session.flush()

        codes = data.get("codes") or []
        if isinstance(codes, list):
            for code in codes:
                if not isinstance(code, dict):
                    continue

                code_type = (code.get("code_type") or "").strip()
                code_value = (code.get("code_value") or "").strip()
                if not code_type or not code_value:
                    continue

                duplicate_code = ProductCode.query.filter_by(
                    tenant_id=tenant_id,
                    code_value=code_value,
                ).first()
                if duplicate_code:
                    db.session.rollback()
                    return _json_error(f"Product code already exists: {code_value}", 409)

                db.session.add(
                    ProductCode(
                        tenant_id=tenant_id,
                        product_id=product.id,
                        code_type=code_type,
                        code_value=code_value,
                        is_primary=_to_bool(code.get("is_primary"), False),
                        generated_by_system=_to_bool(code.get("generated_by_system"), False),
                    )
                )

        db.session.commit()

    except ValueError as exc:
        db.session.rollback()
        return _json_error(str(exc), 400)
    except Exception as exc:
        db.session.rollback()
        return _json_error(f"Failed to create product: {exc}", 500)

    return jsonify({
        "ok": True,
        "message": "Product created successfully.",
        "item": _serialize_product(product),
    }), 201

@bp.get("/products/by-code/<code_value>")
def get_product_by_code(code_value: str):
    tenant_id = _get_tenant_id()
    if not tenant_id:
        return _json_error("tenant_id is required. Pass it as query param or X-Tenant-ID header.", 400)

    code = ProductCode.query.filter_by(
        tenant_id=tenant_id,
        code_value=code_value,
    ).first()

    if not code:
        return _json_error("Product code not found.", 404)

    product = Product.query.filter_by(
        id=code.product_id,
        tenant_id=tenant_id,
    ).first()

    if not product:
        return _json_error("Product not found.", 404)

    return jsonify({
        "ok": True,
        "item": _serialize_product(product),
    })