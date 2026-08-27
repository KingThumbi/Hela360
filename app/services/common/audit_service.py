"""
Audit Service

Cross-cutting audit logging service used throughout Hela360.

All modules should use this service to record audit events instead of
writing directly to the AuditLog model.

This service intentionally contains no business logic.

Hela360 Enterprise Pharmacy POS & ERP
"""

from __future__ import annotations

from typing import Any

from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models.audit import AuditLog
from app.services.common.audit_actions import AuditAction
from app.services.common.audit_modules import AuditModule


class AuditService:
    """
    Enterprise audit logging service.
    """

    def log(
        self,
        *,
        module: AuditModule,
        action: AuditAction,
        entity_type: str,
        tenant_id: str | None,
        entity_id: str | None = None,
        user_id: str | None = None,
        branch_id: str | None = None,
        session_id: str | None = None,
        status: str = "success",
        old_values: dict[str, Any] | None = None,
        new_values: dict[str, Any] | None = None,
        details: dict[str, Any] | None = None,
        reason: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        commit: bool = True,
    ) -> AuditLog:
        """
        Persist an audit record.

        Parameters
        ----------
        module
            Functional Hela360 module responsible for the event.

        action
            Machine-readable audit action.

        entity_type
            Domain entity affected by the event.

        tenant_id
            Tenant boundary within which the event occurred.

        entity_id
            Optional identifier of the affected entity.

        user_id
            Optional authenticated user responsible for the event.

        branch_id
            Optional branch context.

        session_id
            Optional authentication session associated with the event.

        status
            Outcome of the audited operation. Defaults to ``success``.

        old_values
            Optional state before the operation.

        new_values
            Optional state after the operation.

        details
            Additional structured event metadata.

        reason
            Optional human-readable reason for the event.

        ip_address
            Optional originating client IP address.

        user_agent
            Optional originating client user agent.

        commit
            Commit the audit record immediately when True.

        Returns
        -------
        AuditLog
            Persisted audit record.
        """

        audit = AuditLog(
            tenant_id=tenant_id,
            branch_id=branch_id,
            user_id=user_id,
            session_id=session_id,
            module_code=module.value,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action.value,
            status=status,
            old_values=old_values,
            new_values=new_values,
            details=details,
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        db.session.add(audit)

        if commit:
            db.session.commit()

        return audit
        
    def safe_log(
        self,
        **kwargs: Any,
    ) -> None:
        """
        Persist an audit event on a best-effort basis.

        Audit failures must never interrupt the primary business
        transaction.

        Any database transaction left in a failed state is rolled back
        before the exception is logged.
        """

        try:
            self.log(**kwargs)

        except Exception:
            try:
                db.session.rollback()
            except Exception:
                current_app.logger.exception(
                    "Failed to rollback session after audit failure."
                )

            current_app.logger.exception(
                "Failed to persist audit event."
            )
    # ==========================================================
    # Authorization Helpers
    # ==========================================================

    def _authorization_event(
        self,
        *,
        action: AuditAction,
        tenant_id: str | None,
        user_id: str,
        entity_type: str,
        entity_id: str | None = None,
        branch_id: str | None = None,
        reason: str | None = None,
    ) -> None:
        """
        Persist an authorization-related audit event.

        Authorization audit failures are logged on a best-effort basis and
        never interrupt the primary business transaction.
        """
        self.safe_log(
            module=AuditModule.AUTH,
            action=action,
            entity_type=entity_type,
            tenant_id=tenant_id,
            entity_id=entity_id,
            user_id=user_id,
            branch_id=branch_id,
            reason=reason,
        )

    def authorization_denied(
        self,
        *,
        tenant_id: str,
        user_id: str,
        entity_type: str,
        entity_id: str | None = None,
        branch_id: str | None = None,
        reason: str | None = None,
    ) -> None:
        """Record a denied authorization attempt."""
        self._authorization_event(
            action=AuditAction.AUTHORIZATION_DENIED,
            tenant_id=tenant_id,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            branch_id=branch_id,
            reason=reason,
        )

    def tenant_access_denied(
        self,
        *,
        tenant_id: str,
        user_id: str,
        entity_type: str,
        entity_id: str | None = None,
        branch_id: str | None = None,
        reason: str | None = None,
    ) -> None:
        """Record a denied cross-tenant access attempt."""
        self._authorization_event(
            action=AuditAction.TENANT_ACCESS_DENIED,
            tenant_id=tenant_id,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            branch_id=branch_id,
            reason=reason,
        )

    def branch_access_denied(
        self,
        *,
        tenant_id: str,
        user_id: str,
        entity_type: str,
        entity_id: str | None = None,
        branch_id: str | None = None,
        reason: str | None = None,
    ) -> None:
        """Record a denied branch access attempt."""
        self._authorization_event(
            action=AuditAction.BRANCH_ACCESS_DENIED,
            tenant_id=tenant_id,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            branch_id=branch_id,
            reason=reason,
        )

    def login_success(
        self,
        *,
        tenant_id: str,
        user_id: str,
        branch_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """
        Record a successful login.
        """

        self.safe_log(
            module=AuditModule.AUTH,
            action=AuditAction.LOGIN_SUCCESS,
            tenant_id=tenant_id,
            branch_id=branch_id,
            user_id=user_id,
            entity_type="User",
            entity_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def login_failure(
        self,
        *,
        tenant_id: str | None,
        email: str,
        ip_address: str | None = None,
        reason: str | None = None,
    ) -> None:
        """
        Record a failed login attempt.
        """

        self.safe_log(
            module=AuditModule.AUTH,
            action=AuditAction.LOGIN_FAILED,
            tenant_id=tenant_id,
            entity_type="Authentication",
            reason=reason,
            ip_address=ip_address,
            new_values={
                "email": email,
            },
        )

    def logout(
        self,
        *,
        tenant_id: str,
        user_id: str,
        branch_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """
        Record a logout event.
        """

        self.safe_log(
            module=AuditModule.AUTH,
            action=AuditAction.LOGOUT,
            tenant_id=tenant_id,
            branch_id=branch_id,
            user_id=user_id,
            entity_type="User",
            entity_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )


audit_service = AuditService()


__all__ = [
    "AuditService",
    "audit_service",
]