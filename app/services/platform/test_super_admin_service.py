from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import create_app
from app.extensions import db
from app.models import (
    PlatformRole,
    PlatformUser,
    PlatformUserRole,
)
from app.services.platform.platform_permission_policy import (
    SYSTEM_PERMISSION,
)
from app.services.platform.super_admin_service import (
    SuperAdminProvisioningError,
    SuperAdminService,
)
from app.services.tenant.auth.password_service import (
    password_service,
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


def _provision(
    platform_session,
):
    return SuperAdminService(
        platform_session
    ).provision(
        email="ROOT@HELA360.INVALID",
        username="ROOT",
        first_name="Hela360",
        last_name="Administrator",
        password="PlatformRoot@12345",
    )


def test_provision_creates_platform_super_admin(
    platform_session,
):
    result = _provision(platform_session)

    assert result.user_created is True
    assert result.role_assigned is True
    assert result.email == "root@hela360.invalid"
    assert result.username == "root"

    user = platform_session.get(
        PlatformUser,
        result.platform_user_id,
    )

    assert user is not None
    assert user.is_active is True

    assert password_service.verify_password(
        "PlatformRoot@12345",
        user.password_hash,
    )

    assert not password_service.verify_password(
        "wrong-password",
        user.password_hash,
    )


def test_provision_assigns_canonical_super_admin_role(
    platform_session,
):
    result = _provision(platform_session)

    user = platform_session.get(
        PlatformUser,
        result.platform_user_id,
    )

    assert user is not None

    roles = {
        role.code
        for role in user.roles
    }

    assert "super_admin" in roles

    super_admin = platform_session.scalar(
        select(PlatformRole).where(
            PlatformRole.code == "super_admin"
        )
    )

    assert super_admin is not None

    assert {
        permission.code
        for permission in super_admin.permissions
    } == {
        SYSTEM_PERMISSION,
    }


def test_provision_is_idempotent(
    platform_session,
):
    first = _provision(platform_session)
    second = _provision(platform_session)

    assert first.user_created is True
    assert first.role_assigned is True

    assert second.user_created is False
    assert second.role_assigned is False

    users = platform_session.scalars(
        select(PlatformUser).where(
            PlatformUser.email
            == "root@hela360.invalid"
        )
    ).all()

    assert len(users) == 1

    assignments = platform_session.scalars(
        select(PlatformUserRole).where(
            PlatformUserRole.platform_user_id
            == first.platform_user_id
        )
    ).all()

    assert len(assignments) == 1


def test_existing_password_is_not_replaced(
    platform_session,
):
    first = _provision(platform_session)

    user = platform_session.get(
        PlatformUser,
        first.platform_user_id,
    )

    assert user is not None

    original_hash = user.password_hash

    SuperAdminService(
        platform_session
    ).provision(
        email="root@hela360.invalid",
        username="root",
        first_name="Changed",
        password="AnotherValid@12345",
    )

    assert user.password_hash == original_hash

    assert password_service.verify_password(
        "PlatformRoot@12345",
        user.password_hash,
    )


def test_email_collision_is_rejected(
    platform_session,
):
    existing = PlatformUser(
        email="root@hela360.invalid",
        username="someone-else",
        first_name="Existing",
        password_hash="test-hash",
        is_active=True,
    )

    platform_session.add(existing)
    platform_session.flush()

    with pytest.raises(
        SuperAdminProvisioningError,
        match="email is already assigned",
    ):
        _provision(platform_session)


def test_username_collision_is_rejected(
    platform_session,
):
    existing = PlatformUser(
        email="someone@example.invalid",
        username="root",
        first_name="Existing",
        password_hash="test-hash",
        is_active=True,
    )

    platform_session.add(existing)
    platform_session.flush()

    with pytest.raises(
        SuperAdminProvisioningError,
        match="username is already assigned",
    ):
        _provision(platform_session)


def test_invalid_password_is_rejected_for_new_user(
    platform_session,
):
    with pytest.raises(
        SuperAdminProvisioningError,
        match="password policy",
    ):
        SuperAdminService(
            platform_session
        ).provision(
            email="root@hela360.invalid",
            username="root",
            first_name="Hela360",
            password="weak",
        )


def test_super_admin_is_platform_native(
    platform_session,
):
    result = _provision(platform_session)

    user = platform_session.get(
        PlatformUser,
        result.platform_user_id,
    )

    assert user is not None

    assert (
        "tenant_id"
        not in user.__table__.columns
    )
