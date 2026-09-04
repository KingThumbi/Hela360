from __future__ import annotations

from flask import Flask
import pytest

from app.auth.exceptions import (
    InvalidAccessTokenError,
    InvalidRefreshTokenError,
)
from app.auth.platform_jwt import (
    PLATFORM_IDENTITY_TYPE,
    PlatformJWTClaims,
    PlatformJWTTokenType,
)
from app.services.platform.platform_jwt_service import (
    PlatformJWTService,
)


def _app() -> Flask:
    app = Flask(__name__)

    app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret-key",
        JWT_SECRET_KEY="test-jwt-secret-key",
        JWT_ALGORITHM="HS256",
        JWT_ISSUER="hela360-test",
        JWT_AUDIENCE="hela360-test-client",
        JWT_ACCESS_TOKEN_MINUTES=15,
        JWT_REFRESH_TOKEN_DAYS=7,
        JWT_CLOCK_SKEW_SECONDS=0,
    )

    return app


def test_platform_access_token_contract():
    app = _app()

    with app.app_context():
        token = (
            PlatformJWTService
            .issue_access_token(
                platform_user_id="platform-user-1",
                permissions=[
                    "platform.office.access",
                    "platform.catalogue.read",
                ],
                session_id="platform-session-1",
            )
        )

        payload = (
            PlatformJWTService
            .decode_access_token(token)
        )

    assert payload[
        PlatformJWTClaims
        .PLATFORM_USER_ID
    ] == "platform-user-1"

    assert payload[
        PlatformJWTClaims.SUBJECT
    ] == "platform-user-1"

    assert payload[
        PlatformJWTClaims
        .IDENTITY_TYPE
    ] == PLATFORM_IDENTITY_TYPE

    assert payload[
        PlatformJWTClaims.SESSION_ID
    ] == "platform-session-1"

    assert payload[
        PlatformJWTClaims.PERMISSIONS
    ] == [
        "platform.office.access",
        "platform.catalogue.read",
    ]

    assert "tenant_id" not in payload
    assert "branch_id" not in payload
    assert "user_id" not in payload


def test_platform_refresh_token_has_no_permissions():
    app = _app()

    with app.app_context():
        token = (
            PlatformJWTService
            .issue_refresh_token(
                platform_user_id="platform-user-1",
                session_id="platform-session-1",
            )
        )

        payload = (
            PlatformJWTService
            .decode_refresh_token(token)
        )

    assert (
        PlatformJWTClaims.PERMISSIONS
        not in payload
    )

    assert "tenant_id" not in payload
    assert "branch_id" not in payload
    assert "user_id" not in payload


def test_platform_identity_contract():
    app = _app()

    with app.app_context():
        token = (
            PlatformJWTService
            .issue_access_token(
                platform_user_id="platform-user-1",
                permissions=["*"],
                session_id="platform-session-1",
            )
        )

        payload = (
            PlatformJWTService
            .decode_access_token(token)
        )

        identity = (
            PlatformJWTService
            .extract_identity(payload)
        )

    assert identity.platform_user_id == (
        "platform-user-1"
    )

    assert identity.session_id == (
        "platform-session-1"
    )

    assert identity.permissions == ("*",)

    assert identity.token_type is (
        PlatformJWTTokenType.ACCESS
    )

    assert not hasattr(
        identity,
        "tenant_id",
    )

    assert not hasattr(
        identity,
        "branch_id",
    )

    assert not hasattr(
        identity,
        "user_id",
    )


def test_platform_token_pair_metadata():
    app = _app()

    with app.app_context():
        pair = (
            PlatformJWTService
            .issue_token_pair(
                platform_user_id="platform-user-1",
                permissions=["*"],
                session_id="platform-session-1",
            )
        )

        access_payload = (
            PlatformJWTService
            .decode_access_token(
                pair.access_token
            )
        )

        refresh_payload = (
            PlatformJWTService
            .decode_refresh_token(
                pair.refresh_token
            )
        )

        assert pair.access_jti == (
            PlatformJWTService.token_id(
                access_payload
            )
        )

        assert pair.refresh_jti == (
            PlatformJWTService.token_id(
                refresh_payload
            )
        )

        assert pair.access_expires_at == (
            PlatformJWTService.token_expiry(
                access_payload
            )
        )

        assert pair.refresh_expires_at == (
            PlatformJWTService.token_expiry(
                refresh_payload
            )
        )


def test_refresh_token_rejected_as_access_token():
    app = _app()

    with app.app_context():
        token = (
            PlatformJWTService
            .issue_refresh_token(
                platform_user_id="platform-user-1",
                session_id="platform-session-1",
            )
        )

        with pytest.raises(
            InvalidAccessTokenError
        ):
            PlatformJWTService.decode_access_token(
                token
            )


def test_access_token_rejected_as_refresh_token():
    app = _app()

    with app.app_context():
        token = (
            PlatformJWTService
            .issue_access_token(
                platform_user_id="platform-user-1",
                permissions=[],
                session_id="platform-session-1",
            )
        )

        with pytest.raises(
            InvalidRefreshTokenError
        ):
            PlatformJWTService.decode_refresh_token(
                token
            )


def test_platform_token_lifetimes():
    app = _app()

    with app.app_context():
        assert (
            PlatformJWTService
            .access_token_expires_in()
            == 15 * 60
        )

        assert (
            PlatformJWTService
            .refresh_token_expires_in()
            == 7 * 24 * 60 * 60
        )
