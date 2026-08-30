"""
Hela360 Master Catalogue Adoption Service
=========================================

Dedicated command workflow for adopting one approved platform MasterItem
into a tenant-owned Product catalogue.

Architectural boundaries
------------------------
* MasterItem remains platform-owned.
* Product remains tenant-owned.
* Product.master_item_id records catalogue lineage.
* Tenant SKU allocation is delegated to ProductIdentityService.
* Tenant Brand, ProductCategory and UnitOfMeasure resolution is delegated
  to ProductReferenceService.
* Supplier prices, stock, tenant sale prices and procurement state are not
  copied from the master catalogue.
* MasterItem.master_code is never used as the tenant internal SKU.
* This service flushes mutations but never commits or rolls back.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from app.errors import ValidationError
from app.models import MasterItem, Product, ProductUnit
from app.services.common.audit_actions import AuditAction
from app.services.common.audit_modules import AuditModule
from app.services.common.audit_service import AuditService
from app.services.tenant.products import (
    ProductIdentityService,
    ProductReferenceService,
)


class MasterCatalogueAdoptionError(ValidationError):
    """
    Base error for master catalogue adoption failures.
    """


class MasterItemNotAvailableError(
    MasterCatalogueAdoptionError
):
    """
    Raised when a MasterItem cannot be adopted.
    """


class MasterItemAlreadyAdoptedError(
    MasterCatalogueAdoptionError
):
    """
    Raised when the tenant already has a Product linked to the MasterItem.
    """

    def __init__(
        self,
        product: Product,
    ):
        super().__init__(
            "This catalogue item is already in your product catalogue."
        )
        self.product = product


@dataclass(frozen=True, slots=True)
class MasterCatalogueAdoptionResult:
    """
    Result of one successful catalogue adoption.
    """

    master_item: MasterItem
    product: Product
    product_unit: ProductUnit | None


class MasterCatalogueAdoptionService:
    """
    Adopt approved MasterItems into tenant-owned Products.
    """

    def __init__(
        self,
        session: Session,
        *,
        audit_service: AuditService | None = None,
    ):
        self.session = session
        self.identity_service = ProductIdentityService(
            session
        )
        self.reference_service = ProductReferenceService(
            session
        )
        self.audit_service = (
            audit_service
            if audit_service is not None
            else AuditService()
        )

    def adopt(
        self,
        *,
        tenant_id: str,
        master_item_id: str,
        internal_sku: str | None = None,
        name: str | None = None,
        category_name: str | None = None,
        brand_name: str | None = None,
        unit_code: str | None = None,
        unit_name: str | None = None,
        user_id: str | None = None,
        branch_id: str | None = None,
        session_id: str | None = None,
    ) -> MasterCatalogueAdoptionResult:
        """
        Create one tenant Product linked to an approved MasterItem.

        The caller owns the surrounding transaction.
        """

        if not tenant_id:
            raise MasterCatalogueAdoptionError(
                "Authenticated tenant is unavailable."
            )

        master_item = self._get_adoptable_master_item(
            master_item_id=master_item_id
        )

        existing_product = (
            self.session.query(Product)
            .filter(
                Product.tenant_id == tenant_id,
                Product.master_item_id
                == master_item.id,
            )
            .first()
        )

        if existing_product is not None:
            raise MasterItemAlreadyAdoptedError(
                existing_product
            )

        resolved_sku = (
            self.identity_service
            .resolve_internal_sku(
                tenant_id=tenant_id,
                supplied_sku=internal_sku,
            )
        )

        resolved_name = self._required_product_text(
            name
            if self._optional_text(name) is not None
            else master_item.canonical_name,
            field_name="Product name",
            max_length=200,
        )

        resolved_generic_name = (
            self._optional_product_text(
                master_item.generic_name,
                field_name="Generic name",
                max_length=200,
            )
        )

        resolved_manufacturer = (
            self._optional_product_text(
                master_item.manufacturer,
                field_name="Manufacturer",
                max_length=150,
            )
        )

        resolved_country = (
            self._optional_product_text(
                master_item.country_of_origin,
                field_name="Country of origin",
                max_length=100,
            )
        )

        resolved_category_name = (
            self._optional_text(category_name)
            or self._optional_text(
                master_item.category_name
            )
        )

        resolved_brand_name = (
            self._optional_text(brand_name)
            or self._optional_text(
                master_item.brand_name
            )
        )

        category = (
            self.reference_service
            .resolve_category(
                tenant_id=tenant_id,
                category_name=resolved_category_name,
            )
        )

        brand = (
            self.reference_service
            .resolve_brand(
                tenant_id=tenant_id,
                brand_name=resolved_brand_name,
            )
        )

        # Unit adoption is intentionally explicit.
        #
        # MasterItem.pack_unit is supplier/catalogue evidence and is not
        # automatically interpreted as a tenant UnitOfMeasure code.
        unit = (
            self.reference_service
            .resolve_unit(
                tenant_id=tenant_id,
                unit_code=unit_code,
                unit_name=unit_name,
            )
        )

        product = Product(
            tenant_id=tenant_id,
            master_item_id=str(master_item.id),
            category_id=(
                str(category.id)
                if category
                else None
            ),
            brand_id=(
                str(brand.id)
                if brand
                else None
            ),
            unit_id=(
                str(unit.id)
                if unit
                else None
            ),
            internal_sku=resolved_sku,
            supplier_sku=None,
            name=resolved_name,
            generic_name=resolved_generic_name,
            description=None,
            product_type="stockable",
            track_inventory=True,
            track_batches=False,
            track_expiry=False,
            requires_prescription=(
                master_item.requires_prescription
                is True
            ),
            allow_negative_stock=False,
            reorder_level=Decimal("0"),
            reorder_qty=Decimal("0"),
            min_sale_price=None,
            default_sale_price=None,
            cost_price=None,
            # Catalogue tax evidence is deliberately not treated as a
            # tenant tax-code assignment.
            tax_code=None,
            pack_size=None,
            manufacturer=resolved_manufacturer,
            country_of_origin=resolved_country,
            image_url=None,
            is_active=True,
        )

        self.session.add(product)
        self.session.flush()

        product_unit = None

        if unit is not None:
            product_unit = ProductUnit(
                tenant_id=tenant_id,
                product_id=str(product.id),
                unit_id=str(unit.id),
                conversion_factor_to_base=Decimal("1"),
                is_base=True,
                can_sell=True,
                can_receive=True,
                sale_price=None,
                minimum_sale_price=None,
                is_active=True,
            )

            self.session.add(product_unit)
            self.session.flush()

        self.audit_service.log(
            module=AuditModule.CATALOGUE,
            action=(
                AuditAction
                .MASTER_CATALOGUE_ITEM_ADOPTED
            ),
            entity_type="Product",
            tenant_id=tenant_id,
            entity_id=str(product.id),
            user_id=user_id,
            branch_id=branch_id,
            session_id=session_id,
            new_values={
                "master_item_id": str(
                    master_item.id
                ),
                "master_code": (
                    master_item.master_code
                ),
                "product_id": str(product.id),
                "internal_sku": (
                    product.internal_sku
                ),
            },
            details={
                "source": "master_catalogue",
            },
            commit=False,
        )

        return MasterCatalogueAdoptionResult(
            master_item=master_item,
            product=product,
            product_unit=product_unit,
        )

    def _get_adoptable_master_item(
        self,
        *,
        master_item_id: str,
    ) -> MasterItem:
        master_item = (
            self.session.query(MasterItem)
            .filter(
                MasterItem.id == master_item_id,
                MasterItem.review_status
                == "approved",
                MasterItem.is_active.is_(True),
            )
            .first()
        )

        if master_item is None:
            raise MasterItemNotAvailableError(
                "Catalogue item is not available for adoption."
            )

        return master_item

    @staticmethod
    def _optional_text(
        value,
    ) -> str | None:
        if value is None:
            return None

        normalized = str(value).strip()

        return normalized or None

    def _required_product_text(
        self,
        value,
        *,
        field_name: str,
        max_length: int,
    ) -> str:
        normalized = self._optional_text(
            value
        )

        if normalized is None:
            raise MasterCatalogueAdoptionError(
                f"{field_name} is required."
            )

        if len(normalized) > max_length:
            raise MasterCatalogueAdoptionError(
                f"{field_name} exceeds the "
                f"{max_length}-character Product limit."
            )

        return normalized

    def _optional_product_text(
        self,
        value,
        *,
        field_name: str,
        max_length: int,
    ) -> str | None:
        normalized = self._optional_text(
            value
        )

        if normalized is None:
            return None

        if len(normalized) > max_length:
            raise MasterCatalogueAdoptionError(
                f"{field_name} exceeds the "
                f"{max_length}-character Product limit."
            )

        return normalized
