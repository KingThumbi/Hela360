"""
Tenant business-time helpers.

Persisted operational timestamps remain UTC.

Calendar-sensitive business rules, such as stock expiry, operate against
the authenticated tenant's configured IANA timezone.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.models import Tenant


class BusinessTimeError(ValueError):
    """Raised when tenant business-time context cannot be resolved."""


def resolve_tenant_timezone(timezone_name: str) -> ZoneInfo:
    """
    Resolve a configured tenant IANA timezone.

    Invalid configuration must fail explicitly rather than silently falling
    back to the application server timezone.
    """

    try:
        return ZoneInfo(timezone_name)
    except (
        ZoneInfoNotFoundError,
        ValueError,
        TypeError,
    ) as exc:
        raise BusinessTimeError(
            f"Invalid tenant timezone: {timezone_name!r}."
        ) from exc


def tenant_operational_date(
    session,
    *,
    tenant_id: str,
    now: datetime | None = None,
) -> date:
    """
    Resolve the tenant-local calendar date for a UTC operational instant.
    """

    if not tenant_id:
        raise BusinessTimeError(
            "Authenticated tenant is unavailable."
        )

    tenant = (
        session.query(Tenant)
        .filter(Tenant.id == tenant_id)
        .one_or_none()
    )

    if tenant is None:
        raise BusinessTimeError(
            "Authenticated tenant does not exist."
        )

    instant = now or datetime.now(UTC)

    if instant.tzinfo is None:
        raise BusinessTimeError(
            "Operational timestamp must be timezone-aware."
        )

    tenant_timezone = resolve_tenant_timezone(
        tenant.timezone
    )

    return instant.astimezone(
        tenant_timezone
    ).date()
