"""
Hela360 Master Catalogue Query Service
======================================

Tenant-aware read projection over Hela360's platform-owned master catalogue.

Architectural boundaries
------------------------
* MasterItem is platform-owned and has no tenant_id.
* Product remains tenant-owned.
* Product.master_item_id records tenant adoption of a MasterItem.
* Catalogue reads MUST never expose another tenant's Product data.
* Adopted items remain visible and are annotated with adoption state.
* This service is read-only and performs no adoption or catalogue mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import and_, or_

from app.errors import ValidationError
from app.models import MasterItem, Product


ALLOWED_ADOPTION_STATUSES = {
    "all",
    "available",
    "adopted",
}


@dataclass(frozen=True, slots=True)
class MasterCatalogueListFilters:
    """
    Supported tenant-facing master catalogue list filters.
    """

    page: int = 1
    per_page: int = 25
    search: str | None = None
    item_class: str | None = None
    category: str | None = None
    dosage_form: str | None = None
    adoption_status: str = "all"

    @classmethod
    def from_query(cls, args) -> "MasterCatalogueListFilters":
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

        adoption_status = (
            _optional_text(
                args.get("adoption_status")
            )
            or "all"
        ).lower()

        if adoption_status not in ALLOWED_ADOPTION_STATUSES:
            raise ValidationError(
                "adoption_status must be one of: "
                "all, available, adopted."
            )

        return cls(
            page=page,
            per_page=per_page,
            search=_optional_text(
                args.get("search")
                or args.get("q")
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
            adoption_status=adoption_status,
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


def _optional_text(value) -> str | None:
    if value in (None, ""):
        return None

    normalized = str(value).strip()

    return normalized or None


def _decimal(value: Decimal | None) -> str | None:
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


class MasterCatalogueQueryService:
    """
    Build tenant-aware read projections of approved master catalogue items.
    """

    def __init__(self, session):
        self.session = session

    def list_items(
        self,
        *,
        tenant_id: str,
        filters: MasterCatalogueListFilters,
    ) -> tuple[list[dict], dict]:
        """
        Return approved, active MasterItems annotated with tenant adoption.
        """

        if not tenant_id:
            raise ValidationError(
                "Authenticated tenant is unavailable."
            )

        query = self._base_query(
            tenant_id=tenant_id
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

        if filters.adoption_status == "adopted":
            query = query.filter(
                Product.id.is_not(None)
            )

        elif filters.adoption_status == "available":
            query = query.filter(
                Product.id.is_(None)
            )

        total = query.count()

        rows = (
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

        items = [
            self._serialize_item(
                master_item,
                product,
            )
            for master_item, product in rows
        ]

        return (
            items,
            _pagination(
                filters.page,
                filters.per_page,
                total,
            ),
        )

    def get_item(
        self,
        *,
        tenant_id: str,
        master_item_id: str,
    ) -> dict | None:
        """
        Return one approved, active MasterItem with tenant adoption state.
        """

        if not tenant_id:
            raise ValidationError(
                "Authenticated tenant is unavailable."
            )

        row = (
            self._base_query(
                tenant_id=tenant_id
            )
            .filter(
                MasterItem.id
                == master_item_id
            )
            .first()
        )

        if row is None:
            return None

        master_item, product = row

        return self._serialize_item(
            master_item,
            product,
        )

    def _base_query(
        self,
        *,
        tenant_id: str,
    ):
        """
        Build the canonical tenant-safe outer join.

        The tenant condition belongs in the JOIN predicate rather than a
        WHERE clause so unadopted MasterItems remain visible.
        """

        return (
            self.session.query(
                MasterItem,
                Product,
            )
            .outerjoin(
                Product,
                and_(
                    Product.master_item_id
                    == MasterItem.id,
                    Product.tenant_id
                    == tenant_id,
                ),
            )
            .filter(
                MasterItem.review_status
                == "approved",
                MasterItem.is_active.is_(True),
            )
        )

    @staticmethod
    def _serialize_item(
        master_item: MasterItem,
        product: Product | None,
    ) -> dict:
        """
        Serialize canonical identity separately from tenant adoption state.
        """

        return {
            "id": master_item.id,
            "master_code": master_item.master_code,
            "canonical_name": master_item.canonical_name,
            "brand_name": master_item.brand_name,
            "generic_name": master_item.generic_name,
            "strength": master_item.strength,
            "dosage_form": master_item.dosage_form,
            "pack_quantity": _decimal(
                master_item.pack_quantity
            ),
            "pack_unit": master_item.pack_unit,
            "pack_type": master_item.pack_type,
            "item_class": master_item.item_class,
            "category_name": master_item.category_name,
            "subcategory_name": master_item.subcategory_name,
            "manufacturer": master_item.manufacturer,
            "country_of_origin": master_item.country_of_origin,
            "cold_chain": master_item.cold_chain,
            "restricted_item": master_item.restricted_item,
            "requires_prescription": (
                master_item.requires_prescription
            ),
            "tax_classification": (
                master_item.tax_classification
            ),
            "review_status": master_item.review_status,
            "is_active": master_item.is_active,
            "adoption": {
                "is_adopted": product is not None,
                "product_id": (
                    product.id
                    if product
                    else None
                ),
                "internal_sku": (
                    product.internal_sku
                    if product
                    else None
                ),
                "product_name": (
                    product.name
                    if product
                    else None
                ),
                "product_is_active": (
                    product.is_active
                    if product
                    else None
                ),
            },
        }
