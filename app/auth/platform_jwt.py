"""
Hela360 Platform JWT Utilities
==============================

Low-level JWT primitives for Hela360 Office authentication.

Architectural boundaries
------------------------
* Platform identities are distinct from tenant identities.
* Platform tokens never carry tenant_id or branch_id.
* Platform tokens never masquerade as tenant User identities.
* Access tokens may carry effective platform permissions.
* Refresh tokens never carry authorization claims.
* No persistence, database access, or authentication workflow.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any, Final
from uuid import uuid4

import jwt
from flask import current_app

from app.auth.exceptions import (
    ExpiredTokenError,
    InvalidTokenError,
)


PlatformJWTPayload = dict[str, Any]


class PlatformJWTClaims:
    """Canonical Hela360 Office JWT claim names."""

    SUBJECT: Final[str] = "sub"

    PLATFORM_USER_ID: Final[str] = (
        "platform_user_id"
    )

    IDENTITY_TYPE: Final[str] = (
        "identity_type"
    )

    PERMISSIONS: Final[str] = (
        "permissions"
    )

    SESSION_ID: Final[str] = (
        "session_id"
    )

    TYPE: Final[str] = "type"
    JWT_ID: Final[str] = "jti"

    ISSUER: Final[str] = "iss"
    AUDIENCE: Final[str] = "aud"

    ISSUED_AT: Final[str] = "iat"
    NOT_BEFORE: Final[str] = "nbf"
    EXPIRES_AT: Final[str] = "exp"


class PlatformJWTTokenType(StrEnum):
    """Supported Hela360 Office JWT token types."""

    ACCESS = "access"
    REFRESH = "refresh"


PLATFORM_IDENTITY_TYPE: Final[str] = (
    "platform"
)


PLATFORM_REQUIRED_CLAIMS: Final[
    tuple[str, ...]
] = (
    PlatformJWTClaims.SUBJECT,
    PlatformJWTClaims.PLATFORM_USER_ID,
    PlatformJWTClaims.IDENTITY_TYPE,
    PlatformJWTClaims.SESSION_ID,
    PlatformJWTClaims.TYPE,
    PlatformJWTClaims.JWT_ID,
    PlatformJWTClaims.ISSUED_AT,
    PlatformJWTClaims.NOT_BEFORE,
    PlatformJWTClaims.EXPIRES_AT,
    PlatformJWTClaims.ISSUER,
    PlatformJWTClaims.AUDIENCE,
)


@dataclass(
    slots=True,
    frozen=True,
)
class PlatformJWTConfig:
    """Runtime JWT configuration for Hela360 Office."""

    secret: str
    algorithm: str
    issuer: str
    audience: str
    access_lifetime: timedelta
    refresh_lifetime: timedelta
    clock_skew: int


@dataclass(
    slots=True,
    frozen=True,
)
class PlatformIdentity:
    """Authenticated Hela360 Office identity."""

    platform_user_id: str
    permissions: tuple[str, ...]
    session_id: str
    token_type: PlatformJWTTokenType
    jti: str


@dataclass(
    slots=True,
    frozen=True,
)
class PlatformTokenMetadata:
    """Frequently used metadata from a platform JWT."""

    jti: str
    token_type: PlatformJWTTokenType

    issued_at: datetime
    not_before: datetime
    expires_at: datetime

    issuer: str
    audience: str

    platform_user_id: str
    session_id: str


def _config() -> PlatformJWTConfig:
    """Resolve effective platform JWT configuration."""

    return PlatformJWTConfig(
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
            )
        ),
        refresh_lifetime=timedelta(
            days=current_app.config.get(
                "JWT_REFRESH_TOKEN_DAYS",
                30,
            )
        ),
        clock_skew=current_app.config.get(
            "JWT_CLOCK_SKEW_SECONDS",
            30,
        ),
    )


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _to_datetime(
    value: datetime | int | float,
) -> datetime:
    if isinstance(
        value,
        datetime,
    ):
        if value.tzinfo is None:
            return value.replace(
                tzinfo=UTC
            )

        return value.astimezone(
            UTC
        )

    return datetime.fromtimestamp(
        value,
        tz=UTC,
    )


def _build_payload(
    *,
    token_type: PlatformJWTTokenType,
    expires_in: timedelta,
    platform_user_id: str,
    session_id: str,
    permissions: list[str]
    | tuple[str, ...]
    | None = None,
) -> PlatformJWTPayload:
    """
    Build a canonical Hela360 Office JWT payload.
    """

    now = _utc_now()
    config = _config()

    payload: PlatformJWTPayload = {
        PlatformJWTClaims.SUBJECT: (
            platform_user_id
        ),
        PlatformJWTClaims.PLATFORM_USER_ID: (
            platform_user_id
        ),
        PlatformJWTClaims.IDENTITY_TYPE: (
            PLATFORM_IDENTITY_TYPE
        ),
        PlatformJWTClaims.SESSION_ID: (
            session_id
        ),
        PlatformJWTClaims.TYPE: (
            token_type.value
        ),
        PlatformJWTClaims.JWT_ID: (
            str(uuid4())
        ),
        PlatformJWTClaims.ISSUED_AT: now,
        PlatformJWTClaims.NOT_BEFORE: now,
        PlatformJWTClaims.EXPIRES_AT: (
            now + expires_in
        ),
        PlatformJWTClaims.ISSUER: (
            config.issuer
        ),
        PlatformJWTClaims.AUDIENCE: (
            config.audience
        ),
    }

    if permissions:
        payload[
            PlatformJWTClaims.PERMISSIONS
        ] = list(permissions)

    return payload


def require_platform_claims(
    payload: PlatformJWTPayload,
) -> PlatformJWTPayload:
    """Require the canonical platform claim set."""

    missing = [
        claim
        for claim
        in PLATFORM_REQUIRED_CLAIMS
        if claim not in payload
    ]

    if missing:
        raise InvalidTokenError(
            "Missing platform JWT claims: "
            + ", ".join(missing)
        )

    if (
        payload[
            PlatformJWTClaims
            .IDENTITY_TYPE
        ]
        != PLATFORM_IDENTITY_TYPE
    ):
        raise InvalidTokenError(
            "JWT is not a platform identity."
        )

    subject = payload[
        PlatformJWTClaims.SUBJECT
    ]

    platform_user_id = payload[
        PlatformJWTClaims
        .PLATFORM_USER_ID
    ]

    if subject != platform_user_id:
        raise InvalidTokenError(
            "Platform JWT subject mismatch."
        )

    return payload


def create_platform_access_token(
    *,
    platform_user_id: str,
    permissions: list[str],
    session_id: str,
) -> str:
    """Create and sign a platform access token."""

    config = _config()

    payload = _build_payload(
        token_type=(
            PlatformJWTTokenType.ACCESS
        ),
        expires_in=config.access_lifetime,
        platform_user_id=platform_user_id,
        permissions=permissions,
        session_id=session_id,
    )

    return jwt.encode(
        payload,
        config.secret,
        algorithm=config.algorithm,
    )


def create_platform_refresh_token(
    *,
    platform_user_id: str,
    session_id: str,
) -> str:
    """
    Create and sign a platform refresh token.

    Authorization claims are deliberately excluded.
    """

    config = _config()

    payload = _build_payload(
        token_type=(
            PlatformJWTTokenType.REFRESH
        ),
        expires_in=config.refresh_lifetime,
        platform_user_id=platform_user_id,
        session_id=session_id,
    )

    return jwt.encode(
        payload,
        config.secret,
        algorithm=config.algorithm,
    )


def decode_platform_token(
    token: str,
) -> PlatformJWTPayload:
    """Decode and cryptographically validate a platform JWT."""

    config = _config()

    try:
        payload = jwt.decode(
            token,
            config.secret,
            algorithms=[
                config.algorithm
            ],
            issuer=config.issuer,
            audience=config.audience,
            leeway=config.clock_skew,
            options={
                "require": list(
                    PLATFORM_REQUIRED_CLAIMS
                ),
            },
        )

    except jwt.ExpiredSignatureError as exc:
        raise ExpiredTokenError() from exc

    except jwt.PyJWTError as exc:
        raise InvalidTokenError() from exc

    return require_platform_claims(
        payload
    )


def get_platform_permissions(
    payload: PlatformJWTPayload,
) -> tuple[str, ...]:
    """Return effective platform permissions."""

    permissions = payload.get(
        PlatformJWTClaims.PERMISSIONS,
        (),
    )

    return tuple(
        str(permission)
        for permission in permissions
    )


def get_platform_identity(
    payload: PlatformJWTPayload,
) -> PlatformIdentity:
    """Build a strongly typed platform identity."""

    require_platform_claims(
        payload
    )

    try:
        token_type = PlatformJWTTokenType(
            payload[
                PlatformJWTClaims.TYPE
            ]
        )
    except ValueError as exc:
        raise InvalidTokenError(
            "Invalid platform JWT token type."
        ) from exc

    return PlatformIdentity(
        platform_user_id=payload[
            PlatformJWTClaims
            .PLATFORM_USER_ID
        ],
        permissions=(
            get_platform_permissions(
                payload
            )
        ),
        session_id=payload[
            PlatformJWTClaims.SESSION_ID
        ],
        token_type=token_type,
        jti=payload[
            PlatformJWTClaims.JWT_ID
        ],
    )


def platform_token_metadata(
    payload: PlatformJWTPayload,
) -> PlatformTokenMetadata:
    """Extract strongly typed platform JWT metadata."""

    require_platform_claims(
        payload
    )

    try:
        token_type = PlatformJWTTokenType(
            payload[
                PlatformJWTClaims.TYPE
            ]
        )
    except ValueError as exc:
        raise InvalidTokenError(
            "Invalid platform JWT token type."
        ) from exc

    return PlatformTokenMetadata(
        jti=payload[
            PlatformJWTClaims.JWT_ID
        ],
        token_type=token_type,
        issued_at=_to_datetime(
            payload[
                PlatformJWTClaims.ISSUED_AT
            ]
        ),
        not_before=_to_datetime(
            payload[
                PlatformJWTClaims.NOT_BEFORE
            ]
        ),
        expires_at=_to_datetime(
            payload[
                PlatformJWTClaims.EXPIRES_AT
            ]
        ),
        issuer=payload[
            PlatformJWTClaims.ISSUER
        ],
        audience=payload[
            PlatformJWTClaims.AUDIENCE
        ],
        platform_user_id=payload[
            PlatformJWTClaims
            .PLATFORM_USER_ID
        ],
        session_id=payload[
            PlatformJWTClaims.SESSION_ID
        ],
    )


def platform_access_token_expires_in() -> int:
    """Return configured access-token lifetime in seconds."""

    return int(
        _config()
        .access_lifetime
        .total_seconds()
    )


def platform_refresh_token_expires_in() -> int:
    """Return configured refresh-token lifetime in seconds."""

    return int(
        _config()
        .refresh_lifetime
        .total_seconds()
    )


__all__ = [
    "PLATFORM_IDENTITY_TYPE",
    "PLATFORM_REQUIRED_CLAIMS",
    "PlatformIdentity",
    "PlatformJWTClaims",
    "PlatformJWTConfig",
    "PlatformJWTPayload",
    "PlatformJWTTokenType",
    "PlatformTokenMetadata",
    "create_platform_access_token",
    "create_platform_refresh_token",
    "decode_platform_token",
    "get_platform_identity",
    "get_platform_permissions",
    "platform_access_token_expires_in",
    "platform_refresh_token_expires_in",
    "platform_token_metadata",
    "require_platform_claims",
]
