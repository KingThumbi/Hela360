"""
Tests for authorization audit logging.

Covers:

- Generic authorization audit
- Tenant audit
- Branch audit
- Permission reason formatting
- Role reason formatting
- Combined permission/role formatting
- Audit failures are swallowed
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services.tenant.auth.authorization_service import (
    AuthorizationService,
)

from .conftest import user


# ---------------------------------------------------------------------------
# Generic authorization audit
# ---------------------------------------------------------------------------


def test_audit_authorization_denied_generic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    fake_user = user()

    monkeypatch.setattr(
        service,
        "get_user",
        lambda *_args, **_kwargs: fake_user,
    )

    captured: dict = {}

    service.audit_service = SimpleNamespace(
        authorization_denied=lambda **kwargs: captured.update(kwargs),
        tenant_access_denied=lambda **kwargs: None,
        branch_access_denied=lambda **kwargs: None,
    )

    service._audit_authorization_denied(
        fake_user.id,
        resource="permission",
    )

    assert captured["tenant_id"] == fake_user.tenant_id
    assert captured["user_id"] == fake_user.id
    assert captured["entity_type"] == "Permission"
    assert captured["reason"] is None


# ---------------------------------------------------------------------------
# Tenant audit
# ---------------------------------------------------------------------------


def test_audit_tenant_access_denied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    fake_user = user()

    monkeypatch.setattr(
        service,
        "get_user",
        lambda *_args, **_kwargs: fake_user,
    )

    captured: dict = {}

    service.audit_service = SimpleNamespace(
        authorization_denied=lambda **kwargs: None,
        tenant_access_denied=lambda **kwargs: captured.update(kwargs),
        branch_access_denied=lambda **kwargs: None,
    )

    service._audit_authorization_denied(
        fake_user.id,
        resource="tenant",
        resource_id="tenant-2",
    )

    assert captured["entity_type"] == "Tenant"
    assert captured["entity_id"] == "tenant-2"


# ---------------------------------------------------------------------------
# Branch audit
# ---------------------------------------------------------------------------


def test_audit_branch_access_denied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    fake_user = user()

    monkeypatch.setattr(
        service,
        "get_user",
        lambda *_args, **_kwargs: fake_user,
    )

    captured: dict = {}

    service.audit_service = SimpleNamespace(
        authorization_denied=lambda **kwargs: None,
        tenant_access_denied=lambda **kwargs: None,
        branch_access_denied=lambda **kwargs: captured.update(kwargs),
    )

    service._audit_authorization_denied(
        fake_user.id,
        resource="branch",
        resource_id="branch-7",
    )

    assert captured["entity_type"] == "Branch"
    assert captured["entity_id"] == "branch-7"


# ---------------------------------------------------------------------------
# Reason generation
# ---------------------------------------------------------------------------


def test_permission_reason(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    fake_user = user()

    monkeypatch.setattr(
        service,
        "get_user",
        lambda *_args, **_kwargs: fake_user,
    )

    captured: dict = {}

    service.audit_service = SimpleNamespace(
        authorization_denied=lambda **kwargs: captured.update(kwargs),
        tenant_access_denied=lambda **kwargs: None,
        branch_access_denied=lambda **kwargs: None,
    )

    service._audit_authorization_denied(
        fake_user.id,
        resource="permission",
        permission="products.read",
    )

    assert captured["reason"] == "Missing permission: products.read"


def test_role_reason(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    fake_user = user()

    monkeypatch.setattr(
        service,
        "get_user",
        lambda *_args, **_kwargs: fake_user,
    )

    captured: dict = {}

    service.audit_service = SimpleNamespace(
        authorization_denied=lambda **kwargs: captured.update(kwargs),
        tenant_access_denied=lambda **kwargs: None,
        branch_access_denied=lambda **kwargs: None,
    )

    service._audit_authorization_denied(
        fake_user.id,
        resource="role",
        role="manager",
    )

    assert captured["reason"] == "Missing role: manager"


def test_permission_and_role_reason(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    fake_user = user()

    monkeypatch.setattr(
        service,
        "get_user",
        lambda *_args, **_kwargs: fake_user,
    )

    captured: dict = {}

    service.audit_service = SimpleNamespace(
        authorization_denied=lambda **kwargs: captured.update(kwargs),
        tenant_access_denied=lambda **kwargs: None,
        branch_access_denied=lambda **kwargs: None,
    )

    service._audit_authorization_denied(
        fake_user.id,
        resource="authorization",
        permission="products.read",
        role="manager",
    )

    assert (
        captured["reason"]
        == "Missing permission: products.read; Missing role: manager"
    )


# ---------------------------------------------------------------------------
# Fail-safe auditing
# ---------------------------------------------------------------------------


def test_audit_failure_is_swallowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuthorizationService()

    fake_user = user()

    monkeypatch.setattr(
        service,
        "get_user",
        lambda *_args, **_kwargs: fake_user,
    )

    class DummyLogger:
        def __init__(self) -> None:
            self.called = False

        def exception(self, *_args, **_kwargs) -> None:
            self.called = True

    logger = DummyLogger()

    monkeypatch.setattr(
        "app.services.tenant.auth.authorization_service.current_app",
        SimpleNamespace(logger=logger),
    )
    
    service.audit_service = SimpleNamespace(
        authorization_denied=lambda **kwargs: (_ for _ in ()).throw(
            RuntimeError("boom")
        ),
        tenant_access_denied=lambda **kwargs: None,
        branch_access_denied=lambda **kwargs: None,
    )

    service._audit_authorization_denied(
        fake_user.id,
        resource="permission",
    )

    assert logger.called is True