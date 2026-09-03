"""
Hela360 Office Catalogue Category Query Service
================================================

Read-only category distribution derived from platform-owned MasterItems.

Architectural boundaries
------------------------
* MasterItem category_name and subcategory_name are platform catalogue data.
* Tenant ProductCategory records are not queried or reused.
* Categories in this service are derived governance projections, not persisted
  platform category entities.
* This service performs no mutation.
"""

from __future__ import annotations

from sqlalchemy import case, func

from app.models import MasterItem


class PlatformCatalogueCategoryQueryService:
    """
    Build category and subcategory coverage projections for Hela360 Office.
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

        categorized_items = (
            self.session.query(MasterItem)
            .filter(
                MasterItem.category_name.isnot(None)
            )
            .count()
        )

        category_rows = (
            self.session.query(
                MasterItem.category_name.label(
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
                MasterItem.category_name.isnot(None)
            )
            .group_by(
                MasterItem.category_name
            )
            .order_by(
                MasterItem.category_name.asc()
            )
            .all()
        )

        subcategory_rows = (
            self.session.query(
                MasterItem.category_name.label(
                    "category_name"
                ),
                MasterItem.subcategory_name.label(
                    "name"
                ),
                func.count(
                    MasterItem.id
                ).label(
                    "item_count"
                ),
            )
            .filter(
                MasterItem.category_name.isnot(None),
                MasterItem.subcategory_name.isnot(None),
            )
            .group_by(
                MasterItem.category_name,
                MasterItem.subcategory_name,
            )
            .order_by(
                MasterItem.category_name.asc(),
                MasterItem.subcategory_name.asc(),
            )
            .all()
        )

        subcategories_by_category: dict[
            str,
            list[dict],
        ] = {}

        for row in subcategory_rows:
            subcategories_by_category.setdefault(
                row.category_name,
                [],
            ).append(
                {
                    "name": row.name,
                    "item_count": int(
                        row.item_count
                    ),
                }
            )

        categories = [
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
                "subcategories": (
                    subcategories_by_category.get(
                        row.name,
                        [],
                    )
                ),
            }
            for row in category_rows
        ]

        return {
            "total_items": total_items,
            "categorized_items": categorized_items,
            "uncategorized_items": (
                total_items
                - categorized_items
            ),
            "category_count": len(
                categories
            ),
            "categories": categories,
        }


__all__ = [
    "PlatformCatalogueCategoryQueryService",
]
