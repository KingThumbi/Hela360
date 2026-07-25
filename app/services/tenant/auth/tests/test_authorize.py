"""
Tests for AuthorizationService.authorize().

Covers the public authorization entry point and verifies orchestration of
tenant, branch, role and permission enforcement.
"""

from __future__ import annotations

import pytest

from app.services.tenant.auth.authorization_service import AuthorizationService

from .conftest import user


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _patch_resolve(service: AuthorizationService, fake_user):
    service._resolve_user = lambda *_args, **_kwargs: fake_user


# ---------------------------------------------------------------------------
# No requirements
# ---------------------------------------------------------------------------


def test_authorize_returns_resolved_user() -> None:
    service = AuthorizationService()

    fake_user = user()

    _patch_resolve(service, fake_user)

    assert service.authorize(fake_user.id) is fake_user


# ---------------------------------------------------------------------------
# Permission
# ---------------------------------------------------------------------------


def test_authorize_requires_permission(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    fake_user = user()

    _patch_resolve(service, fake_user)

    called = {}

    monkeypatch.setattr(
        service,
        "require_permission",
        lambda *args, **kwargs: called.setdefault("permission", True) or fake_user,
    )

    assert service.authorize(
        fake_user.id,
        permission="products.read",
    ) is fake_user

    assert called["permission"] is True


def test_authorize_requires_any_permissions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    fake_user = user()

    _patch_resolve(service, fake_user)

    called = {}

    monkeypatch.setattr(
        service,
        "require_any_permission",
        lambda *args, **kwargs: called.setdefault("any_permissions", True)
        or fake_user,
    )

    assert service.authorize(
        fake_user.id,
        any_permissions=("a", "b"),
    ) is fake_user

    assert called["any_permissions"] is True


def test_authorize_requires_all_permissions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    fake_user = user()

    _patch_resolve(service, fake_user)

    called = {}

    monkeypatch.setattr(
        service,
        "require_all_permissions",
        lambda *args, **kwargs: called.setdefault("all_permissions", True)
        or fake_user,
    )

    assert service.authorize(
        fake_user.id,
        all_permissions=("a", "b"),
    ) is fake_user

    assert called["all_permissions"] is True


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------


def test_authorize_requires_role(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    fake_user = user()

    _patch_resolve(service, fake_user)

    called = {}

    monkeypatch.setattr(
        service,
        "require_role",
        lambda *args, **kwargs: called.setdefault("role", True) or fake_user,
    )

    assert service.authorize(
        fake_user.id,
        role="manager",
    ) is fake_user

    assert called["role"] is True


def test_authorize_requires_any_roles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    fake_user = user()

    _patch_resolve(service, fake_user)

    called = {}

    monkeypatch.setattr(
        service,
        "require_any_role",
        lambda *args, **kwargs: called.setdefault("any_roles", True)
        or fake_user,
    )

    assert service.authorize(
        fake_user.id,
        any_roles=("manager", "cashier"),
    ) is fake_user

    assert called["any_roles"] is True


def test_authorize_requires_all_roles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    fake_user = user()

    _patch_resolve(service, fake_user)

    called = {}

    monkeypatch.setattr(
        service,
        "require_all_roles",
        lambda *args, **kwargs: called.setdefault("all_roles", True)
        or fake_user,
    )

    assert service.authorize(
        fake_user.id,
        all_roles=("manager", "cashier"),
    ) is fake_user

    assert called["all_roles"] is True


# ---------------------------------------------------------------------------
# Tenant / Branch
# ---------------------------------------------------------------------------


def test_authorize_validates_tenant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    fake_user = user()

    _patch_resolve(service, fake_user)

    called = {}

    monkeypatch.setattr(
        service,
        "validate_tenant_access",
        lambda *args, **kwargs: called.setdefault("tenant", True),
    )

    assert service.authorize(
        fake_user.id,
        tenant_id="tenant-1",
    ) is fake_user

    assert called["tenant"] is True


def test_authorize_validates_branch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    fake_user = user()

    _patch_resolve(service, fake_user)

    called = {}

    monkeypatch.setattr(
        service,
        "validate_branch_access",
        lambda *args, **kwargs: called.setdefault("branch", True),
    )

    assert service.authorize(
        fake_user.id,
        branch_id="branch-1",
    ) is fake_user

    assert called["branch"] is True


# ---------------------------------------------------------------------------
# Combined authorization
# ---------------------------------------------------------------------------


def test_authorize_combined_requirements(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    fake_user = user()

    _patch_resolve(service, fake_user)

    calls: list[str] = []

    monkeypatch.setattr(
        service,
        "validate_tenant_access",
        lambda *a, **k: calls.append("tenant"),
    )

    monkeypatch.setattr(
        service,
        "validate_branch_access",
        lambda *a, **k: calls.append("branch"),
    )

    monkeypatch.setattr(
        service,
        "require_role",
        lambda *a, **k: calls.append("role") or fake_user,
    )

    monkeypatch.setattr(
        service,
        "require_permission",
        lambda *a, **k: calls.append("permission") or fake_user,
    )

    assert service.authorize(
        fake_user.id,
        tenant_id="tenant-1",
        branch_id="branch-1",
        role="manager",
        permission="products.read",
    ) is fake_user

    assert calls == [
        "tenant",
        "branch",
        "role",
        "permission",
    ]