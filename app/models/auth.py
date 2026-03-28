# app/models/auth.py
from flask_login import UserMixin
from app.extensions import db
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

class User(UUIDPrimaryKeyMixin, TimestampMixin, UserMixin, db.Model):
    __tablename__ = "users"
    __table_args__ = (
        db.UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
        db.UniqueConstraint("tenant_id", "username", name="uq_users_tenant_username"),
    )

    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id = db.Column(db.String(36), db.ForeignKey("branches.id"), nullable=True, index=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(150))
    phone = db.Column(db.String(50))
    username = db.Column(db.String(100))
    password_hash = db.Column(db.Text, nullable=False)
    is_owner = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)


class Role(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "roles"
    __table_args__ = (
        db.UniqueConstraint("tenant_id", "code", name="uq_roles_tenant_code"),
    )

    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    is_system = db.Column(db.Boolean, nullable=False, default=False)


class Permission(UUIDPrimaryKeyMixin, db.Model):
    __tablename__ = "permissions"

    code = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    module_code = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)


class RolePermission(db.Model):
    __tablename__ = "role_permissions"

    role_id = db.Column(db.String(36), db.ForeignKey("roles.id"), primary_key=True)
    permission_id = db.Column(db.String(36), db.ForeignKey("permissions.id"), primary_key=True)


class UserRole(db.Model):
    __tablename__ = "user_roles"

    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), primary_key=True)
    role_id = db.Column(db.String(36), db.ForeignKey("roles.id"), primary_key=True)