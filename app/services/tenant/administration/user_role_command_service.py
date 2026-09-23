"""
Hela360 Tenant Administration User Role Command Service
=======================================================

Write-side application service for tenant-scoped staff role assignments.

Security boundaries
-------------------
- Operates only on tenant User and Role records.
- Never operates on Hela360 Office PlatformUser / PlatformRole records.
- Actor, target user and requested roles must resolve inside the same tenant.
- Cross-tenant resources are treated as not found.
- Non-owner administrators cannot change a tenant owner's roles.
- Non-owner administrators cannot grant built-in/system roles.
- Role assignment provenance is preserved.
- Role additions/removals are audit logged in the same transaction.
- Transaction commit/rollback remains with the caller.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from app.models.auth import Role, User, UserRole
from app.services.common.audit_actions import AuditAction
from app.services.common.audit_modules import AuditModule
from app.services.common.audit_service import AuditService
from app.services.tenant.auth.authorization_service import (
    AuthorizationService,
)


class TenantAdministrationRoleAssignmentError(Exception):
    """Raised when a tenant role-assignment command is invalid or unsafe."""


@dataclass(frozen=True, slots=True)
class TenantAdministrationRoleAssignmentResult:
    """Result of replacing one tenant user's assigned role set."""

    target_user_id: str
    role_ids: tuple[str, ...]
    added_role_ids: tuple[str, ...]
    removed_role_ids: tuple[str, ...]

    @property
    def changed(self) -> bool:
        return bool(
            self.added_role_ids
            or self.removed_role_ids
        )


class TenantAdministrationUserRoleCommandService:
    """
    Tenant-scoped role-assignment command boundary.

    The caller supplies tenant scope from authenticated identity.
    This service flushes mutations but never commits or rolls back.
    """

    def __init__(self, session) -> None:
        self.session = session
        self.audit = AuditService()
        self.authorization = AuthorizationService()

    def replace_roles(
        self,
        *,
        tenant_id: str,
        actor_user_id: str,
        target_user_id: str,
        role_ids: list[str] | tuple[str, ...],
        reason: str | None = None,
    ) -> TenantAdministrationRoleAssignmentResult:
        tenant_id = str(tenant_id).strip()
        actor_user_id = str(actor_user_id).strip()
        target_user_id = str(target_user_id).strip()

        if not tenant_id:
            raise TenantAdministrationRoleAssignmentError(
                "Tenant is required."
            )

        if not actor_user_id:
            raise TenantAdministrationRoleAssignmentError(
                "Actor user is required."
            )

        if not target_user_id:
            raise TenantAdministrationRoleAssignmentError(
                "Target user is required."
            )

        normalized_reason = (
            str(reason).strip()
            if reason is not None
            else None
        )

        requested_role_ids = tuple(
            sorted(
                {
                    str(role_id).strip()
                    for role_id in role_ids
                    if str(role_id).strip()
                }
            )
        )

        actor = self._resolve_user(
            tenant_id=tenant_id,
            user_id=actor_user_id,
            label="Actor",
        )

        target = self._resolve_user(
            tenant_id=tenant_id,
            user_id=target_user_id,
            label="User",
        )

        if (
            bool(target.is_owner)
            and not bool(actor.is_owner)
        ):
            raise TenantAdministrationRoleAssignmentError(
                "Only the tenant owner may change "
                "the tenant owner's roles."
            )

        requested_roles = self._resolve_roles(
            tenant_id=tenant_id,
            role_ids=requested_role_ids,
        )

        existing_assignments = self._current_assignments(
            target_user_id=target_user_id,
        )

        existing_by_role_id = {
            str(assignment.role_id): assignment
            for assignment in existing_assignments
        }

        existing_role_ids = set(existing_by_role_id)
        desired_role_ids = set(requested_role_ids)

        added_role_ids = tuple(
            sorted(
                desired_role_ids
                - existing_role_ids
            )
        )

        removed_role_ids = tuple(
            sorted(
                existing_role_ids
                - desired_role_ids
            )
        )

        requested_by_id = {
            str(role.id): role
            for role in requested_roles
        }

        if not bool(actor.is_owner):
            system_role_additions = [
                requested_by_id[role_id]
                for role_id in added_role_ids
                if requested_by_id[role_id].is_system
            ]

            if system_role_additions:
                raise TenantAdministrationRoleAssignmentError(
                    "Only the tenant owner may assign "
                    "a system role."
                )

            removed_system_roles = self._resolve_existing_system_roles(
                tenant_id=tenant_id,
                role_ids=removed_role_ids,
            )

            if removed_system_roles:
                raise TenantAdministrationRoleAssignmentError(
                    "Only the tenant owner may remove "
                    "a system role."
                )

        if not added_role_ids and not removed_role_ids:
            return TenantAdministrationRoleAssignmentResult(
                target_user_id=target_user_id,
                role_ids=tuple(
                    sorted(existing_role_ids)
                ),
                added_role_ids=(),
                removed_role_ids=(),
            )

        removed_role_metadata = self._role_metadata(
            tenant_id=tenant_id,
            role_ids=removed_role_ids,
        )

        for role_id in removed_role_ids:
            assignment = existing_by_role_id[role_id]
            self.session.delete(assignment)

        # Flush removals first so the unit of work cleanly reflects the
        # replacement before new assignments are added.
        self.session.flush()

        for role_id in added_role_ids:
            self.session.add(
                UserRole(
                    user_id=target_user_id,
                    role_id=role_id,
                    assigned_by_user_id=actor_user_id,
                    assignment_reason=normalized_reason,
                )
            )

        self.session.flush()

        for role_id in removed_role_ids:
            metadata = removed_role_metadata[role_id]

            self.audit.log(
                module=AuditModule.AUTH,
                action=AuditAction.ROLE_REMOVED,
                entity_type="user",
                tenant_id=tenant_id,
                entity_id=target_user_id,
                user_id=actor_user_id,
                old_values={
                    "role_id": role_id,
                    "role_code": metadata["code"],
                    "role_name": metadata["name"],
                },
                new_values=None,
                details={
                    "target_user_id": target_user_id,
                    "role_id": role_id,
                    "role_code": metadata["code"],
                    "role_name": metadata["name"],
                },
                reason=normalized_reason,
                commit=False,
            )

        for role_id in added_role_ids:
            role = requested_by_id[role_id]

            self.audit.log(
                module=AuditModule.AUTH,
                action=AuditAction.ROLE_ASSIGNED,
                entity_type="user",
                tenant_id=tenant_id,
                entity_id=target_user_id,
                user_id=actor_user_id,
                old_values=None,
                new_values={
                    "role_id": role_id,
                    "role_code": role.code,
                    "role_name": role.name,
                },
                details={
                    "target_user_id": target_user_id,
                    "role_id": role_id,
                    "role_code": role.code,
                    "role_name": role.name,
                    "is_system": bool(role.is_system),
                },
                reason=normalized_reason,
                commit=False,
            )

        self.session.flush()

        # Role membership has changed. Rebuild the target user's
        # authorization snapshot so subsequent permission checks observe
        # the new role set immediately rather than a cached context.
        self.authorization.refresh_context(
            target_user_id,
            tenant_id=tenant_id,
        )

        return TenantAdministrationRoleAssignmentResult(
            target_user_id=target_user_id,
            role_ids=requested_role_ids,
            added_role_ids=added_role_ids,
            removed_role_ids=removed_role_ids,
        )

    def _resolve_user(
        self,
        *,
        tenant_id: str,
        user_id: str,
        label: str,
    ) -> User:
        stmt = (
            select(User)
            .where(
                User.id == str(user_id),
                User.tenant_id == str(tenant_id),
            )
        )

        user = self.session.execute(
            stmt
        ).scalar_one_or_none()

        if user is None:
            raise TenantAdministrationRoleAssignmentError(
                f"{label} not found."
            )

        return user

    def _resolve_roles(
        self,
        *,
        tenant_id: str,
        role_ids: tuple[str, ...],
    ) -> tuple[Role, ...]:
        if not role_ids:
            return ()

        stmt = (
            select(Role)
            .where(
                Role.tenant_id == str(tenant_id),
                Role.id.in_(role_ids),
            )
            .order_by(Role.id.asc())
        )

        roles = tuple(
            self.session.scalars(stmt).all()
        )

        resolved_ids = {
            str(role.id)
            for role in roles
        }

        missing_ids = sorted(
            set(role_ids) - resolved_ids
        )

        if missing_ids:
            raise TenantAdministrationRoleAssignmentError(
                "Role not found."
            )

        return roles

    def _current_assignments(
        self,
        *,
        target_user_id: str,
    ) -> tuple[UserRole, ...]:
        stmt = (
            select(UserRole)
            .where(
                UserRole.user_id
                == str(target_user_id),
            )
            .order_by(
                UserRole.role_id.asc(),
            )
        )

        return tuple(
            self.session.scalars(stmt).all()
        )

    def _resolve_existing_system_roles(
        self,
        *,
        tenant_id: str,
        role_ids: tuple[str, ...],
    ) -> tuple[Role, ...]:
        if not role_ids:
            return ()

        stmt = (
            select(Role)
            .where(
                Role.tenant_id == str(tenant_id),
                Role.id.in_(role_ids),
                Role.is_system.is_(True),
            )
            .order_by(Role.id.asc())
        )

        return tuple(
            self.session.scalars(stmt).all()
        )

    def _role_metadata(
        self,
        *,
        tenant_id: str,
        role_ids: tuple[str, ...],
    ) -> dict[str, dict[str, str]]:
        if not role_ids:
            return {}

        stmt = (
            select(
                Role.id,
                Role.code,
                Role.name,
            )
            .where(
                Role.tenant_id == str(tenant_id),
                Role.id.in_(role_ids),
            )
        )

        rows = self.session.execute(stmt).all()

        return {
            str(row.id): {
                "code": row.code,
                "name": row.name,
            }
            for row in rows
        }
