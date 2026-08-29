from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.schemas import CreateGoodsReceiptRequest
from app.schemas import (
    CreateStockAdjustmentFromCountRequest,
    CreateStockAdjustmentRequest,
)
from app.schemas import (
    AddDiscoveredStockCountItemRequest,
    CreateStockCountRequest,
    UpdateStockCountItemRequest,
)
from app.serializers import serialize_goods_receipt
from app.serializers import serialize_stock_adjustment
from app.serializers import serialize_stock_count
from app.services.tenant.auth.decorators import (
    _current_identity,
    require_permission,
)
from app.services.tenant.inventory import (
    GoodsReceiptListFilters,
    GoodsReceiptQueryError,
    GoodsReceiptService,
    InventoryListFilters,
    InventoryMovementListFilters,
    InventoryQueryError,
    InventoryQueryService,
    StockAdjustmentListFilters,
    StockAdjustmentQueryError,
    StockAdjustmentService,
    StockCountListFilters,
    StockCountQueryError,
    StockCountService,
)


bp = Blueprint("inventory", __name__)


def _json_error(message: str, status: int = 400):
    return jsonify({"ok": False, "error": message}), status


@bp.get("/inventory")
@require_permission("inventory.read")
def list_inventory_stock():
    identity = _current_identity()

    try:
        filters = InventoryListFilters.from_query(request.args)
        items, pagination = InventoryQueryService(db.session).list_stock(
            tenant_id=identity.tenant_id,
            branch_id=identity.branch_id,
            filters=filters,
        )
    except InventoryQueryError as exc:
        return _json_error(str(exc), 400)

    return jsonify(
        {
            "ok": True,
            "items": items,
            "pagination": pagination,
        }
    )


@bp.get("/inventory/stock/<stock_balance_id>/batches")
@require_permission("inventory.read")
def list_inventory_stock_batches(stock_balance_id: str):
    identity = _current_identity()

    include_zero = str(request.args.get("include_zero") or "").lower() in {
        "1",
        "true",
        "yes",
    }

    try:
        payload = InventoryQueryService(db.session).list_stock_batches(
            tenant_id=identity.tenant_id,
            branch_id=identity.branch_id,
            stock_balance_id=stock_balance_id,
            include_zero=include_zero,
        )
    except InventoryQueryError as exc:
        status = 404 if str(exc) == "Stock balance not found." else 400
        return _json_error(str(exc), status)

    return jsonify(
        {
            "ok": True,
            **payload,
        }
    )


@bp.get("/inventory/movements")
@require_permission("inventory.read")
def list_inventory_movements():
    identity = _current_identity()

    try:
        filters = InventoryMovementListFilters.from_query(request.args)
        items, pagination = InventoryQueryService(db.session).list_movements(
            tenant_id=identity.tenant_id,
            branch_id=identity.branch_id,
            filters=filters,
        )
    except InventoryQueryError as exc:
        return _json_error(str(exc), 400)

    return jsonify(
        {
            "ok": True,
            "items": items,
            "pagination": pagination,
        }
    )


@bp.get("/inventory/goods-receipts")
@require_permission("inventory.receive")
def list_goods_receipts():
    identity = _current_identity()
    service = GoodsReceiptService(db.session)

    try:
        filters = GoodsReceiptListFilters.from_query(request.args)
        items, pagination = service.list_goods_receipts(
            tenant_id=identity.tenant_id,
            branch_id=identity.branch_id,
            filters=filters,
        )
    except GoodsReceiptQueryError as exc:
        return _json_error(str(exc), 400)

    return jsonify(
        {
            "ok": True,
            "items": items,
            "pagination": pagination,
        }
    )


@bp.post("/inventory/goods-receipts")
@require_permission("inventory.receive")
def create_goods_receipt():
    identity = _current_identity()
    payload = request.get_json(silent=True) or {}
    service = GoodsReceiptService(db.session)
    receipt = service.create_goods_receipt(
        tenant_id=identity.tenant_id,
        branch_id=identity.branch_id,
        received_by=identity.user_id,
        request=CreateGoodsReceiptRequest.from_payload(payload),
    )

    return (
        jsonify(
            {
                "ok": True,
                "message": "Goods receipt created successfully.",
                "item": serialize_goods_receipt(
                    receipt,
                    **service.serialization_context(receipt),
                ),
            }
        ),
        201,
    )


@bp.get("/inventory/goods-receipts/<receipt_id>")
@require_permission("inventory.receive")
def get_goods_receipt(receipt_id: str):
    identity = _current_identity()
    service = GoodsReceiptService(db.session)
    receipt = service.get_goods_receipt(
        tenant_id=identity.tenant_id,
        branch_id=identity.branch_id,
        receipt_id=receipt_id,
    )

    return jsonify(
        {
            "ok": True,
            "item": serialize_goods_receipt(
                receipt,
                **service.serialization_context(receipt),
            ),
        }
    )


@bp.get("/inventory/stock-adjustments")
@require_permission("inventory.adjust")
def list_stock_adjustments():
    identity = _current_identity()
    service = StockAdjustmentService(db.session)

    try:
        filters = StockAdjustmentListFilters.from_query(request.args)
        items, pagination = service.list_stock_adjustments(
            tenant_id=identity.tenant_id,
            branch_id=identity.branch_id,
            filters=filters,
        )
    except StockAdjustmentQueryError as exc:
        return _json_error(str(exc), 400)

    return jsonify(
        {
            "ok": True,
            "items": items,
            "pagination": pagination,
        }
    )


@bp.post("/inventory/stock-adjustments")
@require_permission("inventory.adjust")
def create_stock_adjustment():
    identity = _current_identity()
    payload = request.get_json(silent=True) or {}
    service = StockAdjustmentService(db.session)
    adjustment = service.create_manual_adjustment(
        tenant_id=identity.tenant_id,
        branch_id=identity.branch_id,
        posted_by=identity.user_id,
        request=CreateStockAdjustmentRequest.from_payload(payload),
    )

    return (
        jsonify(
            {
                "ok": True,
                "message": "Stock adjustment posted successfully.",
                "item": serialize_stock_adjustment(
                    adjustment,
                    **service.serialization_context(adjustment),
                ),
            }
        ),
        201,
    )


@bp.get("/inventory/stock-adjustments/<adjustment_id>")
@require_permission("inventory.adjust")
def get_stock_adjustment(adjustment_id: str):
    identity = _current_identity()
    service = StockAdjustmentService(db.session)
    adjustment = service.get_stock_adjustment(
        tenant_id=identity.tenant_id,
        branch_id=identity.branch_id,
        adjustment_id=adjustment_id,
    )

    return jsonify(
        {
            "ok": True,
            "item": serialize_stock_adjustment(
                adjustment,
                **service.serialization_context(adjustment),
            ),
        }
    )


@bp.post("/inventory/stock-counts")
@require_permission("inventory.count")
def create_stock_count():
    identity = _current_identity()
    payload = request.get_json(silent=True) or {}
    service = StockCountService(db.session)
    count = service.create_stock_count(
        tenant_id=identity.tenant_id,
        branch_id=identity.branch_id,
        started_by=identity.user_id,
        request=CreateStockCountRequest.from_payload(payload),
    )

    return (
        jsonify(
            {
                "ok": True,
                "message": "Stock count created successfully.",
                "item": serialize_stock_count(
                    count,
                    **service.serialization_context(count),
                ),
            }
        ),
        201,
    )


@bp.post("/inventory/stock-counts/<count_id>/adjust")
@require_permission("inventory.adjust")
def create_stock_adjustment_from_count(count_id: str):
    identity = _current_identity()
    payload = request.get_json(silent=True) or {}
    service = StockAdjustmentService(db.session)
    adjustment = service.create_adjustment_from_stock_count(
        tenant_id=identity.tenant_id,
        branch_id=identity.branch_id,
        count_id=count_id,
        posted_by=identity.user_id,
        request=CreateStockAdjustmentFromCountRequest.from_payload(payload),
    )

    return (
        jsonify(
            {
                "ok": True,
                "message": "Stock adjustment posted successfully.",
                "item": serialize_stock_adjustment(
                    adjustment,
                    **service.serialization_context(adjustment),
                ),
            }
        ),
        201,
    )


@bp.get("/inventory/stock-counts")
@require_permission("inventory.count")
def list_stock_counts():
    identity = _current_identity()
    service = StockCountService(db.session)

    try:
        filters = StockCountListFilters.from_query(request.args)
        items, pagination = service.list_stock_counts(
            tenant_id=identity.tenant_id,
            branch_id=identity.branch_id,
            filters=filters,
        )
    except StockCountQueryError as exc:
        return _json_error(str(exc), 400)

    return jsonify(
        {
            "ok": True,
            "items": items,
            "pagination": pagination,
        }
    )


@bp.get("/inventory/stock-counts/<count_id>")
@require_permission("inventory.count")
def get_stock_count(count_id: str):
    identity = _current_identity()
    service = StockCountService(db.session)
    count = service.get_stock_count(
        tenant_id=identity.tenant_id,
        branch_id=identity.branch_id,
        count_id=count_id,
    )

    return jsonify(
        {
            "ok": True,
            "item": serialize_stock_count(
                count,
                **service.serialization_context(count),
            ),
        }
    )


@bp.post("/inventory/stock-counts/<count_id>/items/discovered")
@require_permission("inventory.count")
def add_discovered_stock_count_item(count_id: str):
    """
    Record physical stock discovered during an open Stock Count.

    This endpoint records counting evidence only. It does not create an
    InventoryBatch, mutate StockBalance, or post an InventoryMovement.

    For blind counts, expected quantities and variance information remain
    concealed by the Stock Count serializer while the count is open.
    """

    identity = _current_identity()
    payload = request.get_json(silent=True) or {}

    service = StockCountService(db.session)

    service.add_discovered_item(
        tenant_id=identity.tenant_id,
        branch_id=identity.branch_id,
        count_id=count_id,
        counted_by=identity.user_id,
        request=AddDiscoveredStockCountItemRequest.from_payload(
            payload
        ),
    )

    count = service.get_stock_count(
        tenant_id=identity.tenant_id,
        branch_id=identity.branch_id,
        count_id=count_id,
    )

    return (
        jsonify(
            {
                "ok": True,
                "message": (
                    "Discovered stock count item recorded successfully."
                ),
                "item": serialize_stock_count(
                    count,
                    **service.serialization_context(count),
                ),
            }
        ),
        201,
    )


@bp.put("/inventory/stock-counts/<count_id>/items/<item_id>")
@require_permission("inventory.count")
def update_stock_count_item(count_id: str, item_id: str):
    identity = _current_identity()
    payload = request.get_json(silent=True) or {}
    service = StockCountService(db.session)
    count = service.update_stock_count_item(
        tenant_id=identity.tenant_id,
        branch_id=identity.branch_id,
        count_id=count_id,
        item_id=item_id,
        counted_by=identity.user_id,
        request=UpdateStockCountItemRequest.from_payload(payload),
    )

    return jsonify(
        {
            "ok": True,
            "message": "Stock count item updated successfully.",
            "item": serialize_stock_count(
                count,
                **service.serialization_context(count),
            ),
        }
    )


@bp.post(
    "/inventory/stock-counts/<count_id>/"
    "scope-products/<product_id>/confirm-no-stock"
)
@require_permission("inventory.count")
def confirm_stock_count_no_stock(
    count_id: str,
    product_id: str,
):
    identity = _current_identity()
    service = StockCountService(db.session)

    count = service.confirm_no_stock(
        tenant_id=identity.tenant_id,
        branch_id=identity.branch_id,
        count_id=count_id,
        product_id=product_id,
        confirmed_by=identity.user_id,
    )

    return jsonify(
        {
            "ok": True,
            "message": "No stock found confirmed successfully.",
            "item": serialize_stock_count(
                count,
                **service.serialization_context(count),
            ),
        }
    )


@bp.post("/inventory/stock-counts/<count_id>/complete")
@require_permission("inventory.count")
def complete_stock_count(count_id: str):
    identity = _current_identity()
    service = StockCountService(db.session)
    count = service.complete_stock_count(
        tenant_id=identity.tenant_id,
        branch_id=identity.branch_id,
        count_id=count_id,
        completed_by=identity.user_id,
    )

    return jsonify(
        {
            "ok": True,
            "message": "Stock count completed successfully.",
            "item": serialize_stock_count(
                count,
                **service.serialization_context(count),
            ),
        }
    )


@bp.post("/inventory/stock-counts/<count_id>/cancel")
@require_permission("inventory.count")
def cancel_stock_count(count_id: str):
    identity = _current_identity()
    service = StockCountService(db.session)
    count = service.cancel_stock_count(
        tenant_id=identity.tenant_id,
        branch_id=identity.branch_id,
        count_id=count_id,
        cancelled_by=identity.user_id,
    )

    return jsonify(
        {
            "ok": True,
            "message": "Stock count cancelled successfully.",
            "item": serialize_stock_count(
                count,
                **service.serialization_context(count),
            ),
        }
    )
