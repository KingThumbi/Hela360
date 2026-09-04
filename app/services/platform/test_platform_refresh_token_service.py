from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app import create_app
from app.extensions import db
from app.models import (
    PlatformRefreshToken,
    PlatformSession,
    PlatformUser,
)
from app.models.security import (
    TokenRevocationReason,
)
from app.services.platform.platform_refresh_token_service import (
    PlatformRefreshTokenService,
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
        last_name="Refresh",
        email=(
            f"platform-refresh-{suffix}"
            "@example.invalid"
        ),
        username=(
            f"platform-refresh-{suffix}"
        ),
        password_hash="test-hash",
        is_active=True,
    )

    session.add(user)
    session.flush()

    return user


def create_platform_auth_session(
    session: Session,
    user: PlatformUser,
) -> PlatformSession:
    now = datetime.now(UTC)

    auth_session = PlatformSession(
        id=str(uuid4()),
        platform_user_id=user.id,
        expires_at=(
            now + timedelta(hours=8)
        ),
        last_activity_at=now,
    )

    session.add(auth_session)
    session.flush()

    return auth_session


def create_token(
    service: PlatformRefreshTokenService,
    user: PlatformUser,
    auth_session: PlatformSession,
    *,
    token_family: str | None = None,
) -> PlatformRefreshToken:
    return service.create(
        platform_user_id=user.id,
        platform_session_id=auth_session.id,
        jwt_id=str(uuid4()),
        expires_at=(
            datetime.now(UTC)
            + timedelta(days=7)
        ),
        token_family=token_family,
        ip_address="127.0.0.1",
        device_name="Test Device",
    )


def test_create_refresh_token(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    auth_session = (
        create_platform_auth_session(
            platform_session,
            user,
        )
    )

    service = (
        PlatformRefreshTokenService(
            platform_session
        )
    )

    token = create_token(
        service,
        user,
        auth_session,
    )

    assert token.id is not None
    assert token.jwt_id is not None
    assert token.token_family is not None

    assert token.platform_user_id == (
        user.id
    )

    assert token.platform_session_id == (
        auth_session.id
    )

    assert token.is_active is True


def test_create_rejects_expired_token(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    auth_session = (
        create_platform_auth_session(
            platform_session,
            user,
        )
    )

    service = PlatformRefreshTokenService(
        platform_session
    )

    with pytest.raises(
        ValueError,
        match="expiry must be in the future",
    ):
        service.create(
            platform_user_id=user.id,
            platform_session_id=(
                auth_session.id
            ),
            jwt_id=str(uuid4()),
            expires_at=(
                datetime.now(UTC)
                - timedelta(seconds=1)
            ),
        )


def test_get_by_jti_and_active_lookup(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    auth_session = (
        create_platform_auth_session(
            platform_session,
            user,
        )
    )

    service = PlatformRefreshTokenService(
        platform_session
    )

    token = create_token(
        service,
        user,
        auth_session,
    )

    assert service.get_by_jti(
        token.jwt_id
    ) is token

    assert service.get_active_by_jti(
        token.jwt_id
    ) is token

    assert service.get_by_jti(
        str(uuid4())
    ) is None


def test_mark_used_updates_metadata(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    auth_session = (
        create_platform_auth_session(
            platform_session,
            user,
        )
    )

    service = PlatformRefreshTokenService(
        platform_session
    )

    token = create_token(
        service,
        user,
        auth_session,
    )

    assert token.last_used_at is None

    service.mark_used(
        token,
        ip_address="127.0.0.2",
    )

    assert token.last_used_at is not None

    assert token.last_ip_address == (
        "127.0.0.2"
    )


def test_revoke_is_idempotent(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    auth_session = (
        create_platform_auth_session(
            platform_session,
            user,
        )
    )

    service = PlatformRefreshTokenService(
        platform_session
    )

    token = create_token(
        service,
        user,
        auth_session,
    )

    first = service.revoke(
        token,
        reason=(
            TokenRevocationReason.LOGOUT
        ),
    )

    revoked_at = token.revoked_at

    second = service.revoke(
        token,
        reason=(
            TokenRevocationReason
            .SECURITY_EVENT
        ),
    )

    assert first is True
    assert second is False

    assert token.revoked_at == revoked_at

    assert token.revoke_reason == (
        TokenRevocationReason.LOGOUT
    )


def test_rotation_preserves_family_and_lineage(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    auth_session = (
        create_platform_auth_session(
            platform_session,
            user,
        )
    )

    service = PlatformRefreshTokenService(
        platform_session
    )

    parent = create_token(
        service,
        user,
        auth_session,
    )

    child = service.rotate(
        old_token=parent,
        new_jwt_id=str(uuid4()),
        expires_at=(
            datetime.now(UTC)
            + timedelta(days=7)
        ),
        ip_address="127.0.0.2",
    )

    assert parent.is_rotated is True
    assert parent.revoked_at is not None

    assert parent.revoke_reason == (
        TokenRevocationReason
        .TOKEN_ROTATED
    )

    assert child.parent_token_id == (
        parent.id
    )

    assert child.token_family == (
        parent.token_family
    )

    assert child.platform_user_id == (
        parent.platform_user_id
    )

    assert child.platform_session_id == (
        parent.platform_session_id
    )

    assert child.is_active is True


def test_rotated_token_cannot_rotate_again(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    auth_session = (
        create_platform_auth_session(
            platform_session,
            user,
        )
    )

    service = PlatformRefreshTokenService(
        platform_session
    )

    parent = create_token(
        service,
        user,
        auth_session,
    )

    service.rotate(
        old_token=parent,
        new_jwt_id=str(uuid4()),
        expires_at=(
            datetime.now(UTC)
            + timedelta(days=7)
        ),
    )

    with pytest.raises(
        ValueError,
        match="already been revoked",
    ):
        service.rotate(
            old_token=parent,
            new_jwt_id=str(uuid4()),
            expires_at=(
                datetime.now(UTC)
                + timedelta(days=7)
            ),
        )


def test_reuse_revokes_active_descendant(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    auth_session = (
        create_platform_auth_session(
            platform_session,
            user,
        )
    )

    service = PlatformRefreshTokenService(
        platform_session
    )

    parent = create_token(
        service,
        user,
        auth_session,
    )

    child = service.rotate(
        old_token=parent,
        new_jwt_id=str(uuid4()),
        expires_at=(
            datetime.now(UTC)
            + timedelta(days=7)
        ),
    )

    count = service.handle_reuse(
        parent
    )

    assert count == 1

    assert parent.revoke_reason == (
        TokenRevocationReason
        .TOKEN_ROTATED
    )

    assert child.revoked_at is not None

    assert child.revoke_reason == (
        TokenRevocationReason
        .REUSE_DETECTED
    )


def test_revoke_session_tokens_is_scoped(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    first_session = (
        create_platform_auth_session(
            platform_session,
            user,
        )
    )

    second_session = (
        create_platform_auth_session(
            platform_session,
            user,
        )
    )

    service = PlatformRefreshTokenService(
        platform_session
    )

    first = create_token(
        service,
        user,
        first_session,
    )

    second = create_token(
        service,
        user,
        second_session,
    )

    count = service.revoke_session_tokens(
        platform_session_id=(
            first_session.id
        ),
    )

    assert count == 1
    assert first.revoked_at is not None
    assert second.revoked_at is None


def test_revoke_user_tokens_is_user_scoped(
    platform_session: Session,
):
    first_user = create_platform_user(
        platform_session
    )

    second_user = create_platform_user(
        platform_session
    )

    first_session = (
        create_platform_auth_session(
            platform_session,
            first_user,
        )
    )

    second_session = (
        create_platform_auth_session(
            platform_session,
            second_user,
        )
    )

    service = PlatformRefreshTokenService(
        platform_session
    )

    first = create_token(
        service,
        first_user,
        first_session,
    )

    second = create_token(
        service,
        second_user,
        second_session,
    )

    count = service.revoke_user_tokens(
        platform_user_id=first_user.id,
    )

    assert count == 1
    assert first.revoked_at is not None
    assert second.revoked_at is None


def test_platform_refresh_tokens_have_no_tenant_scope():
    columns = (
        PlatformRefreshToken
        .__table__
        .columns
    )

    assert "tenant_id" not in columns
    assert "branch_id" not in columns
    assert "user_id" not in columns

    assert "platform_user_id" in columns
    assert "platform_session_id" in columns
