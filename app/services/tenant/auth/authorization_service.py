"""
app.services.tenant.auth.authorization_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Enterprise authorization service for Hela360.

This module provides the single source of truth for authorization decisions
throughout the application.

Authentication answers:

    "Who is the user?"

Authorization answers:

    "What is the user allowed to do?"

This service is intentionally stateless and focuses exclusively on
authorization. It does not perform authentication, session management,
password validation, or token processing.

Responsibilities
----------------
* User resolution
* Role resolution
* Effective permission aggregation
* Permission evaluation
* Tenant access validation
* Branch access validation
* Owner overrides
* Platform administrator extension points
* Authorization helper methods

Design Goals
------------
* Stateless
* Enterprise maintainable
* Deterministic permission resolution
* Future-compatible
* Easily testable
* No circular dependencies
* Single source of authorization logic

The AuthorizationService should be used by:

* API decorators
* Business services
* Controllers
* Background workers
* Scheduled tasks

Permission logic should not be duplicated elsewhere.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from flask import current_app
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.auth import (
    Permission,
    Role,
    RolePermission,
    User,
    UserRole,
)
from app.services.common.audit_service import AuditService

from app.auth.exceptions import (
    AccountArchivedError,
    AccountDisabledError,
    AccountInactiveError,
    AccountLockedError,
    AccountSuspendedError,
    AuthorizationError,
    BranchAccessDeniedError,
    InvalidCredentialsError,
    PermissionDeniedError,
    RoleRequiredError,
    TenantAccessDeniedError,
    UserNotFoundError,
)

__all__ = [
    "AuthorizationContext",
    "AuthorizationService",
    "authorization_service",
]

# ---------------------------------------------------------------------------
# Authorization constants
# ---------------------------------------------------------------------------

#: Reserved permission used internally to represent unrestricted access.
SYSTEM_PERMISSION = "*"

#: Reserved platform administrator role name.
PLATFORM_ADMIN_ROLE = "platform_admin"

#: Reserved tenant owner role name.
OWNER_ROLE = "owner"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass(slots=True, frozen=True)
class AuthorizationContext:
    """
    Immutable authorization snapshot for a user.

    This object represents the fully resolved authorization state of a user
    at a particular point in time.

    It intentionally contains only authorization-related information,
    allowing permission checks to avoid repeated database traversal once
    constructed.

    Future enhancements may cache instances of this object for the lifetime
    of a request or via a distributed cache.
    """

    user: User

    tenant_id: int | str | None = None

    roles: frozenset[str] = field(default_factory=frozenset)

    permissions: frozenset[str] = field(default_factory=frozenset)

    branch_ids: frozenset[str] = field(default_factory=frozenset)

# ---------------------------------------------------------------------------
# Authorization service
# ---------------------------------------------------------------------------

class AuthorizationService:
    """
    Enterprise authorization engine.

    This service is the single source of truth for authorization decisions
    within Hela360. It is responsible only for authorization concerns and is
    intentionally independent of authentication, session management, and JWT
    processing.

    Responsibilities
    ----------------
    * Resolve users, roles and permissions
    * Aggregate effective permissions
    * Evaluate authorization decisions
    * Enforce tenant and branch isolation
    * Support owner and platform administrator overrides
    * Provide authorization helpers for decorators and services

    Notes
    -----
    The service should behave as stateless from the perspective of callers.
    Any internal caching is an implementation detail and may later be replaced
    by request-scoped or distributed caching without changing the public API.
    """

    #: Shared audit service.
    audit_service = AuditService()

    #: Internal authorization context cache.
    #:
    #: Key format:
    #:     (tenant_id, user_id)
    #:
    #: The current implementation uses an in-memory cache as an optimization.
    #: Future implementations may replace this with Flask ``g``, Redis or
    #: another request-scoped caching mechanism.
    _authorization_context_cache: dict[tuple[int | str | None, int | str], AuthorizationContext]

    def __init__(self) -> None:
        """Initialize the authorization service."""
        self._authorization_context_cache = {}

# ---------------------------------------------------------------------------
# User resolution
# ---------------------------------------------------------------------------

    def get_user(
        self,
        user_id: int | str,
        *,
        tenant_id: int | str | None = None,
        eager: bool = True,
    ) -> User | None:
        """
        Retrieve a user eligible for authorization.

        Parameters
        ----------
        user_id:
            Primary key of the user.

        tenant_id:
            Optional tenant identifier. When supplied, the lookup is restricted
            to that tenant to prevent cross-tenant authorization.

        eager:
            When True, eagerly loads role and permission relationships to avoid
            N+1 query patterns during authorization.

        Returns
        -------
        User | None
            The resolved user or ``None`` if no matching user exists.
        """
        stmt = select(User)

        if eager:
            stmt = stmt.options(
                joinedload(User.user_roles)                 # type: ignore[arg-type]
                .joinedload(UserRole.role)                  # type: ignore[arg-type]
                .joinedload(Role.role_permissions)          # type: ignore[arg-type]
                .joinedload(RolePermission.permission)      # type: ignore[arg-type]
            )

        stmt = stmt.where(User.id == user_id)

        if tenant_id is not None:
            stmt = stmt.where(User.tenant_id == tenant_id)

        return db.session.execute(stmt).unique().scalar_one_or_none()

    def get_user_or_raise(
        self,
        user_id: int | str,
        *,
        tenant_id: int | str | None = None,
        eager: bool = True,
    ) -> User:
        """
        Retrieve a user or raise an authorization error.

        This helper should be used by all public authorization methods to
        ensure consistent error semantics throughout the application.
        """
        user = self.get_user(
            user_id=user_id,
            tenant_id=tenant_id,
            eager=eager,
        )

        if user is None:
            raise UserNotFoundError("User could not be resolved.")

        self._validate_user_status(user)

        return user

    def user_exists(
        self,
        user_id: int | str,
        *,
        tenant_id: int | str | None = None,
    ) -> bool:
        """
        Determine whether a user exists within the authorization scope.
        """
        return (
            self.get_user(
                user_id=user_id,
                tenant_id=tenant_id,
                eager=False,
            )
            is not None
        )

    def _validate_user_status(
        self,
        user: User,
    ) -> None:
        """
        Validate that the user account is permitted to authorize requests.

        Supported account states include:

        * inactive
        * disabled
        * locked
        * suspended
        * archived

        Additional account states may be incorporated without affecting the
        public API.
        """
        if getattr(user, "is_active", True) is False:
            raise AccountInactiveError()

        if getattr(user, "is_disabled", False):
            raise AccountDisabledError()

        if getattr(user, "is_locked", False):
            raise AccountLockedError()

        status = getattr(user, "status", None)

        if status is None:
            return

        match str(status).lower():
            case "inactive":
                raise AccountInactiveError()

            case "disabled":
                raise AccountDisabledError()

            case "locked":
                raise AccountLockedError()

            case "suspended":
                raise AccountSuspendedError()

            case "archived":
                raise AccountArchivedError()
        
# ---------------------------------------------------------------------------
# Authorization context
# ---------------------------------------------------------------------------

    def _user_cache_key(
        self,
        user: User,
    ) -> tuple[int | str | None, int | str]:
        """
        Return the cache key for an authorization context.

        The cache key includes both the tenant identifier and the user
        identifier to ensure complete tenant isolation.

        Returns
        -------
        tuple
            A stable cache key in the form::

                (tenant_id, user_id)
        """
        return (
            getattr(user, "tenant_id", None),
            user.id,
        )

    def _get_cached_context(
        self,
        user: User,
    ) -> AuthorizationContext | None:
        """
        Retrieve a cached authorization context for the user.
        """
        return self._authorization_context_cache.get(self._user_cache_key(user))

    def _store_cached_context(
        self,
        context: AuthorizationContext,
    ) -> AuthorizationContext:
        """
        Store an authorization context in the local cache.

        The current implementation is intentionally lightweight. It serves as
        the extension point for future request-scoped or distributed caching.
        """
        self._authorization_context_cache[self._user_cache_key(context.user)] = context
        return context

    def clear_authorization_cache(self) -> None:
        """
        Clear any cached authorization contexts.

        This method is primarily intended for testing and future cache
        invalidation hooks.
        """
        self._authorization_context_cache.clear()

# ---------------------------------------------------------------------------
# Role resolution
# ---------------------------------------------------------------------------

    def get_roles(
        self,
        user: User | int | str,
        *,
        tenant_id: int | str | None = None,
    ) -> frozenset[str]:
        """
        Return the effective roles assigned to a user.

        Parameters
        ----------
        user:
            Either a User instance or a user identifier.

        tenant_id:
            Optional tenant restriction used when resolving the user.

        Returns
        -------
        frozenset[str]
            Deterministically ordered role names.
        """
        return self._get_authorization_context(
            user,
            tenant_id=tenant_id,
        ).roles
        
    def has_role(
        self,
        user: User | int | str,
        role: str,
        *,
        tenant_id: int | str | None = None,
    ) -> bool:
        """
        Determine whether a user possesses a specific role.

        Global authorization overrides automatically satisfy every role check.
        """
        context = self._get_authorization_context(
            user,
            tenant_id=tenant_id,
        )

        if self._has_global_authorization_override(context.user):
            return True

        return role in context.roles

    def has_any_role(
        self,
        user: User | int | str,
        roles: Iterable[str],
        *,
        tenant_id: int | str | None = None,
    ) -> bool:
        """
        Determine whether a user possesses at least one of the supplied roles.

        Global authorization overrides automatically satisfy the requirement.
        """
        context = self._get_authorization_context(
            user,
            tenant_id=tenant_id,
        )

        if self._has_global_authorization_override(context.user):
            return True

        required_roles = frozenset(roles)

        return not context.roles.isdisjoint(required_roles)

    def has_all_roles(
        self,
        user: User | int | str,
        roles: Iterable[str],
        *,
        tenant_id: int | str | None = None,
    ) -> bool:
        """
        Determine whether a user possesses every supplied role.

        Global authorization overrides automatically satisfy the
        requirement.
        """
        context = self._get_authorization_context(
            user,
            tenant_id=tenant_id,
        )

        if self._has_global_authorization_override(context.user):
            return True

        required_roles = frozenset(roles)

        return required_roles.issubset(context.roles)

    def _resolve_user(
        self,
        user: User | int | str,
        *,
        tenant_id: int | str | None = None,
    ) -> User:
        """
        Resolve and validate a user for authorization.

        The caller may supply either a ``User`` instance or a user identifier.
        Identifiers are resolved using the configured tenant scope before the
        user's account status is validated.

        Parameters
        ----------
        user:
            A ``User`` instance or a user identifier.

        tenant_id:
            Optional tenant restriction applied during user resolution.

        Returns
        -------
        User
            A validated user ready for authorization.

        Raises
        ------
        UserNotFoundError
            If the user cannot be resolved.

        AccountInactiveError
            If the account is inactive.

        AccountDisabledError
            If the account is disabled.

        AccountLockedError
            If the account is locked.

        AccountSuspendedError
            If the account is suspended.

        AccountArchivedError
            If the account is archived.
        """
        resolved_user = (
            user
            if isinstance(user, User)
            else self.get_user_or_raise(
                user_id=user,
                tenant_id=tenant_id,
            )
        )

        self._validate_user_status(resolved_user)

        return resolved_user

    def _is_owner(self, user: User) -> bool:
        """
        Determine whether the user is the tenant owner.

        This helper centralizes the owner override logic so future
        enhancements (for example, platform administrators or
        organization owners) can be introduced without modifying
        role evaluation methods.
        """
        return bool(getattr(user, "is_owner", False))   


# ---------------------------------------------------------------------------
# Permission aggregation
# ---------------------------------------------------------------------------

    def get_permissions(
        self,
        user: User | int | str,
        *,
        tenant_id: int | str | None = None,
    ) -> frozenset[str]:
        """
        Return the user's effective permissions.

        Parameters
        ----------
        user:
            Either a User instance or a user identifier.

        tenant_id:
            Optional tenant restriction used when resolving the user.

        Returns
        -------
        frozenset[str]
            Deterministically ordered permission names.
        """
        return self._get_authorization_context(
            user,
            tenant_id=tenant_id,
        ).permissions

    def _aggregate_roles(
        self,
        user: User,
    ) -> frozenset[str]:
        """
        Aggregate every effective role assigned to a user.

        Parameters
        ----------
        user:
            Resolved user.

        Returns
        -------
        frozenset[str]
            Deterministically ordered role names.
        """
        role_names = {
            str(role.name)
            for role in getattr(user, "roles", ())
            if getattr(role, "name", None)
        }

        return frozenset(sorted(role_names))

    def _aggregate_permissions(
        self,
        user: User,
    ) -> frozenset[str]:
        """
        Aggregate every effective permission assigned to a user.

        Effective permissions are computed as the union of permissions granted
        by all assigned roles. Duplicate permissions are removed automatically
        and the resulting collection is deterministically ordered.

        Parameters
        ----------
        user:
            The resolved user.

        Returns
        -------
        frozenset[str]
            Deterministically ordered permission names.
        """
        permission_names = {
            str(permission.name)
            for role in getattr(user, "roles", ())
            for permission in getattr(role, "permissions", ())
            if getattr(permission, "name", None)
        }

        return frozenset(sorted(permission_names))    
    
    def _build_authorization_context(
        self,
        user: User,
    ) -> AuthorizationContext:
        """
        Build a complete authorization context for a user.

        This helper is the single factory responsible for constructing
        AuthorizationContext instances. It centralizes aggregation of all
        authorization data to ensure consistent context creation throughout
        the service.

        Parameters
        ----------
        user:
            The resolved user.

        Returns
        -------
        AuthorizationContext
            Fully populated immutable authorization snapshot.
        """
        return AuthorizationContext(
            user=user,
            tenant_id=getattr(user, "tenant_id", None),
            roles=self._aggregate_roles(user),
            permissions=self._aggregate_permissions(user),
            branch_ids=self._aggregate_branch_ids(user),
        )

    def _get_authorization_context(
        self,
        user: User | int | str,
        *,
        tenant_id: int | str | None = None,
    ) -> AuthorizationContext:
        """
        Return the authorization context for a user.

        The authorization context is resolved from the in-memory cache when
        available. If no cached context exists, a new immutable authorization
        context is constructed, cached, and returned.

        Parameters
        ----------
        user:
            Either a User instance or a user identifier.

        tenant_id:
            Optional tenant restriction used when resolving the user.

        Returns
        -------
        AuthorizationContext
            The cached or newly constructed authorization context.
        """
        resolved_user = self._resolve_user(
            user,
            tenant_id=tenant_id,
        )

        context = self._get_cached_context(resolved_user)

        if context is None:
            context = self._build_authorization_context(
                resolved_user,
            )
            self._store_cached_context(context)

        return context

    def permission_count(
        self,
        user: User | int | str,
        *,
        tenant_id: int | str | None = None,
    ) -> int:
        """
        Return the number of effective permissions assigned to the user.
        """
        return len(
            self.get_permissions(
                user,
                tenant_id=tenant_id,
            )
        )

    def get_permission_objects(
        self,
        user: User | int |str,
        *,
        tenant_id: int | str | None = None,
    ) -> tuple[Permission, ...]:
        """
        Return Permission model instances assigned to the user.

        This helper is intended for administrative interfaces,
        reporting, and auditing. Permission evaluation should
        generally use :meth:`get_permissions`.

        Duplicate permissions inherited from multiple roles are removed while
        preserving deterministic ordering.
        """
        resolved_user = self._resolve_user(
            user,
            tenant_id=tenant_id,
        )

        permissions: dict[str, Permission] = {
            permission.name: permission
            for role in getattr(resolved_user, "roles", ())
            for permission in getattr(role, "permissions", ())
            if getattr(permission, "name", None)
        }

        return tuple(
            permissions[name]
            for name in sorted(permissions)
        )

    def refresh_context(
        self,
        user: User | int | str,
        *,
        tenant_id: int | str | None = None,
    ) -> AuthorizationContext:
        """
        Rebuild and cache the authorization context for a user.

        This method should be invoked whenever authorization-related data
        changes, such as role, permission, or branch assignments.
        """
        resolved_user = self._resolve_user(
            user,
            tenant_id=tenant_id,
        )

        context = self._build_authorization_context(
            resolved_user,
        )

        self._store_cached_context(context)

        return context



# ---------------------------------------------------------------------------
# Permission evaluation
# ---------------------------------------------------------------------------

    def has_permission(
        self,
        user: User | int | str,
        permission: str,
        *,
        tenant_id: int | str | None = None,
    ) -> bool:
        """
        Determine whether a user possesses a specific permission.

        Global authorization overrides automatically satisfy every permission
        check.
        """
        context = self._get_authorization_context(
            user,
            tenant_id=tenant_id,
        )

        if self._has_global_authorization_override(context.user):
            return True

        return permission in context.permissions

    def has_any_permission(
        self,
        user: User | int | str,
        permissions: Iterable[str],
        *,
        tenant_id: int | str | None = None,
    ) -> bool:
        """
        Determine whether a user possesses at least one of the supplied
        permissions.

        Global authorization overrides automatically satisfy the requirement.
        """
        context = self._get_authorization_context(
            user,
            tenant_id=tenant_id,
        )

        if self._has_global_authorization_override(context.user):
            return True

        required_permissions = frozenset(permissions)

        return not context.permissions.isdisjoint(
            required_permissions,
        )

    def has_all_permissions(
        self,
        user: User | int | str,
        permissions: Iterable[str],
        *,
        tenant_id: int | str | None = None,
    ) -> bool:
        """
        Determine whether a user possesses every supplied permission.

        Global authorization overrides automatically satisfy the
        requirement.
        """
        context = self._get_authorization_context(
            user,
            tenant_id=tenant_id,
        )

        if self._has_global_authorization_override(context.user):
            return True

        required_permissions = frozenset(permissions)

        return required_permissions.issubset(
            context.permissions,
        )
    def has_permissions(
        self,
        user: User | int | str,
        permissions: Iterable[str],
        *,
        require_all: bool = True,
        tenant_id: int | str | None = None,
    ) -> bool:
        """
        Generic permission evaluation helper.

        Parameters
        ----------
        require_all:
            When True, every permission is required.
            When False, at least one permission is required.
        """
        if require_all:
            return self.has_all_permissions(
                user,
                permissions,
                tenant_id=tenant_id,
            )

        return self.has_any_permission(
            user,
            permissions,
            tenant_id=tenant_id,
        )

    def has_system_permission(
        self,
        user: User | int | str,
        *,
        tenant_id: int | str | None = None,
    ) -> bool:
        """
        Determine whether the user possesses the reserved wildcard
        system permission.
        """
        resolved_user = self._resolve_user(
            user,
            tenant_id=tenant_id,
        )

        permissions = self.get_permissions(
            resolved_user,
            tenant_id=tenant_id,
        )

        return SYSTEM_PERMISSION in permissions

    def _has_global_access(self, user: User) -> bool:
        """
        Determine whether the user bypasses normal permission evaluation.

        This method centralizes every authorization override within the
        application.

        Current overrides
        -----------------
        * Tenant owner
        * Platform administrator (future compatible)
        * Wildcard system permission

        Future implementations should extend this method rather than modify
        individual permission evaluation methods.
        """
        if self._has_global_authorization_override(user):
            return True

        if self._is_platform_administrator(user):
            return True

        context = self._get_cached_context(user)

        if context is not None:
            return SYSTEM_PERMISSION in context.permissions

        permissions = self.get_permissions(user)

        return SYSTEM_PERMISSION in permissions

    def _is_platform_administrator(self, user: User) -> bool:
        """
        Extension point for platform-wide administrators.

        The current authorization model is tenant-centric. This method
        provides a stable hook for introducing platform administrators
        without requiring changes to permission evaluation logic.
        """
        if getattr(user, "is_platform_admin", False):
            return True

        return PLATFORM_ADMIN_ROLE in self.get_roles(user)

# ---------------------------------------------------------------------------
# Authorization overrides
# ---------------------------------------------------------------------------

    def _has_global_authorization_override(
        self,
        user: User,
    ) -> bool:
        """
        Determine whether a user bypasses standard authorization checks.

        Global authorization overrides are reserved for identities that should
        always succeed authorization regardless of role or permission
        assignments.

        Current overrides
        -----------------
        * Tenant owner

        Future overrides
        ----------------
        * Platform administrator
        * Emergency break-glass accounts
        * System maintenance identities
        """
        return (
            self._is_owner(user)
            or self._is_platform_administrator(user)
        )
# ---------------------------------------------------------------------------
# Resource access
# ---------------------------------------------------------------------------

    def can_access_tenant(
        self,
        user: User | int | str,
        tenant_id: int | str,
    ) -> bool:
        """
        Determine whether the user may access the specified tenant.

        Authorization succeeds when:

        * the user is the tenant owner
        * the user is a platform administrator
        * the user's tenant matches the requested tenant

        Cross-tenant access is denied by default.
        """
        resolved_user = self._resolve_user(user)

        if self._is_platform_administrator(resolved_user):
            return True

        if self._is_owner(resolved_user):
            return True

        return getattr(resolved_user, "tenant_id", None) == tenant_id

    def can_access_branch(
        self,
        user: User | int |str,
        branch_id: int | str,
        *,
        tenant_id: int | str | None = None,
    ) -> bool:
        """
        Determine whether the user may access a branch.

        Current implementation:

        * validates tenant isolation
        * supports future branch-level restrictions
        * defaults to allowing all branches within the user's tenant

        Future versions may incorporate:

        * UserBranch assignments
        * BranchRole mappings
        * Regional managers
        * Read-only branch permissions
        """
        resolved_user = self._resolve_user(
            user,
            tenant_id=tenant_id,
        )

        if self._has_global_access(resolved_user):
            return True

        if tenant_id is not None:
            if not self.can_access_tenant(
                resolved_user,
                tenant_id,
            ):
                return False

        return self._has_branch_access(
            resolved_user,
            branch_id,
        )

    def _has_branch_access(
        self,
        user: User,
        branch_id: int | str,
    ) -> bool:
        """
        Branch authorization extension point.

        The current authorization model grants users access to all branches
        within their tenant.

        Future branch assignment models should replace the default behavior
        implemented here without affecting the public API.
        """
        branch_ids = self._aggregate_branch_ids(user)

        if not branch_ids:
            return True

        return str(branch_id) in {
            str(value)
            for value in branch_ids
        }

    def _aggregate_branch_ids(
        self,
        user: User,
    ) -> frozenset[str]:
        """
        Aggregate the branches explicitly assigned to a user.

        The current authorization model grants tenant-wide branch access by
        default. This helper exists as an extension point for future branch
        assignment models and intentionally performs no caching.

        Supported future implementations may include:

        * user.branch_assignments
        * user.branches
        * UserBranch model
        * Branch-level RBAC
        * Organizational unit assignments

        Parameters
        ----------
        user:
            The resolved user.

        Returns
        -------
        frozenset[str]
            Deterministically ordered branch identifiers assigned to the user.
            An empty set indicates tenant-wide branch access under the current
            authorization model.
        """
        branch_ids: set[str] = set()

        #
        # Future implementations populate branch_ids here.
        #
        # Example:
        #
        # for assignment in getattr(user, "branch_assignments", ()):
        #     branch = getattr(assignment, "branch", assignment)
        #
        #     if branch is None:
        #         continue
        #
        #     branch_id = getattr(branch, "id", None)
        #
        #     if branch_id is not None:
        #         branch_ids.add(str(branch_id))
        #

        return frozenset(sorted(branch_ids))

    def validate_tenant_access(
        self,
        user: User | int | str,
        tenant_id: int | str,
    ) -> None:
        """
        Validate tenant access.

        Raises
        ------
        PermissionError
            If access is denied.
        """
        if self.can_access_tenant(
            user,
            tenant_id,
        ):
            return

        self._audit_authorization_denied(
            user,
            resource="tenant",
            resource_id=tenant_id,
        )

        raise TenantAccessDeniedError(
            "Access to the requested tenant is denied."
        )

    def validate_branch_access(
        self,
        user: User | int | str,
        branch_id: int | str,
        *,
        tenant_id: int | str | None = None,
    ) -> None:
        """
        Validate branch access.

        Raises
        ------
        PermissionError
            If branch access is denied.
        """
        if self.can_access_branch(
            user,
            branch_id,
            tenant_id=tenant_id,
        ):
            return

        self._audit_authorization_denied(
            user,
            resource="branch",
            resource_id=branch_id,
        )

        raise BranchAccessDeniedError(
            "Access to the requested branch is denied."
        )

    def _audit_authorization_denied(
        self,
        user: User | int | str,
        *,
        resource: str,
        resource_id: object | None = None,
        permission: str | None = None,
        role: str | None = None,
    ) -> None:
        """
        Record a meaningful authorization denial.

        Successful authorization checks are intentionally not audited in order
        to avoid excessive audit volume. Audit failures are handled on a
        best-effort basis and must never interfere with authorization
        enforcement.

        Parameters
        ----------
        user:
            User whose authorization request was denied.

        resource:
            Protected resource involved in the authorization decision.

        resource_id:
            Optional identifier of the protected resource.

        permission:
            Permission that was required, if applicable.

        role:
            Role that was required, if applicable.
        """
        try:
            resolved_user = (
                user
                if isinstance(user, User)
                else self.get_user(user, eager=False)
            )

            tenant_id = getattr(resolved_user, "tenant_id", None)
            user_id = getattr(resolved_user, "id", None)
            branch_id = getattr(resolved_user, "branch_id", None)

            reason_parts: list[str] = []

            if permission:
                reason_parts.append(f"Missing permission: {permission}")

            if role:
                reason_parts.append(f"Missing role: {role}")

            reason = "; ".join(reason_parts) or None

            resource_name = resource.strip().lower()

            if resource_name == "tenant":
                self.audit_service.tenant_access_denied(
                    tenant_id=str(tenant_id),
                    user_id=str(user_id),
                    entity_type="Tenant",
                    entity_id=str(resource_id) if resource_id else None,
                    branch_id=str(branch_id) if branch_id else None,
                    reason=reason,
                )

            elif resource_name == "branch":
                self.audit_service.branch_access_denied(
                    tenant_id=str(tenant_id),
                    user_id=str(user_id),
                    entity_type="Branch",
                    entity_id=str(resource_id) if resource_id else None,
                    branch_id=str(branch_id) if branch_id else None,
                    reason=reason,
                )

            else:
                self.audit_service.authorization_denied(
                    tenant_id=str(tenant_id),
                    user_id=str(user_id),
                    entity_type=resource.title(),
                    entity_id=str(resource_id) if resource_id else None,
                    branch_id=str(branch_id) if branch_id else None,
                    reason=reason,
                )

        except Exception:
            current_app.logger.exception(
                "Failed to audit authorization denial."
            )
        
# ---------------------------------------------------------------------------
# Authorization enforcement helpers
# ---------------------------------------------------------------------------

    def require_permission(
        self,
        user: User | int | str,
        permission: str,
        *,
        tenant_id: int | str | None = None,
    ) -> User:
        """
        Require a single permission.

        Returns the resolved user to allow fluent usage by callers.

        Raises
        ------
        PermissionDeniedError
            If the permission requirement is not satisfied.
        """
        resolved_user = self._resolve_user(
            user,
            tenant_id=tenant_id,
        )

        if self.has_permission(
            resolved_user,
            permission,
            tenant_id=tenant_id,
        ):
            return resolved_user

        self._audit_authorization_denied(
            resolved_user,
            resource="permission",
            permission=permission,
        )

        raise PermissionDeniedError(
            f"Permission '{permission}' is required."
        )

    def require_any_permission(
        self,
        user: User | int | str,
        permissions: Iterable[str],
        *,
        tenant_id: int | str | None = None,
    ) -> User:
        """
        Require that a user possesses at least one of the supplied permissions.

        Returns the resolved user to allow fluent usage by callers.

        Raises
        ------
        PermissionDeniedError
            If none of the supplied permissions are granted.
        """
        resolved_user = self._resolve_user(
            user,
            tenant_id=tenant_id,
        )

        required_permissions = tuple(sorted(set(permissions)))

        if self.has_any_permission(
            resolved_user,
            required_permissions,
            tenant_id=tenant_id,
        ):
            return resolved_user

        self._audit_authorization_denied(
            resolved_user,
            resource="permission",
            permission=", ".join(required_permissions),
        )

        raise PermissionDeniedError(
            "At least one of the required permissions is required."
        )
    
    def require_all_permissions(
        self,
        user: User | int | str,
        permissions: Iterable[str],
        *,
        tenant_id: int | str | None = None,
    ) -> User:
        """
        Require that a user possesses every supplied permission.

        Returns the resolved user to allow fluent usage by callers.

        Raises
        ------
        PermissionDeniedError
            If one or more required permissions are not granted.
        """
        resolved_user = self._resolve_user(
            user,
            tenant_id=tenant_id,
        )

        required_permissions = tuple(
            sorted(
                set(permissions),
            )
        )

        if self.has_all_permissions(
            resolved_user,
            required_permissions,
            tenant_id=tenant_id,
        ):
            return resolved_user

        self._audit_authorization_denied(
            resolved_user,
            resource="permission",
            permission=", ".join(required_permissions),
        )

        raise PermissionDeniedError(
            "All required permissions must be granted."
        )

    def require_role(
        self,
        user: User | int | str,
        role: str,
        *,
        tenant_id: int | str | None = None,
    ) -> User:
        """
        Require that a user possesses a specific role.

        Returns the resolved user to allow fluent usage by callers.

        Raises
        ------
        RoleRequiredError
            If the required role is not assigned.
        """
        resolved_user = self._resolve_user(
            user,
            tenant_id=tenant_id,
        )

        if self.has_role(
            resolved_user,
            role,
            tenant_id=tenant_id,
        ):
            return resolved_user

        self._audit_authorization_denied(
            resolved_user,
            resource="role",
            role=role,
        )

        raise RoleRequiredError(
            f"Role '{role}' is required."
        )

    def require_any_role(
        self,
        user: User | int | str,
        roles: Iterable[str],
        *,
        tenant_id: int | str | None = None,
    ) -> User:
        """
        Require that a user possesses at least one of the supplied roles.

        Returns the resolved user to allow fluent usage by callers.

        Raises
        ------
        RoleRequiredError
            If none of the supplied roles are assigned.
        """
        resolved_user = self._resolve_user(
            user,
            tenant_id=tenant_id,
        )

        required_roles = tuple(
            sorted(
                set(roles),
            )
        )

        if self.has_any_role(
            resolved_user,
            required_roles,
            tenant_id=tenant_id,
        ):
            return resolved_user

        self._audit_authorization_denied(
            resolved_user,
            resource="role",
            role=", ".join(required_roles),
        )

        raise RoleRequiredError(
            "None of the required roles are assigned."
        )

    def require_all_roles(
        self,
        user: User | int | str,
        roles: Iterable[str],
        *,
        tenant_id: int | str | None = None,
    ) -> User:
        """
        Require that a user possesses every supplied role.

        Returns the resolved user to allow fluent usage by callers.

        Raises
        ------
        RoleRequiredError
            If one or more required roles are not assigned.
        """
        resolved_user = self._resolve_user(
            user,
            tenant_id=tenant_id,
        )

        required_roles = tuple(
            sorted(
                set(roles),
            )
        )

        if self.has_all_roles(
            resolved_user,
            required_roles,
            tenant_id=tenant_id,
        ):
            return resolved_user

        self._audit_authorization_denied(
            resolved_user,
            resource="role",
            role=", ".join(required_roles),
        )

        raise RoleRequiredError(
            "All required roles must be assigned."
        )

    def authorize(
        self,
        user: User | int | str,
        *,
        permission: str | None = None,
        any_permissions: Iterable[str] | None = None,
        all_permissions: Iterable[str] | None = None,
        role: str | None = None,
        any_roles: Iterable[str] | None = None,
        all_roles: Iterable[str] | None = None,
        tenant_id: int | str | None = None,
        branch_id: int | str | None = None,
    ) -> User:
        """
        Authorize a user against one or more authorization requirements.

        This method provides the primary authorization entry point for
        decorators, middleware, API endpoints, and business services.

        Authorization is enforced in the following order:

        1. User resolution
        2. Tenant access
        3. Branch access
        4. Role requirements
        5. Permission requirements

        Parameters
        ----------
        user:
            User instance or user identifier.

        permission:
            Single required permission.

        any_permissions:
            At least one of these permissions must be granted.

        all_permissions:
            Every supplied permission must be granted.

        role:
            Single required role.

        any_roles:
            At least one of these roles must be assigned.

        all_roles:
            Every supplied role must be assigned.

        tenant_id:
            Optional tenant scope.

        branch_id:
            Optional branch scope.

        Returns
        -------
        User
            The resolved and authorized user.

        Raises
        ------
        TenantAccessDeniedError
            If the user cannot access the requested tenant.

        BranchAccessDeniedError
            If the user cannot access the requested branch.

        RoleRequiredError
            If the required role requirements are not satisfied.

        PermissionDeniedError
            If the required permission requirements are not satisfied.
        """
        resolved_user = self._resolve_user(
            user,
            tenant_id=tenant_id,
        )

        if tenant_id is not None:
            self.validate_tenant_access(
                resolved_user,
                tenant_id,
            )

        if branch_id is not None:
            self.validate_branch_access(
                resolved_user,
                branch_id,
                tenant_id=tenant_id,
            )

        if role is not None:
            self.require_role(
                resolved_user,
                role,
                tenant_id=tenant_id,
            )

        if any_roles is not None:
            self.require_any_role(
                resolved_user,
                any_roles,
                tenant_id=tenant_id,
            )

        if all_roles is not None:
            self.require_all_roles(
                resolved_user,
                all_roles,
                tenant_id=tenant_id,
            )

        if permission is not None:
            self.require_permission(
                resolved_user,
                permission,
                tenant_id=tenant_id,
            )

        if any_permissions is not None:
            self.require_any_permission(
                resolved_user,
                any_permissions,
                tenant_id=tenant_id,
            )

        if all_permissions is not None:
            self.require_all_permissions(
                resolved_user,
                all_permissions,
                tenant_id=tenant_id,
            )

        return resolved_user
# ---------------------------------------------------------------------------
# Singleton service instance
# ---------------------------------------------------------------------------

#: Shared authorization service instance used throughout the application.
#: The service is intentionally stateless, making a module-level singleton
#: appropriate for application-wide use.
authorization_service = AuthorizationService()                              