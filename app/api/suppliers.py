from flask import Blueprint, jsonify, request

from app.api.utils import current_identity
from app.schemas import CreateSupplierRequest, SupplierListFilters, UpdateSupplierRequest
from app.serializers import serialize_supplier
from app.services.tenant.auth.decorators import require_permission
from app.services.tenant.procurement import supplier_service

bp = Blueprint("suppliers", __name__)


def _supplier_response(supplier):
    return {
        "ok": True,
        "item": serialize_supplier(supplier),
    }


@bp.get("/suppliers")
@require_permission("suppliers.view")
def list_suppliers():
    identity = current_identity()
    filters = SupplierListFilters.from_query(request.args)

    items, pagination = supplier_service.list_suppliers(
        identity.tenant_id,
        filters,
    )

    return jsonify(
        {
            "ok": True,
            "items": [serialize_supplier(item) for item in items],
            "pagination": pagination,
        }
    )


@bp.get("/suppliers/<supplier_id>")
@require_permission("suppliers.view")
def get_supplier(supplier_id: str):
    identity = current_identity()
    supplier = supplier_service.get_supplier(
        identity.tenant_id,
        supplier_id,
    )
    return jsonify(_supplier_response(supplier))


@bp.post("/suppliers")
@require_permission("suppliers.create")
def create_supplier():
    identity = current_identity()
    payload = request.get_json(silent=True) or {}
    supplier = supplier_service.create_supplier(
        identity.tenant_id,
        CreateSupplierRequest.from_payload(payload),
    )
    return (
        jsonify(
            {
                "ok": True,
                "message": "Supplier created successfully.",
                "item": serialize_supplier(supplier),
            }
        ),
        201,
    )


@bp.patch("/suppliers/<supplier_id>")
@require_permission("suppliers.update")
def update_supplier(supplier_id: str):
    identity = current_identity()
    payload = request.get_json(silent=True) or {}
    supplier = supplier_service.update_supplier(
        identity.tenant_id,
        supplier_id,
        UpdateSupplierRequest.from_payload(payload),
    )
    return jsonify(_supplier_response(supplier))


@bp.post("/suppliers/<supplier_id>/deactivate")
@require_permission("suppliers.deactivate")
def deactivate_supplier(supplier_id: str):
    identity = current_identity()
    supplier = supplier_service.deactivate_supplier(
        identity.tenant_id,
        supplier_id,
    )
    return jsonify(_supplier_response(supplier))


@bp.post("/suppliers/<supplier_id>/reactivate")
@require_permission("suppliers.deactivate")
def reactivate_supplier(supplier_id: str):
    identity = current_identity()
    supplier = supplier_service.reactivate_supplier(
        identity.tenant_id,
        supplier_id,
    )
    return jsonify(_supplier_response(supplier))
