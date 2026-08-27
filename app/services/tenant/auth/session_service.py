"""
Session Service
===============

Enterprise authentication session lifecycle management for Hela360.

This service is the single authority responsible for persistence and lifecycle
operations involving authenticated user sessions.

Responsibilities
----------------
- Create authenticated sessions
- Resolve sessions
- Resolve active sessions
- Track session activity
- Revoke individual sessions
- Revoke all sessions belonging to a user
- Expire stale sessions
- Validate session state

Architectural Boundaries
------------------------
This service intentionally contains no:

- password verification logic
- JWT creation or decoding logic
- refresh-token persistence logic
- authorization policy evaluation

Those responsibilities belong respectively to:

- PasswordService / AuthenticationService
- JWTService
- RefreshTokenService
- AuthorizationService

A UserSession represents the authenticated device/client context.

Refresh tokens belong to a session. A session does not depend on a particular
refresh token because rotating refresh tokens may produce multiple token
records during the lifetime of one session.

Hela360 Enterprise Pharmacy POS & ERP
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select

from app.extensions import db
from app.models.security import (
    TokenRevocationReason,
    UserSession,
)


# =============================================================================
# Session Service
# =============================================================================


class SessionService:
    """
    Enterprise authentication session lifecycle manager.

    The service is stateless and may safely be reused throughout the
    application lifecycle.
    """

    # =========================================================================
    # Session Creation
    # =========================================================================

    def create(
        self,
        *,
        user_id: str,
        tenant_id: str,
        expires_at: datetime,
        device_name: str | None = None,
        browser: str | None = None,
        operating_system: str | None = None,
        device_fingerprint: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        country: str | None = None,
        city: str | None = None,
    ) -> UserSession:
        """
        Create a new authenticated user session.

        The session is created before JWT issuance so its identifier can be
        embedded into both access and refresh tokens.

        Refresh-token state is deliberately not stored on the session.
        RefreshTokenService owns refresh-token persistence and associates
        individual refresh-token records with this session through session_id.
        """

        now = datetime.now(UTC)

        session = UserSession(
            id=str(uuid4()),
            user_id=user_id,
            tenant_id=tenant_id,
            device_name=device_name,
            browser=browser,
            operating_system=operating_system,
            device_fingerprint=device_fingerprint,
            ip_address=ip_address,
            last_ip_address=ip_address,
            user_agent=user_agent,
            country=country,
            city=city,
            expires_at=expires_at,
            last_activity_at=now,
            revoked_at=None,
        )

        db.session.add(session)
        db.session.commit()

        return session

    # =========================================================================
    # Queries
    # =========================================================================

    def get(
        self,
        session_id: str,
    ) -> UserSession | None:
        """
        Retrieve a session by primary key.
        """

        return db.session.get(
            UserSession,
            session_id,
        )

    def get_active(
        self,
        session_id: str,
    ) -> UserSession | None:
        """
        Retrieve an active, non-revoked and non-expired session.
        """

        session = self.get(session_id)

        if session is None:
            return None

        if session.revoked_at is not None:
            return None

        if session.expires_at <= datetime.now(UTC):
            return None

        return session

    def get_user_sessions(
        self,
        *,
        user_id: str,
        tenant_id: str | None = None,
    ) -> list[UserSession]:
        """
        Return sessions belonging to a user.
        """

        stmt = (
            select(UserSession)
            .where(
                UserSession.user_id == user_id,
            )
            .order_by(
                UserSession.created_at.desc(),
            )
        )

        if tenant_id is not None:
            stmt = stmt.where(
                UserSession.tenant_id == tenant_id,
            )

        return list(
            db.session.scalars(stmt).all()
        )

    def get_active_user_sessions(
        self,
        *,
        user_id: str,
        tenant_id: str | None = None,
    ) -> list[UserSession]:
        """
        Return currently active sessions belonging to a user.
        """

        now = datetime.now(UTC)

        stmt = select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > now,
        )

        if tenant_id is not None:
            stmt = stmt.where(
                UserSession.tenant_id == tenant_id,
            )

        stmt = stmt.order_by(
            UserSession.created_at.desc(),
        )

        return list(
            db.session.scalars(stmt).all()
        )

    # =========================================================================
    # Session Activity
    # =========================================================================

    def touch(
        self,
        session: UserSession,
        *,
        ip_address: str | None = None,
    ) -> None:
        """
        Update session activity metadata.
        """

        session.last_activity_at = datetime.now(UTC)

        if ip_address is not None:
            session.last_ip_address = ip_address

        db.session.commit()

    # =========================================================================
    # Revocation
    # =========================================================================

    def revoke(
        self,
        session: UserSession,
        *,
        reason: TokenRevocationReason = TokenRevocationReason.LOGOUT,
        revoked_by_user_id: str | None = None,
        commit: bool = True,
    ) -> bool:
        """
        Revoke an authenticated session.

        Returns True when the session was newly revoked and False when it had
        already been revoked.

        ``commit=False`` allows a higher-level domain operation to include
        session revocation within a larger atomic transaction.
        """

        if session.revoked_at is not None:
            return False

        session.revoke(
            reason=reason,
            revoked_by_user_id=revoked_by_user_id,
        )

        if commit:
            db.session.commit()

        return True

    def revoke_user_sessions(
        self,
        *,
        user_id: str,
        tenant_id: str | None = None,
        reason: TokenRevocationReason = TokenRevocationReason.LOGOUT_ALL,
        revoked_by_user_id: str | None = None,
    ) -> int:
        """
        Revoke every active session belonging to a user.

        Returns the number of sessions newly revoked.
        """

        sessions = self.get_active_user_sessions(
            user_id=user_id,
            tenant_id=tenant_id,
        )

        if not sessions:
            return 0

        now = datetime.now(UTC)

        for session in sessions:
            session.revoked_at = now
            session.revoke_reason = reason
            session.revoked_by_user_id = revoked_by_user_id

        db.session.commit()

        return len(sessions)

    # =========================================================================
    # Expiration
    # =========================================================================

    def expire_stale_sessions(self) -> int:
        """
        Mark expired, non-revoked sessions as expired.

        Returns the number of sessions updated.
        """

        now = datetime.now(UTC)

        stmt = select(UserSession).where(
            UserSession.revoked_at.is_(None),
            UserSession.expires_at <= now,
        )

        sessions = list(
            db.session.scalars(stmt).all()
        )

        if not sessions:
            return 0

        for session in sessions:
            session.revoked_at = now
            session.revoke_reason = TokenRevocationReason.SESSION_EXPIRED

        db.session.commit()

        return len(sessions)

    # =========================================================================
    # Validation
    # =========================================================================

    def is_active(
        self,
        session: UserSession,
    ) -> bool:
        """
        Return True when a session is currently usable.
        """

        if session.revoked_at is not None:
            return False

        return session.expires_at > datetime.now(UTC)


# =============================================================================
# Singleton
# =============================================================================

session_service = SessionService()


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    "SessionService",
    "session_service",
]