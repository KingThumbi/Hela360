"""
Hela360 Platform Authentication API
===================================

Independent HTTP authentication boundary for Hela360 Office identities.

This package is intentionally separate from app.auth, which remains the
tenant IAM HTTP boundary.
"""

from __future__ import annotations

from flask import Blueprint


bp = Blueprint(
    "platform_auth",
    __name__,
)


def init_platform_auth(app) -> None:
    """Register the Hela360 Office authentication blueprint."""

    from app.platform_auth import routes  # noqa: F401

    app.register_blueprint(
        bp,
        url_prefix="/api/platform-auth",
    )


__all__ = [
    "bp",
    "init_platform_auth",
]
