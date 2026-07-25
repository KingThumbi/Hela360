"""
Login Attempt Service

Enterprise authentication throttling and account protection service.

This service is responsible for recording every authentication attempt
and enforcing configurable security policies that protect tenant
accounts against brute-force attacks and credential stuffing.

Responsibilities
----------------
- Record successful login attempts
- Record failed login attempts
- Enforce account lockouts
- Enforce IP-based throttling
- Determine whether authentication may proceed
- Unlock accounts
- Expire historical login attempts
- Provide authentication metrics

This service intentionally performs no password verification and issues
no JWTs.

Password verification belongs to PasswordService.
JWT issuance belongs to JWTService.
Authentication orchestration belongs to AuthenticationService.

Hela360 Enterprise Pharmacy POS & ERP
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, func, or_, select

from app.extensions import db
from app.models.security import LoginAttempt


# ============================================================================
# Enterprise Defaults
# ============================================================================

DEFAULT_LOOKBACK_WINDOW = timedelta(minutes=15)
DEFAULT_LOCKOUT_DURATION = timedelta(minutes=30)

DEFAULT_MAX_FAILED_ATTEMPTS = 5
DEFAULT_MAX_IP_FAILURES = 20

STATUS_SUCCESS = "success"
STATUS_FAILURE = "failure"


# ============================================================================
# LoginAttemptService
# ============================================================================

class LoginAttemptService:
    """
    Enterprise login attempt management service.

    The service centralizes authentication throttling for every tenant.

    Features
    --------
    • Failed login tracking
    • Successful login auditing
    • User lockout detection
    • IP reputation monitoring
    • Brute-force protection
    • Credential stuffing mitigation
    • Automatic cleanup of stale records

    Notes
    -----
    This service never authenticates users directly. It only records
    authentication activity and evaluates security policies.
    """

    def __init__(
        self,
        *,
        lookback_window: timedelta = DEFAULT_LOOKBACK_WINDOW,
        lockout_duration: timedelta = DEFAULT_LOCKOUT_DURATION,
        max_failed_attempts: int = DEFAULT_MAX_FAILED_ATTEMPTS,
        max_ip_failures: int = DEFAULT_MAX_IP_FAILURES,
    ) -> None:
        self.lookback_window = lookback_window
        self.lockout_duration = lockout_duration
        self.max_failed_attempts = max_failed_attempts
        self.max_ip_failures = max_ip_failures

# ============================================================================
# Recording Login Attempts
# ============================================================================

    def record_success(
        self,
        *,
        email: str,
        tenant_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> LoginAttempt:
        """
        Record a successful login attempt.
        """

        attempt = LoginAttempt(
            email=email.strip().lower(),
            tenant_id=tenant_id,
            ip_address=ip_address,
            user_agent=user_agent,
            successful=True,
            failure_reason=None,
        )

        db.session.add(attempt)
        db.session.commit()

        return attempt

    def record_failure(
        self,
        *,
        email: str,
        tenant_id: str | None = None,
        ip_address: str |None = None,
        user_agent: str | None = None,
        failure_reason: str | None = None,
    ) -> LoginAttempt:
        """
        Record a failed login attempt.
        """

        attempt = LoginAttempt(
            email=email.strip().lower(),
            tenant_id=tenant_id,
            ip_address=ip_address,
            user_agent=user_agent,
            successful=False,
            failure_reason=failure_reason,
        )

        db.session.add(attempt)
        db.session.commit()

        return attempt        
    
# ============================================================================
# Query Operations
# ============================================================================

    def latest_attempt(
        self,
        *,
        email: str,
        tenant_id: str | None = None,
    ) -> LoginAttempt | None:
        """
        Return the most recent login attempt for an email address.
        """

        stmt = (
            select(LoginAttempt)
            .where(
                LoginAttempt.email == email.strip().lower(),
            )
            .order_by(LoginAttempt.created_at.desc())
            .limit(1)
        )

        if tenant_id is not None:
            stmt = stmt.where(
                LoginAttempt.tenant_id == tenant_id,
            )

        return db.session.scalar(stmt)

    def recent_attempts(
        self,
        *,
        email: str,
        tenant_id: str | None = None,
    ) -> list[LoginAttempt]:
        """
        Return recent login attempts within the configured lookback window.
        """

        since = datetime.now(UTC) - self.lookback_window

        stmt = (
            select(LoginAttempt)
            .where(
                LoginAttempt.email == email.strip().lower(),
                LoginAttempt.created_at >= since,
            )
            .order_by(LoginAttempt.created_at.desc())
        )

        if tenant_id is not None:
            stmt = stmt.where(
                LoginAttempt.tenant_id == tenant_id,
            )

        return list(db.session.scalars(stmt))

    def recent_failures(
        self,
        *,
        email: str,
        tenant_id: str | None = None,
    ) -> list[LoginAttempt]:
        """
        Return failed login attempts within the configured lookback window.
        """

        since = datetime.now(UTC) - self.lookback_window

        stmt = (
            select(LoginAttempt)
            .where(
                LoginAttempt.email == email.strip().lower(),
                LoginAttempt.successful.is_(False),
                LoginAttempt.created_at >= since,
            )
            .order_by(LoginAttempt.created_at.desc())
        )

        if tenant_id is not None:
            stmt = stmt.where(
                LoginAttempt.tenant_id == tenant_id,
            )

        return list(db.session.scalars(stmt))

    def failure_count(
        self,
        *,
        email: str,
        tenant_id: str | None = None,
    ) -> int:
        """
        Return the number of failed login attempts within the lookback
        window.
        """

        since = datetime.now(UTC) - self.lookback_window

        stmt = (
            select(func.count())
            .select_from(LoginAttempt)
            .where(
                LoginAttempt.email == email.strip().lower(),
                LoginAttempt.successful.is_(False),
                LoginAttempt.created_at >= since,
            )
        )

        if tenant_id is not None:
            stmt = stmt.where(
                LoginAttempt.tenant_id == tenant_id,
            )

        return int(db.session.scalar(stmt) or 0)

    def ip_failure_count(
        self,
        *,
        ip_address: str,
    ) -> int:
        """
        Return failed login attempts originating from an IP address.
        """

        since = datetime.now(UTC) - self.lookback_window

        stmt = (
            select(func.count())
            .select_from(LoginAttempt)
            .where(
                LoginAttempt.ip_address == ip_address,
                LoginAttempt.successful.is_(False),
                LoginAttempt.created_at >= since,
            )
        )

        return int(db.session.scalar(stmt) or 0)

    def is_account_locked(
        self,
        *,
        email: str,
        tenant_id: str | None = None,
    ) -> bool:
        """
        Determine whether an account is temporarily locked due to
        excessive authentication failures.
        """

        return (
            self.failure_count(
                email=email,
                tenant_id=tenant_id,
            )
            >= self.max_failed_attempts
        )

    def is_ip_locked(
        self,
        *,
        ip_address: str,
    ) -> bool:
        """
        Determine whether an IP address is temporarily throttled.
        """

        return (
            self.ip_failure_count(
                ip_address=ip_address,
            )
            >= self.max_ip_failures
        )

    def can_attempt(
        self,
        *,
        email: str,
        ip_address: str,
        tenant_id: str | None = None,
    ) -> bool:
        """
        Return True when another authentication attempt should be
        permitted.
        """

        return (
            not self.is_account_locked(
                email=email,
                tenant_id=tenant_id,
            )
            and not self.is_ip_locked(
                ip_address=ip_address,
            )
        )

    def remaining_attempts(
        self,
        *,
        email: str,
        tenant_id: str | None = None,
    ) -> int:
        """
        Return the number of failed login attempts remaining before
        account lockout.
        """

        failures = self.failure_count(
            email=email,
            tenant_id=tenant_id,
        )

        return max(
            0,
            self.max_failed_attempts - failures,
        )

# ============================================================================
# Maintenance & Administration
# ============================================================================

    def reset_failures(
        self,
        *,
        email: str,
        tenant_id: str | None = None,
    ) -> int:
        """
        Remove failed login attempts for a user within the lookback
        window.

        Typically called after a successful login or by an
        administrator unlocking an account.

        Returns
        -------
        int
            Number of deleted records.
        """

        since = datetime.now(UTC) - self.lookback_window

        stmt = (
            select(LoginAttempt)
            .where(
                LoginAttempt.email == email.strip().lower(),
                LoginAttempt.successful.is_(False),
                LoginAttempt.created_at >= since,
            )
        )

        if tenant_id is not None:
            stmt = stmt.where(
                LoginAttempt.tenant_id == tenant_id,
            )

        attempts = list(db.session.scalars(stmt))

        count = len(attempts)

        for attempt in attempts:
            db.session.delete(attempt)

        db.session.commit()

        return count

    def purge_old_attempts(
        self,
        *,
        retention_period: timedelta = timedelta(days=90),
    ) -> int:
        """
        Permanently delete historical login attempts older than the
        configured retention period.

        Intended to be executed by a scheduled maintenance task.

        Returns
        -------
        int
            Number of deleted records.
        """

        cutoff = datetime.now(UTC) - retention_period

        stmt = (
            select(LoginAttempt)
            .where(
                LoginAttempt.created_at < cutoff,
            )
        )

        attempts = list(db.session.scalars(stmt))

        count = len(attempts)

        for attempt in attempts:
            db.session.delete(attempt)

        db.session.commit()

        return count

    def statistics(
        self,
        *,
        tenant_id: str | None = None,
        lookback: timedelta = timedelta(days=1),
    ) -> dict[str, int]:
        """
        Return authentication statistics.

        Returns
        -------
        dict
            Example::

                {
                    "total": 150,
                    "successes": 142,
                    "failures": 8,
                }
        """

        since = datetime.now(UTC) - lookback

        filters = [
            LoginAttempt.created_at >= since,
        ]

        if tenant_id is not None:
            filters.append(
                LoginAttempt.tenant_id == tenant_id,
            )

        total = db.session.scalar(
            select(func.count())
            .select_from(LoginAttempt)
            .where(and_(*filters))
        ) or 0

        successes = db.session.scalar(
            select(func.count())
            .select_from(LoginAttempt)
            .where(
                and_(
                    *filters,
                    LoginAttempt.successful.is_(True),
                )
            )
        ) or 0

        failures = db.session.scalar(
            select(func.count())
            .select_from(LoginAttempt)
            .where(
                and_(
                    *filters,
                    LoginAttempt.successful.is_(False),
                )
            )
        ) or 0

        return {
            "total": int(total),
            "successes": int(successes),
            "failures": int(failures),
        }        
    
# ============================================================================
# Singleton
# ============================================================================

login_attempt_service = LoginAttemptService()


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    "LoginAttemptService",
    "login_attempt_service",
]    