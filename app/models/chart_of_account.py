from __future__ import annotations

from app.extensions import db
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class ChartOfAccount(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    db.Model,
):
    __tablename__ = "chart_of_accounts"

    __table_args__ = (
        db.UniqueConstraint(
            "tenant_id",
            "account_code",
            name="uq_chart_of_accounts_tenant_code",
        ),
        db.Index(
            "ix_chart_of_accounts_tenant_branch",
            "tenant_id",
            "branch_id",
        ),
        db.Index(
            "ix_chart_of_accounts_tenant_parent",
            "tenant_id",
            "parent_id",
        ),
        db.CheckConstraint(
            (
                "account_type IN "
                "('asset', 'liability', 'equity', 'revenue', 'expense')"
            ),
            name="ck_chart_of_accounts_account_type",
        ),
        db.CheckConstraint(
            "normal_balance IN ('debit', 'credit')",
            name="ck_chart_of_accounts_normal_balance",
        ),
        db.CheckConstraint(
            "parent_id IS NULL OR parent_id <> id",
            name="ck_chart_of_accounts_not_self_parent",
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
        nullable=True,
        index=True,
    )

    account_code = db.Column(
        db.String(30),
        nullable=False,
    )

    account_name = db.Column(
        db.String(200),
        nullable=False,
    )

    account_type = db.Column(
        db.String(20),
        nullable=False,
    )

    parent_id = db.Column(
        db.String(36),
        db.ForeignKey("chart_of_accounts.id"),
        nullable=True,
        index=True,
    )

    description = db.Column(
        db.Text,
        nullable=True,
    )

    normal_balance = db.Column(
        db.String(10),
        nullable=False,
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    is_system_account = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    currency = db.Column(
        db.String(3),
        nullable=True,
    )

    tenant = db.relationship(
        "Tenant",
        foreign_keys=[tenant_id],
    )

    branch = db.relationship(
        "Branch",
        foreign_keys=[branch_id],
    )

    parent = db.relationship(
        "ChartOfAccount",
        remote_side="ChartOfAccount.id",
        foreign_keys=[parent_id],
        back_populates="children",
    )

    children = db.relationship(
        "ChartOfAccount",
        foreign_keys=[parent_id],
        back_populates="parent",
        lazy="select",
    )
