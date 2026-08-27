"""
Hela360 Tenant System Role Provisioning Service
===============================================

Persists and synchronizes Hela360's built-in tenant roles.

Responsibilities
----------------
- Create missing built-in tenant roles.
- Preserve stable IDs for existing roles.
- Synchronize role metadata with canonical system-role policy.
- Synchronize role-permission assignments from canonical policy.
- Keep tenant roles strictly tenant-scoped.
- Never derive one tenant's authorization policy from another tenant.
- Never commit or roll back implicitly.

Platform/back-office roles are explicitly outside this service's scope.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from app.models.auth import Permission, Role
from app.models.tenant import Tenant
from app.services.platform.permission_catalogue_service import (
    PermissionCatalogueService,
)
from app.services.platform.system_role_policy import (
    SYSTEM_TENANT_ROLES,
    SystemRoleDefinition,
)


@dataclass(frozen=True, slots=True)
class SystemRoleSyncItem:
    """Synchronization result for one built-in tenant role."""

    code: str
    created: bool
    metadata_updated: bool
    permissions_added: tuple[str, ...]
    permissions_removed: tuple[str, ...]

    @property
    def changed(self) -> bool:
        return (
            self.created
            or self.metadata_updated
            or bool(self.permissions_added)
            or bool(self.permissions_removed)
        )


@dataclass(frozen=True, slots=True)
class SystemRoleProvisioningResult:
    """Summary of built-in role synchronization for one tenant."""

    tenant_id: str
    roles: tuple[SystemRoleSyncItem, ...]

    @property
    def changed(self) -> bool:
        return any(item.changed for item in self.roles)


class SystemRoleProvisioningService:
    """
    Synchronize built-in Hela360 tenant roles.

    Transaction ownership remains with the caller.
    """

    def __init__(self, session) -> None:
        self.session = session

    def synchronize(
        self,
        *,
        tenant_id: str,
    ) -> SystemRoleProvisioningResult:
        """
        Synchronize all built-in tenant roles for ``tenant_id``.

        The canonical permission catalogue must exist before role policy can
        be persisted. This method therefore resolves the canonical persisted
        Permission rows through PermissionCatalogueService.
        """

        tenant_id = str(tenant_id).strip()

        if not tenant_id:
            raise ValueError("tenant_id is required.")

        tenant = self.session.get(
            Tenant,
            tenant_id,
        )

        if tenant is None:
            raise ValueError(
                f"Tenant not found: {tenant_id}"
            )

        catalogue = PermissionCatalogueService(
            self.session
        )

        canonical_permissions = {
            permission.code: permission
            for permission in catalogue.canonical_permissions()
        }

        results: list[SystemRoleSyncItem] = []

        for definition in SYSTEM_TENANT_ROLES:
            results.append(
                self._synchronize_role(
                    tenant_id=tenant_id,
                    definition=definition,
                    permissions=canonical_permissions,
                )
            )

        return SystemRoleProvisioningResult(
            tenant_id=tenant_id,
            roles=tuple(results),
        )

    def _synchronize_role(
        self,
        *,
        tenant_id: str,
        definition: SystemRoleDefinition,
        permissions: dict[str, Permission],
    ) -> SystemRoleSyncItem:
        """Synchronize one built-in role."""

        role = self.session.scalar(
            select(Role).where(
                Role.tenant_id == tenant_id,
                Role.code == definition.code,
            )
        )

        created = False
        metadata_updated = False

        if role is None:
            role = Role(
                tenant_id=tenant_id,
                code=definition.code,
                name=definition.name,
                description=definition.description,
                is_system=True,
            )

            self.session.add(role)
            self.session.flush()

            created = True

        else:
            if role.name != definition.name:
                role.name = definition.name
                metadata_updated = True

            if role.description != definition.description:
                role.description = definition.description
                metadata_updated = True

            if role.is_system is not True:
                role.is_system = True
                metadata_updated = True

        desired_codes = set(
            definition.permissions
        )

        missing_catalogue_codes = sorted(
            desired_codes - set(permissions)
        )

        if missing_catalogue_codes:
            raise RuntimeError(
                "System role policy references permissions "
                "missing from the persisted canonical catalogue: "
                + ", ".join(missing_catalogue_codes)
            )

        existing_codes = {
            permission.code
            for permission in role.permissions
        }

        permissions_added = tuple(
            sorted(desired_codes - existing_codes)
        )

        permissions_removed = tuple(
            sorted(existing_codes - desired_codes)
        )

        role.permissions = [
            permissions[code]
            for code in sorted(desired_codes)
        ]

        self.session.flush()

        return SystemRoleSyncItem(
            code=definition.code,
            created=created,
            metadata_updated=metadata_updated,
            permissions_added=permissions_added,
            permissions_removed=permissions_removed,
        )


__all__ = [
    "SystemRoleProvisioningResult",
    "SystemRoleProvisioningService",
    "SystemRoleSyncItem",
]
