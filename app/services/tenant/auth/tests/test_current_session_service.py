"""
Tests for CurrentSessionService.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace

import pytest

from app.auth.exceptions import (
    AccountInactiveError,
    AccountLockedError,
    AuthenticationError,
    BranchAccessDeniedError,
    InvalidAccessTokenError,
    SessionNotFoundError,
    TenantAccessDeniedError,
)
from app.auth.jwt import Identity, JWTTokenType
from app.services.tenant.auth.authorization_service import AuthorizationContext
from app.services.tenant.auth.current_session_service import CurrentSessionService


@dataclass(slots=True)
class FakeRole:
    id: str
    name: str
    code: str


@dataclass(slots=True)
class FakeUser:
    id: str = "user-1"
    tenant_id: str = "tenant-1"
    email: str = "user@example.test"
    username: str = "user"
    first_name: str = "Ada"
    last_name: str = "Lovelace"
    is_active: bool = True
    is_locked: bool = False
    is_owner: bool = False
    is_platform_admin: bool = False
    roles: list[FakeRole] = field(default_factory=list)


def identity(
    *,
    token_type: JWTTokenType = JWTTokenType.ACCESS,
    tenant_id: str = "tenant-1",
    branch_id: str | None = "branch-1",
    session_id: str = "session-1",
    user_id: str = "user-1",
) -> Identity:
    return Identity(
        user_id=user_id,
        tenant_id=tenant_id,
        branch_id=branch_id,
        permissions=("products.read",),
        session_id=session_id,
        token_type=token_type,
        jti="jwt-1",
    )


def session(
    *,
    active: bool = True,
    tenant_id: str = "tenant-1",
    user_id: str = "user-1",
) -> SimpleNamespace:
    return SimpleNamespace(
        id="session-1",
        user_id=user_id,
        tenant_id=tenant_id,
        is_active=active,
    )


def tenant(
    *,
    status: str = "active",
) -> SimpleNamespace:
    return SimpleNamespace(
        id="tenant-1",
        display_name="Tenant One",
        status=status,
    )


def branch(
    *,
    branch_id: str = "branch-1",
    tenant_id: str = "tenant-1",
    name: str = "Main",
    code: str = "MAIN",
) -> SimpleNamespace:
    return SimpleNamespace(
        id=branch_id,
        tenant_id=tenant_id,
        name=name,
        code=code,
        is_active=True,
    )


class FakeAuthorizer:
    def __init__(
        self,
        *,
        user: FakeUser | None = None,
        permissions: frozenset[str] | None = None,
        branch_ids: frozenset[str] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.user = user or FakeUser()
        self.permissions = permissions or frozenset()
        self.branch_ids = branch_ids or frozenset()
        self.error = error

    def authorize(self, *_args, **_kwargs):
        if self.error is not None:
            raise self.error

        return self.user

    def refresh_context(self, user, **_kwargs):
        return AuthorizationContext(
            user_id=user.id,
            tenant_id=user.tenant_id,
            is_owner=getattr(
                user,
                "is_owner",
                False,
            ),
            is_platform_admin=getattr(
                user,
                "is_platform_admin",
                False,
            ),
            roles=frozenset(
                role.name
                for role in user.roles
            ),
            permissions=self.permissions,
            branch_ids=self.branch_ids,
        )


def service(
    authorizer: FakeAuthorizer | None = None,
) -> CurrentSessionService:
    return CurrentSessionService(
        authorizer=authorizer or FakeAuthorizer(),
    )


def prepare(
    svc: CurrentSessionService,
    monkeypatch: pytest.MonkeyPatch,
    *,
    active_session=session(),
    active_tenant=tenant(),
    branches: list[SimpleNamespace] | None = None,
) -> None:
    monkeypatch.setattr(
        svc,
        "_get_active_session",
        lambda _session_id: active_session,
    )
    monkeypatch.setattr(
        svc,
        "_get_active_tenant",
        lambda _tenant_id: active_tenant,
    )
    monkeypatch.setattr(
        svc,
        "_get_accessible_branches",
        lambda **_kwargs: branches if branches is not None else [branch()],
    )


def test_active_user_receives_session_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = FakeUser(
        roles=[
            FakeRole(id="role-2", name="Manager", code="manager"),
            FakeRole(id="role-1", name="Cashier", code="cashier"),
        ],
    )
    svc = service(
        FakeAuthorizer(
            user=user,
            permissions=frozenset(
                {
                    "sales.create",
                    "products.read",
                    "products.read",
                }
            ),
        )
    )
    prepare(svc, monkeypatch)

    response = svc.get_current_session(identity())

    assert response.user.id == "user-1"
    assert response.user.is_platform_admin is False
    assert response.tenant.id == "tenant-1"
    assert [role.code for role in response.roles] == [
        "cashier",
        "manager",
    ]
    assert response.permissions == [
        "products.read",
        "sales.create",
    ]
    assert response.branches[0].id == "branch-1"
    assert response.default_branch_id is None


def test_platform_administrator_status_is_exposed_from_authorization_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = FakeUser(
        is_platform_admin=True,
    )
    svc = service(
        FakeAuthorizer(
            user=user,
        )
    )
    prepare(svc, monkeypatch)

    response = svc.get_current_session(identity())

    assert response.user.is_platform_admin is True


def test_password_and_security_fields_are_not_exposed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    svc = service()
    prepare(svc, monkeypatch)

    response = svc.get_current_session(identity())

    assert not hasattr(response.user, "password_hash")
    assert not hasattr(response, "access_token")
    assert not hasattr(response, "refresh_token")


def test_refresh_token_identity_is_rejected() -> None:
    svc = service()

    with pytest.raises(InvalidAccessTokenError):
        svc.get_current_session(
            identity(token_type=JWTTokenType.REFRESH),
        )


def test_inactive_session_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    svc = service()
    prepare(
        svc,
        monkeypatch,
        active_session=None,
    )

    with pytest.raises(SessionNotFoundError):
        svc.get_current_session(identity())


def test_cross_tenant_session_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    svc = service()
    prepare(
        svc,
        monkeypatch,
        active_session=session(tenant_id="tenant-2"),
    )

    with pytest.raises(AuthenticationError):
        svc.get_current_session(identity())


def test_inactive_user_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    svc = service(
        FakeAuthorizer(
            error=AccountInactiveError(),
        )
    )
    prepare(svc, monkeypatch)

    with pytest.raises(AccountInactiveError):
        svc.get_current_session(identity())


def test_locked_user_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    svc = service(
        FakeAuthorizer(
            error=AccountLockedError(),
        )
    )
    prepare(svc, monkeypatch)

    with pytest.raises(AccountLockedError):
        svc.get_current_session(identity())


def test_inactive_tenant_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    svc = service()
    prepare(svc, monkeypatch)
    monkeypatch.setattr(
        svc,
        "_get_active_tenant",
        lambda _tenant_id: (_ for _ in ()).throw(
            TenantAccessDeniedError(
                "Authenticated tenant is not active."
            )
        ),
    )

    with pytest.raises(TenantAccessDeniedError):
        svc.get_current_session(identity())


def test_branch_scope_must_belong_to_accessible_branches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    svc = service()
    prepare(
        svc,
        monkeypatch,
        branches=[branch(branch_id="branch-2")],
    )

    with pytest.raises(BranchAccessDeniedError):
        svc.get_current_session(identity(branch_id="branch-1"))


def test_branch_list_reflects_authorization_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    svc = service(
        FakeAuthorizer(
            branch_ids=frozenset(),
        )
    )
    prepare(
        svc,
        monkeypatch,
        branches=[
            branch(branch_id="branch-1", code="A"),
            branch(branch_id="branch-2", code="B"),
        ],
    )

    response = svc.get_current_session(identity())

    assert [item.id for item in response.branches] == [
        "branch-1",
        "branch-2",
    ]
    assert response.default_branch_id is None
