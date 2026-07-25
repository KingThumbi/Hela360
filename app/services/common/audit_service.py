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
        tenant_id: str,
        entity_id: str | None = None,
        user_id: str | None = None,
        branch_id: str | None = None,
        old_values: dict[str, Any] | None = None,
        new_values: dict[str, Any] | None = None,
        reason: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        commit: bool = True,
    ) -> AuditLog:
        """
        Persist an audit record.
        """

        audit = AuditLog(
            tenant_id=tenant_id,
            branch_id=branch_id,
            user_id=user_id,
            module_code=module.value,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action.value,
            old_values=old_values,
            new_values=new_values,
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        db.session.add(audit)

        if commit:
            db.session.commit()

        return audit

    def safe_log(self, **kwargs: Any) -> None:
        """
        Best-effort audit logging.

        Audit failures should never interrupt the primary business
        transaction.
        """

        try:
            self.log(**kwargs)

        except SQLAlchemyError:
            db.session.rollback()

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
        tenant_id: str,
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
        tenant_id: str,
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