"""
Tests for authentication authorization decorators.

These tests verify that the decorator layer remains intentionally thin,
delegating every authorization decision to AuthorizationService while
correctly resolving the authenticated identity and authorization scope.
"""

from __future__ import annotations

from typing import Any

import pytest
from werkzeug.exceptions import Unauthorized

from app.auth.jwt import Identity, JWTTokenType
from app.services.tenant.auth import decorators


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def identity() -> Identity:
    """Return a representative authenticated identity."""

    return Identity(
        user_id="user-1",
        tenant_id="tenant-1",
        branch_id="branch-1",
        permissions=("products.read",),
        session_id="session-1",
        token_type=JWTTokenType.ACCESS,
        jti="jwt-1",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _patch_identity(
    monkeypatch: pytest.MonkeyPatch,
    identity: Identity | None,
) -> None:
    monkeypatch.setattr(
        decorators,
        "get_current_identity",
        lambda: identity,
    )


# ---------------------------------------------------------------------------
# _current_identity
# ---------------------------------------------------------------------------


def test_current_identity_returns_identity(
    monkeypatch: pytest.MonkeyPatch,
    identity: Identity,
) -> None:
    _patch_identity(monkeypatch, identity)

    assert decorators._current_identity() is identity


def test_current_identity_aborts_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_identity(monkeypatch, None)

    with pytest.raises(Unauthorized):
        decorators._current_identity()


# ---------------------------------------------------------------------------
# _resolve_scope
# ---------------------------------------------------------------------------


def test_resolve_scope_uses_identity(
    identity: Identity,
) -> None:
    tenant_id, branch_id = decorators._resolve_scope(identity)

    assert tenant_id == "tenant-1"
    assert branch_id == "branch-1"


def test_resolve_scope_overrides_identity(
    identity: Identity,
) -> None:
    tenant_id, branch_id = decorators._resolve_scope(
        identity,
        tenant_id="tenant-9",
        branch_id="branch-9",
    )

    assert tenant_id == "tenant-9"
    assert branch_id == "branch-9"


# ---------------------------------------------------------------------------
# require_authorization
# ---------------------------------------------------------------------------


def test_require_authorization_calls_service(
    monkeypatch: pytest.MonkeyPatch,
    identity: Identity,
) -> None:
    _patch_identity(monkeypatch, identity)

    called: dict[str, Any] = {}

    def fake_authorize(user: str, **kwargs: Any) -> None:
        called["user"] = user
        called.update(kwargs)

    monkeypatch.setattr(
        decorators.authorization_service,
        "authorize",
        fake_authorize,
    )

    @decorators.require_authorization(
        permission="products.read",
    )
    def endpoint() -> str:
        return "ok"

    assert endpoint() == "ok"

    assert called["user"] == "user-1"
    assert called["permission"] == "products.read"
    assert called["tenant_id"] == "tenant-1"
    assert called["branch_id"] == "branch-1"


def test_require_authorization_uses_explicit_scope(
    monkeypatch: pytest.MonkeyPatch,
    identity: Identity,
) -> None:
    _patch_identity(monkeypatch, identity)

    called: dict[str, Any] = {}

    monkeypatch.setattr(
        decorators.authorization_service,
        "authorize",
        lambda user, **kwargs: (
            called.setdefault("user", user),
            called.update(kwargs),
        ),
    )

    @decorators.require_authorization(
        tenant_id="tenant-x",
        branch_id="branch-x",
    )
    def endpoint() -> str:
        return "ok"

    endpoint()

    assert called["tenant_id"] == "tenant-x"
    assert called["branch_id"] == "branch-x"


# ---------------------------------------------------------------------------
# Permission wrappers
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "factory,args,expected",
    [
        (
            decorators.require_permission,
            ("products.read",),
            {"permission": "products.read"},
        ),
        (
            decorators.require_any_permission,
            (["a", "b"],),
            {"any_permissions": ["a", "b"]},
        ),
        (
            decorators.require_all_permissions,
            (["a", "b"],),
            {"all_permissions": ["a", "b"]},
        ),
    ],
)

def test_permission_wrappers_delegate(
    monkeypatch: pytest.MonkeyPatch,
    factory,
    args,
    expected: dict[str, Any],
) -> None:

    captured: dict[str, Any] = {}

    def fake_require_authorization(**kwargs: Any):
        captured.update(kwargs)

        def decorator(view: Any) -> Any:
            return view

        return decorator

    monkeypatch.setattr(
        decorators,
        "require_authorization",
        fake_require_authorization,
    )
    decorator = factory(*args)

    @decorator
    def endpoint() -> None:
        pass

    endpoint()

    for key, value in expected.items():
        assert captured[key] == value


# ---------------------------------------------------------------------------
# Role wrappers
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Role wrappers
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("wrapper", "args", "expected"),
    [
        (
            decorators.require_role,
            ("manager",),
            {"role": "manager"},
        ),
        (
            decorators.require_any_role,
            (("manager", "cashier"),),
            {"any_roles": ("manager", "cashier")},
        ),
        (
            decorators.require_all_roles,
            (("manager", "cashier"),),
            {"all_roles": ("manager", "cashier")},
        ),
    ],
)
def test_role_wrappers_delegate(
    monkeypatch: pytest.MonkeyPatch,
    wrapper,
    args,
    expected: dict[str, Any],
) -> None:
    captured: dict[str, Any] = {}

    def fake_require_authorization(**kwargs: Any):
        captured.update(kwargs)

        def decorator(view: Any) -> Any:
            return view

        return decorator

    monkeypatch.setattr(
        decorators,
        "require_authorization",
        fake_require_authorization,
    )

    decorator = wrapper(*args)

    @decorator
    def endpoint() -> None:
        pass

    endpoint()

    for key, value in expected.items():
        assert captured[key] == value
        
# ---------------------------------------------------------------------------
# Tenant / Branch wrappers
# ---------------------------------------------------------------------------


def test_require_tenant_access_delegates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_require_authorization(**kwargs: Any):
        captured.update(kwargs)

        def decorator(view: Any) -> Any:
            return view

        return decorator

    monkeypatch.setattr(
        decorators,
        "require_authorization",
        fake_require_authorization,
    )

    @decorators.require_tenant_access(
        tenant_id="tenant-2",
    )
    def endpoint() -> None:
        pass

    endpoint()

    assert captured["tenant_id"] == "tenant-2"


def test_require_branch_access_delegates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_require_authorization(**kwargs: Any):
        captured.update(kwargs)

        def decorator(view: Any) -> Any:
            return view

        return decorator

    monkeypatch.setattr(
        decorators,
        "require_authorization",
        fake_require_authorization,
    )

    @decorators.require_branch_access(
        tenant_id="tenant-2",
        branch_id="branch-7",
    )
    def endpoint() -> None:
        pass

    endpoint()

    assert captured["tenant_id"] == "tenant-2"
    assert captured["branch_id"] == "branch-7"