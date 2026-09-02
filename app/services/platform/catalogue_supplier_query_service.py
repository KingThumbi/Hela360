"""
Hela360 Office Catalogue Supplier Query Service
================================================

Read-only platform projection of CatalogueSupplier identities together with
supplier catalogue coverage and price-evidence summary metrics.

Architectural boundaries
------------------------
* CatalogueSupplier is platform-owned and separate from tenant Supplier.
* MasterItemSupplierMapping represents supplier catalogue listing identity.
* SupplierItemPrice represents commercial source evidence.
* This service does not query tenant procurement or inventory data.
* Derived metrics do not mutate or reclassify source evidence.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import case, func

from app.errors import ValidationError
from app.models import (
    CatalogueSupplier,
    MasterItemSupplierMapping,
    SupplierItemPrice,
)


@dataclass(frozen=True)
class CatalogueSupplierListFilters:
    page: int = 1
    per_page: int = 25
    search: str | None = None
    is_active: bool | None = None

    @classmethod
    def from_query(
        cls,
        args,
    ) -> "CatalogueSupplierListFilters":
        page = _positive_integer(
            args.get("page"),
            default=1,
            field="page",
        )

        per_page = _positive_integer(
            args.get("per_page"),
            default=25,
            field="per_page",
        )

        if per_page > 100:
            raise ValidationError(
                "per_page must not exceed 100."
            )

        search = _text(
            args.get("search")
            or args.get("q")
        )

        is_active = _optional_boolean(
            args.get("is_active"),
            field="is_active",
        )

        return cls(
            page=page,
            per_page=per_page,
            search=search,
            is_active=is_active,
        )


class PlatformCatalogueSupplierQueryService:
    """
    Read CatalogueSupplier identities and platform evidence metrics.
    """

    def __init__(
        self,
        session,
    ) -> None:
        self.session = session

    def list_suppliers(
        self,
        *,
        filters: CatalogueSupplierListFilters,
    ) -> tuple[list[dict], dict]:
        mapping_counts = (
            self.session.query(
                MasterItemSupplierMapping.catalogue_supplier_id.label(
                    "supplier_id"
                ),
                func.count(
                    MasterItemSupplierMapping.id
                ).label(
                    "mapping_count"
                ),
            )
            .group_by(
                MasterItemSupplierMapping.catalogue_supplier_id
            )
            .subquery()
        )

        price_counts = (
            self.session.query(
                MasterItemSupplierMapping.catalogue_supplier_id.label(
                    "supplier_id"
                ),
                func.count(
                    SupplierItemPrice.id
                ).label(
                    "price_observation_count"
                ),
                func.sum(
                    case(
                        (
                            SupplierItemPrice.is_comparable_procurement
                            .is_(True),
                            1,
                        ),
                        else_=0,
                    )
                ).label(
                    "comparable_observation_count"
                ),
                func.max(
                    SupplierItemPrice.effective_date
                ).label(
                    "latest_effective_date"
                ),
            )
            .join(
                SupplierItemPrice,
                SupplierItemPrice.supplier_mapping_id
                == MasterItemSupplierMapping.id,
            )
            .group_by(
                MasterItemSupplierMapping.catalogue_supplier_id
            )
            .subquery()
        )

        query = (
            self.session.query(
                CatalogueSupplier,
                func.coalesce(
                    mapping_counts.c.mapping_count,
                    0,
                ).label(
                    "mapping_count"
                ),
                func.coalesce(
                    price_counts.c.price_observation_count,
                    0,
                ).label(
                    "price_observation_count"
                ),
                func.coalesce(
                    price_counts.c.comparable_observation_count,
                    0,
                ).label(
                    "comparable_observation_count"
                ),
                price_counts.c.latest_effective_date,
            )
            .outerjoin(
                mapping_counts,
                mapping_counts.c.supplier_id
                == CatalogueSupplier.id,
            )
            .outerjoin(
                price_counts,
                price_counts.c.supplier_id
                == CatalogueSupplier.id,
            )
        )

        if filters.search:
            pattern = (
                f"%{filters.search}%"
            )

            query = query.filter(
                CatalogueSupplier.name.ilike(
                    pattern
                )
            )

        if filters.is_active is not None:
            query = query.filter(
                CatalogueSupplier.is_active
                == filters.is_active
            )

        total = query.count()

        rows = (
            query.order_by(
                CatalogueSupplier.name.asc()
            )
            .offset(
                (filters.page - 1)
                * filters.per_page
            )
            .limit(
                filters.per_page
            )
            .all()
        )

        items = [
            self._serialize_supplier(
                supplier=supplier,
                mapping_count=mapping_count,
                price_observation_count=price_count,
                comparable_observation_count=(
                    comparable_count
                ),
                latest_effective_date=latest_date,
            )
            for (
                supplier,
                mapping_count,
                price_count,
                comparable_count,
                latest_date,
            ) in rows
        ]

        pages = (
            (total + filters.per_page - 1)
            // filters.per_page
        )

        pagination = {
            "page": filters.page,
            "per_page": filters.per_page,
            "total": total,
            "pages": pages,
            "has_prev": filters.page > 1,
            "has_next": (
                filters.page < pages
            ),
        }

        return items, pagination

    @staticmethod
    def _serialize_supplier(
        *,
        supplier: CatalogueSupplier,
        mapping_count: int,
        price_observation_count: int,
        comparable_observation_count: int,
        latest_effective_date,
    ) -> dict:
        mapping_count = int(
            mapping_count or 0
        )

        price_observation_count = int(
            price_observation_count or 0
        )

        comparable_observation_count = int(
            comparable_observation_count or 0
        )

        return {
            "id": supplier.id,
            "name": supplier.name,
            "country": supplier.country,
            "is_active": supplier.is_active,
            "mapping_count": mapping_count,
            "price_observation_count": (
                price_observation_count
            ),
            "comparable_observation_count": (
                comparable_observation_count
            ),
            "non_comparable_observation_count": (
                price_observation_count
                - comparable_observation_count
            ),
            "latest_effective_date": (
                latest_effective_date.isoformat()
                if latest_effective_date
                else None
            ),
            "procurement_comparable": (
                comparable_observation_count > 0
            ),
        }


def _text(
    value,
) -> str | None:
    if value is None:
        return None

    normalized = str(value).strip()

    return normalized or None


def _positive_integer(
    value,
    *,
    default: int,
    field: str,
) -> int:
    if value in (
        None,
        "",
    ):
        return default

    try:
        parsed = int(value)
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise ValidationError(
            f"{field} must be a positive integer."
        ) from exc

    if parsed < 1:
        raise ValidationError(
            f"{field} must be a positive integer."
        )

    return parsed


def _optional_boolean(
    value,
    *,
    field: str,
) -> bool | None:
    if value in (
        None,
        "",
    ):
        return None

    normalized = str(
        value
    ).strip().lower()

    if normalized == "true":
        return True

    if normalized == "false":
        return False

    raise ValidationError(
        f"{field} must be true or false."
    )


__all__ = [
    "CatalogueSupplierListFilters",
    "PlatformCatalogueSupplierQueryService",
]
