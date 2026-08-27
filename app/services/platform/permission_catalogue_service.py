"""
Hela360 Permission Catalogue Service
====================================

Synchronizes the persisted Permission catalogue with Hela360's canonical
tenant-scoped permission registry.

Responsibilities
----------------
- Create missing canonical Permission rows.
- Update canonical permission metadata deterministically.
- Preserve stable IDs for existing Permission rows.
- Detect persisted non-canonical permission codes.
- Never silently delete permission records.
- Keep permission catalogue synchronization outside routes and application
  startup side effects.

Scope
-----
This service concerns tenant-scoped Hela360 permissions.

Platform/back-office administration is a separate authorization domain and
must not be introduced into this catalogue.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from app.auth.permissions import ALL_PERMISSIONS
from app.models.auth import Permission


@dataclass(frozen=True, slots=True)
class PermissionDefinition:
    """Canonical persisted metadata for one permission."""

    code: str
    name: str
    module_code: str
    description: str


@dataclass(frozen=True, slots=True)
class PermissionCatalogueSyncResult:
    """Summary of one catalogue synchronization."""

    created: tuple[str, ...]
    updated: tuple[str, ...]
    unchanged: tuple[str, ...]
    unexpected: tuple[str, ...]

    @property
    def changed(self) -> bool:
        return bool(self.created or self.updated)


def _humanize(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").title()


def _definition_for(code: str) -> PermissionDefinition:
    """
    Build deterministic persisted metadata from a canonical permission code.

    Example:
        products.view
        -> module_code: products
        -> name: Products View
        -> description: Allow products view operations.
    """

    module_code, action = code.split(".", 1)

    return PermissionDefinition(
        code=code,
        name=f"{_humanize(module_code)} {_humanize(action)}",
        module_code=module_code,
        description=(
            f"Allow {module_code.replace('_', ' ')} "
            f"{action.replace('_', ' ')} operations."
        ),
    )


CANONICAL_PERMISSION_DEFINITIONS: tuple[PermissionDefinition, ...] = tuple(
    _definition_for(code)
    for code in sorted(ALL_PERMISSIONS)
)


class PermissionCatalogueService:
    """
    Synchronize canonical tenant permission definitions with persistence.

    The supplied SQLAlchemy session owns transaction boundaries. This service
    calls flush() where necessary but never commits or rolls back implicitly.
    """

    def __init__(self, session) -> None:
        self.session = session

    def synchronize(self) -> PermissionCatalogueSyncResult:
        """
        Synchronize persisted permissions with the canonical registry.

        Policy
        ------
        - Missing canonical permissions are created.
        - Existing permission IDs are always preserved.
        - Existing non-empty business metadata is preserved.
        - Missing/blank metadata is safely backfilled.
        - Non-canonical persisted permissions are reported but never deleted.

        The supplied SQLAlchemy session owns the transaction boundary.
        """

        persisted = {
            permission.code: permission
            for permission in self.session.scalars(
                select(Permission).order_by(
                    Permission.code.asc()
                )
            )
        }

        created: list[str] = []
        updated: list[str] = []
        unchanged: list[str] = []

        for definition in CANONICAL_PERMISSION_DEFINITIONS:
            permission = persisted.get(
                definition.code
            )

            if permission is None:
                permission = Permission(
                    code=definition.code,
                    name=definition.name,
                    module_code=definition.module_code,
                    description=definition.description,
                )

                self.session.add(permission)
                self.session.flush()

                persisted[definition.code] = permission
                created.append(definition.code)
                continue

            changed = False

            if not str(
                getattr(permission, "name", "") or ""
            ).strip():
                permission.name = definition.name
                changed = True

            if not str(
                getattr(permission, "module_code", "") or ""
            ).strip():
                permission.module_code = (
                    definition.module_code
                )
                changed = True

            if not str(
                getattr(permission, "description", "") or ""
            ).strip():
                permission.description = (
                    definition.description
                )
                changed = True

            if changed:
                updated.append(definition.code)
            else:
                unchanged.append(definition.code)

        canonical_codes = {
            definition.code
            for definition in CANONICAL_PERMISSION_DEFINITIONS
        }

        unexpected = sorted(
            code
            for code in persisted
            if code not in canonical_codes
        )

        return PermissionCatalogueSyncResult(
            created=tuple(sorted(created)),
            updated=tuple(sorted(updated)),
            unchanged=tuple(sorted(unchanged)),
            unexpected=tuple(unexpected),
        )

    def canonical_permissions(self) -> tuple[Permission, ...]:
        """
        Return persisted canonical permissions in deterministic code order.

        Raises RuntimeError when synchronization has not yet established the
        complete canonical catalogue.
        """

        permissions = tuple(
            self.session.scalars(
                select(Permission)
                .where(
                    Permission.code.in_(ALL_PERMISSIONS)
                )
                .order_by(Permission.code.asc())
            )
        )

        found_codes = {
            permission.code
            for permission in permissions
        }

        missing = sorted(
            set(ALL_PERMISSIONS) - found_codes
        )

        if missing:
            raise RuntimeError(
                "Canonical permission catalogue is incomplete. "
                f"Missing: {', '.join(missing)}"
            )

        return permissions


__all__ = [
    "CANONICAL_PERMISSION_DEFINITIONS",
    "PermissionCatalogueService",
    "PermissionCatalogueSyncResult",
    "PermissionDefinition",
]
