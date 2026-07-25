"""
Authentication Service

Enterprise authentication orchestration service for Hela360.

This service coordinates the complete authentication lifecycle while
delegating specialized responsibilities to dedicated services.

Responsibilities
----------------
- User authentication
- Session creation and validation
- JWT issuance
- Refresh token rotation
- Logout (single session)
- Logout from all devices
- Password verification
- Password hash migration
- Password change
- Password reset workflows
- Login throttling
- Audit logging

The AuthenticationService intentionally contains orchestration logic
only. Domain-specific responsibilities are delegated to:

    PasswordService
        • Password hashing
        • Password verification
        • Password policy
        • Password migration

    SessionService
        • Session lifecycle management

    RefreshTokenService
        • Refresh token persistence
        • Token rotation
        • Token revocation

    JWTService
        • Access token generation
        • Refresh token generation
        • JWT decoding

    LoginAttemptService
        • Brute-force protection
        • Account lockouts
        • Login attempt recording

    AuditService
        • Security audit events

This separation keeps each component focused on a single
responsibility while allowing AuthenticationService to expose a clean,
enterprise-grade API for the rest of the application.

Hela360 Enterprise Pharmacy POS & ERP
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from flask_sqlalchemy import session
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models.auth import User
from app.models.security import (
    PasswordResetToken,
    UserSession,
)

from app.services.common.audit_actions import AuditAction
from app.services.common.audit_service import audit_service

from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
)

from app.auth.exceptions import (
    AccountArchivedError,
    AccountDisabledError,
    AccountInactiveError,
    AccountLockedError,
    AccountSuspendedError,
    InvalidCredentialsError,
    UserNotFoundError,
)

from app.services.tenant.auth.login_attempt_service import (
    login_attempt_service,
)

from app.services.tenant.auth.password_service import (
    hash_password,
    upgrade_hash_if_needed,
    validate_password,
    verify_password,
)

from app.services.tenant.auth.refresh_token_service import (
    refresh_token_service,
)

from app.services.tenant.auth.session_service import (
    session_service,
)


# ============================================================================
# Authentication Constants
# ============================================================================

DEFAULT_PASSWORD_RESET_EXPIRY_HOURS = 1


# ============================================================================
# Authentication Result DTOs
# ============================================================================

@dataclass(slots=True, frozen=True)
class AuthenticationResult:
    """
    Returned after a successful authentication.

    Attributes
    ----------
    user:
        Authenticated user.

    access_token:
        Signed JWT access token.

    refresh_token:
        Signed JWT refresh token.

    session:
        Persisted authentication session.

    refresh_token_record:
        Persisted refresh token entity.
    """

    user: User
    access_token: str
    refresh_token: str
    session: UserSession
    refresh_token_record: Any


@dataclass(slots=True, frozen=True)
class RefreshResult:
    """
    Returned after a successful refresh token rotation.
    """

    access_token: str
    refresh_token: str
    session: UserSession
    refresh_token_record: Any


@dataclass(slots=True, frozen=True)
class PasswordChangeResult:
    """
    Result of a password change operation.
    """

    user: User
    password_updated_at: datetime

@dataclass(slots=True)
class AuthenticationContext:
    """
    Authentication state accumulated during a successful login or refresh.
    """

    user: User
    session: UserSession

    ip_address: str | None
    user_agent: str | None

# ============================================================================
# Authentication Service
# ============================================================================

class AuthenticationService:
    """
    Enterprise authentication façade.

    This service provides the single public interface for all
    authentication workflows within Hela360.

    All modules—including API endpoints, background workers, mobile
    applications, integrations and future SSO providers—should interact
    with authentication exclusively through this service.

    Workflow Summary
    ----------------
        Login
            ↓
        LoginAttemptService
            ↓
        PasswordService
            ↓
        SessionService
            ↓
        RefreshTokenService
            ↓
        JWTService
            ↓
        AuditService

    Design Principles
    -----------------
    • Stateless orchestration
    • Explicit transactions
    • Strong typing
    • Multi-tenant aware
    • Audit-first security
    • Separation of concerns
    • Enterprise-ready
    """

    def __init__(
        self,
        *,
        password_reset_expiry_hours: int = (
            DEFAULT_PASSWORD_RESET_EXPIRY_HOURS
        ),
    ) -> None:
        self.password_reset_expiry_hours = (
            password_reset_expiry_hours
        )

    # =======================================================================
    # User Resolution
    # =======================================================================

    def _get_user(
        self,
        *,
        tenant_id: str,
        username_or_email: str,
    ) -> User | None:
        """
        Resolve a tenant user by username or email.

        User roles are eagerly loaded because virtually every successful
        authentication immediately requires authorization.
        """

        identifier = username_or_email.strip().lower()

        stmt = (
            select(User)
            .options(
                selectinload(User.roles),
            )
            .where(
                User.tenant_id == tenant_id,
                User.is_active.is_(True),
                or_(
                    User.email == identifier,
                    User.username == identifier,
                ),
            )
            .limit(1)
        )

        return db.session.scalar(stmt)

    # =======================================================================
    # Password Migration
    # =======================================================================

    def _upgrade_password_hash_if_required(
        self,
        *,
        user: User,
        plaintext_password: str,
    ) -> None:
        """
        Transparently migrate legacy password hashes.

        When a user successfully authenticates using an older hashing
        algorithm (or outdated Argon2 parameters), the password hash is
        upgraded without requiring the user to reset their password.
        """

        upgraded_hash = upgrade_hash_if_needed(
            plaintext_password,
            user.password_hash,
        )

        if upgraded_hash is None:
            return

        user.password_hash = upgraded_hash

        db.session.commit()


    # =======================================================================
    # Authorization Claim Helpers
    # =======================================================================

    def _authorization_claims(
        self,
        user: User,
    ) -> tuple[str | None, list[str]]:
        """
        Resolve the user's authorization claims.

        These claims are embedded into newly issued access tokens so that
        every token reflects the user's current role assignments and
        effective permissions.
        """

        primary_role = (
            user.roles[0].code
            if user.roles
            else None
        )

        permissions = sorted(
            {
                permission.code
                for role in user.roles
                for permission in role.permissions
            }
        )

        return primary_role, permissions


    # =======================================================================
    # Token Helpers
    # =======================================================================

    def _issue_tokens(
        self,
        context: AuthenticationContext,
    ) -> tuple[str, str]:
        """
        Issue a new access token and refresh token for an authenticated
        session.

        Authorization claims are resolved immediately before token issuance
        so that every access token reflects the user's current roles and
        permissions.
        """

        role, permissions = self._authorization_claims(
            context.user,
        )

        access_token = create_access_token(
            user_id=context.user.id,
            tenant_id=context.user.tenant_id,
            branch_id=context.user.branch_id,
            role=role,
            permissions=permissions,
            session_id=context.session.id,
        )

        refresh_token = create_refresh_token(
            user_id=context.user.id,
            tenant_id=context.user.tenant_id,
            session_id=context.session.id,
        )

        return access_token, refresh_token
    
    # =======================================================================
    # Audit Helpers
    # =======================================================================

    def _audit_login_success(
        self,
        *,
        context: AuthenticationContext,
    ) -> None:
        """
        Record a successful authentication.
        """

        audit_service.safe_log(
            action=AuditAction.LOGIN_SUCCESS,
            entity_type="User",
            entity_id=context.user.id,
            user_id=context.user.id,
            tenant_id=context.user.tenant_id,
            branch_id=context.user.branch_id,
            session_id=context.session.id,
            ip_address=context.ip_address,
            user_agent=context.user_agent,
        )

    def _audit_login_failure(
        self,
        *,
        tenant_id: str,
        username_or_email: str,
        ip_address: str | None,
        reason: str,
    ) -> None:
        """
        Record a failed authentication attempt.
        """

        audit_service.safe_log(
            action=AuditAction.LOGIN_FAILURE,
            entity_type="Authentication",
            tenant_id=tenant_id,
            ip_address=ip_address,
            status="failed",
            details={
                "username_or_email": username_or_email,
                "reason": reason,
            },
        )

    def _audit_token_refresh(
        self,
        *,
        context: AuthenticationContext,
    ) -> None:
        """
        Record a successful refresh token rotation.

        A refresh event indicates that an authenticated session has
        successfully exchanged a valid refresh token for a new JWT pair.
        """

        audit_service.safe_log(
            action=AuditAction.TOKEN_REFRESHED,
            entity_type="Authentication",
            entity_id=context.session.id,
            user_id=context.user.id,
            tenant_id=context.user.tenant_id,
            branch_id=context.user.branch_id,
            session_id=context.session.id,
            ip_address=context.ip_address,
            user_agent=context.user_agent,
            metadata={
                "refresh_token_jti": context.session.refresh_token_jti,
            },
        )
    # =======================================================================
    # Session Cleanup Helpers
    # =======================================================================

    def _revoke_refresh_session(
        self,
        *,
        refresh_token,
        session: UserSession,
    ) -> None:
        """
        Revoke both the refresh token and its associated session.

        This helper is used whenever a refresh workflow determines that the
        current authentication context can no longer be trusted.
        """

        refresh_token_service.revoke(refresh_token)
        session_service.revoke(session)

    # =======================================================================
    # Account Validation Helpers
    # =======================================================================

    def _validate_account_state(
        self,
        user: User,
    ) -> None:
        """
        Validate that the user account is permitted to authenticate.

        Raises the appropriate domain exception for the first failing
        account state encountered.
        """

        if not user.is_active:
            raise AccountInactiveError()

        if user.is_disabled:
            raise AccountDisabledError()

        if user.is_locked:
            raise AccountLockedError()

        if getattr(user, "status", None) == "suspended":
            raise AccountSuspendedError()

        if getattr(user, "status", None) == "archived":
            raise AccountArchivedError()

    # =======================================================================
    # Login
    # =======================================================================

    def login(
        self,
        *,
        tenant_id: str,
        username_or_email: str,
        password: str,
        device_name: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuthenticationResult:
        """
        Authenticate a tenant user.

        Workflow
        --------
        1. Enforce login lockout policy.
        2. Resolve the user account.
        3. Verify credentials.
        4. Upgrade the password hash if required.
        5. Create a refresh-token record.
        6. Create an authenticated session.
        7. Build the authentication context.
        8. Issue JWT access and refresh tokens.
        9. Audit the successful authentication.
        10. Return the authenticated session details.

        Raises
        ------
        InvalidCredentialsError
            Username/email or password is invalid.

        AccountLockedError
            Account is temporarily locked due to repeated failures.
        """

        # --------------------------------------------------------------
        # Lockout protection
        # --------------------------------------------------------------

        if login_attempt_service.is_locked(
            email=username_or_email,
            tenant_id=tenant_id,
            ip_address=ip_address,
        ):
            self._audit_login_failure(
                tenant_id=tenant_id,
                username_or_email=username_or_email,
                ip_address=ip_address,
                reason="Account locked",
            )

            raise AccountLockedError(
                "Account temporarily locked due to repeated failed login attempts."
            )

        # --------------------------------------------------------------
        # Resolve user
        # --------------------------------------------------------------

        user = self._get_user(
            tenant_id=tenant_id,
            username_or_email=username_or_email,
        )

        if user is None:
            login_attempt_service.record_failure(
                email=username_or_email,
                tenant_id=tenant_id,
                ip_address=ip_address,
                user_agent=user_agent,
                reason="Unknown account",
            )

            self._audit_login_failure(
                tenant_id=tenant_id,
                username_or_email=username_or_email,
                ip_address=ip_address,
                reason="Unknown account",
            )

            raise InvalidCredentialsError()

        # --------------------------------------------------------------
        # Verify password
        # --------------------------------------------------------------

        if not verify_password(
            password,
            user.password_hash,
        ):
            login_attempt_service.record_failure(
                email=user.email or username_or_email,
                tenant_id=tenant_id,
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                reason="Incorrect password",
            )

            self._audit_login_failure(
                tenant_id=tenant_id,
                username_or_email=username_or_email,
                ip_address=ip_address,
                reason="Incorrect password",
            )

            raise InvalidCredentialsError()

        # --------------------------------------------------------------
        # Record successful authentication
        # --------------------------------------------------------------

        login_attempt_service.record_success(
            email=user.email or username_or_email,
            tenant_id=tenant_id,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        login_attempt_service.reset_failures(
            email=user.email or username_or_email,
            tenant_id=tenant_id,
        )

        # --------------------------------------------------------------
        # Upgrade password hash if required
        # --------------------------------------------------------------

        self._upgrade_password_hash_if_required(
            user=user,
            plaintext_password=password,
        )

        # --------------------------------------------------------------
        # Persist refresh token
        # --------------------------------------------------------------

        refresh_record = refresh_token_service.create(
            user_id=user.id,
            tenant_id=user.tenant_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # --------------------------------------------------------------
        # Create authenticated session
        # --------------------------------------------------------------

        session = session_service.create(
            user_id=user.id,
            tenant_id=user.tenant_id,
            refresh_token_jti=refresh_record.jti,
            expires_at=refresh_record.expires_at,
            device_name=device_name,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # --------------------------------------------------------------
        # Authentication context
        # --------------------------------------------------------------

        context = AuthenticationContext(
            user=user,
            session=session,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # --------------------------------------------------------------
        # Issue tokens
        # --------------------------------------------------------------

        access_token, refresh_token = self._issue_tokens(
            context=context,
        )

        # --------------------------------------------------------------
        # Audit
        # --------------------------------------------------------------

        self._audit_login_success(
            context=context,
        )

        # --------------------------------------------------------------
        # Result
        # --------------------------------------------------------------

        return AuthenticationResult(
            user=user,
            access_token=access_token,
            refresh_token=refresh_token,
            session=session,
            refresh_token_record=refresh_record,
        )
    # =======================================================================
    # Token Refresh
    # =======================================================================

    def refresh(
        self,
        *,
        refresh_token: str,
        ip_address: str | None = None,
        user_agent: str |None = None,
    ) -> RefreshResult:
        """
        Refresh an authenticated session.

        Workflow
        --------
        1. Decode the refresh JWT.
        2. Validate the persisted refresh token.
        3. Resolve the active session.
        4. Resolve and validate the authenticated user.
        5. Rotate the refresh token.
        6. Update the authenticated session.
        7. Issue a fresh JWT pair.
        8. Audit the refresh event.

        Raises
        ------
        InvalidCredentialsError
            Refresh token cannot be used.

        AccountInactiveError
            Authentication session is no longer active.

        UserNotFoundError
            User no longer exists.
        """

        # --------------------------------------------------------------
        # Decode refresh token
        # --------------------------------------------------------------

        identity = refresh_token_service.decode(refresh_token)

        # --------------------------------------------------------------
        # Validate persisted refresh token
        # --------------------------------------------------------------

        current_refresh = refresh_token_service.get_by_jti(
            identity.token_id,
        )

        if current_refresh is None:
            raise InvalidCredentialsError("Refresh token not found.")

        if not refresh_token_service.is_active(current_refresh):
            raise InvalidCredentialsError(
                "Refresh token is no longer valid."
            )

        # --------------------------------------------------------------
        # Resolve active session
        # --------------------------------------------------------------

        session = session_service.get_active(
            identity.session_id,
        )

        if session is None:
            self._revoke_refresh_session(
                refresh_token=current_refresh,
                session=None,
            )
            raise AccountInactiveError(
                "Authentication session has expired."
            )

        # --------------------------------------------------------------
        # Resolve authenticated user
        # --------------------------------------------------------------

        user = db.session.get(User, identity.user_id)

        if user is None:
            self._revoke_refresh_session(
                refresh_token=current_refresh,
                session=session,
            )
            raise UserNotFoundError()

        if not user.is_active:
            self._revoke_refresh_session(
                refresh_token=current_refresh,
                session=session,
            )
            raise AccountInactiveError()

        # --------------------------------------------------------------
        # Authentication context
        # --------------------------------------------------------------

        context = AuthenticationContext(
            user=user,
            session=session,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # --------------------------------------------------------------
        # Rotate refresh token
        # --------------------------------------------------------------

        new_refresh = refresh_token_service.rotate(
            current_refresh,
            ip_address=context.ip_address,
            user_agent=context.user_agent,
        )

        # --------------------------------------------------------------
        # Update session
        # --------------------------------------------------------------

        session.refresh_token_jti = new_refresh.jti
        session.expires_at = new_refresh.expires_at

        session_service.touch(session)

        db.session.commit()

        # --------------------------------------------------------------
        # Issue replacement JWTs
        # --------------------------------------------------------------

        access_token, refresh_jwt = self._issue_tokens(
            context=context,
        )

        # --------------------------------------------------------------
        # Audit
        # --------------------------------------------------------------

        audit_service.safe_log(
            action=AuditAction.TOKEN_REFRESHED,
            entity_type="Authentication",
            entity_id=context.session.id,
            user_id=context.user.id,
            tenant_id=context.user.tenant_id,
            branch_id=context.user.branch_id,
            session_id=context.session.id,
            ip_address=context.ip_address,
            user_agent=context.user_agent,
        )

        return RefreshResult(
            access_token=access_token,
            refresh_token=refresh_jwt,
            session=context.session,
            refresh_token_record=new_refresh,
        )
    # =======================================================================
    # Logout
    # =======================================================================

    def logout(
        self,
        *,
        session_id: str,
    ) -> None:
        """
        Logout a single authenticated session.

        Revokes both the authentication session and its associated
        refresh token. Existing access tokens will naturally expire.
        """

        session = session_service.get(session_id)

        if session is None:
            return

        refresh = refresh_token_service.get_by_jti(
            session.refresh_token_jti,
        )

        if refresh is not None:
            refresh_token_service.revoke(refresh)

        session_service.revoke(session)

        audit_service.safe_log(
            action=AuditAction.LOGOUT,
            entity_type="Authentication",
            entity_id=session.id,
            user_id=session.user_id,
            tenant_id=session.tenant_id,
            session_id=session.id,
        )

    # =======================================================================
    # Logout All Devices
    # =======================================================================

    def logout_everywhere(
        self,
        *,
        user_id: str,
    ) -> int:
        """
        Logout every authenticated session belonging to a user.

        Returns
        -------
        int
            Number of revoked sessions.
        """

        refresh_token_service.revoke_user_tokens(
            user_id=user_id,
        )

        revoked = session_service.revoke_user_sessions(
            user_id=user_id,
        )

        audit_service.safe_log(
            action=AuditAction.LOGOUT_ALL,
            entity_type="User",
            entity_id=user_id,
            user_id=user_id,
            details={
                "revoked_sessions": revoked,
            },
        )

        return revoked

    # =======================================================================
    # Session Validation
    # =======================================================================

    def validate_session(
        self,
        *,
        session_id: str,
    ) -> bool:
        """
        Determine whether a session is currently valid.

        This method is useful for protected endpoints that maintain
        server-side session state in addition to JWT validation.
        """

        session = session_service.get_active(
            session_id,
        )

        if session is None:
            return False

        refresh = refresh_token_service.get_by_jti(
            session.refresh_token_jti,
        )

        if refresh is None:
            return False

        if not refresh_token_service.is_active(refresh):
            return False

        return True

    # =======================================================================
    # Session Activity
    # =======================================================================

    def touch_session(
        self,
        *,
        session_id: str,
    ) -> None:
        """
        Update the activity timestamp for an active session.
        """

        session = session_service.get_active(
            session_id,
        )

        if session is None:
            return

        session_service.touch(session)  


# ============================================================================
# Singleton
# ============================================================================

authentication_service = AuthenticationService()


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    "AuthenticationResult",
    "RefreshResult",
    "AuthenticationService",
    "authentication_service",
]                           