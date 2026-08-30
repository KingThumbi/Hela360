"""
Tenant-facing Hela360 Master Catalogue API.

The master catalogue itself is platform-owned.

These endpoints expose only approved, active catalogue items and annotate
them with Product adoption state for the authenticated tenant.
"""

from flask import Blueprint, jsonify, request

from app.auth.exceptions import AuthenticationError
from app.auth.jwt import get_current_identity
from app.errors import ValidationError
from app.extensions import db
from app.services.tenant.auth.decorators import (
    require_permission,
)
from app.services.tenant.catalogue import (
    MasterCatalogueListFilters,
    MasterCatalogueQueryService,
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
