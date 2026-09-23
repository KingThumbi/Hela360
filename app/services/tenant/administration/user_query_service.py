"""
Hela360 Tenant Administration User Query Service
=================================================

Read-side application service for tenant-scoped user and role administration.

Architectural boundaries
------------------------
- Operates only on tenant User / Role / Permission records.
- Never operates on Hela360 Office PlatformUser / PlatformRole records.
- Every user and role lookup is restricted to the authenticated tenant.
- Cross-tenant resources are treated as not found.
- Effective permissions are resolved by the canonical tenant
  AuthorizationService rather than reimplementing RBAC rules here.
- This service performs no commits or rollbacks.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import noload, selectinload

from app.auth.exceptions import UserNotFoundError
from app.models.auth import (
    Permission,
    Role,
    User,
    UserPermission,
    UserRole,
)
from app.services.tenant.auth.authorization_service import (
    AuthorizationService,
)


class TenantAdministrationUserQueryService:
    """
    Tenant-scoped administrative user queries.

    The caller supplies the authenticated tenant identifier. Tenant scope is
    never accepted from target-resource data.
    """

    def __init__(self, session) -> None:
        self.session = session
        self.authorization = AuthorizationService()

    def list_users(
        self,
        *,
        tenant_id: str,
    ) -> tuple[dict, ...]:
        stmt = (
            select(
                User.id,
                User.tenant_id,
                User.branch_id,
                User.first_name,
                User.last_name,
                User.email,
                User.phone,
                User.username,
                User.is_owner,
                User.is_active,
                User.created_at,
                User.updated_at,
            )
            .where(
                User.tenant_id == str(tenant_id),
            )
            .order_by(
                User.first_name.asc(),
                User.last_name.asc(),
                User.username.asc(),
                User.id.asc(),
            )
        )

        rows = self.session.execute(stmt).all()

        return tuple(
            self._serialize_user_row(row)
            for row in rows
        )

    def get_user(
        self,
        *,
        tenant_id: str,
        user_id: str,
    ) -> dict:
        stmt = (
            select(
                User.id,
                User.tenant_id,
                User.branch_id,
                User.first_name,
                User.last_name,
                User.email,
                User.phone,
                User.username,
                User.is_owner,
                User.is_active,
                User.created_at,
                User.updated_at,
            )
            .where(
                User.id == str(user_id),
                User.tenant_id == str(tenant_id),
            )
        )

        row = self.session.execute(stmt).one_or_none()

        if row is None:
            raise UserNotFoundError(
                "User could not be resolved."
            )

        return self._serialize_user_row(row)

    def list_user_roles(
        self,
        *,
        tenant_id: str,
        user_id: str,
    ) -> tuple[dict, ...]:
        self._require_user_exists(
            tenant_id=tenant_id,
            user_id=user_id,
        )

        stmt = (
            select(
                Role.id,
                Role.code,
                Role.name,
                Role.description,
                Role.is_system,
            )
            .join(
                UserRole,
                UserRole.role_id == Role.id,
            )
            .where(
                UserRole.user_id == str(user_id),
                Role.tenant_id == str(tenant_id),
            )
            .order_by(
                Role.name.asc(),
                Role.code.asc(),
                Role.id.asc(),
            )
        )

        rows = self.session.execute(stmt).all()

        return tuple(
            self._serialize_user_role_row(row)
            for row in rows
        )

    def list_roles(
        self,
        *,
        tenant_id: str,
    ) -> tuple[dict, ...]:
        stmt = (
            select(
                Role.id,
                Role.code,
                Role.name,
                Role.description,
                Role.is_system,
            )
            .where(
                Role.tenant_id == str(tenant_id),
            )
            .order_by(
                Role.is_system.desc(),
                Role.name.asc(),
                Role.code.asc(),
                Role.id.asc(),
            )
        )

        rows = self.session.execute(stmt).all()

        return tuple(
            self._serialize_role_row(row)
            for row in rows
        )

    def effective_permissions(
        self,
        *,
        tenant_id: str,
        user_id: str,
    ) -> tuple[dict, ...]:
        user = self._load_user_for_permission_resolution(
            tenant_id=tenant_id,
            user_id=user_id,
        )

        permissions = (
            self.authorization.get_permission_objects(
                user,
                tenant_id=str(tenant_id),
            )
        )

        return tuple(
            self._serialize_permission(permission)
            for permission in permissions
        )

    def permission_management(
        self,
        *,
        tenant_id: str,
        user_id: str,
    ) -> tuple[dict, ...]:
        """
        Return the tenant permission catalogue annotated for one user.

        The result distinguishes:
        - direct role inheritance,
        - direct user allow/deny overrides,
        - final effective authorization,
        - compatibility-implied permissions.

        No authorization rules are reimplemented here. Final effective
        permission codes come from AuthorizationService.
        """
        user = self._load_user_for_permission_resolution(
            tenant_id=tenant_id,
            user_id=user_id,
        )

        effective_codes = set(
            self.authorization.get_permissions(
                user,
                tenant_id=str(tenant_id),
            )
        )

        role_permission_codes = {
            str(permission.code)
            for role in getattr(user, "roles", ())
            for permission in getattr(
                role,
                "permissions",
                (),
            )
            if getattr(permission, "code", None)
        }

        overrides = {
            str(override.permission.code): override
            for override in getattr(
                user,
                "permission_overrides",
                (),
            )
            if (
                getattr(override, "permission", None)
                is not None
                and getattr(
                    override.permission,
                    "code",
                    None,
                )
            )
        }

        catalogue = self.session.execute(
            select(
                Permission.id,
                Permission.code,
                Permission.name,
                Permission.module_code,
                Permission.description,
            ).order_by(
                Permission.module_code.asc(),
                Permission.code.asc(),
                Permission.id.asc(),
            )
        ).all()

        items: list[dict] = []

        for permission in catalogue:
            code = str(permission.code)
            override = overrides.get(code)

            override_effect = (
                str(override.effect)
                if override is not None
                else None
            )

            role_inherited = (
                code in role_permission_codes
            )
            effective = code in effective_codes

            if override_effect == "deny":
                source = "direct_deny"
            elif override_effect == "allow":
                source = "direct_allow"
            elif role_inherited:
                source = "role"
            elif effective:
                # Effective without a direct role row or direct override.
                # This currently covers compatibility implications such as
                # products.edit -> products.units.edit.
                source = "implied"
            else:
                source = "none"

            items.append(
                {
                    "id": str(permission.id),
                    "code": permission.code,
                    "name": permission.name,
                    "module": permission.module_code,
                    "description": permission.description,
                    "role_inherited": role_inherited,
                    "override_effect": override_effect,
                    "effective": effective,
                    "source": source,
                }
            )

        return tuple(items)

    def _require_user_exists(
        self,
        *,
        tenant_id: str,
        user_id: str,
    ) -> None:
        stmt = select(User.id).where(
            User.id == str(user_id),
            User.tenant_id == str(tenant_id),
        )

        if self.session.scalar(stmt) is None:
            raise UserNotFoundError(
                "User could not be resolved."
            )

    def _load_user_for_permission_resolution(
        self,
        *,
        tenant_id: str,
        user_id: str,
    ) -> User:
        """
        Load only the relationships needed for effective authorization.

        Security/session relationships are explicitly excluded because this
        query is an IAM inspection query, not a session-management query.
        """

        stmt = (
            select(User)
            .options(
                selectinload(User.roles)
                .selectinload(Role.permissions),
                selectinload(User.permission_overrides)
                .selectinload(UserPermission.permission),
                noload(User.sessions),
                noload(User.refresh_tokens),
                noload(User.password_reset_tokens),
            )
            .where(
                User.id == str(user_id),
                User.tenant_id == str(tenant_id),
            )
        )

        user = self.session.execute(
            stmt
        ).scalar_one_or_none()

        if user is None:
            raise UserNotFoundError(
                "User could not be resolved."
            )

        return user

    @staticmethod
    def _serialize_user_row(row) -> dict:
        first_name = row.first_name or ""
        last_name = row.last_name or ""

        full_name = " ".join(
            part
            for part in (
                first_name.strip(),
                last_name.strip(),
            )
            if part
        )

        return {
            "id": str(row.id),
            "tenant_id": str(row.tenant_id),
            "branch_id": (
                str(row.branch_id)
                if row.branch_id is not None
                else None
            ),
            "first_name": row.first_name,
            "last_name": row.last_name,
            "full_name": full_name,
            "email": row.email,
            "phone": row.phone,
            "username": row.username,
            "is_owner": bool(row.is_owner),
            "is_active": bool(row.is_active),
            "created_at": (
                row.created_at.isoformat()
                if row.created_at
                else None
            ),
            "updated_at": (
                row.updated_at.isoformat()
                if row.updated_at
                else None
            ),
        }

    @staticmethod
    def _serialize_user_role_row(row) -> dict:
        return {
            "id": str(row.id),
            "code": row.code,
            "name": row.name,
            "is_system": bool(row.is_system),
        }

    @staticmethod
    def _serialize_role_row(row) -> dict:
        return {
            "id": str(row.id),
            "code": row.code,
            "name": row.name,
            "description": row.description,
            "is_system": bool(row.is_system),
        }

    @staticmethod
    def _serialize_permission(
        permission: Permission,
    ) -> dict:
        return {
            "id": str(permission.id),
            "code": permission.code,
            "name": permission.name,
            "module": permission.module_code,
            "description": permission.description,
        }
