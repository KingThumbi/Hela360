"""Normalize IAM indexes

Revision ID: ade87739755f
Revises: a7b8c9d0e1f2
Create Date: 2026-08-13 16:48:17.517186

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ade87739755f'
down_revision = 'a7b8c9d0e1f2'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index(
        "ix_login_attempts_created_at",
        table_name="login_attempts",
    )

    op.drop_index(
        "ix_login_attempts_ip_address",
        table_name="login_attempts",
    )

    op.drop_index(
        "ix_login_attempts_tenant_id",
        table_name="login_attempts",
    )

    op.drop_index(
        "ix_refresh_tokens_jwt_id",
        table_name="refresh_tokens",
    )


def downgrade():
    op.create_index(
        "ix_refresh_tokens_jwt_id",
        "refresh_tokens",
        ["jwt_id"],
        unique=False,
    )

    op.create_index(
        "ix_login_attempts_tenant_id",
        "login_attempts",
        ["tenant_id"],
        unique=False,
    )

    op.create_index(
        "ix_login_attempts_ip_address",
        "login_attempts",
        ["ip_address"],
        unique=False,
    )

    op.create_index(
        "ix_login_attempts_created_at",
        "login_attempts",
        ["created_at"],
        unique=False,
    )