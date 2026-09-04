"""
Hela360 Platform Authentication Models
======================================

Persistence models for Hela360 Office authentication.

These models are deliberately separate from tenant authentication models.

Platform authentication owns:

* PlatformSession
* PlatformRefreshToken
* PlatformLoginAttempt

No platform authentication record carries tenant or branch scope.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.extensions import db
from app.models.base import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from app.models.security import (
    TokenRevocationReason,
)


def _as_utc(
    value: datetime,
) -> datetime:
    """Normalize a database datetime to UTC."""

    if value.tzinfo is None:
        return value.replace(
            tzinfo=UTC
        )

    return value.astimezone(
        UTC
    )


class PlatformSession(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    db.Model,
):
    """
    Authenticated Hela360 Office session.

    A PlatformSession belongs only to a PlatformUser and carries no tenant
    or branch scope.
    """

    __tablename__ = "platform_sessions"

    __table_args__ = (
        db.CheckConstraint(
            "expires_at > created_at",
            name="ck_platform_sessions_expiry",
        ),
        db.Index(
            "ix_platform_sessions_user",
            "platform_user_id",
        ),
        db.Index(
            "ix_platform_sessions_expires",
            "expires_at",
        ),
        db.Index(
            "ix_platform_sessions_active",
            "revoked_at",
            "expires_at",
        ),
        db.Index(
            "ix_platform_sessions_fingerprint",
            "device_fingerprint",
        ),
    )

    platform_user_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "platform_users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    expires_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
    )

    last_activity_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    device_name = db.Column(
        db.String(150),
        nullable=True,
    )

    browser = db.Column(
        db.String(150),
        nullable=True,
    )

    operating_system = db.Column(
        db.String(150),
        nullable=True,
    )

    device_fingerprint = db.Column(
        db.String(255),
        nullable=True,
    )

    ip_address = db.Column(
        db.String(64),
        nullable=True,
    )

    last_ip_address = db.Column(
        db.String(64),
        nullable=True,
    )

    user_agent = db.Column(
        db.Text,
        nullable=True,
    )

    country = db.Column(
        db.String(100),
        nullable=True,
    )

    city = db.Column(
        db.String(100),
        nullable=True,
    )

    authentication_method = db.Column(
        db.String(50),
        nullable=True,
    )

    authentication_level = db.Column(
        db.String(50),
        nullable=True,
    )

    mfa_verified_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )

    revoked_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    revoked_by_platform_user_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "platform_users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    revoke_reason = db.Column(
        db.Enum(
            TokenRevocationReason,
            name="tokenrevocationreason",
            create_type=False,
        ),
        nullable=True,
    )

    platform_user = db.relationship(
        "PlatformUser",
        foreign_keys=[
            platform_user_id,
        ],
        back_populates="sessions",
        lazy="selectin",
    )

    revoked_by = db.relationship(
        "PlatformUser",
        foreign_keys=[
            revoked_by_platform_user_id,
        ],
        lazy="selectin",
    )

    refresh_tokens = db.relationship(
        "PlatformRefreshToken",
        back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    @property
    def is_expired(self) -> bool:
        return datetime.now(UTC) >= _as_utc(
            self.expires_at
        )

    @property
    def is_active(self) -> bool:
        return (
            self.revoked_at is None
            and not self.is_expired
        )

    def touch(
        self,
        *,
        ip_address: str | None = None,
    ) -> None:
        self.last_activity_at = datetime.now(
            UTC
        )

        if ip_address is not None:
            self.last_ip_address = ip_address

    def revoke(
        self,
        *,
        reason: TokenRevocationReason,
        revoked_by_platform_user_id: str | None = None,
    ) -> None:
        if self.revoked_at is not None:
            return

        self.revoked_at = datetime.now(
            UTC
        )

        self.revoked_by_platform_user_id = (
            revoked_by_platform_user_id
        )

        self.revoke_reason = reason

    def __repr__(self) -> str:
        return (
            f"<PlatformSession "
            f"id={self.id} "
            f"user={self.platform_user_id}>"
        )


class PlatformLoginAttempt(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    db.Model,
):
    """
    Immutable Hela360 Office authentication-attempt record.
    """

    __tablename__ = "platform_login_attempts"

    __table_args__ = (
        db.Index(
            "ix_platform_login_attempts_email",
            "email",
        ),
        db.Index(
            "ix_platform_login_attempts_ip",
            "ip_address",
        ),
        db.Index(
            "ix_platform_login_attempts_successful",
            "successful",
        ),
        db.Index(
            "ix_platform_login_attempts_created",
            "created_at",
        ),
        db.Index(
            "ix_platform_login_attempts_email_created",
            "email",
            "created_at",
        ),
        db.Index(
            "ix_platform_login_attempts_email_success_created",
            "email",
            "successful",
            "created_at",
        ),
    )

    platform_user_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "platform_users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    email = db.Column(
        db.String(255),
        nullable=False,
    )

    ip_address = db.Column(
        db.String(64),
        nullable=True,
    )

    user_agent = db.Column(
        db.Text,
        nullable=True,
    )

    successful = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )

    failure_reason = db.Column(
        db.String(255),
        nullable=True,
    )

    platform_user = db.relationship(
        "PlatformUser",
        foreign_keys=[
            platform_user_id,
        ],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<PlatformLoginAttempt "
            f"email={self.email!r} "
            f"successful={self.successful}>"
        )


class PlatformRefreshToken(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    db.Model,
):
    """
    Persisted rotating refresh token for Hela360 Office authentication.
    """

    __tablename__ = "platform_refresh_tokens"

    __table_args__ = (
        db.UniqueConstraint(
            "jwt_id",
            name="uq_platform_refresh_tokens_jti",
        ),
        db.CheckConstraint(
            "expires_at > created_at",
            name="ck_platform_refresh_tokens_expiry",
        ),
        db.Index(
            "ix_platform_refresh_tokens_family",
            "token_family",
        ),
        db.Index(
            "ix_platform_refresh_tokens_user",
            "platform_user_id",
        ),
        db.Index(
            "ix_platform_refresh_tokens_session",
            "platform_session_id",
        ),
        db.Index(
            "ix_platform_refresh_tokens_expires",
            "expires_at",
        ),
        db.Index(
            "ix_platform_refresh_tokens_active",
            "revoked_at",
            "expires_at",
        ),
    )

    platform_user_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "platform_users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    platform_session_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "platform_sessions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    jwt_id = db.Column(
        db.String(64),
        nullable=False,
    )

    token_family = db.Column(
        db.String(64),
        nullable=False,
    )

    expires_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
    )

    parent_token_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "platform_refresh_tokens.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    replaced_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    last_used_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    ip_address = db.Column(
        db.String(64),
        nullable=True,
    )

    last_ip_address = db.Column(
        db.String(64),
        nullable=True,
    )

    user_agent = db.Column(
        db.Text,
        nullable=True,
    )

    device_name = db.Column(
        db.String(150),
        nullable=True,
    )

    device_fingerprint = db.Column(
        db.String(255),
        nullable=True,
    )

    revoked_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    revoked_by_platform_user_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "platform_users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    revoke_reason = db.Column(
        db.Enum(
            TokenRevocationReason,
            name="tokenrevocationreason",
            create_type=False,
        ),
        nullable=True,
    )

    platform_user = db.relationship(
        "PlatformUser",
        foreign_keys=[
            platform_user_id,
        ],
        back_populates="refresh_tokens",
        lazy="selectin",
    )

    session = db.relationship(
        "PlatformSession",
        back_populates="refresh_tokens",
        lazy="selectin",
    )

    parent = db.relationship(
        "PlatformRefreshToken",
        remote_side="PlatformRefreshToken.id",
        back_populates="children",
        lazy="selectin",
    )

    children = db.relationship(
        "PlatformRefreshToken",
        back_populates="parent",
        lazy="selectin",
    )

    revoked_by = db.relationship(
        "PlatformUser",
        foreign_keys=[
            revoked_by_platform_user_id,
        ],
        lazy="selectin",
    )

    @property
    def is_expired(self) -> bool:
        return datetime.now(UTC) >= _as_utc(
            self.expires_at
        )

    @property
    def is_active(self) -> bool:
        return (
            self.revoked_at is None
            and not self.is_expired
        )

    @property
    def is_rotated(self) -> bool:
        return self.replaced_at is not None

    def mark_used(self) -> None:
        self.last_used_at = datetime.now(
            UTC
        )

    def rotate(self) -> None:
        now = datetime.now(
            UTC
        )

        self.replaced_at = now
        self.revoked_at = now
        self.revoke_reason = (
            TokenRevocationReason.TOKEN_ROTATED
        )

    def revoke(
        self,
        *,
        reason: TokenRevocationReason,
        revoked_by_platform_user_id: str | None = None,
    ) -> None:
        if self.revoked_at is not None:
            return

        self.revoked_at = datetime.now(
            UTC
        )

        self.revoked_by_platform_user_id = (
            revoked_by_platform_user_id
        )

        self.revoke_reason = reason

    def __repr__(self) -> str:
        return (
            f"<PlatformRefreshToken "
            f"id={self.id} "
            f"jti={self.jwt_id}>"
        )


__all__ = [
    "PlatformLoginAttempt",
    "PlatformRefreshToken",
    "PlatformSession",
]
