"""
Refresh Token Service
=====================

Enterprise refresh-token lifecycle management for Hela360.

This service is the single persistence and lifecycle authority for
stateful refresh-token records.

Responsibilities
----------------
- Persist metadata for newly-issued refresh JWTs
- Resolve refresh-token records by JWT ID
- Validate persisted token state
- Maintain refresh-token families
- Rotate refresh tokens
- Revoke individual refresh tokens
- Revoke token families
- Revoke all tokens belonging to a session
- Revoke all tokens belonging to a user
- Support refresh-token reuse detection
- Delete expired refresh-token records
- Emit refresh-token lifecycle audit events

Architectural Boundaries
------------------------
This service does not:

- authenticate users
- verify passwords
- create or decode JWT values
- create access tokens
- create or revoke user sessions
- evaluate authorization permissions

Those responsibilities belong to:

- AuthenticationService
- PasswordService
- JWTService
- SessionService
- AuthorizationService

Refresh-token JWT values are never persisted. Only their security metadata,
including the JWT ID, ownership, expiry, family, rotation lineage and
revocation state, is stored.

Hela360 Enterprise Pharmacy POS & ERP
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select

from app.extensions import db
from app.models.security import (
    RefreshToken,
    TokenRevocationReason,
)
from app.services.common.audit_actions import AuditAction
from app.services.common.audit_modules import AuditModule
from app.services.common.audit_service import audit_service

# =============================================================================
# Refresh Token Service
# =============================================================================


class RefreshTokenService:
    """
    Enterprise refresh-token persistence and lifecycle manager.

    JWT cryptographic operations deliberately remain outside this service.
    """

    # =========================================================================
    # Creation
    # =========================================================================

    def create(
        self,
        *,
        jwt_id: str,
        user_id: str,
        tenant_id: str,
        session_id: str,
        expires_at: datetime,
        token_family: str | None = None,
        parent_token_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        device_name: str | None = None,
        device_fingerprint: str | None = None,
    ) -> RefreshToken:
        """
        Persist metadata for a newly-issued refresh JWT.

        Parameters
        ----------
        jwt_id:
            JTI embedded in the actual signed refresh JWT.

        token_family:
            Rotation-family identifier. A new family is generated when this
            parameter is omitted.

        parent_token_id:
            Previous refresh-token record when this token was produced by
            rotation.
        """

        now = datetime.now(UTC)

        token = RefreshToken(
            id=str(uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            session_id=session_id,
            jwt_id=jwt_id,
            token_family=token_family or str(uuid4()),
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
            revoked_by_user_id=None,
            revoke_reason=None,
            created_at=now,
            updated_at=now,
        )

        db.session.add(token)
        db.session.commit()

        audit_service.safe_log(
            module=AuditModule.AUTH,
            action=AuditAction.REFRESH_TOKEN_ISSUED,
            entity_type="RefreshToken",
            entity_id=token.id,
            user_id=user_id,
            tenant_id=tenant_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "jwt_id": jwt_id,
                "token_family": token.token_family,
                "parent_token_id": parent_token_id,
                "expires_at": expires_at.isoformat(),
            },
        )

        return token

    # =========================================================================
    # Queries
    # =========================================================================

    def get(
        self,
        token_id: str,
    ) -> RefreshToken | None:
        """
        Retrieve a refresh-token record by primary key.
        """

        return db.session.get(
            RefreshToken,
            token_id,
        )

    def get_by_jwt_id(
        self,
        jwt_id: str,
    ) -> RefreshToken | None:
        """
        Retrieve a refresh-token record by JWT identifier.
        """

        stmt = (
            select(RefreshToken)
            .where(
                RefreshToken.jwt_id == jwt_id,
            )
            .limit(1)
        )

        return db.session.scalar(stmt)

    def get_active_by_jwt_id(
        self,
        jwt_id: str,
    ) -> RefreshToken | None:
        """
        Retrieve an active refresh-token record by JWT identifier.
        """

        token = self.get_by_jwt_id(jwt_id)

        if token is None:
            return None

        if not token.is_active:
            return None

        return token

    def list_user_tokens(
        self,
        *,
        user_id: str,
        tenant_id: str | None = None,
        include_revoked: bool = False,
    ) -> list[RefreshToken]:
        """
        Return refresh tokens belonging to a user.
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

        if tenant_id is not None:
            stmt = stmt.where(
                RefreshToken.tenant_id == tenant_id,
            )

        if not include_revoked:
            stmt = stmt.where(
                RefreshToken.revoked_at.is_(None),
            )

        return list(
            db.session.scalars(stmt).all()
        )

    def list_active_tokens(
        self,
        *,
        user_id: str,
        tenant_id: str | None = None,
    ) -> list[RefreshToken]:
        """
        Return active refresh tokens belonging to a user.
        """

        now = datetime.now(UTC)

        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )

        if tenant_id is not None:
            stmt = stmt.where(
                RefreshToken.tenant_id == tenant_id,
            )

        stmt = stmt.order_by(
            RefreshToken.created_at.desc(),
        )

        return list(
            db.session.scalars(stmt).all()
        )

    def list_session_tokens(
        self,
        *,
        session_id: str,
        include_revoked: bool = False,
    ) -> list[RefreshToken]:
        """
        Return refresh-token records belonging to one authentication session.
        """

        stmt = (
            select(RefreshToken)
            .where(
                RefreshToken.session_id == session_id,
            )
            .order_by(
                RefreshToken.created_at.desc(),
            )
        )

        if not include_revoked:
            stmt = stmt.where(
                RefreshToken.revoked_at.is_(None),
            )

        return list(
            db.session.scalars(stmt).all()
        )

    # =========================================================================
    # Validation
    # =========================================================================

    @staticmethod
    def is_active(
        token: RefreshToken,
    ) -> bool:
        """
        Return True when a refresh-token record may still be used.
        """

        return token.is_active

    @staticmethod
    def is_expired(
        token: RefreshToken,
    ) -> bool:
        """
        Return True when the refresh-token lifetime has elapsed.
        """

        return token.is_expired

    @staticmethod
    def is_revoked(
        token: RefreshToken,
    ) -> bool:
        """
        Return True when the refresh token has been revoked.
        """

        return token.is_revoked

    # =========================================================================
    # Usage Tracking
    # =========================================================================

    def mark_used(
        self,
        token: RefreshToken,
        *,
        ip_address: str | None = None,
    ) -> RefreshToken:
        """
        Mark a refresh token as having been used.
        """

        token.mark_used()

        if ip_address is not None:
            token.last_ip_address = ip_address

        token.updated_at = datetime.now(UTC)

        db.session.commit()

        return token

    # =========================================================================
    # Revocation
    # =========================================================================

    def revoke(
        self,
        token: RefreshToken,
        *,
        reason: TokenRevocationReason = TokenRevocationReason.SECURITY_EVENT,
        revoked_by_user_id: str | None = None,
    ) -> RefreshToken:
        """
        Revoke one refresh-token record.

        Revocation is idempotent.
        """

        if token.is_revoked:
            return token

        now = datetime.now(UTC)

        token.revoked_at = now
        token.revoked_by_user_id = revoked_by_user_id
        token.revoke_reason = reason
        token.updated_at = now

        db.session.commit()

        audit_service.safe_log(
            module=AuditModule.AUTH,
            action=AuditAction.REFRESH_TOKEN_REVOKED,
            entity_type="RefreshToken",
            entity_id=token.id,
            user_id=token.user_id,
            tenant_id=token.tenant_id,
            session_id=token.session_id,
            details={
                "jwt_id": token.jwt_id,
                "token_family": token.token_family,
                "reason": reason.value,
            },
        )

        return token

    def revoke_by_jwt_id(
        self,
        jwt_id: str,
        *,
        reason: TokenRevocationReason = TokenRevocationReason.SECURITY_EVENT,
        revoked_by_user_id: str | None = None,
    ) -> bool:
        """
        Revoke a refresh token by JWT identifier.
        """

        token = self.get_by_jwt_id(jwt_id)

        if token is None:
            return False

        self.revoke(
            token,
            reason=reason,
            revoked_by_user_id=revoked_by_user_id,
        )

        return True

    def revoke_family(
        self,
        *,
        token_family: str,
        reason: TokenRevocationReason = TokenRevocationReason.REUSE_DETECTED,
        revoked_by_user_id: str | None = None,
    ) -> int:
        """
        Revoke all active tokens belonging to one rotation family.

        This is the principal containment mechanism for refresh-token reuse.
        """

        stmt = select(RefreshToken).where(
            RefreshToken.token_family == token_family,
            RefreshToken.revoked_at.is_(None),
        )

        tokens = list(
            db.session.scalars(stmt).all()
        )

        if not tokens:
            return 0

        now = datetime.now(UTC)

        for token in tokens:
            token.revoked_at = now
            token.revoked_by_user_id = revoked_by_user_id
            token.revoke_reason = reason
            token.updated_at = now

        db.session.commit()

        for token in tokens:
            audit_service.safe_log(
                module=AuditModule.AUTH,
                action=AuditAction.REFRESH_TOKEN_REVOKED,
                entity_type="RefreshToken",
                entity_id=token.id,
                user_id=token.user_id,
                tenant_id=token.tenant_id,
                session_id=token.session_id,
                details={
                    "jwt_id": token.jwt_id,
                    "token_family": token.token_family,
                    "reason": reason.value,
                },
            )

        return len(tokens)

    def revoke_session_tokens(
        self,
        *,
        session_id: str,
        reason: TokenRevocationReason = TokenRevocationReason.LOGOUT,
        revoked_by_user_id: str | None = None,
        commit: bool = True,
        emit_audit: bool = True,
    ) -> int:
        """
        Revoke all active refresh tokens belonging to a session.

        Parameters
        ----------
        session_id:
            Authentication session whose active refresh tokens are revoked.

        reason:
            Canonical revocation reason persisted on each token.

        revoked_by_user_id:
            User responsible for the revocation, when applicable.

        commit:
            Commit the database transaction immediately.

            Higher-level domain operations may pass ``False`` so token
            revocation can participate in a larger atomic transaction.

        emit_audit:
            Emit individual refresh-token revocation audit events after a
            successful local commit.

            Audit emission is intentionally deferred when ``commit=False``.
            Higher-level transactional workflows should emit their own
            aggregate audit event after the enclosing transaction succeeds.
        """

        stmt = select(RefreshToken).where(
            RefreshToken.session_id == session_id,
            RefreshToken.revoked_at.is_(None),
        )

        tokens = list(
            db.session.scalars(stmt).all()
        )

        if not tokens:
            return 0

        now = datetime.now(UTC)

        for token in tokens:
            token.revoked_at = now
            token.revoked_by_user_id = revoked_by_user_id
            token.revoke_reason = reason
            token.updated_at = now

        if commit:
            db.session.commit()

            if emit_audit:
                for token in tokens:
                    audit_service.safe_log(
                        module=AuditModule.AUTH,
                        action=AuditAction.REFRESH_TOKEN_REVOKED,
                        entity_type="RefreshToken",
                        entity_id=token.id,
                        user_id=token.user_id,
                        tenant_id=token.tenant_id,
                        session_id=token.session_id,
                        details={
                            "jwt_id": token.jwt_id,
                            "token_family": token.token_family,
                            "reason": reason.value,
                        },
                    )

        return len(tokens)

    def revoke_user_tokens(
        self,
        *,
        user_id: str,
        tenant_id: str | None = None,
        reason: TokenRevocationReason = TokenRevocationReason.LOGOUT_ALL,
        revoked_by_user_id: str | None = None,
    ) -> int:
        """
        Revoke all active refresh tokens belonging to a user.
        """

        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )

        if tenant_id is not None:
            stmt = stmt.where(
                RefreshToken.tenant_id == tenant_id,
            )

        tokens = list(
            db.session.scalars(stmt).all()
        )

        if not tokens:
            return 0

        now = datetime.now(UTC)

        for token in tokens:
            token.revoked_at = now
            token.revoked_by_user_id = revoked_by_user_id
            token.revoke_reason = reason
            token.updated_at = now

        db.session.commit()

        return len(tokens)

    # =========================================================================
    # Rotation
    # =========================================================================

    def rotate(
        self,
        *,
        old_token: RefreshToken,
        new_jwt_id: str,
        expires_at: datetime,
        ip_address: str | None = None,
        user_agent: str | None = None,
        device_name: str | None = None,
        device_fingerprint: str | None = None,
    ) -> RefreshToken:
        """
        Persist the replacement for an existing refresh token.

        The replacement remains in the same token family and references the
        previous token through parent_token_id.

        The previous token is marked both as rotated and revoked.
        """

        if old_token.is_revoked:
            raise ValueError("Refresh token has already been revoked.")

        if old_token.is_rotated:
            raise ValueError("Refresh token has already been rotated.")

        if old_token.is_expired:
            raise ValueError("Refresh token has expired.")

        now = datetime.now(UTC)

        old_token.mark_used()
        old_token.rotate()
        old_token.revoked_at = now
        old_token.revoke_reason = TokenRevocationReason.TOKEN_ROTATED
        old_token.updated_at = now

        new_token = RefreshToken(
            id=str(uuid4()),
            tenant_id=old_token.tenant_id,
            user_id=old_token.user_id,
            session_id=old_token.session_id,
            jwt_id=new_jwt_id,
            token_family=old_token.token_family,
            expires_at=expires_at,
            parent_token_id=old_token.id,
            replaced_at=None,
            last_used_at=None,
            ip_address=ip_address,
            last_ip_address=ip_address,
            user_agent=user_agent,
            device_name=device_name or old_token.device_name,
            device_fingerprint=(
                device_fingerprint
                if device_fingerprint is not None
                else old_token.device_fingerprint
            ),
            revoked_at=None,
            revoked_by_user_id=None,
            revoke_reason=None,
            created_at=now,
            updated_at=now,
        )

        db.session.add(new_token)
        db.session.commit()

        audit_service.safe_log(
            module=AuditModule.AUTH,
            action=AuditAction.REFRESH_TOKEN_ROTATED,
            entity_type="RefreshToken",
            entity_id=new_token.id,
            user_id=new_token.user_id,
            tenant_id=new_token.tenant_id,
            session_id=new_token.session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "old_token_id": old_token.id,
                "old_jwt_id": old_token.jwt_id,
                "new_jwt_id": new_token.jwt_id,
                "token_family": new_token.token_family,
            },
        )

        return new_token

    # =========================================================================
    # Compatibility Aliases
    # =========================================================================

    def get_by_jti(
        self,
        jti: str,
    ) -> RefreshToken | None:
        """
        Compatibility alias for get_by_jwt_id().

        New application code should use get_by_jwt_id().
        """

        return self.get_by_jwt_id(jti)

    def get_active_by_jti(
        self,
        jti: str,
    ) -> RefreshToken | None:
        """
        Compatibility alias for get_active_by_jwt_id().

        New application code should use get_active_by_jwt_id().
        """

        return self.get_active_by_jwt_id(jti)

    def revoke_by_jti(
        self,
        jti: str,
        *,
        reason: TokenRevocationReason = TokenRevocationReason.SECURITY_EVENT,
        revoked_by_user_id: str | None = None,
    ) -> bool:
        """
        Compatibility alias for revoke_by_jwt_id().
        """

        return self.revoke_by_jwt_id(
            jti,
            reason=reason,
            revoked_by_user_id=revoked_by_user_id,
        )

    # =========================================================================
    # Maintenance
    # =========================================================================

    def delete_expired(self) -> int:
        """
        Permanently remove expired refresh-token records.

        Intended for scheduled retention/cleanup workflows.
        """

        stmt = select(RefreshToken).where(
            RefreshToken.expires_at < datetime.now(UTC),
        )

        tokens = list(
            db.session.scalars(stmt).all()
        )

        count = len(tokens)

        if not tokens:
            return 0

        for token in tokens:
            db.session.delete(token)

        db.session.commit()

        return count


# =============================================================================
# Shared Singleton
# =============================================================================

refresh_token_service = RefreshTokenService()


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    "RefreshTokenService",
    "refresh_token_service",
]