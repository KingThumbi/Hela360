from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.errors import ValidationError
from app.models import (
    Brand,
    Product,
    ProductCategory,
    ProductCode,
    ProductUnit,
    TaxCode,
    UnitOfMeasure,
)
from app.services.tenant.products import (
    ProductCommandService,
    ProductDeletionBlockedError,
    ProductIdentityService,
    ProductNotFoundError,
    ProductReferenceService,
    ProductSkuConflictError,
    ProductValidationError,
)
from app.auth.jwt import get_current_identity
from app.auth.exceptions import AuthenticationError
from app.services.tenant.auth.decorators import (
    require_permission,
)
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


def _positive_int_arg(name: str, default: int) -> int:
    value = request.args.get(name)

    if value in (None, ""):
        return default

    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a positive integer.")

    if parsed < 1:
        raise ValueError(f"{name} must be a positive integer.")

    return parsed


def _current_identity():
    """
    Return the authenticated JWT identity.

    All product endpoints operate within the authenticated user's tenant
    and branch context. Authentication is expected to have been enforced
    by the route decorators before this helper is called.
    """
    identity = get_current_identity()

    if identity is None:
        raise AuthenticationError(
            "Authentication is required."
        )

    return identity

def _serialize_product(product: Product) -> dict:
    category = (
        db.session.get(
            ProductCategory,
            product.category_id,
        )
        if product.category_id
        else None
    )

    brand = (
        db.session.get(
            Brand,
            product.brand_id,
        )
        if product.brand_id
        else None
    )
    unit = UnitOfMeasure.query.get(product.unit_id) if product.unit_id else None

    codes = ProductCode.query.filter_by(product_id=product.id).order_by(
        ProductCode.is_primary.desc(),
        ProductCode.created_at.asc(),
    ).all()

    return {
        "id": product.id,
        "tenant_id": product.tenant_id,
        "master_item_id": product.master_item_id,
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
                "product_unit_id": str(code.product_unit_id) if code.product_unit_id else None,
                "is_primary": code.is_primary,
                "generated_by_system": code.generated_by_system,
            }
            for code in codes
        ],
        "created_at": product.created_at.isoformat() if product.created_at else None,
        "updated_at": product.updated_at.isoformat() if product.updated_at else None,
    }


def _serialize_product_unit(product_unit: ProductUnit) -> dict:
    unit = db.session.get(UnitOfMeasure, product_unit.unit_id)
    return {
        "id": str(product_unit.id),
        "tenant_id": str(product_unit.tenant_id),
        "product_id": str(product_unit.product_id),
        "unit": (
            {
                "id": str(unit.id),
                "code": unit.code,
                "name": unit.name,
            }
            if unit
            else None
        ),
        "conversion_factor_to_base": str(product_unit.conversion_factor_to_base),
        "is_base": bool(product_unit.is_base),
        "can_sell": bool(product_unit.can_sell),
        "can_receive": bool(product_unit.can_receive),
        "sale_price": (
            str(product_unit.sale_price)
            if product_unit.sale_price is not None
            else None
        ),
        "minimum_sale_price": (
            str(product_unit.minimum_sale_price)
            if product_unit.minimum_sale_price is not None
            else None
        ),
        "is_active": bool(product_unit.is_active),
        "created_at": product_unit.created_at.isoformat() if product_unit.created_at else None,
        "updated_at": product_unit.updated_at.isoformat() if product_unit.updated_at else None,
    }


def _get_or_create_brand(
    tenant_id: str,
    brand_name: str | None,
):
    return ProductReferenceService(
        db.session
    ).resolve_brand(
        tenant_id=tenant_id,
        brand_name=brand_name,
    )


def _get_or_create_category(
    tenant_id: str,
    category_name: str | None,
):
    return ProductReferenceService(
        db.session
    ).resolve_category(
        tenant_id=tenant_id,
        category_name=category_name,
    )


def _get_or_create_unit(
    tenant_id: str,
    unit_code: str | None,
    unit_name: str | None,
):
    return ProductReferenceService(
        db.session
    ).resolve_unit(
        tenant_id=tenant_id,
        unit_code=unit_code,
        unit_name=unit_name,
    )


@bp.get("/products")
@require_permission("products.view")
def list_products():

    identity = _current_identity()

    tenant_id = identity.tenant_id

    try:
        page = _positive_int_arg("page", 1)
        per_page = _positive_int_arg("per_page", 25)
    except ValueError as exc:
        return _json_error(str(exc), 400)

    query = Product.query.filter_by(
        tenant_id=tenant_id,
    )

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

    total = query.count()
    items = (
        query.order_by(Product.name.asc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return jsonify({
        "ok": True,
        "count": total,
        "items": [_serialize_product(item) for item in items],
    })


@bp.get("/products/<product_id>")
@require_permission("products.view")
def get_product(product_id: str):
    """
    Retrieve a single product belonging to the authenticated tenant.
    """

    identity = _current_identity()

    tenant_id = identity.tenant_id

    product = Product.query.filter_by(
        id=product_id,
        tenant_id=tenant_id,
    ).first()

    if product is None:
        return _json_error("Product not found.", 404)

    return jsonify(
        {
            "ok": True,
            "item": _serialize_product(product),
        }
    )


@bp.get("/products/<product_id>/units")
@require_permission("products.view")
def list_product_units(product_id: str):
    identity = _current_identity()
    tenant_id = identity.tenant_id

    product = Product.query.filter_by(
        id=product_id,
        tenant_id=tenant_id,
    ).first()

    if product is None:
        return _json_error("Product not found.", 404)

    units = (
        ProductUnit.query.filter_by(
            tenant_id=tenant_id,
            product_id=product.id,
        )
        .order_by(ProductUnit.is_base.desc(), ProductUnit.created_at.asc())
        .all()
    )

    return jsonify(
        {
            "ok": True,
            "items": [_serialize_product_unit(unit) for unit in units],
        }
    )


@bp.post("/products")
@require_permission("products.create")
def create_product():
    """
    Create a product within the authenticated tenant.

    Tenant ownership is derived from the authenticated JWT and cannot
    be supplied or overridden by the client.
    """

    identity = _current_identity()

    tenant_id = identity.tenant_id

    data = request.get_json(silent=True) or {}

    internal_sku = (data.get("internal_sku") or "").strip()
    name = (data.get("name") or "").strip()

    if not name:
        return _json_error("name is required.")

    try:
        # -------------------------------------------------------------
        # Internal SKU
        # -------------------------------------------------------------

        identity_service = ProductIdentityService(
            db.session
        )

        internal_sku = identity_service.resolve_internal_sku(
            tenant_id=tenant_id,
            supplied_sku=internal_sku,
        )

        # -------------------------------------------------------------
        # Tax Code
        # -------------------------------------------------------------

        requested_tax_code = (
            data.get("tax_code") or ""
        ).strip()

        resolved_tax_code = None

        if requested_tax_code:
            tax_code = TaxCode.query.filter_by(
                tenant_id=tenant_id,
                code=requested_tax_code,
                is_active=True,
            ).first()

            if tax_code is None:
                return _json_error(
                    "tax_code is invalid or inactive for this tenant.",
                    400,
                )

            resolved_tax_code = tax_code.code
        category_id = data.get("category_id")
        brand_id = data.get("brand_id")
        unit_id = data.get("unit_id")

        category = None
        brand = None
        unit = None

        # -------------------------------------------------------------
        # Category
        # -------------------------------------------------------------

        if category_id:
            category = ProductCategory.query.filter_by(
                id=category_id,
                tenant_id=tenant_id,
            ).first()

            if category is None:
                return _json_error(
                    "category_id not found for this tenant.",
                    404,
                )
        else:
            category = _get_or_create_category(
                tenant_id,
                data.get("category_name"),
            )

        # -------------------------------------------------------------
        # Brand
        # -------------------------------------------------------------

        if brand_id:
            brand = Brand.query.filter_by(
                id=brand_id,
                tenant_id=tenant_id,
            ).first()

            if brand is None:
                return _json_error(
                    "brand_id not found for this tenant.",
                    404,
                )
        else:
            brand = _get_or_create_brand(
                tenant_id,
                data.get("brand_name"),
            )

        # -------------------------------------------------------------
        # Unit of Measure
        # -------------------------------------------------------------

        if unit_id:
            unit = UnitOfMeasure.query.filter_by(
                id=unit_id,
                tenant_id=tenant_id,
            ).first()

            if unit is None:
                return _json_error(
                    "unit_id not found for this tenant.",
                    404,
                )
        else:
            unit = _get_or_create_unit(
                tenant_id=tenant_id,
                unit_code=data.get("unit_code"),
                unit_name=data.get("unit_name"),
            )

        # -------------------------------------------------------------
        # Product
        # -------------------------------------------------------------

        product = Product(
            tenant_id=tenant_id,
            category_id=category.id if category else None,
            brand_id=brand.id if brand else None,
            unit_id=unit.id if unit else None,
            internal_sku=internal_sku,
            supplier_sku=(
                (data.get("supplier_sku") or "").strip()
                or None
            ),
            name=name,
            generic_name=(
                (data.get("generic_name") or "").strip()
                or None
            ),
            description=(
                (data.get("description") or "").strip()
                or None
            ),
            product_type=(
                (data.get("product_type") or "stockable").strip()
            ),
            track_inventory=_to_bool(
                data.get("track_inventory"),
                True,
            ),
            track_batches=_to_bool(
                data.get("track_batches"),
                False,
            ),
            track_expiry=_to_bool(
                data.get("track_expiry"),
                False,
            ),
            requires_prescription=_to_bool(
                data.get("requires_prescription"),
                False,
            ),
            allow_negative_stock=_to_bool(
                data.get("allow_negative_stock"),
                False,
            ),
            reorder_level=_to_decimal(
                data.get("reorder_level"),
                "reorder_level",
                default=Decimal("0"),
            ),
            reorder_qty=_to_decimal(
                data.get("reorder_qty"),
                "reorder_qty",
                default=Decimal("0"),
            ),
            min_sale_price=_to_decimal(
                data.get("min_sale_price"),
                "min_sale_price",
            ),
            default_sale_price=_to_decimal(
                data.get("default_sale_price"),
                "default_sale_price",
            ),
            cost_price=_to_decimal(
                data.get("cost_price"),
                "cost_price",
            ),
            tax_code=resolved_tax_code,
            pack_size=(
                (data.get("pack_size") or "").strip()
                or None
            ),
            manufacturer=(
                (data.get("manufacturer") or "").strip()
                or None
            ),
            country_of_origin=(
                (data.get("country_of_origin") or "").strip()
                or None
            ),
            image_url=(
                (data.get("image_url") or "").strip()
                or None
            ),
            # Product lifecycle state is not client-controlled during
            # creation. New products always enter the catalogue as active.
            # Archive and restore operations own lifecycle transitions.
            is_active=True,
        )

        db.session.add(product)
        db.session.flush()

        if unit:
            db.session.add(
                ProductUnit(
                    tenant_id=tenant_id,
                    product_id=product.id,
                    unit_id=unit.id,
                    conversion_factor_to_base=Decimal("1"),
                    is_base=True,
                    can_sell=True,
                    can_receive=True,
                    sale_price=product.default_sale_price,
                    minimum_sale_price=product.min_sale_price,
                    is_active=True,
                )
            )

        # -------------------------------------------------------------
        # Product Codes
        # -------------------------------------------------------------

        codes = data.get("codes") or []

        if isinstance(codes, list):
            for code in codes:

                if not isinstance(code, dict):
                    continue

                code_type = (
                    code.get("code_type") or ""
                ).strip()

                code_value = (
                    code.get("code_value") or ""
                ).strip()

                if not code_type or not code_value:
                    continue

                duplicate_code = ProductCode.query.filter_by(
                    tenant_id=tenant_id,
                    code_value=code_value,
                ).first()

                if duplicate_code:
                    db.session.rollback()

                    return _json_error(
                        f"Product code already exists: {code_value}",
                        409,
                    )

                product_unit_id = (code.get("product_unit_id") or "").strip() or None
                if product_unit_id:
                    product_unit = ProductUnit.query.filter_by(
                        id=product_unit_id,
                        tenant_id=tenant_id,
                        product_id=product.id,
                    ).first()
                    if product_unit is None:
                        db.session.rollback()
                        return _json_error(
                            f"Product unit not found: {product_unit_id}",
                            404,
                        )

                db.session.add(
                    ProductCode(
                        tenant_id=tenant_id,
                        product_id=product.id,
                        product_unit_id=product_unit_id,
                        code_type=code_type,
                        code_value=code_value,
                        is_primary=_to_bool(
                            code.get("is_primary"),
                            False,
                        ),
                        generated_by_system=_to_bool(
                            code.get("generated_by_system"),
                            False,
                        ),
                    )
                )

        db.session.commit()

    except ProductSkuConflictError as exc:
        db.session.rollback()
        return _json_error(str(exc), 409)

    except (ValueError, ValidationError) as exc:
        db.session.rollback()
        return _json_error(str(exc), 400)

    except Exception as exc:
        db.session.rollback()
        return _json_error(
            f"Failed to create product: {exc}",
            500,
        )

    return (
        jsonify(
            {
                "ok": True,
                "message": "Product created successfully.",
                "item": _serialize_product(product),
            }
        ),
        201,
    )

@bp.patch("/products/<product_id>")
@require_permission("products.edit")
def update_product(product_id: str):
    """
    Update approved product master-data fields.

    Structural identity, inventory configuration, units, codes and lifecycle
    state are intentionally excluded from ordinary product editing.
    """

    identity = _current_identity()
    tenant_id = identity.tenant_id

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return _json_error(
            "A product update object is required.",
            400,
        )

    changes = dict(data)

    try:
        if "category_id" in changes:
            raw_category_id = changes["category_id"]

            if raw_category_id in (None, ""):
                changes["category_id"] = None
            else:
                category = (
                    ProductCategory.query
                    .filter_by(
                        id=str(raw_category_id).strip(),
                        tenant_id=tenant_id,
                        is_active=True,
                    )
                    .first()
                )

                if category is None:
                    raise ProductValidationError(
                        "Selected category is not available."
                    )

                changes["category_id"] = str(category.id)

        if "brand_id" in changes:
            raw_brand_id = changes["brand_id"]

            if raw_brand_id in (None, ""):
                changes["brand_id"] = None
            else:
                brand = (
                    Brand.query
                    .filter_by(
                        id=str(raw_brand_id).strip(),
                        tenant_id=tenant_id,
                        is_active=True,
                    )
                    .first()
                )

                if brand is None:
                    raise ProductValidationError(
                        "Selected brand is not available."
                    )

                changes["brand_id"] = str(brand.id)

        if "tax_code" in changes:
            raw_tax_code = changes["tax_code"]

            if raw_tax_code in (None, ""):
                changes["tax_code"] = None
            else:
                tax_code = (
                    TaxCode.query
                    .filter_by(
                        tenant_id=tenant_id,
                        code=str(raw_tax_code).strip(),
                        is_active=True,
                    )
                    .first()
                )

                if tax_code is None:
                    raise ProductValidationError(
                        "Selected tax code is not available."
                    )

                changes["tax_code"] = tax_code.code

        product = ProductCommandService(
            db.session
        ).update(
            tenant_id=tenant_id,
            product_id=product_id,
            changes=changes,
        )

        db.session.commit()

    except ProductNotFoundError as exc:
        db.session.rollback()
        return _json_error(str(exc), 404)

    except ProductValidationError as exc:
        db.session.rollback()
        return _json_error(str(exc), 400)

    except Exception as exc:
        db.session.rollback()
        return _json_error(
            f"Failed to update product: {exc}",
            500,
        )

    return jsonify(
        {
            "ok": True,
            "message": "Product updated.",
            "item": _serialize_product(product),
        }
    ), 200


@bp.delete("/products/<product_id>")
@require_permission("products.delete")
def delete_product(product_id: str):
    """
    Permanently delete an unused archived tenant-owned product.

    A product must already be archived and must have no historical or
    non-zero stock dependencies. Product-owned configuration records and
    zero stock projections may be cleaned up by the command service.
    """

    identity = _current_identity()

    try:
        product = ProductCommandService(
            db.session
        ).delete_permanently(
            tenant_id=identity.tenant_id,
            product_id=product_id,
        )

        deleted_product_id = str(product.id)

        db.session.commit()

    except ProductNotFoundError as exc:
        db.session.rollback()
        return _json_error(str(exc), 404)

    except ProductDeletionBlockedError as exc:
        db.session.rollback()

        return (
            jsonify(
                {
                    "ok": False,
                    "error": str(exc),
                    "code": "PRODUCT_DELETION_BLOCKED",
                    "blockers": [
                        {
                            "code": blocker.code,
                            "count": blocker.count,
                        }
                        for blocker in exc.blockers
                    ],
                }
            ),
            409,
        )

    except Exception as exc:
        db.session.rollback()
        return _json_error(
            f"Failed to permanently delete product: {exc}",
            500,
        )

    return (
        jsonify(
            {
                "ok": True,
                "message": "Product permanently deleted.",
                "id": deleted_product_id,
            }
        ),
        200,
    )


@bp.post("/products/<product_id>/archive")
@require_permission("products.edit")
def archive_product(product_id: str):
    """
    Archive a tenant-owned product.

    Archiving preserves historical records while removing the product from
    normal operational use.
    """

    identity = _current_identity()

    try:
        result = ProductCommandService(
            db.session
        ).archive(
            tenant_id=identity.tenant_id,
            product_id=product_id,
        )

        db.session.commit()

    except ProductNotFoundError as exc:
        db.session.rollback()
        return _json_error(str(exc), 404)

    except Exception as exc:
        db.session.rollback()
        return _json_error(
            f"Failed to archive product: {exc}",
            500,
        )

    return jsonify(
        {
            "ok": True,
            "message": (
                "Product archived."
                if result.changed
                else "Product is already archived."
            ),
            "item": _serialize_product(
                result.product
            ),
        }
    ), 200


@bp.post("/products/<product_id>/restore")
@require_permission("products.edit")
def restore_product(product_id: str):
    """
    Restore an archived tenant-owned product.
    """

    identity = _current_identity()

    try:
        result = ProductCommandService(
            db.session
        ).restore(
            tenant_id=identity.tenant_id,
            product_id=product_id,
        )

        db.session.commit()

    except ProductNotFoundError as exc:
        db.session.rollback()
        return _json_error(str(exc), 404)

    except Exception as exc:
        db.session.rollback()
        return _json_error(
            f"Failed to restore product: {exc}",
            500,
        )

    return jsonify(
        {
            "ok": True,
            "message": (
                "Product restored."
                if result.changed
                else "Product is already active."
            ),
            "item": _serialize_product(
                result.product
            ),
        }
    ), 200


@bp.get("/products/tax-codes")
@require_permission("products.view")
def list_product_tax_codes():
    """
    Return active product tax classifications for the authenticated tenant.

    Tax configuration is tenant-owned. The client cannot request or inspect
    another tenant's tax-code catalogue.
    """

    identity = _current_identity()
    tenant_id = identity.tenant_id

    tax_codes = (
        TaxCode.query
        .filter_by(
            tenant_id=tenant_id,
            is_active=True,
        )
        .order_by(
            TaxCode.rate.asc(),
            TaxCode.code.asc(),
        )
        .all()
    )

    return jsonify(
        {
            "ok": True,
            "items": [
                {
                    "id": str(tax_code.id),
                    "code": tax_code.code,
                    "name": tax_code.name,
                    "rate": str(tax_code.rate),
                    "description": tax_code.description,
                }
                for tax_code in tax_codes
            ],
        }
    ), 200


@bp.get("/products/by-code/<code_value>")
@require_permission("products.view")
def get_product_by_code(code_value: str):
    """
    Retrieve a product using one of its registered product codes.

    Tenant access is derived from the authenticated JWT rather than
    client-supplied request parameters.
    """

    identity = _current_identity()
    tenant_id = identity.tenant_id

    code = ProductCode.query.filter_by(
        tenant_id=tenant_id,
        code_value=code_value,
    ).first()

    if code is None:
        return _json_error("Product code not found.", 404)

    product = Product.query.filter_by(
        id=code.product_id,
        tenant_id=tenant_id,
    ).first()

    if product is None:
        return _json_error("Product not found.", 404)

    return jsonify(
        {
            "ok": True,
            "item": _serialize_product(product),
        }
    )
