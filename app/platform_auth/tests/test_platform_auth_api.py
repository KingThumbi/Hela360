from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import select

from app import create_app
from app.extensions import db
from app.models import (
    PlatformLoginAttempt,
    PlatformRole,
    PlatformUser,
    PlatformUserRole,
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
    "Hela360-Platform-API-Test-2026!"
)


@pytest.fixture()
def app():
    app = create_app()

    app.config.update(
        TESTING=True,
        JWT_SECRET_KEY=(
            "platform-api-test-secret-key-"
            "at-least-32-bytes-long"
        ),
        JWT_ACCESS_TOKEN_MINUTES=15,
        JWT_REFRESH_TOKEN_DAYS=7,
    )

    return app


@pytest.fixture()
def isolated_db(app):
    """
    Keep Platform authentication API tests isolated by explicit teardown.

    HTTP routes use the real Flask-SQLAlchemy scoped session and real commit
    behavior. After each test, only data belonging to the Platform API test
    domain is removed, followed by canonical Platform IAM rows when no
    non-test Platform users remain.

    This keeps request/session behavior production-realistic while preventing
    test state from leaking into subsequent suites.
    """

    yield

    with app.app_context():
        from sqlalchemy import delete

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

        test_user_ids = tuple(
            db.session.scalars(
                select(
                    PlatformUser.id
                ).where(
                    PlatformUser.email.like(
                        "platform-api-%@example.invalid"
                    )
                )
            ).all()
        )

        if test_user_ids:
            test_session_ids = tuple(
                db.session.scalars(
                    select(
                        PlatformSession.id
                    ).where(
                        PlatformSession.platform_user_id.in_(
                            test_user_ids
                        )
                    )
                ).all()
            )

            db.session.execute(
                delete(
                    PlatformRefreshToken
                ).where(
                    PlatformRefreshToken.platform_user_id.in_(
                        test_user_ids
                    )
                )
            )

            db.session.execute(
                delete(
                    PlatformLoginAttempt
                ).where(
                    PlatformLoginAttempt.platform_user_id.in_(
                        test_user_ids
                    )
                )
            )

            db.session.execute(
                delete(
                    PlatformUserRole
                ).where(
                    PlatformUserRole.platform_user_id.in_(
                        test_user_ids
                    )
                )
            )

            if test_session_ids:
                db.session.execute(
                    delete(
                        PlatformSession
                    ).where(
                        PlatformSession.id.in_(
                            test_session_ids
                        )
                    )
                )

            db.session.execute(
                delete(
                    PlatformUser
                ).where(
                    PlatformUser.id.in_(
                        test_user_ids
                    )
                )
            )

        non_test_users = db.session.scalar(
            select(
                PlatformUser.id
            ).where(
                ~PlatformUser.email.like(
                    "platform-api-%@example.invalid"
                )
            ).limit(1)
        )

        if non_test_users is None:
            db.session.execute(
                delete(
                    PlatformRolePermission
                )
            )

            db.session.execute(
                delete(
                    PlatformRole
                )
            )

            db.session.execute(
                delete(
                    PlatformPermission
                )
            )

        db.session.commit()
        db.session.remove()


@pytest.fixture()
def client(
    app,
    isolated_db,
):
    return app.test_client()


@pytest.fixture()
def platform_user(
    app,
    isolated_db,
):
    with app.app_context():
        PlatformPermissionCatalogueService(
            db.session
        ).synchronize()

        PlatformRoleProvisioningService(
            db.session
        ).synchronize()

        role = db.session.scalar(
            select(
                PlatformRole
            ).where(
                PlatformRole.code
                == OFFICE_ADMIN_ROLE.code
            )
        )

        assert role is not None

        suffix = uuid4().hex[:12]

        user = PlatformUser(
            id=str(uuid4()),
            first_name="Platform",
            last_name="API",
            email=(
                f"platform-api-{suffix}"
                "@example.invalid"
            ),
            username=(
                f"platform-api-{suffix}"
            ),
            password_hash=(
                password_service
                .hash_password(
                    TEST_PASSWORD
                )
            ),
            is_active=True,
        )

        db.session.add(user)
        db.session.flush()

        db.session.add(
            PlatformUserRole(
                platform_user_id=(
                    user.id
                ),
                platform_role_id=(
                    role.id
                ),
                assignment_reason=(
                    "Platform API test."
                ),
            )
        )

        db.session.commit()

        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
        }


def login(
    client,
    platform_user,
):
    response = client.post(
        "/api/platform-auth/login",
        json={
            "username_or_email": (
                platform_user[
                    "email"
                ]
            ),
            "password": (
                TEST_PASSWORD
            ),
        },
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["success"] is True

    return payload


def test_platform_login(
    client,
    platform_user,
):
    payload = login(
        client,
        platform_user,
    )

    assert payload["user"]["id"] == (
        platform_user["id"]
    )

    assert payload["access_token"]
    assert payload["refresh_token"]

    assert (
        "platform.office.access"
        in payload[
            "authorization"
        ][
            "permissions"
        ]
    )


def test_invalid_login_records_security_evidence(
    app,
    client,
    platform_user,
):
    response = client.post(
        "/api/platform-auth/login",
        json={
            "username_or_email": (
                platform_user[
                    "email"
                ]
            ),
            "password": (
                "wrong-password"
            ),
        },
    )

    assert response.status_code == 401

    with app.app_context():
        attempt = db.session.scalar(
            select(
                PlatformLoginAttempt
            )
            .where(
                PlatformLoginAttempt
                .platform_user_id
                == platform_user["id"],
                PlatformLoginAttempt
                .successful
                .is_(False),
            )
            .order_by(
                PlatformLoginAttempt
                .created_at
                .desc()
            )
        )

        assert attempt is not None

        assert (
            attempt.failure_reason
            == "Incorrect password"
        )


def test_platform_session_endpoint(
    client,
    platform_user,
):
    auth = login(
        client,
        platform_user,
    )

    response = client.get(
        "/api/platform-auth/session",
        headers={
            "Authorization": (
                "Bearer "
                + auth[
                    "access_token"
                ]
            ),
        },
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["success"] is True

    assert payload["user"]["id"] == (
        platform_user["id"]
    )


def test_platform_session_requires_token(
    client,
):
    response = client.get(
        "/api/platform-auth/session"
    )

    assert response.status_code == 401


def test_refresh_rotates_credentials(
    client,
    platform_user,
):
    auth = login(
        client,
        platform_user,
    )

    response = client.post(
        "/api/platform-auth/refresh",
        json={
            "refresh_token": (
                auth[
                    "refresh_token"
                ]
            ),
        },
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["success"] is True

    assert (
        payload["refresh_token"]
        != auth["refresh_token"]
    )

    assert (
        payload["access_token"]
        != auth["access_token"]
    )


def test_logout_invalidates_session(
    client,
    platform_user,
):
    auth = login(
        client,
        platform_user,
    )

    logout_response = client.post(
        "/api/platform-auth/logout",
        json={
            "refresh_token": (
                auth[
                    "refresh_token"
                ]
            ),
        },
    )

    assert (
        logout_response.status_code
        == 200
    )

    session_response = client.get(
        "/api/platform-auth/session",
        headers={
            "Authorization": (
                "Bearer "
                + auth[
                    "access_token"
                ]
            ),
        },
    )

    assert (
        session_response.status_code
        == 401
    )


def test_logout_all_uses_authenticated_platform_identity(
    client,
    platform_user,
):
    first = login(
        client,
        platform_user,
    )

    second = login(
        client,
        platform_user,
    )

    response = client.post(
        "/api/platform-auth/logout-all",
        headers={
            "Authorization": (
                "Bearer "
                + first[
                    "access_token"
                ]
            ),
        },
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["success"] is True

    for auth in (
        first,
        second,
    ):
        refresh_response = (
            client.post(
                "/api/platform-auth/refresh",
                json={
                    "refresh_token": (
                        auth[
                            "refresh_token"
                        ]
                    ),
                },
            )
        )

        assert (
            refresh_response
            .status_code
            == 401
        )


def test_tenant_auth_and_platform_auth_are_distinct(
    client,
    platform_user,
):
    auth = login(
        client,
        platform_user,
    )

    # A Platform access token must not establish tenant IAM identity.
    response = client.get(
        "/api/office/catalogue/master-items",
        headers={
            "Authorization": (
                "Bearer "
                + auth[
                    "access_token"
                ]
            ),
        },
    )

    # The legacy Office catalogue boundary is still tenant-platform-admin
    # based. It will be migrated separately.
    assert response.status_code in (
        401,
        403,
    )
