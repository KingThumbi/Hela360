"""
Hela360 Canonical Unit-of-Measure Policy
========================================

Defines the platform-owned canonical UOM vocabulary.

These definitions describe semantic unit identities only.

Product-specific conversion factors belong to ProductUnit and must never be
defined here.
"""

from __future__ import annotations

from dataclasses import dataclass


UNIT_FAMILY_DISCRETE = "discrete"
UNIT_FAMILY_CONTAINER = "container"
UNIT_FAMILY_PACKAGING = "packaging"

CANONICAL_UOM_FAMILIES = frozenset(
    {
        UNIT_FAMILY_DISCRETE,
        UNIT_FAMILY_CONTAINER,
        UNIT_FAMILY_PACKAGING,
    }
)


@dataclass(frozen=True, slots=True)
class CanonicalUOMDefinition:
    """One platform-governed canonical unit-of-measure definition."""

    code: str
    name: str
    unit_family: str
    description: str
    is_packaging_unit: bool
    sort_order: int


CANONICAL_UOM_DEFINITIONS: tuple[CanonicalUOMDefinition, ...] = (
    # ------------------------------------------------------------------
    # Discrete operational units
    # ------------------------------------------------------------------
    CanonicalUOMDefinition(
        code="EA",
        name="Each",
        unit_family=UNIT_FAMILY_DISCRETE,
        description=(
            "Generic single countable item where no more specific "
            "operational unit applies."
        ),
        is_packaging_unit=False,
        sort_order=10,
    ),
    CanonicalUOMDefinition(
        code="PC",
        name="Piece",
        unit_family=UNIT_FAMILY_DISCRETE,
        description="Single countable piece.",
        is_packaging_unit=False,
        sort_order=20,
    ),
    CanonicalUOMDefinition(
        code="TAB",
        name="Tablet",
        unit_family=UNIT_FAMILY_DISCRETE,
        description="Single pharmaceutical tablet.",
        is_packaging_unit=False,
        sort_order=30,
    ),
    CanonicalUOMDefinition(
        code="CAP",
        name="Capsule",
        unit_family=UNIT_FAMILY_DISCRETE,
        description="Single pharmaceutical capsule.",
        is_packaging_unit=False,
        sort_order=40,
    ),
    CanonicalUOMDefinition(
        code="SACH",
        name="Sachet",
        unit_family=UNIT_FAMILY_DISCRETE,
        description="Single sachet.",
        is_packaging_unit=False,
        sort_order=50,
    ),
    CanonicalUOMDefinition(
        code="SUPP",
        name="Suppository",
        unit_family=UNIT_FAMILY_DISCRETE,
        description="Single suppository.",
        is_packaging_unit=False,
        sort_order=60,
    ),
    CanonicalUOMDefinition(
        code="PESS",
        name="Pessary",
        unit_family=UNIT_FAMILY_DISCRETE,
        description="Single pessary.",
        is_packaging_unit=False,
        sort_order=70,
    ),
    CanonicalUOMDefinition(
        code="PAIR",
        name="Pair",
        unit_family=UNIT_FAMILY_DISCRETE,
        description="One pair treated as an operational stock unit.",
        is_packaging_unit=False,
        sort_order=80,
    ),
    CanonicalUOMDefinition(
        code="SET",
        name="Set",
        unit_family=UNIT_FAMILY_DISCRETE,
        description="One defined set treated as an operational stock unit.",
        is_packaging_unit=False,
        sort_order=90,
    ),

    # ------------------------------------------------------------------
    # Containers / immediate presentations
    # ------------------------------------------------------------------
    CanonicalUOMDefinition(
        code="BOT",
        name="Bottle",
        unit_family=UNIT_FAMILY_CONTAINER,
        description="Single bottle.",
        is_packaging_unit=False,
        sort_order=110,
    ),
    CanonicalUOMDefinition(
        code="TUBE",
        name="Tube",
        unit_family=UNIT_FAMILY_CONTAINER,
        description="Single tube.",
        is_packaging_unit=False,
        sort_order=120,
    ),
    CanonicalUOMDefinition(
        code="VIAL",
        name="Vial",
        unit_family=UNIT_FAMILY_CONTAINER,
        description="Single vial.",
        is_packaging_unit=False,
        sort_order=130,
    ),
    CanonicalUOMDefinition(
        code="AMP",
        name="Ampoule",
        unit_family=UNIT_FAMILY_CONTAINER,
        description="Single ampoule.",
        is_packaging_unit=False,
        sort_order=140,
    ),
    CanonicalUOMDefinition(
        code="BAG",
        name="Bag",
        unit_family=UNIT_FAMILY_CONTAINER,
        description="Single bag presentation.",
        is_packaging_unit=False,
        sort_order=150,
    ),
    CanonicalUOMDefinition(
        code="INH",
        name="Inhaler",
        unit_family=UNIT_FAMILY_CONTAINER,
        description="Single inhaler device.",
        is_packaging_unit=False,
        sort_order=160,
    ),
    CanonicalUOMDefinition(
        code="ROLL",
        name="Roll",
        unit_family=UNIT_FAMILY_CONTAINER,
        description="Single roll.",
        is_packaging_unit=False,
        sort_order=170,
    ),

    # ------------------------------------------------------------------
    # Packaging units
    # ------------------------------------------------------------------
    CanonicalUOMDefinition(
        code="STRIP",
        name="Strip",
        unit_family=UNIT_FAMILY_PACKAGING,
        description=(
            "Product-specific strip containing one or more base units."
        ),
        is_packaging_unit=True,
        sort_order=210,
    ),
    CanonicalUOMDefinition(
        code="BLISTER",
        name="Blister",
        unit_family=UNIT_FAMILY_PACKAGING,
        description=(
            "Product-specific blister containing one or more base units."
        ),
        is_packaging_unit=True,
        sort_order=220,
    ),
    CanonicalUOMDefinition(
        code="PACK",
        name="Pack",
        unit_family=UNIT_FAMILY_PACKAGING,
        description=(
            "Product-specific pack containing one or more base units."
        ),
        is_packaging_unit=True,
        sort_order=230,
    ),
    CanonicalUOMDefinition(
        code="BOX",
        name="Box",
        unit_family=UNIT_FAMILY_PACKAGING,
        description=(
            "Product-specific box containing one or more base units."
        ),
        is_packaging_unit=True,
        sort_order=240,
    ),
    CanonicalUOMDefinition(
        code="OUTER",
        name="Outer",
        unit_family=UNIT_FAMILY_PACKAGING,
        description=(
            "Intermediate outer packaging containing product-specific "
            "quantities."
        ),
        is_packaging_unit=True,
        sort_order=250,
    ),
    CanonicalUOMDefinition(
        code="CARTON",
        name="Carton",
        unit_family=UNIT_FAMILY_PACKAGING,
        description=(
            "Carton containing a product-specific quantity of base or "
            "intermediate units."
        ),
        is_packaging_unit=True,
        sort_order=260,
    ),
)


ALL_CANONICAL_UOM_CODES = frozenset(
    definition.code
    for definition in CANONICAL_UOM_DEFINITIONS
)


def get_canonical_uom(
    code: str,
) -> CanonicalUOMDefinition | None:
    """Return one canonical UOM definition by code."""

    normalized = code.strip().upper()

    return next(
        (
            definition
            for definition in CANONICAL_UOM_DEFINITIONS
            if definition.code == normalized
        ),
        None,
    )


__all__ = [
    "ALL_CANONICAL_UOM_CODES",
    "CANONICAL_UOM_DEFINITIONS",
    "CANONICAL_UOM_FAMILIES",
    "CanonicalUOMDefinition",
    "UNIT_FAMILY_CONTAINER",
    "UNIT_FAMILY_DISCRETE",
    "UNIT_FAMILY_PACKAGING",
    "get_canonical_uom",
]
