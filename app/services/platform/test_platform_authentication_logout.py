from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app import create_app
from app.auth.exceptions import (
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)
from app.extensions import db
from app.models import (
    PlatformRole,
    PlatformUser,
    PlatformUserRole,
)
from app.models.security import (
    TokenRevocationReason,
)
from app.services.platform.platform_authentication_service import (
    PlatformAuthenticationService,
)
from app.services.platform.platform_permission_catalogue_service import (
    PlatformPermissionCatalogueService,
)
from app.services.platform.platform_role_policy import (
    OFFICE_ADMIN_ROLE,
)
from app.services.platform.platform_role_provisioning_service import (
    PlatformRoleProvisioningService,
)
from app.services.tenant.auth.password_service import (
    password_service,
)


TEST_PASSWORD = (
    "Hela360-Logout-Test-2026!"
)


@pytest.fixture()
def app():
    app = create_app()

    app.config.update(
        TESTING=True,
        JWT_SECRET_KEY=(
            "platform-logout-test-secret-"
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


def create_office_user(
    session: Session,
) -> PlatformUser:
    PlatformPermissionCatalogueService(
        session
    ).synchronize()

    PlatformRoleProvisioningService(
        session
    ).synchronize()

    role = session.query(
        PlatformRole
    ).filter(
        PlatformRole.code
        == OFFICE_ADMIN_ROLE.code
    ).one()

    suffix = uuid4().hex[:12]

    user = PlatformUser(
        id=str(uuid4()),
        first_name="Platform",
        last_name="Logout",
        email=(
            f"platform-logout-{suffix}"
            "@example.invalid"
        ),
        username=(
            f"platform-logout-{suffix}"
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

    session.add(
        PlatformUserRole(
            platform_user_id=(
                user.id
            ),
            platform_role_id=(
                role.id
            ),
            assignment_reason=(
                "Logout test."
            ),
        )
    )

    session.flush()
    session.expire_all()

    return user


def login(
    session: Session,
    user: PlatformUser,
):
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
    )

    return service, result


def test_logout_revokes_session_and_refresh_token(
    platform_session: Session,
):
    user = create_office_user(
        platform_session
    )

    service, login_result = login(
        platform_session,
        user,
    )

    result = service.logout(
        refresh_token=(
            login_result
            .refresh_token
        )
    )

    assert result.platform_user_id == (
        user.id
    )

    assert (
        result.platform_session_id
        == login_result.session.id
    )

    assert result.refresh_tokens_revoked == 1

    assert result.session_revoked is True

    assert (
        login_result
        .refresh_token_record
        .revoke_reason
        == TokenRevocationReason.LOGOUT
    )

    assert (
        login_result
        .session
        .revoke_reason
        == TokenRevocationReason.LOGOUT
    )


def test_logout_is_idempotent(
    platform_session: Session,
):
    user = create_office_user(
        platform_session
    )

    service, login_result = login(
        platform_session,
        user,
    )

    first = service.logout(
        refresh_token=(
            login_result
            .refresh_token
        )
    )

    second = service.logout(
        refresh_token=(
            login_result
            .refresh_token
        )
    )

    assert first.refresh_tokens_revoked == 1
    assert first.session_revoked is True

    assert second.refresh_tokens_revoked == 0
    assert second.session_revoked is False


def test_rotated_parent_can_still_terminate_session(
    platform_session: Session,
):
    user = create_office_user(
        platform_session
    )

    service, login_result = login(
        platform_session,
        user,
    )

    parent_record = (
        login_result
        .refresh_token_record
    )

    refreshed = service.refresh(
        refresh_token=(
            login_result
            .refresh_token
        )
    )

    assert parent_record.is_rotated

    result = service.logout(
        refresh_token=(
            login_result
            .refresh_token
        )
    )

    assert result.refresh_tokens_revoked == 1
    assert result.session_revoked is True

    assert (
        parent_record.revoke_reason
        == TokenRevocationReason
        .TOKEN_ROTATED
    )

    assert (
        refreshed
        .refresh_token_record
        .revoke_reason
        == TokenRevocationReason
        .LOGOUT
    )

    assert (
        login_result
        .session
        .revoke_reason
        == TokenRevocationReason.LOGOUT
    )


def test_logout_rejects_access_token(
    platform_session: Session,
):
    user = create_office_user(
        platform_session
    )

    service, login_result = login(
        platform_session,
        user,
    )

    with pytest.raises(
        InvalidRefreshTokenError
    ):
        service.logout(
            refresh_token=(
                login_result
                .access_token
            )
        )


def test_logout_rejects_unpersisted_refresh_token(
    platform_session: Session,
):
    user = create_office_user(
        platform_session
    )

    service, login_result = login(
        platform_session,
        user,
    )

    service.logout(
        refresh_token=(
            login_result
            .refresh_token
        )
    )

    # Delete the historical persistence record to simulate a valid signed JWT
    # whose server-side authentication evidence no longer exists.
    platform_session.delete(
        login_result
        .refresh_token_record
    )

    platform_session.flush()

    with pytest.raises(
        InvalidCredentialsError,
        match="not found",
    ):
        service.logout(
            refresh_token=(
                login_result
                .refresh_token
            )
        )


def test_logout_all_revokes_every_user_session(
    platform_session: Session,
):
    user = create_office_user(
        platform_session
    )

    service, first = login(
        platform_session,
        user,
    )

    _service, second = login(
        platform_session,
        user,
    )

    assert first.session.id != (
        second.session.id
    )

    result = service.logout_all(
        platform_user_id=user.id
    )

    assert result.platform_user_id == (
        user.id
    )

    assert result.refresh_tokens_revoked == 2
    assert result.sessions_revoked == 2

    assert (
        first
        .refresh_token_record
        .revoke_reason
        == TokenRevocationReason
        .LOGOUT_ALL
    )

    assert (
        second
        .refresh_token_record
        .revoke_reason
        == TokenRevocationReason
        .LOGOUT_ALL
    )

    assert (
        first.session.revoke_reason
        == TokenRevocationReason
        .LOGOUT_ALL
    )

    assert (
        second.session.revoke_reason
        == TokenRevocationReason
        .LOGOUT_ALL
    )


def test_logout_all_is_idempotent(
    platform_session: Session,
):
    user = create_office_user(
        platform_session
    )

    service, _result = login(
        platform_session,
        user,
    )

    first = service.logout_all(
        platform_user_id=user.id
    )

    second = service.logout_all(
        platform_user_id=user.id
    )

    assert first.refresh_tokens_revoked == 1
    assert first.sessions_revoked == 1

    assert second.refresh_tokens_revoked == 0
    assert second.sessions_revoked == 0


def test_logout_all_requires_user_id(
    platform_session: Session,
):
    service = (
        PlatformAuthenticationService(
            platform_session
        )
    )

    with pytest.raises(
        ValueError,
        match="platform_user_id is required",
    ):
        service.logout_all(
            platform_user_id=""
        )


def test_logout_results_have_no_tenant_scope(
    platform_session: Session,
):
    user = create_office_user(
        platform_session
    )

    service, login_result = login(
        platform_session,
        user,
    )

    result = service.logout(
        refresh_token=(
            login_result
            .refresh_token
        )
    )

    assert not hasattr(
        result,
        "tenant_id",
    )

    assert not hasattr(
        result,
        "branch_id",
    )
