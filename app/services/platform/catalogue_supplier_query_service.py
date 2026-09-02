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

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import case, func

from app.errors import ValidationError
from app.models import (
    CatalogueSupplier,
    MasterItem,
    MasterItemSupplierMapping,
    SupplierItemPrice,
)


def _decimal(
    value: Decimal | None,
) -> str | None:
    if value is None:
        return None

    return str(value)


def _date(
    value,
) -> str | None:
    if value is None:
        return None

    return value.isoformat()


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

    def get_supplier(
        self,
        *,
        supplier_id: str,
    ) -> dict | None:
        """
        Retrieve one CatalogueSupplier with mapped Master Items and
        supplier-price evidence summary metrics.
        """

        if not supplier_id:
            raise ValidationError(
                "Catalogue supplier id is required."
            )

        supplier = (
            self.session.query(
                CatalogueSupplier
            )
            .filter(
                CatalogueSupplier.id
                == supplier_id
            )
            .first()
        )

        if supplier is None:
            return None

        mappings = (
            self.session.query(
                MasterItemSupplierMapping,
                MasterItem,
            )
            .join(
                MasterItem,
                MasterItem.id
                == MasterItemSupplierMapping.master_item_id,
            )
            .filter(
                MasterItemSupplierMapping.catalogue_supplier_id
                == supplier_id
            )
            .order_by(
                MasterItem.canonical_name.asc(),
                MasterItem.master_code.asc(),
                MasterItemSupplierMapping.supplier_item_name.asc(),
                MasterItemSupplierMapping.id.asc(),
            )
            .all()
        )

        mapping_ids = [
            mapping.id
            for mapping, _master_item in mappings
        ]

        prices_by_mapping: dict[
            str,
            list[SupplierItemPrice],
        ] = defaultdict(list)

        if mapping_ids:
            prices = (
                self.session.query(
                    SupplierItemPrice
                )
                .filter(
                    SupplierItemPrice.supplier_mapping_id.in_(
                        mapping_ids
                    )
                )
                .order_by(
                    SupplierItemPrice.effective_date
                    .desc()
                    .nullslast(),
                    SupplierItemPrice.id.asc(),
                )
                .all()
            )

            for price in prices:
                prices_by_mapping[
                    price.supplier_mapping_id
                ].append(price)

        serialized_mappings = []

        price_observation_count = 0
        comparable_observation_count = 0
        latest_effective_date = None

        for mapping, master_item in mappings:
            mapping_prices = (
                prices_by_mapping.get(
                    mapping.id,
                    [],
                )
            )

            comparable_prices = [
                price
                for price in mapping_prices
                if (
                    price.is_comparable_procurement
                    is True
                )
            ]

            dated_comparable_prices = [
                price
                for price in comparable_prices
                if price.effective_date
                is not None
            ]

            latest_comparable = (
                max(
                    dated_comparable_prices,
                    key=lambda price: (
                        price.effective_date,
                        price.id,
                    ),
                )
                if dated_comparable_prices
                else None
            )

            dated_prices = [
                price.effective_date
                for price in mapping_prices
                if price.effective_date
                is not None
            ]

            if dated_prices:
                mapping_latest_date = max(
                    dated_prices
                )

                if (
                    latest_effective_date
                    is None
                    or mapping_latest_date
                    > latest_effective_date
                ):
                    latest_effective_date = (
                        mapping_latest_date
                    )

            price_count = len(
                mapping_prices
            )

            comparable_count = len(
                comparable_prices
            )

            price_observation_count += (
                price_count
            )

            comparable_observation_count += (
                comparable_count
            )

            serialized_mappings.append(
                {
                    "id": mapping.id,
                    "supplier_item_code": (
                        mapping.supplier_item_code
                    ),
                    "supplier_item_name": (
                        mapping.supplier_item_name
                    ),
                    "source_description": (
                        mapping.source_description
                    ),
                    "is_active": (
                        mapping.is_active
                    ),
                    "master_item": {
                        "id": master_item.id,
                        "master_code": (
                            master_item.master_code
                        ),
                        "canonical_name": (
                            master_item.canonical_name
                        ),
                        "review_status": (
                            master_item.review_status
                        ),
                        "is_active": (
                            master_item.is_active
                        ),
                    },
                    "price_observation_count": (
                        price_count
                    ),
                    "comparable_observation_count": (
                        comparable_count
                    ),
                    "non_comparable_observation_count": (
                        price_count
                        - comparable_count
                    ),
                    "latest_comparable_price": (
                        self._serialize_price(
                            latest_comparable
                        )
                        if latest_comparable
                        else None
                    ),
                }
            )

        return {
            "id": supplier.id,
            "name": supplier.name,
            "country": supplier.country,
            "is_active": supplier.is_active,
            "mapping_count": len(
                serialized_mappings
            ),
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
                _date(
                    latest_effective_date
                )
            ),
            "procurement_comparable": (
                comparable_observation_count
                > 0
            ),
            "mappings": serialized_mappings,
        }


    @staticmethod
    def _serialize_price(
        price: SupplierItemPrice,
    ) -> dict:
        return {
            "id": price.id,
            "source_offer_key": (
                price.source_offer_key
            ),
            "price_type": (
                price.price_type
            ),
            "amount": _decimal(
                price.amount
            ),
            "currency": (
                price.currency
            ),
            "discount_percent": (
                _decimal(
                    price.discount_percent
                )
            ),
            "vat_source": (
                price.vat_source
            ),
            "effective_date": (
                _date(
                    price.effective_date
                )
            ),
            "source_document": (
                price.source_document
            ),
            "source_location": (
                price.source_location
            ),
            "is_comparable_procurement": (
                price.is_comparable_procurement
            ),
        }


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
