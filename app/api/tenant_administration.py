"""
Hela360 Tenant Administration API
=================================

Tenant ERP administration surface.

This blueprint is deliberately separate from Hela360 Office administration.
It operates exclusively on tenant identities, roles and permissions.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.api.utils import current_identity
from app.extensions import db
from app.services.tenant.administration import (
    TenantAdministrationPermissionAssignmentError,
    TenantAdministrationRoleAssignmentError,
    TenantAdministrationUserPermissionCommandService,
    TenantAdministrationUserQueryService,
    TenantAdministrationUserRoleCommandService,
)
from app.services.tenant.auth.decorators import (
    require_permission,
)


bp = Blueprint(
    "tenant_administration",
    __name__,
)


def _service() -> TenantAdministrationUserQueryService:
    return TenantAdministrationUserQueryService(
        db.session
    )


@bp.get("/users")
@require_permission("users.read")
def list_users():
    identity = current_identity()

    items = _service().list_users(
        tenant_id=str(identity.tenant_id),
    )

    return jsonify(
        {
            "ok": True,
            "count": len(items),
            "items": list(items),
        }
    )


@bp.get("/users/<string:user_id>")
@require_permission("users.read")
def get_user(user_id: str):
    identity = current_identity()

    item = _service().get_user(
        tenant_id=str(identity.tenant_id),
        user_id=user_id,
    )

    return jsonify(
        {
            "ok": True,
            "item": item,
        }
    )


@bp.get("/users/<string:user_id>/roles")
@require_permission("users.read")
def get_user_roles(user_id: str):
    identity = current_identity()

    items = _service().list_user_roles(
        tenant_id=str(identity.tenant_id),
        user_id=user_id,
    )

    return jsonify(
        {
            "ok": True,
            "count": len(items),
            "items": list(items),
        }
    )


@bp.get(
    "/users/<string:user_id>/effective-permissions"
)
@require_permission("users.read")
def get_user_effective_permissions(user_id: str):
    identity = current_identity()

    items = _service().effective_permissions(
        tenant_id=str(identity.tenant_id),
        user_id=user_id,
    )

    return jsonify(
        {
            "ok": True,
            "count": len(items),
            "items": list(items),
        }
    )


@bp.get("/users/<string:user_id>/permissions")
@require_permission("users.read")
def get_user_permission_management(user_id: str):
    identity = current_identity()

    items = _service().permission_management(
        tenant_id=str(identity.tenant_id),
        user_id=user_id,
    )

    return jsonify(
        {
            "ok": True,
            "count": len(items),
            "items": list(items),
        }
    )


@bp.put(
    "/users/<string:user_id>/permissions/"
    "<string:permission_code>"
)
@require_permission("users.manage")
def set_user_permission_override(
    user_id: str,
    permission_code: str,
):
    identity = current_identity()

    payload = request.get_json(silent=True) or {}

    effect = payload.get("effect")
    reason = payload.get("reason")

    if not isinstance(effect, str):
        return (
            jsonify(
                {
                    "ok": False,
                    "error": {
                        "code": (
                            "INVALID_PERMISSION_ASSIGNMENT"
                        ),
                        "message": (
                            "effect must be a string."
                        ),
                    },
                }
            ),
            400,
        )

    if reason is not None and not isinstance(
        reason,
        str,
    ):
        return (
            jsonify(
                {
                    "ok": False,
                    "error": {
                        "code": (
                            "INVALID_PERMISSION_ASSIGNMENT"
                        ),
                        "message": (
                            "reason must be a string."
                        ),
                    },
                }
            ),
            400,
        )

    service = (
        TenantAdministrationUserPermissionCommandService(
            db.session
        )
    )

    try:
        result = service.set_override(
            tenant_id=str(identity.tenant_id),
            actor_user_id=str(identity.user_id),
            target_user_id=user_id,
            permission_code=permission_code,
            effect=effect,
            reason=reason,
        )

        db.session.commit()

    except TenantAdministrationPermissionAssignmentError as exc:
        db.session.rollback()

        return (
            jsonify(
                {
                    "ok": False,
                    "error": {
                        "code": (
                            "PERMISSION_ASSIGNMENT_REJECTED"
                        ),
                        "message": str(exc),
                    },
                }
            ),
            400,
        )

    except Exception:
        db.session.rollback()
        raise

    return jsonify(
        {
            "ok": True,
            "item": {
                "user_id": (
                    result.target_user_id
                ),
                "permission_id": (
                    result.permission_id
                ),
                "permission_code": (
                    result.permission_code
                ),
                "previous_effect": (
                    result.previous_effect
                ),
                "effect": result.effect,
                "changed": result.changed,
            },
        }
    )


@bp.get("/roles")
@require_permission("roles.read")
def list_roles():
    identity = current_identity()

    items = _service().list_roles(
        tenant_id=str(identity.tenant_id),
    )

    return jsonify(
        {
            "ok": True,
            "count": len(items),
            "items": list(items),
        }
    )


@bp.put("/users/<string:user_id>/roles")
@require_permission("users.manage")
def replace_user_roles(user_id: str):
    identity = current_identity()

    payload = request.get_json(silent=True) or {}

    role_ids = payload.get("role_ids")
    reason = payload.get("reason")

    if not isinstance(role_ids, list):
        return (
            jsonify(
                {
                    "ok": False,
                    "error": {
                        "code": "INVALID_ROLE_ASSIGNMENT",
                        "message": (
                            "role_ids must be an array."
                        ),
                    },
                }
            ),
            400,
        )

    if reason is not None and not isinstance(
        reason,
        str,
    ):
        return (
            jsonify(
                {
                    "ok": False,
                    "error": {
                        "code": "INVALID_ROLE_ASSIGNMENT",
                        "message": (
                            "reason must be a string."
                        ),
                    },
                }
            ),
            400,
        )

    service = (
        TenantAdministrationUserRoleCommandService(
            db.session
        )
    )

    try:
        result = service.replace_roles(
            tenant_id=str(identity.tenant_id),
            actor_user_id=str(identity.user_id),
            target_user_id=user_id,
            role_ids=role_ids,
            reason=reason,
        )

        db.session.commit()

    except TenantAdministrationRoleAssignmentError as exc:
        db.session.rollback()

        return (
            jsonify(
                {
                    "ok": False,
                    "error": {
                        "code": "ROLE_ASSIGNMENT_REJECTED",
                        "message": str(exc),
                    },
                }
            ),
            400,
        )

    except Exception:
        db.session.rollback()
        raise

    return jsonify(
        {
            "ok": True,
            "item": {
                "user_id": result.target_user_id,
                "role_ids": list(result.role_ids),
                "added_role_ids": list(
                    result.added_role_ids
                ),
                "removed_role_ids": list(
                    result.removed_role_ids
                ),
                "changed": result.changed,
            },
        }
    )

