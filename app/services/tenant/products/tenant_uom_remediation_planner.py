"""
Hela360 Tenant UOM Remediation Planner
======================================

Read-only planning layer built on top of TenantUOMAuditService.

The planner converts audit findings into explicit reviewable remediation
proposals. It does NOT mutate UnitOfMeasure, Product, ProductUnit,
GoodsReceiptItem, SaleItem, or canonical catalogue records.

The planner is intentionally conservative:
- historical evidence is preserved;
- ambiguous operational units require human review;
- dosage form is never silently treated as operational UOM;
- mixed legacy UOM rows are planned at product level;
- execution belongs to a later approved remediation phase.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func

from app.models import (
    GoodsReceiptItem,
    Product,
    ProductUnit,
    SaleItem,
    UnitOfMeasure,
)
from app.services.tenant.products.tenant_uom_audit_service import (
    CANONICALLY_LINKED,
    CUSTOM_UNMAPPED,
    DOSAGE_FORM_AS_UOM,
    HISTORICAL_ONLY,
    LEGACY_PRODUCT_SPECIFIC,
    MIXED_PRODUCT_SEMANTICS,
    SAFE_TO_LINK,
    TenantUOMAuditItem,
    TenantUOMAuditService,
)


NO_ACTION = "NO_ACTION"
LINK_EXISTING_UOM = "LINK_EXISTING_UOM"
REVIEW_OPERATIONAL_UNIT = "REVIEW_OPERATIONAL_UNIT"
SPLIT_CURRENT_PRODUCTS = "SPLIT_CURRENT_PRODUCTS"
PRESERVE_HISTORICAL_UNIT = "PRESERVE_HISTORICAL_UNIT"
REVIEW_LEGACY_UNIT = "REVIEW_LEGACY_UNIT"


@dataclass(frozen=True, slots=True)
class TenantUOMProductPlan:
    product_id: str
    internal_sku: str
    product_name: str
    product_active: bool

    current_product_unit_id: str | None
    current_product_unit_active: bool | None
    current_product_unit_is_base: bool | None

    goods_receipt_reference_count: int
    sale_reference_count: int
    historical_reference_count: int

    recommended_action: str
    suggested_canonical_code: str | None
    suggestion_confidence: str | None
    semantic_evidence: tuple[str, ...]

    requires_human_approval: bool
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TenantUOMRemediationPlan:
    tenant_id: str
    source_uom_id: str
    source_code: str
    source_name: str

    audit_classification: str
    suggested_canonical_code: str | None

    recommended_action: str

    product_plans: tuple[TenantUOMProductPlan, ...]

    historical_reference_count: int

    requires_human_approval: bool
    can_apply_automatically: bool

    reasons: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TenantUOMRemediationResult:
    plans: tuple[TenantUOMRemediationPlan, ...]

    @property
    def total_count(self) -> int:
        return len(self.plans)

    def count(self, action: str) -> int:
        return sum(
            1
            for plan in self.plans
            if plan.recommended_action == action
        )


class TenantUOMRemediationPlanner:
    """
    Produce reviewable remediation plans without changing data.

    Transaction ownership remains with the caller.
    """

    def __init__(self, session) -> None:
        self.session = session
        self.audit_service = TenantUOMAuditService(
            session
        )

    def plan_tenant(
        self,
        *,
        tenant_id: str,
        include_linked: bool = False,
    ) -> TenantUOMRemediationResult:
        audit = self.audit_service.audit_tenant(
            tenant_id=tenant_id
        )

        plans = []

        for item in audit.items:
            if (
                item.classification == CANONICALLY_LINKED
                and not include_linked
            ):
                continue

            plans.append(
                self._plan_item(item)
            )

        return TenantUOMRemediationResult(
            plans=tuple(plans)
        )

    def plan_unit(
        self,
        *,
        tenant_id: str,
        uom_id: str,
    ) -> TenantUOMRemediationPlan:
        item = self.audit_service.audit_unit(
            tenant_id=tenant_id,
            uom_id=uom_id,
        )

        return self._plan_item(item)

    def _plan_item(
        self,
        item: TenantUOMAuditItem,
    ) -> TenantUOMRemediationPlan:
        product_plans = self._product_plans(
            item=item
        )

        action = self._recommended_action(item)

        warnings = []

        if item.historical_reference_count:
            warnings.append(
                "Operational history exists. Historical "
                "ProductUnit references must remain unchanged."
            )

        if item.classification == MIXED_PRODUCT_SEMANTICS:
            warnings.append(
                "This tenant UOM has conflicting current "
                "product semantics and must not be linked "
                "globally until current products are split."
            )

        if item.classification == DOSAGE_FORM_AS_UOM:
            warnings.append(
                "Dosage form does not prove the operational "
                "inventory unit. Human review must choose the "
                "appropriate current unit."
            )

        if item.classification == CUSTOM_UNMAPPED:
            warnings.append(
                "Current evidence does not prove a canonical "
                "operational unit."
            )

        if item.classification == LEGACY_PRODUCT_SPECIFIC:
            warnings.append(
                "Product-specific legacy UOM vocabulary must "
                "not be generalized across the tenant."
            )

        requires_human_approval = (
            action
            not in {
                NO_ACTION,
                LINK_EXISTING_UOM,
                PRESERVE_HISTORICAL_UNIT,
            }
        )

        can_apply_automatically = (
            action == LINK_EXISTING_UOM
            and item.safe_to_link
            and item.historical_reference_count == 0
        )

        return TenantUOMRemediationPlan(
            tenant_id=item.tenant_id,
            source_uom_id=item.uom_id,
            source_code=item.code,
            source_name=item.name,
            audit_classification=item.classification,
            suggested_canonical_code=(
                item.suggested_canonical_code
            ),
            recommended_action=action,
            product_plans=product_plans,
            historical_reference_count=(
                item.historical_reference_count
            ),
            requires_human_approval=(
                requires_human_approval
            ),
            can_apply_automatically=(
                can_apply_automatically
            ),
            reasons=item.reasons,
            warnings=tuple(warnings),
        )

    def _recommended_action(
        self,
        item: TenantUOMAuditItem,
    ) -> str:
        if item.classification == CANONICALLY_LINKED:
            return NO_ACTION

        if item.classification == SAFE_TO_LINK:
            return LINK_EXISTING_UOM

        if item.classification == HISTORICAL_ONLY:
            return PRESERVE_HISTORICAL_UNIT

        if item.classification == MIXED_PRODUCT_SEMANTICS:
            return SPLIT_CURRENT_PRODUCTS

        if item.classification == DOSAGE_FORM_AS_UOM:
            return REVIEW_OPERATIONAL_UNIT

        if item.classification == LEGACY_PRODUCT_SPECIFIC:
            return REVIEW_LEGACY_UNIT

        return REVIEW_OPERATIONAL_UNIT

    def _product_plans(
        self,
        *,
        item: TenantUOMAuditItem,
    ) -> tuple[TenantUOMProductPlan, ...]:
        products = (
            self.session.query(Product)
            .filter(
                Product.tenant_id == item.tenant_id,
                Product.unit_id == item.uom_id,
            )
            .order_by(
                Product.internal_sku,
                Product.id,
            )
            .all()
        )

        plans = []

        for product in products:
            product_unit = (
                self.session.query(ProductUnit)
                .filter(
                    ProductUnit.tenant_id
                    == item.tenant_id,
                    ProductUnit.product_id
                    == str(product.id),
                    ProductUnit.unit_id
                    == item.uom_id,
                    ProductUnit.is_base.is_(True),
                )
                .order_by(
                    ProductUnit.is_active.desc(),
                    ProductUnit.id,
                )
                .first()
            )

            gr_count = self._history_count(
                GoodsReceiptItem,
                product_unit,
            )
            sale_count = self._history_count(
                SaleItem,
                product_unit,
            )

            history_count = (
                gr_count + sale_count
            )

            warnings = []

            if history_count:
                warnings.append(
                    "This ProductUnit has operational history "
                    "and must be preserved as historical "
                    "evidence if the current product is moved."
                )

            recommended_action = (
                self._product_action(
                    item=item,
                    history_count=history_count,
                )
            )

            semantic_evidence = (
                self.audit_service
                .product_semantic_evidence(
                    product=product
                )
            )

            (
                product_suggestion,
                suggestion_confidence,
            ) = self._product_suggestion(
                item=item,
                evidence=semantic_evidence,
            )

            plans.append(
                TenantUOMProductPlan(
                    product_id=str(product.id),
                    internal_sku=product.internal_sku,
                    product_name=product.name,
                    product_active=bool(
                        product.is_active
                    ),
                    current_product_unit_id=(
                        str(product_unit.id)
                        if product_unit
                        else None
                    ),
                    current_product_unit_active=(
                        bool(product_unit.is_active)
                        if product_unit
                        else None
                    ),
                    current_product_unit_is_base=(
                        bool(product_unit.is_base)
                        if product_unit
                        else None
                    ),
                    goods_receipt_reference_count=(
                        gr_count
                    ),
                    sale_reference_count=(
                        sale_count
                    ),
                    historical_reference_count=(
                        history_count
                    ),
                    recommended_action=(
                        recommended_action
                    ),
                    suggested_canonical_code=(
                        product_suggestion
                    ),
                    suggestion_confidence=(
                        suggestion_confidence
                    ),
                    semantic_evidence=(
                        semantic_evidence.evidence_reasons
                    ),
                    requires_human_approval=(
                        recommended_action
                        not in {
                            NO_ACTION,
                            PRESERVE_HISTORICAL_UNIT,
                        }
                    ),
                    warnings=tuple(warnings),
                )
            )

        return tuple(plans)

    def _product_suggestion(
        self,
        *,
        item: TenantUOMAuditItem,
        evidence,
    ) -> tuple[str | None, str | None]:
        # Product-level suggestions are deliberately
        # limited to mixed current usage.
        #
        # Dosage-form misuse and custom UOMs still
        # require an explicit operational-unit decision.
        if (
            item.classification
            != MIXED_PRODUCT_SEMANTICS
        ):
            return None, None

        expected = (
            evidence.expected_canonical_codes
        )

        if len(expected) != 1:
            return None, None

        if evidence.incompatible_dosage_forms:
            return None, None

        return expected[0], "high"

    def _product_action(
        self,
        *,
        item: TenantUOMAuditItem,
        history_count: int,
    ) -> str:
        if item.classification == CANONICALLY_LINKED:
            return NO_ACTION

        if item.classification == HISTORICAL_ONLY:
            return PRESERVE_HISTORICAL_UNIT

        if item.classification == SAFE_TO_LINK:
            return LINK_EXISTING_UOM

        if item.classification == MIXED_PRODUCT_SEMANTICS:
            return REVIEW_OPERATIONAL_UNIT

        if item.classification == DOSAGE_FORM_AS_UOM:
            return REVIEW_OPERATIONAL_UNIT

        if item.classification == LEGACY_PRODUCT_SPECIFIC:
            return REVIEW_LEGACY_UNIT

        if history_count:
            return REVIEW_OPERATIONAL_UNIT

        return REVIEW_OPERATIONAL_UNIT

    def _history_count(
        self,
        model,
        product_unit: ProductUnit | None,
    ) -> int:
        if product_unit is None:
            return 0

        return int(
            self.session.query(
                func.count(model.id)
            )
            .filter(
                model.product_unit_id
                == str(product_unit.id)
            )
            .scalar()
            or 0
        )


__all__ = [
    "LINK_EXISTING_UOM",
    "NO_ACTION",
    "PRESERVE_HISTORICAL_UNIT",
    "REVIEW_LEGACY_UNIT",
    "REVIEW_OPERATIONAL_UNIT",
    "SPLIT_CURRENT_PRODUCTS",
    "TenantUOMProductPlan",
    "TenantUOMRemediationPlan",
    "TenantUOMRemediationPlanner",
    "TenantUOMRemediationResult",
]
