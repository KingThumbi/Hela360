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
from app.services.platform.catalogue_supplier_query_service import (
    CatalogueSupplierListFilters,
    PlatformCatalogueSupplierQueryService,
)
from app.services.platform.catalogue_data_quality_service import (
    PlatformCatalogueDataQualityService,
)
from app.services.platform.master_item_governance_service import (
    MasterItemApprovalConflictError,
    MasterItemGovernanceError,
    MasterItemGovernanceNotFoundError,
    PlatformMasterItemGovernanceService,
)
from app.services.platform.master_item_query_service import (
    PlatformMasterItemListFilters,
    PlatformMasterItemQueryService,
)
from app.services.platform.master_item_supplier_evidence_service import (
    PlatformMasterItemSupplierEvidenceService,
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


@bp.get("/office/catalogue/suppliers")
def list_catalogue_suppliers():
    """
    List platform-owned CatalogueSuppliers with supplier-evidence metrics.
    """

    identity = _current_identity()

    if not _has_office_access(identity):
        return _json_error(
            "Platform administrator access is required.",
            403,
        )

    try:
        filters = (
            CatalogueSupplierListFilters
            .from_query(request.args)
        )

        suppliers, pagination = (
            PlatformCatalogueSupplierQueryService(
                db.session
            ).list_suppliers(
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
            "suppliers": suppliers,
        }
    )


@bp.get(
    "/office/catalogue/suppliers/<supplier_id>"
)
def get_catalogue_supplier(
    supplier_id: str,
):
    """
    Retrieve one platform-owned CatalogueSupplier with mapped
    Master Items and supplier evidence summary metrics.
    """

    identity = _current_identity()

    if not _has_office_access(identity):
        return _json_error(
            "Platform administrator access is required.",
            403,
        )

    try:
        supplier = (
            PlatformCatalogueSupplierQueryService(
                db.session
            ).get_supplier(
                supplier_id=supplier_id
            )
        )

    except ValidationError as exc:
        return _json_error(
            str(exc),
            400,
        )

    if supplier is None:
        return _json_error(
            "Catalogue supplier not found.",
            404,
        )

    return jsonify(
        {
            "ok": True,
            "supplier": supplier,
        }
    )


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


@bp.get(
    "/office/catalogue/master-items/<master_item_id>"
)
def get_master_item(
    master_item_id: str,
):
    """
    Retrieve one platform-owned MasterItem for Office inspection.
    """

    identity = _current_identity()

    if not _has_office_access(identity):
        return _json_error(
            "Platform administrator access is required.",
            403,
        )

    try:
        item = (
            PlatformMasterItemQueryService(
                db.session
            ).get_item(
                master_item_id=master_item_id
            )
        )

    except ValidationError as exc:
        return _json_error(
            str(exc),
            400,
        )

    if item is None:
        return _json_error(
            "Master item not found.",
            404,
        )

    return jsonify(
        {
            "ok": True,
            "item": item,
        }
    )


@bp.get(
    "/office/catalogue/master-items/"
    "<master_item_id>/supplier-evidence"
)
def get_master_item_supplier_evidence(
    master_item_id: str,
):
    """
    Retrieve supplier mappings and price evidence for one MasterItem.
    """

    identity = _current_identity()

    if not _has_office_access(identity):
        return _json_error(
            "Platform administrator access is required.",
            403,
        )

    try:
        evidence = (
            PlatformMasterItemSupplierEvidenceService(
                db.session
            ).get_evidence(
                master_item_id=master_item_id
            )
        )

    except ValidationError as exc:
        return _json_error(
            str(exc),
            400,
        )

    if evidence is None:
        return _json_error(
            "Master item not found.",
            404,
        )

    return jsonify(
        {
            "ok": True,
            "evidence": evidence,
        }
    )


@bp.post(
    "/office/catalogue/master-items/<master_item_id>/approve"
)
def approve_master_item(
    master_item_id: str,
):
    """
    Approve one draft platform-owned MasterItem.
    """

    identity = _current_identity()

    if not _has_office_access(identity):
        return _json_error(
            "Platform administrator access is required.",
            403,
        )

    try:
        result = (
            PlatformMasterItemGovernanceService(
                db.session
            ).approve_item(
                master_item_id=master_item_id,
                user_id=identity.user_id,
                session_id=getattr(
                    identity,
                    "session_id",
                    None,
                ),
            )
        )

        db.session.commit()

    except MasterItemGovernanceNotFoundError as exc:
        db.session.rollback()

        return _json_error(
            str(exc),
            404,
        )

    except MasterItemApprovalConflictError as exc:
        db.session.rollback()

        return _json_error(
            str(exc),
            409,
        )

    except MasterItemGovernanceError as exc:
        db.session.rollback()

        return _json_error(
            str(exc),
            400,
        )

    except Exception:
        db.session.rollback()
        raise

    item = result.master_item

    return jsonify(
        {
            "ok": True,
            "message": "Master Item approved.",
            "item": {
                "id": item.id,
                "master_code": item.master_code,
                "canonical_name": (
                    item.canonical_name
                ),
                "review_status": (
                    item.review_status
                ),
                "is_active": item.is_active,
            },
        }
    )


@bp.get(
    "/office/catalogue/data-quality"
)
def get_catalogue_data_quality():
    """
    Return platform-wide catalogue quality observations.
    """

    identity = _current_identity()

    if not _has_office_access(identity):
        return _json_error(
            "Platform administrator access is required.",
            403,
        )

    summary = (
        PlatformCatalogueDataQualityService(
            db.session
        ).get_summary()
    )

    return jsonify(
        {
            "ok": True,
            "summary": summary,
        }
    )


__all__ = [
    "bp",
]
