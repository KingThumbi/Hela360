"""
Hela360 Platform IAM Models
===========================

Platform-native identity and authorization models used by Hela360 Office.

Architectural boundaries
------------------------
* Platform IAM is global and has no tenant_id.
* Platform users are distinct from tenant User records.
* Platform roles are distinct from tenant Role records.
* Platform permissions are distinct from tenant Permission records.
* Platform role and permission assignments are auditable.
* These models do not participate in tenant authentication or tenant RBAC.
"""

from __future__ import annotations

from app.extensions import db
from app.models.base import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class PlatformUser(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    db.Model,
):
    """
    Global authenticated identity for Hela360 Office.
    """

    __tablename__ = "platform_users"

    email = db.Column(
        db.String(150),
        nullable=False,
        unique=True,
        index=True,
    )

    username = db.Column(
        db.String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    first_name = db.Column(
        db.String(100),
        nullable=False,
    )

    last_name = db.Column(
        db.String(100),
    )

    password_hash = db.Column(
        db.Text,
        nullable=False,
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    roles = db.relationship(
        "PlatformRole",
        secondary="platform_user_roles",
        primaryjoin=(
            "PlatformUser.id == "
            "PlatformUserRole.platform_user_id"
        ),
        secondaryjoin=(
            "PlatformRole.id == "
            "PlatformUserRole.platform_role_id"
        ),
        back_populates="users",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<PlatformUser "
            f"id={self.id} "
            f"username={self.username}>"
        )

    sessions = db.relationship(
        "PlatformSession",
        foreign_keys="PlatformSession.platform_user_id",
        back_populates="platform_user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    refresh_tokens = db.relationship(
        "PlatformRefreshToken",
        foreign_keys="PlatformRefreshToken.platform_user_id",
        back_populates="platform_user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )


class PlatformRole(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    db.Model,
):
    """
    Global role governing Hela360 Office access.
    """

    __tablename__ = "platform_roles"

    code = db.Column(
        db.String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    name = db.Column(
        db.String(150),
        nullable=False,
    )

    description = db.Column(
        db.Text,
    )

    is_system = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    users = db.relationship(
        "PlatformUser",
        secondary="platform_user_roles",
        primaryjoin=(
            "PlatformRole.id == "
            "PlatformUserRole.platform_role_id"
        ),
        secondaryjoin=(
            "PlatformUser.id == "
            "PlatformUserRole.platform_user_id"
        ),
        back_populates="roles",
        lazy="selectin",
    )

    permissions = db.relationship(
        "PlatformPermission",
        secondary="platform_role_permissions",
        primaryjoin=(
            "PlatformRole.id == "
            "PlatformRolePermission.platform_role_id"
        ),
        secondaryjoin=(
            "PlatformPermission.id == "
            "PlatformRolePermission.platform_permission_id"
        ),
        back_populates="roles",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<PlatformRole {self.code}>"
        )


class PlatformPermission(
    UUIDPrimaryKeyMixin,
    db.Model,
):
    """
    Atomic permission governing Hela360 Office actions.
    """

    __tablename__ = "platform_permissions"

    code = db.Column(
        db.String(150),
        nullable=False,
        unique=True,
        index=True,
    )

    name = db.Column(
        db.String(150),
        nullable=False,
    )

    module_code = db.Column(
        db.String(100),
        nullable=False,
        index=True,
    )

    description = db.Column(
        db.Text,
    )

    roles = db.relationship(
        "PlatformRole",
        secondary="platform_role_permissions",
        primaryjoin=(
            "PlatformPermission.id == "
            "PlatformRolePermission.platform_permission_id"
        ),
        secondaryjoin=(
            "PlatformRole.id == "
            "PlatformRolePermission.platform_role_id"
        ),
        back_populates="permissions",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<PlatformPermission {self.code}>"
        )


class PlatformUserRole(
    TimestampMixin,
    db.Model,
):
    """
    Auditable assignment of one PlatformRole to one PlatformUser.
    """

    __tablename__ = "platform_user_roles"

    __table_args__ = (
        db.Index(
            "ix_platform_user_roles_user",
            "platform_user_id",
        ),
        db.Index(
            "ix_platform_user_roles_role",
            "platform_role_id",
        ),
    )

    platform_user_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "platform_users.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    platform_role_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "platform_roles.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    assigned_by_platform_user_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "platform_users.id",
        ),
        nullable=True,
        index=True,
    )

    assignment_reason = db.Column(
        db.String(255),
    )

    user = db.relationship(
        "PlatformUser",
        foreign_keys=[platform_user_id],
        overlaps="roles,users",
    )

    role = db.relationship(
        "PlatformRole",
        foreign_keys=[platform_role_id],
        overlaps="roles,users",
    )

    assigned_by = db.relationship(
        "PlatformUser",
        foreign_keys=[
            assigned_by_platform_user_id
        ],
    )

    def __repr__(self) -> str:
        return (
            f"<PlatformUserRole "
            f"user={self.platform_user_id} "
            f"role={self.platform_role_id}>"
        )


class PlatformRolePermission(
    TimestampMixin,
    db.Model,
):
    """
    Auditable permission assignment to one PlatformRole.
    """

    __tablename__ = "platform_role_permissions"

    __table_args__ = (
        db.Index(
            "ix_platform_role_permissions_role",
            "platform_role_id",
        ),
        db.Index(
            "ix_platform_role_permissions_permission",
            "platform_permission_id",
        ),
    )

    platform_role_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "platform_roles.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    platform_permission_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "platform_permissions.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    assigned_by_platform_user_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "platform_users.id",
        ),
        nullable=True,
        index=True,
    )

    assignment_reason = db.Column(
        db.String(255),
    )

    role = db.relationship(
        "PlatformRole",
        foreign_keys=[platform_role_id],
        overlaps="permissions,roles",
    )

    permission = db.relationship(
        "PlatformPermission",
        foreign_keys=[platform_permission_id],
        overlaps="permissions,roles",
    )

    assigned_by = db.relationship(
        "PlatformUser",
        foreign_keys=[
            assigned_by_platform_user_id
        ],
    )

    def __repr__(self) -> str:
        return (
            f"<PlatformRolePermission "
            f"role={self.platform_role_id} "
            f"permission={self.platform_permission_id}>"
        )


__all__ = [
    "PlatformPermission",
    "PlatformRole",
    "PlatformRolePermission",
    "PlatformUser",
    "PlatformUserRole",
]
