"""
JWT Service

Enterprise orchestration layer for JWT operations.

This service owns no persistence and performs no business logic.
It provides a clean abstraction over the application's JWT provider.

Responsibilities
----------------
- Issue access/refresh token pairs
- Decode and validate JWTs
- Verify token type
- Extract common JWT claims
- Expose configured token lifetimes

Persistence of sessions, refresh tokens, revocation and audit logging
belongs to the AuthenticationService and related persistence services.

Hela360 Enterprise Pharmacy POS & ERP
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Final, final

from app.auth.exceptions import (
    InvalidAccessTokenError,
    InvalidRefreshTokenError,
)
from app.auth.jwt import (
    access_token_expires_in,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_token_expiry,
    get_token_id,
    is_access_token,
    is_refresh_token,
    refresh_token_expires_in,
)
from app.auth.schemas import IssuedTokenPair

JWTPayload: Final = dict[str, Any]


@final
class JWTService:
    """
    Stateless enterprise JWT orchestration service.

    This class intentionally contains:

    - no database access
    - no SQLAlchemy models
    - no authentication workflow
    - no refresh-token persistence

    It exists solely to provide a stable interface over the JWT
    implementation used by Hela360.
    """

    # ------------------------------------------------------------------
    # Token Issuance
    # ------------------------------------------------------------------

    @staticmethod
    def issue_token_pair(
        *,
        user_id: str,
        tenant_id: str,
        branch_id: str | None,
        role: str | None,
        permissions: list[str],
        session_id: str,
    ) -> IssuedTokenPair:
        """
        Issue a new access/refresh token pair.
        """

        access_token = create_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            branch_id=branch_id,
            role=role,
            permissions=permissions,
            session_id=session_id,
        )

        refresh_token = create_refresh_token(
            user_id=user_id,
            tenant_id=tenant_id,
            session_id=session_id,
        )

        access_payload = decode_token(access_token)
        refresh_payload = decode_token(refresh_token)

        return IssuedTokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            access_jti=get_token_id(access_payload),
            refresh_jti=get_token_id(refresh_payload),
            access_expires_at=get_token_expiry(access_payload),
            refresh_expires_at=get_token_expiry(refresh_payload),
        )

    # ------------------------------------------------------------------
    # Decoding
    # ------------------------------------------------------------------

    @staticmethod
    def decode(token: str) -> JWTPayload:
        """
        Decode any valid JWT.
        """
        return decode_token(token)

    @staticmethod
    def _decode_expected(
        token: str,
        *,
        refresh: bool,
    ) -> JWTPayload:
        """
        Decode a token and verify its expected type.
        """

        payload = decode_token(token)

        if refresh:
            if not is_refresh_token(payload):
                raise InvalidRefreshTokenError()
        else:
            if not is_access_token(payload):
                raise InvalidAccessTokenError()

        return payload

    @classmethod
    def decode_access_token(
        cls,
        token: str,
    ) -> JWTPayload:
        """
        Decode and validate an access token.
        """

        return cls._decode_expected(
            token,
            refresh=False,
        )

    @classmethod
    def decode_refresh_token(
        cls,
        token: str,
    ) -> JWTPayload:
        """
        Decode and validate a refresh token.
        """

        return cls._decode_expected(
            token,
            refresh=True,
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @classmethod
    def validate_access_token(
        cls,
        token: str,
    ) -> bool:
        """
        Return True when the supplied access token is valid.
        """

        try:
            cls.decode_access_token(token)
            return True
        except Exception:
            return False

    @classmethod
    def validate_refresh_token(
        cls,
        token: str,
    ) -> bool:
        """
        Return True when the supplied refresh token is valid.
        """

        try:
            cls.decode_refresh_token(token)
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Claim Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def extract_claim(
        payload: JWTPayload,
        claim: str,
        default: Any = None,
    ) -> Any:
        """
        Return a claim from a decoded payload.
        """

        return payload.get(claim, default)

    @classmethod
    def extract_user_id(
        cls,
        payload: JWTPayload,
    ) -> str | None:
        return cls.extract_claim(payload, "sub")

    @classmethod
    def extract_session_id(
        cls,
        payload: JWTPayload,
    ) -> str | None:
        return cls.extract_claim(payload, "sid")

    @classmethod
    def extract_tenant_id(
        cls,
        payload: JWTPayload,
    ) -> str | None:
        return cls.extract_claim(payload, "tenant_id")

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    @staticmethod
    def token_id(payload: JWTPayload) -> str:
        """
        Return the JWT ID (JTI).
        """

        return get_token_id(payload)

    @staticmethod
    def token_expiry(payload: JWTPayload) -> datetime:
        """
        Return the expiry timestamp.
        """

        return get_token_expiry(payload)

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    @staticmethod
    def access_token_expires_in() -> int:
        """
        Access-token lifetime in seconds.
        """

        return access_token_expires_in()

    @staticmethod
    def refresh_token_expires_in() -> int:
        """
        Refresh-token lifetime in seconds.
        """

        return refresh_token_expires_in()


# ----------------------------------------------------------------------
# Shared Singleton
# ----------------------------------------------------------------------

jwt_service = JWTService()

__all__ = [
    "JWTService",
    "jwt_service",
]