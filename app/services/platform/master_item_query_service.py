"""
Hela360 Office Master Item Query Service
========================================

Read-only platform-governance projection over the Hela360 Master Catalogue.

Architectural boundaries
------------------------
* MasterItem is platform-owned and has no tenant_id.
* This service does not join tenant Product records.
* This service exposes catalogue governance state such as review_status and
  is_active rather than restricting reads to approved active items.
* This service performs no catalogue mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import or_

from app.errors import ValidationError
from app.models import MasterItem


@dataclass(frozen=True, slots=True)
class PlatformMasterItemListFilters:
    """Supported Hela360 Office Master Item list filters."""

    page: int = 1
    per_page: int = 25
    search: str | None = None
    review_status: str | None = None
    is_active: bool | None = None
    item_class: str | None = None
    category: str | None = None
    dosage_form: str | None = None

    @classmethod
    def from_query(
        cls,
        args,
    ) -> "PlatformMasterItemListFilters":
        page = _positive_int(
            args.get("page"),
            "page",
            1,
        )

        per_page = _positive_int(
            args.get("per_page"),
            "per_page",
            25,
        )

        if per_page > 100:
            raise ValidationError(
                "per_page must not exceed 100."
            )

        return cls(
            page=page,
            per_page=per_page,
            search=_optional_text(
                args.get("search")
                or args.get("q")
            ),
            review_status=_optional_text(
                args.get("review_status")
            ),
            is_active=_optional_bool(
                args.get("is_active"),
                "is_active",
            ),
            item_class=_optional_text(
                args.get("item_class")
            ),
            category=_optional_text(
                args.get("category")
            ),
            dosage_form=_optional_text(
                args.get("dosage_form")
            ),
        )


def _positive_int(
    value,
    field_name: str,
    default: int,
) -> int:
    if value in (None, ""):
        return default

    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(
            f"{field_name} must be a positive integer."
        ) from exc

    if parsed < 1:
        raise ValidationError(
            f"{field_name} must be a positive integer."
        )

    return parsed


def _optional_text(
    value,
) -> str | None:
    if value in (None, ""):
        return None

    normalized = str(value).strip()

    return normalized or None


def _optional_bool(
    value,
    field_name: str,
) -> bool | None:
    if value in (None, ""):
        return None

    normalized = str(value).strip().lower()

    if normalized in {
        "true",
        "1",
    }:
        return True

    if normalized in {
        "false",
        "0",
    }:
        return False

    raise ValidationError(
        f"{field_name} must be true or false."
    )


def _decimal(
    value: Decimal | None,
) -> str | None:
    if value is None:
        return None

    return str(value)


def _pagination(
    page: int,
    per_page: int,
    total: int,
) -> dict:
    pages = (
        (total + per_page - 1) // per_page
        if per_page
        else 1
    )

    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages,
        "has_prev": page > 1,
        "has_next": page < pages,
    }


class PlatformMasterItemQueryService:
    """
    Build read-only Hela360 Office projections of platform MasterItems.
    """

    def __init__(
        self,
        session,
    ) -> None:
        self.session = session

    def list_items(
        self,
        *,
        filters: PlatformMasterItemListFilters,
    ) -> tuple[list[dict], dict]:
        query = self.session.query(
            MasterItem
        )

        if filters.search:
            like = f"%{filters.search}%"

            query = query.filter(
                or_(
                    MasterItem.master_code.ilike(like),
                    MasterItem.canonical_name.ilike(like),
                    MasterItem.brand_name.ilike(like),
                    MasterItem.generic_name.ilike(like),
                    MasterItem.strength.ilike(like),
                    MasterItem.dosage_form.ilike(like),
                    MasterItem.category_name.ilike(like),
                    MasterItem.subcategory_name.ilike(like),
                    MasterItem.manufacturer.ilike(like),
                )
            )

        if filters.review_status:
            query = query.filter(
                MasterItem.review_status
                == filters.review_status
            )

        if filters.is_active is not None:
            query = query.filter(
                MasterItem.is_active.is_(
                    filters.is_active
                )
            )

        if filters.item_class:
            query = query.filter(
                MasterItem.item_class
                == filters.item_class
            )

        if filters.category:
            query = query.filter(
                MasterItem.category_name
                == filters.category
            )

        if filters.dosage_form:
            query = query.filter(
                MasterItem.dosage_form
                == filters.dosage_form
            )

        total = query.count()

        items = (
            query.order_by(
                MasterItem.canonical_name.asc(),
                MasterItem.master_code.asc(),
            )
            .offset(
                (filters.page - 1)
                * filters.per_page
            )
            .limit(filters.per_page)
            .all()
        )

        return (
            [
                self._serialize_item(item)
                for item in items
            ],
            _pagination(
                filters.page,
                filters.per_page,
                total,
            ),
        )

    def get_item(
        self,
        *,
        master_item_id: str,
    ) -> dict | None:
        """
        Return one platform-owned MasterItem for Office inspection.
        """

        if not master_item_id:
            raise ValidationError(
                "Master item id is required."
            )

        item = (
            self.session.query(MasterItem)
            .filter(
                MasterItem.id
                == master_item_id
            )
            .first()
        )

        if item is None:
            return None

        return self._serialize_item(item)


    @staticmethod
    def _serialize_item(
        item: MasterItem,
    ) -> dict:
        return {
            "id": item.id,
            "master_code": item.master_code,
            "canonical_name": item.canonical_name,
            "brand_name": item.brand_name,
            "generic_name": item.generic_name,
            "strength": item.strength,
            "dosage_form": item.dosage_form,
            "pack_quantity": _decimal(
                item.pack_quantity
            ),
            "pack_unit": item.pack_unit,
            "pack_type": item.pack_type,
            "item_class": item.item_class,
            "category_name": item.category_name,
            "subcategory_name": item.subcategory_name,
            "manufacturer": item.manufacturer,
            "country_of_origin": item.country_of_origin,
            "cold_chain": item.cold_chain,
            "restricted_item": item.restricted_item,
            "requires_prescription": (
                item.requires_prescription
            ),
            "tax_classification": (
                item.tax_classification
            ),
            "review_status": item.review_status,
            "is_active": item.is_active,
        }


__all__ = [
    "PlatformMasterItemListFilters",
    "PlatformMasterItemQueryService",
]
