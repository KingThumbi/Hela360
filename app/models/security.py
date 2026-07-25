"""
Security Models

Enterprise authentication and security models for Hela360.

This module contains all stateful security entities used by the
authentication subsystem. Identity (users, roles and permissions)
lives in ``app.models.auth`` while transient authentication state
is modeled here.

Responsibilities
----------------
• User authentication sessions
• Refresh token rotation
• Password reset workflows
• Login attempt tracking
• Token revocation history

Design Principles
-----------------
• Multi-tenant aware
• Fully auditable
• UUID primary keys
• Soft revocation instead of deletion
• Refresh-token rotation support
• JWT replay detection
• MFA-ready
• Geo-location ready
• Enterprise indexing strategy

Hela360 Enterprise Pharmacy POS & ERP
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from app.extensions import db
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


# ============================================================================
# Enumerations
# ============================================================================


class AuthenticationMethod(StrEnum):
    """
    Primary authentication mechanism used to establish a session.
    """

    PASSWORD = "password"
    PASSWORD_MFA = "password_mfa"
    SSO = "sso"
    API_KEY = "api_key"
    SERVICE_ACCOUNT = "service_account"


class AuthenticationLevel(StrEnum):
    """
    Authentication assurance level.

    NORMAL
        Username + password

    MFA
        Password + second factor

    ELEVATED
        Privileged authentication for highly sensitive operations.
    """

    NORMAL = "normal"
    MFA = "mfa"
    ELEVATED = "elevated"


class SessionStatus(StrEnum):
    """
    Current session lifecycle state.
    """

    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class TokenRevocationReason(StrEnum):
    """
    Reason a refresh token or session was revoked.
    """

    LOGOUT = "logout"

    LOGOUT_ALL = "logout_all"

    TOKEN_ROTATED = "token_rotated"

    PASSWORD_CHANGED = "password_changed"

    ACCOUNT_DISABLED = "account_disabled"

    ADMIN_REVOKED = "admin_revoked"

    REUSE_DETECTED = "reuse_detected"

    SECURITY_EVENT = "security_event"

    SESSION_EXPIRED = "session_expired"

    USER_DELETED = "user_deleted"


class PasswordResetStatus(StrEnum):
    """
    Password reset lifecycle.
    """

    PENDING = "pending"

    USED = "used"

    EXPIRED = "expired"

    REVOKED = "revoked"


class LoginFailureCode(StrEnum):
    """
    Machine-readable login failure reasons.

    These values should be used by services instead of hard-coded
    strings to improve analytics, reporting and security monitoring.
    """

    INVALID_CREDENTIALS = "invalid_credentials"

    INVALID_PASSWORD = "invalid_password"

    UNKNOWN_EMAIL = "unknown_email"

    UNKNOWN_USERNAME = "unknown_username"

    ACCOUNT_DISABLED = "account_disabled"

    ACCOUNT_LOCKED = "account_locked"

    PASSWORD_EXPIRED = "password_expired"

    PASSWORD_RESET_REQUIRED = "password_reset_required"

    MFA_REQUIRED = "mfa_required"

    MFA_FAILED = "mfa_failed"

    SESSION_REVOKED = "session_revoked"

    RATE_LIMITED = "rate_limited"


# ============================================================================
# Shared Mixins
# ============================================================================


class SessionMetadataMixin:
    """
    Common metadata captured for authenticated sessions.

    Shared by UserSession and can later be reused by API sessions,
    service accounts and SSO sessions.
    """

    device_name = db.Column(
        db.String(150),
    )

    browser = db.Column(
        db.String(120),
    )

    operating_system = db.Column(
        db.String(120),
    )

    device_fingerprint = db.Column(
        db.String(255),
        index=True,
    )

    ip_address = db.Column(
        db.String(64),
    )

    last_ip_address = db.Column(
        db.String(64),
    )

    user_agent = db.Column(
        db.Text,
    )

    country = db.Column(
        db.String(100),
    )

    city = db.Column(
        db.String(100),
    )


class AuthenticationAuditMixin:
    """
    Stores information describing how a user authenticated.
    """

    authentication_method = db.Column(
        db.Enum(
            AuthenticationMethod,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=AuthenticationMethod.PASSWORD,
    )

    authentication_level = db.Column(
        db.Enum(
            AuthenticationLevel,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=AuthenticationLevel.NORMAL,
    )

    mfa_verified_at = db.Column(
        db.DateTime(timezone=True),
    )


class RevocationMixin:
    """
    Shared revocation fields.

    Used by sessions, refresh tokens and password reset tokens.
    """

    revoked_at = db.Column(
        db.DateTime(timezone=True),
        index=True,
    )

    revoked_by_user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        index=True,
    )

    revoke_reason = db.Column(
        db.Enum(
            TokenRevocationReason,
            native_enum=False,
            length=50,
        ),
    )

    @property
    def is_revoked(self) -> bool:
        """
        Return True when this object has been revoked.
        """
        return self.revoked_at is not None


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    "AuthenticationMethod",
    "AuthenticationLevel",
    "SessionStatus",
    "TokenRevocationReason",
    "PasswordResetStatus",
    "LoginFailureCode",
    "SessionMetadataMixin",
    "AuthenticationAuditMixin",
    "RevocationMixin",
]

# ============================================================================
# User Sessions
# ============================================================================


class UserSession(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SessionMetadataMixin,
    AuthenticationAuditMixin,
    RevocationMixin,
    db.Model,
):
    """
    Authenticated user session.

    Every successful login creates one UserSession.

    A session owns one or more refresh tokens throughout its lifetime.
    Access tokens remain stateless and are therefore never persisted.

    Sessions provide:

    • Device management
    • Login history
    • Logout from individual devices
    • Logout everywhere
    • Concurrent session control
    • Security investigations
    • Audit support
    """

    __tablename__ = "user_sessions"

    __table_args__ = (
        db.CheckConstraint(
            "expires_at > created_at",
            name="ck_user_sessions_expiry",
        ),
        db.Index(
            "ix_user_sessions_user_active",
            "user_id",
            "revoked_at",
        ),
        db.Index(
            "ix_user_sessions_tenant",
            "tenant_id",
        ),
        db.Index(
            "ix_user_sessions_expires",
            "expires_at",
        ),
    )

    # ------------------------------------------------------------------
    # Ownership
    # ------------------------------------------------------------------

    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    branch_id = db.Column(
        db.String(36),
        db.ForeignKey("branches.id"),
        index=True,
    )

    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Session State
    # ------------------------------------------------------------------

    status = db.Column(
        db.Enum(
            SessionStatus,
            native_enum=False,
            length=20,
        ),
        nullable=False,
        default=SessionStatus.ACTIVE,
        index=True,
    )

    expires_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    last_activity_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        index=True,
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    user = db.relationship(
        "User",
        back_populates="sessions",
        lazy="selectin",
    )

    refresh_tokens = db.relationship(
        "RefreshToken",
        back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    revoked_by = db.relationship(
        "User",
        foreign_keys=[RevocationMixin.revoked_by_user_id],
        lazy="selectin",
    )

    # ------------------------------------------------------------------
    # Computed Properties
    # ------------------------------------------------------------------

    @property
    def is_active(self) -> bool:
        """
        True if the session is currently valid.
        """
        return (
            self.status == SessionStatus.ACTIVE
            and not self.is_revoked
            and not self.is_expired
        )

    @property
    def is_expired(self) -> bool:
        """
        True if the session lifetime has elapsed.
        """
        return datetime.now(UTC) >= self.expires_at

    @property
    def duration(self):
        """
        Total configured session lifetime.
        """
        return self.expires_at - self.created_at

    @property
    def idle_time(self):
        """
        Time since the last authenticated activity.
        """
        return datetime.now(UTC) - self.last_activity_at

    # ------------------------------------------------------------------
    # Domain Methods
    # ------------------------------------------------------------------

    def touch(self) -> None:
        """
        Update last activity timestamp.
        """
        self.last_activity_at = datetime.now(UTC)

    def revoke(
        self,
        *,
        reason: TokenRevocationReason,
        revoked_by_user_id: str | None = None,
    ) -> None:
        """
        Revoke this session.
        """

        if self.is_revoked:
            return

        self.revoked_at = datetime.now(UTC)
        self.revoked_by_user_id = revoked_by_user_id
        self.revoke_reason = reason
        self.status = SessionStatus.REVOKED

    def expire(self) -> None:
        """
        Mark session as expired.

        Used by scheduled cleanup jobs.
        """

        self.status = SessionStatus.EXPIRED

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"<UserSession "
            f"id={self.id} "
            f"user={self.user_id} "
            f"status={self.status.value}>"
        )

# ============================================================================
# Login Attempts
# ============================================================================


class LoginAttempt(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    db.Model,
):
    """
    Immutable authentication attempt log.

    Every authentication attempt—successful or failed—is persisted to
    support account lockout, brute-force protection, security auditing,
    and operational reporting.

    Records are append-only and may be purged according to the configured
    retention policy.
    """

    __tablename__ = "login_attempts"

    __table_args__ = (
        db.Index(
            "ix_login_attempts_email",
            "email",
        ),
        db.Index(
            "ix_login_attempts_tenant",
            "tenant_id",
        ),
        db.Index(
            "ix_login_attempts_ip",
            "ip_address",
        ),
        db.Index(
            "ix_login_attempts_successful",
            "successful",
        ),
        db.Index(
            "ix_login_attempts_created",
            "created_at",
        ),
        db.Index(
            "ix_login_attempts_email_created",
            "email",
            "created_at",
        ),
        db.Index(
            "ix_login_attempts_email_success_created",
            "email",
            "successful",
            "created_at",
        ),
    )

    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "tenants.id",
            ondelete="CASCADE",
        ),
        nullable=True,
        index=True,
    )

    email = db.Column(
        db.String(255),
        nullable=False,
        index=True,
    )

    ip_address = db.Column(
        db.String(64),
        nullable=True,
        index=True,
    )

    user_agent = db.Column(
        db.Text,
        nullable=True,
    )

    successful = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    failure_reason = db.Column(
        db.String(255),
        nullable=True,
    )

    tenant = db.relationship(
        "Tenant",
        lazy="joined",
    )

    def __repr__(self) -> str:
        return (
            f"<LoginAttempt "
            f"email={self.email!r} "
            f"successful={self.successful}>"
        )


# ============================================================================
# Refresh Tokens
# ============================================================================


class RefreshToken(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    RevocationMixin,
    db.Model,
):
    """
    Refresh token persisted in the database.

    Hela360 implements rotating refresh tokens.

    Every refresh operation:

        Old Token  -----------> Revoked
                     |
                     +-------> New Refresh Token

    All tokens belonging to the same login chain share a
    common token family, allowing replay attack detection and
    family-wide revocation.

    Access tokens remain stateless JWTs and are never stored.
    """

    __tablename__ = "refresh_tokens"

    __table_args__ = (
        db.UniqueConstraint(
            "jwt_id",
            name="uq_refresh_tokens_jti",
        ),
        db.CheckConstraint(
            "expires_at > created_at",
            name="ck_refresh_tokens_expiry",
        ),
        db.Index(
            "ix_refresh_tokens_family",
            "token_family",
        ),
        db.Index(
            "ix_refresh_tokens_user",
            "user_id",
        ),
        db.Index(
            "ix_refresh_tokens_session",
            "session_id",
        ),
        db.Index(
            "ix_refresh_tokens_expires",
            "expires_at",
        ),
        db.Index(
            "ix_refresh_tokens_active",
            "revoked_at",
            "expires_at",
        ),
    )

    # ------------------------------------------------------------------
    # Ownership
    # ------------------------------------------------------------------

    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    session_id = db.Column(
        db.String(36),
        db.ForeignKey("user_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # JWT Metadata
    # ------------------------------------------------------------------

    jwt_id = db.Column(
        db.String(64),
        nullable=False,
        unique=True,
        index=True,
    )

    token_family = db.Column(
        db.String(64),
        nullable=False,
        index=True,
    )

    expires_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Rotation
    # ------------------------------------------------------------------

    parent_token_id = db.Column(
        db.String(36),
        db.ForeignKey("refresh_tokens.id"),
        index=True,
    )

    replaced_at = db.Column(
        db.DateTime(timezone=True),
        index=True,
    )

    last_used_at = db.Column(
        db.DateTime(timezone=True),
        index=True,
    )

    # ------------------------------------------------------------------
    # Device / Client
    # ------------------------------------------------------------------

    ip_address = db.Column(
        db.String(64),
    )

    last_ip_address = db.Column(
        db.String(64),
    )

    user_agent = db.Column(
        db.Text,
    )

    device_name = db.Column(
        db.String(150),
    )

    device_fingerprint = db.Column(
        db.String(255),
        index=True,
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    user = db.relationship(
        "User",
        back_populates="refresh_tokens",
        lazy="selectin",
    )

    session = db.relationship(
        "UserSession",
        back_populates="refresh_tokens",
        lazy="selectin",
    )

    parent = db.relationship(
        "RefreshToken",
        remote_side="RefreshToken.id",
        back_populates="children",
        lazy="selectin",
    )

    children = db.relationship(
        "RefreshToken",
        back_populates="parent",
        lazy="selectin",
    )

    revoked_by = db.relationship(
        "User",
        foreign_keys=[RevocationMixin.revoked_by_user_id],
        lazy="selectin",
    )

    # ------------------------------------------------------------------
    # Computed Properties
    # ------------------------------------------------------------------

    @property
    def is_expired(self) -> bool:
        """
        True if the refresh token has expired.
        """
        return datetime.now(UTC) >= self.expires_at

    @property
    def is_active(self) -> bool:
        """
        True if the refresh token may still be used.
        """
        return (
            not self.is_revoked
            and not self.is_expired
        )

    @property
    def is_rotated(self) -> bool:
        """
        True once this token has been exchanged
        for a replacement token.
        """
        return self.replaced_at is not None

    @property
    def has_children(self) -> bool:
        """
        Indicates whether this token has produced
        one or more successor tokens.
        """
        return len(self.children) > 0

    # ------------------------------------------------------------------
    # Domain Methods
    # ------------------------------------------------------------------

    def mark_used(self) -> None:
        """
        Update the last usage timestamp.
        """
        self.last_used_at = datetime.now(UTC)

    def rotate(self) -> None:
        """
        Mark this token as rotated.

        The RefreshTokenService is responsible for
        creating the replacement token.
        """
        self.replaced_at = datetime.now(UTC)

        self.revoked_at = datetime.now(UTC)

        self.revoke_reason = (
            TokenRevocationReason.TOKEN_ROTATED
        )

    def revoke(
        self,
        *,
        reason: TokenRevocationReason,
        revoked_by_user_id: str | None = None,
    ) -> None:
        """
        Revoke the refresh token.
        """

        if self.is_revoked:
            return

        self.revoked_at = datetime.now(UTC)
        self.revoked_by_user_id = revoked_by_user_id
        self.revoke_reason = reason

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"<RefreshToken "
            f"id={self.id} "
            f"family={self.token_family} "
            f"active={self.is_active}>"
        )

# ============================================================================
# Password Reset Tokens
# ============================================================================

class PasswordResetToken(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    """
    One-time password reset token.

    A reset token is issued when a user requests a password reset and
    remains valid until it expires or is consumed.

    Security Features
    -----------------
    • Random cryptographically secure token
    • Hashed before persistence
    • Single-use
    • Expiration timestamp
    • Revocation support
    • Tenant isolation
    • Audit friendly
    """

    __tablename__ = "password_reset_tokens"

    __table_args__ = (
        db.Index(
            "ix_password_reset_lookup",
            "tenant_id",
            "token_hash",
        ),
        db.Index(
            "ix_password_reset_user",
            "user_id",
        ),
        db.CheckConstraint(
            "expires_at > created_at",
            name="ck_password_reset_expiry",
        ),
    )

    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    token_hash = db.Column(
        db.String(255),
        nullable=False,
        unique=True,
    )

    expires_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    used_at = db.Column(
        db.DateTime(timezone=True),
    )

    revoked_at = db.Column(
        db.DateTime(timezone=True),
    )

    requested_ip = db.Column(
        db.String(64),
    )

    requested_user_agent = db.Column(
        db.Text,
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    user = db.relationship(
        "User",
        back_populates="password_reset_tokens",
        lazy="joined",
    )

    # ------------------------------------------------------------------
    # Derived Properties
    # ------------------------------------------------------------------

    @property
    def is_used(self) -> bool:
        """Return True if this reset token has already been consumed."""
        return self.used_at is not None

    @property
    def is_revoked(self) -> bool:
        """Return True if this reset token has been revoked."""
        return self.revoked_at is not None

    @property
    def is_expired(self) -> bool:
        """Return True if the reset token has expired."""
        return self.expires_at <= utcnow()

    @property
    def is_active(self) -> bool:
        """Return True if this token may still be used."""
        return (
            not self.is_used
            and not self.is_revoked
            and not self.is_expired
        )

    # ------------------------------------------------------------------
    # Lifecycle Helpers
    # ------------------------------------------------------------------

    def mark_used(self) -> None:
        """Mark this reset token as consumed."""
        if self.used_at is None:
            self.used_at = utcnow()

    def revoke(self) -> None:
        """Revoke this reset token."""
        if self.revoked_at is None:
            self.revoked_at = utcnow()

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            "<PasswordResetToken("
            f"id={self.id}, "
            f"user={self.user_id}, "
            f"active={self.is_active}"
            ")>"
        )

# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    # Enums
    "SessionStatus",
    "TokenStatus",
    "LoginStatus",

    # Models
    "UserSession",
    "RefreshToken",
    "PasswordResetToken",
    "LoginAttempt",
]        