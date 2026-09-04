"""
Hela360 Office Catalogue Brand Query Service
=============================================

Read-only brand distribution derived from platform-owned MasterItems.

Architectural boundaries
------------------------
* MasterItem.brand_name is platform catalogue metadata.
* Tenant Brand records are not queried or reused.
* Brand rows returned here are derived governance projections, not persisted
  platform brand entities.
* This service performs no mutation or normalization.
"""

from __future__ import annotations

from sqlalchemy import case, func

from app.models import MasterItem


class PlatformCatalogueBrandQueryService:
    """
    Build brand coverage projections for Hela360 Office.
    """

    def __init__(
        self,
        session,
    ) -> None:
        self.session = session

    def get_summary(
        self,
    ) -> dict:
        total_items = (
            self.session.query(MasterItem)
            .count()
        )

        branded_items = (
            self.session.query(MasterItem)
            .filter(
                MasterItem.brand_name.isnot(None)
            )
            .count()
        )

        brand_rows = (
            self.session.query(
                MasterItem.brand_name.label(
                    "name"
                ),
                func.count(
                    MasterItem.id
                ).label(
                    "item_count"
                ),
                func.sum(
                    case(
                        (
                            MasterItem.review_status
                            == "approved",
                            1,
                        ),
                        else_=0,
                    )
                ).label(
                    "approved_count"
                ),
                func.sum(
                    case(
                        (
                            MasterItem.review_status
                            == "draft",
                            1,
                        ),
                        else_=0,
                    )
                ).label(
                    "draft_count"
                ),
                func.sum(
                    case(
                        (
                            MasterItem.is_active
                            .is_(True),
                            1,
                        ),
                        else_=0,
                    )
                ).label(
                    "active_count"
                ),
                func.sum(
                    case(
                        (
                            MasterItem.is_active
                            .is_(False),
                            1,
                        ),
                        else_=0,
                    )
                ).label(
                    "inactive_count"
                ),
            )
            .filter(
                MasterItem.brand_name.isnot(None)
            )
            .group_by(
                MasterItem.brand_name
            )
            .order_by(
                MasterItem.brand_name.asc()
            )
            .all()
        )

        brands = [
            {
                "name": row.name,
                "item_count": int(
                    row.item_count
                ),
                "approved_count": int(
                    row.approved_count or 0
                ),
                "draft_count": int(
                    row.draft_count or 0
                ),
                "active_count": int(
                    row.active_count or 0
                ),
                "inactive_count": int(
                    row.inactive_count or 0
                ),
            }
            for row in brand_rows
        ]

        return {
            "total_items": total_items,
            "branded_items": branded_items,
            "unbranded_items": (
                total_items
                - branded_items
            ),
            "brand_count": len(
                brands
            ),
            "brands": brands,
        }


__all__ = [
    "PlatformCatalogueBrandQueryService",
]
