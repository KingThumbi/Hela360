"""
Authentication Exceptions

Enterprise exception hierarchy for the Hela360 Identity and Access
Management (IAM) subsystem.

These exceptions provide a strongly-typed error model for the
authentication and authorization services.

The API layer is responsible for translating these exceptions into
appropriate HTTP responses.

Example
-------
AuthenticationError        -> 401 Unauthorized
AuthorizationError         -> 403 Forbidden
AccountLockedError         -> 423 Locked
ValidationError            -> 400 Bad Request
ConflictError              -> 409 Conflict

Hela360 Enterprise Pharmacy POS & ERP
"""

from __future__ import annotations


# ============================================================================
# Base Exceptions
# ============================================================================


class AuthenticationError(Exception):
    """
    Base class for all authentication-related exceptions.
    """

    default_message = "Authentication failed."

    def __init__(self, message: str | None = None):
        super().__init__(message or self.default_message)


class AuthorizationError(Exception):
    """
    Base class for authorization failures.
    """

    default_message = "You do not have permission to perform this action."

    def __init__(self, message: str | None = None):
        super().__init__(message or self.default_message)

class AccountStatusError(AuthenticationError):
    """
    Base class for account state failures.
    """

    default_message = "Account status does not permit authentication."

# ============================================================================
# Authentication Failures
# ============================================================================


class InvalidCredentialsError(AuthenticationError):
    """
    Invalid username/email or password.
    """

    default_message = "Invalid username or password."


class InvalidTokenError(AuthenticationError):
    """
    Base class for invalid JWTs.
    """

    default_message = "Invalid authentication token."


class InvalidAccessTokenError(InvalidTokenError):
    """
    Access token is invalid.
    """

    default_message = "Invalid access token."


class InvalidRefreshTokenError(InvalidTokenError):
    """
    Refresh token is invalid.
    """

    default_message = "Invalid refresh token."


class ExpiredTokenError(InvalidTokenError):
    """
    JWT has expired.
    """

    default_message = "Authentication token has expired."


class RevokedTokenError(InvalidTokenError):
    """
    Refresh token has already been revoked.
    """

    default_message = "Authentication token has been revoked."


class InvalidTokenTypeError(InvalidTokenError):
    """
    JWT is of the wrong type.
    """

    default_message = "Unexpected authentication token type."


class MissingTokenError(AuthenticationError):
    """
    Authorization header missing.
    """

    default_message = "Authentication token is required."


# ============================================================================
# Session Errors
# ============================================================================


class SessionError(AuthenticationError):
    """
    Base session exception.
    """

    default_message = "Invalid session."


class SessionExpiredError(SessionError):
    """
    Session has expired.
    """

    default_message = "Your session has expired."


class SessionRevokedError(SessionError):
    """
    Session has been revoked.
    """

    default_message = "Your session has been revoked."


class SessionNotFoundError(SessionError):
    """
    Session does not exist.
    """

    default_message = "Session not found."


# ============================================================================
# Account Errors
# ============================================================================


class AccountLockedError(AuthenticationError):
    """
    Account locked due to excessive failed logins.
    """

    default_message = "Account is temporarily locked."


class AccountDisabledError(AuthenticationError):
    """
    User account disabled.
    """

    default_message = "Account has been disabled."

class AccountSuspendedError(AccountStatusError):
    """
    Raised when a suspended user account attempts authentication or
    authorization.

    Suspended accounts remain in the system but are temporarily prohibited
    from accessing protected resources until reinstated.
    """


class AccountArchivedError(AccountStatusError):
    """
    Raised when an archived user account attempts authentication or
    authorization.

    Archived accounts are retained for historical or compliance purposes but
    are permanently excluded from active system access.
    """

class PasswordExpiredError(AuthenticationError):
    """
    Password must be changed.
    """

    default_message = "Password has expired."


class PasswordReuseError(AuthenticationError):
    """
    Password reuse detected.
    """

    default_message = "Password has been used previously."

class AccountInactiveError(AuthenticationError):
    """
    User account is inactive.
    """

    default_message = "Account is inactive."


class UserNotFoundError(AuthenticationError):
    """
    User could not be resolved.
    """

    default_message = "User not found."


# ============================================================================
# Password Reset
# ============================================================================


class PasswordResetError(AuthenticationError):
    """
    Base password reset exception.
    """

    default_message = "Password reset failed."


class InvalidPasswordResetTokenError(PasswordResetError):
    """
    Reset token invalid.
    """

    default_message = "Invalid password reset token."


class ExpiredPasswordResetTokenError(PasswordResetError):
    """
    Reset token expired.
    """

    default_message = "Password reset token has expired."


class UsedPasswordResetTokenError(PasswordResetError):
    """
    Reset token already used.
    """

    default_message = "Password reset token has already been used."


# ============================================================================
# Authorization Errors
# ============================================================================


class PermissionDeniedError(AuthorizationError):
    """
    Required permission missing.
    """

    default_message = "Permission denied."


class RoleRequiredError(AuthorizationError):
    """
    Required role missing.
    """

    default_message = "Required role not assigned."


class TenantAccessDeniedError(AuthorizationError):
    """
    User attempted cross-tenant access.
    """

    default_message = "Tenant access denied."


class BranchAccessDeniedError(AuthorizationError):
    """
    User attempted unauthorized branch access.
    """

    default_message = "Branch access denied."


# ============================================================================
# Configuration Errors
# ============================================================================


class AuthenticationConfigurationError(RuntimeError):
    """
    Authentication subsystem is misconfigured.
    """

    default_message = "Authentication configuration error."

    def __init__(self, message: str | None = None):
        super().__init__(message or self.default_message)


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    "AuthenticationError",
    "AuthorizationError",
    "InvalidCredentialsError",
    "InvalidTokenError",
    "InvalidAccessTokenError",
    "InvalidRefreshTokenError",
    "ExpiredTokenError",
    "RevokedTokenError",
    "InvalidTokenTypeError",
    "MissingTokenError",
    "SessionError",
    "SessionExpiredError",
    "SessionRevokedError",
    "SessionNotFoundError",
    "AccountLockedError",
    "AccountDisabledError",
    "PasswordExpiredError",
    "PasswordReuseError",
    "PasswordResetError",
    "InvalidPasswordResetTokenError",
    "ExpiredPasswordResetTokenError",
    "UsedPasswordResetTokenError",
    "PermissionDeniedError",
    "RoleRequiredError",
    "TenantAccessDeniedError",
    "BranchAccessDeniedError",
    "AuthenticationConfigurationError",
]