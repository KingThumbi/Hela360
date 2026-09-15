"""
Hela360 Tenant UOM Audit Service
================================

Read-only analysis of tenant UnitOfMeasure records against the
platform-owned canonical UOM catalogue.

This service does NOT:
- modify UnitOfMeasure rows;
- rewrite Product.unit_id;
- modify ProductUnit rows;
- change conversion factors;
- rewrite historical receipt or sale evidence;
- automatically map dosage forms to operational units.

Its purpose is to identify which tenant UOM rows are safe to link to a
canonical UOM and which require human review or product-level repair.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

from sqlalchemy import func

from app.models import (
    CanonicalUnitOfMeasure,
    GoodsReceiptItem,
    MasterItem,
    Product,
    ProductUnit,
    SaleItem,
    UnitOfMeasure,
)


CANONICALLY_LINKED = "CANONICALLY_LINKED"
SAFE_TO_LINK = "SAFE_TO_LINK"
MIXED_PRODUCT_SEMANTICS = "MIXED_PRODUCT_SEMANTICS"
DOSAGE_FORM_AS_UOM = "DOSAGE_FORM_AS_UOM"
LEGACY_PRODUCT_SPECIFIC = "LEGACY_PRODUCT_SPECIFIC"
CUSTOM_UNMAPPED = "CUSTOM_UNMAPPED"
HISTORICAL_ONLY = "HISTORICAL_ONLY"


STRICT_TENANT_UOM_ALIASES = {
    ("EA", "EACH"): "EA",
    ("PC", "PIECE"): "PC",
    ("TAB", "TABLET"): "TAB",
    ("TAB", "TAB"): "TAB",
    ("1", "TAB"): "TAB",
    ("CAP", "CAPSULE"): "CAP",
    ("CAPS", "CAPSULE"): "CAP",
    ("SACH", "SACHET"): "SACH",
    ("SUPP", "SUPPOSITORY"): "SUPP",
    ("PESS", "PESSARY"): "PESS",
    ("PAIR", "PAIR"): "PAIR",
    ("SET", "SET"): "SET",
    ("BOT", "BOTTLE"): "BOT",
    ("BOTTLE", "BOTTLE"): "BOT",
    ("TUBE", "TUBE"): "TUBE",
    ("VIAL", "VIAL"): "VIAL",
    ("AMP", "AMPOULE"): "AMP",
    ("AMPOULE", "AMPOULE"): "AMP",
    ("BAG", "BAG"): "BAG",
    ("INH", "INHALER"): "INH",
    ("ROLL", "ROLL"): "ROLL",
    ("STRIP", "STRIP"): "STRIP",
    ("BLISTER", "BLISTER"): "BLISTER",
    ("PACK", "PACK"): "PACK",
    ("BOX", "BOX"): "BOX",
    ("OUTER", "OUTER"): "OUTER",
    ("CARTON", "CARTON"): "CARTON",
}


DOSAGE_FORM_TERMS = frozenset(
    {
        "SYRUP",
        "SUSPENSION",
        "CREAM",
        "OINTMENT",
        "DROPS",
        "POWDER",
        "SOLUTION",
        "LOTION",
        "GEL",
        "INJECTION",
    }
)


DOSAGE_FORM_CANONICAL_CODES = {
    "TABLET": "TAB",
    "CAPSULE": "CAP",
    "SUPPOSITORY": "SUPP",
    "PESSARY": "PESS",
    "INHALER": "INH",
    "SACHET": "SACH",
}


# These are legitimate dosage/presentation concepts, but Hela360 does
# not currently have a canonical operational UOM for them. They are
# still useful as evidence that a discrete TAB/CAP/etc assignment is
# semantically inconsistent.
OTHER_DISTINCT_DOSAGE_FORMS = frozenset(
    {
        "LOZENGE",
    }
)


DISCRETE_PRESENTATION_CODES = frozenset(
    {
        "TAB",
        "CAP",
        "SACH",
        "SUPP",
        "PESS",
    }
)


NAME_EVIDENCE_PATTERNS = (
    (
        "TAB",
        re.compile(
            r"\b(?:TAB|TABS|TABLET|TABLETS)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "CAP",
        re.compile(
            r"\b(?:CAP|CAPS|CAPSULE|CAPSULES)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "SUPP",
        re.compile(
            r"\b(?:SUPP|SUPPOSITORY|SUPPOSITORIES)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "PESS",
        re.compile(
            r"\b(?:PESSARY|PESSARIES)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "SACH",
        re.compile(
            r"\b(?:SACHET|SACHETS)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "INH",
        re.compile(
            r"\b(?:INHALER|INHALERS)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "VIAL",
        re.compile(
            r"\b(?:VIAL|VIALS)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "AMP",
        re.compile(
            r"\b(?:AMPOULE|AMPOULES|AMPUL|AMPULS)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "BOT",
        re.compile(
            r"\b(?:BOTTLE|BOTTLES)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "TUBE",
        re.compile(
            r"\b(?:TUBE|TUBES)\b",
            re.IGNORECASE,
        ),
    ),
)


@dataclass(frozen=True, slots=True)
class TenantUOMAuditItem:
    uom_id: str
    tenant_id: str
    code: str
    name: str
    canonical_uom_id: str | None
    canonical_code: str | None
    suggested_canonical_code: str | None
    classification: str
    confidence: str
    reasons: tuple[str, ...]
    product_count: int
    active_product_count: int
    product_unit_count: int
    goods_receipt_reference_count: int
    sale_reference_count: int
    historical_reference_count: int
    requires_product_split: bool
    safe_to_link: bool


@dataclass(frozen=True, slots=True)
class TenantUOMAuditResult:
    items: tuple[TenantUOMAuditItem, ...]

    @property
    def total_count(self) -> int:
        return len(self.items)

    def count(self, classification: str) -> int:
        return sum(
            1
            for item in self.items
            if item.classification == classification
        )


@dataclass(frozen=True, slots=True)
class _ProductSemanticEvidence:
    product_id: str
    sku: str
    expected_codes: frozenset[str]
    incompatible_dosage_forms: frozenset[str]


class TenantUOMAuditService:
    """
    Audit tenant UOM semantics without mutating operational data.

    Transaction ownership remains with the caller.
    """

    def __init__(self, session) -> None:
        self.session = session

    def audit_tenant(
        self,
        *,
        tenant_id: str,
    ) -> TenantUOMAuditResult:
        units = (
            self.session.query(UnitOfMeasure)
            .filter(
                UnitOfMeasure.tenant_id == tenant_id,
            )
            .order_by(
                UnitOfMeasure.code,
                UnitOfMeasure.name,
                UnitOfMeasure.id,
            )
            .all()
        )

        return TenantUOMAuditResult(
            items=tuple(
                self._audit_unit(unit)
                for unit in units
            )
        )

    def audit_unit(
        self,
        *,
        tenant_id: str,
        uom_id: str,
    ) -> TenantUOMAuditItem:
        unit = (
            self.session.query(UnitOfMeasure)
            .filter(
                UnitOfMeasure.id == uom_id,
                UnitOfMeasure.tenant_id == tenant_id,
            )
            .first()
        )

        if unit is None:
            raise ValueError(
                "Tenant UnitOfMeasure was not found."
            )

        return self._audit_unit(unit)

    def _audit_unit(
        self,
        unit: UnitOfMeasure,
    ) -> TenantUOMAuditItem:
        tenant_id = str(unit.tenant_id)
        uom_id = str(unit.id)

        product_units = (
            self.session.query(ProductUnit)
            .filter(
                ProductUnit.tenant_id == tenant_id,
                ProductUnit.unit_id == uom_id,
            )
            .all()
        )

        product_unit_ids = tuple(
            str(product_unit.id)
            for product_unit in product_units
        )

        base_product_ids = {
            str(product_unit.product_id)
            for product_unit in product_units
            if (
                product_unit.is_base
                and product_unit.is_active
            )
        }

        direct_products = (
            self.session.query(Product)
            .filter(
                Product.tenant_id == tenant_id,
                Product.unit_id == uom_id,
            )
            .all()
        )

        product_ids = {
            str(product.id)
            for product in direct_products
        }
        product_ids.update(base_product_ids)

        if product_ids:
            products = (
                self.session.query(Product)
                .filter(
                    Product.tenant_id == tenant_id,
                    Product.id.in_(product_ids),
                )
                .all()
            )
        else:
            products = []

        active_product_count = sum(
            1
            for product in products
            if product.is_active
        )

        gr_count = self._history_count(
            GoodsReceiptItem,
            product_unit_ids,
        )

        sale_count = self._history_count(
            SaleItem,
            product_unit_ids,
        )

        history_count = gr_count + sale_count

        canonical = (
            self.session.get(
                CanonicalUnitOfMeasure,
                unit.canonical_uom_id,
            )
            if unit.canonical_uom_id
            else None
        )

        alias_code = self._strict_alias_code(unit)

        candidate_code = (
            canonical.code
            if canonical is not None
            else alias_code
        )

        evidence = tuple(
            self._product_semantic_evidence(product)
            for product in products
        )

        contradictions = self._contradictions(
            candidate_code=candidate_code,
            evidence=evidence,
        )

        classification, confidence, reasons = (
            self._classify(
                unit=unit,
                canonical=canonical,
                candidate_code=candidate_code,
                product_count=len(products),
                history_count=history_count,
                contradictions=contradictions,
            )
        )

        return TenantUOMAuditItem(
            uom_id=uom_id,
            tenant_id=tenant_id,
            code=unit.code,
            name=unit.name,
            canonical_uom_id=(
                str(canonical.id)
                if canonical is not None
                else None
            ),
            canonical_code=(
                canonical.code
                if canonical is not None
                else None
            ),
            suggested_canonical_code=candidate_code,
            classification=classification,
            confidence=confidence,
            reasons=tuple(reasons),
            product_count=len(products),
            active_product_count=active_product_count,
            product_unit_count=len(product_units),
            goods_receipt_reference_count=gr_count,
            sale_reference_count=sale_count,
            historical_reference_count=history_count,
            requires_product_split=(
                classification
                == MIXED_PRODUCT_SEMANTICS
            ),
            safe_to_link=(
                classification == SAFE_TO_LINK
            ),
        )

    def _history_count(
        self,
        model,
        product_unit_ids: tuple[str, ...],
    ) -> int:
        if not product_unit_ids:
            return 0

        return int(
            self.session.query(
                func.count(model.id)
            )
            .filter(
                model.product_unit_id.in_(
                    product_unit_ids
                )
            )
            .scalar()
            or 0
        )

    def _strict_alias_code(
        self,
        unit: UnitOfMeasure,
    ) -> str | None:
        code = self._normalize(unit.code)
        name = self._normalize(unit.name)

        return STRICT_TENANT_UOM_ALIASES.get(
            (code, name)
        )

    def _product_semantic_evidence(
        self,
        product: Product,
    ) -> _ProductSemanticEvidence:
        expected_codes: set[str] = set()
        incompatible_forms: set[str] = set()

        master_item = (
            self.session.get(
                MasterItem,
                product.master_item_id,
            )
            if product.master_item_id
            else None
        )

        dosage_form = self._normalize(
            getattr(
                master_item,
                "dosage_form",
                None,
            )
        )

        if dosage_form:
            canonical_code = (
                DOSAGE_FORM_CANONICAL_CODES.get(
                    dosage_form
                )
            )

            if canonical_code:
                expected_codes.add(
                    canonical_code
                )

            elif (
                dosage_form in DOSAGE_FORM_TERMS
                or dosage_form
                in OTHER_DISTINCT_DOSAGE_FORMS
            ):
                incompatible_forms.add(
                    dosage_form
                )

        product_name = product.name or ""

        for code, pattern in NAME_EVIDENCE_PATTERNS:
            if pattern.search(product_name):
                expected_codes.add(code)

        return _ProductSemanticEvidence(
            product_id=str(product.id),
            sku=product.internal_sku,
            expected_codes=frozenset(
                expected_codes
            ),
            incompatible_dosage_forms=frozenset(
                incompatible_forms
            ),
        )

    def _contradictions(
        self,
        *,
        candidate_code: str | None,
        evidence: tuple[
            _ProductSemanticEvidence,
            ...
        ],
    ) -> tuple[str, ...]:
        if candidate_code is None:
            return ()

        contradictions: list[str] = []

        for item in evidence:
            other_codes = sorted(
                code
                for code in item.expected_codes
                if code != candidate_code
            )

            if other_codes:
                contradictions.append(
                    f"{item.sku}: expected "
                    + "/".join(other_codes)
                    + f", not {candidate_code}"
                )

            if (
                candidate_code
                in DISCRETE_PRESENTATION_CODES
                and item.incompatible_dosage_forms
            ):
                contradictions.append(
                    f"{item.sku}: dosage form "
                    + "/".join(
                        sorted(
                            item.incompatible_dosage_forms
                        )
                    )
                    + " conflicts with "
                    + candidate_code
                )

        return tuple(contradictions)

    def _classify(
        self,
        *,
        unit: UnitOfMeasure,
        canonical: CanonicalUnitOfMeasure | None,
        candidate_code: str | None,
        product_count: int,
        history_count: int,
        contradictions: tuple[str, ...],
    ) -> tuple[str, str, list[str]]:
        code = self._normalize(unit.code)
        name = self._normalize(unit.name)

        if (
            product_count == 0
            and history_count > 0
        ):
            return (
                HISTORICAL_ONLY,
                "high",
                [
                    "No current base product uses this UOM.",
                    (
                        "Operational history exists and must "
                        "remain unchanged."
                    ),
                ],
            )

        if self._looks_product_specific(code):
            return (
                LEGACY_PRODUCT_SPECIFIC,
                "high",
                [
                    (
                        "The tenant UOM code appears to be "
                        "product-specific legacy vocabulary."
                    ),
                    (
                        "It must not be globally normalized "
                        "without product-level review."
                    ),
                ],
            )

        if (
            code in DOSAGE_FORM_TERMS
            or name in DOSAGE_FORM_TERMS
        ):
            return (
                DOSAGE_FORM_AS_UOM,
                "high",
                [
                    (
                        "The UOM code/name represents a dosage "
                        "form rather than an operational unit."
                    ),
                    (
                        "Dosage form must remain separate from "
                        "inventory unit identity."
                    ),
                ],
            )

        if contradictions:
            return (
                MIXED_PRODUCT_SEMANTICS,
                "high",
                [
                    (
                        "Products using this tenant UOM contain "
                        "conflicting presentation evidence."
                    ),
                    *contradictions,
                ],
            )

        if canonical is not None:
            return (
                CANONICALLY_LINKED,
                "high",
                [
                    (
                        "The tenant UOM is already linked to "
                        f"canonical {canonical.code}."
                    ),
                    (
                        "No contradictory product semantics "
                        "were detected."
                    ),
                ],
            )

        if candidate_code is not None:
            return (
                SAFE_TO_LINK,
                "high",
                [
                    (
                        "Code/name matches a strict canonical "
                        f"alias for {candidate_code}."
                    ),
                    (
                        "No contradictory product semantics "
                        "were detected."
                    ),
                ],
            )

        return (
            CUSTOM_UNMAPPED,
            "low",
            [
                (
                    "No strict canonical mapping can be proven "
                    "from the current evidence."
                ),
                (
                    "Human review is required before linking "
                    "or remediating this UOM."
                ),
            ],
        )

    @staticmethod
    def _normalize(
        value: str | None,
    ) -> str:
        return (value or "").strip().upper()

    @staticmethod
    def _looks_product_specific(
        code: str,
    ) -> bool:
        return "-" in code


__all__ = [
    "CANONICALLY_LINKED",
    "CUSTOM_UNMAPPED",
    "DOSAGE_FORM_AS_UOM",
    "HISTORICAL_ONLY",
    "LEGACY_PRODUCT_SPECIFIC",
    "MIXED_PRODUCT_SEMANTICS",
    "SAFE_TO_LINK",
    "TenantUOMAuditItem",
    "TenantUOMAuditResult",
    "TenantUOMAuditService",
]
