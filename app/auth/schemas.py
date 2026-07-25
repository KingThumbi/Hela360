"""
Authentication Schemas

Strongly typed request and response models used by the authentication
service and API routes.

These dataclasses provide a clean contract between the API layer and the
authentication service without introducing external validation
dependencies.

Validation of HTTP payloads should occur in the route layer before
constructing these objects.

Hela360 Enterprise Pharmacy POS & ERP
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# =====================================================================
# Login
# =====================================================================

@dataclass(slots=True)
class LoginRequest:
    """Login request payload."""

    email: str
    password: str
    tenant_id: str | None = None
    branch_id: str | None = None
    remember_me: bool = False
    device_name: str | None = None


@dataclass(slots=True)
class LoginResponse:
    """
    Response returned after successful authentication.
    """

    access_token: str
    refresh_token: str

    access_expires_in: int
    refresh_expires_in: int

    token_type: str = "Bearer"
    
# =====================================================================
# Token Pair
# =====================================================================

@dataclass(slots=True)
class TokenPair:
    """
    Represents an issued JWT pair.

    Used internally by the authentication services before being
    transformed into API responses.
    """

    access_token: str
    refresh_token: str

    access_expires_in: int
    refresh_expires_in: int

    token_type: str = "Bearer"


@dataclass(slots=True)
class IssuedTokenPair:
    """
    Rich token information returned by JWTService.

    Includes JWT IDs and absolute expiry timestamps so higher-level
    services can persist refresh tokens, perform rotation, and audit
    authentication events.
    """

    access_token: str
    refresh_token: str

    access_jti: str
    refresh_jti: str

    access_expires_at: datetime
    refresh_expires_at: datetime

# =====================================================================
# Refresh Token
# =====================================================================

@dataclass(slots=True)
class RefreshTokenRequest:
    """Refresh access token request."""

    refresh_token: str


@dataclass(slots=True)
class RefreshTokenResponse:
    """
    Response returned after successful refresh-token rotation.

    A new access token and a new refresh token are issued on every
    successful refresh. Their respective lifetimes are returned so the
    client can manage token renewal without relying on hard-coded values.
    """

    access_token: str
    refresh_token: str

    access_expires_in: int
    refresh_expires_in: int

    token_type: str = "Bearer"

# =====================================================================
# Logout
# =====================================================================

@dataclass(slots=True)
class LogoutRequest:
    """Logout request."""

    refresh_token: str | None = None


# =====================================================================
# Password Change
# =====================================================================

@dataclass(slots=True)
class ChangePasswordRequest:
    """Authenticated password change."""

    current_password: str
    new_password: str


# =====================================================================
# Forgot Password
# =====================================================================

@dataclass(slots=True)
class ForgotPasswordRequest:
    """Forgot password request."""

    email: str


# =====================================================================
# Reset Password
# =====================================================================

@dataclass(slots=True)
class ResetPasswordRequest:
    """Reset password using reset token."""

    token: str
    new_password: str


# =====================================================================
# Authenticated User
# =====================================================================

@dataclass(slots=True)
class CurrentUserResponse:
    """Current authenticated user."""

    id: str
    email: str
    username: str | None
    first_name: str
    last_name: str

    tenant_id: str
    branch_id: str | None

    role: str | None
    permissions: list[str] = field(default_factory=list)

    is_owner: bool = False
    is_active: bool = True


# =====================================================================
# Generic API Response
# =====================================================================

@dataclass(slots=True)
class AuthResponse:
    """
    Generic authentication response.

    Can be used for logout, password changes,
    password reset confirmation, etc.
    """

    ok: bool
    message: str


# =====================================================================
# Error Response
# =====================================================================

@dataclass(slots=True)
class ErrorResponse:
    """Standard authentication error."""

    ok: bool = False
    error: str = ""
    code: str | None = None
    details: dict[str, Any] | None = None


# =====================================================================
# Module Exports
# =====================================================================

__all__ = [
    "LoginRequest",
    "LoginResponse",
    "TokenPair",
    "IssuedTokenPair",
    "RefreshTokenRequest",
    "RefreshTokenResponse",
    "LogoutRequest",
    "ChangePasswordRequest",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    "CurrentUserResponse",
    "AuthResponse",
    "ErrorResponse",
]