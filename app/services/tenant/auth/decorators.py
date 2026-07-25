"""
Authorization decorators for Hela360.

These decorators provide a declarative authorization layer for Flask
views, REST API endpoints and future GraphQL or RPC handlers.

All authorization decisions are delegated to AuthorizationService,
ensuring there is a single source of truth for access control across
the application.

Decorators never implement authorization logic directly—they merely:

    • Resolve the authenticated identity
    • Determine tenant and branch scope
    • Invoke AuthorizationService.authorize()

This keeps authorization policies centralized while providing an
ergonomic interface for route protection.

Example
-------

@app.get("/products")
@require_permission("products.read")
def list_products():
    ...

@app.post("/products")
@require_role("inventory_manager")
def create_product():
    ...

@app.delete("/products/<uuid:id>")
@require_all_permissions(
    "products.delete",
    "inventory.write",
)
def delete_product(id):
    ...

Hela360 Enterprise Pharmacy POS & ERP
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from flask import abort

from app.auth.jwt import (
    Identity,
    get_current_identity,
)
from app.services.tenant.auth.authorization_service import (
    authorization_service,
)

# ============================================================================
# Generic typing
# ============================================================================

P = ParamSpec("P")
R = TypeVar("R")


# ============================================================================
# Identity helpers
# ============================================================================


def _current_identity() -> Identity:
    """
    Return the currently authenticated identity.

    Returns
    -------
    Identity
        The authenticated JWT identity.

    Raises
    ------
    401 Unauthorized
        If no authenticated identity is available.

    Notes
    -----
    Authentication is expected to have already been performed by
    authentication middleware or a JWT validation decorator.
    """

    identity = get_current_identity()

    if identity is None:
        abort(401)

    return identity


# ============================================================================
# Scope helpers
# ============================================================================


def _resolve_scope(
    identity: Identity,
    *,
    tenant_id: int | str | None = None,
    branch_id: int | str | None = None,
) -> tuple[str, str | None]:
    """
    Resolve the effective authorization scope.

    Explicit decorator arguments override values obtained from the JWT
    identity. When omitted, tenant and branch information are derived
    from the authenticated identity.

    Parameters
    ----------
    identity:
        Authenticated JWT identity.

    tenant_id:
        Optional tenant override.

    branch_id:
        Optional branch override.

    Returns
    -------
    tuple[str, str | None]
        Effective ``(tenant_id, branch_id)`` used during authorization.
    """

    resolved_tenant = (
        str(tenant_id)
        if tenant_id is not None
        else identity.tenant_id
    )

    resolved_branch = (
        str(branch_id)
        if branch_id is not None
        else identity.branch_id
    )

    return resolved_tenant, resolved_branch

# ============================================================================
# Generic authorization decorator
# ============================================================================


def require_authorization(
    *,
    permission: str | None = None,
    any_permissions: Iterable[str] | None = None,
    all_permissions: Iterable[str] | None = None,
    role: str | None = None,
    any_roles: Iterable[str] | None = None,
    all_roles: Iterable[str] | None = None,
    tenant_id: int | str | None = None,
    branch_id: int | str | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Protect a view using the enterprise authorization engine.

    This is the single decorator responsible for enforcing all
    authorization requirements. The remaining decorators in this module
    are thin convenience wrappers around this function.

    Authorization is performed in the following order:

        1. Resolve the authenticated identity.
        2. Resolve tenant and branch scope.
        3. Delegate authorization to AuthorizationService.
        4. Execute the wrapped view if authorization succeeds.

    Parameters
    ----------
    permission:
        Require a single permission.

    any_permissions:
        Require at least one of the supplied permissions.

    all_permissions:
        Require every supplied permission.

    role:
        Require a single role.

    any_roles:
        Require at least one of the supplied roles.

    all_roles:
        Require every supplied role.

    tenant_id:
        Optional tenant scope override.

    branch_id:
        Optional branch scope override.

    Returns
    -------
    Callable
        Decorated Flask view.

    Raises
    ------
    401 Unauthorized
        If no authenticated identity exists.

    AuthorizationError
        Any authorization exception raised by AuthorizationService.
    """

    def decorator(
        view: Callable[P, R],
    ) -> Callable[P, R]:
        @wraps(view)
        def wrapper(
            *args: P.args,
            **kwargs: P.kwargs,
        ) -> R:
            identity = _current_identity()

            resolved_tenant_id, resolved_branch_id = (
                _resolve_scope(
                    identity,
                    tenant_id=tenant_id,
                    branch_id=branch_id,
                )
            )

            authorization_service.authorize(
                identity.user_id,
                permission=permission,
                any_permissions=any_permissions,
                all_permissions=all_permissions,
                role=role,
                any_roles=any_roles,
                all_roles=all_roles,
                tenant_id=resolved_tenant_id,
                branch_id=resolved_branch_id,
            )

            return view(
                *args,
                **kwargs,
            )

        return wrapper

    return decorator

# ============================================================================
# Permission decorators
# ============================================================================


def require_permission(
    permission: str,
    *,
    tenant_id: int | str | None = None,
    branch_id: int | str | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Require a single permission.
    """
    return require_authorization(
        permission=permission,
        tenant_id=tenant_id,
        branch_id=branch_id,
    )


def require_any_permission(
    permissions: Iterable[str],
    *,
    tenant_id: int | str | None = None,
    branch_id: int | str | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Require at least one permission.
    """
    return require_authorization(
        any_permissions=permissions,
        tenant_id=tenant_id,
        branch_id=branch_id,
    )


def require_all_permissions(
    permissions: Iterable[str],
    *,
    tenant_id: int | str | None = None,
    branch_id: int | str | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Require every supplied permission.
    """
    return require_authorization(
        all_permissions=permissions,
        tenant_id=tenant_id,
        branch_id=branch_id,
    )

# ============================================================================
# Role decorators
# ============================================================================

def require_role(
    role: str,
    *,
    tenant_id: int | str | None = None,
    branch_id: int | str | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Require a specific role.
    """
    return require_authorization(
        role=role,
        tenant_id=tenant_id,
        branch_id=branch_id,
    )


def require_any_role(
    roles: Iterable[str],
    *,
    tenant_id: int | str | None = None,
    branch_id: int | str | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Require at least one role.
    """
    return require_authorization(
        any_roles=roles,
        tenant_id=tenant_id,
        branch_id=branch_id,
    )


def require_all_roles(
    roles: Iterable[str],
    *,
    tenant_id: int | str | None = None,
    branch_id: int | str | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Require every supplied role.
    """
    return require_authorization(
        all_roles=roles,
        tenant_id=tenant_id,
        branch_id=branch_id,
    )
# ============================================================================
# Tenant and branch decorators
# ============================================================================


def require_tenant_access(
    *,
    tenant_id: int | str | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Require access to a tenant.

    When ``tenant_id`` is omitted, the tenant identifier contained in the
    authenticated JWT is used.
    """
    return require_authorization(
        tenant_id=tenant_id,
    )


def require_branch_access(
    *,
    tenant_id: int | str | None = None,
    branch_id: int | str | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Require access to a branch.

    When ``branch_id`` is omitted, the branch identifier contained in the
    authenticated JWT is used.

    The tenant scope defaults to the authenticated tenant unless explicitly
    overridden.
    """
    return require_authorization(
        tenant_id=tenant_id,
        branch_id=branch_id,
    )


# ============================================================================
# Public exports
# ============================================================================

__all__ = (
    "require_authorization",
    "require_permission",
    "require_any_permission",
    "require_all_permissions",
    "require_role",
    "require_any_role",
    "require_all_roles",
    "require_tenant_access",
    "require_branch_access",
)    