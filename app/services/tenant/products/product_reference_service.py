"""
Product Reference Service
=========================

Centralized resolution of tenant-owned Product reference data.

Responsibilities
----------------
* Resolve or create tenant ProductCategory records by name.
* Resolve or create tenant Brand records by name.
* Resolve or create tenant UnitOfMeasure records by code.
* Preserve tenant isolation for all reference data.
* Keep reusable Product reference rules out of Flask routes.
* Provide the same reference-resolution path for ordinary Product creation
  and future master-catalogue adoption.

This service does not commit transactions. The caller owns commit/rollback.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import Brand, ProductCategory, UnitOfMeasure


class ProductReferenceService:
    """
    Resolve tenant-owned Product reference entities.
    """

    def __init__(self, session: Session):
        self.session = session

    def resolve_brand(
        self,
        *,
        tenant_id: str,
        brand_name: str | None,
    ) -> Brand | None:
        """
        Resolve an existing tenant Brand by name or create it.

        Empty values resolve to None.
        """

        normalized_name = self._optional_text(
            brand_name
        )

        if normalized_name is None:
            return None

        brand = (
            self.session.query(Brand)
            .filter(
                Brand.tenant_id == tenant_id,
                Brand.name == normalized_name,
            )
            .first()
        )

        if brand is not None:
            return brand

        brand = Brand(
            tenant_id=tenant_id,
            name=normalized_name,
            is_active=True,
        )

        self.session.add(brand)
        self.session.flush()

        return brand

    def resolve_category(
        self,
        *,
        tenant_id: str,
        category_name: str | None,
    ) -> ProductCategory | None:
        """
        Resolve an existing tenant ProductCategory by name or create it.

        Empty values resolve to None.
        """

        normalized_name = self._optional_text(
            category_name
        )

        if normalized_name is None:
            return None

        category = (
            self.session.query(ProductCategory)
            .filter(
                ProductCategory.tenant_id
                == tenant_id,
                ProductCategory.name
                == normalized_name,
            )
            .first()
        )

        if category is not None:
            return category

        category = ProductCategory(
            tenant_id=tenant_id,
            name=normalized_name,
            is_active=True,
        )

        self.session.add(category)
        self.session.flush()

        return category

    def resolve_unit(
        self,
        *,
        tenant_id: str,
        unit_code: str | None,
        unit_name: str | None,
    ) -> UnitOfMeasure | None:
        """
        Resolve an existing tenant UnitOfMeasure by code or create it.

        Existing behavior is intentionally preserved:

        * no code and no name -> None
        * supplied code matching an existing tenant unit -> existing unit
        * creation requires both unit_code and unit_name
        """

        normalized_code = self._optional_text(
            unit_code
        )
        normalized_name = self._optional_text(
            unit_name
        )

        if (
            normalized_code is None
            and normalized_name is None
        ):
            return None

        if normalized_code is not None:
            existing = (
                self.session.query(UnitOfMeasure)
                .filter(
                    UnitOfMeasure.tenant_id
                    == tenant_id,
                    UnitOfMeasure.code
                    == normalized_code,
                )
                .first()
            )

            if existing is not None:
                return existing

        if normalized_code is None:
            raise ValueError(
                "unit_code is required when creating a new unit."
            )

        if normalized_name is None:
            raise ValueError(
                "unit_name is required when creating a new unit."
            )

        unit = UnitOfMeasure(
            tenant_id=tenant_id,
            code=normalized_code,
            name=normalized_name,
            base_factor=Decimal("1"),
        )

        self.session.add(unit)
        self.session.flush()

        return unit

    @staticmethod
    def _optional_text(
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = str(value).strip()

        return normalized or None
