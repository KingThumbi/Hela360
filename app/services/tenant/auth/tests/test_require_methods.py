"""
Tests for AuthorizationService enforcement helpers.

Covers:

- require_permission
- require_any_permission
- require_all_permissions
- require_role
- require_any_role
- require_all_roles
- authorize
"""

from __future__ import annotations

import pytest

from app.auth.exceptions import (
    PermissionDeniedError,
    RoleRequiredError,
)
from app.services.tenant.auth.authorization_service import (
    AuthorizationService,
)

from .conftest import user


# ---------------------------------------------------------------------------
# require_permission
# ---------------------------------------------------------------------------


def test_require_permission_returns_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    resolved = user()

    monkeypatch.setattr(
        service,
        "_resolve_user",
        lambda *_a, **_k: resolved,
    )

    monkeypatch.setattr(
        service,
        "has_permission",
        lambda *_a, **_k: True,
    )

    assert (
        service.require_permission(
            "user",
            "products.read",
        )
        is resolved
    )


def test_require_permission_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    resolved = user()

    monkeypatch.setattr(
        service,
        "_resolve_user",
        lambda *_a, **_k: resolved,
    )

    monkeypatch.setattr(
        service,
        "has_permission",
        lambda *_a, **_k: False,
    )

    monkeypatch.setattr(
        service,
        "_audit_authorization_denied",
        lambda *_a, **_k: None,
    )

    with pytest.raises(PermissionDeniedError):
        service.require_permission(
            "user",
            "products.read",
        )


# ---------------------------------------------------------------------------
# require_any_permission
# ---------------------------------------------------------------------------


def test_require_any_permission_returns_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    resolved = user()

    monkeypatch.setattr(
        service,
        "_resolve_user",
        lambda *_a, **_k: resolved,
    )

    monkeypatch.setattr(
        service,
        "has_any_permission",
        lambda *_a, **_k: True,
    )

    assert (
        service.require_any_permission(
            "user",
            ["a", "b"],
        )
        is resolved
    )


def test_require_any_permission_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    resolved = user()

    monkeypatch.setattr(
        service,
        "_resolve_user",
        lambda *_a, **_k: resolved,
    )

    monkeypatch.setattr(
        service,
        "has_any_permission",
        lambda *_a, **_k: False,
    )

    monkeypatch.setattr(
        service,
        "_audit_authorization_denied",
        lambda *_a, **_k: None,
    )

    with pytest.raises(PermissionDeniedError):
        service.require_any_permission(
            "user",
            ["a", "b"],
        )


# ---------------------------------------------------------------------------
# require_all_permissions
# ---------------------------------------------------------------------------


def test_require_all_permissions_returns_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    resolved = user()

    monkeypatch.setattr(
        service,
        "_resolve_user",
        lambda *_a, **_k: resolved,
    )

    monkeypatch.setattr(
        service,
        "has_all_permissions",
        lambda *_a, **_k: True,
    )

    assert (
        service.require_all_permissions(
            "user",
            ["a", "b"],
        )
        is resolved
    )


def test_require_all_permissions_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    resolved = user()

    monkeypatch.setattr(
        service,
        "_resolve_user",
        lambda *_a, **_k: resolved,
    )

    monkeypatch.setattr(
        service,
        "has_all_permissions",
        lambda *_a, **_k: False,
    )

    monkeypatch.setattr(
        service,
        "_audit_authorization_denied",
        lambda *_a, **_k: None,
    )

    with pytest.raises(PermissionDeniedError):
        service.require_all_permissions(
            "user",
            ["a", "b"],
        )


# ---------------------------------------------------------------------------
# require_role
# ---------------------------------------------------------------------------


def test_require_role_returns_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    resolved = user()

    monkeypatch.setattr(
        service,
        "_resolve_user",
        lambda *_a, **_k: resolved,
    )

    monkeypatch.setattr(
        service,
        "has_role",
        lambda *_a, **_k: True,
    )

    assert (
        service.require_role(
            "user",
            "manager",
        )
        is resolved
    )


def test_require_role_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    resolved = user()

    monkeypatch.setattr(
        service,
        "_resolve_user",
        lambda *_a, **_k: resolved,
    )

    monkeypatch.setattr(
        service,
        "has_role",
        lambda *_a, **_k: False,
    )

    monkeypatch.setattr(
        service,
        "_audit_authorization_denied",
        lambda *_a, **_k: None,
    )

    with pytest.raises(RoleRequiredError):
        service.require_role(
            "user",
            "manager",
        )


# ---------------------------------------------------------------------------
# require_any_role
# ---------------------------------------------------------------------------


def test_require_any_role_returns_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    resolved = user()

    monkeypatch.setattr(
        service,
        "_resolve_user",
        lambda *_a, **_k: resolved,
    )

    monkeypatch.setattr(
        service,
        "has_any_role",
        lambda *_a, **_k: True,
    )

    assert (
        service.require_any_role(
            "user",
            ["manager", "cashier"],
        )
        is resolved
    )


def test_require_any_role_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    resolved = user()

    monkeypatch.setattr(
        service,
        "_resolve_user",
        lambda *_a, **_k: resolved,
    )

    monkeypatch.setattr(
        service,
        "has_any_role",
        lambda *_a, **_k: False,
    )

    monkeypatch.setattr(
        service,
        "_audit_authorization_denied",
        lambda *_a, **_k: None,
    )

    with pytest.raises(RoleRequiredError):
        service.require_any_role(
            "user",
            ["manager", "cashier"],
        )


# ---------------------------------------------------------------------------
# require_all_roles
# ---------------------------------------------------------------------------


def test_require_all_roles_returns_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    resolved = user()

    monkeypatch.setattr(
        service,
        "_resolve_user",
        lambda *_a, **_k: resolved,
    )

    monkeypatch.setattr(
        service,
        "has_all_roles",
        lambda *_a, **_k: True,
    )

    assert (
        service.require_all_roles(
            "user",
            ["manager", "cashier"],
        )
        is resolved
    )


def test_require_all_roles_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    resolved = user()

    monkeypatch.setattr(
        service,
        "_resolve_user",
        lambda *_a, **_k: resolved,
    )

    monkeypatch.setattr(
        service,
        "has_all_roles",
        lambda *_a, **_k: False,
    )

    monkeypatch.setattr(
        service,
        "_audit_authorization_denied",
        lambda *_a, **_k: None,
    )

    with pytest.raises(RoleRequiredError):
        service.require_all_roles(
            "user",
            ["manager", "cashier"],
        )


# ---------------------------------------------------------------------------
# authorize
# ---------------------------------------------------------------------------


def test_authorize_returns_resolved_user_without_requirements(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    resolved = user()

    monkeypatch.setattr(
        service,
        "_resolve_user",
        lambda *_a, **_k: resolved,
    )

    assert service.authorize("user") is resolved


def test_authorize_validates_tenant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    resolved = user()

    called = False

    monkeypatch.setattr(
        service,
        "_resolve_user",
        lambda *_a, **_k: resolved,
    )

    def validate(*_a, **_k):
        nonlocal called
        called = True

    monkeypatch.setattr(
        service,
        "validate_tenant_access",
        validate,
    )

    service.authorize(
        "user",
        tenant_id="tenant-1",
    )

    assert called


def test_authorize_validates_branch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    resolved = user()

    called = False

    monkeypatch.setattr(
        service,
        "_resolve_user",
        lambda *_a, **_k: resolved,
    )

    def validate(*_a, **_k):
        nonlocal called
        called = True

    monkeypatch.setattr(
        service,
        "validate_branch_access",
        validate,
    )

    service.authorize(
        "user",
        branch_id="main",
    )

    assert called


@pytest.mark.parametrize(
    ("kwargs", "method"),
    [
        ({"role": "manager"}, "require_role"),
        ({"any_roles": ["manager"]}, "require_any_role"),
        ({"all_roles": ["manager"]}, "require_all_roles"),
        ({"permission": "products.read"}, "require_permission"),
        (
            {"any_permissions": ["products.read"]},
            "require_any_permission",
        ),
        (
            {"all_permissions": ["products.read"]},
            "require_all_permissions",
        ),
    ],
)
def test_authorize_dispatches_to_requirement_helpers(
    monkeypatch: pytest.MonkeyPatch,
    kwargs: dict,
    method: str,
) -> None:
    service = AuthorizationService()

    resolved = user()

    monkeypatch.setattr(
        service,
        "_resolve_user",
        lambda *_a, **_k: resolved,
    )

    called = False

    def helper(*_a, **_k):
        nonlocal called
        called = True
        return resolved

    monkeypatch.setattr(
        service,
        method,
        helper,
    )

    assert service.authorize("user", **kwargs) is resolved
    assert called