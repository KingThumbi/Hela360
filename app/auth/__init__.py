"""
Hela360 Enterprise Authentication & Identity Management

This package implements authentication and authorization for the Hela360
multi-tenant Pharmacy POS & ERP platform.

Responsibilities
----------------
- JWT authentication
- Refresh token management
- User session management
- Password management
- Role & permission enforcement
- Authentication audit support

This package is intentionally modular to keep authentication logic
isolated from the rest of the application.

Modules
-------
routes.py
    Authentication API endpoints.

service.py
    Core authentication business logic.

jwt.py
    JWT creation, validation, and refresh token handling.

password.py
    Secure password hashing and verification.

decorators.py
    Route protection decorators.

permissions.py
    Permission registry and authorization helpers.

schemas.py
    Request/response validation schemas.

utils.py
    Shared helper utilities.
"""

from flask import Blueprint

# Authentication API Blueprint
bp = Blueprint("auth", __name__)


def init_app(app) -> None:
    """
    Register the authentication blueprint with the Flask application.

    This function is intentionally lightweight so it can be called from
    the application factory without introducing circular imports.

    Example
    -------
        from app.auth import init_app

        init_app(app)
    """
    from . import routes  # noqa: F401

    app.register_blueprint(bp, url_prefix="/api/auth")


__all__ = [
    "bp",
    "init_app",
]