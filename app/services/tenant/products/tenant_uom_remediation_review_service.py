"""
Tenant UOM remediation human-review lifecycle.

This service persists planner evidence and explicit human decisions.

It deliberately does NOT execute remediation. It must not mutate
UnitOfMeasure, Product, ProductUnit, inventory, sales, or canonical
catalogue records. Execution belongs to C5E3.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from uuid import uuid4

from app.models import (
    CanonicalUnitOfMeasure,
    Product,
    ProductUnit,
    TenantUOMRemediationProductDecision,
    TenantUOMRemediationReview,
    UnitOfMeasure,
    User,
)
from app.services.common.audit_actions import AuditAction
from app.services.common.audit_modules import AuditModule
from app.services.common.audit_service import AuditService
from app.services.tenant.products.tenant_uom_audit_service import (
    CANONICALLY_LINKED,
    CUSTOM_UNMAPPED,
    DOSAGE_FORM_AS_UOM,
    HISTORICAL_ONLY,
    LEGACY_PRODUCT_SPECIFIC,
    MIXED_PRODUCT_SEMANTICS,
    SAFE_TO_LINK,
)
from app.services.tenant.products.tenant_uom_remediation_planner import (
    LINK_EXISTING_UOM,
    NO_ACTION,
    PRESERVE_HISTORICAL_UNIT,
    SPLIT_CURRENT_PRODUCTS,
    TenantUOMRemediationPlan,
    TenantUOMRemediationPlanner,
)


PLANNER_VERSION = "3F.6C5E1"

KEEP_UNMAPPED = "KEEP_UNMAPPED"
MOVE_CURRENT_PRODUCT = "MOVE_CURRENT_PRODUCT"
KEEP_CURRENT_PRODUCT = "KEEP_CURRENT_PRODUCT"

REVIEW_SELECTED_ACTIONS = frozenset(
    {
        LINK_EXISTING_UOM,
        KEEP_UNMAPPED,
        SPLIT_CURRENT_PRODUCTS,
        PRESERVE_HISTORICAL_UNIT,
        NO_ACTION,
    }
)

PRODUCT_SELECTED_ACTIONS = frozenset(
    {
        MOVE_CURRENT_PRODUCT,
        KEEP_CURRENT_PRODUCT,
    }
)


def utcnow():
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class TenantUOMRemediationStaleness:
    review_id: str
    tenant_id: str
    source_uom_id: str

    is_stale: bool
    reasons: tuple[str, ...]

    stored_planner_version: str
    current_planner_version: str

    stored_fingerprint: str
    current_fingerprint: str

    current_snapshot: dict


class TenantUOMRemediationReviewError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 400,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class TenantUOMRemediationReviewService:
    """
    Persist and govern tenant UOM remediation reviews.

    Transaction ownership remains with the caller.
    """

    def __init__(
        self,
        session,
        *,
        planner: TenantUOMRemediationPlanner | None = None,
        audit_service: AuditService | None = None,
    ) -> None:
        self.session = session
        self.planner = (
            planner
            if planner is not None
            else TenantUOMRemediationPlanner(session)
        )
        self.audit_service = (
            audit_service
            if audit_service is not None
            else AuditService()
        )

    def create_pending_review(
        self,
        *,
        tenant_id: str,
        source_uom_id: str,
        created_by: str,
    ) -> TenantUOMRemediationReview:
        actor = self._get_user(
            tenant_id=tenant_id,
            user_id=created_by,
            label="Creating user",
        )

        self._get_tenant_uom(
            tenant_id=tenant_id,
            uom_id=source_uom_id,
            label="Source UOM",
        )

        existing = (
            self.session.query(
                TenantUOMRemediationReview
            )
            .filter(
                TenantUOMRemediationReview.tenant_id
                == tenant_id,
                TenantUOMRemediationReview.source_uom_id
                == source_uom_id,
                TenantUOMRemediationReview.status.in_(
                    ("pending", "approved")
                ),
            )
            .first()
        )

        if existing is not None:
            raise TenantUOMRemediationReviewError(
                "An active remediation review already exists "
                "for this tenant UOM.",
                409,
            )

        plan = self.planner.plan_unit(
            tenant_id=tenant_id,
            uom_id=source_uom_id,
        )

        snapshot = self._serialize_plan(plan)
        fingerprint = self._fingerprint(snapshot)

        review = TenantUOMRemediationReview(
            id=str(uuid4()),
            tenant_id=tenant_id,
            source_uom_id=source_uom_id,
            status="pending",
            audit_classification=plan.audit_classification,
            recommended_action=plan.recommended_action,
            suggested_canonical_code=(
                plan.suggested_canonical_code
            ),
            selected_action=None,
            selected_canonical_uom_id=None,
            planner_version=PLANNER_VERSION,
            planner_fingerprint=fingerprint,
            planner_snapshot=snapshot,
            created_by=str(actor.id),
            reviewed_by=None,
            reviewed_at=None,
            review_reason=None,
            created_at=utcnow(),
            updated_at=utcnow(),
        )

        self.session.add(review)

        # Persist the parent first so child ProductDecision rows
        # can safely reference review.id during the later flush.
        self.session.flush()

        for product_plan in plan.product_plans:
            decision = (
                TenantUOMRemediationProductDecision(
                    id=str(uuid4()),
                    review_id=review.id,
                    tenant_id=tenant_id,
                    product_id=product_plan.product_id,
                    source_product_unit_id=(
                        product_plan.current_product_unit_id
                    ),
                    recommended_action=(
                        product_plan.recommended_action
                    ),
                    suggested_canonical_code=(
                        product_plan.suggested_canonical_code
                    ),
                    selected_action=None,
                    target_canonical_uom_id=None,
                    target_tenant_uom_id=None,
                    preserve_historical_unit=True,
                    review_note=None,
                    created_at=utcnow(),
                    updated_at=utcnow(),
                )
            )
            self.session.add(decision)

        self.session.flush()

        self.audit_service.log(
            module=AuditModule.CATALOGUE,
            action=(
                AuditAction
                .UOM_REMEDIATION_REVIEW_CREATED
            ),
            entity_type="tenant_uom_remediation_review",
            tenant_id=tenant_id,
            entity_id=review.id,
            user_id=str(actor.id),
            new_values={
                "status": "pending",
                "source_uom_id": source_uom_id,
                "audit_classification":
                    plan.audit_classification,
                "recommended_action":
                    plan.recommended_action,
            },
            details={
                "planner_version": PLANNER_VERSION,
                "planner_fingerprint": fingerprint,
                "product_decision_count":
                    len(plan.product_plans),
            },
            commit=False,
        )

        self.session.flush()

        return review

    def get_review(
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
                TenantUOMRemediationReview.id == review_id,
                TenantUOMRemediationReview.tenant_id
                == tenant_id,
            )
            .first()
        )

        if review is None:
            raise TenantUOMRemediationReviewError(
                "UOM remediation review was not found.",
                404,
            )

        return review

    def get_review_detail(
        self,
        *,
        tenant_id: str,
        review_id: str,
        include_staleness: bool = True,
    ) -> dict:
        """
        Return tenant-scoped review governance state.

        The stored planner snapshot remains immutable evidence.
        Current staleness is calculated separately.
        """
        review = self.get_review(
            tenant_id=tenant_id,
            review_id=review_id,
        )

        decisions = self._review_decisions(
            tenant_id=tenant_id,
            review_id=review.id,
        )

        detail = {
            "review": review,
            "product_decisions": decisions,
            "staleness": None,
        }

        if include_staleness:
            detail["staleness"] = (
                self.assess_staleness(
                    tenant_id=tenant_id,
                    review_id=review.id,
                )
            )

        return detail

    def assess_staleness(
        self,
        *,
        tenant_id: str,
        review_id: str,
    ) -> TenantUOMRemediationStaleness:
        """
        Recompute planner evidence and compare it with the
        immutable evidence stored on the review.

        This method is read-only. It never changes review status
        and never mutates operational UOM/Product/ProductUnit data.
        """
        review = self.get_review(
            tenant_id=tenant_id,
            review_id=review_id,
        )

        current_plan = self.planner.plan_unit(
            tenant_id=tenant_id,
            uom_id=review.source_uom_id,
        )

        current_snapshot = self._serialize_plan(
            current_plan
        )
        current_fingerprint = self._fingerprint(
            current_snapshot
        )

        reasons = []

        if review.planner_version != PLANNER_VERSION:
            reasons.append(
                "planner_version_changed"
            )

        if (
            review.planner_fingerprint
            != current_fingerprint
        ):
            reasons.append(
                "planner_fingerprint_changed"
            )

        return TenantUOMRemediationStaleness(
            review_id=str(review.id),
            tenant_id=str(review.tenant_id),
            source_uom_id=str(
                review.source_uom_id
            ),
            is_stale=bool(reasons),
            reasons=tuple(reasons),
            stored_planner_version=(
                review.planner_version
            ),
            current_planner_version=PLANNER_VERSION,
            stored_fingerprint=(
                review.planner_fingerprint
            ),
            current_fingerprint=current_fingerprint,
            current_snapshot=current_snapshot,
        )

    def list_reviews(
        self,
        *,
        tenant_id: str,
        status: str | None = None,
    ) -> tuple[TenantUOMRemediationReview, ...]:
        query = (
            self.session.query(
                TenantUOMRemediationReview
            )
            .filter(
                TenantUOMRemediationReview.tenant_id
                == tenant_id
            )
        )

        if status is not None:
            normalized = status.strip().lower()

            if normalized not in {
                "pending",
                "approved",
                "rejected",
                "superseded",
                "executed",
            }:
                raise TenantUOMRemediationReviewError(
                    "Unsupported remediation review status.",
                    400,
                )

            query = query.filter(
                TenantUOMRemediationReview.status
                == normalized
            )

        rows = (
            query.order_by(
                TenantUOMRemediationReview.created_at.desc(),
                TenantUOMRemediationReview.id.desc(),
            )
            .all()
        )

        return tuple(rows)

    def approve_review(
        self,
        *,
        tenant_id: str,
        review_id: str,
        reviewed_by: str,
        selected_action: str,
        selected_canonical_uom_id: str | None = None,
        product_decisions: list[dict] | None = None,
        review_reason: str | None = None,
    ) -> TenantUOMRemediationReview:
        review = self.get_review(
            tenant_id=tenant_id,
            review_id=review_id,
        )

        actor = self._get_user(
            tenant_id=tenant_id,
            user_id=reviewed_by,
            label="Reviewing user",
        )

        self._require_status(
            review=review,
            allowed={"pending"},
            operation="approve",
        )

        if str(actor.id) == str(review.created_by):
            raise TenantUOMRemediationReviewError(
                "A remediation review cannot be approved "
                "by the user who created it.",
                409,
            )

        staleness = self.assess_staleness(
            tenant_id=tenant_id,
            review_id=review.id,
        )

        if staleness.is_stale:
            raise TenantUOMRemediationReviewError(
                "The remediation review is stale. "
                "Supersede it and create a new review "
                "before approval.",
                409,
            )

        selected_action = (
            selected_action or ""
        ).strip()

        if selected_action not in REVIEW_SELECTED_ACTIONS:
            raise TenantUOMRemediationReviewError(
                "Unsupported remediation review action.",
                400,
            )

        selected_canonical = None

        if selected_canonical_uom_id:
            selected_canonical = self._get_canonical_uom(
                canonical_uom_id=(
                    selected_canonical_uom_id
                )
            )

        self._validate_review_action(
            review=review,
            selected_action=selected_action,
            selected_canonical=selected_canonical,
        )

        decisions = self._review_decisions(
            tenant_id=tenant_id,
            review_id=review.id,
        )

        submitted = product_decisions or []

        if (
            selected_action == KEEP_UNMAPPED
            and submitted
        ):
            raise TenantUOMRemediationReviewError(
                "KEEP_UNMAPPED does not accept product decisions.",
                400,
            )

        self._apply_product_decisions(
            review=review,
            persisted_decisions=decisions,
            submitted_decisions=submitted,
            selected_canonical=selected_canonical,
        )

        now = utcnow()

        old_values = {
            "status": review.status,
            "selected_action": review.selected_action,
            "selected_canonical_uom_id":
                review.selected_canonical_uom_id,
        }

        review.status = "approved"
        review.selected_action = selected_action
        review.selected_canonical_uom_id = (
            str(selected_canonical.id)
            if selected_canonical is not None
            else None
        )
        review.reviewed_by = str(actor.id)
        review.reviewed_at = now
        review.review_reason = (
            (review_reason or "").strip() or None
        )
        review.updated_at = now

        self.session.flush()

        self.audit_service.log(
            module=AuditModule.CATALOGUE,
            action=(
                AuditAction
                .UOM_REMEDIATION_REVIEW_APPROVED
            ),
            entity_type="tenant_uom_remediation_review",
            tenant_id=tenant_id,
            entity_id=review.id,
            user_id=str(actor.id),
            old_values=old_values,
            new_values={
                "status": "approved",
                "selected_action": selected_action,
                "selected_canonical_uom_id": (
                    review.selected_canonical_uom_id
                ),
            },
            details={
                "planner_fingerprint":
                    review.planner_fingerprint,
                "product_decision_count":
                    len(decisions),
            },
            reason=review.review_reason,
            commit=False,
        )

        self.session.flush()

        return review

    def reject_review(
        self,
        *,
        tenant_id: str,
        review_id: str,
        reviewed_by: str,
        review_reason: str,
    ) -> TenantUOMRemediationReview:
        review = self.get_review(
            tenant_id=tenant_id,
            review_id=review_id,
        )

        actor = self._get_user(
            tenant_id=tenant_id,
            user_id=reviewed_by,
            label="Reviewing user",
        )

        self._require_status(
            review=review,
            allowed={"pending"},
            operation="reject",
        )

        reason = (review_reason or "").strip()

        if not reason:
            raise TenantUOMRemediationReviewError(
                "review_reason is required when rejecting "
                "a remediation review.",
                400,
            )

        old_status = review.status
        now = utcnow()

        review.status = "rejected"
        review.reviewed_by = str(actor.id)
        review.reviewed_at = now
        review.review_reason = reason
        review.updated_at = now

        self.session.flush()

        self.audit_service.log(
            module=AuditModule.CATALOGUE,
            action=(
                AuditAction
                .UOM_REMEDIATION_REVIEW_REJECTED
            ),
            entity_type="tenant_uom_remediation_review",
            tenant_id=tenant_id,
            entity_id=review.id,
            user_id=str(actor.id),
            old_values={"status": old_status},
            new_values={"status": "rejected"},
            reason=reason,
            commit=False,
        )

        self.session.flush()

        return review

    def supersede_review(
        self,
        *,
        tenant_id: str,
        review_id: str,
        reviewed_by: str,
        review_reason: str,
    ) -> TenantUOMRemediationReview:
        review = self.get_review(
            tenant_id=tenant_id,
            review_id=review_id,
        )

        actor = self._get_user(
            tenant_id=tenant_id,
            user_id=reviewed_by,
            label="Reviewing user",
        )

        self._require_status(
            review=review,
            allowed={"pending", "approved"},
            operation="supersede",
        )

        reason = (review_reason or "").strip()

        if not reason:
            raise TenantUOMRemediationReviewError(
                "review_reason is required when superseding "
                "a remediation review.",
                400,
            )

        old_status = review.status
        now = utcnow()

        review.status = "superseded"
        review.reviewed_by = str(actor.id)
        review.reviewed_at = now
        review.review_reason = reason
        review.updated_at = now

        self.session.flush()

        self.audit_service.log(
            module=AuditModule.CATALOGUE,
            action=(
                AuditAction
                .UOM_REMEDIATION_REVIEW_SUPERSEDED
            ),
            entity_type="tenant_uom_remediation_review",
            tenant_id=tenant_id,
            entity_id=review.id,
            user_id=str(actor.id),
            old_values={"status": old_status},
            new_values={"status": "superseded"},
            reason=reason,
            commit=False,
        )

        self.session.flush()

        return review

    def _validate_review_action(
        self,
        *,
        review: TenantUOMRemediationReview,
        selected_action: str,
        selected_canonical,
    ) -> None:
        classification = review.audit_classification

        if classification == MIXED_PRODUCT_SEMANTICS:
            if selected_action != SPLIT_CURRENT_PRODUCTS:
                raise TenantUOMRemediationReviewError(
                    "Mixed product semantics require "
                    "SPLIT_CURRENT_PRODUCTS.",
                    400,
                )

        if classification == HISTORICAL_ONLY:
            if selected_action != PRESERVE_HISTORICAL_UNIT:
                raise TenantUOMRemediationReviewError(
                    "Historical-only UOMs must be preserved.",
                    400,
                )

        if classification == CANONICALLY_LINKED:
            if selected_action != NO_ACTION:
                raise TenantUOMRemediationReviewError(
                    "Already-linked UOMs require NO_ACTION.",
                    400,
                )

        if selected_action == KEEP_UNMAPPED:
            if classification not in {
                SAFE_TO_LINK,
                CUSTOM_UNMAPPED,
                DOSAGE_FORM_AS_UOM,
                LEGACY_PRODUCT_SPECIFIC,
            }:
                raise TenantUOMRemediationReviewError(
                    "KEEP_UNMAPPED is valid only for unresolved "
                    "or deliberately unlinked tenant UOMs.",
                    400,
                )

            if selected_canonical is not None:
                raise TenantUOMRemediationReviewError(
                    "KEEP_UNMAPPED cannot select a canonical UOM.",
                    400,
                )

        if selected_action == LINK_EXISTING_UOM:
            if selected_canonical is None:
                raise TenantUOMRemediationReviewError(
                    "selected_canonical_uom_id is required "
                    "when linking a tenant UOM.",
                    400,
                )

            if classification not in {SAFE_TO_LINK}:
                raise TenantUOMRemediationReviewError(
                    "Only SAFE_TO_LINK reviews may globally "
                    "link the existing tenant UOM.",
                    400,
                )

        if classification in {
            CUSTOM_UNMAPPED,
            DOSAGE_FORM_AS_UOM,
            LEGACY_PRODUCT_SPECIFIC,
        }:
            if selected_action == LINK_EXISTING_UOM:
                raise TenantUOMRemediationReviewError(
                    "This source UOM cannot be globally linked "
                    "without product-level remediation.",
                    400,
                )

    def _apply_product_decisions(
        self,
        *,
        review: TenantUOMRemediationReview,
        persisted_decisions: tuple[
            TenantUOMRemediationProductDecision,
            ...
        ],
        submitted_decisions: list[dict],
        selected_canonical,
    ) -> None:
        persisted_by_product = {
            row.product_id: row
            for row in persisted_decisions
        }

        submitted_by_product = {}

        for payload in submitted_decisions:
            product_id = str(
                payload.get("product_id") or ""
            ).strip()

            if not product_id:
                raise TenantUOMRemediationReviewError(
                    "Each product decision requires product_id.",
                    400,
                )

            if product_id in submitted_by_product:
                raise TenantUOMRemediationReviewError(
                    "Duplicate product decision.",
                    400,
                )

            if product_id not in persisted_by_product:
                raise TenantUOMRemediationReviewError(
                    "Product does not belong to this "
                    "remediation review.",
                    400,
                )

            submitted_by_product[product_id] = payload

        if (
            review.audit_classification
            == MIXED_PRODUCT_SEMANTICS
        ):
            expected = set(persisted_by_product)
            received = set(submitted_by_product)

            if expected != received:
                raise TenantUOMRemediationReviewError(
                    "Every product in a mixed UOM review "
                    "requires an explicit decision.",
                    400,
                )

        for product_id, payload in (
            submitted_by_product.items()
        ):
            row = persisted_by_product[product_id]

            self._get_product(
                tenant_id=review.tenant_id,
                product_id=product_id,
            )

            action = str(
                payload.get("selected_action") or ""
            ).strip()

            if action not in PRODUCT_SELECTED_ACTIONS:
                raise TenantUOMRemediationReviewError(
                    "Unsupported product remediation action.",
                    400,
                )

            target_canonical_id = (
                payload.get("target_canonical_uom_id")
            )
            target_tenant_uom_id = (
                payload.get("target_tenant_uom_id")
            )

            target_canonical = None
            target_tenant_uom = None

            if target_canonical_id:
                target_canonical = (
                    self._get_canonical_uom(
                        canonical_uom_id=str(
                            target_canonical_id
                        )
                    )
                )

            if target_tenant_uom_id:
                target_tenant_uom = (
                    self._get_tenant_uom(
                        tenant_id=review.tenant_id,
                        uom_id=str(
                            target_tenant_uom_id
                        ),
                        label="Target tenant UOM",
                    )
                )

            if action == MOVE_CURRENT_PRODUCT:
                if target_tenant_uom is None:
                    raise TenantUOMRemediationReviewError(
                        "Moving a product requires an explicit "
                        "target_tenant_uom_id.",
                        400,
                    )

            if action == KEEP_CURRENT_PRODUCT:
                if selected_canonical is None:
                    raise TenantUOMRemediationReviewError(
                        "Keeping a product on a mixed source UOM "
                        "requires selecting the canonical identity "
                        "that the source UOM will retain.",
                        400,
                    )

            if (
                target_canonical is not None
                and target_tenant_uom is not None
                and (
                    target_tenant_uom.canonical_uom_id
                    is None
                    or str(
                        target_tenant_uom.canonical_uom_id
                    )
                    != str(target_canonical.id)
                )
            ):
                raise TenantUOMRemediationReviewError(
                    "Target tenant UOM must be canonically mapped "
                    "to target_canonical_uom_id.",
                    400,
                )

            preserve = payload.get(
                "preserve_historical_unit",
                True,
            )

            history_count = (
                self._snapshot_history_count(
                    review=review,
                    product_id=product_id,
                )
            )

            if history_count > 0 and preserve is not True:
                raise TenantUOMRemediationReviewError(
                    "ProductUnit history exists and must be "
                    "preserved.",
                    400,
                )

            row.selected_action = action
            row.target_canonical_uom_id = (
                str(target_canonical.id)
                if target_canonical is not None
                else None
            )
            row.target_tenant_uom_id = (
                str(target_tenant_uom.id)
                if target_tenant_uom is not None
                else None
            )
            row.preserve_historical_unit = bool(
                preserve
            )
            row.review_note = (
                str(payload.get("review_note") or "")
                .strip()
                or None
            )
            row.updated_at = utcnow()

    def _snapshot_history_count(
        self,
        *,
        review: TenantUOMRemediationReview,
        product_id: str,
    ) -> int:
        snapshot = review.planner_snapshot or {}

        for product in snapshot.get("products", []):
            if str(product.get("product_id")) == product_id:
                return int(
                    product.get(
                        "historical_reference_count",
                        0,
                    )
                    or 0
                )

        return 0

    def _review_decisions(
        self,
        *,
        tenant_id: str,
        review_id: str,
    ) -> tuple[
        TenantUOMRemediationProductDecision,
        ...
    ]:
        rows = (
            self.session.query(
                TenantUOMRemediationProductDecision
            )
            .filter(
                TenantUOMRemediationProductDecision.tenant_id
                == tenant_id,
                TenantUOMRemediationProductDecision.review_id
                == review_id,
            )
            .order_by(
                TenantUOMRemediationProductDecision.product_id
            )
            .all()
        )

        return tuple(rows)

    def _get_user(
        self,
        *,
        tenant_id: str,
        user_id: str,
        label: str,
    ) -> User:
        user = (
            self.session.query(User)
            .filter(
                User.id == user_id,
                User.tenant_id == tenant_id,
            )
            .first()
        )

        if user is None:
            raise TenantUOMRemediationReviewError(
                f"{label} was not found.",
                404,
            )

        return user

    def _get_product(
        self,
        *,
        tenant_id: str,
        product_id: str,
    ) -> Product:
        product = (
            self.session.query(Product)
            .filter(
                Product.id == product_id,
                Product.tenant_id == tenant_id,
            )
            .first()
        )

        if product is None:
            raise TenantUOMRemediationReviewError(
                "Product was not found.",
                404,
            )

        return product

    def _get_tenant_uom(
        self,
        *,
        tenant_id: str,
        uom_id: str,
        label: str,
    ) -> UnitOfMeasure:
        unit = (
            self.session.query(UnitOfMeasure)
            .filter(
                UnitOfMeasure.id == uom_id,
                UnitOfMeasure.tenant_id == tenant_id,
            )
            .first()
        )

        if unit is None:
            raise TenantUOMRemediationReviewError(
                f"{label} was not found.",
                404,
            )

        return unit

    def _get_canonical_uom(
        self,
        *,
        canonical_uom_id: str,
    ) -> CanonicalUnitOfMeasure:
        unit = (
            self.session.query(CanonicalUnitOfMeasure)
            .filter(
                CanonicalUnitOfMeasure.id
                == canonical_uom_id,
                CanonicalUnitOfMeasure.is_active.is_(True),
            )
            .first()
        )

        if unit is None:
            raise TenantUOMRemediationReviewError(
                "Canonical UOM was not found or is inactive.",
                404,
            )

        return unit

    def _require_status(
        self,
        *,
        review: TenantUOMRemediationReview,
        allowed: set[str],
        operation: str,
    ) -> None:
        if review.status not in allowed:
            raise TenantUOMRemediationReviewError(
                "Cannot "
                f"{operation} remediation review from "
                f"status {review.status!r}.",
                409,
            )

    def _serialize_plan(
        self,
        plan: TenantUOMRemediationPlan,
    ) -> dict:
        return {
            "tenant_id": plan.tenant_id,
            "source_uom_id": plan.source_uom_id,
            "source_code": plan.source_code,
            "source_name": plan.source_name,
            "audit_classification":
                plan.audit_classification,
            "suggested_canonical_code":
                plan.suggested_canonical_code,
            "recommended_action":
                plan.recommended_action,
            "historical_reference_count":
                plan.historical_reference_count,
            "requires_human_approval":
                plan.requires_human_approval,
            "can_apply_automatically":
                plan.can_apply_automatically,
            "reasons": list(plan.reasons),
            "warnings": list(plan.warnings),
            "products": [
                {
                    "product_id":
                        product.product_id,
                    "internal_sku":
                        product.internal_sku,
                    "product_name":
                        product.product_name,
                    "product_active":
                        product.product_active,
                    "current_product_unit_id":
                        product.current_product_unit_id,
                    "current_product_unit_active":
                        product.current_product_unit_active,
                    "current_product_unit_is_base":
                        product.current_product_unit_is_base,
                    "goods_receipt_reference_count":
                        product.goods_receipt_reference_count,
                    "sale_reference_count":
                        product.sale_reference_count,
                    "historical_reference_count":
                        product.historical_reference_count,
                    "recommended_action":
                        product.recommended_action,
                    "suggested_canonical_code":
                        product.suggested_canonical_code,
                    "suggestion_confidence":
                        product.suggestion_confidence,
                    "semantic_evidence":
                        list(product.semantic_evidence),
                    "requires_human_approval":
                        product.requires_human_approval,
                    "warnings":
                        list(product.warnings),
                }
                for product in plan.product_plans
            ],
        }

    def _fingerprint(
        self,
        snapshot: dict,
    ) -> str:
        payload = json.dumps(
            snapshot,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")

        return sha256(payload).hexdigest()


__all__ = [
    "KEEP_CURRENT_PRODUCT",
    "KEEP_UNMAPPED",
    "MOVE_CURRENT_PRODUCT",
    "PLANNER_VERSION",
    "PRODUCT_SELECTED_ACTIONS",
    "REVIEW_SELECTED_ACTIONS",
    "TenantUOMRemediationReviewError",
    "TenantUOMRemediationReviewService",
    "TenantUOMRemediationStaleness",
]
