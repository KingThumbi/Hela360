"""
Hela360 Platform Refresh Token Service
======================================

Persistence and lifecycle orchestration for Hela360 Office refresh tokens.

Architectural boundaries
------------------------
* Operates only on PlatformRefreshToken records.
* Never touches tenant RefreshToken records.
* Carries no tenant or branch scope.
* Does not encode or decode JWTs.
* Does not create or revoke PlatformSession records.
* Does not evaluate authorization policy.
* Does not emit audit events.
* Never commits or rolls back implicitly.

Transaction ownership remains with the caller.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select

from app.models import PlatformRefreshToken
from app.models.security import TokenRevocationReason


class PlatformRefreshTokenService:
    """
    Manage persisted Hela360 Office refresh-token state.

    This service adds, mutates and flushes ORM state. The caller owns the
    enclosing transaction.
    """

    def __init__(self, session) -> None:
        self.session = session

    def create(
        self,
        *,
        platform_user_id: str,
        platform_session_id: str,
        jwt_id: str,
        expires_at: datetime,
        token_family: str | None = None,
        parent_token_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        device_name: str | None = None,
        device_fingerprint: str | None = None,
    ) -> PlatformRefreshToken:
        """
        Persist a newly issued platform refresh token.

        When token_family is omitted, a new rotation family is created.
        """

        now = datetime.now(UTC)

        if expires_at <= now:
            raise ValueError(
                "Platform refresh token expiry must be in the future."
            )

        token = PlatformRefreshToken(
            id=str(uuid4()),
            platform_user_id=platform_user_id,
            platform_session_id=platform_session_id,
            jwt_id=jwt_id,
            token_family=(
                token_family
                or str(uuid4())
            ),
            expires_at=expires_at,
            parent_token_id=parent_token_id,
            replaced_at=None,
            last_used_at=None,
            ip_address=ip_address,
            last_ip_address=ip_address,
            user_agent=user_agent,
            device_name=device_name,
            device_fingerprint=device_fingerprint,
            revoked_at=None,
            revoked_by_platform_user_id=None,
            revoke_reason=None,
        )

        self.session.add(token)
        self.session.flush()

        return token

    def get(
        self,
        token_id: str,
    ) -> PlatformRefreshToken | None:
        """Return one persisted token by primary key."""

        return self.session.get(
            PlatformRefreshToken,
            token_id,
        )

    def get_by_jwt_id(
        self,
        jwt_id: str,
    ) -> PlatformRefreshToken | None:
        """Return one persisted token by JWT identifier."""

        return self.session.scalar(
            select(PlatformRefreshToken)
            .where(
                PlatformRefreshToken.jwt_id
                == jwt_id
            )
        )

    def get_by_jti(
        self,
        jti: str,
    ) -> PlatformRefreshToken | None:
        """Compatibility alias using standard JWT terminology."""

        return self.get_by_jwt_id(jti)

    def get_active_by_jwt_id(
        self,
        jwt_id: str,
    ) -> PlatformRefreshToken | None:
        """Return a token only when it is currently active."""

        token = self.get_by_jwt_id(
            jwt_id
        )

        if token is None:
            return None

        if not token.is_active:
            return None

        return token

    def get_active_by_jti(
        self,
        jti: str,
    ) -> PlatformRefreshToken | None:
        """Compatibility alias using standard JWT terminology."""

        return self.get_active_by_jwt_id(
            jti
        )

    def mark_used(
        self,
        token: PlatformRefreshToken,
        *,
        ip_address: str | None = None,
    ) -> None:
        """Record successful use of a refresh token."""

        token.mark_used()

        if ip_address is not None:
            token.last_ip_address = (
                ip_address
            )

        self.session.flush()

    def revoke(
        self,
        token: PlatformRefreshToken,
        *,
        reason: TokenRevocationReason = (
            TokenRevocationReason.SECURITY_EVENT
        ),
        revoked_by_platform_user_id: str | None = None,
    ) -> bool:
        """
        Revoke one refresh token.

        Returns True when newly revoked and False when already revoked.
        """

        if token.revoked_at is not None:
            return False

        token.revoke(
            reason=reason,
            revoked_by_platform_user_id=(
                revoked_by_platform_user_id
            ),
        )

        self.session.flush()

        return True

    def revoke_by_jwt_id(
        self,
        jwt_id: str,
        *,
        reason: TokenRevocationReason = (
            TokenRevocationReason.SECURITY_EVENT
        ),
        revoked_by_platform_user_id: str | None = None,
    ) -> bool:
        """Revoke one refresh token resolved by its JWT identifier."""

        token = self.get_by_jwt_id(
            jwt_id
        )

        if token is None:
            return False

        return self.revoke(
            token,
            reason=reason,
            revoked_by_platform_user_id=(
                revoked_by_platform_user_id
            ),
        )

    def revoke_by_jti(
        self,
        jti: str,
        *,
        reason: TokenRevocationReason = (
            TokenRevocationReason.SECURITY_EVENT
        ),
        revoked_by_platform_user_id: str | None = None,
    ) -> bool:
        """Compatibility alias using standard JWT terminology."""

        return self.revoke_by_jwt_id(
            jti,
            reason=reason,
            revoked_by_platform_user_id=(
                revoked_by_platform_user_id
            ),
        )

    def revoke_family(
        self,
        *,
        token_family: str,
        reason: TokenRevocationReason = (
            TokenRevocationReason.REUSE_DETECTED
        ),
        revoked_by_platform_user_id: str | None = None,
    ) -> int:
        """Revoke every currently active token in one rotation family."""

        tokens = tuple(
            self.session.scalars(
                select(PlatformRefreshToken)
                .where(
                    PlatformRefreshToken.token_family
                    == token_family,
                    PlatformRefreshToken.revoked_at.is_(None),
                )
                .order_by(
                    PlatformRefreshToken.created_at.asc(),
                    PlatformRefreshToken.id.asc(),
                )
            ).all()
        )

        if not tokens:
            return 0

        for token in tokens:
            token.revoke(
                reason=reason,
                revoked_by_platform_user_id=(
                    revoked_by_platform_user_id
                ),
            )

        self.session.flush()

        return len(tokens)

    def revoke_session_tokens(
        self,
        *,
        platform_session_id: str,
        reason: TokenRevocationReason = (
            TokenRevocationReason.LOGOUT
        ),
        revoked_by_platform_user_id: str | None = None,
    ) -> int:
        """Revoke all active refresh tokens belonging to one session."""

        tokens = tuple(
            self.session.scalars(
                select(PlatformRefreshToken)
                .where(
                    PlatformRefreshToken.platform_session_id
                    == platform_session_id,
                    PlatformRefreshToken.revoked_at.is_(None),
                )
                .order_by(
                    PlatformRefreshToken.created_at.asc(),
                    PlatformRefreshToken.id.asc(),
                )
            ).all()
        )

        if not tokens:
            return 0

        for token in tokens:
            token.revoke(
                reason=reason,
                revoked_by_platform_user_id=(
                    revoked_by_platform_user_id
                ),
            )

        self.session.flush()

        return len(tokens)

    def revoke_user_tokens(
        self,
        *,
        platform_user_id: str,
        reason: TokenRevocationReason = (
            TokenRevocationReason.LOGOUT_ALL
        ),
        revoked_by_platform_user_id: str | None = None,
    ) -> int:
        """Revoke every active token belonging to one PlatformUser."""

        tokens = tuple(
            self.session.scalars(
                select(PlatformRefreshToken)
                .where(
                    PlatformRefreshToken.platform_user_id
                    == platform_user_id,
                    PlatformRefreshToken.revoked_at.is_(None),
                )
                .order_by(
                    PlatformRefreshToken.created_at.asc(),
                    PlatformRefreshToken.id.asc(),
                )
            ).all()
        )

        if not tokens:
            return 0

        for token in tokens:
            token.revoke(
                reason=reason,
                revoked_by_platform_user_id=(
                    revoked_by_platform_user_id
                ),
            )

        self.session.flush()

        return len(tokens)

    def rotate(
        self,
        *,
        old_token: PlatformRefreshToken,
        new_jwt_id: str,
        expires_at: datetime,
        ip_address: str | None = None,
        user_agent: str | None = None,
        device_name: str | None = None,
        device_fingerprint: str | None = None,
    ) -> PlatformRefreshToken:
        """
        Persist a replacement refresh token in the same rotation family.

        The old token becomes TOKEN_ROTATED and the replacement points to it
        through parent_token_id.
        """

        if old_token.revoked_at is not None:
            raise ValueError(
                "Platform refresh token has already been revoked."
            )

        if old_token.is_rotated:
            raise ValueError(
                "Platform refresh token has already been rotated."
            )

        if old_token.is_expired:
            raise ValueError(
                "Platform refresh token has expired."
            )

        now = datetime.now(UTC)

        if expires_at <= now:
            raise ValueError(
                "Replacement refresh token expiry must be in the future."
            )

        old_token.mark_used()
        old_token.rotate()

        new_token = PlatformRefreshToken(
            id=str(uuid4()),
            platform_user_id=(
                old_token.platform_user_id
            ),
            platform_session_id=(
                old_token.platform_session_id
            ),
            jwt_id=new_jwt_id,
            token_family=(
                old_token.token_family
            ),
            expires_at=expires_at,
            parent_token_id=old_token.id,
            replaced_at=None,
            last_used_at=None,
            ip_address=ip_address,
            last_ip_address=ip_address,
            user_agent=user_agent,
            device_name=(
                device_name
                or old_token.device_name
            ),
            device_fingerprint=(
                device_fingerprint
                if device_fingerprint
                is not None
                else old_token.device_fingerprint
            ),
            revoked_at=None,
            revoked_by_platform_user_id=None,
            revoke_reason=None,
        )

        self.session.add(new_token)
        self.session.flush()

        return new_token

    def handle_reuse(
        self,
        token: PlatformRefreshToken,
    ) -> int:
        """
        Respond to reuse of a rotated refresh token.

        The historical parent remains TOKEN_ROTATED. Any still-active token in
        the same family is revoked as REUSE_DETECTED.

        Returns the number of newly revoked family members.
        """

        if not token.is_rotated:
            raise ValueError(
                "Refresh-token reuse handling requires a rotated token."
            )

        return self.revoke_family(
            token_family=token.token_family,
            reason=(
                TokenRevocationReason.REUSE_DETECTED
            ),
        )

    def delete_expired(
        self,
    ) -> int:
        """
        Delete expired refresh-token persistence records.

        Intended for explicit retention/maintenance workflows.
        """

        tokens = tuple(
            self.session.scalars(
                select(PlatformRefreshToken)
                .where(
                    PlatformRefreshToken.expires_at
                    < datetime.now(UTC)
                )
            ).all()
        )

        if not tokens:
            return 0

        for token in tokens:
            self.session.delete(token)

        self.session.flush()

        return len(tokens)


__all__ = [
    "PlatformRefreshTokenService",
]
