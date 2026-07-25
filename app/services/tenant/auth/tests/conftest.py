"""
Shared pytest fixtures for AuthorizationService tests.

This module provides lightweight fake domain objects and reusable fixtures
used across the AuthorizationService test suite.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from app.services.tenant.auth.authorization_service import (
    AuthorizationService,
)


# ---------------------------------------------------------------------------
# Fake domain models
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class FakePermission:
    """Simple permission model used by tests."""

    name: str


@dataclass(slots=True)
class FakeRole:
    """Simple role model used by tests."""

    name: str
    permissions: list[FakePermission] = field(default_factory=list)


@dataclass(slots=True)
class FakeBranch:
    """Simple branch model used by tests."""

    id: str


@dataclass(slots=True)
class FakeUser:
    """Simple user model used by tests."""

    id: str = "user-1"
    tenant_id: str = "tenant-1"

    roles: list[FakeRole] = field(default_factory=list)
    branches: list[FakeBranch] = field(default_factory=list)

    is_active: bool = True
    is_disabled: bool = False
    is_locked: bool = False

    is_platform_admin: bool = False
    is_owner: bool = False

    status: str = "active"


# ---------------------------------------------------------------------------
# Builder helpers
# ---------------------------------------------------------------------------


def permission(name: str = "products.read") -> FakePermission:
    """Create a fake permission."""
    return FakePermission(name=name)


def role(
    name: str = "manager",
    permissions: list[FakePermission] | None = None,
) -> FakeRole:
    """Create a fake role."""
    return FakeRole(
        name=name,
        permissions=permissions or [],
    )


def branch(branch_id: str = "branch-1") -> FakeBranch:
    """Create a fake branch."""
    return FakeBranch(id=branch_id)


def user(
    *,
    user_id: str = "user-1",
    tenant_id: str = "tenant-1",
    roles: list[FakeRole] | None = None,
    branches: list[FakeBranch] | None = None,
    is_active: bool = True,
    is_disabled: bool = False,
    is_locked: bool = False,
    is_platform_admin: bool = False,
    is_owner: bool = False,
    status: str = "active",
) -> FakeUser:
    """Create a fake user."""

    return FakeUser(
        id=user_id,
        tenant_id=tenant_id,
        roles=roles or [],
        branches=branches or [],
        is_active=is_active,
        is_disabled=is_disabled,
        is_locked=is_locked,
        is_platform_admin=is_platform_admin,
        is_owner=is_owner,
        status=status,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def authorization_service() -> AuthorizationService:
    """Return a fresh AuthorizationService instance."""

    return AuthorizationService()