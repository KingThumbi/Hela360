"""
Canonical Hela360 Tenant System Role Policy
===========================================

Defines built-in tenant roles and the canonical permissions they receive.

This module describes tenant authorization policy only.

Hela360 platform/back-office administration is a separate authorization
domain and MUST NOT be represented by these roles.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.auth.permissions import ALL_PERMISSIONS


@dataclass(frozen=True, slots=True)
class SystemRoleDefinition:
    """Canonical definition of a built-in tenant role."""

    code: str
    name: str
    description: str
    permissions: frozenset[str]


TENANT_ADMINISTRATOR_ROLE = SystemRoleDefinition(
    code="admin",
    name="Administrator",
    description=(
        "Full tenant administration access."
    ),
    permissions=frozenset(
        ALL_PERMISSIONS
    ),
)


SYSTEM_TENANT_ROLES: tuple[
    SystemRoleDefinition,
    ...
] = (
    TENANT_ADMINISTRATOR_ROLE,
)


def get_system_role(
    code: str,
) -> SystemRoleDefinition | None:
    """Return a canonical system role by code."""

    normalized = str(code).strip().lower()

    for role in SYSTEM_TENANT_ROLES:
        if role.code == normalized:
            return role

    return None


__all__ = [
    "SYSTEM_TENANT_ROLES",
    "TENANT_ADMINISTRATOR_ROLE",
    "SystemRoleDefinition",
    "get_system_role",
]
