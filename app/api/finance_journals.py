from __future__ import annotations

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from app.api.utils import current_identity as _current_identity
from app.extensions import db
from app.services.tenant.auth.decorators import require_permission
from app.services.tenant.finance import (
    JournalEntryConflictError,
    JournalEntryError,
    JournalEntryNotFoundError,
    JournalEntryService,
    JournalEntryStateError,
)

bp = Blueprint("finance_journals", __name__)


def _json_error(message: str, status: int = 400):
    return jsonify({"ok": False, "error": message}), status


def _serialize(entry):
    reversal_number = entry.reversal_entries[0].journal_number if entry.reversal_entries else None
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
        "total_debit": f"{entry.total_debit:.2f}",
        "total_credit": f"{entry.total_credit:.2f}",
        "created_by": entry.created_by,
        "updated_by": entry.updated_by,
        "posted_by": entry.posted_by,
        "posted_at": entry.posted_at.isoformat() if entry.posted_at else None,
        "reversal_of_id": entry.reversal_of_id,
        "original_journal_number": entry.reversal_of.journal_number if entry.reversal_of else None,
        "reversal_journal_number": reversal_number,
        "lines": [
            {
                "id": line.id,
                "line_number": line.line_number,
                "account_id": line.account_id,
                "account_code": line.account.account_code if line.account else None,
                "account_name": line.account.account_name if line.account else None,
                "description": line.description,
                "debit": f"{line.debit:.2f}",
                "credit": f"{line.credit:.2f}",
            }
            for line in entry.lines
        ],
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
        "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
    }


def _branch_for_write(data: dict, identity):
    requested = data.get("branch_id")
    if identity.branch_id is not None:
        if requested not in (None, "", identity.branch_id):
            return None, "A branch-scoped user may only manage journals for their own branch."
        return identity.branch_id, None
    if requested in (None, ""):
        return None, "branch_id is required when the authenticated user has no selected branch."
    return str(requested).strip(), None


def _handle_service_error(exc: JournalEntryError):
    if isinstance(exc, JournalEntryNotFoundError):
        return _json_error(str(exc), 404)
    if isinstance(exc, (JournalEntryConflictError, JournalEntryStateError)):
        return _json_error(str(exc), 409)
    return _json_error(str(exc), 400)


@bp.get("/finance/journals")
@require_permission("finance.journals.read")
def list_journals():
    identity = _current_identity()
    try:
        raw_limit = request.args.get("limit", "50")
        limit = int(raw_limit)
        if limit < 1:
            raise ValueError
        entries = JournalEntryService(db.session).list(
            identity.tenant_id,
            branch_id=identity.branch_id,
            status=request.args.get("status"),
            limit=min(limit, 100),
        )
    except ValueError as exc:
        if isinstance(exc, JournalEntryError):
            return _handle_service_error(exc)
        return _json_error("limit must be a positive integer.", 400)
    return jsonify({"ok": True, "count": len(entries), "items": [_serialize(item) for item in entries]})


@bp.get("/finance/journals/<entry_id>")
@require_permission("finance.journals.read")
def get_journal(entry_id: str):
    identity = _current_identity()
    try:
        entry = JournalEntryService(db.session).get(
            identity.tenant_id, entry_id, branch_id=identity.branch_id
        )
    except JournalEntryError as exc:
        return _handle_service_error(exc)
    return jsonify({"ok": True, "item": _serialize(entry)})


@bp.post("/finance/journals")
@require_permission("finance.journals.create")
def create_journal():
    identity = _current_identity()
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return _json_error("Request body must be a JSON object.")
    branch_id, branch_error = _branch_for_write(data, identity)
    if branch_error:
        return _json_error(branch_error, 403)
    allowed = {"branch_id", "journal_date", "description", "reference", "lines"}
    unknown = set(data) - allowed
    if unknown:
        return _json_error(f"Unsupported journal fields: {', '.join(sorted(unknown))}.")
    try:
        entry = JournalEntryService(db.session).create_draft(
            identity.tenant_id,
            branch_id=branch_id,
            journal_date=data.get("journal_date"),
            description=data.get("description"),
            reference=data.get("reference"),
            lines=data.get("lines"),
            actor_user_id=identity.user_id,
        )
        db.session.commit()
    except JournalEntryError as exc:
        db.session.rollback()
        return _handle_service_error(exc)
    except IntegrityError:
        db.session.rollback()
        return _json_error("The journal conflicts with an existing record. Refresh and try again.", 409)
    except Exception:
        db.session.rollback()
        raise
    return jsonify({"ok": True, "message": "Journal draft created.", "item": _serialize(entry)}), 201


@bp.patch("/finance/journals/<entry_id>")
@require_permission("finance.journals.create")
def update_journal_draft(entry_id: str):
    identity = _current_identity()
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return _json_error("Request body must be a JSON object.")
    try:
        entry = JournalEntryService(db.session).update_draft(
            identity.tenant_id,
            entry_id,
            fields=data,
            branch_id=identity.branch_id,
            actor_user_id=identity.user_id,
        )
        db.session.commit()
    except JournalEntryError as exc:
        db.session.rollback()
        return _handle_service_error(exc)
    except IntegrityError:
        db.session.rollback()
        return _json_error("The journal update conflicts with an existing record.", 409)
    except Exception:
        db.session.rollback()
        raise
    return jsonify({"ok": True, "message": "Journal draft updated.", "item": _serialize(entry)})


@bp.post("/finance/journals/<entry_id>/post")
@require_permission("finance.journals.post")
def post_journal(entry_id: str):
    identity = _current_identity()
    try:
        entry = JournalEntryService(db.session).post(
            identity.tenant_id,
            entry_id,
            branch_id=identity.branch_id,
            actor_user_id=identity.user_id,
        )
        db.session.commit()
    except JournalEntryError as exc:
        db.session.rollback()
        return _handle_service_error(exc)
    except IntegrityError:
        db.session.rollback()
        return _json_error("The journal could not be posted because of a record conflict.", 409)
    except Exception:
        db.session.rollback()
        raise
    return jsonify({"ok": True, "message": "Journal posted.", "item": _serialize(entry)})


@bp.post("/finance/journals/<entry_id>/reverse")
@require_permission("finance.journals.reverse")
def reverse_journal(entry_id: str):
    identity = _current_identity()
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return _json_error("Request body must be a JSON object.")
    unknown = set(data) - {"journal_date", "reason"}
    if unknown:
        return _json_error(f"Unsupported reversal fields: {', '.join(sorted(unknown))}.")
    try:
        entry = JournalEntryService(db.session).reverse(
            identity.tenant_id,
            entry_id,
            journal_date=data.get("journal_date"),
            reason=data.get("reason"),
            branch_id=identity.branch_id,
            actor_user_id=identity.user_id,
        )
        db.session.commit()
    except JournalEntryError as exc:
        db.session.rollback()
        return _handle_service_error(exc)
    except IntegrityError:
        db.session.rollback()
        return _json_error("A reversal already exists or the journal conflicts with another record.", 409)
    except Exception:
        db.session.rollback()
        raise
    return jsonify({"ok": True, "message": "Reversal journal posted.", "item": _serialize(entry)}), 201


__all__ = ["bp"]
