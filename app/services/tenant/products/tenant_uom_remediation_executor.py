"""
Tenant UOM remediation execution boundary.

C5E3A established execution preflight and provenance.

C5E3B adds execution of LINK_EXISTING_UOM only.

This phase deliberately does NOT mutate:
- Product.unit_id
- ProductUnit rows
- inventory, sales, receipts, or historical evidence

Transaction ownership remains with the caller.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.models import (
    CanonicalUnitOfMeasure,
    TenantUOMRemediationReview,
    UnitOfMeasure,
    User,
)
from app.services.common.audit_actions import AuditAction
from app.services.common.audit_modules import AuditModule
from app.services.common.audit_service import AuditService
from app.services.tenant.products.tenant_uom_audit_service import (
    SAFE_TO_LINK,
)
from app.services.tenant.products.tenant_uom_remediation_planner import (
    LINK_EXISTING_UOM,
)
from app.services.tenant.products.tenant_uom_remediation_review_service import (
    REVIEW_SELECTED_ACTIONS,
    TenantUOMRemediationReviewService,
)


def utcnow():
    return datetime.now(timezone.utc)


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


@dataclass(frozen=True, slots=True)
class TenantUOMRemediationExecutionResult:
    review_id: str
    tenant_id: str
    source_uom_id: str
    selected_action: str
    selected_canonical_uom_id: str
    status: str
    changed: bool
    execution_summary: dict


class TenantUOMRemediationExecutor:
    """
    Governed tenant UOM remediation execution boundary.

    C5E3B supports LINK_EXISTING_UOM only.

    Transaction ownership remains with the caller.
    """

    def __init__(
        self,
        session,
        *,
        review_service: (
            TenantUOMRemediationReviewService | None
        ) = None,
        audit_service=None,
    ) -> None:
        self.session = session
        self.review_service = (
            review_service
            if review_service is not None
            else TenantUOMRemediationReviewService(
                session
            )
        )
        self.audit_service = (
            audit_service
            if audit_service is not None
            else AuditService()
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

    def execute_link_existing_uom(
        self,
        *,
        tenant_id: str,
        review_id: str,
        executed_by: str,
    ) -> TenantUOMRemediationExecutionResult:
        """
        Execute one approved SAFE_TO_LINK review.

        The only operational data mutation in this phase is:

            UnitOfMeasure.canonical_uom_id

        Product and ProductUnit structure is untouched.
        """

        preflight = self.preflight(
            tenant_id=tenant_id,
            review_id=review_id,
            executed_by=executed_by,
        )

        if (
            preflight.selected_action
            != LINK_EXISTING_UOM
        ):
            raise TenantUOMRemediationExecutionError(
                "C5E3B can execute only LINK_EXISTING_UOM "
                "remediation reviews.",
                409,
            )

        review = self._get_review_for_update(
            tenant_id=tenant_id,
            review_id=review_id,
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

        if review.selected_action != LINK_EXISTING_UOM:
            raise TenantUOMRemediationExecutionError(
                "The remediation review no longer contains "
                "LINK_EXISTING_UOM as its approved action.",
                409,
            )

        if review.audit_classification != SAFE_TO_LINK:
            raise TenantUOMRemediationExecutionError(
                "Only SAFE_TO_LINK remediation reviews may "
                "execute LINK_EXISTING_UOM.",
                409,
            )

        canonical_uom_id = (
            review.selected_canonical_uom_id
        )

        if not canonical_uom_id:
            raise TenantUOMRemediationExecutionError(
                "Approved LINK_EXISTING_UOM review has no "
                "selected canonical UOM.",
                409,
            )

        actor = self._get_user(
            tenant_id=tenant_id,
            user_id=executed_by,
        )

        source_uom = self._get_tenant_uom_for_update(
            tenant_id=tenant_id,
            uom_id=str(review.source_uom_id),
        )

        canonical_uom = self._get_canonical_uom(
            canonical_uom_id=str(
                canonical_uom_id
            )
        )

        locked_staleness = (
            self.review_service.assess_staleness(
                tenant_id=tenant_id,
                review_id=str(review.id),
            )
        )

        if locked_staleness.is_stale:
            raise TenantUOMRemediationExecutionError(
                "The approved remediation review became stale "
                "before execution. Supersede it and create a "
                "new review.",
                409,
            )

        if source_uom.canonical_uom_id is not None:
            raise TenantUOMRemediationExecutionError(
                "The source tenant UOM is already canonically "
                "linked. The approved review no longer matches "
                "the executable operational state.",
                409,
            )

        old_values = {
            "status": review.status,
            "source_uom_id":
                str(source_uom.id),
            "source_canonical_uom_id":
                source_uom.canonical_uom_id,
            "executed_by":
                review.executed_by,
            "executed_at":
                (
                    review.executed_at.isoformat()
                    if review.executed_at
                    else None
                ),
        }

        now = utcnow()

        source_uom.canonical_uom_id = str(
            canonical_uom.id
        )

        execution_summary = {
            "action": LINK_EXISTING_UOM,
            "audit_classification":
                review.audit_classification,
            "source_uom_id":
                str(source_uom.id),
            "canonical_uom_id":
                str(canonical_uom.id),
            "operational_link_changed": True,
            "product_changes": 0,
            "product_unit_changes": 0,
            "historical_records_changed": 0,
        }

        review.status = "executed"
        review.executed_by = str(actor.id)
        review.executed_at = now
        review.execution_summary = execution_summary
        review.updated_at = now

        self.session.flush()

        self.audit_service.log(
            module=AuditModule.CATALOGUE,
            action=(
                AuditAction
                .UOM_REMEDIATION_REVIEW_EXECUTED
            ),
            entity_type=(
                "tenant_uom_remediation_review"
            ),
            tenant_id=tenant_id,
            entity_id=str(review.id),
            user_id=str(actor.id),
            old_values=old_values,
            new_values={
                "status": "executed",
                "source_uom_id":
                    str(source_uom.id),
                "source_canonical_uom_id":
                    str(canonical_uom.id),
                "executed_by":
                    str(actor.id),
                "executed_at":
                    now.isoformat(),
            },
            details=execution_summary,
            reason=review.review_reason,
            commit=False,
        )

        self.session.flush()

        return TenantUOMRemediationExecutionResult(
            review_id=str(review.id),
            tenant_id=str(review.tenant_id),
            source_uom_id=str(
                source_uom.id
            ),
            selected_action=(
                LINK_EXISTING_UOM
            ),
            selected_canonical_uom_id=str(
                canonical_uom.id
            ),
            status="executed",
            changed=True,
            execution_summary=(
                execution_summary
            ),
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

    def _get_review_for_update(
        self,
        *,
        tenant_id: str,
        review_id: str,
    ) -> TenantUOMRemediationReview:
        review = (
            self.session.query(
                TenantUOMRemediationReview
            )
            .filter(
                TenantUOMRemediationReview.id
                == review_id,
                TenantUOMRemediationReview.tenant_id
                == tenant_id,
            )
            .with_for_update()
            .first()
        )

        if review is None:
            raise TenantUOMRemediationExecutionError(
                "UOM remediation review was not found.",
                404,
            )

        return review

    def _get_tenant_uom_for_update(
        self,
        *,
        tenant_id: str,
        uom_id: str,
    ) -> UnitOfMeasure:
        unit = (
            self.session.query(UnitOfMeasure)
            .filter(
                UnitOfMeasure.id == uom_id,
                UnitOfMeasure.tenant_id
                == tenant_id,
            )
            .with_for_update()
            .first()
        )

        if unit is None:
            raise TenantUOMRemediationExecutionError(
                "Source tenant UOM was not found.",
                404,
            )

        return unit

    def _get_canonical_uom(
        self,
        *,
        canonical_uom_id: str,
    ) -> CanonicalUnitOfMeasure:
        unit = (
            self.session.query(
                CanonicalUnitOfMeasure
            )
            .filter(
                CanonicalUnitOfMeasure.id
                == canonical_uom_id,
                CanonicalUnitOfMeasure.is_active
                .is_(True),
            )
            .first()
        )

        if unit is None:
            raise TenantUOMRemediationExecutionError(
                "Canonical UOM was not found or is inactive.",
                404,
            )

        return unit


__all__ = [
    "TenantUOMRemediationExecutionError",
    "TenantUOMRemediationExecutionPreflight",
    "TenantUOMRemediationExecutionResult",
    "TenantUOMRemediationExecutor",
]
