"""
Hela360 Office Catalogue Data Quality Service
==============================================

Read-only platform catalogue quality observations.

Architectural boundaries
------------------------
* MasterItem is platform-owned and global.
* Supplier mappings and supplier prices are platform evidence.
* This service reports objective catalogue observations.
* Missing optional metadata is not treated as an invalid MasterItem.
* No quality score or severity policy is inferred.
* This service performs no mutation.
"""

from __future__ import annotations

from sqlalchemy import distinct

from app.models import (
    MasterItem,
    MasterItemSupplierMapping,
    SupplierItemPrice,
)


class PlatformCatalogueDataQualityService:
    """
    Build platform-wide catalogue quality observations for Hela360 Office.
    """

    def __init__(
        self,
        session,
    ) -> None:
        self.session = session

    def get_summary(
        self,
    ) -> dict:
        total = (
            self.session.query(MasterItem)
            .count()
        )

        approved = (
            self.session.query(MasterItem)
            .filter(
                MasterItem.review_status
                == "approved"
            )
            .count()
        )

        draft = (
            self.session.query(MasterItem)
            .filter(
                MasterItem.review_status
                == "draft"
            )
            .count()
        )

        active = (
            self.session.query(MasterItem)
            .filter(
                MasterItem.is_active.is_(True)
            )
            .count()
        )

        inactive = total - active

        categorized = (
            self.session.query(MasterItem)
            .filter(
                MasterItem.category_name
                .isnot(None)
            )
            .count()
        )

        classified = (
            self.session.query(MasterItem)
            .filter(
                MasterItem.item_class
                .isnot(None)
            )
            .count()
        )

        dosage_form_populated = (
            self.session.query(MasterItem)
            .filter(
                MasterItem.dosage_form
                .isnot(None)
            )
            .count()
        )

        complete_pack_definition = (
            self.session.query(MasterItem)
            .filter(
                MasterItem.pack_quantity
                .isnot(None),
                MasterItem.pack_unit
                .isnot(None),
                MasterItem.pack_type
                .isnot(None),
            )
            .count()
        )

        generic_name_populated = (
            self.session.query(MasterItem)
            .filter(
                MasterItem.generic_name
                .isnot(None)
            )
            .count()
        )

        manufacturer_populated = (
            self.session.query(MasterItem)
            .filter(
                MasterItem.manufacturer
                .isnot(None)
            )
            .count()
        )

        mapped_master_items = (
            self.session.query(
                distinct(
                    MasterItemSupplierMapping
                    .master_item_id
                )
            )
            .count()
        )

        priced_master_items = (
            self.session.query(
                distinct(
                    MasterItemSupplierMapping
                    .master_item_id
                )
            )
            .join(
                SupplierItemPrice,
                SupplierItemPrice
                .supplier_mapping_id
                == MasterItemSupplierMapping.id,
            )
            .count()
        )

        comparable_master_items = (
            self.session.query(
                distinct(
                    MasterItemSupplierMapping
                    .master_item_id
                )
            )
            .join(
                SupplierItemPrice,
                SupplierItemPrice
                .supplier_mapping_id
                == MasterItemSupplierMapping.id,
            )
            .filter(
                SupplierItemPrice
                .is_comparable_procurement
                .is_(True)
            )
            .count()
        )

        dated_comparable_master_items = (
            self.session.query(
                distinct(
                    MasterItemSupplierMapping
                    .master_item_id
                )
            )
            .join(
                SupplierItemPrice,
                SupplierItemPrice
                .supplier_mapping_id
                == MasterItemSupplierMapping.id,
            )
            .filter(
                SupplierItemPrice
                .is_comparable_procurement
                .is_(True),
                SupplierItemPrice
                .effective_date
                .isnot(None),
            )
            .count()
        )

        return {
            "catalogue": {
                "total": total,
                "approved": approved,
                "draft": draft,
                "active": active,
                "inactive": inactive,
            },
            "enrichment": {
                "categorized": categorized,
                "uncategorized": (
                    total - categorized
                ),
                "classified": classified,
                "unclassified": (
                    total - classified
                ),
                "dosage_form_populated": (
                    dosage_form_populated
                ),
                "dosage_form_missing": (
                    total
                    - dosage_form_populated
                ),
                "complete_pack_definition": (
                    complete_pack_definition
                ),
                "incomplete_pack_definition": (
                    total
                    - complete_pack_definition
                ),
                "generic_name_populated": (
                    generic_name_populated
                ),
                "generic_name_missing": (
                    total
                    - generic_name_populated
                ),
                "manufacturer_populated": (
                    manufacturer_populated
                ),
                "manufacturer_missing": (
                    total
                    - manufacturer_populated
                ),
            },
            "provenance": {
                "with_supplier_mapping": (
                    mapped_master_items
                ),
                "without_supplier_mapping": (
                    total
                    - mapped_master_items
                ),
                "with_price_evidence": (
                    priced_master_items
                ),
                "without_price_evidence": (
                    total
                    - priced_master_items
                ),
                "with_comparable_evidence": (
                    comparable_master_items
                ),
                "with_dated_comparable_evidence": (
                    dated_comparable_master_items
                ),
            },
        }


__all__ = [
    "PlatformCatalogueDataQualityService",
]
