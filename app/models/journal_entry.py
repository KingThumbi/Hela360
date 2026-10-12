from __future__ import annotations

from app.extensions import db
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class JournalEntry(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    """Tenant- and branch-scoped manual general-ledger journal header.

    Posted accounting amounts and journal lines are immutable through the
    application service. Reversals are represented by a separate posted entry.
    """

    __tablename__ = "journal_entries"
    __table_args__ = (
        db.UniqueConstraint(
            "tenant_id", "journal_number", name="uq_journal_entries_tenant_number"
        ),
        db.UniqueConstraint(
            "tenant_id", "reversal_of_id", name="uq_journal_entries_tenant_reversal_of"
        ),
        db.CheckConstraint(
            "status IN ('draft', 'posted')", name="ck_journal_entries_status"
        ),
        db.CheckConstraint("total_debit >= 0", name="ck_journal_entries_total_debit_nonnegative"),
        db.CheckConstraint("total_credit >= 0", name="ck_journal_entries_total_credit_nonnegative"),
        db.Index(
            "ix_journal_entries_tenant_branch_date",
            "tenant_id",
            "branch_id",
            "journal_date",
        ),
        db.Index("ix_journal_entries_tenant_status", "tenant_id", "status"),
    )

    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id = db.Column(db.String(36), db.ForeignKey("branches.id"), nullable=False, index=True)
    journal_number = db.Column(db.String(30), nullable=False)
    journal_date = db.Column(db.Date, nullable=False, index=True)
    description = db.Column(db.String(500), nullable=False)
    reference = db.Column(db.String(100), nullable=True)
    currency = db.Column(db.String(3), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="draft", index=True)
    total_debit = db.Column(db.Numeric(18, 2), nullable=False, default=0)
    total_credit = db.Column(db.Numeric(18, 2), nullable=False, default=0)
    created_by = db.Column(db.String(36), nullable=True)
    updated_by = db.Column(db.String(36), nullable=True)
    posted_by = db.Column(db.String(36), nullable=True)
    posted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    reversal_of_id = db.Column(
        db.String(36),
        db.ForeignKey("journal_entries.id", ondelete="RESTRICT"),
        nullable=True,
    )

    tenant = db.relationship("Tenant", foreign_keys=[tenant_id])
    branch = db.relationship("Branch", foreign_keys=[branch_id])
    lines = db.relationship(
        "JournalEntryLine",
        back_populates="journal_entry",
        cascade="all, delete-orphan",
        order_by="JournalEntryLine.line_number",
        lazy="selectin",
    )
    reversal_of = db.relationship(
        "JournalEntry",
        remote_side="JournalEntry.id",
        foreign_keys=[reversal_of_id],
        back_populates="reversal_entries",
    )
    reversal_entries = db.relationship(
        "JournalEntry",
        foreign_keys=[reversal_of_id],
        back_populates="reversal_of",
        lazy="selectin",
    )


class JournalEntryLine(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    """A single debit or credit row within a journal entry."""

    __tablename__ = "journal_entry_lines"
    __table_args__ = (
        db.UniqueConstraint(
            "journal_entry_id", "line_number", name="uq_journal_entry_lines_entry_number"
        ),
        db.CheckConstraint("line_number >= 1", name="ck_journal_entry_lines_line_number_positive"),
        db.CheckConstraint(
            "debit >= 0 AND credit >= 0 AND "
            "((debit > 0 AND credit = 0) OR (credit > 0 AND debit = 0))",
            name="ck_journal_entry_lines_one_positive_side",
        ),
        db.Index("ix_journal_entry_lines_tenant_account", "tenant_id", "account_id"),
    )

    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    journal_entry_id = db.Column(
        db.String(36),
        db.ForeignKey("journal_entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_id = db.Column(db.String(36), db.ForeignKey("chart_of_accounts.id"), nullable=False, index=True)
    line_number = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=True)
    debit = db.Column(db.Numeric(18, 2), nullable=False, default=0)
    credit = db.Column(db.Numeric(18, 2), nullable=False, default=0)

    journal_entry = db.relationship("JournalEntry", back_populates="lines")
    account = db.relationship("ChartOfAccount", foreign_keys=[account_id])
