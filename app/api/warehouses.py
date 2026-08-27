from flask import Blueprint, jsonify

from app.extensions import db
from app.models import Warehouse
from app.serializers import serialize_warehouse
from app.services.tenant.auth.decorators import (
    _current_identity,
    require_any_permission,
)

bp = Blueprint("warehouses", __name__)


@bp.get("/warehouses")
@require_any_permission(("inventory.read", "inventory.count", "inventory.adjust"))
def list_warehouses():
    identity = _current_identity()

    warehouses = (
        db.session.query(Warehouse)
        .filter(
            Warehouse.tenant_id == identity.tenant_id,
            Warehouse.branch_id == identity.branch_id,
            Warehouse.is_active.is_(True),
        )
        .order_by(
            Warehouse.code.asc(),
            Warehouse.name.asc(),
            Warehouse.created_at.asc(),
        )
        .all()
    )

    return jsonify(
        {
            "ok": True,
            "items": [
                serialize_warehouse(warehouse)
                for warehouse in warehouses
            ],
        }
    )
