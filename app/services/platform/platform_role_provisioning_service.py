"""
Hela360 Platform Role Provisioning Service
==========================================

Persists and synchronizes Hela360's built-in platform roles.

Responsibilities
----------------
* Create missing built-in platform roles.
* Preserve stable IDs for existing roles.
* Synchronize role metadata with canonical platform policy.
* Synchronize role-permission assignments.
* Never modify custom platform roles.
* Never touch tenant Role or Permission records.
* Never commit or roll back implicitly.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from app.models import (
    PlatformPermission,
    PlatformRole,
)
from app.services.platform.platform_permission_catalogue_service import (
    PlatformPermissionCatalogueService,
)
from app.services.platform.platform_role_policy import (
    SYSTEM_PLATFORM_ROLES,
    PlatformRoleDefinition,
)


@dataclass(frozen=True, slots=True)
class PlatformRoleSyncItem:
    """Synchronization result for one built-in platform role."""

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
class PlatformRoleProvisioningResult:
    """Summary of built-in platform role synchronization."""

    roles: tuple[PlatformRoleSyncItem, ...]

    @property
    def changed(self) -> bool:
        return any(
            item.changed
            for item in self.roles
        )


class PlatformRoleProvisioningService:
    """
    Synchronize built-in Hela360 platform roles.

    Transaction ownership remains with the caller.
    """

    def __init__(self, session) -> None:
        self.session = session

    def synchronize(
        self,
    ) -> PlatformRoleProvisioningResult:
        """Synchronize all built-in platform roles."""

        catalogue = PlatformPermissionCatalogueService(
            self.session
        )

        canonical_permissions = {
            permission.code: permission
            for permission
            in catalogue.canonical_permissions()
        }

        results: list[PlatformRoleSyncItem] = []

        for definition in SYSTEM_PLATFORM_ROLES:
            results.append(
                self._synchronize_role(
                    definition=definition,
                    permissions=canonical_permissions,
                )
            )

        return PlatformRoleProvisioningResult(
            roles=tuple(results),
        )

    def _synchronize_role(
        self,
        *,
        definition: PlatformRoleDefinition,
        permissions: dict[
            str,
            PlatformPermission,
        ],
    ) -> PlatformRoleSyncItem:
        """Synchronize one built-in platform role."""

        role = self.session.scalar(
            select(PlatformRole).where(
                PlatformRole.code
                == definition.code
            )
        )

        created = False
        metadata_updated = False

        if role is None:
            role = PlatformRole(
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

            if (
                role.description
                != definition.description
            ):
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
                "Platform role policy references permissions "
                "missing from the persisted canonical catalogue: "
                + ", ".join(missing_catalogue_codes)
            )

        existing_codes = {
            permission.code
            for permission in role.permissions
        }

        permissions_added = tuple(
            sorted(
                desired_codes - existing_codes
            )
        )

        permissions_removed = tuple(
            sorted(
                existing_codes - desired_codes
            )
        )

        role.permissions = [
            permissions[code]
            for code in sorted(desired_codes)
        ]

        self.session.flush()

        return PlatformRoleSyncItem(
            code=definition.code,
            created=created,
            metadata_updated=metadata_updated,
            permissions_added=permissions_added,
            permissions_removed=permissions_removed,
        )


__all__ = [
    "PlatformRoleProvisioningResult",
    "PlatformRoleProvisioningService",
    "PlatformRoleSyncItem",
]
