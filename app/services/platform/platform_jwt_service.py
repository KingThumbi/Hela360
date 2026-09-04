"""
Hela360 Platform JWT Service
============================

Application-facing JWT abstraction for Hela360 Office.

This service owns no persistence and performs no login workflow.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Final, final

from app.auth.exceptions import (
    InvalidAccessTokenError,
    InvalidRefreshTokenError,
)
from app.auth.platform_jwt import (
    PlatformIdentity,
    PlatformJWTPayload,
    PlatformJWTClaims,
    PlatformJWTTokenType,
    create_platform_access_token,
    create_platform_refresh_token,
    decode_platform_token,
    get_platform_identity,
    platform_access_token_expires_in,
    platform_refresh_token_expires_in,
    platform_token_metadata,
)
from app.auth.schemas import IssuedTokenPair


PlatformPayload: Final = (
    PlatformJWTPayload
)


@final
class PlatformJWTService:
    """
    Stateless Hela360 Office JWT orchestration service.
    """

    @staticmethod
    def issue_access_token(
        *,
        platform_user_id: str,
        permissions: list[str],
        session_id: str,
    ) -> str:
        """Issue a signed platform access token."""

        return create_platform_access_token(
            platform_user_id=(
                platform_user_id
            ),
            permissions=permissions,
            session_id=session_id,
        )

    @staticmethod
    def issue_refresh_token(
        *,
        platform_user_id: str,
        session_id: str,
    ) -> str:
        """Issue a signed platform refresh token."""

        return create_platform_refresh_token(
            platform_user_id=(
                platform_user_id
            ),
            session_id=session_id,
        )

    @classmethod
    def issue_token_pair(
        cls,
        *,
        platform_user_id: str,
        permissions: list[str],
        session_id: str,
    ) -> IssuedTokenPair:
        """Issue a platform access/refresh token pair."""

        access_token = (
            cls.issue_access_token(
                platform_user_id=(
                    platform_user_id
                ),
                permissions=permissions,
                session_id=session_id,
            )
        )

        refresh_token = (
            cls.issue_refresh_token(
                platform_user_id=(
                    platform_user_id
                ),
                session_id=session_id,
            )
        )

        access_payload = (
            cls.decode_access_token(
                access_token
            )
        )

        refresh_payload = (
            cls.decode_refresh_token(
                refresh_token
            )
        )

        access_metadata = (
            platform_token_metadata(
                access_payload
            )
        )

        refresh_metadata = (
            platform_token_metadata(
                refresh_payload
            )
        )

        return IssuedTokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            access_jti=access_metadata.jti,
            refresh_jti=(
                refresh_metadata.jti
            ),
            access_expires_at=(
                access_metadata.expires_at
            ),
            refresh_expires_at=(
                refresh_metadata.expires_at
            ),
        )

    @staticmethod
    def decode(
        token: str,
    ) -> PlatformJWTPayload:
        """Decode any valid platform JWT."""

        return decode_platform_token(
            token
        )

    @staticmethod
    def _require_type(
        payload: PlatformJWTPayload,
        *,
        expected: PlatformJWTTokenType,
    ) -> PlatformJWTPayload:
        """Validate the expected platform token type."""

        if payload.get(
            PlatformJWTClaims.TYPE
        ) != expected.value:
            if (
                expected
                is PlatformJWTTokenType.ACCESS
            ):
                raise InvalidAccessTokenError()

            raise InvalidRefreshTokenError()

        return payload

    @classmethod
    def decode_access_token(
        cls,
        token: str,
    ) -> PlatformJWTPayload:
        """Decode and validate a platform access token."""

        payload = decode_platform_token(
            token
        )

        return cls._require_type(
            payload,
            expected=(
                PlatformJWTTokenType.ACCESS
            ),
        )

    @classmethod
    def decode_refresh_token(
        cls,
        token: str,
    ) -> PlatformJWTPayload:
        """Decode and validate a platform refresh token."""

        payload = decode_platform_token(
            token
        )

        return cls._require_type(
            payload,
            expected=(
                PlatformJWTTokenType.REFRESH
            ),
        )

    @classmethod
    def validate_access_token(
        cls,
        token: str,
    ) -> bool:
        try:
            cls.decode_access_token(
                token
            )
            return True

        except Exception:
            return False

    @classmethod
    def validate_refresh_token(
        cls,
        token: str,
    ) -> bool:
        try:
            cls.decode_refresh_token(
                token
            )
            return True

        except Exception:
            return False

    @staticmethod
    def extract_claim(
        payload: PlatformJWTPayload,
        claim: str,
        default: Any = None,
    ) -> Any:
        return payload.get(
            claim,
            default,
        )

    @staticmethod
    def extract_platform_user_id(
        payload: PlatformJWTPayload,
    ) -> str:
        return payload[
            PlatformJWTClaims
            .PLATFORM_USER_ID
        ]

    @staticmethod
    def extract_session_id(
        payload: PlatformJWTPayload,
    ) -> str:
        return payload[
            PlatformJWTClaims.SESSION_ID
        ]

    @staticmethod
    def extract_identity(
        payload: PlatformJWTPayload,
    ) -> PlatformIdentity:
        return get_platform_identity(
            payload
        )

    @staticmethod
    def token_id(
        payload: PlatformJWTPayload,
    ) -> str:
        return platform_token_metadata(
            payload
        ).jti

    @staticmethod
    def token_expiry(
        payload: PlatformJWTPayload,
    ) -> datetime:
        return platform_token_metadata(
            payload
        ).expires_at

    @staticmethod
    def access_token_expires_in() -> int:
        return (
            platform_access_token_expires_in()
        )

    @staticmethod
    def refresh_token_expires_in() -> int:
        return (
            platform_refresh_token_expires_in()
        )


platform_jwt_service = (
    PlatformJWTService()
)


__all__ = [
    "PlatformJWTService",
    "PlatformPayload",
    "platform_jwt_service",
]
