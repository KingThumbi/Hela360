from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.api.utils import current_identity as _current_identity
from app.extensions import db
from app.models import Branch, ChartOfAccount
from app.services.tenant.auth.decorators import require_permission
from app.services.tenant.finance import (
    AccountConflictError,
    ChartOfAccountsError,
    ChartOfAccountsService,
)

bp = Blueprint("finance_accounts", __name__)


def _json_error(message: str, status: int = 400):
    return jsonify({"ok": False, "error": message}), status


def _visible_query(tenant_id: str, branch_id: str | None):
    query = ChartOfAccount.query.filter_by(tenant_id=tenant_id)
    if branch_id is not None:
        query = query.filter(
            db.or_(
                ChartOfAccount.branch_id.is_(None),
                ChartOfAccount.branch_id == branch_id,
            )
        )
    return query


def _serialize_parent(parent: ChartOfAccount | None):
    if parent is None:
        return None
    return {
        "id": parent.id,
        "account_code": parent.account_code,
        "account_name": parent.account_name,
    }


def _serialize_branch(branch: Branch | None):
    if branch is None:
        return None
    return {
        "id": branch.id,
        "code": branch.code,
        "name": branch.name,
    }


def _serialize(account: ChartOfAccount) -> dict:
    return {
        "id": account.id,
        "tenant_id": account.tenant_id,
        "branch_id": account.branch_id,
        "account_code": account.account_code,
        "account_name": account.account_name,
        "account_type": account.account_type,
        "parent_id": account.parent_id,
        "parent": _serialize_parent(account.parent),
        "description": account.description,
        "normal_balance": account.normal_balance,
        "is_active": account.is_active,
        "is_system_account": account.is_system_account,
        "currency": account.currency,
        "branch": _serialize_branch(account.branch),
        "created_at": account.created_at.isoformat() if account.created_at else None,
        "updated_at": account.updated_at.isoformat() if account.updated_at else None,
    }


def _requested_branch(data: dict, identity):
    if "branch_id" not in data:
        return False, None, None

    requested = data.get("branch_id")
    requested = (
        str(requested).strip()
        if requested not in (None, "")
        else None
    )

    if identity.branch_id is not None and requested != identity.branch_id:
        return True, None, (
            "A branch-scoped user may only manage accounts for their own branch."
        )

    return True, requested, None


@bp.get("/finance/accounts")
@require_permission("finance.accounts.read")
def list_accounts():
    identity = _current_identity()
    accounts = (
        _visible_query(identity.tenant_id, identity.branch_id)
        .order_by(ChartOfAccount.account_code.asc())
        .all()
    )
    return jsonify(
        {
            "ok": True,
            "count": len(accounts),
            "items": [_serialize(account) for account in accounts],
        }
    )


@bp.get("/finance/accounts/<account_id>")
@require_permission("finance.accounts.read")
def get_account(account_id: str):
    identity = _current_identity()
    account = (
        _visible_query(identity.tenant_id, identity.branch_id)
        .filter(ChartOfAccount.id == account_id)
        .first()
    )
    if account is None:
        return _json_error("Account not found.", 404)
    return jsonify({"ok": True, "item": _serialize(account)})


@bp.post("/finance/accounts")
@require_permission("finance.accounts.create")
def create_account():
    identity = _current_identity()
    data = request.get_json(silent=True) or {}

    if identity.branch_id is not None and "branch_id" not in data:
        return _json_error(
            "branch_id is required for a branch-scoped finance user.",
            403,
        )

    _, requested_branch, branch_error = _requested_branch(data, identity)
    if branch_error:
        return _json_error(branch_error, 403)

    try:
        account = ChartOfAccountsService(db.session).create_account(
            identity.tenant_id,
            account_code=data.get("account_code"),
            account_name=data.get("account_name"),
            account_type=data.get("account_type"),
            normal_balance=data.get("normal_balance"),
            parent_id=data.get("parent_id"),
            description=data.get("description"),
            is_active=data.get("is_active", True),
            branch_id=requested_branch,
            currency=data.get("currency"),
            actor_user_id=identity.user_id,
        )
        db.session.commit()
    except (AccountConflictError, ChartOfAccountsError) as exc:
        db.session.rollback()
        return _json_error(
            str(exc),
            409 if isinstance(exc, AccountConflictError) else 400,
        )
    except Exception:
        db.session.rollback()
        raise

    return (
        jsonify(
            {
                "ok": True,
                "message": "Finance account created successfully.",
                "item": _serialize(account),
            }
        ),
        201,
    )


@bp.patch("/finance/accounts/<account_id>")
@require_permission("finance.accounts.update")
def update_account(account_id: str):
    identity = _current_identity()
    account = (
        _visible_query(identity.tenant_id, identity.branch_id)
        .filter(ChartOfAccount.id == account_id)
        .first()
    )
    if account is None:
        return _json_error("Account not found.", 404)

    if identity.branch_id is not None and account.branch_id is None:
        return _json_error(
            "A branch-scoped user cannot modify a tenant-wide finance account.",
            403,
        )

    data = request.get_json(silent=True) or {}
    _, _, branch_error = _requested_branch(data, identity)
    if branch_error:
        return _json_error(branch_error, 403)

    try:
        account = ChartOfAccountsService(db.session).update_account(
            identity.tenant_id,
            account.id,
            fields=data,
            actor_user_id=identity.user_id,
        )
        db.session.commit()
    except (AccountConflictError, ChartOfAccountsError) as exc:
        db.session.rollback()
        return _json_error(
            str(exc),
            409 if isinstance(exc, AccountConflictError) else 400,
        )
    except Exception:
        db.session.rollback()
        raise

    return jsonify(
        {
            "ok": True,
            "message": "Finance account updated successfully.",
            "item": _serialize(account),
        }
    )


__all__ = ["bp"]
