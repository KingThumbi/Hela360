from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.extensions import db
from app.models import Sale, User
from app.models.pos import SaleActionRequest
from app.services.refunds import RefundService, RefundError


def utcnow():
    return datetime.now(timezone.utc)


class ApprovalError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class SaleApprovalService:
    def __init__(self, session):
        self.session = session

    def create_refund_request(self, tenant_id: str, sale_id: str, requested_by: str, payload: dict) -> SaleActionRequest:
        sale = self._get_sale_or_404(tenant_id, sale_id)
        self._ensure_no_pending_request(tenant_id, sale_id, "refund_sale")

        reason = (payload.get("reason") or "").strip()
        if not reason:
            raise ApprovalError("reason is required.", 400)

        user = self._get_user_or_404(tenant_id, requested_by, "Requesting user")

        request_row = SaleActionRequest(
            id=str(uuid4()),
            tenant_id=tenant_id,
            sale_id=sale.id,
            action_type="refund_sale",
            status="pending",
            requested_by=user.id,
            request_reason=reason,
            request_payload=payload,
            requires_approval=True,
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        self.session.add(request_row)
        self.session.flush()
        return request_row

    def create_void_request(self, tenant_id: str, sale_id: str, requested_by: str, payload: dict) -> SaleActionRequest:
        sale = self._get_sale_or_404(tenant_id, sale_id)
        self._ensure_no_pending_request(tenant_id, sale_id, "void_sale")

        reason = (payload.get("reason") or "").strip()
        if not reason:
            raise ApprovalError("reason is required.", 400)

        user = self._get_user_or_404(tenant_id, requested_by, "Requesting user")

        request_row = SaleActionRequest(
            id=str(uuid4()),
            tenant_id=tenant_id,
            sale_id=sale.id,
            action_type="void_sale",
            status="pending",
            requested_by=user.id,
            request_reason=reason,
            request_payload=payload,
            requires_approval=True,
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        self.session.add(request_row)
        self.session.flush()
        return request_row

    def approve_request(self, tenant_id: str, request_id: str, approved_by: str, decision_reason: str | None = None):
        request_row = self._get_request_or_404(tenant_id, request_id)
        approver = self._get_user_or_404(tenant_id, approved_by, "Approver")

        self._require_pending(request_row)
        self._require_admin(approver)
        self._prevent_self_approval(request_row, approver.id)

        now = utcnow()
        request_row.status = "approved"
        request_row.approved_by = approver.id
        request_row.decision_reason = (decision_reason or "").strip() or None
        request_row.approved_at = now
        request_row.updated_at = now
        self.session.flush()

        if request_row.action_type == "refund_sale":
            refund = RefundService(self.session).create_refund(
                tenant_id=tenant_id,
                sale_id=request_row.sale_id,
                payload=request_row.request_payload or {},
            )
            request_row.status = "executed"
            request_row.executed_at = utcnow()
            request_row.updated_at = utcnow()
            self.session.flush()
            return {"request": request_row, "result": refund, "result_type": "refund"}

        if request_row.action_type == "void_sale":
            sale = self._execute_void_sale(
                tenant_id=tenant_id,
                sale_id=request_row.sale_id,
                payload=request_row.request_payload or {},
            )
            request_row.status = "executed"
            request_row.executed_at = utcnow()
            request_row.updated_at = utcnow()
            self.session.flush()
            return {"request": request_row, "result": sale, "result_type": "sale"}

        raise ApprovalError(f"Unsupported action_type: {request_row.action_type}", 400)

    def reject_request(self, tenant_id: str, request_id: str, rejected_by: str, decision_reason: str | None = None):
        request_row = self._get_request_or_404(tenant_id, request_id)
        rejector = self._get_user_or_404(tenant_id, rejected_by, "Rejecting user")

        self._require_pending(request_row)
        self._require_admin(rejector)
        self._prevent_self_approval(request_row, rejector.id)

        now = utcnow()
        request_row.status = "rejected"
        request_row.rejected_by = rejector.id
        request_row.decision_reason = (decision_reason or "").strip() or None
        request_row.rejected_at = now
        request_row.updated_at = now
        self.session.flush()
        return request_row

    def _get_sale_or_404(self, tenant_id: str, sale_id: str):
        sale = (
            self.session.query(Sale)
            .filter(Sale.id == sale_id, Sale.tenant_id == tenant_id)
            .first()
        )
        if not sale:
            raise ApprovalError("Sale not found.", 404)
        return sale

    def _get_user_or_404(self, tenant_id: str, user_id: str, label: str):
        user = (
            self.session.query(User)
            .filter(User.id == user_id, User.tenant_id == tenant_id)
            .first()
        )
        if not user:
            raise ApprovalError(f"{label} not found.", 404)
        return user

    def _get_request_or_404(self, tenant_id: str, request_id: str):
        request_row = (
            self.session.query(SaleActionRequest)
            .filter(SaleActionRequest.id == request_id, SaleActionRequest.tenant_id == tenant_id)
            .first()
        )
        if not request_row:
            raise ApprovalError("Action request not found.", 404)
        return request_row

    def _ensure_no_pending_request(self, tenant_id: str, sale_id: str, action_type: str):
        existing = (
            self.session.query(SaleActionRequest)
            .filter(
                SaleActionRequest.tenant_id == tenant_id,
                SaleActionRequest.sale_id == sale_id,
                SaleActionRequest.action_type == action_type,
                SaleActionRequest.status == "pending",
            )
            .first()
        )
        if existing:
            raise ApprovalError(f"A pending {action_type} request already exists for this sale.", 409)

    def _require_pending(self, request_row: SaleActionRequest):
        if request_row.status != "pending":
            raise ApprovalError(f"Only pending requests can be processed. Current status: {request_row.status}.", 409)

    def _prevent_self_approval(self, request_row: SaleActionRequest, actor_id: str):
       # if str(request_row.requested_by) == str(actor_id):
        #    raise ApprovalError("Requester cannot approve or reject their own request.", 403)
        return #remove this and replace the above to 
    def _require_admin(self, user):
        email = (getattr(user, "email", "") or "").strip().lower()

        if email == "admin@hela360.local":
            return

            raise ApprovalError("Only admin can approve or reject action requests.", 403)
    def _execute_void_sale(self, tenant_id: str, sale_id: str, payload: dict):
        """
        Reuse your existing void logic helper if you refactor it later.
        For now this imports lazily to avoid circular imports.
        """
        from app.api.sales import get_sale_items_for_sale, restore_stock_for_void, now_utc

        sale = self._get_sale_or_404(tenant_id, sale_id)

        current_status = (getattr(sale, "status", "") or "").strip().lower()
        if current_status == "voided":
            raise ApprovalError("Sale is already voided.", 409)

        branch_id = getattr(sale, "branch_id", None)
        warehouse_id = getattr(sale, "warehouse_id", None)
        cashier_id = getattr(sale, "cashier_id", None)

        if not branch_id or not warehouse_id or not cashier_id:
            raise ApprovalError("Sale is missing branch_id, warehouse_id, or cashier_id.", 400)

        reason = (payload.get("reason") or "").strip()
        sale_items = get_sale_items_for_sale(str(sale.id))
        if not sale_items:
            raise ApprovalError("Sale has no items to void.", 400)

        from decimal import Decimal

        for item in sale_items:
            quantity = Decimal(str(getattr(item, "quantity", 0)))
            product_id = getattr(item, "product_id", None)
            if not product_id:
                raise ApprovalError(f"Sale item {item.id} has no product_id.", 400)

            restore_stock_for_void(
                tenant_id=tenant_id,
                branch_id=str(branch_id),
                warehouse_id=str(warehouse_id),
                sale_id=str(sale.id),
                product_id=product_id,
                quantity=quantity,
                created_by=str(cashier_id),
            )

        sale.status = "voided"
        if hasattr(sale, "updated_at"):
            sale.updated_at = now_utc()

        if hasattr(sale, "notes"):
            existing_notes = (getattr(sale, "notes", None) or "").strip()
            void_note = "Sale voided via approval"
            if reason:
                void_note = f"{void_note}: {reason}"
            sale.notes = f"{existing_notes}\n{void_note}".strip() if existing_notes else void_note

        self.session.flush()
        return sale