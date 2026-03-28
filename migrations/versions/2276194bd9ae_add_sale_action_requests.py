"""add sale action requests

Revision ID: 2276194bd9ae
Revises: 8fc9a0626e01
Create Date: 2026-03-22 02:58:17.579150

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2276194bd9ae'
down_revision = '8fc9a0626e01'
branch_labels = None
depends_on = None



def upgrade():
    op.create_table(
        "sale_action_requests",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),

        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("sale_id", sa.String(length=36), nullable=False),

        sa.Column("action_type", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),

        sa.Column("requested_by", sa.String(length=36), nullable=False),
        sa.Column("approved_by", sa.String(length=36), nullable=True),
        sa.Column("rejected_by", sa.String(length=36), nullable=True),

        sa.Column("request_reason", sa.Text(), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("request_payload", sa.JSON(), nullable=True),

        sa.Column("requires_approval", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),

        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"]),
        sa.ForeignKeyConstraint(["requested_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["rejected_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_sale_action_requests_tenant_id", "sale_action_requests", ["tenant_id"])
    op.create_index("ix_sale_action_requests_sale_id", "sale_action_requests", ["sale_id"])
    op.create_index("ix_sale_action_requests_action_type", "sale_action_requests", ["action_type"])
    op.create_index("ix_sale_action_requests_status", "sale_action_requests", ["status"])
    op.create_index("ix_sale_action_requests_requested_by", "sale_action_requests", ["requested_by"])

    op.alter_column("sale_action_requests", "status", server_default=None)
    op.alter_column("sale_action_requests", "requires_approval", server_default=None)


def downgrade():
    op.drop_index("ix_sale_action_requests_requested_by", table_name="sale_action_requests")
    op.drop_index("ix_sale_action_requests_status", table_name="sale_action_requests")
    op.drop_index("ix_sale_action_requests_action_type", table_name="sale_action_requests")
    op.drop_index("ix_sale_action_requests_sale_id", table_name="sale_action_requests")
    op.drop_index("ix_sale_action_requests_tenant_id", table_name="sale_action_requests")
    op.drop_table("sale_action_requests")