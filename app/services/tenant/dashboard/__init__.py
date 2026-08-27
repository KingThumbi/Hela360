"""
Hela360 Tenant Dashboard Services
=================================

Tenant- and branch-scoped operational dashboard read services.

The dashboard layer is a read-projection layer. It aggregates authoritative
data owned by Hela360's sales, inventory, payment and other business domains
without becoming the source of truth for those domains.
"""

from app.services.tenant.dashboard.dashboard_query_service import (
    DashboardQueryError,
    DashboardQueryService,
)

__all__ = [
    "DashboardQueryError",
    "DashboardQueryService",
]
