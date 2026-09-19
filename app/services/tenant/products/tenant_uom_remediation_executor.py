"""
Tenant UOM remediation execution boundary.

C5E3A established execution preflight and provenance.
C5E3B added governed LINK_EXISTING_UOM execution.
C5E3C added governed SPLIT_CURRENT_PRODUCTS execution.
C5E3D added governed non-mutating terminal execution.
C5E3E added governed KEEP_UNMAPPED terminal execution.
C5E3F adds generic execution dispatch across approved actions.

C5E3C may replace the current Product/ProductUnit base-unit
structure only through explicit approved product decisions.

Historical ProductUnit identity, unit identity, conversion factors,
and transactional evidence must never be rewritten.

Transaction ownership remains with the caller.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

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
    TenantUOMAuditService,
)
from app.services.tenant.products.tenant_uom_remediation_planner import (
    LINK_EXISTING_UOM,
    NO_ACTION,
    PRESERVE_HISTORICAL_UNIT,
    SPLIT_CURRENT_PRODUCTS,
)
from app.services.tenant.products.tenant_uom_remediation_review_service import (
    KEEP_CURRENT_PRODUCT,
    KEEP_UNMAPPED,
    MOVE_CURRENT_PRODUCT,
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
    selected_canonical_uom_id: str | None
    status: str
    changed: bool
    execution_summary: dict


class TenantUOMRemediationExecutor:
    """
    Governed tenant UOM remediation execution boundary.

    Supports governed execution for LINK_EXISTING_UOM,
    SPLIT_CURRENT_PRODUCTS, KEEP_UNMAPPED,
    PRESERVE_HISTORICAL_UNIT, and NO_ACTION.

    execute_review() is the generic orchestration entry point.
    Specialized executors remain available and authoritative.

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

    def execute_review(
        self,
        *,
        tenant_id: str,
        review_id: str,
        executed_by: str,
    ) -> TenantUOMRemediationExecutionResult:
        """
        Dispatch an approved remediation review to its
        specialized governed executor.

        The specialized executor remains authoritative for
        preflight, locking, staleness checks, mutation rules,
        audit provenance, and transaction ownership.
        """
        review = self.review_service.get_review(
            tenant_id=tenant_id,
            review_id=review_id,
        )

        selected_action = (
            review.selected_action or ""
        ).strip()

        dispatch = {
            LINK_EXISTING_UOM:
                self.execute_link_existing_uom,
            SPLIT_CURRENT_PRODUCTS:
                self.execute_split_current_products,
            KEEP_UNMAPPED:
                self.execute_keep_unmapped,
            PRESERVE_HISTORICAL_UNIT:
                self.execute_preserve_historical_unit,
            NO_ACTION:
                self.execute_no_action,
        }

        executor = dispatch.get(selected_action)

        if executor is None:
            raise TenantUOMRemediationExecutionError(
                "The remediation review does not contain a "
                "supported executable action.",
                409,
            )

        return executor(
            tenant_id=tenant_id,
            review_id=review_id,
            executed_by=executed_by,
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

    def execute_split_current_products(
        self,
        *,
        tenant_id: str,
        review_id: str,
        executed_by: str,
    ) -> TenantUOMRemediationExecutionResult:
        """
        Execute an approved mixed-semantics product split.

        C5E3C may mutate:
        - Product.unit_id
        - current ProductUnit lifecycle/base flags
        - source UnitOfMeasure.canonical_uom_id when KEEP decisions
          establish the identity retained by the source UOM

        Historical ProductUnit identity, unit_id, and conversion
        factor are never rewritten.
        """

        preflight = self.preflight(
            tenant_id=tenant_id,
            review_id=review_id,
            executed_by=executed_by,
        )

        if (
            preflight.selected_action
            != SPLIT_CURRENT_PRODUCTS
        ):
            raise TenantUOMRemediationExecutionError(
                "C5E3C can execute only SPLIT_CURRENT_PRODUCTS "
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

        if (
            review.selected_action
            != SPLIT_CURRENT_PRODUCTS
        ):
            raise TenantUOMRemediationExecutionError(
                "The remediation review no longer contains "
                "SPLIT_CURRENT_PRODUCTS as its approved action.",
                409,
            )

        if (
            review.audit_classification
            != MIXED_PRODUCT_SEMANTICS
        ):
            raise TenantUOMRemediationExecutionError(
                "Only MIXED_PRODUCT_SEMANTICS reviews may "
                "execute SPLIT_CURRENT_PRODUCTS.",
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

        decisions = self._get_decisions_for_update(
            tenant_id=tenant_id,
            review_id=str(review.id),
        )

        if not decisions:
            raise TenantUOMRemediationExecutionError(
                "The split remediation review contains no "
                "product decisions.",
                409,
            )

        keep_decisions = [
            row
            for row in decisions
            if row.selected_action
            == KEEP_CURRENT_PRODUCT
        ]

        move_decisions = [
            row
            for row in decisions
            if row.selected_action
            == MOVE_CURRENT_PRODUCT
        ]

        if (
            len(keep_decisions)
            + len(move_decisions)
            != len(decisions)
        ):
            raise TenantUOMRemediationExecutionError(
                "The split remediation review contains an "
                "unsupported product decision.",
                409,
            )

        retained_canonical = None

        if keep_decisions:
            if not review.selected_canonical_uom_id:
                raise TenantUOMRemediationExecutionError(
                    "KEEP_CURRENT_PRODUCT decisions require the "
                    "approved source canonical UOM identity.",
                    409,
                )

            retained_canonical = self._get_canonical_uom(
                canonical_uom_id=str(
                    review.selected_canonical_uom_id
                )
            )

            if source_uom.canonical_uom_id is not None:
                raise TenantUOMRemediationExecutionError(
                    "The source tenant UOM is already canonically "
                    "linked. The approved split review no longer "
                    "matches the executable state.",
                    409,
                )

        prepared_moves = []

        for decision in decisions:
            product = self._get_product_for_update(
                tenant_id=tenant_id,
                product_id=str(decision.product_id),
            )

            if product.unit_id != str(source_uom.id):
                raise TenantUOMRemediationExecutionError(
                    "A reviewed product no longer uses the source "
                    "tenant UOM.",
                    409,
                )

            product_units = (
                self._get_product_units_for_update(
                    tenant_id=tenant_id,
                    product_id=str(product.id),
                )
            )

            base_units = [
                row
                for row in product_units
                if row.is_base
            ]

            if len(base_units) != 1:
                raise TenantUOMRemediationExecutionError(
                    "Reviewed product must have exactly one "
                    "current base ProductUnit.",
                    409,
                )

            current_base = base_units[0]

            if (
                current_base.unit_id
                != product.unit_id
            ):
                raise TenantUOMRemediationExecutionError(
                    "Product base ProductUnit does not match "
                    "Product.unit_id.",
                    409,
                )

            if Decimal(
                str(
                    current_base
                    .conversion_factor_to_base
                )
            ) != Decimal("1"):
                raise TenantUOMRemediationExecutionError(
                    "Current base ProductUnit must have "
                    "conversion_factor_to_base = 1.",
                    409,
                )

            if (
                decision.source_product_unit_id
                and str(current_base.id)
                != str(
                    decision.source_product_unit_id
                )
            ):
                raise TenantUOMRemediationExecutionError(
                    "The reviewed source ProductUnit no longer "
                    "matches the current base ProductUnit.",
                    409,
                )

            if (
                decision.selected_action
                == KEEP_CURRENT_PRODUCT
            ):
                continue

            if not decision.target_tenant_uom_id:
                raise TenantUOMRemediationExecutionError(
                    "MOVE_CURRENT_PRODUCT requires an approved "
                    "target_tenant_uom_id.",
                    409,
                )

            target_uom = self._get_tenant_uom_for_update(
                tenant_id=tenant_id,
                uom_id=str(
                    decision.target_tenant_uom_id
                ),
            )

            if str(target_uom.id) == str(source_uom.id):
                raise TenantUOMRemediationExecutionError(
                    "MOVE_CURRENT_PRODUCT target must differ "
                    "from the source tenant UOM.",
                    409,
                )

            if decision.target_canonical_uom_id:
                target_canonical = (
                    self._get_canonical_uom(
                        canonical_uom_id=str(
                            decision
                            .target_canonical_uom_id
                        )
                    )
                )

                if (
                    target_uom.canonical_uom_id
                    is not None
                    and str(
                        target_uom.canonical_uom_id
                    )
                    != str(target_canonical.id)
                ):
                    raise TenantUOMRemediationExecutionError(
                        "Target tenant UOM canonical identity "
                        "no longer matches the approved decision.",
                        409,
                    )

            target_product_unit = next(
                (
                    row
                    for row in product_units
                    if row.unit_id
                    == str(target_uom.id)
                ),
                None,
            )

            if target_product_unit is not None:
                if Decimal(
                    str(
                        target_product_unit
                        .conversion_factor_to_base
                    )
                ) != Decimal("1"):
                    raise TenantUOMRemediationExecutionError(
                        "Existing target ProductUnit cannot become "
                        "base because its conversion factor is "
                        "not 1.",
                        409,
                    )

            prepared_moves.append(
                (
                    product,
                    current_base,
                    target_uom,
                    target_product_unit,
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
                "before split execution. Supersede it and create "
                "a new review.",
                409,
            )

        old_values = {
            "status": review.status,
            "source_uom_id": str(source_uom.id),
            "source_canonical_uom_id":
                source_uom.canonical_uom_id,
            "executed_by": review.executed_by,
            "executed_at": (
                review.executed_at.isoformat()
                if review.executed_at
                else None
            ),
        }

        product_summaries = []

        for (
            product,
            current_base,
            target_uom,
            target_product_unit,
        ) in prepared_moves:
            old_base_id = str(current_base.id)
            old_base_unit_id = str(
                current_base.unit_id
            )
            old_base_factor = str(
                current_base
                .conversion_factor_to_base
            )

            current_base.is_base = False
            current_base.is_active = False
            current_base.can_sell = False
            current_base.can_receive = False

            # Release the partial unique base index before
            # promoting/creating the replacement base row.
            self.session.flush()

            if target_product_unit is None:
                target_product_unit = ProductUnit(
                    tenant_id=tenant_id,
                    product_id=str(product.id),
                    unit_id=str(target_uom.id),
                    conversion_factor_to_base=Decimal(
                        "1"
                    ),
                    is_base=True,
                    can_sell=True,
                    can_receive=True,
                    is_active=True,
                )

                self.session.add(
                    target_product_unit
                )
            else:
                target_product_unit.is_base = True
                target_product_unit.is_active = True
                target_product_unit.can_sell = True
                target_product_unit.can_receive = True

            product.unit_id = str(target_uom.id)

            self.session.flush()

            final_bases = (
                self.session.query(ProductUnit)
                .filter(
                    ProductUnit.tenant_id
                    == tenant_id,
                    ProductUnit.product_id
                    == str(product.id),
                    ProductUnit.is_base.is_(True),
                )
                .all()
            )

            if len(final_bases) != 1:
                raise TenantUOMRemediationExecutionError(
                    "Split execution failed the one-base "
                    "ProductUnit invariant.",
                    409,
                )

            final_base = final_bases[0]

            if (
                final_base.unit_id
                != product.unit_id
                or final_base.unit_id
                != str(target_uom.id)
                or not final_base.is_active
                or Decimal(
                    str(
                        final_base
                        .conversion_factor_to_base
                    )
                )
                != Decimal("1")
            ):
                raise TenantUOMRemediationExecutionError(
                    "Split execution failed the replacement "
                    "base ProductUnit invariant.",
                    409,
                )

            if (
                str(current_base.id)
                != old_base_id
                or str(current_base.unit_id)
                != old_base_unit_id
                or str(
                    current_base
                    .conversion_factor_to_base
                )
                != old_base_factor
            ):
                raise TenantUOMRemediationExecutionError(
                    "Historical ProductUnit identity or factor "
                    "changed during split execution.",
                    409,
                )

            product_summaries.append(
                {
                    "product_id":
                        str(product.id),
                    "action":
                        MOVE_CURRENT_PRODUCT,
                    "old_product_unit_id":
                        old_base_id,
                    "old_unit_id":
                        old_base_unit_id,
                    "new_product_unit_id":
                        str(final_base.id),
                    "new_unit_id":
                        str(target_uom.id),
                }
            )

        if retained_canonical is not None:
            source_uom.canonical_uom_id = str(
                retained_canonical.id
            )

        now = utcnow()

        execution_summary = {
            "action": SPLIT_CURRENT_PRODUCTS,
            "audit_classification":
                review.audit_classification,
            "source_uom_id":
                str(source_uom.id),
            "source_canonical_uom_id": (
                str(retained_canonical.id)
                if retained_canonical is not None
                else None
            ),
            "keep_product_count":
                len(keep_decisions),
            "moved_product_count":
                len(prepared_moves),
            "product_changes":
                len(prepared_moves),
            "product_unit_changes":
                len(prepared_moves) * 2,
            "historical_records_changed": 0,
            "products": product_summaries,
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
                "source_canonical_uom_id": (
                    str(retained_canonical.id)
                    if retained_canonical
                    is not None
                    else None
                ),
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
            source_uom_id=str(source_uom.id),
            selected_action=(
                SPLIT_CURRENT_PRODUCTS
            ),
            selected_canonical_uom_id=(
                str(retained_canonical.id)
                if retained_canonical is not None
                else None
            ),
            status="executed",
            changed=True,
            execution_summary=execution_summary,
        )

    def execute_keep_unmapped(
        self,
        *,
        tenant_id: str,
        review_id: str,
        executed_by: str,
    ) -> TenantUOMRemediationExecutionResult:
        """
        Execute an approved KEEP_UNMAPPED review.

        This terminal human decision preserves the tenant UOM
        without canonical linkage or product-level remediation.
        """
        preflight = self.preflight(
            tenant_id=tenant_id,
            review_id=review_id,
            executed_by=executed_by,
        )

        if preflight.selected_action != KEEP_UNMAPPED:
            raise TenantUOMRemediationExecutionError(
                "C5E3E unmapped execution can execute only "
                "KEEP_UNMAPPED remediation reviews.",
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

        if review.selected_action != KEEP_UNMAPPED:
            raise TenantUOMRemediationExecutionError(
                "The remediation review no longer contains "
                "KEEP_UNMAPPED as its approved action.",
                409,
            )

        allowed_classifications = {
            SAFE_TO_LINK,
            CUSTOM_UNMAPPED,
            DOSAGE_FORM_AS_UOM,
            LEGACY_PRODUCT_SPECIFIC,
        }

        if (
            review.audit_classification
            not in allowed_classifications
        ):
            raise TenantUOMRemediationExecutionError(
                "KEEP_UNMAPPED is not valid for the stored "
                "audit classification.",
                409,
            )

        if review.selected_canonical_uom_id is not None:
            raise TenantUOMRemediationExecutionError(
                "KEEP_UNMAPPED cannot execute with a selected "
                "canonical UOM.",
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

        decisions = self._get_decisions_for_update(
            tenant_id=tenant_id,
            review_id=str(review.id),
        )

        selected_decisions = [
            decision
            for decision in decisions
            if (
                decision.selected_action is not None
                or decision.target_canonical_uom_id is not None
                or decision.target_tenant_uom_id is not None
                or decision.preserve_historical_unit is not True
                or decision.review_note is not None
            )
        ]

        if selected_decisions:
            raise TenantUOMRemediationExecutionError(
                "KEEP_UNMAPPED cannot execute with product-level "
                "remediation decisions.",
                409,
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
                "before KEEP_UNMAPPED execution. Supersede it "
                "and create a new review.",
                409,
            )

        locked_audit = TenantUOMAuditService(
            self.session
        ).audit_unit(
            tenant_id=tenant_id,
            uom_id=str(source_uom.id),
        )

        if (
            locked_audit.classification
            != review.audit_classification
        ):
            raise TenantUOMRemediationExecutionError(
                "The source tenant UOM no longer has the "
                "approved audit classification.",
                409,
            )

        if (
            locked_audit.classification
            not in allowed_classifications
        ):
            raise TenantUOMRemediationExecutionError(
                "The source tenant UOM is no longer eligible "
                "for KEEP_UNMAPPED.",
                409,
            )

        if source_uom.canonical_uom_id is not None:
            raise TenantUOMRemediationExecutionError(
                "KEEP_UNMAPPED requires the source tenant UOM "
                "to remain without canonical linkage.",
                409,
            )

        old_values = {
            "status": review.status,
            "source_uom_id": str(source_uom.id),
            "source_canonical_uom_id":
                source_uom.canonical_uom_id,
            "executed_by": review.executed_by,
            "executed_at": (
                review.executed_at.isoformat()
                if review.executed_at
                else None
            ),
        }

        now = utcnow()

        execution_summary = {
            "action": KEEP_UNMAPPED,
            "audit_classification":
                review.audit_classification,
            "source_uom_id": str(source_uom.id),
            "source_canonical_uom_id":
                source_uom.canonical_uom_id,
            "operational_link_changed": False,
            "product_changes": 0,
            "product_unit_changes": 0,
            "historical_records_changed": 0,
            "product_decision_count": len(decisions),
            "selected_product_decision_count": 0,
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
            entity_type="tenant_uom_remediation_review",
            tenant_id=tenant_id,
            entity_id=str(review.id),
            user_id=str(actor.id),
            old_values=old_values,
            new_values={
                "status": "executed",
                "source_uom_id": str(source_uom.id),
                "source_canonical_uom_id":
                    source_uom.canonical_uom_id,
                "executed_by": str(actor.id),
                "executed_at": now.isoformat(),
            },
            details=execution_summary,
            reason=review.review_reason,
            commit=False,
        )

        self.session.flush()

        return TenantUOMRemediationExecutionResult(
            review_id=str(review.id),
            tenant_id=str(review.tenant_id),
            source_uom_id=str(source_uom.id),
            selected_action=KEEP_UNMAPPED,
            selected_canonical_uom_id=None,
            status="executed",
            changed=False,
            execution_summary=execution_summary,
        )

    def execute_preserve_historical_unit(
        self,
        *,
        tenant_id: str,
        review_id: str,
        executed_by: str,
    ) -> TenantUOMRemediationExecutionResult:
        """
        Execute an approved HISTORICAL_ONLY preservation review.

        This is intentionally non-mutating for operational UOM,
        Product, ProductUnit, inventory, sales, and historical
        transactional evidence.
        """
        preflight = self.preflight(
            tenant_id=tenant_id,
            review_id=review_id,
            executed_by=executed_by,
        )

        if (
            preflight.selected_action
            != PRESERVE_HISTORICAL_UNIT
        ):
            raise TenantUOMRemediationExecutionError(
                "C5E3D historical execution can execute only "
                "PRESERVE_HISTORICAL_UNIT remediation reviews.",
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

        if (
            review.selected_action
            != PRESERVE_HISTORICAL_UNIT
        ):
            raise TenantUOMRemediationExecutionError(
                "The remediation review no longer contains "
                "PRESERVE_HISTORICAL_UNIT as its approved action.",
                409,
            )

        if review.audit_classification != HISTORICAL_ONLY:
            raise TenantUOMRemediationExecutionError(
                "Only HISTORICAL_ONLY remediation reviews may "
                "execute PRESERVE_HISTORICAL_UNIT.",
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

        locked_staleness = (
            self.review_service.assess_staleness(
                tenant_id=tenant_id,
                review_id=str(review.id),
            )
        )

        if locked_staleness.is_stale:
            raise TenantUOMRemediationExecutionError(
                "The approved remediation review became stale "
                "before historical-preservation execution. "
                "Supersede it and create a new review.",
                409,
            )

        locked_audit = TenantUOMAuditService(
            self.session
        ).audit_unit(
            tenant_id=tenant_id,
            uom_id=str(source_uom.id),
        )

        if locked_audit.classification != HISTORICAL_ONLY:
            raise TenantUOMRemediationExecutionError(
                "The source tenant UOM is no longer "
                "HISTORICAL_ONLY.",
                409,
            )

        old_values = {
            "status": review.status,
            "source_uom_id": str(source_uom.id),
            "source_canonical_uom_id":
                source_uom.canonical_uom_id,
            "executed_by": review.executed_by,
            "executed_at": (
                review.executed_at.isoformat()
                if review.executed_at
                else None
            ),
        }

        now = utcnow()

        execution_summary = {
            "action": PRESERVE_HISTORICAL_UNIT,
            "audit_classification":
                review.audit_classification,
            "source_uom_id": str(source_uom.id),
            "source_canonical_uom_id":
                source_uom.canonical_uom_id,
            "operational_link_changed": False,
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
                    source_uom.canonical_uom_id,
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
            source_uom_id=str(source_uom.id),
            selected_action=PRESERVE_HISTORICAL_UNIT,
            selected_canonical_uom_id=(
                review.selected_canonical_uom_id
            ),
            status="executed",
            changed=False,
            execution_summary=execution_summary,
        )

    def execute_no_action(
        self,
        *,
        tenant_id: str,
        review_id: str,
        executed_by: str,
    ) -> TenantUOMRemediationExecutionResult:
        """
        Execute an approved CANONICALLY_LINKED NO_ACTION review.

        Operational state is intentionally left unchanged.
        """
        preflight = self.preflight(
            tenant_id=tenant_id,
            review_id=review_id,
            executed_by=executed_by,
        )

        if preflight.selected_action != NO_ACTION:
            raise TenantUOMRemediationExecutionError(
                "C5E3D no-action execution can execute only "
                "NO_ACTION remediation reviews.",
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

        if review.selected_action != NO_ACTION:
            raise TenantUOMRemediationExecutionError(
                "The remediation review no longer contains "
                "NO_ACTION as its approved action.",
                409,
            )

        if (
            review.audit_classification
            != CANONICALLY_LINKED
        ):
            raise TenantUOMRemediationExecutionError(
                "Only CANONICALLY_LINKED remediation reviews may "
                "execute NO_ACTION.",
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

        locked_staleness = (
            self.review_service.assess_staleness(
                tenant_id=tenant_id,
                review_id=str(review.id),
            )
        )

        if locked_staleness.is_stale:
            raise TenantUOMRemediationExecutionError(
                "The approved remediation review became stale "
                "before NO_ACTION execution. Supersede it and "
                "create a new review.",
                409,
            )

        locked_audit = TenantUOMAuditService(
            self.session
        ).audit_unit(
            tenant_id=tenant_id,
            uom_id=str(source_uom.id),
        )

        if (
            locked_audit.classification
            != CANONICALLY_LINKED
        ):
            raise TenantUOMRemediationExecutionError(
                "The source tenant UOM is no longer "
                "CANONICALLY_LINKED.",
                409,
            )

        old_values = {
            "status": review.status,
            "source_uom_id": str(source_uom.id),
            "source_canonical_uom_id":
                source_uom.canonical_uom_id,
            "executed_by": review.executed_by,
            "executed_at": (
                review.executed_at.isoformat()
                if review.executed_at
                else None
            ),
        }

        now = utcnow()

        execution_summary = {
            "action": NO_ACTION,
            "audit_classification":
                review.audit_classification,
            "source_uom_id": str(source_uom.id),
            "source_canonical_uom_id":
                source_uom.canonical_uom_id,
            "operational_link_changed": False,
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
                    source_uom.canonical_uom_id,
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
            source_uom_id=str(source_uom.id),
            selected_action=NO_ACTION,
            selected_canonical_uom_id=(
                review.selected_canonical_uom_id
            ),
            status="executed",
            changed=False,
            execution_summary=execution_summary,
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

    def _get_decisions_for_update(
        self,
        *,
        tenant_id: str,
        review_id: str,
    ) -> tuple[
        TenantUOMRemediationProductDecision,
        ...,
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
            .with_for_update()
            .all()
        )

        return tuple(rows)

    def _get_product_for_update(
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
            .with_for_update()
            .first()
        )

        if product is None:
            raise TenantUOMRemediationExecutionError(
                "Reviewed product was not found.",
                404,
            )

        return product

    def _get_product_units_for_update(
        self,
        *,
        tenant_id: str,
        product_id: str,
    ) -> tuple[ProductUnit, ...]:
        rows = (
            self.session.query(ProductUnit)
            .filter(
                ProductUnit.tenant_id
                == tenant_id,
                ProductUnit.product_id
                == product_id,
            )
            .order_by(ProductUnit.id)
            .with_for_update()
            .all()
        )

        if not rows:
            raise TenantUOMRemediationExecutionError(
                "Reviewed product has no ProductUnit rows.",
                409,
            )

        return tuple(rows)

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
