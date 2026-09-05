from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from werkzeug.security import (
    generate_password_hash,
)

from app import create_app
from app.auth.exceptions import (
    AccountInactiveError,
    AccountLockedError,
    InvalidCredentialsError,
    PermissionDeniedError,
)
from app.extensions import db
from app.models import (
    PlatformLoginAttempt,
    PlatformPermission,
    PlatformRefreshToken,
    PlatformRole,
    PlatformRolePermission,
    PlatformSession,
    PlatformUser,
    PlatformUserRole,
)
from app.services.platform.platform_authentication_service import (
    PLATFORM_OFFICE_ACCESS_PERMISSION,
    PlatformAuthenticationService,
)
from app.services.platform.platform_login_attempt_service import (
    PlatformLoginAttemptService,
)
from app.services.tenant.auth.password_service import (
    password_service,
)


TEST_PASSWORD = (
    "Hela360-Test-Password-2026!"
)


@pytest.fixture()
def app():
    app = create_app()

    app.config.update(
        TESTING=True,
        JWT_SECRET_KEY=(
            "platform-authentication-test-secret-"
            "key-at-least-32-bytes"
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
    *,
    active: bool = True,
    password_hash: str | None = None,
) -> PlatformUser:
    suffix = uuid4().hex[:12]

    user = PlatformUser(
        id=str(uuid4()),
        first_name="Platform",
        last_name="Authentication",
        email=(
            f"platform-auth-{suffix}"
            "@example.invalid"
        ),
        username=(
            f"platform-auth-{suffix}"
        ),
        password_hash=(
            password_hash
            or password_service
            .hash_password(
                TEST_PASSWORD
            )
        ),
        is_active=active,
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


def assign_permissions(
    session: Session,
    *,
    user: PlatformUser,
    permissions: tuple[str, ...],
) -> PlatformRole:
    suffix = uuid4().hex[:12]

    role = PlatformRole(
        id=str(uuid4()),
        code=f"test-role-{suffix}",
        name=f"Test Role {suffix}",
        description=(
            "Platform authentication test role."
        ),
        is_system=False,
    )

    session.add(role)
    session.flush()

    for code in permissions:
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
                    "Authentication test."
                ),
            )
        )

    session.add(
        PlatformUserRole(
            platform_user_id=user.id,
            platform_role_id=role.id,
            assignment_reason=(
                "Authentication test."
            ),
        )
    )

    session.flush()
    session.expire_all()

    return role


def login_service(
    session: Session,
    *,
    max_failed_attempts: int = 5,
) -> PlatformAuthenticationService:
    attempts = (
        PlatformLoginAttemptService(
            session,
            max_failed_attempts=(
                max_failed_attempts
            ),
        )
    )

    return PlatformAuthenticationService(
        session,
        login_attempts=attempts,
    )


def test_successful_platform_login(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    assign_permissions(
        platform_session,
        user=user,
        permissions=(
            PLATFORM_OFFICE_ACCESS_PERMISSION,
            "platform.catalogue.read",
        ),
    )

    result = login_service(
        platform_session
    ).login(
        username_or_email=user.email,
        password=TEST_PASSWORD,
        device_name="Test Browser",
        ip_address="127.0.0.1",
        user_agent="pytest",
    )

    assert result.user.id == user.id

    assert (
        result.authorization
        .platform_user_id
        == user.id
    )

    assert (
        PLATFORM_OFFICE_ACCESS_PERMISSION
        in result.authorization.permissions
    )

    assert result.access_token
    assert result.refresh_token

    assert (
        result.session
        .platform_user_id
        == user.id
    )

    assert (
        result.refresh_token_record
        .platform_user_id
        == user.id
    )

    assert (
        result.refresh_token_record
        .platform_session_id
        == result.session.id
    )


def test_login_by_username_is_case_insensitive(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    assign_permissions(
        platform_session,
        user=user,
        permissions=(
            PLATFORM_OFFICE_ACCESS_PERMISSION,
        ),
    )

    result = login_service(
        platform_session
    ).login(
        username_or_email=(
            user.username.upper()
        ),
        password=TEST_PASSWORD,
    )

    assert result.user.id == user.id


def test_wrong_password_records_failure(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    assign_permissions(
        platform_session,
        user=user,
        permissions=(
            PLATFORM_OFFICE_ACCESS_PERMISSION,
        ),
    )

    service = login_service(
        platform_session
    )

    with pytest.raises(
        InvalidCredentialsError
    ):
        service.login(
            username_or_email=(
                user.username
            ),
            password="wrong-password",
        )

    failures = list(
        platform_session.scalars(
            select(
                PlatformLoginAttempt
            ).where(
                PlatformLoginAttempt
                .platform_user_id
                == user.id,
                PlatformLoginAttempt
                .successful
                .is_(False),
            )
        ).all()
    )

    assert len(failures) == 1

    assert failures[0].email == (
        user.email.lower()
    )

    assert (
        failures[0].failure_reason
        == "Incorrect password"
    )


def test_unknown_account_records_failure(
    platform_session: Session,
):
    service = login_service(
        platform_session
    )

    with pytest.raises(
        InvalidCredentialsError
    ):
        service.login(
            username_or_email=(
                "missing@example.invalid"
            ),
            password=TEST_PASSWORD,
        )

    attempt = platform_session.scalar(
        select(
            PlatformLoginAttempt
        ).where(
            PlatformLoginAttempt.email
            == "missing@example.invalid"
        )
    )

    assert attempt is not None
    assert attempt.successful is False
    assert attempt.platform_user_id is None

    assert attempt.failure_reason == (
        "Unknown account"
    )


def test_inactive_platform_user_is_rejected(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session,
        active=False,
    )

    assign_permissions(
        platform_session,
        user=user,
        permissions=(
            PLATFORM_OFFICE_ACCESS_PERMISSION,
        ),
    )

    with pytest.raises(
        AccountInactiveError
    ):
        login_service(
            platform_session
        ).login(
            username_or_email=user.email,
            password=TEST_PASSWORD,
        )

    assert not platform_session.scalars(
        select(
            PlatformSession
        ).where(
            PlatformSession
            .platform_user_id
            == user.id
        )
    ).all()


def test_platform_user_without_office_access_is_denied(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    assign_permissions(
        platform_session,
        user=user,
        permissions=(
            "platform.catalogue.read",
        ),
    )

    with pytest.raises(
        PermissionDeniedError,
        match="platform.office.access",
    ):
        login_service(
            platform_session
        ).login(
            username_or_email=user.email,
            password=TEST_PASSWORD,
        )

    assert not platform_session.scalars(
        select(
            PlatformSession
        ).where(
            PlatformSession
            .platform_user_id
            == user.id
        )
    ).all()


def test_success_persists_session_refresh_token_and_attempt(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    assign_permissions(
        platform_session,
        user=user,
        permissions=(
            PLATFORM_OFFICE_ACCESS_PERMISSION,
        ),
    )

    result = login_service(
        platform_session
    ).login(
        username_or_email=user.email,
        password=TEST_PASSWORD,
    )

    persisted_session = (
        platform_session.get(
            PlatformSession,
            result.session.id,
        )
    )

    persisted_refresh = (
        platform_session.get(
            PlatformRefreshToken,
            result
            .refresh_token_record
            .id,
        )
    )

    success = platform_session.scalar(
        select(
            PlatformLoginAttempt
        ).where(
            PlatformLoginAttempt
            .platform_user_id
            == user.id,
            PlatformLoginAttempt
            .successful
            .is_(True),
        )
    )

    assert persisted_session is not None
    assert persisted_refresh is not None
    assert success is not None

    assert (
        persisted_session.expires_at
        == result
        .refresh_token_record
        .expires_at
    )


def test_successful_login_upgrades_legacy_password_hash(
    platform_session: Session,
):
    legacy_hash = (
        generate_password_hash(
            TEST_PASSWORD
        )
    )

    user = create_platform_user(
        platform_session,
        password_hash=legacy_hash,
    )

    assign_permissions(
        platform_session,
        user=user,
        permissions=(
            PLATFORM_OFFICE_ACCESS_PERMISSION,
        ),
    )

    login_service(
        platform_session
    ).login(
        username_or_email=user.email,
        password=TEST_PASSWORD,
    )

    assert user.password_hash != (
        legacy_hash
    )

    assert user.password_hash.startswith(
        "$argon2"
    )


def test_account_lockout_cannot_be_bypassed_by_switching_to_username(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    assign_permissions(
        platform_session,
        user=user,
        permissions=(
            PLATFORM_OFFICE_ACCESS_PERMISSION,
        ),
    )

    service = login_service(
        platform_session,
        max_failed_attempts=2,
    )

    for _ in range(2):
        with pytest.raises(
            InvalidCredentialsError
        ):
            service.login(
                username_or_email=user.email,
                password="wrong-password",
            )

    with pytest.raises(
        AccountLockedError
    ):
        service.login(
            username_or_email=user.username,
            password=TEST_PASSWORD,
        )


def test_platform_authentication_has_no_tenant_records(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    assign_permissions(
        platform_session,
        user=user,
        permissions=(
            PLATFORM_OFFICE_ACCESS_PERMISSION,
        ),
    )

    result = login_service(
        platform_session
    ).login(
        username_or_email=user.email,
        password=TEST_PASSWORD,
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
