"""
JWT Service
===========

Enterprise orchestration layer for JSON Web Token operations.

This service is the single application-facing abstraction over the
low-level JWT provider implemented in ``app.auth.jwt``.

Responsibilities
----------------
- Issue access tokens
- Issue refresh tokens
- Issue access/refresh token pairs
- Decode and validate JWTs
- Verify token type
- Extract common JWT claims
- Expose token identifiers and expiry metadata
- Expose configured token lifetimes

Architectural Boundaries
------------------------
This service owns no persistence and performs no authentication workflow.

It does not:

- persist refresh tokens
- create or revoke authentication sessions
- rotate persisted refresh-token records
- evaluate authorization policy
- perform password verification
- perform audit logging

Persistence and authentication orchestration belong to
AuthenticationService, SessionService, and RefreshTokenService.

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
    get_session_id,
    get_tenant_id,
    get_token_expiry,
    get_token_id,
    get_user_id,
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

    JWTService provides a stable application-facing interface over the
    underlying JWT implementation.

    The service deliberately owns no database state.
    """

    # =====================================================================
    # Access Token Issuance
    # =====================================================================

    @staticmethod
    def issue_access_token(
        *,
        user_id: str,
        tenant_id: str,
        branch_id: str | None,
        permissions: list[str],
        session_id: str,
    ) -> str:
        """
        Issue a signed access token.

        Access tokens are stateless and therefore are not persisted.
        """

        return create_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            branch_id=branch_id,
            permissions=permissions,
            session_id=session_id,
        )

    # =====================================================================
    # Refresh Token Issuance
    # =====================================================================

    @staticmethod
    def issue_refresh_token(
        *,
        user_id: str,
        tenant_id: str,
        session_id: str,
    ) -> str:
        """
        Issue a signed refresh token.

        The caller is responsible for decoding the generated token metadata
        and persisting its JTI through RefreshTokenService.
        """

        return create_refresh_token(
            user_id=user_id,
            tenant_id=tenant_id,
            session_id=session_id,
        )

    # =====================================================================
    # Token Pair Issuance
    # =====================================================================

    @classmethod
    def issue_token_pair(
        cls,
        *,
        user_id: str,
        tenant_id: str,
        branch_id: str | None,
        permissions: list[str],
        session_id: str,
    ) -> IssuedTokenPair:
        """
        Issue an access/refresh token pair.

        The returned DTO contains the JWT strings together with the JTI and
        expiry metadata required by the authentication persistence layer.
        """

        access_token = cls.issue_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            branch_id=branch_id,
            permissions=permissions,
            session_id=session_id,
        )

        refresh_token = cls.issue_refresh_token(
            user_id=user_id,
            tenant_id=tenant_id,
            session_id=session_id,
        )

        access_payload = cls.decode_access_token(access_token)
        refresh_payload = cls.decode_refresh_token(refresh_token)

        return IssuedTokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            access_jti=cls.token_id(access_payload),
            refresh_jti=cls.token_id(refresh_payload),
            access_expires_at=cls.token_expiry(access_payload),
            refresh_expires_at=cls.token_expiry(refresh_payload),
        )

    # =====================================================================
    # Decoding
    # =====================================================================

    @staticmethod
    def decode(
        token: str,
    ) -> JWTPayload:
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
        Decode a JWT and verify that it has the expected token type.
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

    # =====================================================================
    # Validation
    # =====================================================================

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

    # =====================================================================
    # Claim Helpers
    # =====================================================================

    @staticmethod
    def extract_claim(
        payload: JWTPayload,
        claim: str,
        default: Any = None,
    ) -> Any:
        """
        Return a claim from a decoded JWT payload.
        """

        return payload.get(claim, default)

    @classmethod
    def extract_user_id(
        cls,
        payload: JWTPayload,
    ) -> str:
        """
        Return the authenticated user identifier from a JWT payload.

        Claim-name resolution is delegated to the canonical JWT layer.
        """

        return get_user_id(payload)

    @classmethod
    def extract_session_id(
        cls,
        payload: JWTPayload,
    ) -> str:
        """
        Return the authentication session identifier from a JWT payload.

        Claim-name resolution is delegated to the canonical JWT layer.
        """

        return get_session_id(payload)

    @classmethod
    def extract_tenant_id(
        cls,
        payload: JWTPayload,
    ) -> str:
        """
        Return the tenant identifier from a JWT payload.

        Claim-name resolution is delegated to the canonical JWT layer.
        """

        return get_tenant_id(payload)
    
    # =====================================================================
    # Token Metadata
    # =====================================================================

    @staticmethod
    def token_id(
        payload: JWTPayload,
    ) -> str:
        """
        Return the JWT identifier (JTI).
        """

        return get_token_id(payload)

    @staticmethod
    def token_expiry(
        payload: JWTPayload,
    ) -> datetime:
        """
        Return the JWT expiry timestamp.
        """

        return get_token_expiry(payload)

    # =====================================================================
    # Configuration
    # =====================================================================

    @staticmethod
    def access_token_expires_in() -> int:
        """
        Return the configured access-token lifetime in seconds.
        """

        return access_token_expires_in()

    @staticmethod
    def refresh_token_expires_in() -> int:
        """
        Return the configured refresh-token lifetime in seconds.
        """

        return refresh_token_expires_in()


# =========================================================================
# Shared Singleton
# =========================================================================

jwt_service = JWTService()


# =========================================================================
# Module Exports
# =========================================================================

__all__ = [
    "JWTService",
    "JWTPayload",
    "jwt_service",
]