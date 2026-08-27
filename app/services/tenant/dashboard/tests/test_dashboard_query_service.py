from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

from app.services.tenant.dashboard.dashboard_query_service import (
    DashboardPeriod,
    DashboardQueryError,
    DashboardQueryService,
    _day_period,
    _money,
    _resolve_timezone,
)


def test_money_preserves_exact_decimal_values() -> None:
    assert _money(Decimal("1000")) == "1000.00"
    assert _money(Decimal("1000.5")) == "1000.50"
    assert _money(None) == "0.00"


def test_day_period_uses_tenant_timezone_and_utc_boundaries() -> None:
    period = _day_period(
        date(2026, 8, 21),
        ZoneInfo("Africa/Nairobi"),
    )

    assert (
        period.start
        == datetime(
            2026,
            8,
            20,
            21,
            0,
            tzinfo=timezone.utc,
        )
    )

    assert (
        period.end
        == datetime(
            2026,
            8,
            21,
            21,
            0,
            tzinfo=timezone.utc,
        )
    )


def test_invalid_timezone_is_rejected() -> None:
    with pytest.raises(
        DashboardQueryError,
        match="Invalid tenant timezone",
    ):
        _resolve_timezone(
            "Not/A/Real-Timezone"
        )


def test_overview_requires_tenant() -> None:
    service = DashboardQueryService(
        session=SimpleNamespace()
    )

    with pytest.raises(
        DashboardQueryError,
        match="Authenticated tenant is unavailable",
    ):
        service.overview(
            tenant_id="",
            branch_id="branch-1",
        )


def test_overview_requires_branch() -> None:
    service = DashboardQueryService(
        session=SimpleNamespace()
    )

    with pytest.raises(
        DashboardQueryError,
        match="Authenticated user is not assigned to a branch",
    ):
        service.overview(
            tenant_id="tenant-1",
            branch_id=None,
        )
