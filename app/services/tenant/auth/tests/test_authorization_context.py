"""
Tests for AuthorizationService authorization context.

Covers:

- _aggregate_roles
- _aggregate_permissions
- _build_authorization_context
- _get_authorization_context
- refresh_context
"""

from __future__ import annotations

import pytest

from app.services.tenant.auth.authorization_service import (
    AuthorizationContext,
    AuthorizationService,
)

from .conftest import (
    permission,
    role,
    user,
)
# ---------------------------------------------------------------------------
# _aggregate_roles
# ---------------------------------------------------------------------------


def test_aggregate_roles_returns_role_names() -> None:
    service = AuthorizationService()

    u = user(
        roles=[
            role(name="admin"),
            role(name="manager"),
        ],
    )

    assert service._aggregate_roles(u) == {
        "admin",
        "manager",
    }


def test_aggregate_roles_empty_user() -> None:
    service = AuthorizationService()

    assert service._aggregate_roles(user()) == set()

# ---------------------------------------------------------------------------
# _aggregate_permissions
# ---------------------------------------------------------------------------


def test_aggregate_permissions_returns_permission_codes() -> None:
    service = AuthorizationService()

    admin = role(
        permissions=[
            permission("products.read"),
            permission("products.write"),
        ],
    )

    manager = role(
        permissions=[
            permission("reports.read"),
        ],
    )

    u = user(
        roles=[admin, manager],
    )

    assert service._aggregate_permissions(u) == {
        "products.read",
        "products.write",
        "reports.read",
    }


def test_aggregate_permissions_deduplicates() -> None:
    service = AuthorizationService()

    admin = role(
        permissions=[
            permission("products.read"),
        ],
    )

    manager = role(
        permissions=[
            permission("products.read"),
        ],
    )

    u = user(
        roles=[admin, manager],
    )

    assert service._aggregate_permissions(u) == {
        "products.read",
    } 

# ---------------------------------------------------------------------------
# _build_authorization_context
# ---------------------------------------------------------------------------


def test_build_authorization_context() -> None:
    service = AuthorizationService()

    u = user(
        tenant_id="tenant-1",
    )

    context = service._build_authorization_context(u)

    assert isinstance(context, AuthorizationContext)

    assert context.user_id == u.id
    assert context.tenant_id == "tenant-1"
    assert context.is_owner is False
    assert context.is_platform_admin is False
    assert context.roles == frozenset()
    assert context.permissions == frozenset()
    assert context.branch_ids == frozenset()       

def test_cached_authorization_context_is_orm_independent() -> None:
    service = AuthorizationService()

    u = user(
        tenant_id="tenant-1",
        roles=[
            role(
                name="cashier",
                permissions=[
                    permission("sales.create"),
                ],
            ),
        ],
    )

    context = service._build_authorization_context(u)

    # The cached snapshot must contain only scalar/immutable authorization
    # state and must not retain the originating ORM/user object.
    assert context.user_id == u.id
    assert context.tenant_id == u.tenant_id
    assert context.roles == frozenset({"cashier"})
    assert context.permissions == frozenset({
        "sales.create",
    })

    service._store_cached_context(context)

    cached = service._authorization_context_cache[
        service._authorization_cache_key(
            tenant_id=context.tenant_id,
            user_id=context.user_id,
        )
    ]

    assert cached is context
    assert cached.has_global_override is False
    assert "sales.create" in cached.permissions

    # Architectural regression guard: AuthorizationContext must never
    # regain a SQLAlchemy/User reference.
    assert not hasattr(cached, "user")

def test_get_authorization_context_builds_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    fake_user = user()

    expected = AuthorizationContext(
        user_id=fake_user.id,
        tenant_id=fake_user.tenant_id,
    )

    monkeypatch.setattr(
        service,
        "_resolve_user",
        lambda *args, **kwargs: fake_user,
    )

    monkeypatch.setattr(
        service,
        "_get_cached_context",
        lambda *_: None,
    )

    monkeypatch.setattr(
        service,
        "_build_authorization_context",
        lambda *_: expected,
    )

    stored = []

    monkeypatch.setattr(
        service,
        "_store_cached_context",
        lambda context: stored.append(context),
    )

    result = service._get_authorization_context("user-1")

    assert result is expected
    assert stored == [expected]    

def test_get_authorization_context_uses_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    fake_user = user()

    cached = AuthorizationContext(
        user_id=fake_user.id,
        tenant_id=fake_user.tenant_id,
    )

    monkeypatch.setattr(
        service,
        "_resolve_user",
        lambda *args, **kwargs: fake_user,
    )

    monkeypatch.setattr(
        service,
        "_get_cached_context",
        lambda *_: cached,
    )

    build_called = False

    def build(_):
        nonlocal build_called
        build_called = True
        return cached

    monkeypatch.setattr(
        service,
        "_build_authorization_context",
        build,
    )

    result = service._get_authorization_context("user-1")

    assert result is cached
    assert build_called is False    

# ---------------------------------------------------------------------------
# refresh_context
# ---------------------------------------------------------------------------


def test_refresh_context_rebuilds_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    fake_user = user()

    context = AuthorizationContext(
        user_id=fake_user.id,
        tenant_id=fake_user.tenant_id,
    )

    monkeypatch.setattr(
        service,
        "_resolve_user",
        lambda *args, **kwargs: fake_user,
    )

    monkeypatch.setattr(
        service,
        "_build_authorization_context",
        lambda *_: context,
    )

    stored = []

    monkeypatch.setattr(
        service,
        "_store_cached_context",
        lambda c: stored.append(c),
    )

    result = service.refresh_context("user-1")

    assert result is context
    assert stored == [context]    