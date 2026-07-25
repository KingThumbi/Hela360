"""
Refresh Token Service

Enterprise refresh token lifecycle management for Hela360.

This service is the single authority responsible for managing OAuth-style
refresh tokens issued to authenticated users.

Responsibilities
----------------
- Issue refresh tokens
- Persist token metadata
- Resolve active refresh tokens
- Validate token state
- Rotate refresh tokens
- Revoke individual tokens
- Revoke all tokens for a user
- Revoke all tokens for a session
- Cleanup expired tokens
- Support audit logging

Design Principles
-----------------
- Stateless JWT access tokens
- Stateful refresh tokens
- Rotation on every refresh
- Reuse detection support
- Database-backed revocation
- Multi-tenant isolation
- Enterprise security

This service intentionally DOES NOT:

- Authenticate users
- Verify passwords
- Create JWT access tokens

Those responsibilities belong respectively to:

- AuthenticationService
- PasswordService
- JWTService

Hela360 Enterprise Pharmacy POS & ERP
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Final
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models.security import RefreshToken
from app.services.common.audit_actions import AuditAction
from app.services.common.audit_service import audit_service


# ============================================================================
# Constants
# ============================================================================

ACTIVE_STATUS: Final[str] = "active"
REVOKED_STATUS: Final[str] = "revoked"
EXPIRED_STATUS: Final[str] = "expired"

SYSTEM_REVOCATION_REASON: Final[str] = "system"
USER_LOGOUT_REASON: Final[str] = "logout"
PASSWORD_CHANGE_REASON: Final[str] = "password_changed"
ADMIN_REVOCATION_REASON: Final[str] = "admin_revoked"
TOKEN_ROTATION_REASON: Final[str] = "rotated"
SECURITY_EVENT_REASON: Final[str] = "security_event"


# ============================================================================
# Refresh Token Service
# ============================================================================

class RefreshTokenService:
    """
    Enterprise refresh token lifecycle manager.

    This service owns every database operation involving RefreshToken
    entities and enforces the application's refresh token security policy.

    Features
    --------
    • Token persistence
    • Token lookup
    • Rotation support
    • Revocation
    • Expiry validation
    • Session-based management
    • User-wide logout
    • Audit integration
    • Cleanup utilities

    Notes
    -----
    Refresh token *values* are never stored.

    The JWT itself is validated by JWTService. This service only tracks
    metadata such as:

    - JTI
    - ownership
    - expiry
    - revocation state
    - rotation history
    - session association

    Thread Safety
    -------------
    Instances are stateless and may safely be reused throughout the
    application lifecycle.
    """

    def __init__(self) -> None:
        """Initialize the refresh token service."""
        super().__init__()

    # ========================================================================
    # Token Creation
    # ========================================================================

    def create(
        self,
        *,
        jti: str,
        user_id: str,
        tenant_id: str,
        session_id: str,
        expires_at: datetime,
        created_by_ip: str | None = None,
        user_agent: str | None = None,
    ) -> RefreshToken:
        """
        Persist a newly-issued refresh token.

        Parameters
        ----------
        jti:
            JWT ID embedded inside the refresh token.

        user_id:
            Owner of the token.

        tenant_id:
            Tenant that owns the user.

        session_id:
            Authentication session associated with this token.

        expires_at:
            UTC expiry timestamp.

        created_by_ip:
            Client IP address.

        user_agent:
            Browser or device information.

        Returns
        -------
        RefreshToken
            Newly-created database record.

        Raises
        ------
        SQLAlchemyError
            If persistence fails.
        """

        token = RefreshToken(
            id=str(uuid4()),
            jti=jti,
            user_id=user_id,
            tenant_id=tenant_id,
            session_id=session_id,
            expires_at=expires_at,
            created_by_ip=created_by_ip,
            user_agent=user_agent,
            revoked_at=None,
            revoked_reason=None,
            replaced_by_jti=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        db.session.add(token)
        db.session.commit()

        audit_service.safe_log(
            action=AuditAction.REFRESH_TOKEN_CREATED,
            entity_type="RefreshToken",
            entity_id=token.id,
            user_id=user_id,
            tenant_id=tenant_id,
            details={
                "session_id": session_id,
                "jti": jti,
                "expires_at": expires_at.isoformat(),
            },
        )

        return token

    # ------------------------------------------------------------------
    # Query Operations
    # ------------------------------------------------------------------

    def get(
        self,
        token_id: str,
    ) -> RefreshToken | None:
        """
        Retrieve a refresh token by its primary key.
        """

        return db.session.get(
            RefreshToken,
            token_id,
        )

    def get_by_jti(
        self,
        jti: str,
    ) -> RefreshToken | None:
        """
        Retrieve a refresh token using its JWT ID (JTI).

        Parameters
        ----------
        jti:
            JWT identifier embedded within the refresh token.
        """

        stmt = (
            select(RefreshToken)
            .where(RefreshToken.jti == jti)
            .limit(1)
        )

        return db.session.scalar(stmt)

    def get_active_by_jti(
        self,
        jti: str,
    ) -> RefreshToken | None:
        """
        Return an active refresh token.

        A token is active only if:

        • it exists
        • it has not expired
        • it has not been revoked
        """

        token = self.get_by_jti(jti)

        if token is None:
            return None

        if self.is_revoked(token):
            return None

        if self.is_expired(token):
            return None

        return token

    def list_user_tokens(
        self,
        *,
        user_id: str,
        include_revoked: bool = False,
    ) -> list[RefreshToken]:
        """
        Return refresh tokens belonging to a user.

        Parameters
        ----------
        user_id:
            User identifier.

        include_revoked:
            Include revoked tokens.
        """

        stmt = (
            select(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
            )
            .order_by(
                RefreshToken.created_at.desc(),
            )
        )

        if not include_revoked:
            stmt = stmt.where(
                RefreshToken.revoked_at.is_(None),
            )

        return list(db.session.scalars(stmt))

    def list_active_tokens(
        self,
        *,
        user_id: str,
    ) -> list[RefreshToken]:
        """
        Return active refresh tokens for a user.
        """

        now = datetime.now(UTC)

        stmt = (
            select(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > now,
            )
            .order_by(
                RefreshToken.created_at.desc(),
            )
        )

        return list(db.session.scalars(stmt))

    # ------------------------------------------------------------------
    # Revocation
    # ------------------------------------------------------------------

    def revoke(
        self,
        token: RefreshToken,
        *,
        revoked_by: str | None = None,
        reason: str | None = None,
    ) -> RefreshToken:
        """
        Revoke a refresh token.

        This operation is idempotent.
        """

        if token.is_revoked:
            return token

        token.revoke(
            revoked_by=revoked_by,
            reason=reason,
        )

        db.session.commit()

        return token

    def revoke_by_jti(
        self,
        jti: str,
        *,
        revoked_by: str | None = None,
        reason: str |None = None,
    ) -> bool:
        """
        Revoke a refresh token by JWT ID.

        Returns
        -------
        bool
            True if a token was revoked.
        """

        token = self.get_by_jti(jti)

        if token is None:
            return False

        self.revoke(
            token,
            revoked_by=revoked_by,
            reason=reason,
        )

        return True

    def revoke_family(
        self,
        family_id: str,
        *,
        revoked_by: str | None = None,
        reason: str | None = None,
    ) -> int:
        """
        Revoke every token belonging to a rotation family.

        Used when token reuse is detected.
        """

        stmt = (
            select(RefreshToken)
            .where(
                RefreshToken.family_id == family_id,
                RefreshToken.revoked_at.is_(None),
            )
        )

        tokens = list(db.session.scalars(stmt))

        for token in tokens:
            token.revoke(
                revoked_by=revoked_by,
                reason=reason,
            )

        db.session.commit()

        return len(tokens)

    def revoke_user_tokens(
        self,
        *,
        user_id: str,
        revoked_by: str | None = None,
        reason: str | None = None,
    ) -> int:
        """
        Revoke every active refresh token belonging to a user.

        Used for:

        • Logout all devices
        • Password reset
        • Administrative lockout
        """

        stmt = (
            select(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
        )

        tokens = list(db.session.scalars(stmt))

        for token in tokens:
            token.revoke(
                revoked_by=revoked_by,
                reason=reason,
            )

        db.session.commit()

        return len(tokens)

    # ------------------------------------------------------------------
    # Rotation
    # ------------------------------------------------------------------

    def rotate(
        self,
        *,
        old_token: RefreshToken,
        new_jti: str,
        expires_at: datetime,
        session_id: str | None = None,
        created_by_ip: str | None = None,
        created_by_user_agent: str | None = None,
    ) -> RefreshToken:
        """
        Rotate an existing refresh token.

        The previous token is revoked and replaced by a newly
        issued token belonging to the same token family.
        """

        self.revoke(
            old_token,
            reason="token_rotation",
        )

        return self.create(
            user_id=old_token.user_id,
            tenant_id=old_token.tenant_id,
            session_id=session_id or old_token.session_id,
            jti=new_jti,
            family_id=old_token.family_id,
            expires_at=expires_at,
            created_by_ip=created_by_ip,
            created_by_user_agent=created_by_user_agent,
        )

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    def delete_expired(self) -> int:
        """
        Permanently remove expired refresh tokens.

        Intended for scheduled maintenance jobs.
        """

        stmt = (
            select(RefreshToken)
            .where(
                RefreshToken.expires_at < datetime.now(UTC)
            )
        )

        tokens = list(db.session.scalars(stmt))

        count = len(tokens)

        for token in tokens:
            db.session.delete(token)

        db.session.commit()

        return count        
    
# ------------------------------------------------------------------
# Singleton
# ------------------------------------------------------------------

refresh_token_service = RefreshTokenService()


# ------------------------------------------------------------------
# Module Exports
# ------------------------------------------------------------------

__all__ = [
    "RefreshTokenService",
    "refresh_token_service",
]    