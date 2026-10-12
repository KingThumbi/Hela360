"""Finance checkpoint 3: manual journal entries

Revision ID: a16d7b3c9e42
Revises: ddd36b184c40
Create Date: 2026-10-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "a16d7b3c9e42"
down_revision = "ddd36b184c40"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "journal_entries",
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("branch_id", sa.String(length=36), nullable=False),
        sa.Column("journal_number", sa.String(length=30), nullable=False),
        sa.Column("journal_date", sa.Date(), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("reference", sa.String(length=100), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("total_debit", sa.Numeric(18, 2), nullable=False),
        sa.Column("total_credit", sa.Numeric(18, 2), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("posted_by", sa.String(length=36), nullable=True),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reversal_of_id", sa.String(length=36), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('draft', 'posted')", name="ck_journal_entries_status"),
        sa.CheckConstraint("total_debit >= 0", name="ck_journal_entries_total_debit_nonnegative"),
        sa.CheckConstraint("total_credit >= 0", name="ck_journal_entries_total_credit_nonnegative"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], name="fk_journal_entries_branch_id_branches"),
        sa.ForeignKeyConstraint(["reversal_of_id"], ["journal_entries.id"], name="fk_journal_entries_reversal_of_id_journal_entries", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_journal_entries_tenant_id_tenants"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "journal_number", name="uq_journal_entries_tenant_number"),
        sa.UniqueConstraint("tenant_id", "reversal_of_id", name="uq_journal_entries_tenant_reversal_of"),
    )
    op.create_index("ix_journal_entries_tenant_id", "journal_entries", ["tenant_id"], unique=False)
    op.create_index("ix_journal_entries_branch_id", "journal_entries", ["branch_id"], unique=False)
    op.create_index("ix_journal_entries_journal_date", "journal_entries", ["journal_date"], unique=False)
    op.create_index("ix_journal_entries_status", "journal_entries", ["status"], unique=False)
    op.create_index("ix_journal_entries_tenant_branch_date", "journal_entries", ["tenant_id", "branch_id", "journal_date"], unique=False)
    op.create_index("ix_journal_entries_tenant_status", "journal_entries", ["tenant_id", "status"], unique=False)

    op.create_table(
        "journal_entry_lines",
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("journal_entry_id", sa.String(length=36), nullable=False),
        sa.Column("account_id", sa.String(length=36), nullable=False),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("debit", sa.Numeric(18, 2), nullable=False),
        sa.Column("credit", sa.Numeric(18, 2), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("line_number >= 1", name="ck_journal_entry_lines_line_number_positive"),
        sa.CheckConstraint(
            "debit >= 0 AND credit >= 0 AND ((debit > 0 AND credit = 0) OR (credit > 0 AND debit = 0))",
            name="ck_journal_entry_lines_one_positive_side",
        ),
        sa.ForeignKeyConstraint(["account_id"], ["chart_of_accounts.id"], name="fk_journal_entry_lines_account_id_chart_of_accounts"),
        sa.ForeignKeyConstraint(["journal_entry_id"], ["journal_entries.id"], name="fk_journal_entry_lines_journal_entry_id_journal_entries", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_journal_entry_lines_tenant_id_tenants"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("journal_entry_id", "line_number", name="uq_journal_entry_lines_entry_number"),
    )
    op.create_index("ix_journal_entry_lines_tenant_id", "journal_entry_lines", ["tenant_id"], unique=False)
    op.create_index("ix_journal_entry_lines_journal_entry_id", "journal_entry_lines", ["journal_entry_id"], unique=False)
    op.create_index("ix_journal_entry_lines_account_id", "journal_entry_lines", ["account_id"], unique=False)
    op.create_index("ix_journal_entry_lines_tenant_account", "journal_entry_lines", ["tenant_id", "account_id"], unique=False)


def downgrade():
    op.drop_index("ix_journal_entry_lines_tenant_account", table_name="journal_entry_lines")
    op.drop_index("ix_journal_entry_lines_account_id", table_name="journal_entry_lines")
    op.drop_index("ix_journal_entry_lines_journal_entry_id", table_name="journal_entry_lines")
    op.drop_index("ix_journal_entry_lines_tenant_id", table_name="journal_entry_lines")
    op.drop_table("journal_entry_lines")
    op.drop_index("ix_journal_entries_tenant_status", table_name="journal_entries")
    op.drop_index("ix_journal_entries_tenant_branch_date", table_name="journal_entries")
    op.drop_index("ix_journal_entries_status", table_name="journal_entries")
    op.drop_index("ix_journal_entries_journal_date", table_name="journal_entries")
    op.drop_index("ix_journal_entries_branch_id", table_name="journal_entries")
    op.drop_index("ix_journal_entries_tenant_id", table_name="journal_entries")
    op.drop_table("journal_entries")
