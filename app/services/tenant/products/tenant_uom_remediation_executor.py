"""
Tenant UOM remediation execution boundary.

C5E3A provides execution preflight only.

It deliberately does NOT yet mutate:
- UnitOfMeasure.canonical_uom_id
- Product.unit_id
- ProductUnit rows
- inventory, sales, receipts, or historical evidence
- remediation review execution status

Operational execution is added in later C5E3 phases.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models import User
from app.services.tenant.products.tenant_uom_remediation_review_service import (
    REVIEW_SELECTED_ACTIONS,
    TenantUOMRemediationReviewService,
)


class TenantUOMRemediationExecutionError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 400,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True, slots=True)
class TenantUOMRemediationExecutionPreflight:
    review_id: str
    tenant_id: str
    source_uom_id: str
    status: str
    selected_action: str
    product_decision_count: int
    planner_fingerprint: str
    is_stale: bool
    can_execute: bool


class TenantUOMRemediationExecutor:
    """
    Validate whether an approved remediation review is safe
    to enter the operational execution phase.

    Transaction ownership remains with the caller.
    """

    def __init__(
        self,
        session,
        *,
        review_service: (
            TenantUOMRemediationReviewService | None
        ) = None,
    ) -> None:
        self.session = session
        self.review_service = (
            review_service
            if review_service is not None
            else TenantUOMRemediationReviewService(
                session
            )
        )

    def preflight(
        self,
        *,
        tenant_id: str,
        review_id: str,
        executed_by: str,
    ) -> TenantUOMRemediationExecutionPreflight:
        review = self.review_service.get_review(
            tenant_id=tenant_id,
            review_id=review_id,
        )

        self._get_user(
            tenant_id=tenant_id,
            user_id=executed_by,
        )

        if review.status == "executed":
            raise TenantUOMRemediationExecutionError(
                "The remediation review has already been executed.",
                409,
            )

        if review.status != "approved":
            raise TenantUOMRemediationExecutionError(
                "Only an approved remediation review may be executed.",
                409,
            )

        selected_action = (
            review.selected_action or ""
        ).strip()

        if not selected_action:
            raise TenantUOMRemediationExecutionError(
                "Approved remediation review has no selected action.",
                409,
            )

        if selected_action not in REVIEW_SELECTED_ACTIONS:
            raise TenantUOMRemediationExecutionError(
                "Approved remediation review contains an "
                "unsupported selected action.",
                409,
            )

        staleness = (
            self.review_service.assess_staleness(
                tenant_id=tenant_id,
                review_id=review.id,
            )
        )

        if staleness.is_stale:
            raise TenantUOMRemediationExecutionError(
                "The approved remediation review is stale. "
                "Supersede it and create a new review "
                "before execution.",
                409,
            )

        detail = (
            self.review_service.get_review_detail(
                tenant_id=tenant_id,
                review_id=review.id,
                include_staleness=False,
            )
        )

        decision_count = len(
            detail["product_decisions"]
        )

        return TenantUOMRemediationExecutionPreflight(
            review_id=str(review.id),
            tenant_id=str(review.tenant_id),
            source_uom_id=str(
                review.source_uom_id
            ),
            status=review.status,
            selected_action=selected_action,
            product_decision_count=decision_count,
            planner_fingerprint=(
                review.planner_fingerprint
            ),
            is_stale=False,
            can_execute=True,
        )

    def _get_user(
        self,
        *,
        tenant_id: str,
        user_id: str,
    ) -> User:
        user = (
            self.session.query(User)
            .filter(
                User.id == user_id,
                User.tenant_id == tenant_id,
                User.is_active.is_(True),
            )
            .first()
        )

        if user is None:
            raise TenantUOMRemediationExecutionError(
                "Executing user was not found or is inactive.",
                404,
            )

        return user


__all__ = [
    "TenantUOMRemediationExecutionError",
    "TenantUOMRemediationExecutionPreflight",
    "TenantUOMRemediationExecutor",
]
