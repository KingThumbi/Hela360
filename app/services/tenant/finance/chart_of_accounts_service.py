from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select

from app.extensions import db
from app.models import Branch, ChartOfAccount, Tenant
from app.services.common.audit_actions import AuditAction
from app.services.common.audit_modules import AuditModule
from app.services.common.audit_service import audit_service


class ChartOfAccountsError(ValueError):
    pass


class AccountNotFoundError(ChartOfAccountsError):
    pass


class AccountConflictError(ChartOfAccountsError):
    pass


class ChartSeedConflictError(ChartOfAccountsError):
    pass


@dataclass(frozen=True, slots=True)
class DefaultAccountDefinition:
    code: str
    name: str
    account_type: str
    normal_balance: str
    parent_code: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class ChartSeedResult:
    created: tuple[str, ...]
    unchanged: tuple[str, ...]

    @property
    def changed(self) -> bool:
        return bool(self.created)


DEFAULT_CHART: tuple[DefaultAccountDefinition, ...] = (
    DefaultAccountDefinition("1000", "Cash & Cash Equivalents", "asset", "debit"),
    DefaultAccountDefinition("1010", "Cash on Hand", "asset", "debit", "1000"),
    DefaultAccountDefinition("1020", "Bank Accounts", "asset", "debit", "1000"),
    DefaultAccountDefinition(
        "1030", "Mobile Money & Payment Clearing", "asset", "debit", "1000"
    ),
    DefaultAccountDefinition("1100", "Accounts Receivable", "asset", "debit"),
    DefaultAccountDefinition("1200", "Inventory", "asset", "debit"),
    DefaultAccountDefinition("1300", "Other Current Assets", "asset", "debit"),
    DefaultAccountDefinition("2000", "Accounts Payable", "liability", "credit"),
    DefaultAccountDefinition("2100", "Tax Liabilities", "liability", "credit"),
    DefaultAccountDefinition("2200", "Other Liabilities", "liability", "credit"),
    DefaultAccountDefinition("3000", "Owner's Equity", "equity", "credit"),
    DefaultAccountDefinition("4000", "Sales Revenue", "revenue", "credit"),
    DefaultAccountDefinition("4100", "Sales Returns", "revenue", "debit"),
    DefaultAccountDefinition("4200", "Discounts Allowed", "revenue", "debit"),
    DefaultAccountDefinition("4500", "Other Income", "revenue", "credit"),
    DefaultAccountDefinition("5000", "Cost of Goods Sold", "expense", "debit"),
    DefaultAccountDefinition("6000", "Operating Expenses", "expense", "debit"),
    DefaultAccountDefinition("6100", "Consumables", "expense", "debit", "6000"),
    DefaultAccountDefinition("6200", "Utilities", "expense", "debit", "6000"),
    DefaultAccountDefinition("6300", "Rent", "expense", "debit", "6000"),
    DefaultAccountDefinition(
        "6400", "Payroll-related Expenses", "expense", "debit", "6000"
    ),
    DefaultAccountDefinition(
        "6500", "Banking & Payment Charges", "expense", "debit", "6000"
    ),
    DefaultAccountDefinition(
        "6600", "Other Operating Expenses", "expense", "debit", "6000"
    ),
)

_NORMAL_BALANCE_BY_TYPE = {
    "asset": "debit",
    "liability": "credit",
    "equity": "credit",
    "revenue": "credit",
    "expense": "debit",
}

_ALLOWED_NORMAL_BALANCES_BY_TYPE = {
    "asset": frozenset({"debit"}),
    "liability": frozenset({"credit"}),
    "equity": frozenset({"credit"}),
    # Contra-revenue accounts such as Sales Returns and
    # Discounts Allowed naturally carry debit balances.
    "revenue": frozenset({"debit", "credit"}),
    "expense": frozenset({"debit"}),
}

_ACCOUNT_TYPES = frozenset(_NORMAL_BALANCE_BY_TYPE)
_NORMAL_BALANCES = frozenset({"debit", "credit"})


class ChartOfAccountsService:
    # Tenant-scoped Chart of Accounts command/query service.
    # The caller owns the transaction boundary.

    def __init__(self, session=None) -> None:
        self.session = session or db.session

    @staticmethod
    def _normalize_type(value: Any) -> str:
        value = str(value or "").strip().lower()
        if value not in _ACCOUNT_TYPES:
            raise ChartOfAccountsError(
                "account_type must be one of: asset, liability, equity, revenue, expense."
            )
        return value

    @staticmethod
    def _normalize_balance(value: Any) -> str:
        value = str(value or "").strip().lower()
        if value not in _NORMAL_BALANCES:
            raise ChartOfAccountsError(
                "normal_balance must be either debit or credit."
            )
        return value

    @staticmethod
    def _normalize_code(value: Any) -> str:
        code = str(value or "").strip()
        if not code:
            raise ChartOfAccountsError("account_code is required.")
        if len(code) > 30:
            raise ChartOfAccountsError("account_code must not exceed 30 characters.")
        return code

    @staticmethod
    def _normalize_name(value: Any) -> str:
        name = str(value or "").strip()
        if not name:
            raise ChartOfAccountsError("account_name is required.")
        if len(name) > 200:
            raise ChartOfAccountsError("account_name must not exceed 200 characters.")
        return name

    @staticmethod
    def _coerce_bool(value: Any, default: bool) -> bool:
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)

    @staticmethod
    def _normalize_currency(value: Any, fallback: str) -> str:
        raw = str(value or fallback or "").strip().upper()
        if len(raw) != 3 or not raw.isalpha():
            raise ChartOfAccountsError(
                "currency must be a 3-letter alphabetic currency code."
            )
        return raw

    def _tenant(self, tenant_id: str) -> Tenant:
        tenant = self.session.get(Tenant, tenant_id)
        if tenant is None:
            raise AccountNotFoundError("Tenant not found.")
        return tenant

    def _branch(self, tenant_id: str, branch_id: str | None) -> Branch | None:
        if branch_id is None:
            return None
        branch = self.session.get(Branch, branch_id)
        if branch is None or branch.tenant_id != tenant_id:
            raise ChartOfAccountsError(
                "branch_id must reference a branch belonging to the authenticated tenant."
            )
        return branch

    def _find(self, tenant_id: str, account_id: str) -> ChartOfAccount | None:
        return self.session.scalar(
            select(ChartOfAccount).where(
                ChartOfAccount.id == account_id,
                ChartOfAccount.tenant_id == tenant_id,
            )
        )

    def get(self, tenant_id: str, account_id: str) -> ChartOfAccount:
        account = self._find(tenant_id, account_id)
        if account is None:
            raise AccountNotFoundError("Account not found.")
        return account

    def list(
        self,
        tenant_id: str,
        *,
        branch_id: str | None = None,
        include_inactive: bool = True,
    ) -> list[ChartOfAccount]:
        query = select(ChartOfAccount).where(
            ChartOfAccount.tenant_id == tenant_id,
        )
        if branch_id is not None:
            query = query.where(
                (ChartOfAccount.branch_id.is_(None))
                | (ChartOfAccount.branch_id == branch_id)
            )
        if not include_inactive:
            query = query.where(ChartOfAccount.is_active.is_(True))
        return list(
            self.session.scalars(
                query.order_by(ChartOfAccount.account_code.asc())
            )
        )

    def _assert_parent(
        self,
        *,
        tenant_id: str,
        parent_id: str | None,
        account_id: str | None,
        branch_id: str | None,
    ) -> ChartOfAccount | None:
        if parent_id is None:
            return None
        if account_id is not None and parent_id == account_id:
            raise ChartOfAccountsError("An account cannot be its own parent.")

        parent = self._find(tenant_id, parent_id)
        if parent is None:
            raise ChartOfAccountsError(
                "parent_id must reference an account in the same tenant."
            )

        if branch_id is None and parent.branch_id is not None:
            raise ChartOfAccountsError(
                "A tenant-wide account cannot have a branch-specific parent."
            )
        if branch_id is not None and parent.branch_id not in (None, branch_id):
            raise ChartOfAccountsError(
                "A branch-specific account may only inherit from a tenant-wide "
                "or same-branch parent."
            )
        return parent

    def _assert_no_cycle(
        self,
        *,
        tenant_id: str,
        account_id: str | None,
        parent_id: str | None,
    ) -> None:
        if parent_id is None:
            return

        seen: set[str] = set()
        current_id = parent_id
        while current_id is not None:
            if current_id in seen:
                raise ChartOfAccountsError("Account hierarchy contains a cycle.")
            seen.add(current_id)

            current = self._find(tenant_id, current_id)
            if current is None:
                raise ChartOfAccountsError("Parent account no longer exists.")

            if account_id is not None and current.id == account_id:
                raise ChartOfAccountsError(
                    "Account hierarchy cannot make an account its own ancestor."
                )
            current_id = current.parent_id

    def _assert_children_compatible_with_branch(
        self,
        *,
        tenant_id: str,
        account_id: str,
        branch_id: str | None,
    ) -> None:
        if branch_id is None:
            return

        incompatible_child = self.session.scalar(
            select(ChartOfAccount.id).where(
                ChartOfAccount.tenant_id == tenant_id,
                ChartOfAccount.parent_id == account_id,
                db.or_(
                    ChartOfAccount.branch_id.is_(None),
                    ChartOfAccount.branch_id != branch_id,
                ),
            ).limit(1)
        )
        if incompatible_child is not None:
            raise ChartOfAccountsError(
                "A branch-specific parent cannot have tenant-wide "
                "or different-branch child accounts."
            )

    def _assert_code_available(
        self,
        tenant_id: str,
        account_code: str,
        *,
        account_id: str | None = None,
    ) -> None:
        existing = self.session.scalar(
            select(ChartOfAccount).where(
                ChartOfAccount.tenant_id == tenant_id,
                ChartOfAccount.account_code == account_code,
            )
        )
        if existing is not None and existing.id != account_id:
            raise AccountConflictError(
                f"Account code {account_code!r} is already in use."
            )

    def create_account(
        self,
        tenant_id: str,
        *,
        account_code: str,
        account_name: str,
        account_type: str,
        normal_balance: str | None = None,
        parent_id: str | None = None,
        description: str | None = None,
        is_active: bool = True,
        branch_id: str | None = None,
        currency: str | None = None,
        is_system_account: bool = False,
        actor_user_id: str | None = None,
    ) -> ChartOfAccount:
        if is_system_account:
            raise ChartOfAccountsError(
                "System accounts can only be provisioned by the controlled default-chart seeder."
            )

        tenant = self._tenant(tenant_id)
        branch = self._branch(tenant_id, branch_id)
        account_type = self._normalize_type(account_type)
        normal_balance = self._normalize_balance(
            normal_balance or _NORMAL_BALANCE_BY_TYPE[account_type]
        )

        if normal_balance not in _ALLOWED_NORMAL_BALANCES_BY_TYPE[account_type]:
            raise ChartOfAccountsError(
                f"{account_type} accounts cannot use a "
                f"{normal_balance} normal balance."
            )

        account_code = self._normalize_code(account_code)
        account_name = self._normalize_name(account_name)
        self._assert_code_available(tenant_id, account_code)

        parent = self._assert_parent(
            tenant_id=tenant_id,
            parent_id=parent_id,
            account_id=None,
            branch_id=branch_id,
        )
        self._assert_no_cycle(
            tenant_id=tenant_id,
            account_id=None,
            parent_id=parent_id,
        )

        account = ChartOfAccount(
            tenant_id=tenant.id,
            branch_id=branch.id if branch else None,
            account_code=account_code,
            account_name=account_name,
            account_type=account_type,
            parent_id=parent.id if parent else None,
            description=str(description).strip() if description is not None else None,
            normal_balance=normal_balance,
            is_active=self._coerce_bool(is_active, True),
            is_system_account=False,
            currency=self._normalize_currency(currency, tenant.base_currency),
        )
        self.session.add(account)
        self.session.flush()

        audit_service.log(
            module=AuditModule.FINANCE,
            action=AuditAction.FINANCE_ACCOUNT_CREATED,
            entity_type="ChartOfAccount",
            entity_id=account.id,
            tenant_id=tenant_id,
            branch_id=account.branch_id,
            user_id=actor_user_id,
            new_values=self.snapshot(account),
            commit=False,
        )
        return account

    def update_account(
        self,
        tenant_id: str,
        account_id: str,
        *,
        fields: dict[str, Any],
        actor_user_id: str | None = None,
    ) -> ChartOfAccount:
        account = self.get(tenant_id, account_id)
        if not fields:
            return account

        original = self.snapshot(account)

        if account.is_system_account:
            immutable = {
                "account_code",
                "account_type",
                "normal_balance",
                "parent_id",
                "branch_id",
                "currency",
            }
            if immutable.intersection(fields):
                raise ChartOfAccountsError(
                    "System account structure cannot be changed."
                )
            if "is_active" in fields and not self._coerce_bool(
                fields["is_active"],
                account.is_active,
            ):
                raise ChartOfAccountsError("System accounts cannot be deactivated.")

        account_code = account.account_code
        account_name = account.account_name
        account_type = account.account_type
        normal_balance = account.normal_balance
        parent_id = account.parent_id
        branch_id = account.branch_id
        currency = account.currency

        if "account_code" in fields:
            account_code = self._normalize_code(fields["account_code"])
            self._assert_code_available(
                tenant_id, account_code, account_id=account.id
            )

        if "account_name" in fields:
            account_name = self._normalize_name(fields["account_name"])

        if "account_type" in fields:
            account_type = self._normalize_type(fields["account_type"])

        if "normal_balance" in fields:
            normal_balance = self._normalize_balance(fields["normal_balance"])
        elif "account_type" in fields:
            normal_balance = _NORMAL_BALANCE_BY_TYPE[account_type]

        if normal_balance not in _ALLOWED_NORMAL_BALANCES_BY_TYPE[account_type]:
            raise ChartOfAccountsError(
                f"{account_type} accounts cannot use a "
                f"{normal_balance} normal balance."
            )

        if "parent_id" in fields:
            parent_id = fields["parent_id"] or None

        if "branch_id" in fields:
            branch_id = fields["branch_id"] or None
            self._branch(tenant_id, branch_id)

            if branch_id != account.branch_id:
                self._assert_children_compatible_with_branch(
                    tenant_id=tenant_id,
                    account_id=account.id,
                    branch_id=branch_id,
                )

        if "currency" in fields:
            currency = self._normalize_currency(
                fields["currency"],
                self._tenant(tenant_id).base_currency,
            )

        parent = self._assert_parent(
            tenant_id=tenant_id,
            parent_id=parent_id,
            account_id=account.id,
            branch_id=branch_id,
        )
        self._assert_no_cycle(
            tenant_id=tenant_id,
            account_id=account.id,
            parent_id=parent_id,
        )

        account.account_code = account_code
        account.account_name = account_name
        account.account_type = account_type
        account.normal_balance = normal_balance
        account.parent_id = parent.id if parent else None
        account.branch_id = branch_id
        account.currency = currency

        if "description" in fields:
            account.description = (
                str(fields["description"]).strip()
                if fields["description"] is not None
                else None
            )

        if "is_active" in fields:
            requested_active = self._coerce_bool(
                fields["is_active"],
                account.is_active,
            )
            if not requested_active and account.is_active:
                active_child_exists = self.session.scalar(
                    select(ChartOfAccount.id).where(
                        ChartOfAccount.tenant_id == tenant_id,
                        ChartOfAccount.parent_id == account.id,
                        ChartOfAccount.is_active.is_(True),
                    ).limit(1)
                )
                if active_child_exists is not None:
                    raise ChartOfAccountsError(
                        "An account with active child accounts cannot be deactivated."
                    )
            account.is_active = requested_active

        self.session.flush()

        action = (
            AuditAction.FINANCE_ACCOUNT_DEACTIVATED
            if original["is_active"] and not account.is_active
            else AuditAction.FINANCE_ACCOUNT_UPDATED
        )
        audit_service.log(
            module=AuditModule.FINANCE,
            action=action,
            entity_type="ChartOfAccount",
            entity_id=account.id,
            tenant_id=tenant_id,
            branch_id=account.branch_id,
            user_id=actor_user_id,
            old_values=original,
            new_values=self.snapshot(account),
            commit=False,
        )
        return account

    def seed_default_chart(
        self,
        tenant_id: str,
        *,
        actor_user_id: str | None = None,
    ) -> ChartSeedResult:
        tenant = self._tenant(tenant_id)
        existing_by_code = {
            account.account_code: account
            for account in self.session.scalars(
                select(ChartOfAccount).where(
                    ChartOfAccount.tenant_id == tenant_id
                )
            )
        }

        created: list[str] = []
        unchanged: list[str] = []

        for definition in DEFAULT_CHART:
            existing = existing_by_code.get(definition.code)

            if existing is not None:
                expected_parent_id = None
                if definition.parent_code:
                    parent = existing_by_code.get(definition.parent_code)
                    if parent is None:
                        raise ChartSeedConflictError(
                            f"Default chart parent {definition.parent_code} is missing."
                        )
                    expected_parent_id = parent.id

                if (
                    not existing.is_system_account
                    or existing.account_type != definition.account_type
                    or existing.normal_balance != definition.normal_balance
                    or existing.parent_id != expected_parent_id
                    or existing.branch_id is not None
                    or (existing.currency or tenant.base_currency).upper()
                    != tenant.base_currency.upper()
                ):
                    raise ChartSeedConflictError(
                        f"Existing account {definition.code} conflicts with the default chart."
                    )

                unchanged.append(definition.code)
                continue

            parent = None
            if definition.parent_code:
                parent = existing_by_code.get(definition.parent_code)
                if parent is None:
                    raise ChartSeedConflictError(
                        f"Default chart parent {definition.parent_code} is missing."
                    )

            account = ChartOfAccount(
                tenant_id=tenant_id,
                branch_id=None,
                account_code=definition.code,
                account_name=definition.name,
                account_type=definition.account_type,
                parent_id=parent.id if parent else None,
                description=definition.description,
                normal_balance=definition.normal_balance,
                is_active=True,
                is_system_account=True,
                currency=tenant.base_currency.upper(),
            )
            self.session.add(account)
            self.session.flush()
            existing_by_code[definition.code] = account
            created.append(definition.code)

            audit_service.log(
                module=AuditModule.FINANCE,
                action=AuditAction.FINANCE_ACCOUNT_CREATED,
                entity_type="ChartOfAccount",
                entity_id=account.id,
                tenant_id=tenant_id,
                branch_id=None,
                user_id=actor_user_id,
                new_values=self.snapshot(account),
                details={"source": "default_chart_seed"},
                commit=False,
            )

        return ChartSeedResult(
            created=tuple(created),
            unchanged=tuple(unchanged),
        )

    @staticmethod
    def snapshot(account: ChartOfAccount) -> dict[str, Any]:
        return {
            "id": account.id,
            "tenant_id": account.tenant_id,
            "branch_id": account.branch_id,
            "account_code": account.account_code,
            "account_name": account.account_name,
            "account_type": account.account_type,
            "parent_id": account.parent_id,
            "description": account.description,
            "normal_balance": account.normal_balance,
            "is_active": account.is_active,
            "is_system_account": account.is_system_account,
            "currency": account.currency,
        }


__all__ = [
    "AccountConflictError",
    "AccountNotFoundError",
    "ChartOfAccountsError",
    "ChartOfAccountsService",
    "ChartSeedConflictError",
    "DEFAULT_CHART",
    "DefaultAccountDefinition",
    "ChartSeedResult",
]
