"""
Hela360 Platform Permission Catalogue Service
=============================================

Persists and synchronizes the canonical Hela360 platform permission catalogue.

This service operates only on PlatformPermission records and never touches the
tenant Permission model.

Transaction ownership remains with the caller.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from app.models import PlatformPermission
from app.services.platform.platform_permission_policy import (
    PLATFORM_PERMISSION_DEFINITIONS,
    PlatformPermissionDefinition,
)


@dataclass(frozen=True, slots=True)
class PlatformPermissionSyncItem:
    """Synchronization result for one platform permission."""

    code: str
    created: bool
    metadata_updated: bool

    @property
    def changed(self) -> bool:
        return self.created or self.metadata_updated


@dataclass(frozen=True, slots=True)
class PlatformPermissionCatalogueResult:
    """Summary of platform permission catalogue synchronization."""

    permissions: tuple[PlatformPermissionSyncItem, ...]

    @property
    def changed(self) -> bool:
        return any(
            item.changed
            for item in self.permissions
        )


class PlatformPermissionCatalogueService:
    """
    Synchronize the canonical platform permission catalogue.

    Transaction ownership remains with the caller.
    """

    def __init__(self, session) -> None:
        self.session = session

    def synchronize(
        self,
    ) -> PlatformPermissionCatalogueResult:
        """Synchronize all canonical platform permissions."""

        results: list[PlatformPermissionSyncItem] = []

        for definition in PLATFORM_PERMISSION_DEFINITIONS:
            results.append(
                self._synchronize_permission(
                    definition
                )
            )

        return PlatformPermissionCatalogueResult(
            permissions=tuple(results),
        )

    def canonical_permissions(
        self,
    ) -> tuple[PlatformPermission, ...]:
        """
        Return persisted canonical platform permissions.

        Raises RuntimeError if the persisted catalogue is incomplete.
        """

        codes = {
            definition.code
            for definition in PLATFORM_PERMISSION_DEFINITIONS
        }

        permissions = tuple(
            self.session.scalars(
                select(PlatformPermission)
                .where(
                    PlatformPermission.code.in_(codes)
                )
                .order_by(
                    PlatformPermission.code
                )
            ).all()
        )

        persisted_codes = {
            permission.code
            for permission in permissions
        }

        missing_codes = sorted(
            codes - persisted_codes
        )

        if missing_codes:
            raise RuntimeError(
                "Canonical platform permission catalogue "
                "is incomplete: "
                + ", ".join(missing_codes)
            )

        return permissions

    def _synchronize_permission(
        self,
        definition: PlatformPermissionDefinition,
    ) -> PlatformPermissionSyncItem:
        """Synchronize one canonical platform permission."""

        permission = self.session.scalar(
            select(PlatformPermission).where(
                PlatformPermission.code
                == definition.code
            )
        )

        created = False
        metadata_updated = False

        if permission is None:
            permission = PlatformPermission(
                code=definition.code,
                name=definition.name,
                module_code=definition.module_code,
                description=definition.description,
            )

            self.session.add(permission)
            self.session.flush()

            created = True

        else:
            if permission.name != definition.name:
                permission.name = definition.name
                metadata_updated = True

            if (
                permission.module_code
                != definition.module_code
            ):
                permission.module_code = (
                    definition.module_code
                )
                metadata_updated = True

            if (
                permission.description
                != definition.description
            ):
                permission.description = (
                    definition.description
                )
                metadata_updated = True

            if metadata_updated:
                self.session.flush()

        return PlatformPermissionSyncItem(
            code=definition.code,
            created=created,
            metadata_updated=metadata_updated,
        )


__all__ = [
    "PlatformPermissionCatalogueResult",
    "PlatformPermissionCatalogueService",
    "PlatformPermissionSyncItem",
]
