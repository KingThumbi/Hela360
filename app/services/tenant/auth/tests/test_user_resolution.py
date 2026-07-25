"""
Tests for AuthorizationService user resolution.

Covers:

- __init__
- get_user_or_raise
- user_exists
- _validate_user_status
- _resolve_user
"""

from __future__ import annotations

import pytest

from app.auth.exceptions import (
    AccountArchivedError,
    AccountDisabledError,
    AccountInactiveError,
    AccountLockedError,
    AccountSuspendedError,
    UserNotFoundError,
)
from app.services.tenant.auth.authorization_service import AuthorizationService

from .conftest import user


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


def test_service_initializes_empty_cache() -> None:
    service = AuthorizationService()

    assert service._authorization_context_cache == {}


# ---------------------------------------------------------------------------
# get_user_or_raise
# ---------------------------------------------------------------------------


def test_get_user_or_raise_returns_user(monkeypatch: pytest.MonkeyPatch) -> None:
    service = AuthorizationService()
    fake_user = user()

    monkeypatch.setattr(
        service,
        "get_user",
        lambda **kwargs: fake_user,
    )

    result = service.get_user_or_raise("user-1")

    assert result is fake_user


def test_get_user_or_raise_raises_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    monkeypatch.setattr(
        service,
        "get_user",
        lambda **kwargs: None,
    )

    with pytest.raises(UserNotFoundError):
        service.get_user_or_raise("missing")


# ---------------------------------------------------------------------------
# user_exists
# ---------------------------------------------------------------------------


def test_user_exists_true(monkeypatch: pytest.MonkeyPatch) -> None:
    service = AuthorizationService()

    monkeypatch.setattr(
        service,
        "get_user",
        lambda **kwargs: user(),
    )

    assert service.user_exists("user-1") is True


def test_user_exists_false(monkeypatch: pytest.MonkeyPatch) -> None:
    service = AuthorizationService()

    monkeypatch.setattr(
        service,
        "get_user",
        lambda **kwargs: None,
    )

    assert service.user_exists("missing") is False


# ---------------------------------------------------------------------------
# _validate_user_status
# ---------------------------------------------------------------------------


def test_validate_user_status_accepts_active_user() -> None:
    service = AuthorizationService()

    service._validate_user_status(user())


@pytest.mark.parametrize(
    ("kwargs", "exception"),
    [
        ({"is_active": False}, AccountInactiveError),
        ({"is_disabled": True}, AccountDisabledError),
        ({"is_locked": True}, AccountLockedError),
        ({"status": "inactive"}, AccountInactiveError),
        ({"status": "disabled"}, AccountDisabledError),
        ({"status": "locked"}, AccountLockedError),
        ({"status": "suspended"}, AccountSuspendedError),
        ({"status": "archived"}, AccountArchivedError),
    ],
)
def test_validate_user_status_rejects_invalid_accounts(
    kwargs: dict,
    exception: type[Exception],
) -> None:
    service = AuthorizationService()

    with pytest.raises(exception):
        service._validate_user_status(user(**kwargs))


# ---------------------------------------------------------------------------
# _resolve_user
# ---------------------------------------------------------------------------


def test_resolve_user_resolves_identifier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    fake_user = user()

    monkeypatch.setattr(
        service,
        "get_user_or_raise",
        lambda **kwargs: fake_user,
    )

    result = service._resolve_user("user-1")

    assert result is fake_user


def test_resolve_user_passes_tenant_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    fake_user = user()

    captured: dict[str, object] = {}

    def fake_get_user_or_raise(**kwargs):
        captured.update(kwargs)
        return fake_user

    monkeypatch.setattr(
        service,
        "get_user_or_raise",
        fake_get_user_or_raise,
    )

    service._resolve_user(
        "user-1",
        tenant_id="tenant-42",
    )

    assert captured == {
        "user_id": "user-1",
        "tenant_id": "tenant-42",
    }


def test_resolve_user_validates_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    fake_user = user()

    monkeypatch.setattr(
        service,
        "get_user_or_raise",
        lambda **kwargs: fake_user,
    )

    called = False

    def validate(resolved):
        nonlocal called
        called = True
        assert resolved is fake_user

    monkeypatch.setattr(
        service,
        "_validate_user_status",
        validate,
    )

    result = service._resolve_user("user-1")

    assert result is fake_user
    assert called is True


def test_resolve_user_propagates_user_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    def raise_error(**kwargs):
        raise UserNotFoundError("missing")

    monkeypatch.setattr(
        service,
        "get_user_or_raise",
        raise_error,
    )

    with pytest.raises(UserNotFoundError):
        service._resolve_user("missing")