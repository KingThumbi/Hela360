"""
Enterprise API Error Handlers.

Converts domain exceptions into consistent JSON responses.
"""

from __future__ import annotations

from flask import jsonify
from werkzeug.exceptions import HTTPException

from app.auth.exceptions import (
    AccountDisabledError,
    AccountInactiveError,
    AccountLockedError,
    AccountSuspendedError,
    AuthenticationError,
    AuthorizationError,
    InvalidCredentialsError,
    UserNotFoundError,
)
from app.errors import DomainError


def register_error_handlers(app):
    """
    Register enterprise API exception handlers.
    """

    @app.errorhandler(InvalidCredentialsError)
    def invalid_credentials(exc):
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_CREDENTIALS",
                        "message": str(exc),
                    },
                }
            ),
            401,
        )

    @app.errorhandler(AccountLockedError)
    def account_locked(exc):
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "ACCOUNT_LOCKED",
                        "message": str(exc),
                    },
                }
            ),
            423,
        )

    def account_unavailable(exc):
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "ACCOUNT_UNAVAILABLE",
                        "message": str(exc),
                    },
                }
            ),
            403,
        )

    app.register_error_handler(AccountInactiveError, account_unavailable)
    app.register_error_handler(AccountDisabledError, account_unavailable)
    app.register_error_handler(AccountSuspendedError, account_unavailable)

    @app.errorhandler(UserNotFoundError)
    def user_not_found(exc):
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "USER_NOT_FOUND",
                        "message": str(exc),
                    },
                }
            ),
            404,
        )

    @app.errorhandler(AuthenticationError)
    def authentication_failed(exc):
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "AUTHENTICATION_ERROR",
                        "message": str(exc),
                    },
                }
            ),
            401,
        )

    @app.errorhandler(AuthorizationError)
    def authorization_failed(exc):
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "AUTHORIZATION_DENIED",
                        "message": str(exc),
                    },
                }
            ),
            403,
        )

    @app.errorhandler(DomainError)
    def domain_error(exc):
        return (
            jsonify(
                {
                    "ok": False,
                    "error": {
                        "code": exc.code,
                        "message": str(exc),
                    },
                }
            ),
            exc.status_code,
        )

    @app.errorhandler(HTTPException)
    def http_exception(exc):
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": exc.name.upper().replace(" ", "_"),
                        "message": exc.description,
                    },
                }
            ),
            exc.code,
        )

    @app.errorhandler(Exception)
    def internal_error(exc):
        app.logger.exception(exc)

        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "An unexpected error occurred.",
                    },
                }
            ),
            500,
        )
