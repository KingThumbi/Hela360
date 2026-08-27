"""
Canonical Hela360 Tenant Permission Registry
============================================

This module defines the canonical permission catalogue for tenant-scoped
authorization within Hela360.

Scope
-----
These permissions govern access inside an individual Hela360 tenant.

They MUST NOT be used to represent Hela360 platform/back-office
administration. Platform administration is a separate authorization domain.

Architecture
------------
Permissions are atomic capabilities.

Users receive effective permissions primarily through tenant roles:

    User
      -> Role
          -> Permission

Direct user permission overrides may supplement or deny role-derived
permissions where explicitly required.

Tenant ownership and future platform-administrator authority are separate
authorization concepts and MUST NOT be inferred from role names.

Permission Naming Convention
----------------------------
    resource.action

Examples:

    products.view
    products.create
    sales.refund
    inventory.adjust
    reports.export
    users.manage

The values defined here are the canonical application permission codes.
Database Permission rows are persisted representations of this catalogue and
must remain synchronized with it.
"""

from __future__ import annotations

from collections.abc import Iterable


# ============================================================================
# Permission Registry
# ============================================================================


class Permissions:
    """Canonical tenant-scoped Hela360 permission constants."""

    # ------------------------------------------------------------------
    # Products
    # ------------------------------------------------------------------

    PRODUCTS_VIEW = "products.view"
    PRODUCTS_CREATE = "products.create"
    PRODUCTS_EDIT = "products.edit"
    PRODUCTS_DELETE = "products.delete"

    # ------------------------------------------------------------------
    # Inventory
    # ------------------------------------------------------------------

    INVENTORY_READ = "inventory.read"
    INVENTORY_RECEIVE = "inventory.receive"
    INVENTORY_COUNT = "inventory.count"
    INVENTORY_ADJUST = "inventory.adjust"
    INVENTORY_TRANSFER = "inventory.transfer"

    # ------------------------------------------------------------------
    # Sales / POS
    # ------------------------------------------------------------------

    SALES_READ = "sales.read"
    SALES_CREATE = "sales.create"
    SALES_REFUND = "sales.refund"
    SALES_CANCEL = "sales.cancel"

    # ------------------------------------------------------------------
    # Customers
    # ------------------------------------------------------------------

    CUSTOMERS_VIEW = "customers.view"
    CUSTOMERS_CREATE = "customers.create"
    CUSTOMERS_EDIT = "customers.edit"

    # ------------------------------------------------------------------
    # Suppliers / Procurement
    # ------------------------------------------------------------------

    SUPPLIERS_VIEW = "suppliers.view"
    SUPPLIERS_CREATE = "suppliers.create"
    SUPPLIERS_UPDATE = "suppliers.update"
    SUPPLIERS_DEACTIVATE = "suppliers.deactivate"

    # ------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------

    REPORTS_VIEW = "reports.view"
    REPORTS_EXPORT = "reports.export"

    # ------------------------------------------------------------------
    # User & Role Administration
    # ------------------------------------------------------------------

    USERS_READ = "users.read"
    USERS_MANAGE = "users.manage"

    ROLES_READ = "roles.read"
    ROLES_MANAGE = "roles.manage"

    # ------------------------------------------------------------------
    # Tenant Settings
    # ------------------------------------------------------------------

    SETTINGS_MANAGE = "settings.manage"

    # ------------------------------------------------------------------
    # Branches
    # ------------------------------------------------------------------

    BRANCHES_READ = "branches.read"
    BRANCHES_MANAGE = "branches.manage"

    # ------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------

    AUDIT_VIEW = "audit.view"

    # ------------------------------------------------------------------
    # Tenant Administration
    # ------------------------------------------------------------------

    TENANT_MANAGE = "tenant.manage"


# ============================================================================
# Canonical Catalogue
# ============================================================================


ALL_PERMISSIONS: tuple[str, ...] = tuple(
    value
    for name, value in Permissions.__dict__.items()
    if name.isupper()
)


# ============================================================================
# Validation
# ============================================================================


def is_valid_permission(permission: str) -> bool:
    """Return whether ``permission`` is a canonical tenant permission."""

    return permission in ALL_PERMISSIONS


# ============================================================================
# Permission Matching
# ============================================================================


def _matches(permission: str, granted: str) -> bool:
    """
    Determine whether a granted permission satisfies a requested permission.

    Exact permission codes are the normal authorization mechanism.

    Module wildcards remain supported by the matcher for compatibility with
    existing authorization infrastructure, but wildcard grants are not part
    of the canonical tenant permission catalogue.
    """

    if granted == "*":
        return True

    if granted == permission:
        return True

    if granted.endswith(".*"):
        prefix = granted[:-2]
        return permission.startswith(prefix + ".")

    return False


# ============================================================================
# Permission Checks
# ============================================================================


def has_permission(identity, permission: str) -> bool:
    """Determine whether an authenticated identity has a permission."""

    if identity is None:
        return False

    if getattr(identity, "is_owner", False):
        return True

    permissions = getattr(identity, "permissions", [])

    if not permissions:
        return False

    return any(
        _matches(permission, granted)
        for granted in permissions
    )


def has_any_permission(
    identity,
    permissions: Iterable[str],
) -> bool:
    """Return whether the identity has at least one requested permission."""

    return any(
        has_permission(identity, permission)
        for permission in permissions
    )


def has_all_permissions(
    identity,
    permissions: Iterable[str],
) -> bool:
    """Return whether the identity has every requested permission."""

    return all(
        has_permission(identity, permission)
        for permission in permissions
    )


# ============================================================================
# Utilities
# ============================================================================


def list_permissions() -> list[str]:
    """Return the canonical tenant permission catalogue."""

    return sorted(ALL_PERMISSIONS)


def permission_groups() -> dict[str, list[str]]:
    """Return canonical permissions grouped by module."""

    groups: dict[str, list[str]] = {}

    for permission in sorted(ALL_PERMISSIONS):
        module = permission.split(".")[0]
        groups.setdefault(module, []).append(permission)

    return groups


__all__ = [
    "Permissions",
    "ALL_PERMISSIONS",
    "is_valid_permission",
    "has_permission",
    "has_any_permission",
    "has_all_permissions",
    "list_permissions",
    "permission_groups",
]
