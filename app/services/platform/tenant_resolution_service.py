"""
Hela360 Tenant Resolution Service
=================================

Resolves public workspace identifiers into tenant identities.

This service deliberately separates public workspace resolution from
tenant authentication.

AuthenticationService remains tenant-ID based.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.extensions import db
from app.models import Tenant


@dataclass(frozen=True, slots=True)
class ResolvedTenant:
    id: str
    workspace_slug: str
    display_name: str
    status: str


class TenantResolutionError(Exception):
    """
    Raised when a public workspace cannot be resolved to an eligible tenant.
    """


class TenantResolutionService:
    """
    Resolve tenant workspaces without performing user authentication.
    """

    @staticmethod
    def normalize_workspace(
        workspace: str,
    ) -> str:
        return workspace.strip().lower()

    def resolve_workspace(
        self,
        workspace: str,
    ) -> ResolvedTenant:
        normalized = self.normalize_workspace(
            workspace,
        )

        if not normalized:
            raise TenantResolutionError(
                "Workspace could not be resolved."
            )

        tenant = (
            db.session.query(Tenant)
            .filter(
                Tenant.workspace_slug == normalized,
            )
            .first()
        )

        if tenant is None:
            raise TenantResolutionError(
                "Workspace could not be resolved."
            )

        if tenant.status != "active":
            raise TenantResolutionError(
                "Workspace could not be resolved."
            )

        return ResolvedTenant(
            id=str(tenant.id),
            workspace_slug=tenant.workspace_slug,
            display_name=tenant.display_name,
            status=tenant.status,
        )


tenant_resolution_service = (
    TenantResolutionService()
)


__all__ = [
    "ResolvedTenant",
    "TenantResolutionError",
    "TenantResolutionService",
    "tenant_resolution_service",
]
