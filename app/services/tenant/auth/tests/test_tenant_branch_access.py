"""
Tests for tenant and branch authorization.

Covers:

- _aggregate_branch_ids
- _has_branch_access
- can_access_tenant
- can_access_branch
- validate_tenant_access
- validate_branch_access
"""

from __future__ import annotations

import pytest

from app.auth.exceptions import (
    BranchAccessDeniedError,
    TenantAccessDeniedError,
)
from app.services.tenant.auth.authorization_service import (
    AuthorizationService,
)

from .conftest import user


# ---------------------------------------------------------------------------
# _aggregate_branch_ids
# ---------------------------------------------------------------------------


def test_aggregate_branch_ids_returns_empty_set() -> None:
    """
    The current implementation is an extension point and grants
    tenant-wide branch access by default.
    """
    service = AuthorizationService()

    assert service._aggregate_branch_ids(user()) == frozenset()


# ---------------------------------------------------------------------------
# _has_branch_access
# ---------------------------------------------------------------------------


def test_has_branch_access_defaults_to_tenant_wide_access() -> None:
    """
    With no explicit branch assignments every branch is accessible.
    """
    service = AuthorizationService()

    assert service._has_branch_access(user(), "main") is True


def test_has_branch_access_honors_branch_assignments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    fake_user = user()

    monkeypatch.setattr(
        service,
        "_aggregate_branch_ids",
        lambda *_args, **_kwargs: frozenset({"main", "west"}),
    )

    assert service._has_branch_access(fake_user, "main") is True
    assert service._has_branch_access(fake_user, "west") is True
    assert service._has_branch_access(fake_user, "east") is False


# ---------------------------------------------------------------------------
# can_access_tenant
# ---------------------------------------------------------------------------


def test_can_access_tenant_true(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    monkeypatch.setattr(
        service,
        "_resolve_user",
        lambda *_args, **_kwargs: user(tenant_id="tenant-1"),
    )

    monkeypatch.setattr(
        service,
        "_is_platform_administrator",
        lambda *_args, **_kwargs: False,
    )

    monkeypatch.setattr(
        service,
        "_is_owner",
        lambda *_args, **_kwargs: False,
    )

    assert service.can_access_tenant("user", "tenant-1") is True


def test_can_access_tenant_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    monkeypatch.setattr(
        service,
        "_resolve_user",
        lambda *_args, **_kwargs: user(tenant_id="tenant-2"),
    )

    monkeypatch.setattr(
        service,
        "_is_platform_administrator",
        lambda *_args, **_kwargs: False,
    )

    monkeypatch.setattr(
        service,
        "_is_owner",
        lambda *_args, **_kwargs: False,
    )

    assert service.can_access_tenant("user", "tenant-1") is False


def test_can_access_tenant_owner_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    fake_user = user()

    monkeypatch.setattr(
        service,
        "_resolve_user",
        lambda *_args, **_kwargs: fake_user,
    )

    monkeypatch.setattr(
        service,
        "_is_platform_administrator",
        lambda *_args, **_kwargs: False,
    )

    monkeypatch.setattr(
        service,
        "_is_owner",
        lambda *_args, **_kwargs: True,
    )

    assert service.can_access_tenant("user", "another-tenant") is True


# ---------------------------------------------------------------------------
# can_access_branch
# ---------------------------------------------------------------------------


def test_can_access_branch_true(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    fake_user = user()

    monkeypatch.setattr(
        service,
        "_resolve_user",
        lambda *_args, **_kwargs: fake_user,
    )

    monkeypatch.setattr(
        service,
        "_has_global_access",
        lambda *_args, **_kwargs: False,
    )

    monkeypatch.setattr(
        service,
        "_has_branch_access",
        lambda *_args, **_kwargs: True,
    )

    assert service.can_access_branch("user", "main") is True


def test_can_access_branch_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    fake_user = user()

    monkeypatch.setattr(
        service,
        "_resolve_user",
        lambda *_args, **_kwargs: fake_user,
    )

    monkeypatch.setattr(
        service,
        "_has_global_access",
        lambda *_args, **_kwargs: False,
    )

    monkeypatch.setattr(
        service,
        "_has_branch_access",
        lambda *_args, **_kwargs: False,
    )

    assert service.can_access_branch("user", "main") is False


def test_can_access_branch_global_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    fake_user = user()

    monkeypatch.setattr(
        service,
        "_resolve_user",
        lambda *_args, **_kwargs: fake_user,
    )

    monkeypatch.setattr(
        service,
        "_has_global_access",
        lambda *_args, **_kwargs: True,
    )

    assert service.can_access_branch("user", "main") is True


# ---------------------------------------------------------------------------
# validate_tenant_access
# ---------------------------------------------------------------------------


def test_validate_tenant_access_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    monkeypatch.setattr(
        service,
        "can_access_tenant",
        lambda *_args, **_kwargs: True,
    )

    service.validate_tenant_access("user", "tenant-1")


def test_validate_tenant_access_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    monkeypatch.setattr(
        service,
        "can_access_tenant",
        lambda *_args, **_kwargs: False,
    )

    monkeypatch.setattr(
        service,
        "_audit_authorization_denied",
        lambda *args, **kwargs: None,
    )

    with pytest.raises(TenantAccessDeniedError):
        service.validate_tenant_access("user", "tenant-1")


# ---------------------------------------------------------------------------
# validate_branch_access
# ---------------------------------------------------------------------------


def test_validate_branch_access_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    monkeypatch.setattr(
        service,
        "can_access_branch",
        lambda *_args, **_kwargs: True,
    )

    service.validate_branch_access("user", "main")


def test_validate_branch_access_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    monkeypatch.setattr(
        service,
        "can_access_branch",
        lambda *_args, **_kwargs: False,
    )

    monkeypatch.setattr(
        service,
        "_audit_authorization_denied",
        lambda *args, **kwargs: None,
    )

    with pytest.raises(BranchAccessDeniedError):
        service.validate_branch_access("user", "main")