"""
Canonical Hela360 Platform Role Policy
======================================

Defines built-in roles for Hela360 Office and other platform-owned
administration surfaces.

Platform roles are global and MUST NOT be represented by tenant Role records.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.platform.platform_permission_policy import (
    ALL_PLATFORM_PERMISSIONS,
    SYSTEM_PERMISSION,
)


@dataclass(frozen=True, slots=True)
class PlatformRoleDefinition:
    """Canonical definition of one built-in platform role."""

    code: str
    name: str
    description: str
    permissions: frozenset[str]


SUPER_ADMIN_ROLE = PlatformRoleDefinition(
    code="super_admin",
    name="Super Admin",
    description=(
        "Unrestricted Hela360 platform administrator with authority "
        "across all Hela360 Office functions."
    ),
    permissions=frozenset({
        SYSTEM_PERMISSION,
    }),
)


OFFICE_ADMIN_ROLE = PlatformRoleDefinition(
    code="office_admin",
    name="Office Admin",
    description=(
        "Broad Hela360 Office administrator without the Super Admin "
        "system override."
    ),
    permissions=frozenset(
        ALL_PLATFORM_PERMISSIONS
        - {
            SYSTEM_PERMISSION,
        }
    ),
)


CATALOGUE_MANAGER_ROLE = PlatformRoleDefinition(
    code="catalogue_manager",
    name="Catalogue Manager",
    description=(
        "Manages governed Hela360 Master Catalogue workflows."
    ),
    permissions=frozenset({
        "platform.office.access",
        "platform.catalogue.read",
        "platform.catalogue.review",
        "platform.catalogue.approve",
        "platform.catalogue.manage",
        "platform.suppliers.read",
    }),
)


SUPPLIER_INTELLIGENCE_MANAGER_ROLE = PlatformRoleDefinition(
    code="supplier_intelligence_manager",
    name="Supplier Intelligence Manager",
    description=(
        "Manages platform supplier intelligence and supporting evidence."
    ),
    permissions=frozenset({
        "platform.office.access",
        "platform.suppliers.read",
        "platform.suppliers.manage",
        "platform.catalogue.read",
    }),
)


TENANT_OPERATIONS_MANAGER_ROLE = PlatformRoleDefinition(
    code="tenant_operations_manager",
    name="Tenant Operations Manager",
    description=(
        "Manages Hela360 tenant platform operations and lifecycle."
    ),
    permissions=frozenset({
        "platform.office.access",
        "platform.tenants.read",
        "platform.tenants.manage",
        "platform.catalogue.read",
    }),
)


AUDITOR_ROLE = PlatformRoleDefinition(
    code="auditor",
    name="Auditor",
    description=(
        "Read-only access to platform governance and audit information."
    ),
    permissions=frozenset({
        "platform.office.access",
        "platform.catalogue.read",
        "platform.suppliers.read",
        "platform.tenants.read",
        "platform.audit.read",
        "platform.roles.read",
        "platform.users.read",
        "platform.settings.read",
    }),
)


SYSTEM_PLATFORM_ROLES: tuple[
    PlatformRoleDefinition,
    ...,
] = (
    SUPER_ADMIN_ROLE,
    OFFICE_ADMIN_ROLE,
    CATALOGUE_MANAGER_ROLE,
    SUPPLIER_INTELLIGENCE_MANAGER_ROLE,
    TENANT_OPERATIONS_MANAGER_ROLE,
    AUDITOR_ROLE,
)


def get_platform_role(
    code: str,
) -> PlatformRoleDefinition | None:
    """Return a canonical built-in platform role by code."""

    normalized = str(code).strip().lower()

    for role in SYSTEM_PLATFORM_ROLES:
        if role.code == normalized:
            return role

    return None


__all__ = [
    "AUDITOR_ROLE",
    "CATALOGUE_MANAGER_ROLE",
    "OFFICE_ADMIN_ROLE",
    "SUPER_ADMIN_ROLE",
    "SUPPLIER_INTELLIGENCE_MANAGER_ROLE",
    "SYSTEM_PLATFORM_ROLES",
    "TENANT_OPERATIONS_MANAGER_ROLE",
    "PlatformRoleDefinition",
    "get_platform_role",
]
