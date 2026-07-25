"""
Tests for AuthorizationService role APIs.

Covers:

- get_roles
- has_role
- has_any_role
- has_all_roles
"""

from __future__ import annotations

import pytest

from app.services.tenant.auth.authorization_service import (
    AuthorizationContext,
    AuthorizationService,
)

from .conftest import user


# ---------------------------------------------------------------------------
# get_roles
# ---------------------------------------------------------------------------


def test_get_roles_returns_context_roles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    context = AuthorizationContext(
        user=user(),
        roles=frozenset({"admin", "manager"}),
    )

    monkeypatch.setattr(
        service,
        "_get_authorization_context",
        lambda *args, **kwargs: context,
    )

    assert service.get_roles("user-1") == frozenset(
        {"admin", "manager"},
    )


# ---------------------------------------------------------------------------
# has_role
# ---------------------------------------------------------------------------


def test_has_role_true(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    context = AuthorizationContext(
        user=user(),
        roles=frozenset({"admin"}),
    )

    monkeypatch.setattr(
        service,
        "_get_authorization_context",
        lambda *args, **kwargs: context,
    )

    monkeypatch.setattr(
        service,
        "_has_global_authorization_override",
        lambda *_: False,
    )

    assert service.has_role("user-1", "admin") is True


def test_has_role_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    context = AuthorizationContext(
        user=user(),
        roles=frozenset({"manager"}),
    )

    monkeypatch.setattr(
        service,
        "_get_authorization_context",
        lambda *args, **kwargs: context,
    )

    monkeypatch.setattr(
        service,
        "_has_global_authorization_override",
        lambda *_: False,
    )

    assert service.has_role("user-1", "admin") is False


def test_has_role_global_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    context = AuthorizationContext(user=user())

    monkeypatch.setattr(
        service,
        "_get_authorization_context",
        lambda *args, **kwargs: context,
    )

    monkeypatch.setattr(
        service,
        "_has_global_authorization_override",
        lambda *_: True,
    )

    assert service.has_role("user-1", "anything") is True


# ---------------------------------------------------------------------------
# has_any_role
# ---------------------------------------------------------------------------


def test_has_any_role_true(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    context = AuthorizationContext(
        user=user(),
        roles=frozenset({"manager", "cashier"}),
    )

    monkeypatch.setattr(
        service,
        "_get_authorization_context",
        lambda *args, **kwargs: context,
    )

    monkeypatch.setattr(
        service,
        "_has_global_authorization_override",
        lambda *_: False,
    )

    assert service.has_any_role(
        "user-1",
        ["admin", "manager"],
    )


def test_has_any_role_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    context = AuthorizationContext(
        user=user(),
        roles=frozenset({"cashier"}),
    )

    monkeypatch.setattr(
        service,
        "_get_authorization_context",
        lambda *args, **kwargs: context,
    )

    monkeypatch.setattr(
        service,
        "_has_global_authorization_override",
        lambda *_: False,
    )

    assert not service.has_any_role(
        "user-1",
        ["admin", "manager"],
    )


def test_has_any_role_global_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    context = AuthorizationContext(user=user())

    monkeypatch.setattr(
        service,
        "_get_authorization_context",
        lambda *args, **kwargs: context,
    )

    monkeypatch.setattr(
        service,
        "_has_global_authorization_override",
        lambda *_: True,
    )

    assert service.has_any_role(
        "user-1",
        ["anything"],
    )


# ---------------------------------------------------------------------------
# has_all_roles
# ---------------------------------------------------------------------------


def test_has_all_roles_true(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    context = AuthorizationContext(
        user=user(),
        roles=frozenset({"admin", "manager", "cashier"}),
    )

    monkeypatch.setattr(
        service,
        "_get_authorization_context",
        lambda *args, **kwargs: context,
    )

    monkeypatch.setattr(
        service,
        "_has_global_authorization_override",
        lambda *_: False,
    )

    assert service.has_all_roles(
        "user-1",
        ["admin", "manager"],
    )


def test_has_all_roles_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    context = AuthorizationContext(
        user=user(),
        roles=frozenset({"manager"}),
    )

    monkeypatch.setattr(
        service,
        "_get_authorization_context",
        lambda *args, **kwargs: context,
    )

    monkeypatch.setattr(
        service,
        "_has_global_authorization_override",
        lambda *_: False,
    )

    assert not service.has_all_roles(
        "user-1",
        ["admin", "manager"],
    )


def test_has_all_roles_global_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    context = AuthorizationContext(user=user())

    monkeypatch.setattr(
        service,
        "_get_authorization_context",
        lambda *args, **kwargs: context,
    )

    monkeypatch.setattr(
        service,
        "_has_global_authorization_override",
        lambda *_: True,
    )

    assert service.has_all_roles(
        "user-1",
        ["admin", "manager"],
    )