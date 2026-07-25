"""
JWT Utilities for Hela360 Enterprise Authentication.

This module provides the low-level JWT functionality used throughout the
authentication subsystem.

Responsibilities
----------------
- Create signed access tokens
- Create signed refresh tokens
- Decode and validate JWTs
- Extract Bearer tokens from HTTP requests
- Resolve authenticated identities
- Provide strongly-typed access to JWT metadata

Design Principles
-----------------
- Stateless
- No database access
- No SQLAlchemy models
- No business logic
- No authentication workflows
- Configuration-driven
- Reusable across API, workers and CLI

Persistence of sessions, refresh-token rotation, revocation,
audit logging and authentication workflows belong in the
service layer.

Hela360 Enterprise Pharmacy POS & ERP
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any, Final
from uuid import uuid4

import jwt
from flask import current_app, request


# ============================================================================
# Type Aliases
# ============================================================================

JWTPayload = dict[str, Any]


# ============================================================================
# JWT Claim Names
# ============================================================================

class JWTClaims:
    """
    Standard JWT claim names used throughout Hela360.

    Centralising claim names eliminates duplicated string literals and
    provides a single source of truth for every JWT payload generated
    by the authentication subsystem.
    """

    SUBJECT: Final[str] = "sub"

    USER_ID: Final[str] = "user_id"
    TENANT_ID: Final[str] = "tenant_id"
    BRANCH_ID: Final[str] = "branch_id"

    ROLE: Final[str] = "role"
    PERMISSIONS: Final[str] = "permissions"

    SESSION_ID: Final[str] = "session_id"

    TYPE: Final[str] = "type"

    JWT_ID: Final[str] = "jti"

    ISSUER: Final[str] = "iss"
    AUDIENCE: Final[str] = "aud"

    ISSUED_AT: Final[str] = "iat"
    NOT_BEFORE: Final[str] = "nbf"
    EXPIRES_AT: Final[str] = "exp"


# ============================================================================
# JWT Token Types
# ============================================================================

class JWTTokenType(StrEnum):
    """
    Supported JWT token types.
    """

    ACCESS = "access"
    REFRESH = "refresh"


# ============================================================================
# Standard Claim Groups
# ============================================================================

ACCESS_CLAIMS: Final[tuple[str, ...]] = (
    JWTClaims.ROLE,
    JWTClaims.PERMISSIONS,
)

REQUIRED_CLAIMS: Final[tuple[str, ...]] = (
    JWTClaims.USER_ID,
    JWTClaims.TENANT_ID,
    JWTClaims.SESSION_ID,
    JWTClaims.TYPE,
    JWTClaims.JWT_ID,
    JWTClaims.ISSUED_AT,
    JWTClaims.EXPIRES_AT,
)


# ============================================================================
# JWT Configuration
# ============================================================================

@dataclass(slots=True, frozen=True)
class JWTConfig:
    """
    Runtime JWT configuration.

    Values are resolved from Flask configuration whenever tokens are
    created or validated.
    """

    secret: str
    algorithm: str
    issuer: str
    audience: str
    access_lifetime: timedelta
    refresh_lifetime: timedelta
    clock_skew: int


# ============================================================================
# Authenticated Identity
# ============================================================================

@dataclass(slots=True, frozen=True)
class Identity:
    """
    Authenticated identity extracted from a validated JWT.
    """

    user_id: str
    tenant_id: str
    branch_id: str | None

    role: str | None
    permissions: tuple[str, ...]

    session_id: str

    token_type: JWTTokenType

    jti: str


# ============================================================================
# Token Metadata
# ============================================================================

@dataclass(slots=True, frozen=True)
class TokenMetadata:
    """
    Frequently used metadata extracted from a JWT.

    Useful for authentication workflows that need to inspect a token
    without repeatedly accessing raw payload fields.
    """

    jti: str
    token_type: JWTTokenType

    issued_at: datetime
    not_before: datetime
    expires_at: datetime

    issuer: str
    audience: str

    user_id: str
    tenant_id: str
    session_id: str

# ============================================================================
# Configuration Helpers
# ============================================================================

def _config() -> JWTConfig:
    """
    Resolve the effective JWT configuration.

    JWT_SECRET_KEY is preferred over Flask's SECRET_KEY so the
    signing key can be rotated independently of other application
    secrets while remaining backwards compatible.
    """

    return JWTConfig(
        secret=current_app.config.get(
            "JWT_SECRET_KEY",
            current_app.config["SECRET_KEY"],
        ),
        algorithm=current_app.config.get(
            "JWT_ALGORITHM",
            "HS256",
        ),
        issuer=current_app.config.get(
            "JWT_ISSUER",
            "hela360",
        ),
        audience=current_app.config.get(
            "JWT_AUDIENCE",
            "hela360-api",
        ),
        access_lifetime=timedelta(
            minutes=current_app.config.get(
                "JWT_ACCESS_TOKEN_MINUTES",
                15,
            ),
        ),
        refresh_lifetime=timedelta(
            days=current_app.config.get(
                "JWT_REFRESH_TOKEN_DAYS",
                30,
            ),
        ),
        clock_skew=current_app.config.get(
            "JWT_CLOCK_SKEW_SECONDS",
            30,
        ),
    )


def _secret() -> str:
    """
    Return the JWT signing secret.
    """

    return _config().secret


def _algorithm() -> str:
    """
    Return the configured signing algorithm.
    """

    return _config().algorithm


def _issuer() -> str:
    """
    Return the configured JWT issuer.
    """

    return _config().issuer


def _audience() -> str:
    """
    Return the configured JWT audience.
    """

    return _config().audience


def _access_lifetime() -> timedelta:
    """
    Return the configured access-token lifetime.
    """

    return _config().access_lifetime


def _refresh_lifetime() -> timedelta:
    """
    Return the configured refresh-token lifetime.
    """

    return _config().refresh_lifetime


def _clock_skew() -> int:
    """
    Return the permitted JWT clock skew in seconds.
    """

    return _config().clock_skew


# ============================================================================
# Datetime Helpers
# ============================================================================

def _utc_now() -> datetime:
    """
    Return the current UTC timestamp.

    Centralising timestamp generation improves consistency and
    simplifies testing through monkey-patching.
    """

    return datetime.now(UTC)


def _to_datetime(value: datetime | int | float) -> datetime:
    """
    Convert a JWT timestamp into a timezone-aware UTC datetime.

    PyJWT may return datetime objects or Unix timestamps depending
    on configuration and version.
    """

    if isinstance(value, datetime):
        return value.astimezone(UTC)

    return datetime.fromtimestamp(value, tz=UTC)

# ============================================================================
# Internal Payload Helpers
# ============================================================================

def _build_payload(
    *,
    token_type: JWTTokenType,
    expires_in: timedelta,
    user_id: str,
    tenant_id: str,
    session_id: str,
    branch_id: str | None = None,
    role: str | None = None,
    permissions: list[str] | tuple[str, ...] | None = None,
) -> JWTPayload:
    """
    Build a canonical JWT payload.

    All JWTs issued by Hela360 are created through this function to
    guarantee a consistent claim set across the platform.

    Access tokens include authorization claims (role and permissions).
    Refresh tokens intentionally omit authorization information.
    """

    now = _utc_now()

    payload: JWTPayload = {
        JWTClaims.SUBJECT: user_id,
        JWTClaims.USER_ID: user_id,
        JWTClaims.TENANT_ID: tenant_id,
        JWTClaims.SESSION_ID: session_id,
        JWTClaims.TYPE: token_type.value,
        JWTClaims.JWT_ID: str(uuid4()),
        JWTClaims.ISSUED_AT: now,
        JWTClaims.NOT_BEFORE: now,
        JWTClaims.EXPIRES_AT: now + expires_in,
        JWTClaims.ISSUER: _issuer(),
        JWTClaims.AUDIENCE: _audience(),
    }

    if branch_id is not None:
        payload[JWTClaims.BRANCH_ID] = branch_id

    if role is not None:
        payload[JWTClaims.ROLE] = role

    if permissions:
        payload[JWTClaims.PERMISSIONS] = list(permissions)

    return payload


# ============================================================================
# Payload Validation Helpers
# ============================================================================

def has_required_claims(
    payload: JWTPayload,
) -> bool:
    """
    Return True if all mandatory claims are present.

    Cryptographic verification is handled by PyJWT. This helper
    validates the application's expected claim set.
    """

    return all(
        claim in payload
        for claim in REQUIRED_CLAIMS
    )


def require_claims(
    payload: JWTPayload,
) -> JWTPayload:
    """
    Validate that all required claims exist.

    Raises
    ------
    KeyError
        If one or more required claims are missing.
    """

    missing = [
        claim
        for claim in REQUIRED_CLAIMS
        if claim not in payload
    ]

    if missing:
        raise KeyError(
            "Missing JWT claims: "
            + ", ".join(missing)
        )

    return payload


def payload_metadata(
    payload: JWTPayload,
) -> TokenMetadata:
    """
    Convert a decoded JWT payload into strongly typed metadata.
    """

    require_claims(payload)

    return TokenMetadata(
        jti=payload[JWTClaims.JWT_ID],
        token_type=JWTTokenType(payload[JWTClaims.TYPE]),
        issued_at=_to_datetime(payload[JWTClaims.ISSUED_AT]),
        not_before=_to_datetime(payload[JWTClaims.NOT_BEFORE]),
        expires_at=_to_datetime(payload[JWTClaims.EXPIRES_AT]),
        issuer=payload[JWTClaims.ISSUER],
        audience=payload[JWTClaims.AUDIENCE],
        user_id=payload[JWTClaims.USER_ID],
        tenant_id=payload[JWTClaims.TENANT_ID],
        session_id=payload[JWTClaims.SESSION_ID],
    )    

# ============================================================================
# Token Creation
# ============================================================================

def create_access_token(
    *,
    user_id: str,
    tenant_id: str,
    branch_id: str | None,
    role: str | None,
    permissions: list[str],
    session_id: str,
) -> str:
    """
    Create and sign an access token.

    Access tokens carry the authenticated user's authorization
    context and are intended for short-lived API access.
    """

    payload = _build_payload(
        token_type=JWTTokenType.ACCESS,
        expires_in=_access_lifetime(),
        user_id=user_id,
        tenant_id=tenant_id,
        branch_id=branch_id,
        role=role,
        permissions=permissions,
        session_id=session_id,
    )

    return jwt.encode(
        payload,
        _secret(),
        algorithm=_algorithm(),
    )


def create_refresh_token(
    *,
    user_id: str,
    tenant_id: str,
    session_id: str,
) -> str:
    """
    Create and sign a refresh token.

    Refresh tokens intentionally contain only identity information
    required to issue new access tokens. Authorization claims are
    omitted to ensure fresh authorization is loaded from the database
    during token rotation.
    """

    payload = _build_payload(
        token_type=JWTTokenType.REFRESH,
        expires_in=_refresh_lifetime(),
        user_id=user_id,
        tenant_id=tenant_id,
        session_id=session_id,
    )

    return jwt.encode(
        payload,
        _secret(),
        algorithm=_algorithm(),
    )


# ============================================================================
# Token Validation
# ============================================================================

def decode_token(
    token: str,
) -> JWTPayload:
    """
    Decode and cryptographically validate a JWT.

    Validation performed by PyJWT includes:

    - Signature verification
    - Expiration (exp)
    - Not-before (nbf)
    - Issued-at (iat)
    - Issuer (iss)
    - Audience (aud)

    Returns
    -------
    JWTPayload
        Verified JWT payload.

    Raises
    ------
    jwt.PyJWTError
        If validation fails.
    """

    payload: JWTPayload = jwt.decode(
        token,
        _secret(),
        algorithms=[_algorithm()],
        issuer=_issuer(),
        audience=_audience(),
        leeway=_clock_skew(),
        options={
            "require": REQUIRED_CLAIMS,
        },
    )

    require_claims(payload)

    return payload

# ============================================================================
# JWT Metadata Helpers
# ============================================================================

def get_token_id(
    payload: JWTPayload,
) -> str:
    """
    Return the JWT ID (JTI).

    Parameters
    ----------
    payload:
        Decoded JWT payload.

    Returns
    -------
    str
        Globally unique JWT identifier.
    """

    return payload[JWTClaims.JWT_ID]


def get_token_type(
    payload: JWTPayload,
) -> JWTTokenType:
    """
    Return the JWT token type.

    Returns
    -------
    JWTTokenType
        ACCESS or REFRESH.
    """

    return JWTTokenType(
        payload[JWTClaims.TYPE]
    )


def get_token_expiry(
    payload: JWTPayload,
) -> datetime:
    """
    Return the token expiry timestamp.

    PyJWT may return ``exp`` as either a Unix timestamp or a
    timezone-aware datetime depending on configuration.

    Returns
    -------
    datetime
        UTC expiration timestamp.
    """

    return _to_datetime(
        payload[JWTClaims.EXPIRES_AT]
    )


def get_token_issued_at(
    payload: JWTPayload,
) -> datetime:
    """
    Return the token issued-at timestamp.
    """

    return _to_datetime(
        payload[JWTClaims.ISSUED_AT]
    )


def get_token_not_before(
    payload: JWTPayload,
) -> datetime:
    """
    Return the token not-before timestamp.
    """

    return _to_datetime(
        payload[JWTClaims.NOT_BEFORE]
    )


def get_user_id(
    payload: JWTPayload,
) -> str:
    """
    Return the authenticated user ID.
    """

    return payload[JWTClaims.USER_ID]


def get_tenant_id(
    payload: JWTPayload,
) -> str:
    """
    Return the tenant ID.
    """

    return payload[JWTClaims.TENANT_ID]


def get_branch_id(
    payload: JWTPayload,
) -> str | None:
    """
    Return the branch ID if present.
    """

    return payload.get(
        JWTClaims.BRANCH_ID
    )


def get_session_id(
    payload: JWTPayload,
) -> str:
    """
    Return the authentication session ID.
    """

    return payload[JWTClaims.SESSION_ID]


def get_role(
    payload: JWTPayload,
) -> str | None:
    """
    Return the user's role.
    """

    return payload.get(
        JWTClaims.ROLE
    )


def get_permissions(
    payload: JWTPayload,
) -> list[str]:
    """
    Return the permissions embedded in the access token.

    Refresh tokens intentionally return an empty list because
    they do not carry authorization data.
    """

    permissions = payload.get(
        JWTClaims.PERMISSIONS,
        [],
    )

    return list(permissions)


def get_identity(
    payload: JWTPayload,
) -> Identity:
    """
    Convert a validated JWT payload into a strongly typed
    authenticated identity object.

    Returns
    -------
    Identity
        Authenticated request identity.
    """

    require_claims(payload)

    return Identity(
        user_id=get_user_id(payload),
        tenant_id=get_tenant_id(payload),
        branch_id=get_branch_id(payload),
        role=get_role(payload),
        permissions=get_permissions(payload),
        session_id=get_session_id(payload),
        token_type=get_token_type(payload),
        jti=get_token_id(payload),
    )

# ============================================================================
# Bearer Token Extraction
# ============================================================================

def get_bearer_token() -> str | None:
    """
    Extract the Bearer token from the current HTTP request.

    Returns
    -------
    str | None
        JWT string if a valid Bearer Authorization header exists,
        otherwise None.

    Notes
    -----
    Expected format::

        Authorization: Bearer <jwt>
    """

    header = request.headers.get("Authorization")

    if not header:
        return None

    scheme, _, token = header.partition(" ")

    if scheme.lower() != "bearer":
        return None

    token = token.strip()

    return token or None


# ============================================================================
# Current Request Identity
# ============================================================================

def get_current_identity() -> Identity | None:
    """
    Resolve the authenticated identity for the current request.

    This helper performs the complete JWT authentication flow:

    1. Read the Authorization header.
    2. Extract the Bearer token.
    3. Decode and validate the JWT.
    4. Convert the payload into a strongly typed Identity.

    Returns
    -------
    Identity | None
        Authenticated identity, or None if authentication fails.

    Notes
    -----
    This helper never raises JWT exceptions. It is intentionally
    tolerant because it is frequently used by decorators and
    request middleware.
    """

    token = get_bearer_token()

    if token is None:
        return None

    try:
        payload = decode_token(token)

    except jwt.PyJWTError:
        return None

    return get_identity(payload)


# ============================================================================
# Token Type Utilities
# ============================================================================

def is_token_type(
    payload: JWTPayload,
    token_type: JWTTokenType,
) -> bool:
    """
    Return True if the JWT is of the specified type.
    """

    return (
        get_token_type(payload)
        is token_type
    )


def is_access_token(
    payload: JWTPayload,
) -> bool:
    """
    Return True if this is an access token.
    """

    return is_token_type(
        payload,
        JWTTokenType.ACCESS,
    )


def is_refresh_token(
    payload: JWTPayload,
) -> bool:
    """
    Return True if this is a refresh token.
    """

    return is_token_type(
        payload,
        JWTTokenType.REFRESH,
    )


# ============================================================================
# Lifetime Helpers
# ============================================================================

def access_token_expires_in() -> int:
    """
    Return the configured access-token lifetime.

    Returns
    -------
    int
        Lifetime in seconds.
    """

    return int(
        _access_lifetime().total_seconds()
    )


def refresh_token_expires_in() -> int:
    """
    Return the configured refresh-token lifetime.

    Returns
    -------
    int
        Lifetime in seconds.
    """

    return int(
        _refresh_lifetime().total_seconds()
    )

# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    # ------------------------------------------------------------------
    # Types
    # ------------------------------------------------------------------
    "JWTPayload",
    "JWTClaims",
    "JWTTokenType",
    "JWTConfig",
    "Identity",
    "TokenMetadata",

    # ------------------------------------------------------------------
    # Token Creation
    # ------------------------------------------------------------------
    "create_access_token",
    "create_refresh_token",

    # ------------------------------------------------------------------
    # Token Validation
    # ------------------------------------------------------------------
    "decode_token",

    # ------------------------------------------------------------------
    # Payload Validation
    # ------------------------------------------------------------------
    "has_required_claims",
    "require_claims",
    "payload_metadata",

    # ------------------------------------------------------------------
    # Metadata Helpers
    # ------------------------------------------------------------------
    "get_token_id",
    "get_token_type",
    "get_token_expiry",
    "get_token_issued_at",
    "get_token_not_before",

    # ------------------------------------------------------------------
    # Claim Helpers
    # ------------------------------------------------------------------
    "get_user_id",
    "get_tenant_id",
    "get_branch_id",
    "get_session_id",
    "get_role",
    "get_permissions",

    # ------------------------------------------------------------------
    # Identity Helpers
    # ------------------------------------------------------------------
    "get_identity",
    "get_current_identity",

    # ------------------------------------------------------------------
    # Bearer Helpers
    # ------------------------------------------------------------------
    "get_bearer_token",

    # ------------------------------------------------------------------
    # Token Type Helpers
    # ------------------------------------------------------------------
    "is_token_type",
    "is_access_token",
    "is_refresh_token",

    # ------------------------------------------------------------------
    # Lifetime Helpers
    # ------------------------------------------------------------------
    "access_token_expires_in",
    "refresh_token_expires_in",
]