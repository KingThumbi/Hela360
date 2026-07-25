"""
Permission Registry & Authorization Helpers

This module defines the complete permission catalogue used by Hela360's
Role-Based Access Control (RBAC) system.

Responsibilities
----------------
- Central permission registry
- Permission validation
- Wildcard permission support
- Owner/Super Admin bypass
- Authorization helper functions

Permission Naming Convention
----------------------------
resource.action

Examples
--------
products.read
products.create
sales.refund
inventory.transfer
reports.export
users.manage

Hela360 Enterprise Pharmacy POS & ERP
"""

from __future__ import annotations

from collections.abc import Iterable


# ======================================================================
# Permission Registry
# ======================================================================


class Permissions:
    """Application permission constants."""

    # ------------------------------------------------------------------
    # Products
    # ------------------------------------------------------------------
    PRODUCTS_READ = "products.read"
    PRODUCTS_CREATE = "products.create"
    PRODUCTS_EDIT = "products.edit"
    PRODUCTS_DELETE = "products.delete"

    # ------------------------------------------------------------------
    # Inventory
    # ------------------------------------------------------------------
    INVENTORY_READ = "inventory.read"
    INVENTORY_RECEIVE = "inventory.receive"
    INVENTORY_ADJUST = "inventory.adjust"
    INVENTORY_TRANSFER = "inventory.transfer"

    # ------------------------------------------------------------------
    # Sales
    # ------------------------------------------------------------------
    SALES_READ = "sales.read"
    SALES_CREATE = "sales.create"
    SALES_REFUND = "sales.refund"
    SALES_CANCEL = "sales.cancel"

    # ------------------------------------------------------------------
    # Customers
    # ------------------------------------------------------------------
    CUSTOMERS_READ = "customers.read"
    CUSTOMERS_CREATE = "customers.create"
    CUSTOMERS_EDIT = "customers.edit"

    # ------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------
    REPORTS_VIEW = "reports.view"
    REPORTS_EXPORT = "reports.export"

    # ------------------------------------------------------------------
    # User Administration
    # ------------------------------------------------------------------
    USERS_READ = "users.read"
    USERS_MANAGE = "users.manage"

    ROLES_READ = "roles.read"
    ROLES_MANAGE = "roles.manage"

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
    # Tenant
    # ------------------------------------------------------------------
    TENANT_MANAGE = "tenant.manage"

    # ------------------------------------------------------------------
    # System
    # ------------------------------------------------------------------
    SYSTEM_ADMIN = "*"


# ======================================================================
# Permission Catalogue
# ======================================================================

ALL_PERMISSIONS: tuple[str, ...] = tuple(
    value
    for name, value in Permissions.__dict__.items()
    if name.isupper()
)


# ======================================================================
# Validation
# ======================================================================


def is_valid_permission(permission: str) -> bool:
    """
    Determine whether a permission exists.
    """
    return permission in ALL_PERMISSIONS


# ======================================================================
# Wildcard Matching
# ======================================================================


def _matches(permission: str, granted: str) -> bool:
    """
    Determine whether a granted permission satisfies the requested
    permission.

    Supported Examples
    ------------------

    *

    products.*

    inventory.*

    sales.*

    reports.*

    Exact match:

    products.read
    """

    if granted == "*":
        return True

    if granted == permission:
        return True

    if granted.endswith(".*"):

        prefix = granted[:-2]

        return permission.startswith(prefix + ".")

    return False


# ======================================================================
# Permission Checks
# ======================================================================


def has_permission(identity, permission: str) -> bool:
    """
    Determine whether an authenticated identity possesses
    a required permission.
    """

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
    """
    Require at least one permission.
    """

    return any(
        has_permission(identity, permission)
        for permission in permissions
    )


def has_all_permissions(
    identity,
    permissions: Iterable[str],
) -> bool:
    """
    Require every permission.
    """

    return all(
        has_permission(identity, permission)
        for permission in permissions
    )


# ======================================================================
# Utilities
# ======================================================================


def list_permissions() -> list[str]:
    """
    Return the complete permission catalogue.
    """

    return sorted(ALL_PERMISSIONS)


def permission_groups() -> dict[str, list[str]]:
    """
    Return permissions grouped by module.
    """

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