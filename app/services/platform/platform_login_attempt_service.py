"""
Hela360 Platform Login Attempt Service
======================================

Authentication-attempt tracking and throttling for Hela360 Office.

Architectural boundaries
------------------------
* Operates only on PlatformLoginAttempt records.
* Never touches tenant LoginAttempt records.
* Carries no tenant or branch scope.
* Login-attempt records are treated as immutable security evidence.
* A successful attempt logically resets account failure counting without
  deleting historical attempts.
* Does not verify passwords or issue JWTs.
* Never commits or rolls back implicitly.

Transaction ownership remains with the caller.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from app.models import PlatformLoginAttempt


DEFAULT_LOOKBACK_WINDOW = timedelta(
    minutes=15
)

DEFAULT_MAX_FAILED_ATTEMPTS = 5
DEFAULT_MAX_IP_FAILURES = 20


class PlatformLoginAttemptService:
    """
    Track Hela360 Office authentication attempts.

    Records are immutable after creation. Successful authentication resets the
    effective account failure counter by becoming the new counting boundary,
    while historical failures remain available for security review.
    """

    def __init__(
        self,
        session,
        *,
        lookback_window: timedelta = (
            DEFAULT_LOOKBACK_WINDOW
        ),
        max_failed_attempts: int = (
            DEFAULT_MAX_FAILED_ATTEMPTS
        ),
        max_ip_failures: int = (
            DEFAULT_MAX_IP_FAILURES
        ),
    ) -> None:
        self.session = session

        self.lookback_window = (
            lookback_window
        )

        self.max_failed_attempts = (
            max_failed_attempts
        )

        self.max_ip_failures = (
            max_ip_failures
        )

    @staticmethod
    def normalize_identifier(
        value: str,
    ) -> str:
        """Normalize a submitted username/email identifier."""

        return str(
            value or ""
        ).strip().lower()

    def record_success(
        self,
        *,
        identifier: str,
        platform_user_id: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> PlatformLoginAttempt:
        """Persist one successful Platform authentication attempt."""

        normalized = (
            self.normalize_identifier(
                identifier
            )
        )

        if not normalized:
            raise ValueError(
                "Login identifier is required."
            )

        attempt = PlatformLoginAttempt(
            platform_user_id=(
                platform_user_id
            ),
            email=normalized,
            ip_address=ip_address,
            user_agent=user_agent,
            successful=True,
            failure_reason=None,
        )

        self.session.add(attempt)
        self.session.flush()

        return attempt

    def record_failure(
        self,
        *,
        identifier: str,
        platform_user_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        failure_reason: str | None = None,
    ) -> PlatformLoginAttempt:
        """Persist one failed Platform authentication attempt."""

        normalized = (
            self.normalize_identifier(
                identifier
            )
        )

        if not normalized:
            raise ValueError(
                "Login identifier is required."
            )

        attempt = PlatformLoginAttempt(
            platform_user_id=(
                platform_user_id
            ),
            email=normalized,
            ip_address=ip_address,
            user_agent=user_agent,
            successful=False,
            failure_reason=(
                failure_reason
            ),
        )

        self.session.add(attempt)
        self.session.flush()

        return attempt

    def latest_success(
        self,
        *,
        identifier: str,
    ) -> PlatformLoginAttempt | None:
        """Return the latest successful attempt for an identifier."""

        normalized = (
            self.normalize_identifier(
                identifier
            )
        )

        return self.session.scalar(
            select(PlatformLoginAttempt)
            .where(
                PlatformLoginAttempt.email
                == normalized,
                PlatformLoginAttempt.successful
                .is_(True),
            )
            .order_by(
                PlatformLoginAttempt
                .created_at
                .desc(),
                PlatformLoginAttempt
                .id
                .desc(),
            )
            .limit(1)
        )

    def recent_attempts(
        self,
        *,
        identifier: str,
    ) -> tuple[
        PlatformLoginAttempt,
        ...,
    ]:
        """Return recent attempts for an identifier."""

        normalized = (
            self.normalize_identifier(
                identifier
            )
        )

        since = (
            datetime.now(UTC)
            - self.lookback_window
        )

        attempts = self.session.scalars(
            select(PlatformLoginAttempt)
            .where(
                PlatformLoginAttempt.email
                == normalized,
                PlatformLoginAttempt.created_at
                >= since,
            )
            .order_by(
                PlatformLoginAttempt
                .created_at
                .desc(),
                PlatformLoginAttempt
                .id
                .desc(),
            )
        ).all()

        return tuple(attempts)

    def failure_count(
        self,
        *,
        identifier: str,
    ) -> int:
        """
        Return consecutive recent failures since the most recent success.

        Historical failures remain persisted but stop contributing to the
        current account lockout counter after a successful authentication.
        """

        normalized = (
            self.normalize_identifier(
                identifier
            )
        )

        since = (
            datetime.now(UTC)
            - self.lookback_window
        )

        latest_success = (
            self.latest_success(
                identifier=normalized
            )
        )

        if (
            latest_success is not None
            and latest_success.created_at
            is not None
        ):
            success_time = (
                latest_success.created_at
            )

            if (
                success_time.tzinfo
                is None
            ):
                success_time = (
                    success_time.replace(
                        tzinfo=UTC
                    )
                )

            if success_time > since:
                since = success_time

        count = self.session.scalar(
            select(func.count())
            .select_from(
                PlatformLoginAttempt
            )
            .where(
                PlatformLoginAttempt.email
                == normalized,
                PlatformLoginAttempt.successful
                .is_(False),
                PlatformLoginAttempt.created_at
                > since,
            )
        )

        return int(
            count or 0
        )

    def ip_failure_count(
        self,
        *,
        ip_address: str | None,
    ) -> int:
        """Return recent failures originating from one IP address."""

        if not ip_address:
            return 0

        since = (
            datetime.now(UTC)
            - self.lookback_window
        )

        count = self.session.scalar(
            select(func.count())
            .select_from(
                PlatformLoginAttempt
            )
            .where(
                PlatformLoginAttempt.ip_address
                == ip_address,
                PlatformLoginAttempt.successful
                .is_(False),
                PlatformLoginAttempt.created_at
                >= since,
            )
        )

        return int(
            count or 0
        )

    def is_account_locked(
        self,
        *,
        identifier: str,
    ) -> bool:
        """Return whether the identifier has reached its failure limit."""

        return (
            self.failure_count(
                identifier=identifier
            )
            >= self.max_failed_attempts
        )

    def is_ip_locked(
        self,
        *,
        ip_address: str | None,
    ) -> bool:
        """Return whether an IP has reached its failure limit."""

        if not ip_address:
            return False

        return (
            self.ip_failure_count(
                ip_address=ip_address
            )
            >= self.max_ip_failures
        )

    def can_attempt(
        self,
        *,
        identifier: str,
        ip_address: str | None = None,
    ) -> bool:
        """Return whether another authentication attempt may proceed."""

        return (
            not self.is_account_locked(
                identifier=identifier
            )
            and not self.is_ip_locked(
                ip_address=ip_address
            )
        )

    def remaining_attempts(
        self,
        *,
        identifier: str,
    ) -> int:
        """Return failures remaining before account throttling."""

        return max(
            0,
            self.max_failed_attempts
            - self.failure_count(
                identifier=identifier
            ),
        )

    def purge_old_attempts(
        self,
        *,
        retention_period: timedelta = (
            timedelta(days=90)
        ),
    ) -> int:
        """
        Delete authentication evidence older than the retention period.

        This is an explicit maintenance operation and still does not commit.
        """

        cutoff = (
            datetime.now(UTC)
            - retention_period
        )

        attempts = tuple(
            self.session.scalars(
                select(
                    PlatformLoginAttempt
                ).where(
                    PlatformLoginAttempt
                    .created_at
                    < cutoff
                )
            ).all()
        )

        if not attempts:
            return 0

        for attempt in attempts:
            self.session.delete(
                attempt
            )

        self.session.flush()

        return len(attempts)


__all__ = [
    "DEFAULT_LOOKBACK_WINDOW",
    "DEFAULT_MAX_FAILED_ATTEMPTS",
    "DEFAULT_MAX_IP_FAILURES",
    "PlatformLoginAttemptService",
]
