"""
Authentication & Authorization Decorators

These decorators protect API endpoints by enforcing:

- Authentication
- Tenant isolation
- Branch isolation
- Role-based access control (RBAC)
- Permission-based authorization (PBAC)

All authorization is enforced on the backend.

Hela360 Enterprise Pharmacy POS & ERP
"""

from __future__ import annotations

from functools import wraps
from typing import Callable

from flask import g, jsonify

from .jwt import get_current_identity
from .permissions import has_permission


# ----------------------------------------------------------------------
# Error Responses
# ----------------------------------------------------------------------

def _error(message: str, status: int):
    """Return a consistent JSON error response."""
    return jsonify(
        {
            "ok": False,
            "error": message,
        }
    ), status


# ----------------------------------------------------------------------
# Authentication
# ----------------------------------------------------------------------

def login_required(view: Callable):
    """
    Ensure the request contains a valid authenticated JWT.

    On success, the authenticated identity is stored in flask.g
    as:

        g.identity

    Returns
    -------
    HTTP 401
        If authentication fails.
    """

    @wraps(view)
    def wrapper(*args, **kwargs):

        identity = get_current_identity()

        if identity is None:
            return _error("Authentication required.", 401)

        g.identity = identity

        return view(*args, **kwargs)

    return wrapper


# ----------------------------------------------------------------------
# Permission Enforcement
# ----------------------------------------------------------------------

def permission_required(permission: str):
    """
    Require a specific permission.

    Example
    -------

        @permission_required("products.create")
    """

    def decorator(view):

        @wraps(view)
        def wrapper(*args, **kwargs):

            identity = getattr(g, "identity", None)

            if identity is None:
                identity = get_current_identity()

                if identity is None:
                    return _error("Authentication required.", 401)

                g.identity = identity

            if not has_permission(identity, permission):
                return _error("Permission denied.", 403)

            return view(*args, **kwargs)

        return wrapper

    return decorator


# ----------------------------------------------------------------------
# Role Enforcement
# ----------------------------------------------------------------------

def role_required(*roles: str):
    """
    Restrict access to one or more roles.

    Example
    -------

        @role_required("Administrator")
    """

    def decorator(view):

        @wraps(view)
        def wrapper(*args, **kwargs):

            identity = getattr(g, "identity", None)

            if identity is None:
                identity = get_current_identity()

                if identity is None:
                    return _error("Authentication required.", 401)

                g.identity = identity

            if identity.role not in roles:
                return _error("Insufficient role.", 403)

            return view(*args, **kwargs)

        return wrapper

    return decorator


# ----------------------------------------------------------------------
# Tenant Isolation
# ----------------------------------------------------------------------

def tenant_required(view):
    """
    Ensure the authenticated user belongs to the requested tenant.

    Routes should place the resolved tenant_id in:

        g.tenant_id
    """

    @wraps(view)
    def wrapper(*args, **kwargs):

        identity = getattr(g, "identity", None)

        if identity is None:
            identity = get_current_identity()

            if identity is None:
                return _error("Authentication required.", 401)

            g.identity = identity

        tenant_id = getattr(g, "tenant_id", None)

        if tenant_id is None:
            return _error("Tenant context missing.", 400)

        if identity.tenant_id != tenant_id:
            return _error("Tenant access denied.", 403)

        return view(*args, **kwargs)

    return wrapper


# ----------------------------------------------------------------------
# Branch Isolation
# ----------------------------------------------------------------------

def branch_required(view):
    """
    Restrict access to the authenticated branch.

    Routes should place the resolved branch_id in:

        g.branch_id
    """

    @wraps(view)
    def wrapper(*args, **kwargs):

        identity = getattr(g, "identity", None)

        if identity is None:
            identity = get_current_identity()

            if identity is None:
                return _error("Authentication required.", 401)

            g.identity = identity

        branch_id = getattr(g, "branch_id", None)

        if branch_id is None:
            return _error("Branch context missing.", 400)

        if (
            identity.branch_id
            and identity.branch_id != branch_id
        ):
            return _error("Branch access denied.", 403)

        return view(*args, **kwargs)

    return wrapper


# ----------------------------------------------------------------------
# Owner / Administrator
# ----------------------------------------------------------------------

def owner_required(view):
    """
    Restrict access to tenant owners.

    Intended for sensitive operations such as:

    - Billing
    - Subscription
    - Tenant deletion
    - Security configuration
    """

    @wraps(view)
    def wrapper(*args, **kwargs):

        identity = getattr(g, "identity", None)

        if identity is None:
            identity = get_current_identity()

            if identity is None:
                return _error("Authentication required.", 401)

            g.identity = identity

        if not getattr(identity, "is_owner", False):
            return _error("Owner access required.", 403)

        return view(*args, **kwargs)

    return wrapper