from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app import create_app
from app.extensions import db
from app.models import (
    PlatformSession,
    PlatformUser,
)
from app.models.security import (
    TokenRevocationReason,
)
from app.services.platform.platform_session_service import (
    PlatformSessionService,
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
        last_name="Session",
        email=(
            f"platform-session-{suffix}"
            "@example.invalid"
        ),
        username=(
            f"platform-session-{suffix}"
        ),
        password_hash="test-hash",
        is_active=True,
    )

    session.add(
        user
    )

    session.flush()

    return user


def test_create_platform_session(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    service = PlatformSessionService(
        platform_session
    )

    expires_at = (
        datetime.now(UTC)
        + timedelta(hours=1)
    )

    auth_session = service.create(
        platform_user_id=user.id,
        expires_at=expires_at,
        ip_address="127.0.0.1",
        device_name="Test Device",
        authentication_method="password",
    )

    assert auth_session.id is not None

    assert (
        auth_session.platform_user_id
        == user.id
    )

    assert auth_session.ip_address == (
        "127.0.0.1"
    )

    assert auth_session.last_ip_address == (
        "127.0.0.1"
    )

    assert auth_session.authentication_method == (
        "password"
    )

    assert auth_session.is_active is True


def test_create_rejects_expired_session(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    service = PlatformSessionService(
        platform_session
    )

    with pytest.raises(
        ValueError,
        match="expiry must be in the future",
    ):
        service.create(
            platform_user_id=user.id,
            expires_at=(
                datetime.now(UTC)
                - timedelta(seconds=1)
            ),
        )


def test_get_and_get_active(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    service = PlatformSessionService(
        platform_session
    )

    auth_session = service.create(
        platform_user_id=user.id,
        expires_at=(
            datetime.now(UTC)
            + timedelta(hours=1)
        ),
    )

    assert service.get(
        auth_session.id
    ) is auth_session

    assert service.get_active(
        auth_session.id
    ) is auth_session

    assert service.get(
        str(uuid4())
    ) is None


def test_get_active_rejects_revoked_session(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    service = PlatformSessionService(
        platform_session
    )

    auth_session = service.create(
        platform_user_id=user.id,
        expires_at=(
            datetime.now(UTC)
            + timedelta(hours=1)
        ),
    )

    service.revoke(
        auth_session,
        reason=TokenRevocationReason.LOGOUT,
    )

    assert service.get_active(
        auth_session.id
    ) is None


def test_list_user_sessions_is_user_scoped(
    platform_session: Session,
):
    first_user = create_platform_user(
        platform_session
    )

    second_user = create_platform_user(
        platform_session
    )

    service = PlatformSessionService(
        platform_session
    )

    first = service.create(
        platform_user_id=first_user.id,
        expires_at=(
            datetime.now(UTC)
            + timedelta(hours=1)
        ),
    )

    second = service.create(
        platform_user_id=first_user.id,
        expires_at=(
            datetime.now(UTC)
            + timedelta(hours=2)
        ),
    )

    service.create(
        platform_user_id=second_user.id,
        expires_at=(
            datetime.now(UTC)
            + timedelta(hours=1)
        ),
    )

    sessions = service.list_user_sessions(
        platform_user_id=first_user.id
    )

    assert {
        item.id
        for item in sessions
    } == {
        first.id,
        second.id,
    }


def test_list_active_user_sessions_excludes_revoked(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    service = PlatformSessionService(
        platform_session
    )

    active = service.create(
        platform_user_id=user.id,
        expires_at=(
            datetime.now(UTC)
            + timedelta(hours=1)
        ),
    )

    revoked = service.create(
        platform_user_id=user.id,
        expires_at=(
            datetime.now(UTC)
            + timedelta(hours=1)
        ),
    )

    service.revoke(
        revoked,
        reason=TokenRevocationReason.LOGOUT,
    )

    sessions = service.list_active_user_sessions(
        platform_user_id=user.id
    )

    assert [
        item.id
        for item in sessions
    ] == [
        active.id
    ]


def test_touch_updates_activity_without_commit(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    service = PlatformSessionService(
        platform_session
    )

    auth_session = service.create(
        platform_user_id=user.id,
        expires_at=(
            datetime.now(UTC)
            + timedelta(hours=1)
        ),
        ip_address="127.0.0.1",
    )

    previous_activity = (
        auth_session.last_activity_at
    )

    service.touch(
        auth_session,
        ip_address="127.0.0.2",
    )

    assert (
        auth_session.last_activity_at
        >= previous_activity
    )

    assert auth_session.last_ip_address == (
        "127.0.0.2"
    )


def test_revoke_is_idempotent(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    service = PlatformSessionService(
        platform_session
    )

    auth_session = service.create(
        platform_user_id=user.id,
        expires_at=(
            datetime.now(UTC)
            + timedelta(hours=1)
        ),
    )

    first = service.revoke(
        auth_session,
        reason=TokenRevocationReason.LOGOUT,
    )

    revoked_at = (
        auth_session.revoked_at
    )

    second = service.revoke(
        auth_session,
        reason=(
            TokenRevocationReason
            .ADMIN_REVOKED
        ),
    )

    assert first is True
    assert second is False

    assert (
        auth_session.revoked_at
        == revoked_at
    )

    assert auth_session.revoke_reason == (
        TokenRevocationReason.LOGOUT
    )


def test_revoke_user_sessions_only_targets_one_user(
    platform_session: Session,
):
    target_user = create_platform_user(
        platform_session
    )

    other_user = create_platform_user(
        platform_session
    )

    service = PlatformSessionService(
        platform_session
    )

    target_one = service.create(
        platform_user_id=target_user.id,
        expires_at=(
            datetime.now(UTC)
            + timedelta(hours=1)
        ),
    )

    target_two = service.create(
        platform_user_id=target_user.id,
        expires_at=(
            datetime.now(UTC)
            + timedelta(hours=1)
        ),
    )

    other = service.create(
        platform_user_id=other_user.id,
        expires_at=(
            datetime.now(UTC)
            + timedelta(hours=1)
        ),
    )

    count = service.revoke_user_sessions(
        platform_user_id=target_user.id,
        reason=(
            TokenRevocationReason
            .ACCOUNT_DISABLED
        ),
    )

    assert count == 2

    assert target_one.revoked_at is not None
    assert target_two.revoked_at is not None

    assert target_one.revoke_reason == (
        TokenRevocationReason
        .ACCOUNT_DISABLED
    )

    assert other.revoked_at is None


def test_expire_stale_sessions(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    service = PlatformSessionService(
        platform_session
    )

    now = datetime.now(UTC)

    stale = PlatformSession(
        id=str(uuid4()),
        platform_user_id=user.id,
        created_at=(
            now - timedelta(hours=2)
        ),
        updated_at=(
            now - timedelta(hours=2)
        ),
        expires_at=(
            now - timedelta(minutes=1)
        ),
        last_activity_at=(
            now - timedelta(hours=1)
        ),
    )

    active = PlatformSession(
        id=str(uuid4()),
        platform_user_id=user.id,
        created_at=(
            now - timedelta(minutes=5)
        ),
        updated_at=(
            now - timedelta(minutes=5)
        ),
        expires_at=(
            now + timedelta(hours=1)
        ),
        last_activity_at=now,
    )

    platform_session.add_all(
        [
            stale,
            active,
        ]
    )

    platform_session.flush()

    count = (
        service.expire_stale_sessions()
    )

    assert count == 1

    assert stale.revoked_at is not None

    assert stale.revoke_reason == (
        TokenRevocationReason
        .SESSION_EXPIRED
    )

    assert active.revoked_at is None


def test_service_has_no_tenant_scope():
    assert (
        "tenant_id"
        not in PlatformSession.__table__.columns
    )

    assert (
        "branch_id"
        not in PlatformSession.__table__.columns
    )
