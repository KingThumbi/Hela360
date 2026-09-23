"""
Hela360 Tenant Administration User Permission Command Service
==============================================================

Write-side application service for tenant-scoped direct user permission
overrides.

Security boundaries
-------------------
- Operates only on tenant User and canonical tenant Permission records.
- Never operates on Hela360 Office PlatformUser / PlatformPermission records.
- Actor and target user must resolve inside the authenticated tenant.
- Cross-tenant target users are treated as not found.
- Non-owner administrators cannot change a tenant owner's permissions.
- Non-owner administrators may only alter permissions they themselves
  effectively possess.
- Tenant owners may manage any canonical tenant permission.
- Direct overrides support allow, deny, or inherit.
- Inherit is represented by absence of a UserPermission row.
- Assignment provenance is preserved.
- Permission changes are audit logged in the same transaction.
- Transaction commit/rollback remains with the caller.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from app.auth.permissions import is_valid_permission
from app.models.auth import (
    Permission,
    User,
    UserPermission,
)
from app.services.common.audit_actions import AuditAction
from app.services.common.audit_modules import AuditModule
from app.services.common.audit_service import AuditService
from app.services.tenant.auth.authorization_service import (
    AuthorizationService,
)


class TenantAdministrationPermissionAssignmentError(
    Exception
):
    """Raised when a direct user-permission command is invalid or unsafe."""


@dataclass(frozen=True, slots=True)
class TenantAdministrationPermissionAssignmentResult:
    """Result of changing one direct user permission override."""

    target_user_id: str
    permission_id: str
    permission_code: str
    previous_effect: str | None
    effect: str | None

    @property
    def changed(self) -> bool:
        return self.previous_effect != self.effect


class TenantAdministrationUserPermissionCommandService:
    """
    Tenant-scoped direct permission-override command boundary.

    ``effect`` accepts:

    - ``allow``   -> persist a direct allow
    - ``deny``    -> persist a direct deny
    - ``inherit`` -> remove any direct override

    The caller supplies tenant scope from authenticated identity.
    This service flushes mutations but never commits or rolls back.
    """

    VALID_EFFECTS = frozenset(
        {
            "allow",
            "deny",
            "inherit",
        }
    )

    def __init__(self, session) -> None:
        self.session = session
        self.audit = AuditService()
        self.authorization = AuthorizationService()

    def set_override(
        self,
        *,
        tenant_id: str,
        actor_user_id: str,
        target_user_id: str,
        permission_code: str,
        effect: str,
        reason: str | None = None,
    ) -> TenantAdministrationPermissionAssignmentResult:
        tenant_id = str(tenant_id).strip()
        actor_user_id = str(actor_user_id).strip()
        target_user_id = str(target_user_id).strip()
        permission_code = str(
            permission_code
        ).strip()
        effect = str(effect).strip().lower()

        if not tenant_id:
            raise TenantAdministrationPermissionAssignmentError(
                "Tenant is required."
            )

        if not actor_user_id:
            raise TenantAdministrationPermissionAssignmentError(
                "Actor user is required."
            )

        if not target_user_id:
            raise TenantAdministrationPermissionAssignmentError(
                "Target user is required."
            )

        if not permission_code:
            raise TenantAdministrationPermissionAssignmentError(
                "Permission code is required."
            )

        if effect not in self.VALID_EFFECTS:
            raise TenantAdministrationPermissionAssignmentError(
                "Effect must be allow, deny, or inherit."
            )

        if not is_valid_permission(permission_code):
            raise TenantAdministrationPermissionAssignmentError(
                "Permission is not part of the canonical "
                "tenant permission catalogue."
            )

        normalized_reason = (
            str(reason).strip()
            if reason is not None
            else None
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
            raise TenantAdministrationPermissionAssignmentError(
                "Only the tenant owner may change "
                "the tenant owner's permissions."
            )

        permission = self._resolve_permission(
            permission_code=permission_code,
        )

        # Prevent privilege escalation through delegated administration.
        #
        # The tenant owner is the explicit override. Everyone else may
        # alter only capabilities that they themselves currently possess.
        if (
            not bool(actor.is_owner)
            and not self.authorization.has_permission(
                actor,
                permission_code,
                tenant_id=tenant_id,
            )
        ):
            raise TenantAdministrationPermissionAssignmentError(
                "A non-owner administrator may only change "
                "permissions they themselves possess."
            )

        existing = self._current_override(
            target_user_id=target_user_id,
            permission_id=str(permission.id),
        )

        previous_effect = (
            str(existing.effect)
            if existing is not None
            else None
        )

        desired_effect = (
            None
            if effect == "inherit"
            else effect
        )

        if previous_effect == desired_effect:
            return (
                TenantAdministrationPermissionAssignmentResult(
                    target_user_id=target_user_id,
                    permission_id=str(permission.id),
                    permission_code=permission_code,
                    previous_effect=previous_effect,
                    effect=desired_effect,
                )
            )

        if desired_effect is None:
            if existing is not None:
                self.session.delete(existing)

        elif existing is None:
            self.session.add(
                UserPermission(
                    user_id=target_user_id,
                    permission_id=str(permission.id),
                    effect=desired_effect,
                    assigned_by_user_id=actor_user_id,
                    assignment_reason=normalized_reason,
                )
            )

        else:
            existing.effect = desired_effect
            existing.assigned_by_user_id = (
                actor_user_id
            )
            existing.assignment_reason = (
                normalized_reason
            )

        self.session.flush()

        action = self._audit_action(
            previous_effect=previous_effect,
            desired_effect=desired_effect,
        )

        self.audit.log(
            module=AuditModule.AUTH,
            action=action,
            entity_type="user",
            tenant_id=tenant_id,
            entity_id=target_user_id,
            user_id=actor_user_id,
            old_values=(
                {
                    "permission_id": str(
                        permission.id
                    ),
                    "permission_code": permission.code,
                    "effect": previous_effect,
                }
                if previous_effect is not None
                else None
            ),
            new_values=(
                {
                    "permission_id": str(
                        permission.id
                    ),
                    "permission_code": permission.code,
                    "effect": desired_effect,
                }
                if desired_effect is not None
                else None
            ),
            details={
                "target_user_id": target_user_id,
                "permission_id": str(
                    permission.id
                ),
                "permission_code": permission.code,
                "permission_name": permission.name,
                "previous_effect": previous_effect,
                "effect": desired_effect,
            },
            reason=normalized_reason,
            commit=False,
        )

        self.session.flush()

        # Permission state has changed. Rebuild the target user's
        # authorization snapshot so subsequent checks observe it.
        self.authorization.refresh_context(
            target_user_id,
            tenant_id=tenant_id,
        )

        return (
            TenantAdministrationPermissionAssignmentResult(
                target_user_id=target_user_id,
                permission_id=str(permission.id),
                permission_code=permission_code,
                previous_effect=previous_effect,
                effect=desired_effect,
            )
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
            raise TenantAdministrationPermissionAssignmentError(
                f"{label} not found."
            )

        return user

    def _resolve_permission(
        self,
        *,
        permission_code: str,
    ) -> Permission:
        stmt = (
            select(Permission)
            .where(
                Permission.code
                == str(permission_code),
            )
        )

        permission = self.session.execute(
            stmt
        ).scalar_one_or_none()

        if permission is None:
            raise TenantAdministrationPermissionAssignmentError(
                "Canonical permission is not synchronized "
                "to persistence."
            )

        return permission

    def _current_override(
        self,
        *,
        target_user_id: str,
        permission_id: str,
    ) -> UserPermission | None:
        stmt = (
            select(UserPermission)
            .where(
                UserPermission.user_id
                == str(target_user_id),
                UserPermission.permission_id
                == str(permission_id),
            )
        )

        return self.session.execute(
            stmt
        ).scalar_one_or_none()

    @staticmethod
    def _audit_action(
        *,
        previous_effect: str | None,
        desired_effect: str | None,
    ) -> AuditAction:
        # Moving toward an explicit allow is a grant.
        if desired_effect == "allow":
            return AuditAction.PERMISSION_GRANTED

        # Moving toward an explicit deny is a revocation.
        if desired_effect == "deny":
            return AuditAction.PERMISSION_REVOKED

        # Returning to inherit removes the previous direct override.
        if previous_effect == "deny":
            return AuditAction.PERMISSION_GRANTED

        return AuditAction.PERMISSION_REVOKED
