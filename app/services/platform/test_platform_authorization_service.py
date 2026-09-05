from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app import create_app
from app.auth.exceptions import (
    AccountInactiveError,
    PermissionDeniedError,
    UserNotFoundError,
)
from app.extensions import db
from app.models import (
    PlatformPermission,
    PlatformRole,
    PlatformRolePermission,
    PlatformUser,
    PlatformUserRole,
)
from app.services.platform.platform_authorization_service import (
    PlatformAuthorizationContext,
    PlatformAuthorizationService,
)
from app.services.platform.platform_permission_policy import (
    SYSTEM_PERMISSION,
)


@pytest.fixture()
def platform_session():
    app = create_app()

    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()

        session = Session(
            bind=connection,
            expire_on_commit=False,
        )

        try:
            session.execute(
                delete(PlatformUserRole)
            )
            session.execute(
                delete(PlatformRolePermission)
            )
            session.execute(
                delete(PlatformRole)
            )
            session.flush()

            yield session

        finally:
            session.close()
            transaction.rollback()
            connection.close()


def create_platform_user(
    session: Session,
    *,
    active: bool = True,
) -> PlatformUser:
    suffix = uuid4().hex[:12]

    user = PlatformUser(
        id=str(uuid4()),
        first_name="Platform",
        last_name="Authorization",
        email=(
            f"platform-authz-{suffix}"
            "@example.invalid"
        ),
        username=(
            f"platform-authz-{suffix}"
        ),
        password_hash="test-hash",
        is_active=active,
    )

    session.add(user)
    session.flush()

    return user


def create_permission(
    session: Session,
    code: str,
) -> PlatformPermission:
    permission = (
        session.query(PlatformPermission)
        .filter(PlatformPermission.code == code)
        .one_or_none()
    )

    if permission is not None:
        return permission

    permission = PlatformPermission(
        id=str(uuid4()),
        code=code,
        name=code,
        module_code=(
            "system"
            if code == SYSTEM_PERMISSION
            else "test"
        ),
        description=(
            f"Test permission {code}"
        ),
    )

    session.add(permission)
    session.flush()

    return permission


def create_role(
    session: Session,
    *,
    code: str,
    permissions: tuple[
        PlatformPermission,
        ...,
    ],
) -> PlatformRole:
    role = PlatformRole(
        id=str(uuid4()),
        code=code,
        name=code.replace(
            "_",
            " ",
        ).title(),
        description=f"Test role {code}",
        is_system=True,
    )

    session.add(role)
    session.flush()

    for permission in permissions:
        session.add(
            PlatformRolePermission(
                platform_role_id=role.id,
                platform_permission_id=(
                    permission.id
                ),
            )
        )

    session.flush()

    return role


def assign_role(
    session: Session,
    *,
    user: PlatformUser,
    role: PlatformRole,
) -> None:
    session.add(
        PlatformUserRole(
            platform_user_id=user.id,
            platform_role_id=role.id,
            assigned_by_platform_user_id=None,
            assignment_reason="Authorization test.",
        )
    )

    session.flush()
    session.expire_all()


def test_context_resolves_roles_and_permissions(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    catalogue_read = create_permission(
        platform_session,
        "platform.catalogue.read",
    )

    supplier_read = create_permission(
        platform_session,
        "platform.suppliers.read",
    )

    role = create_role(
        platform_session,
        code="catalogue_manager",
        permissions=(
            catalogue_read,
            supplier_read,
        ),
    )

    assign_role(
        platform_session,
        user=user,
        role=role,
    )

    context = PlatformAuthorizationService(
        platform_session
    ).context_for_user(
        user.id
    )

    assert context == (
        PlatformAuthorizationContext(
            platform_user_id=user.id,
            roles=(
                "catalogue_manager",
            ),
            permissions=(
                "platform.catalogue.read",
                "platform.suppliers.read",
            ),
        )
    )


def test_context_aggregates_multiple_roles_without_duplicates(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    office_access = create_permission(
        platform_session,
        "platform.office.access",
    )

    catalogue_read = create_permission(
        platform_session,
        "platform.catalogue.read",
    )

    first_role = create_role(
        platform_session,
        code="catalogue_manager",
        permissions=(
            office_access,
            catalogue_read,
        ),
    )

    second_role = create_role(
        platform_session,
        code="auditor",
        permissions=(
            office_access,
        ),
    )

    assign_role(
        platform_session,
        user=user,
        role=first_role,
    )

    assign_role(
        platform_session,
        user=user,
        role=second_role,
    )

    context = PlatformAuthorizationService(
        platform_session
    ).context_for_user(
        user.id
    )

    assert context.roles == (
        "auditor",
        "catalogue_manager",
    )

    assert context.permissions == (
        "platform.catalogue.read",
        "platform.office.access",
    )


def test_super_admin_wildcard_grants_any_canonical_permission(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    wildcard = create_permission(
        platform_session,
        SYSTEM_PERMISSION,
    )

    role = create_role(
        platform_session,
        code="super_admin",
        permissions=(
            wildcard,
        ),
    )

    assign_role(
        platform_session,
        user=user,
        role=role,
    )

    service = PlatformAuthorizationService(
        platform_session
    )

    context = service.context_for_user(
        user.id
    )

    assert context.permissions == (
        SYSTEM_PERMISSION,
    )

    assert (
        context.has_global_override
        is True
    )

    assert service.has_permission(
        user.id,
        "platform.settings.manage",
    )

    assert service.has_permission(
        user.id,
        "platform.catalogue.approve",
    )


def test_explicit_role_does_not_receive_wildcard(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    catalogue_read = create_permission(
        platform_session,
        "platform.catalogue.read",
    )

    role = create_role(
        platform_session,
        code="catalogue_manager",
        permissions=(
            catalogue_read,
        ),
    )

    assign_role(
        platform_session,
        user=user,
        role=role,
    )

    context = PlatformAuthorizationService(
        platform_session
    ).context_for_user(
        user.id
    )

    assert (
        context.has_global_override
        is False
    )

    assert context.has_permission(
        "platform.catalogue.read"
    )

    assert not context.has_permission(
        "platform.settings.manage"
    )


def test_require_permission_returns_context_when_allowed(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    permission = create_permission(
        platform_session,
        "platform.office.access",
    )

    role = create_role(
        platform_session,
        code="auditor",
        permissions=(
            permission,
        ),
    )

    assign_role(
        platform_session,
        user=user,
        role=role,
    )

    context = PlatformAuthorizationService(
        platform_session
    ).require_permission(
        user.id,
        "platform.office.access",
    )

    assert context.platform_user_id == (
        user.id
    )


def test_require_permission_denies_missing_permission(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    permission = create_permission(
        platform_session,
        "platform.catalogue.read",
    )

    role = create_role(
        platform_session,
        code="catalogue_manager",
        permissions=(
            permission,
        ),
    )

    assign_role(
        platform_session,
        user=user,
        role=role,
    )

    service = PlatformAuthorizationService(
        platform_session
    )

    with pytest.raises(
        PermissionDeniedError,
        match="platform.settings.manage",
    ):
        service.require_permission(
            user.id,
            "platform.settings.manage",
        )


def test_has_any_and_all_permissions(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    office_access = create_permission(
        platform_session,
        "platform.office.access",
    )

    catalogue_read = create_permission(
        platform_session,
        "platform.catalogue.read",
    )

    role = create_role(
        platform_session,
        code="catalogue_manager",
        permissions=(
            office_access,
            catalogue_read,
        ),
    )

    assign_role(
        platform_session,
        user=user,
        role=role,
    )

    service = PlatformAuthorizationService(
        platform_session
    )

    assert service.has_any_permission(
        user.id,
        [
            "platform.settings.manage",
            "platform.catalogue.read",
        ],
    )

    assert service.has_all_permissions(
        user.id,
        [
            "platform.office.access",
            "platform.catalogue.read",
        ],
    )

    assert not service.has_all_permissions(
        user.id,
        [
            "platform.catalogue.read",
            "platform.settings.manage",
        ],
    )


def test_unknown_permission_is_rejected(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    service = PlatformAuthorizationService(
        platform_session
    )

    with pytest.raises(
        ValueError,
        match="Unknown platform permission",
    ):
        service.has_permission(
            user.id,
            "platform.not.real",
        )


def test_missing_platform_user_is_rejected(
    platform_session: Session,
):
    service = PlatformAuthorizationService(
        platform_session
    )

    with pytest.raises(
        UserNotFoundError,
        match="Platform user not found",
    ):
        service.context_for_user(
            str(uuid4())
        )


def test_inactive_platform_user_is_rejected(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session,
        active=False,
    )

    service = PlatformAuthorizationService(
        platform_session
    )

    with pytest.raises(
        AccountInactiveError,
        match="Platform user is inactive",
    ):
        service.context_for_user(
            user.id
        )


def test_context_contains_no_tenant_scope():
    fields = {
        field
        for field in (
            PlatformAuthorizationContext
            .__dataclass_fields__
        )
    }

    assert fields == {
        "platform_user_id",
        "roles",
        "permissions",
    }

    assert "tenant_id" not in fields
    assert "branch_ids" not in fields
    assert "is_owner" not in fields
