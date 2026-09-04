from __future__ import annotations

from datetime import (
    UTC,
    datetime,
    timedelta,
)
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app import create_app
from app.extensions import db
from app.models import (
    PlatformLoginAttempt,
    PlatformUser,
)
from app.services.platform.platform_login_attempt_service import (
    PlatformLoginAttemptService,
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
        last_name="Login",
        email=(
            f"platform-login-{suffix}"
            "@example.invalid"
        ),
        username=(
            f"platform-login-{suffix}"
        ),
        password_hash="test-hash",
        is_active=True,
    )

    session.add(user)
    session.flush()

    return user


def test_record_failure(
    platform_session: Session,
):
    service = (
        PlatformLoginAttemptService(
            platform_session
        )
    )

    attempt = service.record_failure(
        identifier=" USER@Example.COM ",
        ip_address="127.0.0.1",
        failure_reason=(
            "Incorrect password"
        ),
    )

    assert attempt.email == (
        "user@example.com"
    )

    assert attempt.successful is False

    assert attempt.failure_reason == (
        "Incorrect password"
    )


def test_record_success_links_platform_user(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    service = (
        PlatformLoginAttemptService(
            platform_session
        )
    )

    attempt = service.record_success(
        identifier=user.email,
        platform_user_id=user.id,
        ip_address="127.0.0.1",
    )

    assert attempt.successful is True

    assert attempt.platform_user_id == (
        user.id
    )

    assert attempt.failure_reason is None


def test_failure_count_tracks_recent_failures(
    platform_session: Session,
):
    service = (
        PlatformLoginAttemptService(
            platform_session
        )
    )

    for _ in range(3):
        service.record_failure(
            identifier="office@example.com",
        )

    assert service.failure_count(
        identifier="office@example.com"
    ) == 3


def test_success_logically_resets_failure_count_without_deleting_history(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    service = (
        PlatformLoginAttemptService(
            platform_session
        )
    )

    service.record_failure(
        identifier=user.email,
        platform_user_id=user.id,
    )

    service.record_failure(
        identifier=user.email,
        platform_user_id=user.id,
    )

    assert service.failure_count(
        identifier=user.email
    ) == 2

    service.record_success(
        identifier=user.email,
        platform_user_id=user.id,
    )

    assert service.failure_count(
        identifier=user.email
    ) == 0

    attempts = service.recent_attempts(
        identifier=user.email
    )

    assert len(attempts) == 3

    assert sum(
        not attempt.successful
        for attempt in attempts
    ) == 2


def test_account_lockout_threshold(
    platform_session: Session,
):
    service = (
        PlatformLoginAttemptService(
            platform_session,
            max_failed_attempts=3,
        )
    )

    for _ in range(3):
        service.record_failure(
            identifier="office@example.com",
        )

    assert service.is_account_locked(
        identifier="office@example.com"
    )

    assert not service.can_attempt(
        identifier="office@example.com"
    )


def test_ip_lockout_threshold(
    platform_session: Session,
):
    service = (
        PlatformLoginAttemptService(
            platform_session,
            max_ip_failures=2,
        )
    )

    service.record_failure(
        identifier="one@example.com",
        ip_address="127.0.0.9",
    )

    service.record_failure(
        identifier="two@example.com",
        ip_address="127.0.0.9",
    )

    assert service.is_ip_locked(
        ip_address="127.0.0.9"
    )

    assert not service.can_attempt(
        identifier="three@example.com",
        ip_address="127.0.0.9",
    )


def test_no_ip_address_does_not_trigger_ip_lock(
    platform_session: Session,
):
    service = (
        PlatformLoginAttemptService(
            platform_session,
            max_ip_failures=1,
        )
    )

    assert service.ip_failure_count(
        ip_address=None
    ) == 0

    assert not service.is_ip_locked(
        ip_address=None
    )


def test_remaining_attempts(
    platform_session: Session,
):
    service = (
        PlatformLoginAttemptService(
            platform_session,
            max_failed_attempts=5,
        )
    )

    service.record_failure(
        identifier="office@example.com",
    )

    service.record_failure(
        identifier="office@example.com",
    )

    assert service.remaining_attempts(
        identifier="office@example.com"
    ) == 3


def test_records_have_no_tenant_scope():
    columns = (
        PlatformLoginAttempt
        .__table__
        .columns
    )

    assert "tenant_id" not in columns
    assert "branch_id" not in columns
    assert "user_id" not in columns

    assert "platform_user_id" in columns


def test_service_does_not_delete_failures_on_success(
    platform_session: Session,
):
    user = create_platform_user(
        platform_session
    )

    service = (
        PlatformLoginAttemptService(
            platform_session
        )
    )

    failure = service.record_failure(
        identifier=user.email,
        platform_user_id=user.id,
    )

    service.record_success(
        identifier=user.email,
        platform_user_id=user.id,
    )

    persisted = platform_session.get(
        PlatformLoginAttempt,
        failure.id,
    )

    assert persisted is not None

    assert persisted.successful is False
