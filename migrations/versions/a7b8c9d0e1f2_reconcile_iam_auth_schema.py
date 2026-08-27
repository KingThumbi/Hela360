"""Reconcile IAM auth schema

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-08-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "a7b8c9d0e1f2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def _drop_fk_for_columns(table_name: str, column_names: tuple[str, ...]) -> None:
    quoted_columns = ", ".join(f"'{column}'" for column in column_names)
    op.execute(
        sa.text(
            f"""
            DO $$
            DECLARE
                constraint_name text;
            BEGIN
                SELECT con.conname
                INTO constraint_name
                FROM pg_constraint con
                JOIN pg_class rel ON rel.oid = con.conrelid
                JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
                WHERE rel.relname = '{table_name}'
                  AND nsp.nspname = current_schema()
                  AND con.contype = 'f'
                  AND (
                      SELECT array_agg(att.attname::text ORDER BY keys.ordinality)
                      FROM unnest(con.conkey) WITH ORDINALITY AS keys(attnum, ordinality)
                      JOIN pg_attribute att
                        ON att.attrelid = con.conrelid
                       AND att.attnum = keys.attnum
                  ) = ARRAY[{quoted_columns}];

                IF constraint_name IS NOT NULL THEN
                    EXECUTE format('ALTER TABLE %I DROP CONSTRAINT %I', '{table_name}', constraint_name);
                END IF;
            END $$;
            """
        )
    )


def upgrade():
    session_status = sa.Enum(
        "active",
        "expired",
        "revoked",
        native_enum=False,
        length=20,
    )
    authentication_method = sa.Enum(
        "password",
        "password_mfa",
        "sso",
        "api_key",
        "service_account",
        native_enum=False,
        length=32,
    )
    authentication_level = sa.Enum(
        "normal",
        "mfa",
        "elevated",
        native_enum=False,
        length=32,
    )
    token_revocation_reason = sa.Enum(
        "logout",
        "logout_all",
        "token_rotated",
        "password_changed",
        "account_disabled",
        "admin_revoked",
        "reuse_detected",
        "security_event",
        "session_expired",
        "user_deleted",
        native_enum=False,
        length=50,
    )

    op.create_table(
        "user_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("branch_id", sa.String(length=36), nullable=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("status", session_status, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("device_name", sa.String(length=150), nullable=True),
        sa.Column("browser", sa.String(length=120), nullable=True),
        sa.Column("operating_system", sa.String(length=120), nullable=True),
        sa.Column("device_fingerprint", sa.String(length=255), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("last_ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("authentication_method", authentication_method, nullable=False),
        sa.Column("authentication_level", authentication_level, nullable=False),
        sa.Column("mfa_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("revoke_reason", token_revocation_reason, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("expires_at > created_at", name="ck_user_sessions_expiry"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.ForeignKeyConstraint(["revoked_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_sessions_branch_id"), "user_sessions", ["branch_id"])
    op.create_index(op.f("ix_user_sessions_device_fingerprint"), "user_sessions", ["device_fingerprint"])
    op.create_index(op.f("ix_user_sessions_expires_at"), "user_sessions", ["expires_at"])
    op.create_index("ix_user_sessions_expires", "user_sessions", ["expires_at"])
    op.create_index(op.f("ix_user_sessions_last_activity_at"), "user_sessions", ["last_activity_at"])
    op.create_index(op.f("ix_user_sessions_revoked_at"), "user_sessions", ["revoked_at"])
    op.create_index(op.f("ix_user_sessions_revoked_by_user_id"), "user_sessions", ["revoked_by_user_id"])
    op.create_index(op.f("ix_user_sessions_status"), "user_sessions", ["status"])
    op.create_index(op.f("ix_user_sessions_tenant_id"), "user_sessions", ["tenant_id"])
    op.create_index("ix_user_sessions_tenant", "user_sessions", ["tenant_id"])
    op.create_index(op.f("ix_user_sessions_user_id"), "user_sessions", ["user_id"])
    op.create_index("ix_user_sessions_user_active", "user_sessions", ["user_id", "revoked_at"])

    op.create_table(
        "login_attempts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("successful", sa.Boolean(), nullable=False),
        sa.Column("failure_reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_login_attempts_created_at"), "login_attempts", ["created_at"])
    op.create_index("ix_login_attempts_created", "login_attempts", ["created_at"])
    op.create_index(op.f("ix_login_attempts_email"), "login_attempts", ["email"])
    op.create_index("ix_login_attempts_email_created", "login_attempts", ["email", "created_at"])
    op.create_index(
        "ix_login_attempts_email_success_created",
        "login_attempts",
        ["email", "successful", "created_at"],
    )
    op.create_index(op.f("ix_login_attempts_ip_address"), "login_attempts", ["ip_address"])
    op.create_index("ix_login_attempts_ip", "login_attempts", ["ip_address"])
    op.create_index(op.f("ix_login_attempts_successful"), "login_attempts", ["successful"])
    op.create_index(op.f("ix_login_attempts_tenant_id"), "login_attempts", ["tenant_id"])
    op.create_index("ix_login_attempts_tenant", "login_attempts", ["tenant_id"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("jwt_id", sa.String(length=64), nullable=False),
        sa.Column("token_family", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("parent_token_id", sa.String(length=36), nullable=True),
        sa.Column("replaced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("last_ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("device_name", sa.String(length=150), nullable=True),
        sa.Column("device_fingerprint", sa.String(length=255), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("revoke_reason", token_revocation_reason, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("expires_at > created_at", name="ck_refresh_tokens_expiry"),
        sa.ForeignKeyConstraint(["parent_token_id"], ["refresh_tokens.id"]),
        sa.ForeignKeyConstraint(["revoked_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["user_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("jwt_id", name="uq_refresh_tokens_jti"),
    )
    op.create_index("ix_refresh_tokens_active", "refresh_tokens", ["revoked_at", "expires_at"])
    op.create_index(op.f("ix_refresh_tokens_device_fingerprint"), "refresh_tokens", ["device_fingerprint"])
    op.create_index(op.f("ix_refresh_tokens_expires_at"), "refresh_tokens", ["expires_at"])
    op.create_index("ix_refresh_tokens_expires", "refresh_tokens", ["expires_at"])
    op.create_index("ix_refresh_tokens_family", "refresh_tokens", ["token_family"])
    op.create_index(op.f("ix_refresh_tokens_jwt_id"), "refresh_tokens", ["jwt_id"])
    op.create_index(op.f("ix_refresh_tokens_last_used_at"), "refresh_tokens", ["last_used_at"])
    op.create_index(op.f("ix_refresh_tokens_parent_token_id"), "refresh_tokens", ["parent_token_id"])
    op.create_index(op.f("ix_refresh_tokens_replaced_at"), "refresh_tokens", ["replaced_at"])
    op.create_index(op.f("ix_refresh_tokens_revoked_at"), "refresh_tokens", ["revoked_at"])
    op.create_index(op.f("ix_refresh_tokens_revoked_by_user_id"), "refresh_tokens", ["revoked_by_user_id"])
    op.create_index("ix_refresh_tokens_session", "refresh_tokens", ["session_id"])
    op.create_index(op.f("ix_refresh_tokens_session_id"), "refresh_tokens", ["session_id"])
    op.create_index(op.f("ix_refresh_tokens_tenant_id"), "refresh_tokens", ["tenant_id"])
    op.create_index(op.f("ix_refresh_tokens_token_family"), "refresh_tokens", ["token_family"])
    op.create_index("ix_refresh_tokens_user", "refresh_tokens", ["user_id"])
    op.create_index(op.f("ix_refresh_tokens_user_id"), "refresh_tokens", ["user_id"])

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("requested_ip", sa.String(length=64), nullable=True),
        sa.Column("requested_user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("expires_at > created_at", name="ck_password_reset_expiry"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(op.f("ix_password_reset_tokens_expires_at"), "password_reset_tokens", ["expires_at"])
    op.create_index(op.f("ix_password_reset_tokens_tenant_id"), "password_reset_tokens", ["tenant_id"])
    op.create_index(op.f("ix_password_reset_tokens_user_id"), "password_reset_tokens", ["user_id"])
    op.create_index("ix_password_reset_lookup", "password_reset_tokens", ["tenant_id", "token_hash"])
    op.create_index("ix_password_reset_user", "password_reset_tokens", ["user_id"])

    _drop_fk_for_columns("role_permissions", ("role_id",))
    _drop_fk_for_columns("role_permissions", ("permission_id",))
    op.add_column("role_permissions", sa.Column("assigned_by_user_id", sa.String(length=36), nullable=True))
    op.add_column("role_permissions", sa.Column("assignment_reason", sa.String(length=255), nullable=True))
    op.add_column(
        "role_permissions",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.add_column(
        "role_permissions",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.alter_column("role_permissions", "created_at", server_default=None)
    op.alter_column("role_permissions", "updated_at", server_default=None)
    op.create_foreign_key(
        "fk_role_permissions_assigned_by_user_id_users",
        "role_permissions",
        "users",
        ["assigned_by_user_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_role_permissions_role_id_roles",
        "role_permissions",
        "roles",
        ["role_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_role_permissions_permission_id_permissions",
        "role_permissions",
        "permissions",
        ["permission_id"],
        ["id"],
        ondelete="CASCADE",
    )

    _drop_fk_for_columns("user_roles", ("user_id",))
    _drop_fk_for_columns("user_roles", ("role_id",))
    op.add_column("user_roles", sa.Column("assigned_by_user_id", sa.String(length=36), nullable=True))
    op.add_column("user_roles", sa.Column("assignment_reason", sa.String(length=255), nullable=True))
    op.add_column(
        "user_roles",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.add_column(
        "user_roles",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.alter_column("user_roles", "created_at", server_default=None)
    op.alter_column("user_roles", "updated_at", server_default=None)
    op.create_index("ix_user_roles_user", "user_roles", ["user_id"])
    op.create_index("ix_user_roles_role", "user_roles", ["role_id"])
    op.create_foreign_key(
        "fk_user_roles_assigned_by_user_id_users",
        "user_roles",
        "users",
        ["assigned_by_user_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_user_roles_user_id_users",
        "user_roles",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_user_roles_role_id_roles",
        "user_roles",
        "roles",
        ["role_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.add_column("audit_logs", sa.Column("session_id", sa.String(length=36), nullable=True))
    op.add_column(
        "audit_logs",
        sa.Column("status", sa.String(length=20), nullable=False, server_default="success"),
    )
    op.add_column("audit_logs", sa.Column("details", sa.JSON(), nullable=True))
    op.alter_column("audit_logs", "status", server_default=None)
    op.create_index(op.f("ix_audit_logs_session_id"), "audit_logs", ["session_id"])
    op.create_index(op.f("ix_audit_logs_status"), "audit_logs", ["status"])


def downgrade():
    _drop_fk_for_columns("user_roles", ("role_id",))
    _drop_fk_for_columns("user_roles", ("user_id",))
    _drop_fk_for_columns("user_roles", ("assigned_by_user_id",))
    op.create_foreign_key("user_roles_role_id_fkey", "user_roles", "roles", ["role_id"], ["id"])
    op.create_foreign_key("user_roles_user_id_fkey", "user_roles", "users", ["user_id"], ["id"])
    op.drop_index("ix_user_roles_role", table_name="user_roles")
    op.drop_index("ix_user_roles_user", table_name="user_roles")
    op.drop_column("user_roles", "updated_at")
    op.drop_column("user_roles", "created_at")
    op.drop_column("user_roles", "assignment_reason")
    op.drop_column("user_roles", "assigned_by_user_id")

    _drop_fk_for_columns("role_permissions", ("permission_id",))
    _drop_fk_for_columns("role_permissions", ("role_id",))
    _drop_fk_for_columns("role_permissions", ("assigned_by_user_id",))
    op.create_foreign_key("role_permissions_permission_id_fkey", "role_permissions", "permissions", ["permission_id"], ["id"])
    op.create_foreign_key("role_permissions_role_id_fkey", "role_permissions", "roles", ["role_id"], ["id"])
    op.drop_column("role_permissions", "updated_at")
    op.drop_column("role_permissions", "created_at")
    op.drop_column("role_permissions", "assignment_reason")
    op.drop_column("role_permissions", "assigned_by_user_id")

    op.drop_index(op.f("ix_audit_logs_status"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_session_id"), table_name="audit_logs")
    op.drop_column("audit_logs", "details")
    op.drop_column("audit_logs", "status")
    op.drop_column("audit_logs", "session_id")

    op.drop_index("ix_password_reset_user", table_name="password_reset_tokens")
    op.drop_index("ix_password_reset_lookup", table_name="password_reset_tokens")
    op.drop_index(op.f("ix_password_reset_tokens_user_id"), table_name="password_reset_tokens")
    op.drop_index(op.f("ix_password_reset_tokens_tenant_id"), table_name="password_reset_tokens")
    op.drop_index(op.f("ix_password_reset_tokens_expires_at"), table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")

    op.drop_index(op.f("ix_login_attempts_tenant_id"), table_name="login_attempts")
    op.drop_index("ix_login_attempts_tenant", table_name="login_attempts")
    op.drop_index(op.f("ix_login_attempts_successful"), table_name="login_attempts")
    op.drop_index("ix_login_attempts_ip", table_name="login_attempts")
    op.drop_index(op.f("ix_login_attempts_ip_address"), table_name="login_attempts")
    op.drop_index("ix_login_attempts_email_success_created", table_name="login_attempts")
    op.drop_index("ix_login_attempts_email_created", table_name="login_attempts")
    op.drop_index(op.f("ix_login_attempts_email"), table_name="login_attempts")
    op.drop_index("ix_login_attempts_created", table_name="login_attempts")
    op.drop_index(op.f("ix_login_attempts_created_at"), table_name="login_attempts")
    op.drop_table("login_attempts")

    op.drop_index(op.f("ix_refresh_tokens_user_id"), table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_user", table_name="refresh_tokens")
    op.drop_index(op.f("ix_refresh_tokens_token_family"), table_name="refresh_tokens")
    op.drop_index(op.f("ix_refresh_tokens_tenant_id"), table_name="refresh_tokens")
    op.drop_index(op.f("ix_refresh_tokens_session_id"), table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_session", table_name="refresh_tokens")
    op.drop_index(op.f("ix_refresh_tokens_revoked_by_user_id"), table_name="refresh_tokens")
    op.drop_index(op.f("ix_refresh_tokens_revoked_at"), table_name="refresh_tokens")
    op.drop_index(op.f("ix_refresh_tokens_replaced_at"), table_name="refresh_tokens")
    op.drop_index(op.f("ix_refresh_tokens_parent_token_id"), table_name="refresh_tokens")
    op.drop_index(op.f("ix_refresh_tokens_last_used_at"), table_name="refresh_tokens")
    op.drop_index(op.f("ix_refresh_tokens_jwt_id"), table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_family", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_expires", table_name="refresh_tokens")
    op.drop_index(op.f("ix_refresh_tokens_expires_at"), table_name="refresh_tokens")
    op.drop_index(op.f("ix_refresh_tokens_device_fingerprint"), table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_active", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    op.drop_index("ix_user_sessions_user_active", table_name="user_sessions")
    op.drop_index(op.f("ix_user_sessions_user_id"), table_name="user_sessions")
    op.drop_index("ix_user_sessions_tenant", table_name="user_sessions")
    op.drop_index(op.f("ix_user_sessions_tenant_id"), table_name="user_sessions")
    op.drop_index(op.f("ix_user_sessions_status"), table_name="user_sessions")
    op.drop_index(op.f("ix_user_sessions_revoked_by_user_id"), table_name="user_sessions")
    op.drop_index(op.f("ix_user_sessions_revoked_at"), table_name="user_sessions")
    op.drop_index(op.f("ix_user_sessions_last_activity_at"), table_name="user_sessions")
    op.drop_index("ix_user_sessions_expires", table_name="user_sessions")
    op.drop_index(op.f("ix_user_sessions_expires_at"), table_name="user_sessions")
    op.drop_index(op.f("ix_user_sessions_device_fingerprint"), table_name="user_sessions")
    op.drop_index(op.f("ix_user_sessions_branch_id"), table_name="user_sessions")
    op.drop_table("user_sessions")
