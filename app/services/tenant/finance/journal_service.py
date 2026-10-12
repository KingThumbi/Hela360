from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import (
    Branch,
    ChartOfAccount,
    JournalEntry,
    JournalEntryLine,
    NumberSequence,
    Tenant,
)
from app.services.common.audit_actions import AuditAction
from app.services.common.audit_modules import AuditModule
from app.services.common.audit_service import audit_service


CENT = Decimal("0.01")
ZERO = Decimal("0.00")
MAX_AMOUNT = Decimal("9999999999999999.99")
SEQUENCE_NAMESPACE = "finance_journal"


class JournalEntryError(ValueError):
    """Base error for manual journal operations."""


class JournalEntryNotFoundError(JournalEntryError):
    """A journal does not exist within the requested tenant/scope."""


class JournalEntryConflictError(JournalEntryError):
    """A unique journal identity or reversal already exists."""


class JournalEntryStateError(JournalEntryError):
    """The operation is not valid for the journal's current state."""


class JournalEntryService:
    """Safe manual journal commands and queries.

    The caller owns commit/rollback. Drafts may be edited; posted entries are
    immutable. Reversal creates a new posted entry with opposite line sides.
    Source documents are intentionally not auto-posted by this checkpoint.
    """

    def __init__(self, session=None) -> None:
        self.session = session or db.session

    @staticmethod
    def _parse_date(value: Any, *, field: str = "journal_date") -> date:
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        try:
            return date.fromisoformat(str(value or "").strip())
        except (TypeError, ValueError) as exc:
            raise JournalEntryError(f"{field} must be an ISO date (YYYY-MM-DD).") from exc

    @staticmethod
    def _text(value: Any, *, field: str, required: bool, max_length: int) -> str | None:
        text = str(value or "").strip()
        if required and not text:
            raise JournalEntryError(f"{field} is required.")
        if len(text) > max_length:
            raise JournalEntryError(f"{field} must not exceed {max_length} characters.")
        return text or None

    @staticmethod
    def _money(value: Any, *, field: str) -> Decimal:
        if isinstance(value, bool) or value is None:
            raise JournalEntryError(f"{field} must be a monetary amount with at most 2 decimal places.")
        try:
            amount = Decimal(str(value).strip())
        except (InvalidOperation, ValueError, AttributeError) as exc:
            raise JournalEntryError(f"{field} must be a valid monetary amount.") from exc
        if not amount.is_finite():
            raise JournalEntryError(f"{field} must be finite.")
        if amount < ZERO:
            raise JournalEntryError(f"{field} cannot be negative.")
        try:
            normalized = amount.quantize(CENT)
        except InvalidOperation as exc:
            raise JournalEntryError(f"{field} exceeds the supported amount range.") from exc
        if normalized != amount:
            raise JournalEntryError(f"{field} must not exceed 2 decimal places.")
        if normalized > MAX_AMOUNT:
            raise JournalEntryError(f"{field} exceeds the supported amount range.")
        return normalized

    def _tenant(self, tenant_id: str) -> Tenant:
        tenant = self.session.get(Tenant, tenant_id)
        if tenant is None:
            raise JournalEntryNotFoundError("Tenant not found.")
        return tenant

    def _branch(self, tenant_id: str, branch_id: str | None) -> Branch:
        if not branch_id:
            raise JournalEntryError("A branch is required for a journal entry.")
        branch = self.session.get(Branch, str(branch_id))
        if branch is None or branch.tenant_id != tenant_id:
            raise JournalEntryError("branch_id must reference a branch belonging to the authenticated tenant.")
        if not branch.is_active:
            raise JournalEntryError("The selected branch is inactive.")
        return branch

    def _next_journal_number(self, tenant_id: str) -> str:
        """Atomically reserve a tenant-scoped journal number on SQLite/PostgreSQL."""
        dialect = self.session.get_bind().dialect.name
        if dialect == "postgresql":
            from sqlalchemy.dialects.postgresql import insert as dialect_insert
        elif dialect == "sqlite":
            from sqlalchemy.dialects.sqlite import insert as dialect_insert
        else:
            sequence = self.session.scalar(
                select(NumberSequence)
                .where(
                    NumberSequence.tenant_id == tenant_id,
                    NumberSequence.namespace == SEQUENCE_NAMESPACE,
                )
                .with_for_update()
            )
            if sequence is None:
                sequence = NumberSequence(
                    tenant_id=tenant_id,
                    namespace=SEQUENCE_NAMESPACE,
                    next_value=1,
                )
                self.session.add(sequence)
                self.session.flush()
            value = int(sequence.next_value)
            sequence.next_value = value + 1
            return f"JV-{value:08d}"

        self.session.execute(
            dialect_insert(NumberSequence)
            .values(tenant_id=tenant_id, namespace=SEQUENCE_NAMESPACE, next_value=1)
            .on_conflict_do_nothing(index_elements=["tenant_id", "namespace"])
        )
        next_value = self.session.execute(
            update(NumberSequence)
            .where(
                NumberSequence.tenant_id == tenant_id,
                NumberSequence.namespace == SEQUENCE_NAMESPACE,
            )
            .values(next_value=NumberSequence.next_value + 1)
            .returning(NumberSequence.next_value)
        ).scalar_one()
        return f"JV-{int(next_value) - 1:08d}"

    def _entry_query(
        self,
        tenant_id: str,
        entry_id: str,
        branch_id: str | None = None,
        *,
        for_update: bool = False,
    ):
        query = (
            select(JournalEntry)
            .options(
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account),
                selectinload(JournalEntry.reversal_entries),
                selectinload(JournalEntry.reversal_of),
            )
            .where(JournalEntry.tenant_id == tenant_id, JournalEntry.id == entry_id)
        )
        if branch_id is not None:
            query = query.where(JournalEntry.branch_id == branch_id)
        if for_update:
            query = query.with_for_update()
        return query

    def get(
        self,
        tenant_id: str,
        entry_id: str,
        *,
        branch_id: str | None = None,
        for_update: bool = False,
    ) -> JournalEntry:
        entry = self.session.scalar(
            self._entry_query(tenant_id, entry_id, branch_id, for_update=for_update)
        )
        if entry is None:
            raise JournalEntryNotFoundError("Journal entry not found.")
        return entry

    def list(
        self,
        tenant_id: str,
        *,
        branch_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[JournalEntry]:
        query = (
            select(JournalEntry)
            .options(
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account),
                selectinload(JournalEntry.reversal_entries),
                selectinload(JournalEntry.reversal_of),
            )
            .where(JournalEntry.tenant_id == tenant_id)
        )
        if branch_id is not None:
            query = query.where(JournalEntry.branch_id == branch_id)
        if status:
            normalized = status.strip().lower()
            if normalized not in {"draft", "posted"}:
                raise JournalEntryError("status must be either draft or posted.")
            query = query.where(JournalEntry.status == normalized)
        query = query.order_by(JournalEntry.journal_date.desc(), JournalEntry.created_at.desc()).limit(
            max(1, min(int(limit), 100))
        )
        return list(self.session.scalars(query))

    def _validate_lines(
        self,
        tenant_id: str,
        branch_id: str,
        tenant_currency: str,
        lines: Any,
    ) -> tuple[list[dict[str, Any]], Decimal, Decimal]:
        if not isinstance(lines, list) or len(lines) < 2:
            raise JournalEntryError("A journal entry must contain at least two lines.")
        if len(lines) > 500:
            raise JournalEntryError("A journal entry cannot contain more than 500 lines.")

        normalized: list[dict[str, Any]] = []
        total_debit = ZERO
        total_credit = ZERO
        for index, raw_line in enumerate(lines, start=1):
            if not isinstance(raw_line, dict):
                raise JournalEntryError(f"Line {index} must be an object.")
            account_id = str(raw_line.get("account_id") or "").strip()
            if not account_id:
                raise JournalEntryError(f"Line {index}: account_id is required.")
            account = self.session.scalar(
                select(ChartOfAccount).where(
                    ChartOfAccount.id == account_id,
                    ChartOfAccount.tenant_id == tenant_id,
                )
            )
            if account is None:
                raise JournalEntryError(f"Line {index}: account was not found in this tenant.")
            if not account.is_active:
                raise JournalEntryError(f"Line {index}: account {account.account_code} is inactive.")
            if account.branch_id not in (None, branch_id):
                raise JournalEntryError(f"Line {index}: account belongs to another branch.")
            if (account.currency or tenant_currency).upper() != tenant_currency.upper():
                raise JournalEntryError(
                    f"Line {index}: account currency does not match the tenant base currency; foreign-currency journals are not enabled in this checkpoint."
                )
            has_children = self.session.scalar(
                select(ChartOfAccount.id)
                .where(
                    ChartOfAccount.tenant_id == tenant_id,
                    ChartOfAccount.parent_id == account.id,
                )
                .limit(1)
            )
            if has_children is not None:
                raise JournalEntryError(
                    f"Line {index}: account {account.account_code} is a summary account and cannot receive postings."
                )

            debit = self._money(raw_line.get("debit", "0.00"), field=f"line {index} debit")
            credit = self._money(raw_line.get("credit", "0.00"), field=f"line {index} credit")
            if (debit > ZERO) == (credit > ZERO):
                raise JournalEntryError(
                    f"Line {index}: provide a positive debit or a positive credit, but not both."
                )
            line_description = self._text(
                raw_line.get("description"),
                field=f"line {index} description",
                required=False,
                max_length=500,
            )
            normalized.append(
                {
                    "account_id": account.id,
                    "line_number": index,
                    "description": line_description,
                    "debit": debit,
                    "credit": credit,
                }
            )
            total_debit += debit
            total_credit += credit

            if total_debit > MAX_AMOUNT:
                raise JournalEntryError(
                    "Total debit exceeds the supported journal amount range."
                )
            if total_credit > MAX_AMOUNT:
                raise JournalEntryError(
                    "Total credit exceeds the supported journal amount range."
                )

        return normalized, total_debit.quantize(CENT), total_credit.quantize(CENT)

    def _replace_lines(
        self,
        entry: JournalEntry,
        normalized_lines: list[dict[str, Any]],
        total_debit: Decimal,
        total_credit: Decimal,
    ) -> None:
        entry.lines.clear()
        self.session.flush()
        for item in normalized_lines:
            entry.lines.append(JournalEntryLine(tenant_id=entry.tenant_id, **item))
        entry.total_debit = total_debit
        entry.total_credit = total_credit
        self.session.flush()

    @staticmethod
    def snapshot(entry: JournalEntry) -> dict[str, Any]:
        return {
            "id": entry.id,
            "tenant_id": entry.tenant_id,
            "branch_id": entry.branch_id,
            "journal_number": entry.journal_number,
            "journal_date": entry.journal_date.isoformat(),
            "description": entry.description,
            "reference": entry.reference,
            "currency": entry.currency,
            "status": entry.status,
            "total_debit": format(Decimal(entry.total_debit or ZERO), ".2f"),
            "total_credit": format(Decimal(entry.total_credit or ZERO), ".2f"),
            "created_by": entry.created_by,
            "updated_by": entry.updated_by,
            "posted_by": entry.posted_by,
            "posted_at": entry.posted_at.isoformat() if entry.posted_at else None,
            "reversal_of_id": entry.reversal_of_id,
            "lines": [
                {
                    "id": line.id,
                    "line_number": line.line_number,
                    "account_id": line.account_id,
                    "account_code": line.account.account_code if line.account else None,
                    "account_name": line.account.account_name if line.account else None,
                    "description": line.description,
                    "debit": format(Decimal(line.debit or ZERO), ".2f"),
                    "credit": format(Decimal(line.credit or ZERO), ".2f"),
                }
                for line in entry.lines
            ],
        }

    def create_draft(
        self,
        tenant_id: str,
        *,
        branch_id: str,
        journal_date: Any,
        description: Any,
        reference: Any = None,
        lines: Any,
        actor_user_id: str | None = None,
    ) -> JournalEntry:
        tenant = self._tenant(tenant_id)
        branch = self._branch(tenant_id, branch_id)
        parsed_date = self._parse_date(journal_date)
        parsed_description = self._text(description, field="description", required=True, max_length=500)
        parsed_reference = self._text(reference, field="reference", required=False, max_length=100)
        normalized, debit_total, credit_total = self._validate_lines(
            tenant_id, branch.id, tenant.base_currency, lines
        )

        entry = JournalEntry(
            tenant_id=tenant_id,
            branch_id=branch.id,
            journal_number=self._next_journal_number(tenant_id),
            journal_date=parsed_date,
            description=parsed_description,
            reference=parsed_reference,
            currency=tenant.base_currency.upper(),
            status="draft",
            total_debit=debit_total,
            total_credit=credit_total,
            created_by=actor_user_id,
            updated_by=actor_user_id,
        )
        self.session.add(entry)
        self.session.flush()
        for item in normalized:
            self.session.add(JournalEntryLine(tenant_id=tenant_id, journal_entry_id=entry.id, **item))
        self.session.flush()
        entry = self.get(tenant_id, entry.id, branch_id=branch.id)
        audit_service.log(
            module=AuditModule.FINANCE,
            action=AuditAction.FINANCE_JOURNAL_CREATED,
            entity_type="JournalEntry",
            entity_id=entry.id,
            tenant_id=tenant_id,
            branch_id=branch.id,
            user_id=actor_user_id,
            new_values=self.snapshot(entry),
            commit=False,
        )
        return entry

    def update_draft(
        self,
        tenant_id: str,
        entry_id: str,
        *,
        fields: dict[str, Any],
        branch_id: str | None = None,
        actor_user_id: str | None = None,
    ) -> JournalEntry:
        allowed = {"journal_date", "description", "reference", "lines"}
        unknown = set(fields) - allowed
        if unknown:
            raise JournalEntryError(f"Unsupported journal fields: {', '.join(sorted(unknown))}.")
        entry = self.get(tenant_id, entry_id, branch_id=branch_id, for_update=True)
        if entry.status != "draft":
            raise JournalEntryStateError("Posted journal entries are immutable; create a reversal or a new journal instead.")
        if not fields:
            return entry
        old_values = self.snapshot(entry)
        tenant = self._tenant(tenant_id)
        if "journal_date" in fields:
            entry.journal_date = self._parse_date(fields["journal_date"])
        if "description" in fields:
            entry.description = self._text(fields["description"], field="description", required=True, max_length=500)
        if "reference" in fields:
            entry.reference = self._text(fields["reference"], field="reference", required=False, max_length=100)
        if "lines" in fields:
            normalized, total_debit, total_credit = self._validate_lines(
                tenant_id, entry.branch_id, tenant.base_currency, fields["lines"]
            )
            self._replace_lines(entry, normalized, total_debit, total_credit)
        entry.updated_by = actor_user_id
        self.session.flush()
        entry = self.get(tenant_id, entry.id, branch_id=branch_id)
        audit_service.log(
            module=AuditModule.FINANCE,
            action=AuditAction.FINANCE_JOURNAL_UPDATED,
            entity_type="JournalEntry",
            entity_id=entry.id,
            tenant_id=tenant_id,
            branch_id=entry.branch_id,
            user_id=actor_user_id,
            old_values=old_values,
            new_values=self.snapshot(entry),
            commit=False,
        )
        return entry

    def post(
        self,
        tenant_id: str,
        entry_id: str,
        *,
        branch_id: str | None = None,
        actor_user_id: str | None = None,
    ) -> JournalEntry:
        entry = self.get(tenant_id, entry_id, branch_id=branch_id, for_update=True)
        if entry.status != "draft":
            raise JournalEntryStateError("Only draft journal entries can be posted.")
        tenant = self._tenant(tenant_id)
        # Re-check account state and scope at posting time, not just at draft creation.
        payload_lines = [
            {
                "account_id": line.account_id,
                "description": line.description,
                "debit": str(line.debit),
                "credit": str(line.credit),
            }
            for line in entry.lines
        ]
        normalized, debit_total, credit_total = self._validate_lines(
            tenant_id, entry.branch_id, tenant.base_currency, payload_lines
        )
        if debit_total <= ZERO or credit_total <= ZERO or debit_total != credit_total:
            raise JournalEntryError(
                f"Journal must balance before posting. Debits: {debit_total:.2f}; credits: {credit_total:.2f}."
            )
        old_values = self.snapshot(entry)
        entry.total_debit = debit_total
        entry.total_credit = credit_total
        entry.status = "posted"
        entry.posted_by = actor_user_id
        entry.posted_at = datetime.now(timezone.utc)
        entry.updated_by = actor_user_id
        self.session.flush()
        entry = self.get(tenant_id, entry.id, branch_id=branch_id)
        audit_service.log(
            module=AuditModule.FINANCE,
            action=AuditAction.FINANCE_JOURNAL_POSTED,
            entity_type="JournalEntry",
            entity_id=entry.id,
            tenant_id=tenant_id,
            branch_id=entry.branch_id,
            user_id=actor_user_id,
            old_values=old_values,
            new_values=self.snapshot(entry),
            commit=False,
        )
        return entry

    def reverse(
        self,
        tenant_id: str,
        entry_id: str,
        *,
        journal_date: Any,
        reason: Any,
        branch_id: str | None = None,
        actor_user_id: str | None = None,
    ) -> JournalEntry:
        entry = self.get(tenant_id, entry_id, branch_id=branch_id, for_update=True)
        if entry.status != "posted":
            raise JournalEntryStateError("Only posted journal entries can be reversed.")
        if entry.reversal_of_id is not None:
            raise JournalEntryStateError("A reversal journal cannot itself be reversed.")
        existing_reversal_id = self.session.scalar(
            select(JournalEntry.id).where(
                JournalEntry.tenant_id == tenant_id,
                JournalEntry.reversal_of_id == entry.id,
            ).limit(1)
        )
        if existing_reversal_id is not None:
            raise JournalEntryConflictError("This journal entry already has a reversal.")

        parsed_date = self._parse_date(journal_date)
        parsed_reason = self._text(reason, field="reason", required=True, max_length=400)
        description = f"Reversal of {entry.journal_number}: {parsed_reason}"
        if len(description) > 500:
            description = description[:500]
        reversal = JournalEntry(
            tenant_id=entry.tenant_id,
            branch_id=entry.branch_id,
            journal_number=self._next_journal_number(tenant_id),
            journal_date=parsed_date,
            description=description,
            reference=entry.journal_number,
            currency=entry.currency,
            status="posted",
            total_debit=entry.total_credit,
            total_credit=entry.total_debit,
            created_by=actor_user_id,
            updated_by=actor_user_id,
            posted_by=actor_user_id,
            posted_at=datetime.now(timezone.utc),
            reversal_of_id=entry.id,
        )
        self.session.add(reversal)
        self.session.flush()
        for line in entry.lines:
            self.session.add(
                JournalEntryLine(
                    tenant_id=entry.tenant_id,
                    journal_entry_id=reversal.id,
                    account_id=line.account_id,
                    line_number=line.line_number,
                    description=line.description,
                    debit=line.credit,
                    credit=line.debit,
                )
            )
        self.session.flush()
        reversal = self.get(tenant_id, reversal.id, branch_id=entry.branch_id)
        audit_service.log(
            module=AuditModule.FINANCE,
            action=AuditAction.FINANCE_JOURNAL_REVERSED,
            entity_type="JournalEntry",
            entity_id=entry.id,
            tenant_id=tenant_id,
            branch_id=entry.branch_id,
            user_id=actor_user_id,
            old_values=self.snapshot(entry),
            new_values={
                "reversal": self.snapshot(reversal),
                "reason": parsed_reason,
            },
            details={"reversal_journal_id": reversal.id, "reversal_journal_number": reversal.journal_number},
            commit=False,
        )
        return reversal
