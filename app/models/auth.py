# app/models/auth.py

from flask_login import UserMixin

from app.extensions import db
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


# ============================================================================
# Users
# ============================================================================

class User(UUIDPrimaryKeyMixin, TimestampMixin, UserMixin, db.Model):
    """
    Tenant user.

    Represents an authenticated user belonging to a tenant.
    Authentication state (sessions, refresh tokens, password reset tokens)
    is stored in app.models.security.
    """

    __tablename__ = "users"

    __table_args__ = (
        db.UniqueConstraint(
            "tenant_id",
            "email",
            name="uq_users_tenant_email",
        ),
        db.UniqueConstraint(
            "tenant_id",
            "username",
            name="uq_users_tenant_username",
        ),
    )

    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    branch_id = db.Column(
        db.String(36),
        db.ForeignKey("branches.id"),
        index=True,
    )

    first_name = db.Column(
        db.String(100),
        nullable=False,
    )

    last_name = db.Column(
        db.String(100),
    )

    email = db.Column(
        db.String(150),
    )

    phone = db.Column(
        db.String(50),
    )

    username = db.Column(
        db.String(100),
    )

    password_hash = db.Column(
        db.Text,
        nullable=False,
    )

    is_owner = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    roles = db.relationship(
        "Role",
        secondary="user_roles",
        back_populates="users",
        lazy="selectin",
    )

    sessions = db.relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    refresh_tokens = db.relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    password_reset_tokens = db.relationship(
        "PasswordResetToken",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<User "
            f"id={self.id} "
            f"username={self.username}>"
        )


# ============================================================================
# Roles
# ============================================================================

class Role(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    """
    Role assigned to users within a tenant.
    """

    __tablename__ = "roles"

    __table_args__ = (
        db.UniqueConstraint(
            "tenant_id",
            "code",
            name="uq_roles_tenant_code",
        ),
    )

    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    name = db.Column(
        db.String(100),
        nullable=False,
    )

    code = db.Column(
        db.String(50),
        nullable=False,
    )

    description = db.Column(
        db.Text,
    )

    is_system = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )

    users = db.relationship(
        "User",
        secondary="user_roles",
        back_populates="roles",
        lazy="selectin",
    )

    permissions = db.relationship(
        "Permission",
        secondary="role_permissions",
        back_populates="roles",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Role {self.code}>"


# ============================================================================
# Permissions
# ============================================================================

class Permission(UUIDPrimaryKeyMixin, db.Model):
    """
    Atomic permission assignable to one or more roles.
    """

    __tablename__ = "permissions"

    code = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
    )

    name = db.Column(
        db.String(150),
        nullable=False,
    )

    module_code = db.Column(
        db.String(50),
        nullable=False,
    )

    description = db.Column(
        db.Text,
    )

    roles = db.relationship(
        "Role",
        secondary="role_permissions",
        back_populates="permissions",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Permission {self.code}>"


# ============================================================================
# Role-Permission Assignments
# ============================================================================

class RolePermission(TimestampMixin, db.Model):
    """
    Associates permissions with roles.

    Keeping this as an explicit entity rather than an anonymous junction table
    allows Hela360 to audit when permissions were granted, by whom, and to
    extend the model in future without redesigning the schema.
    """

    __tablename__ = "role_permissions"

    __table_args__ = (
        db.UniqueConstraint(
            "role_id",
            "permission_id",
            name="uq_role_permission",
        ),
    )

    role_id = db.Column(
        db.String(36),
        db.ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    )

    permission_id = db.Column(
        db.String(36),
        db.ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    )

    assigned_by_user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=True,
    )

    assignment_reason = db.Column(
        db.String(255),
    )

    role = db.relationship(
        "Role",
        foreign_keys=[role_id],
    )

    permission = db.relationship(
        "Permission",
        foreign_keys=[permission_id],
    )

    assigned_by = db.relationship(
        "User",
        foreign_keys=[assigned_by_user_id],
    )

    def __repr__(self) -> str:
        return (
            f"<RolePermission "
            f"role={self.role_id} "
            f"permission={self.permission_id}>"
        )


# ============================================================================
# User-Role Assignments
# ============================================================================

class UserRole(TimestampMixin, db.Model):
    """
    Associates users with roles.

    Role assignments are auditable and may later support temporary assignments,
    delegated administration and approval workflows without requiring schema
    changes.
    """

    __tablename__ = "user_roles"

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "role_id",
            name="uq_user_role",
        ),
        db.Index(
            "ix_user_roles_user",
            "user_id",
        ),
        db.Index(
            "ix_user_roles_role",
            "role_id",
        ),
    )

    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    role_id = db.Column(
        db.String(36),
        db.ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    )

    assigned_by_user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=True,
    )

    assignment_reason = db.Column(
        db.String(255),
    )

    user = db.relationship(
        "User",
        foreign_keys=[user_id],
    )

    role = db.relationship(
        "Role",
        foreign_keys=[role_id],
    )

    assigned_by = db.relationship(
        "User",
        foreign_keys=[assigned_by_user_id],
    )

    def __repr__(self) -> str:
        return (
            f"<UserRole "
            f"user={self.user_id} "
            f"role={self.role_id}>"
        )