"""
Tenant-Aware Service

Provides common helpers for services that operate within the context
of a tenant, branch and authenticated user.

This service builds upon BaseService by adding utilities for
multi-tenant data isolation.

It intentionally contains no business logic.

Responsibilities
----------------
- Current authenticated identity
- Current tenant
- Current branch
- Current user
- Tenant-aware query helpers
- Ownership validation

Hela360 Enterprise Pharmacy POS & ERP
"""

from __future__ import annotations

from flask import g
from sqlalchemy.orm import Query

from app.auth.exceptions import (
    AuthenticationError,
    TenantAccessDeniedError,
)
from app.auth.jwt import get_current_identity
from app.auth.services.base import BaseService


class TenantService(BaseService):
    """
    Base class for tenant-aware services.
    """

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    def identity(self):
        """
        Return the authenticated identity.

        Raises
        ------
        AuthenticationError
            If the request is unauthenticated.
        """

        identity = getattr(g, "identity", None)

        if identity is None:
            identity = get_current_identity()

        if identity is None:
            raise AuthenticationError()

        return identity

    # ------------------------------------------------------------------
    # Current Context
    # ------------------------------------------------------------------

    @property
    def current_user_id(self) -> str:
        """
        Current authenticated user.
        """

        return self.identity().user_id

    @property
    def current_tenant_id(self) -> str:
        """
        Current tenant.
        """

        return self.identity().tenant_id

    @property
    def current_branch_id(self) -> str | None:
        """
        Current branch.
        """

        return self.identity().branch_id

    @property
    def current_role(self) -> str | None:
        """
        Current primary role.
        """

        return self.identity().role

    @property
    def current_permissions(self) -> list[str]:
        """
        Current permission list.
        """

        return self.identity().permissions

    # ------------------------------------------------------------------
    # Query Helpers
    # ------------------------------------------------------------------

    def tenant_query(
        self,
        model,
    ) -> Query:
        """
        Return a tenant-scoped query.

        Model must contain a tenant_id column.
        """

        return model.query.filter_by(
            tenant_id=self.current_tenant_id,
        )

    def branch_query(
        self,
        model,
    ) -> Query:
        """
        Return a branch-scoped query.

        Model must contain tenant_id and branch_id columns.
        """

        return (
            model.query
            .filter_by(
                tenant_id=self.current_tenant_id,
            )
            .filter_by(
                branch_id=self.current_branch_id,
            )
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def require_same_tenant(
        self,
        tenant_id: str,
    ) -> None:
        """
        Ensure the supplied tenant belongs to the current identity.
        """

        if tenant_id != self.current_tenant_id:
            raise TenantAccessDeniedError()

    def owns(
        self,
        model,
    ) -> bool:
        """
        Return True if an ORM object belongs to the current tenant.
        """

        return getattr(
            model,
            "tenant_id",
            None,
        ) == self.current_tenant_id

    def require_ownership(
        self,
        model,
    ) -> None:
        """
        Ensure an ORM object belongs to the authenticated tenant.
        """

        if not self.owns(model):
            raise TenantAccessDeniedError()

    # ------------------------------------------------------------------
    # Convenience Helpers
    # ------------------------------------------------------------------

    def tenant_filter(
        self,
        **kwargs,
    ) -> dict:
        """
        Return a filter dictionary automatically including tenant_id.

        Example
        -------
        Product.query.filter_by(**self.tenant_filter(active=True))
        """

        return {
            "tenant_id": self.current_tenant_id,
            **kwargs,
        }

    def branch_filter(
        self,
        **kwargs,
    ) -> dict:
        """
        Return a filter dictionary including tenant_id and branch_id.
        """

        return {
            "tenant_id": self.current_tenant_id,
            "branch_id": self.current_branch_id,
            **kwargs,
        }


__all__ = [
    "TenantService",
]