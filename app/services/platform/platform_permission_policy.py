"""
Canonical Hela360 Platform Permission Policy
============================================

Defines the permissions used by Hela360 Office and other platform-owned
administration surfaces.

This permission catalogue is completely separate from tenant permissions in
``app.auth.permissions``.

Platform permissions govern platform-owned resources such as:

* Hela360 Office access
* Platform users and roles
* Master Catalogue governance
* Supplier intelligence
* Tenant administration
* Platform audit
* Platform settings

Tenant ERP permissions MUST NOT be added here.
"""

from __future__ import annotations

from dataclasses import dataclass


SYSTEM_PERMISSION = "*"


@dataclass(frozen=True, slots=True)
class PlatformPermissionDefinition:
    """Canonical definition of one platform permission."""

    code: str
    name: str
    module_code: str
    description: str


PLATFORM_PERMISSION_DEFINITIONS: tuple[
    PlatformPermissionDefinition,
    ...,
] = (
    PlatformPermissionDefinition(
        code=SYSTEM_PERMISSION,
        name="System Override",
        module_code="system",
        description=(
            "Unrestricted platform authorization override reserved "
            "for the Super Admin role."
        ),
    ),
    PlatformPermissionDefinition(
        code="platform.office.access",
        name="Access Hela360 Office",
        module_code="office",
        description="Enter the Hela360 Office application boundary.",
    ),
    PlatformPermissionDefinition(
        code="platform.users.read",
        name="Read Platform Users",
        module_code="users",
        description="View Hela360 Office user accounts.",
    ),
    PlatformPermissionDefinition(
        code="platform.users.create",
        name="Create Platform Users",
        module_code="users",
        description="Create subordinate Hela360 Office user accounts.",
    ),
    PlatformPermissionDefinition(
        code="platform.users.update",
        name="Update Platform Users",
        module_code="users",
        description="Update Hela360 Office user accounts.",
    ),
    PlatformPermissionDefinition(
        code="platform.users.disable",
        name="Disable Platform Users",
        module_code="users",
        description="Disable or reactivate Hela360 Office user accounts.",
    ),
    PlatformPermissionDefinition(
        code="platform.roles.read",
        name="Read Platform Roles",
        module_code="roles",
        description="View platform roles and their permissions.",
    ),
    PlatformPermissionDefinition(
        code="platform.roles.manage",
        name="Manage Platform Roles",
        module_code="roles",
        description="Create and maintain platform role definitions.",
    ),
    PlatformPermissionDefinition(
        code="platform.catalogue.read",
        name="Read Platform Catalogue",
        module_code="catalogue",
        description="View governed Hela360 Master Catalogue data.",
    ),
    PlatformPermissionDefinition(
        code="platform.catalogue.review",
        name="Review Platform Catalogue",
        module_code="catalogue",
        description="Review Master Catalogue governance records.",
    ),
    PlatformPermissionDefinition(
        code="platform.catalogue.approve",
        name="Approve Platform Catalogue",
        module_code="catalogue",
        description="Approve governed Master Catalogue items.",
    ),
    PlatformPermissionDefinition(
        code="platform.catalogue.manage",
        name="Manage Platform Catalogue",
        module_code="catalogue",
        description="Manage platform-owned Master Catalogue metadata.",
    ),
    PlatformPermissionDefinition(
        code="platform.suppliers.read",
        name="Read Supplier Intelligence",
        module_code="suppliers",
        description="View platform-owned supplier intelligence.",
    ),
    PlatformPermissionDefinition(
        code="platform.suppliers.manage",
        name="Manage Supplier Intelligence",
        module_code="suppliers",
        description="Manage supplier evidence and intelligence.",
    ),
    PlatformPermissionDefinition(
        code="platform.tenants.read",
        name="Read Tenants",
        module_code="tenants",
        description="View Hela360 tenant records and platform status.",
    ),
    PlatformPermissionDefinition(
        code="platform.tenants.manage",
        name="Manage Tenants",
        module_code="tenants",
        description="Manage tenant platform lifecycle and administration.",
    ),
    PlatformPermissionDefinition(
        code="platform.audit.read",
        name="Read Platform Audit",
        module_code="audit",
        description="View platform governance and administration audit events.",
    ),
    PlatformPermissionDefinition(
        code="platform.settings.read",
        name="Read Platform Settings",
        module_code="settings",
        description="View platform-level configuration.",
    ),
    PlatformPermissionDefinition(
        code="platform.settings.manage",
        name="Manage Platform Settings",
        module_code="settings",
        description="Manage platform-level configuration.",
    ),
)


ALL_PLATFORM_PERMISSIONS = frozenset(
    definition.code
    for definition in PLATFORM_PERMISSION_DEFINITIONS
)


def get_platform_permission(
    code: str,
) -> PlatformPermissionDefinition | None:
    """Return a canonical platform permission by code."""

    normalized = str(code).strip()

    for definition in PLATFORM_PERMISSION_DEFINITIONS:
        if definition.code == normalized:
            return definition

    return None


def is_valid_platform_permission(
    code: str,
) -> bool:
    """Return whether a permission belongs to the platform catalogue."""

    return str(code).strip() in ALL_PLATFORM_PERMISSIONS


def list_platform_permissions() -> list[str]:
    """Return the canonical platform permission codes."""

    return sorted(ALL_PLATFORM_PERMISSIONS)


__all__ = [
    "ALL_PLATFORM_PERMISSIONS",
    "PLATFORM_PERMISSION_DEFINITIONS",
    "PlatformPermissionDefinition",
    "SYSTEM_PERMISSION",
    "get_platform_permission",
    "is_valid_platform_permission",
    "list_platform_permissions",
]
