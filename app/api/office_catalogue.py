"""
Hela360 Office Catalogue API.

Platform-management read endpoints for governing the Hela360 Master Catalogue.

These endpoints are intentionally separate from the tenant-facing catalogue
API and must not expose tenant Product adoption state.
"""

from flask import Blueprint, jsonify, request

from app.auth.exceptions import AuthenticationError
from app.auth.jwt import get_current_identity
from app.errors import ValidationError
from app.extensions import db
from app.services.platform.master_item_query_service import (
    PlatformMasterItemListFilters,
    PlatformMasterItemQueryService,
)
from app.services.tenant.auth.authorization_service import (
    authorization_service,
)


bp = Blueprint(
    "office_catalogue",
    __name__,
)


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


def _has_office_access(
    identity,
) -> bool:
    """
    Resolve the authenticated authorization context and determine whether
    the identity may enter the Hela360 Office application boundary.

    This is a bootstrap platform-admin boundary. Future Office actions will
    use explicit platform permissions.
    """

    user = authorization_service.authorize(
        identity.user_id,
        tenant_id=identity.tenant_id,
        branch_id=identity.branch_id,
    )

    context = authorization_service.refresh_context(
        user,
        tenant_id=identity.tenant_id,
    )

    return context.is_platform_admin is True


@bp.get("/office/catalogue/master-items")
def list_master_items():
    """
    List platform-owned MasterItems for Hela360 Office governance.
    """

    identity = _current_identity()

    if not _has_office_access(identity):
        return _json_error(
            "Platform administrator access is required.",
            403,
        )

    try:
        filters = (
            PlatformMasterItemListFilters
            .from_query(request.args)
        )

        items, pagination = (
            PlatformMasterItemQueryService(
                db.session
            ).list_items(
                filters=filters
            )
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


__all__ = [
    "bp",
]
