"""
Session Service

Enterprise session lifecycle management.

This service owns creation, lookup, revocation and expiration of user
authentication sessions.

Responsibilities
----------------
- Create login sessions
- Resolve active sessions
- Revoke sessions
- Revoke all sessions for a user
- Update last activity
- Check session validity

This service intentionally contains NO JWT logic and NO password
verification logic.

JWT issuance belongs to JWTService.
Authentication workflows belong to AuthenticationService.

Hela360 Enterprise Pharmacy POS & ERP
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import select

from app.extensions import db
from app.models.auth import AuthSession


class SessionService:
    """
    Enterprise authentication session service.
    """

    # ------------------------------------------------------------------
    # Session Creation
    # ------------------------------------------------------------------

    def create(
        self,
        *,
        user_id: str,
        tenant_id: str,
        refresh_token_jti: str,
        expires_at: datetime,
        device_name: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuthSession:
        """
        Create a new authenticated session.
        """

        session = AuthSession(
            id=str(uuid4()),
            user_id=user_id,
            tenant_id=tenant_id,
            refresh_token_jti=refresh_token_jti,
            device_name=device_name,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
            revoked_at=None,
            last_activity_at=datetime.now(UTC),
        )

        db.session.add(session)
        db.session.commit()

        return session

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get(
        self,
        session_id: str,
    ) -> AuthSession | None:
        """
        Retrieve a session by ID.
        """

        return db.session.get(
            AuthSession,
            session_id,
        )

    def get_active(
        self,
        session_id: str,
    ) -> AuthSession | None:
        """
        Return an active session.
        """

        session = self.get(session_id)

        if session is None:
            return None

        if self.is_revoked(session):
            return None

        if self.is_expired(session):
            return None

        return session

    def list_user_sessions(
        self,
        *,
        user_id: str,
    ) -> list[AuthSession]:
        """
        Return all sessions for a user.
        """

        stmt = (
            select(AuthSession)
            .where(AuthSession.user_id == user_id)
            .order_by(AuthSession.created_at.desc())
        )

        return list(db.session.scalars(stmt))

    # ------------------------------------------------------------------
    # Activity
    # ------------------------------------------------------------------

    def touch(
        self,
        session: AuthSession,
    ) -> None:
        """
        Update the last activity timestamp.
        """

        session.last_activity_at = datetime.now(UTC)

        db.session.commit()

    # ------------------------------------------------------------------
    # Revocation
    # ------------------------------------------------------------------

    def revoke(
        self,
        session: AuthSession,
    ) -> None:
        """
        Revoke a session.
        """

        if session.revoked_at is None:
            session.revoked_at = datetime.now(UTC)
            db.session.commit()

    def revoke_by_id(
        self,
        session_id: str,
    ) -> bool:
        """
        Revoke a session by ID.

        Returns
        -------
        bool
            True if revoked.
        """

        session = self.get(session_id)

        if session is None:
            return False

        self.revoke(session)

        return True

    def revoke_user_sessions(
        self,
        *,
        user_id: str,
    ) -> int:
        """
        Revoke every session belonging to a user.

        Returns
        -------
        int
            Number of sessions revoked.
        """

        now = datetime.now(UTC)

        stmt = (
            select(AuthSession)
            .where(
                AuthSession.user_id == user_id,
                AuthSession.revoked_at.is_(None),
            )
        )

        sessions = list(db.session.scalars(stmt))

        for session in sessions:
            session.revoked_at = now

        db.session.commit()

        return len(sessions)

    # ------------------------------------------------------------------
    # Expiry
    # ------------------------------------------------------------------

    def is_expired(
        self,
        session: AuthSession,
    ) -> bool:
        """
        Return True if the session has expired.
        """

        return session.expires_at <= datetime.now(UTC)

    def is_revoked(
        self,
        session: AuthSession,
    ) -> bool:
        """
        Return True if the session has been revoked.
        """

        return session.revoked_at is not None

    def is_active(
        self,
        session: AuthSession,
    ) -> bool:
        """
        Return True if the session is currently valid.
        """

        return (
            not self.is_revoked(session)
            and not self.is_expired(session)
        )

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    def delete_expired(
        self,
    ) -> int:
        """
        Permanently remove expired sessions.

        Returns
        -------
        int
            Number of deleted sessions.
        """

        stmt = (
            select(AuthSession)
            .where(AuthSession.expires_at < datetime.now(UTC))
        )

        sessions = list(db.session.scalars(stmt))

        count = len(sessions)

        for session in sessions:
            db.session.delete(session)

        db.session.commit()

        return count


session_service = SessionService()


__all__ = [
    "SessionService",
    "session_service",
]