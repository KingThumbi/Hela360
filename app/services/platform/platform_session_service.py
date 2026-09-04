"""
Hela360 Platform Session Service
================================

Persistence and lifecycle orchestration for authenticated Hela360 Office
sessions.

Architectural boundaries
------------------------
* Operates only on PlatformSession records.
* Never reads or mutates tenant UserSession records.
* Carries no tenant or branch scope.
* Contains no password verification.
* Contains no JWT creation or decoding.
* Contains no refresh-token persistence.
* Contains no authorization policy evaluation.
* Never commits or rolls back implicitly.

Transaction ownership remains with the caller.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select

from app.models import PlatformSession
from app.models.security import TokenRevocationReason


class PlatformSessionService:
    """
    Manage Hela360 Office authentication sessions.

    The service mutates and flushes state but never commits or rolls back.
    """

    def __init__(self, session) -> None:
        self.session = session

    def create(
        self,
        *,
        platform_user_id: str,
        expires_at: datetime,
        device_name: str | None = None,
        browser: str | None = None,
        operating_system: str | None = None,
        device_fingerprint: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        country: str | None = None,
        city: str | None = None,
        authentication_method: str | None = None,
        authentication_level: str | None = None,
        mfa_verified_at: datetime | None = None,
    ) -> PlatformSession:
        """
        Create a platform authentication session.

        The session is normally created before token issuance so its identifier
        can later be embedded in platform access and refresh tokens.
        """

        now = datetime.now(UTC)

        if expires_at <= now:
            raise ValueError(
                "Platform session expiry must be in the future."
            )

        auth_session = PlatformSession(
            id=str(uuid4()),
            platform_user_id=platform_user_id,
            expires_at=expires_at,
            last_activity_at=now,
            device_name=device_name,
            browser=browser,
            operating_system=operating_system,
            device_fingerprint=device_fingerprint,
            ip_address=ip_address,
            last_ip_address=ip_address,
            user_agent=user_agent,
            country=country,
            city=city,
            authentication_method=authentication_method,
            authentication_level=authentication_level,
            mfa_verified_at=mfa_verified_at,
            revoked_at=None,
            revoked_by_platform_user_id=None,
            revoke_reason=None,
        )

        self.session.add(auth_session)
        self.session.flush()

        return auth_session

    def get(
        self,
        session_id: str,
    ) -> PlatformSession | None:
        """Return one platform session by primary key."""

        return self.session.get(
            PlatformSession,
            session_id,
        )

    def get_active(
        self,
        session_id: str,
    ) -> PlatformSession | None:
        """Return a platform session only when currently active."""

        auth_session = self.get(session_id)

        if auth_session is None:
            return None

        if not auth_session.is_active:
            return None

        return auth_session

    def list_user_sessions(
        self,
        *,
        platform_user_id: str,
    ) -> tuple[PlatformSession, ...]:
        """Return all sessions belonging to one PlatformUser."""

        sessions = self.session.scalars(
            select(PlatformSession)
            .where(
                PlatformSession.platform_user_id
                == platform_user_id
            )
            .order_by(
                PlatformSession.created_at.desc(),
                PlatformSession.id.asc(),
            )
        ).all()

        return tuple(sessions)

    def list_active_user_sessions(
        self,
        *,
        platform_user_id: str,
    ) -> tuple[PlatformSession, ...]:
        """Return active sessions belonging to one PlatformUser."""

        now = datetime.now(UTC)

        sessions = self.session.scalars(
            select(PlatformSession)
            .where(
                PlatformSession.platform_user_id
                == platform_user_id,
                PlatformSession.revoked_at.is_(None),
                PlatformSession.expires_at > now,
            )
            .order_by(
                PlatformSession.created_at.desc(),
                PlatformSession.id.asc(),
            )
        ).all()

        return tuple(sessions)

    def touch(
        self,
        auth_session: PlatformSession,
        *,
        ip_address: str | None = None,
    ) -> None:
        """Record authenticated activity for a platform session."""

        auth_session.touch(
            ip_address=ip_address
        )

        self.session.flush()

    def revoke(
        self,
        auth_session: PlatformSession,
        *,
        reason: TokenRevocationReason = (
            TokenRevocationReason.LOGOUT
        ),
        revoked_by_platform_user_id: str | None = None,
    ) -> bool:
        """
        Revoke one platform session.

        Returns True when newly revoked and False when already revoked.
        """

        if auth_session.revoked_at is not None:
            return False

        auth_session.revoke(
            reason=reason,
            revoked_by_platform_user_id=(
                revoked_by_platform_user_id
            ),
        )

        self.session.flush()

        return True

    def revoke_user_sessions(
        self,
        *,
        platform_user_id: str,
        reason: TokenRevocationReason = (
            TokenRevocationReason.LOGOUT_ALL
        ),
        revoked_by_platform_user_id: str | None = None,
    ) -> int:
        """Revoke every active session belonging to one PlatformUser."""

        sessions = self.list_active_user_sessions(
            platform_user_id=platform_user_id
        )

        if not sessions:
            return 0

        for auth_session in sessions:
            auth_session.revoke(
                reason=reason,
                revoked_by_platform_user_id=(
                    revoked_by_platform_user_id
                ),
            )

        self.session.flush()

        return len(sessions)

    def expire_stale_sessions(self) -> int:
        """
        Revoke sessions whose configured lifetime has elapsed.
        """

        now = datetime.now(UTC)

        stale_sessions = self.session.scalars(
            select(PlatformSession)
            .where(
                PlatformSession.revoked_at.is_(None),
                PlatformSession.expires_at <= now,
            )
            .order_by(
                PlatformSession.expires_at.asc(),
                PlatformSession.id.asc(),
            )
        ).all()

        if not stale_sessions:
            return 0

        for auth_session in stale_sessions:
            auth_session.revoke(
                reason=(
                    TokenRevocationReason.SESSION_EXPIRED
                )
            )

        self.session.flush()

        return len(stale_sessions)


__all__ = [
    "PlatformSessionService",
]
