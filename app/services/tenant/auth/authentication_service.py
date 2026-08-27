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
from datetime import UTC, datetime, timedelta
from typing import Any

from flask_sqlalchemy import session
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models.auth import (
    Role,
    User,
    UserPermission,
)
from app.models.security import (
    PasswordResetToken,
    TokenRevocationReason,
    UserSession,
)

from app.services.tenant.auth.authorization_service import (
    authorization_service,
)

from app.services.tenant.auth.jwt_service import (
    jwt_service,
)

from app.services.common.audit_actions import AuditAction
from app.services.common.audit_service import audit_service
from app.services.common.audit_modules import AuditModule

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
                selectinload(User.roles)
                .selectinload(Role.permissions),

                selectinload(
                    User.permission_overrides
                ).selectinload(
                    UserPermission.permission
                ),
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
    ) -> list[str]:
        """
        Resolve the user's effective authorization claims.

        Access-token authorization claims are derived from the canonical
        AuthorizationService so JWTs reflect the user's complete effective
        permission state:

            role permissions
            + explicit user allows
            - explicit user denies

        Assigned tenant roles are not projected into a singular JWT role.
        Hela360 supports multiple role assignments, and role collection order
        does not define user identity or authorization precedence.
        """

        return sorted(
            authorization_service.get_permissions(
                user,
                tenant_id=user.tenant_id,
            )
        )

    # =======================================================================
    # Token Helpers
    # =======================================================================

    def _issue_tokens(
        self,
        context: AuthenticationContext,
    ):
        """
        Issue a new access/refresh JWT pair for an authenticated session.

        JWTService is the canonical token-issuance boundary. The returned
        token-pair metadata contains the actual refresh-token JTI and expiry
        that must subsequently be persisted through RefreshTokenService.
        """

        permissions = self._authorization_claims(
            context.user,
        )

        return jwt_service.issue_token_pair(
            user_id=str(context.user.id),
            tenant_id=str(context.user.tenant_id),
            branch_id=(
                str(context.user.branch_id)
                if context.user.branch_id
                else None
            ),
            permissions=permissions,
            session_id=str(context.session.id),
        )    
    # =======================================================================
    # Audit Helpers
    # =======================================================================

    def _audit_login_success(
        self,
        *,
        context: AuthenticationContext,
    ) -> None:
        """
        Record a successful authentication event.
        """

        audit_service.safe_log(
            module=AuditModule.AUTH,
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

        audit_service.login_failure(
            tenant_id=tenant_id,
            email=username_or_email,
            ip_address=ip_address,
            reason=reason,
        )

    # =======================================================================
    # Session Cleanup Helpers
    # =======================================================================

    def _revoke_refresh_session(
        self,
        *,
        refresh_token,
        session: UserSession | None,
        reason: TokenRevocationReason = TokenRevocationReason.SECURITY_EVENT,
    ) -> None:
        """
        Revoke a refresh token and, when available, its associated session.

        This helper is used when a refresh workflow determines that the
        authentication context can no longer be trusted.
        """

        refresh_token_service.revoke(
            refresh_token,
            reason=reason,
        )

        if session is not None:
            session_service.revoke(
                session,
                reason=reason,
            )
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

        if not login_attempt_service.can_attempt(
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
                failure_reason="Unknown account",
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
                ip_address=ip_address,
                user_agent=user_agent,
                failure_reason="Incorrect password",
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
        # Create authenticated session
        # --------------------------------------------------------------

        provisional_session_expiry = (
            datetime.now(UTC)
            + timedelta(
                seconds=jwt_service.refresh_token_expires_in(),
            )
        )

        session = session_service.create(
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            expires_at=provisional_session_expiry,
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
        # Issue authoritative JWT pair
        # --------------------------------------------------------------

        token_pair = self._issue_tokens(
            context=context,
        )

        # Synchronize the session lifetime with the actual
        # refresh-token expiry issued by JWTService.
        session.expires_at = token_pair.refresh_expires_at

        # --------------------------------------------------------------
        # Persist refresh-token metadata
        # --------------------------------------------------------------

        refresh_record = refresh_token_service.create(
            jwt_id=token_pair.refresh_jti,
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            session_id=str(session.id),
            expires_at=token_pair.refresh_expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            device_name=device_name,
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
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
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
        user_agent: str | None = None,
    ) -> RefreshResult:
        """
        Rotate a valid refresh token and issue replacement authentication
        credentials.

        Workflow
        --------
        1. Decode and validate the refresh JWT.
        2. Resolve its persisted refresh-token record.
        3. Validate token ownership and lifecycle state.
        4. Resolve the active authentication session.
        5. Resolve and validate the authenticated user.
        6. Issue a replacement refresh JWT.
        7. Persist the replacement as a rotation child of the old token.
        8. Issue a fresh access token.
        9. Extend and touch the authenticated session.
        10. Return the replacement token pair.
        """

        # --------------------------------------------------------------
        # Decode refresh JWT
        # --------------------------------------------------------------

        payload = jwt_service.decode_refresh_token(
            refresh_token,
        )

        jwt_id = jwt_service.token_id(payload)
        user_id = jwt_service.extract_user_id(payload)
        tenant_id = jwt_service.extract_tenant_id(payload)
        session_id = jwt_service.extract_session_id(payload)

        if not jwt_id or not user_id or not tenant_id or not session_id:
            raise InvalidCredentialsError(
                "Refresh token is missing required authentication claims."
            )

        # --------------------------------------------------------------
        # Resolve persisted refresh-token record
        # --------------------------------------------------------------

        current_refresh = refresh_token_service.get_by_jwt_id(
            jwt_id,
        )

        if current_refresh is None:
            raise InvalidCredentialsError(
                "Refresh token not found."
            )

        # --------------------------------------------------------------
        # Validate token claim ownership
        # --------------------------------------------------------------

        if (
            str(current_refresh.user_id) != str(user_id)
            or str(current_refresh.tenant_id) != str(tenant_id)
            or str(current_refresh.session_id) != str(session_id)
        ):
            refresh_token_service.revoke_family(
                token_family=current_refresh.token_family,
                reason=TokenRevocationReason.SECURITY_EVENT,
            )

            raise InvalidCredentialsError(
                "Refresh token authentication context is invalid."
            )

        # --------------------------------------------------------------
        # Detect replay / invalid persisted token
        # --------------------------------------------------------------

        if not current_refresh.is_active:
            if current_refresh.is_rotated:
                refresh_token_service.revoke_family(
                    token_family=current_refresh.token_family,
                    reason=TokenRevocationReason.REUSE_DETECTED,
                )

                session = session_service.get(
                    str(current_refresh.session_id),
                )

                if session is not None:
                    session_service.revoke(
                        session,
                        reason=TokenRevocationReason.REUSE_DETECTED,
                    )

            raise InvalidCredentialsError(
                "Refresh token is no longer valid."
            )

        # --------------------------------------------------------------
        # Resolve active session
        # --------------------------------------------------------------

        session = session_service.get_active(
            str(session_id),
        )

        if session is None:
            refresh_token_service.revoke(
                current_refresh,
                reason=TokenRevocationReason.SESSION_EXPIRED,
            )

            raise AccountInactiveError(
                "Authentication session has expired."
            )

        # --------------------------------------------------------------
        # Resolve authenticated user
        # --------------------------------------------------------------

        user = db.session.get(
            User,
            str(user_id),
        )

        if user is None:
            self._revoke_refresh_session(
                refresh_token=current_refresh,
                session=session,
                reason=TokenRevocationReason.USER_DELETED,
            )

            raise UserNotFoundError()

        if str(user.tenant_id) != str(tenant_id):
            self._revoke_refresh_session(
                refresh_token=current_refresh,
                session=session,
                reason=TokenRevocationReason.SECURITY_EVENT,
            )

            raise InvalidCredentialsError(
                "Refresh token tenant context is invalid."
            )

        if not user.is_active:
            self._revoke_refresh_session(
                refresh_token=current_refresh,
                session=session,
                reason=TokenRevocationReason.ACCOUNT_DISABLED,
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
        # Issue replacement refresh JWT first
        # --------------------------------------------------------------

        replacement_refresh_jwt = jwt_service.issue_refresh_token(
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            session_id=str(session.id),
        )

        replacement_payload = jwt_service.decode_refresh_token(
            replacement_refresh_jwt,
        )

        replacement_jwt_id = jwt_service.token_id(
            replacement_payload,
        )

        replacement_expires_at = jwt_service.token_expiry(
            replacement_payload,
        )

        # --------------------------------------------------------------
        # Persist rotation
        # --------------------------------------------------------------

        new_refresh = refresh_token_service.rotate(
            old_token=current_refresh,
            new_jwt_id=replacement_jwt_id,
            expires_at=replacement_expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # --------------------------------------------------------------
        # Issue fresh access JWT
        # --------------------------------------------------------------

        permissions = self._authorization_claims(
            user,
        )

        access_token = jwt_service.issue_access_token(
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            branch_id=(
                str(user.branch_id)
                if user.branch_id
                else None
            ),
            permissions=permissions,
            session_id=str(session.id),
        )

        # --------------------------------------------------------------
        # Refresh session lifetime/activity
        # --------------------------------------------------------------

        session.expires_at = replacement_expires_at

        session_service.touch(
            session,
            ip_address=ip_address,
        )

        # --------------------------------------------------------------
        # Result
        # --------------------------------------------------------------

        return RefreshResult(
            access_token=access_token,
            refresh_token=replacement_refresh_jwt,
            session=session,
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
        Logout one authenticated session.

        All still-active refresh tokens belonging to the session are revoked.
        Existing access tokens expire naturally.
        """

        session = session_service.get(
            session_id,
        )

        if session is None:
            return

        refresh_token_service.revoke_session_tokens(
            session_id=str(session.id),
            reason=TokenRevocationReason.LOGOUT,
            revoked_by_user_id=str(session.user_id),
        )

        session_service.revoke(
            session,
            reason=TokenRevocationReason.LOGOUT,
            revoked_by_user_id=str(session.user_id),
        )

        audit_service.safe_log(
            module=AuditModule.AUTH,
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

        All active refresh tokens and authentication sessions belonging to
        the user's tenant are revoked.

        Returns
        -------
        int
            Number of authentication sessions revoked.

        Raises
        ------
        UserNotFoundError
            The requested user no longer exists.
        """

        # --------------------------------------------------------------
        # Resolve user / tenant context
        # --------------------------------------------------------------

        user = db.session.get(
            User,
            user_id,
        )

        if user is None:
            raise UserNotFoundError()

        tenant_id = str(user.tenant_id)

        # --------------------------------------------------------------
        # Revoke refresh tokens
        # --------------------------------------------------------------

        refresh_token_service.revoke_user_tokens(
            user_id=str(user.id),
            tenant_id=tenant_id,
            reason=TokenRevocationReason.LOGOUT_ALL,
            revoked_by_user_id=str(user.id),
        )

        # --------------------------------------------------------------
        # Revoke authenticated sessions
        # --------------------------------------------------------------

        revoked = session_service.revoke_user_sessions(
            user_id=str(user.id),
            tenant_id=tenant_id,
            reason=TokenRevocationReason.LOGOUT_ALL,
            revoked_by_user_id=str(user.id),
        )

        # --------------------------------------------------------------
        # Audit
        # --------------------------------------------------------------

        audit_service.safe_log(
            module=AuditModule.AUTH,
            action=AuditAction.LOGOUT_ALL,
            entity_type="User",
            entity_id=str(user.id),
            user_id=str(user.id),
            tenant_id=tenant_id,
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
        Determine whether an authentication session is currently valid.

        A usable session must itself be active and retain at least one active
        refresh token belonging to that session.
        """

        session = session_service.get_active(
            session_id,
        )

        if session is None:
            return False

        refresh_tokens = refresh_token_service.list_session_tokens(
            session_id=str(session.id),
            include_revoked=False,
        )

        return any(
            token.is_active
            for token in refresh_tokens
        )
    
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