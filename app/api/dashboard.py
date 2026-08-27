"""
Hela360 Tenant Dashboard API
============================

Authenticated tenant-administrator dashboard endpoints.

Security
--------
Tenant and branch scope originate exclusively from the authenticated identity.
The frontend is not permitted to supply or override tenant scope.
"""

from __future__ import annotations

from datetime import date

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.services.tenant.auth.decorators import (
    _current_identity,
    require_permission,
)
from app.services.tenant.dashboard import (
    DashboardQueryError,
    DashboardQueryService,
)


bp = Blueprint("dashboard", __name__)


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


def _optional_operational_date() -> date | None:
    """
    Parse an optional YYYY-MM-DD operational date.

    The date represents the tenant-local business day. Timezone resolution
    remains the responsibility of DashboardQueryService.
    """

    raw = (
        request.args.get("operational_date")
        or ""
    ).strip()

    if not raw:
        return None

    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise DashboardQueryError(
            "operational_date must use YYYY-MM-DD format."
        ) from exc


@bp.get("/dashboard/overview")
@require_permission("reports.view")
def dashboard_overview():
    """
    Return the tenant administrator's operational dashboard projection.
    """

    identity = _current_identity()

    try:
        payload = DashboardQueryService(
            db.session
        ).overview(
            tenant_id=identity.tenant_id,
            branch_id=identity.branch_id,
            operational_date=_optional_operational_date(),
        )
    except DashboardQueryError as exc:
        return _json_error(
            str(exc),
            400,
        )

    return jsonify(
        {
            "ok": True,
            "dashboard": payload,
        }
    )
