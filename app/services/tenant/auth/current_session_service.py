"""
Current authenticated session service.

Builds the backend session contract consumed by future frontend identity and
tenant-scope hydration. The route remains thin; this service owns lookup,
status validation, deterministic serialization, and scope-safe branch output.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Iterable

from sqlalchemy import select

from app.auth.exceptions import (
    AuthenticationError,
    BranchAccessDeniedError,
    InvalidAccessTokenError,
    SessionNotFoundError,
    TenantAccessDeniedError,
)
from app.auth.jwt import Identity, JWTTokenType
from app.auth.schemas import (
    CurrentSessionBranchResponse,
    CurrentSessionResponse,
    CurrentSessionRoleResponse,
    CurrentSessionTenantResponse,
    CurrentSessionUserResponse,
)
from app.extensions import db
from app.models.auth import User
from app.models.security import UserSession
from app.models.tenant import Branch, Tenant
from app.services.tenant.auth.authorization_service import (
    AuthorizationService,
    authorization_service,
)


class CurrentSessionService:
    """
    Resolve and serialize the current authenticated session.
    """

    def __init__(
        self,
        *,
        authorizer: AuthorizationService = authorization_service,
    ) -> None:
        self.authorizer = authorizer

    def get_current_session(
        self,
        identity: Identity,
    ) -> CurrentSessionResponse:
        """
        Return the current authenticated session response.
        """

        self._require_access_identity(identity)

        session = self._get_active_session(identity.session_id)

        if session is None:
            raise SessionNotFoundError(
                "Authenticated session is no longer active."
            )

        self._validate_session_scope(
            session=session,
            identity=identity,
        )

        user = self.authorizer.authorize(
            identity.user_id,
            tenant_id=identity.tenant_id,
            branch_id=identity.branch_id,
        )

        tenant = self._get_active_tenant(identity.tenant_id)

        context = self.authorizer.refresh_context(
            user,
            tenant_id=identity.tenant_id,
        )

        branches = self._get_accessible_branches(
            tenant_id=identity.tenant_id,
            branch_ids=context.branch_ids,
        )

        self._validate_identity_branch(
            identity=identity,
            branches=branches,
        )

        return CurrentSessionResponse(
            user=self._serialize_user(user),
            tenant=self._serialize_tenant(tenant),
            roles=self._serialize_roles(user),
            permissions=sorted(context.permissions),
            branches=[
                self._serialize_branch(branch)
                for branch in branches
            ],
            default_branch_id=None,
        )

    def _require_access_identity(
        self,
        identity: Identity,
    ) -> None:
        if identity.token_type != JWTTokenType.ACCESS:
            raise InvalidAccessTokenError(
                "Current session requires an access token."
            )

    def _get_active_session(
        self,
        session_id: str,
    ) -> UserSession | None:
        session = db.session.get(
            UserSession,
            session_id,
        )

        if session is None:
            return None

        if not self._is_session_active(session):
            return None

        return session

    def _is_session_active(
        self,
        session: UserSession,
    ) -> bool:
        active = getattr(session, "is_active", None)

        if isinstance(active, bool):
            return active

        if getattr(session, "revoked_at", None) is not None:
            return False

        expires_at = getattr(session, "expires_at", None)

        if expires_at is None:
            return False

        return expires_at > datetime.now(UTC)

    def _validate_session_scope(
        self,
        *,
        session: UserSession,
        identity: Identity,
    ) -> None:
        if str(session.user_id) != identity.user_id:
            raise AuthenticationError(
                "Authenticated session user does not match token identity."
            )

        if str(session.tenant_id) != identity.tenant_id:
            raise AuthenticationError(
                "Authenticated session tenant does not match token identity."
            )

    def _get_active_tenant(
        self,
        tenant_id: str,
    ) -> Tenant:
        tenant = db.session.get(
            Tenant,
            tenant_id,
        )

        if tenant is None:
            raise TenantAccessDeniedError(
                "Authenticated tenant could not be resolved."
            )

        if str(getattr(tenant, "status", "")).lower() != "active":
            raise TenantAccessDeniedError(
                "Authenticated tenant is not active."
            )

        return tenant

    def _get_accessible_branches(
        self,
        *,
        tenant_id: str,
        branch_ids: Iterable[str],
    ) -> list[Branch]:
        branch_id_set = {
            str(branch_id)
            for branch_id in branch_ids
        }

        stmt = (
            select(Branch)
            .where(
                Branch.tenant_id == tenant_id,
                Branch.is_active.is_(True),
            )
            .order_by(
                Branch.code.asc(),
                Branch.name.asc(),
                Branch.id.asc(),
            )
        )

        if branch_id_set:
            stmt = stmt.where(
                Branch.id.in_(branch_id_set),
            )

        return list(db.session.scalars(stmt))

    def _validate_identity_branch(
        self,
        *,
        identity: Identity,
        branches: list[Branch],
    ) -> None:
        if identity.branch_id is None:
            return

        branch_ids = {
            str(branch.id)
            for branch in branches
        }

        if identity.branch_id not in branch_ids:
            raise BranchAccessDeniedError(
                "Authenticated branch is not available in the tenant scope."
            )

    def _serialize_user(
        self,
        user: User,
    ) -> CurrentSessionUserResponse:
        return CurrentSessionUserResponse(
            id=str(user.id),
            email=getattr(user, "email", None),
            username=getattr(user, "username", None),
            first_name=str(getattr(user, "first_name", "")),
            last_name=getattr(user, "last_name", None),
            is_active=bool(getattr(user, "is_active", False)),
            is_locked=bool(getattr(user, "is_locked", False)),
            is_owner=bool(getattr(user, "is_owner", False)),
        )

    def _serialize_tenant(
        self,
        tenant: Tenant,
    ) -> CurrentSessionTenantResponse:
        status = str(getattr(tenant, "status", ""))

        return CurrentSessionTenantResponse(
            id=str(tenant.id),
            name=str(tenant.display_name),
            status=status,
            is_active=status.lower() == "active",
        )

    def _serialize_roles(
        self,
        user: User,
    ) -> list[CurrentSessionRoleResponse]:
        roles = sorted(
            getattr(user, "roles", ()),
            key=lambda role: (
                str(getattr(role, "code", "")),
                str(getattr(role, "name", "")),
                str(getattr(role, "id", "")),
            ),
        )

        return [
            CurrentSessionRoleResponse(
                id=str(role.id),
                name=str(role.name),
                code=str(role.code),
            )
            for role in roles
        ]

    def _serialize_branch(
        self,
        branch: Branch,
    ) -> CurrentSessionBranchResponse:
        return CurrentSessionBranchResponse(
            id=str(branch.id),
            tenant_id=str(branch.tenant_id),
            name=str(branch.name),
            code=str(branch.code),
            is_active=bool(branch.is_active),
        )


current_session_service = CurrentSessionService()


__all__ = [
    "CurrentSessionService",
    "current_session_service",
]
