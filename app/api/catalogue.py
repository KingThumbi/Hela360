"""
Tenant-facing Hela360 Master Catalogue API.

The master catalogue itself is platform-owned.

These endpoints expose only approved, active catalogue items and annotate
them with Product adoption state for the authenticated tenant.
"""

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from app.auth.exceptions import AuthenticationError
from app.auth.jwt import get_current_identity
from app.errors import ValidationError
from app.extensions import db
from app.models import Product
from app.services.tenant.auth.decorators import (
    require_permission,
)
from app.services.tenant.catalogue import (
    MasterCatalogueAdoptionError,
    MasterCatalogueAdoptionService,
    MasterCatalogueListFilters,
    MasterCatalogueQueryService,
    MasterItemAlreadyAdoptedError,
    MasterItemNotAvailableError,
)
from app.services.tenant.products import (
    ProductSkuConflictError,
)


bp = Blueprint("catalogue", __name__)


def _json_error(
    message: str,
    status: int = 400,
):
    return (
        jsonify(
            {
                "ok": False,
                "error": message,
            }
        ),
        status,
    )


def _already_adopted_response(
    product: Product,
):
    return (
        jsonify(
            {
                "ok": False,
                "error": (
                    "This catalogue item is already "
                    "in your product catalogue."
                ),
                "code": (
                    "master_item_already_adopted"
                ),
                "product": {
                    "id": product.id,
                    "master_item_id": (
                        product.master_item_id
                    ),
                    "internal_sku": (
                        product.internal_sku
                    ),
                    "name": product.name,
                    "is_active": product.is_active,
                },
            }
        ),
        409,
    )


def _current_identity():
    identity = get_current_identity()

    if identity is None:
        raise AuthenticationError(
            "Authentication is required."
        )

    return identity


@bp.get("/catalogue/items")
@require_permission("products.view")
def list_catalogue_items():
    """
    List approved Hela360 catalogue items with tenant adoption state.
    """

    identity = _current_identity()

    try:
        filters = (
            MasterCatalogueListFilters
            .from_query(request.args)
        )

        service = MasterCatalogueQueryService(
            db.session
        )

        items, pagination = service.list_items(
            tenant_id=identity.tenant_id,
            filters=filters,
        )

    except ValidationError as exc:
        return _json_error(
            str(exc),
            400,
        )

    return jsonify(
        {
            "ok": True,
            "count": pagination["total"],
            "pagination": pagination,
            "items": items,
        }
    )


@bp.get("/catalogue/items/<master_item_id>")
@require_permission("products.view")
def get_catalogue_item(
    master_item_id: str,
):
    """
    Retrieve one approved Hela360 catalogue item.
    """

    identity = _current_identity()

    service = MasterCatalogueQueryService(
        db.session
    )

    try:
        item = service.get_item(
            tenant_id=identity.tenant_id,
            master_item_id=master_item_id,
        )

    except ValidationError as exc:
        return _json_error(
            str(exc),
            400,
        )

    if item is None:
        return _json_error(
            "Catalogue item not found.",
            404,
        )

    return jsonify(
        {
            "ok": True,
            "item": item,
        }
    )


@bp.post("/catalogue/items/<master_item_id>/adopt")
@require_permission("products.create")
def adopt_catalogue_item(
    master_item_id: str,
):
    """
    Adopt one approved master catalogue item into the tenant Product catalogue.
    """

    identity = _current_identity()

    data = request.get_json(silent=True)

    if data is None:
        data = {}

    if not isinstance(data, dict):
        return _json_error(
            "A catalogue adoption object is required.",
            400,
        )

    try:
        result = MasterCatalogueAdoptionService(
            db.session
        ).adopt(
            tenant_id=identity.tenant_id,
            master_item_id=master_item_id,
            internal_sku=data.get("internal_sku"),
            name=data.get("name"),
            category_name=data.get(
                "category_name"
            ),
            brand_name=data.get(
                "brand_name"
            ),
            unit_code=data.get(
                "unit_code"
            ),
            unit_name=data.get(
                "unit_name"
            ),
            user_id=identity.user_id,
            branch_id=identity.branch_id,
            session_id=getattr(
                identity,
                "session_id",
                None,
            ),
        )

        db.session.commit()

    except MasterItemAlreadyAdoptedError as exc:
        db.session.rollback()

        return _already_adopted_response(
            exc.product
        )

    except MasterItemNotAvailableError as exc:
        db.session.rollback()

        return _json_error(
            str(exc),
            404,
        )

    except ProductSkuConflictError as exc:
        db.session.rollback()

        return _json_error(
            str(exc),
            409,
        )

    except (
        MasterCatalogueAdoptionError,
        ValueError,
        ValidationError,
    ) as exc:
        db.session.rollback()

        return _json_error(
            str(exc),
            400,
        )

    except IntegrityError:
        db.session.rollback()

        existing_product = (
            db.session.query(Product)
            .filter(
                Product.tenant_id
                == identity.tenant_id,
                Product.master_item_id
                == master_item_id,
            )
            .first()
        )

        if existing_product is not None:
            return _already_adopted_response(
                existing_product
            )

        supplied_sku = (
            data.get("internal_sku")
            if isinstance(data, dict)
            else None
        )
        normalized_sku = (
            str(supplied_sku).strip()
            if supplied_sku is not None
            else ""
        )

        if normalized_sku:
            sku_product = (
                db.session.query(Product)
                .filter(
                    Product.tenant_id
                    == identity.tenant_id,
                    Product.internal_sku
                    == normalized_sku,
                )
                .first()
            )

            if sku_product is not None:
                return _json_error(
                    (
                        "A product with that "
                        "internal_sku already exists."
                    ),
                    409,
                )

        raise

    except Exception:
        db.session.rollback()
        raise

    product = result.product

    return (
        jsonify(
            {
                "ok": True,
                "message": (
                    "Catalogue item added to your "
                    "product catalogue."
                ),
                "item": {
                    "id": product.id,
                    "tenant_id": product.tenant_id,
                    "master_item_id": (
                        product.master_item_id
                    ),
                    "internal_sku": (
                        product.internal_sku
                    ),
                    "name": product.name,
                    "generic_name": (
                        product.generic_name
                    ),
                    "category_id": (
                        product.category_id
                    ),
                    "brand_id": (
                        product.brand_id
                    ),
                    "unit_id": (
                        product.unit_id
                    ),
                    "requires_prescription": (
                        product.requires_prescription
                    ),
                    "manufacturer": (
                        product.manufacturer
                    ),
                    "country_of_origin": (
                        product.country_of_origin
                    ),
                    "is_active": (
                        product.is_active
                    ),
                },
            }
        ),
        201,
    )
