"""
Hela360 Canonical UOM Catalogue Service
=======================================

Persists and synchronizes Hela360's platform-owned canonical UOM catalogue.

Architectural rules
-------------------
* Canonical UOMs are platform-owned and have no tenant_id.
* Canonical code is the semantic identity used for synchronization.
* Governed metadata may be repaired by synchronization.
* Unknown persisted UOMs are preserved and never deleted automatically.
* Tenant UnitOfMeasure records are not modified here.
* ProductUnit conversion factors are not modified here.
* Transaction ownership remains with the caller.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from app.models import CanonicalUnitOfMeasure
from app.services.platform.canonical_uom_policy import (
    CANONICAL_UOM_DEFINITIONS,
    CanonicalUOMDefinition,
)


@dataclass(frozen=True, slots=True)
class CanonicalUOMSyncItem:
    """Synchronization result for one canonical UOM."""

    code: str
    created: bool
    metadata_updated: bool

    @property
    def changed(self) -> bool:
        return self.created or self.metadata_updated


@dataclass(frozen=True, slots=True)
class CanonicalUOMCatalogueResult:
    """Summary of one canonical UOM catalogue synchronization."""

    units: tuple[CanonicalUOMSyncItem, ...]

    @property
    def changed(self) -> bool:
        return any(
            item.changed
            for item in self.units
        )

    @property
    def created_count(self) -> int:
        return sum(
            1
            for item in self.units
            if item.created
        )

    @property
    def updated_count(self) -> int:
        return sum(
            1
            for item in self.units
            if (
                not item.created
                and item.metadata_updated
            )
        )

    @property
    def unchanged_count(self) -> int:
        return sum(
            1
            for item in self.units
            if not item.changed
        )

    @property
    def processed_count(self) -> int:
        return len(self.units)


class CanonicalUOMCatalogueService:
    """
    Synchronize the platform-owned canonical UOM catalogue.

    Transaction ownership remains with the caller.
    """

    def __init__(
        self,
        session,
    ) -> None:
        self.session = session

    def synchronize(
        self,
    ) -> CanonicalUOMCatalogueResult:
        """Synchronize every governed canonical UOM definition."""

        results: list[CanonicalUOMSyncItem] = []

        for definition in CANONICAL_UOM_DEFINITIONS:
            results.append(
                self._synchronize_unit(
                    definition
                )
            )

        return CanonicalUOMCatalogueResult(
            units=tuple(results),
        )

    def canonical_units(
        self,
    ) -> tuple[CanonicalUnitOfMeasure, ...]:
        """
        Return all persisted governed canonical UOMs.

        Raises RuntimeError when the persisted catalogue is incomplete.
        """

        codes = {
            definition.code
            for definition in CANONICAL_UOM_DEFINITIONS
        }

        units = tuple(
            self.session.scalars(
                select(CanonicalUnitOfMeasure)
                .where(
                    CanonicalUnitOfMeasure.code.in_(
                        codes
                    )
                )
                .order_by(
                    CanonicalUnitOfMeasure.sort_order,
                    CanonicalUnitOfMeasure.code,
                )
            ).all()
        )

        persisted_codes = {
            unit.code
            for unit in units
        }

        missing_codes = sorted(
            codes - persisted_codes
        )

        if missing_codes:
            raise RuntimeError(
                "Canonical UOM catalogue is incomplete: "
                + ", ".join(missing_codes)
            )

        return units

    def _synchronize_unit(
        self,
        definition: CanonicalUOMDefinition,
    ) -> CanonicalUOMSyncItem:
        """Synchronize one platform-owned canonical UOM."""

        unit = self.session.scalar(
            select(CanonicalUnitOfMeasure)
            .where(
                CanonicalUnitOfMeasure.code
                == definition.code
            )
        )

        created = False
        metadata_updated = False

        if unit is None:
            unit = CanonicalUnitOfMeasure(
                code=definition.code,
                name=definition.name,
                unit_family=definition.unit_family,
                description=definition.description,
                is_packaging_unit=(
                    definition.is_packaging_unit
                ),
                is_active=True,
                sort_order=definition.sort_order,
            )

            self.session.add(unit)
            self.session.flush()

            created = True

        else:
            governed_values = {
                "name": definition.name,
                "unit_family": definition.unit_family,
                "description": definition.description,
                "is_packaging_unit": (
                    definition.is_packaging_unit
                ),
                "is_active": True,
                "sort_order": definition.sort_order,
            }

            for field, expected in governed_values.items():
                if getattr(unit, field) != expected:
                    setattr(
                        unit,
                        field,
                        expected,
                    )
                    metadata_updated = True

            if metadata_updated:
                self.session.flush()

        return CanonicalUOMSyncItem(
            code=definition.code,
            created=created,
            metadata_updated=metadata_updated,
        )


__all__ = [
    "CanonicalUOMCatalogueResult",
    "CanonicalUOMCatalogueService",
    "CanonicalUOMSyncItem",
]
