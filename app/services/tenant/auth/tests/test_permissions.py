"""
Tests for AuthorizationService permission evaluation.

Covers:

- get_permissions
- permission_count
- get_permission_objects
- refresh_context
- has_permission
- has_any_permission
- has_all_permissions
- has_permissions
- has_system_permission
- _has_global_access
- _is_platform_administrator
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services.tenant.auth.authorization_service import (
    AuthorizationContext,
    AuthorizationService,
    PLATFORM_ADMIN_ROLE,
    SYSTEM_PERMISSION,
)

from .conftest import permission, role, user


# ---------------------------------------------------------------------------
# get_permissions
# ---------------------------------------------------------------------------


def test_get_permissions_returns_context_permissions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    context = AuthorizationContext(
        user=user(),
        tenant_id="tenant-1",
        roles=frozenset(),
        permissions=frozenset({"products.read", "sales.read"}),
        branch_ids=frozenset(),
    )

    monkeypatch.setattr(
        service,
        "_get_authorization_context",
        lambda *args, **kwargs: context,
    )

    assert service.get_permissions("user-1") == context.permissions


# ---------------------------------------------------------------------------
# permission_count
# ---------------------------------------------------------------------------


def test_permission_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    monkeypatch.setattr(
        service,
        "get_permissions",
        lambda *args, **kwargs: frozenset(
            {"a", "b", "c"},
        ),
    )

    assert service.permission_count("user") == 3


# ---------------------------------------------------------------------------
# get_permission_objects
# ---------------------------------------------------------------------------


def test_get_permission_objects_returns_sorted_unique() -> None:
    service = AuthorizationService()

    p1 = permission("b")
    p2 = permission("a")
    p3 = permission("a")

    r = role(
        permissions=[p1, p2, p3],
    )

    u = user(
        roles=[r],
    )

    service._resolve_user = lambda *a, **k: u

    result = service.get_permission_objects("user")

    assert tuple(p.name for p in result) == (
        "a",
        "b",
    )


# ---------------------------------------------------------------------------
# refresh_context
# ---------------------------------------------------------------------------


def test_refresh_context_rebuilds_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    u = user()

    context = AuthorizationContext(
        user=u,
        tenant_id=u.tenant_id,
        roles=frozenset(),
        permissions=frozenset(),
        branch_ids=frozenset(),
    )

    monkeypatch.setattr(
        service,
        "_resolve_user",
        lambda *args, **kwargs: u,
    )

    monkeypatch.setattr(
        service,
        "_build_authorization_context",
        lambda *_: context,
    )

    stored = {}

    monkeypatch.setattr(
        service,
        "_store_cached_context",
        lambda c: stored.setdefault("context", c),
    )

    result = service.refresh_context("user")

    assert result is context
    assert stored["context"] is context


# ---------------------------------------------------------------------------
# has_permission
# ---------------------------------------------------------------------------


def test_has_permission_true(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    u = user()

    context = AuthorizationContext(
        user=u,
        permissions=frozenset({"inventory.read"}),
    )

    monkeypatch.setattr(
        service,
        "_get_authorization_context",
        lambda *a, **k: context,
    )

    monkeypatch.setattr(
        service,
        "_has_global_authorization_override",
        lambda *_: False,
    )

    assert service.has_permission(
        u,
        "inventory.read",
    )


def test_has_permission_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    context = AuthorizationContext(
        user=user(),
    )

    monkeypatch.setattr(
        service,
        "_get_authorization_context",
        lambda *a, **k: context,
    )

    monkeypatch.setattr(
        service,
        "_has_global_authorization_override",
        lambda *_: True,
    )

    assert service.has_permission(
        "user",
        "anything",
    )


# ---------------------------------------------------------------------------
# has_any_permission
# ---------------------------------------------------------------------------


def test_has_any_permission() -> None:
    service = AuthorizationService()

    context = AuthorizationContext(
        user=user(),
        permissions=frozenset({"a", "b"}),
    )

    service._get_authorization_context = lambda *a, **k: context
    service._has_global_authorization_override = lambda *_: False

    assert service.has_any_permission(
        "user",
        ["x", "b"],
    )


# ---------------------------------------------------------------------------
# has_all_permissions
# ---------------------------------------------------------------------------


def test_has_all_permissions() -> None:
    service = AuthorizationService()

    context = AuthorizationContext(
        user=user(),
        permissions=frozenset({"a", "b", "c"}),
    )

    service._get_authorization_context = lambda *a, **k: context
    service._has_global_authorization_override = lambda *_: False

    assert service.has_all_permissions(
        "user",
        ["a", "b"],
    )


# ---------------------------------------------------------------------------
# has_permissions
# ---------------------------------------------------------------------------


def test_has_permissions_dispatch_all(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    monkeypatch.setattr(
        service,
        "has_all_permissions",
        lambda *a, **k: True,
    )

    assert service.has_permissions(
        "user",
        ["a"],
    )


def test_has_permissions_dispatch_any(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    monkeypatch.setattr(
        service,
        "has_any_permission",
        lambda *a, **k: True,
    )

    assert service.has_permissions(
        "user",
        ["a"],
        require_all=False,
    )


# ---------------------------------------------------------------------------
# has_system_permission
# ---------------------------------------------------------------------------


def test_has_system_permission(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    u = user()

    monkeypatch.setattr(
        service,
        "_resolve_user",
        lambda *a, **k: u,
    )

    monkeypatch.setattr(
        service,
        "get_permissions",
        lambda *a, **k: frozenset(
            {SYSTEM_PERMISSION},
        ),
    )

    assert service.has_system_permission(u)


# ---------------------------------------------------------------------------
# _has_global_access
# ---------------------------------------------------------------------------


def test_has_global_access_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    monkeypatch.setattr(
        service,
        "_has_global_authorization_override",
        lambda *_: True,
    )

    assert service._has_global_access(user())


def test_has_global_access_system_permission(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    u = user()

    monkeypatch.setattr(
        service,
        "_has_global_authorization_override",
        lambda *_: False,
    )

    monkeypatch.setattr(
        service,
        "_is_platform_administrator",
        lambda *_: False,
    )

    monkeypatch.setattr(
        service,
        "_get_cached_context",
        lambda *_: AuthorizationContext(
            user=u,
            permissions=frozenset({SYSTEM_PERMISSION}),
        ),
    )

    assert service._has_global_access(u)


# ---------------------------------------------------------------------------
# _is_platform_administrator
# ---------------------------------------------------------------------------


def test_platform_admin_flag() -> None:
    service = AuthorizationService()

    assert service._is_platform_administrator(
        user(is_platform_admin=True),
    )


def test_platform_admin_role(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    monkeypatch.setattr(
        service,
        "get_roles",
        lambda *_: frozenset(
            {PLATFORM_ADMIN_ROLE},
        ),
    )

    assert service._is_platform_administrator(
        user(),
    )