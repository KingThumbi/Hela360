from flask import Blueprint, jsonify, request

from app.extensions import db
from app.serializers import (
    serialize_till,
    serialize_till_shift,
    serialize_till_shift_reconciliation,
)
from app.services.tenant.auth.decorators import (
    _current_identity,
    require_permission,
)
from app.services.tenant.pos import TillShiftService

bp = Blueprint("tills", __name__)


def _service() -> TillShiftService:
    return TillShiftService(db.session)


@bp.get("/tills")
@require_permission("sales.create")
def list_tills():
    identity = _current_identity()
    tills = _service().list_active_tills(
        tenant_id=identity.tenant_id,
        branch_id=identity.branch_id,
    )

    return jsonify(
        {
            "ok": True,
            "items": [serialize_till(till) for till in tills],
        }
    )


@bp.get("/till-shifts/current")
@require_permission("sales.create")
def get_current_till_shift():
    identity = _current_identity()
    shift = _service().get_current_shift(
        tenant_id=identity.tenant_id,
        branch_id=identity.branch_id,
        cashier_id=identity.user_id,
        till_id=(request.args.get("till_id") or "").strip() or None,
    )

    return jsonify(
        {
            "ok": True,
            "item": (
                serialize_till_shift(
                    shift,
                    current_session_id=identity.session_id,
                )
                if shift
                else None
            ),
        }
    )


@bp.post("/till-shifts/open")
@require_permission("sales.create")
def open_till_shift():
    identity = _current_identity()
    payload = request.get_json(silent=True) or {}
    shift = _service().open_shift(
        tenant_id=identity.tenant_id,
        branch_id=identity.branch_id,
        cashier_id=identity.user_id,
        session_id=identity.session_id,
        payload=payload,
    )

    return (
        jsonify(
            {
                "ok": True,
                "message": "Till shift opened successfully.",
                "item": serialize_till_shift(
                    shift,
                    current_session_id=identity.session_id,
                ),
            }
        ),
        201,
    )


@bp.post("/till-shifts/<shift_id>/takeover")
@require_permission("sales.create")
def takeover_till_shift(shift_id: str):
    identity = _current_identity()

    shift = _service().takeover_shift(
        tenant_id=identity.tenant_id,
        branch_id=identity.branch_id,
        cashier_id=identity.user_id,
        session_id=identity.session_id,
        shift_id=shift_id,
    )

    return jsonify(
        {
            "ok": True,
            "message": "Till shift transferred to this session successfully.",
            "item": serialize_till_shift(
                    shift,
                    current_session_id=identity.session_id,
                ),
        }
    )


@bp.post("/till-shifts/<shift_id>/close")
@require_permission("sales.create")
def close_till_shift(shift_id: str):
    identity = _current_identity()
    payload = request.get_json(silent=True) or {}
    shift, reconciliation = _service().close_shift(
        tenant_id=identity.tenant_id,
        branch_id=identity.branch_id,
        cashier_id=identity.user_id,
        session_id=identity.session_id,
        shift_id=shift_id,
        payload=payload,
    )

    return jsonify(
        {
            "ok": True,
            "message": "Till shift closed successfully.",
            "item": serialize_till_shift(
                    shift,
                    current_session_id=identity.session_id,
                ),
            "reconciliation": serialize_till_shift_reconciliation(
                **reconciliation,
            ),
        }
    )
