"""
Hela360 Office Master Item Supplier Evidence Service
====================================================

Read-only platform-governance projection of supplier catalogue mappings and
supplier price evidence for one MasterItem.

Architectural boundaries
------------------------
* MasterItem, CatalogueSupplier, MasterItemSupplierMapping and
  SupplierItemPrice are platform-owned catalogue data.
* This service does not query tenant Supplier or Product records.
* Supplier evidence is preserved as source evidence rather than promoted into
  canonical MasterItem identity.
* Procurement comparison uses only observations explicitly marked comparable.
* This service performs no mutation.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

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


class PlatformMasterItemSupplierEvidenceService:
    """
    Build a read-only supplier-evidence projection for Hela360 Office.
    """

    def __init__(
        self,
        session,
    ) -> None:
        self.session = session

    def get_evidence(
        self,
        *,
        master_item_id: str,
    ) -> dict | None:
        if not master_item_id:
            raise ValidationError(
                "Master item id is required."
            )

        master_item = (
            self.session.query(MasterItem)
            .filter(
                MasterItem.id
                == master_item_id
            )
            .first()
        )

        if master_item is None:
            return None

        mappings = (
            self.session.query(
                MasterItemSupplierMapping,
                CatalogueSupplier,
            )
            .join(
                CatalogueSupplier,
                CatalogueSupplier.id
                == MasterItemSupplierMapping.catalogue_supplier_id,
            )
            .filter(
                MasterItemSupplierMapping.master_item_id
                == master_item_id
            )
            .order_by(
                CatalogueSupplier.name.asc(),
                MasterItemSupplierMapping.supplier_item_name.asc(),
                MasterItemSupplierMapping.id.asc(),
            )
            .all()
        )

        mapping_ids = [
            mapping.id
            for mapping, _supplier in mappings
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

        comparable_count = 0
        price_count = 0

        for mapping, supplier in mappings:
            mapping_prices = prices_by_mapping.get(
                mapping.id,
                [],
            )

            serialized_prices = [
                self._serialize_price(price)
                for price in mapping_prices
            ]

            comparable_prices = [
                price
                for price in mapping_prices
                if (
                    price.is_comparable_procurement
                    is True
                    and price.effective_date
                    is not None
                )
            ]

            comparable_count += len(
                comparable_prices
            )

            price_count += len(
                mapping_prices
            )

            latest_comparable = (
                max(
                    comparable_prices,
                    key=lambda price: (
                        price.effective_date,
                        price.id,
                    ),
                )
                if comparable_prices
                else None
            )

            serialized_mappings.append(
                {
                    "id": mapping.id,
                    "supplier": {
                        "id": supplier.id,
                        "name": supplier.name,
                        "country": supplier.country,
                        "is_active": supplier.is_active,
                    },
                    "supplier_item_code": (
                        mapping.supplier_item_code
                    ),
                    "supplier_item_name": (
                        mapping.supplier_item_name
                    ),
                    "source_description": (
                        mapping.source_description
                    ),
                    "is_active": mapping.is_active,
                    "latest_comparable_price": (
                        self._serialize_price(
                            latest_comparable
                        )
                        if latest_comparable
                        else None
                    ),
                    "prices": serialized_prices,
                }
            )

        return {
            "master_item_id": master_item.id,
            "master_code": master_item.master_code,
            "canonical_name": master_item.canonical_name,
            "mapping_count": len(
                serialized_mappings
            ),
            "price_observation_count": (
                price_count
            ),
            "comparable_observation_count": (
                comparable_count
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
            "price_type": price.price_type,
            "amount": _decimal(
                price.amount
            ),
            "currency": price.currency,
            "discount_percent": _decimal(
                price.discount_percent
            ),
            "vat_source": price.vat_source,
            "effective_date": _date(
                price.effective_date
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


__all__ = [
    "PlatformMasterItemSupplierEvidenceService",
]
