from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import create_app
from app.extensions import db
from app.models import (
    PlatformLoginAttempt,
    PlatformRefreshToken,
    PlatformSession,
    PlatformUser,
)
from app.models.security import (
    TokenRevocationReason,
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
        last_name="Tester",
        email=f"platform-{suffix}@example.invalid",
        username=f"platform-{suffix}",
        password_hash="test-hash",
        is_active=True,
    )

    session.add(user)
    session.flush()

    return user


def create_platform_session(
    session: Session,
    user: PlatformUser,
) -> PlatformSession:
    auth_session = PlatformSession(
        id=str(uuid4()),
        platform_user_id=user.id,
        expires_at=(
            datetime.now(UTC)
            + timedelta(hours=1)
        ),
        last_activity_at=datetime.now(UTC),
        ip_address="127.0.0.1",
        last_ip_address="127.0.0.1",
        device_name="Test Device",
    )

    session.add(auth_session)
    session.flush()

    return auth_session


def create_refresh_token(
    session: Session,
    user: PlatformUser,
    auth_session: PlatformSession,
) -> PlatformRefreshToken:
    token = PlatformRefreshToken(
        id=str(uuid4()),
        platform_user_id=user.id,
        platform_session_id=auth_session.id,
        jwt_id=str(uuid4()),
        token_family=str(uuid4()),
        expires_at=(
            datetime.now(UTC)
            + timedelta(days=7)
        ),
    )

    session.add(token)
    session.flush()

    return token


def test_platform_session_is_platform_native(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    auth_session = create_platform_session(
        platform_session,
        user,
    )

    assert auth_session.platform_user_id == user.id

    assert (
        "tenant_id"
        not in PlatformSession.__table__.columns
    )

    assert (
        "branch_id"
        not in PlatformSession.__table__.columns
    )

    assert (
        "user_id"
        not in PlatformSession.__table__.columns
    )


def test_platform_session_lifecycle(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    auth_session = create_platform_session(
        platform_session,
        user,
    )

    assert auth_session.is_active is True
    assert auth_session.is_expired is False

    previous_activity = (
        auth_session.last_activity_at
    )

    auth_session.touch(
        ip_address="127.0.0.2"
    )

    assert (
        auth_session.last_activity_at
        >= previous_activity
    )

    assert (
        auth_session.last_ip_address
        == "127.0.0.2"
    )

    auth_session.revoke(
        reason=TokenRevocationReason.LOGOUT
    )

    platform_session.flush()

    assert auth_session.is_active is False

    assert auth_session.revoked_at is not None

    assert auth_session.revoke_reason == (
        TokenRevocationReason.LOGOUT
    )


def test_platform_refresh_token_relationships(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    auth_session = create_platform_session(
        platform_session,
        user,
    )

    token = create_refresh_token(
        platform_session,
        user,
        auth_session,
    )

    loaded = platform_session.scalar(
        select(PlatformRefreshToken)
        .where(
            PlatformRefreshToken.id
            == token.id
        )
    )

    assert loaded is not None

    assert (
        loaded.platform_user_id
        == user.id
    )

    assert (
        loaded.platform_session_id
        == auth_session.id
    )

    assert loaded.platform_user.id == user.id

    assert loaded.session.id == auth_session.id


def test_platform_refresh_token_rotation(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    auth_session = create_platform_session(
        platform_session,
        user,
    )

    token = create_refresh_token(
        platform_session,
        user,
        auth_session,
    )

    assert token.is_active is True
    assert token.is_rotated is False

    token.rotate()

    platform_session.flush()

    assert token.is_active is False
    assert token.is_rotated is True
    assert token.replaced_at is not None
    assert token.revoked_at is not None

    assert token.revoke_reason == (
        TokenRevocationReason.TOKEN_ROTATED
    )


def test_platform_refresh_token_parent_child_chain(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    auth_session = create_platform_session(
        platform_session,
        user,
    )

    parent = create_refresh_token(
        platform_session,
        user,
        auth_session,
    )

    child = PlatformRefreshToken(
        id=str(uuid4()),
        platform_user_id=user.id,
        platform_session_id=auth_session.id,
        jwt_id=str(uuid4()),
        token_family=parent.token_family,
        expires_at=(
            datetime.now(UTC)
            + timedelta(days=7)
        ),
        parent_token_id=parent.id,
    )

    platform_session.add(child)
    platform_session.flush()

    loaded_child = platform_session.get(
        PlatformRefreshToken,
        child.id,
    )

    assert loaded_child is not None
    assert loaded_child.parent is not None
    assert loaded_child.parent.id == parent.id

    assert any(
        item.id == child.id
        for item in parent.children
    )


def test_platform_login_attempt_is_platform_native(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    attempt = PlatformLoginAttempt(
        id=str(uuid4()),
        platform_user_id=user.id,
        email=user.email,
        ip_address="127.0.0.1",
        successful=True,
    )

    platform_session.add(attempt)
    platform_session.flush()

    loaded = platform_session.get(
        PlatformLoginAttempt,
        attempt.id,
    )

    assert loaded is not None

    assert loaded.platform_user_id == user.id
    assert loaded.platform_user.id == user.id
    assert loaded.successful is True

    assert (
        "tenant_id"
        not in PlatformLoginAttempt.__table__.columns
    )


def test_platform_refresh_token_has_no_tenant_scope():
    columns = (
        PlatformRefreshToken
        .__table__
        .columns
    )

    assert "tenant_id" not in columns
    assert "branch_id" not in columns
    assert "user_id" not in columns

    assert "platform_user_id" in columns

    assert (
        "platform_session_id"
        in columns
    )
