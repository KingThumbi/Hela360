"""
JWT Authentication Contract Tests
=================================

Regression tests for Hela360's JWT authentication boundary.

Architectural guarantees
------------------------
- Access tokens carry authenticated identity and effective permissions.
- Access tokens do not manufacture a singular role from multi-role RBAC.
- Refresh tokens do not carry authorization claims.
- JWT Identity represents authenticated request identity, not tenant-role
  presentation.
"""

from __future__ import annotations

from flask import Flask

from app.auth.jwt import (
    JWTClaims,
    JWTTokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_identity,
    get_permissions,
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


def test_access_token_contains_permissions_but_no_singular_role() -> None:
    app = _app()

    with app.app_context():
        token = create_access_token(
            user_id="user-1",
            tenant_id="tenant-1",
            branch_id="branch-1",
            permissions=[
                "products.view",
                "sales.create",
            ],
            session_id="session-1",
        )

        payload = decode_token(token)

    assert payload[JWTClaims.USER_ID] == "user-1"
    assert payload[JWTClaims.TENANT_ID] == "tenant-1"
    assert payload[JWTClaims.BRANCH_ID] == "branch-1"
    assert payload[JWTClaims.SESSION_ID] == "session-1"

    assert payload[JWTClaims.PERMISSIONS] == [
        "products.view",
        "sales.create",
    ]

    # Hela360 supports multiple tenant roles. Token issuance must not invent
    # a "primary" role based on collection order.
    assert "role" not in payload


def test_access_token_identity_has_no_singular_role() -> None:
    app = _app()

    with app.app_context():
        token = create_access_token(
            user_id="user-1",
            tenant_id="tenant-1",
            branch_id=None,
            permissions=[
                "inventory.read",
                "reports.view",
            ],
            session_id="session-1",
        )

        payload = decode_token(token)
        identity = get_identity(payload)

    assert identity.user_id == "user-1"
    assert identity.tenant_id == "tenant-1"
    assert identity.branch_id is None
    assert identity.session_id == "session-1"
    assert identity.token_type is JWTTokenType.ACCESS

    assert identity.permissions == (
        "inventory.read",
        "reports.view",
    )

    assert not hasattr(identity, "role")


def test_refresh_token_contains_no_authorization_claims() -> None:
    app = _app()

    with app.app_context():
        token = create_refresh_token(
            user_id="user-1",
            tenant_id="tenant-1",
            session_id="session-1",
        )

        payload = decode_token(token)

    assert payload[JWTClaims.USER_ID] == "user-1"
    assert payload[JWTClaims.TENANT_ID] == "tenant-1"
    assert payload[JWTClaims.SESSION_ID] == "session-1"

    assert JWTClaims.PERMISSIONS not in payload
    assert "role" not in payload

    assert get_permissions(payload) == []


def test_role_is_not_part_of_jwt_claim_registry() -> None:
    """
    Prevent accidental reintroduction of the legacy singular JWT role claim.
    """

    assert not hasattr(JWTClaims, "ROLE")
