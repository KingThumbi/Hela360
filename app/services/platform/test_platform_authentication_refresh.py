from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import create_app
from app.auth.exceptions import (
    AccountInactiveError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    PermissionDeniedError,
)
from app.extensions import db
from app.models import (
    PlatformPermission,
    PlatformRole,
    PlatformRolePermission,
    PlatformUser,
    PlatformUserRole,
)
from app.models.security import (
    TokenRevocationReason,
)
from app.services.platform.platform_authentication_service import (
    PLATFORM_OFFICE_ACCESS_PERMISSION,
    PlatformAuthenticationService,
)
from app.services.platform.platform_jwt_service import (
    PlatformJWTService,
)
from app.services.tenant.auth.password_service import (
    password_service,
)


TEST_PASSWORD = (
    "Hela360-Refresh-Test-2026!"
)


@pytest.fixture()
def app():
    app = create_app()

    app.config.update(
        TESTING=True,
        JWT_SECRET_KEY=(
            "platform-refresh-test-secret-"
            "key-at-least-32-bytes-long"
        ),
        JWT_ACCESS_TOKEN_MINUTES=15,
        JWT_REFRESH_TOKEN_DAYS=7,
    )

    return app


@pytest.fixture()
def platform_session(app):
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()

        session = Session(
            bind=connection,
            expire_on_commit=False,
        )

        try:
            yield session

        finally:
            session.close()
            transaction.rollback()
            connection.close()


def create_platform_user(
    session: Session,
) -> PlatformUser:
    suffix = uuid4().hex[:12]

    user = PlatformUser(
        id=str(uuid4()),
        first_name="Platform",
        last_name="Refresh",
        email=(
            f"platform-refresh-{suffix}"
            "@example.invalid"
        ),
        username=(
            f"platform-refresh-{suffix}"
        ),
        password_hash=(
            password_service
            .hash_password(
                TEST_PASSWORD
            )
        ),
        is_active=True,
    )

    session.add(user)
    session.flush()

    return user


def get_or_create_permission(
    session: Session,
    code: str,
) -> PlatformPermission:
    permission = session.scalar(
        select(
            PlatformPermission
        ).where(
            PlatformPermission.code
            == code
        )
    )

    if permission is not None:
        return permission

    permission = PlatformPermission(
        id=str(uuid4()),
        code=code,
        name=code,
        module_code="test",
        description=(
            f"Test permission {code}"
        ),
    )

    session.add(permission)
    session.flush()

    return permission


def assign_role(
    session: Session,
    *,
    user: PlatformUser,
    permission_codes: tuple[str, ...],
) -> PlatformRole:
    suffix = uuid4().hex[:12]

    role = PlatformRole(
        id=str(uuid4()),
        code=(
            f"refresh-role-{suffix}"
        ),
        name=(
            f"Refresh Role {suffix}"
        ),
        description=(
            "Platform refresh test role."
        ),
        is_system=False,
    )

    session.add(role)
    session.flush()

    for code in permission_codes:
        permission = (
            get_or_create_permission(
                session,
                code,
            )
        )

        session.add(
            PlatformRolePermission(
                platform_role_id=(
                    role.id
                ),
                platform_permission_id=(
                    permission.id
                ),
                assignment_reason=(
                    "Refresh test."
                ),
            )
        )

    session.add(
        PlatformUserRole(
            platform_user_id=(
                user.id
            ),
            platform_role_id=(
                role.id
            ),
            assignment_reason=(
                "Refresh test."
            ),
        )
    )

    session.flush()
    session.expire_all()

    return role


def login(
    session: Session,
):
    user = create_platform_user(
        session
    )

    role = assign_role(
        session,
        user=user,
        permission_codes=(
            PLATFORM_OFFICE_ACCESS_PERMISSION,
            "platform.catalogue.read",
        ),
    )

    service = (
        PlatformAuthenticationService(
            session
        )
    )

    result = service.login(
        username_or_email=(
            user.email
        ),
        password=(
            TEST_PASSWORD
        ),
        ip_address="127.0.0.1",
        user_agent="pytest",
    )

    return (
        service,
        user,
        role,
        result,
    )


def test_refresh_rotates_token_and_preserves_family(
    platform_session: Session,
):
    (
        service,
        user,
        _role,
        login_result,
    ) = login(platform_session)

    old_record = (
        login_result
        .refresh_token_record
    )

    result = service.refresh(
        refresh_token=(
            login_result
            .refresh_token
        ),
        ip_address="127.0.0.2",
        user_agent="pytest-refresh",
    )

    assert result.user.id == user.id

    assert result.refresh_token != (
        login_result.refresh_token
    )

    assert result.access_token != (
        login_result.access_token
    )

    assert old_record.is_rotated

    assert old_record.revoke_reason == (
        TokenRevocationReason
        .TOKEN_ROTATED
    )

    assert (
        result.refresh_token_record
        .parent_token_id
        == old_record.id
    )

    assert (
        result.refresh_token_record
        .token_family
        == old_record.token_family
    )

    assert (
        result.session.expires_at
        == result.refresh_token_record
        .expires_at
    )


def test_refresh_recalculates_current_permissions(
    platform_session: Session,
):
    (
        service,
        user,
        role,
        login_result,
    ) = login(platform_session)

    settings_permission = (
        get_or_create_permission(
            platform_session,
            "platform.settings.read",
        )
    )

    platform_session.add(
        PlatformRolePermission(
            platform_role_id=(
                role.id
            ),
            platform_permission_id=(
                settings_permission.id
            ),
            assignment_reason=(
                "Permission changed "
                "after login."
            ),
        )
    )

    platform_session.flush()
    platform_session.expire_all()

    result = service.refresh(
        refresh_token=(
            login_result
            .refresh_token
        )
    )

    payload = (
        PlatformJWTService
        .decode_access_token(
            result.access_token
        )
    )

    identity = (
        PlatformJWTService
        .extract_identity(
            payload
        )
    )

    assert (
        "platform.settings.read"
        in identity.permissions
    )

    assert (
        user.id
        == identity.platform_user_id
    )


def test_reuse_of_rotated_token_revokes_family_and_session(
    platform_session: Session,
):
    (
        service,
        _user,
        _role,
        login_result,
    ) = login(platform_session)

    rotated = service.refresh(
        refresh_token=(
            login_result
            .refresh_token
        )
    )

    with pytest.raises(
        InvalidCredentialsError
    ):
        service.refresh(
            refresh_token=(
                login_result
                .refresh_token
            )
        )

    assert (
        rotated
        .refresh_token_record
        .revoke_reason
        == TokenRevocationReason
        .REUSE_DETECTED
    )

    assert (
        login_result
        .session
        .revoke_reason
        == TokenRevocationReason
        .REUSE_DETECTED
    )


def test_refresh_rejects_unpersisted_signed_token(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    fake_session_id = str(
        uuid4()
    )

    token = (
        PlatformJWTService
        .issue_refresh_token(
            platform_user_id=(
                user.id
            ),
            session_id=(
                fake_session_id
            ),
        )
    )

    service = (
        PlatformAuthenticationService(
            platform_session
        )
    )

    with pytest.raises(
        InvalidCredentialsError,
        match="not found",
    ):
        service.refresh(
            refresh_token=token
        )


def test_refresh_rejects_access_token(
    platform_session: Session,
):
    (
        service,
        _user,
        _role,
        login_result,
    ) = login(platform_session)

    with pytest.raises(
        InvalidRefreshTokenError
    ):
        service.refresh(
            refresh_token=(
                login_result
                .access_token
            )
        )


def test_revoked_session_invalidates_refresh_token(
    platform_session: Session,
):
    (
        service,
        _user,
        _role,
        login_result,
    ) = login(platform_session)

    service.sessions.revoke(
        login_result.session,
        reason=(
            TokenRevocationReason
            .ADMIN_REVOKED
        ),
    )

    with pytest.raises(
        AccountInactiveError
    ):
        service.refresh(
            refresh_token=(
                login_result
                .refresh_token
            )
        )

    assert (
        login_result
        .refresh_token_record
        .revoke_reason
        == TokenRevocationReason
        .SESSION_EXPIRED
    )


def test_disabled_user_revokes_refresh_family_and_session(
    platform_session: Session,
):
    (
        service,
        user,
        _role,
        login_result,
    ) = login(platform_session)

    user.is_active = False
    platform_session.flush()

    with pytest.raises(
        AccountInactiveError
    ):
        service.refresh(
            refresh_token=(
                login_result
                .refresh_token
            )
        )

    assert (
        login_result
        .refresh_token_record
        .revoke_reason
        == TokenRevocationReason
        .ACCOUNT_DISABLED
    )

    assert (
        login_result
        .session
        .revoke_reason
        == TokenRevocationReason
        .ACCOUNT_DISABLED
    )


def test_loss_of_office_access_revokes_session(
    platform_session: Session,
):
    (
        service,
        _user,
        role,
        login_result,
    ) = login(platform_session)

    office_permission = (
        platform_session.scalar(
            select(
                PlatformPermission
            ).where(
                PlatformPermission.code
                == PLATFORM_OFFICE_ACCESS_PERMISSION
            )
        )
    )

    assignment = (
        platform_session.get(
            PlatformRolePermission,
            {
                "platform_role_id": (
                    role.id
                ),
                "platform_permission_id": (
                    office_permission.id
                ),
            },
        )
    )

    assert assignment is not None

    platform_session.delete(
        assignment
    )

    platform_session.flush()
    platform_session.expire_all()

    with pytest.raises(
        PermissionDeniedError,
        match="platform.office.access",
    ):
        service.refresh(
            refresh_token=(
                login_result
                .refresh_token
            )
        )

    assert (
        login_result
        .refresh_token_record
        .revoke_reason
        == TokenRevocationReason
        .ADMIN_REVOKED
    )

    assert (
        login_result
        .session
        .revoke_reason
        == TokenRevocationReason
        .ADMIN_REVOKED
    )


def test_refresh_result_has_no_tenant_scope(
    platform_session: Session,
):
    (
        service,
        _user,
        _role,
        login_result,
    ) = login(platform_session)

    result = service.refresh(
        refresh_token=(
            login_result
            .refresh_token
        )
    )

    assert not hasattr(
        result.user,
        "tenant_id",
    )

    assert not hasattr(
        result.session,
        "tenant_id",
    )

    assert not hasattr(
        result.refresh_token_record,
        "tenant_id",
    )
