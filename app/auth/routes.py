"""
Authentication API

Enterprise authentication endpoints for Hela360.

Responsibilities
----------------
- Login
- Refresh access tokens
- Logout
- Logout all sessions
- Current authenticated user
- Session validation

Business logic is delegated entirely to AuthenticationService.
"""

from __future__ import annotations

from dataclasses import asdict

from flask import g
from flask import jsonify
from flask import request

from app.auth import bp
from app.auth.decorators import login_required
from app.auth.exceptions import (
    AccountDisabledError,
    AccountInactiveError,
    AccountLockedError,
    AccountSuspendedError,
    AuthenticationError,
    InvalidCredentialsError,
)
from app.auth.jwt import access_token_expires_in
from app.auth.jwt import get_current_identity
from app.auth.jwt import refresh_token_expires_in
from app.auth.schemas import LoginRequest
from app.auth.schemas import LoginResponse
from app.auth.schemas import RefreshTokenRequest
from app.auth.schemas import RefreshTokenResponse
from app.services.platform.tenant_resolution_service import (
    TenantResolutionError,
    tenant_resolution_service,
)
from app.services.tenant.auth.authentication_service import (
    authentication_service,
)
from app.services.tenant.auth.current_session_service import (
    current_session_service,
)

# =============================================================================
# Helpers
# =============================================================================


def _client_ip() -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")

    if forwarded:
        return forwarded.split(",")[0].strip()

    return request.remote_addr


def _user_agent() -> str | None:
    return request.headers.get("User-Agent")


def _device_name() -> str | None:
    return request.headers.get("X-Device-Name")


def _json_error(message: str, status: int):
    return jsonify(
        {
            "ok": False,
            "message": message,
        }
    ), status

@bp.post("/login")
def login():
    """
    Authenticate a user and issue JWT tokens.
    """

    payload = request.get_json(silent=True) or {}

    workspace = str(
        payload.get("workspace") or ""
    ).strip()

    email = str(
        payload.get("email") or ""
    ).strip()

    password = str(
        payload.get("password") or ""
    )

    if not workspace:
        return _json_error(
            "workspace is required.",
            400,
        )

    if not email:
        return _json_error(
            "email is required.",
            400,
        )

    if not password:
        return _json_error(
            "password is required.",
            400,
        )

    login_request = LoginRequest(
        workspace=workspace,
        email=email,
        password=password,
        branch_id=payload.get("branch_id"),
        remember_me=payload.get(
            "remember_me",
            False,
        ),
        device_name=payload.get(
            "device_name",
        ),
    )

    try:
        tenant = (
            tenant_resolution_service
            .resolve_workspace(
                login_request.workspace,
            )
        )

        result = authentication_service.login(
            tenant_id=tenant.id,
            username_or_email=login_request.email,
            password=login_request.password,
            device_name=login_request.device_name,
            ip_address=_client_ip(),
            user_agent=_user_agent(),
        )

        response = LoginResponse(
            access_token=result.access_token,
            refresh_token=result.refresh_token,
            access_expires_in=access_token_expires_in(),
            refresh_expires_in=refresh_token_expires_in(),
        )

        return jsonify(asdict(response)), 200

    except TenantResolutionError:
        return _json_error(
            "Invalid username or password.",
            401,
        )

    except InvalidCredentialsError as exc:
        return _json_error(str(exc), 401)

    except AccountLockedError as exc:
        return _json_error(str(exc), 423)

    except (
        AccountInactiveError,
        AccountDisabledError,
        AccountSuspendedError,
    ) as exc:
        return _json_error(str(exc), 403)

    except AuthenticationError as exc:
        return _json_error(str(exc), 401)

@bp.post("/refresh")
def refresh():
    """
    Rotate a refresh token and issue a replacement JWT pair.
    """

    payload = request.get_json(silent=True) or {}

    refresh_request = RefreshTokenRequest(
        refresh_token=payload["refresh_token"],
    )

    try:
        result = authentication_service.refresh(
            refresh_token=refresh_request.refresh_token,
            ip_address=_client_ip(),
            user_agent=_user_agent(),
        )

        response = RefreshTokenResponse(
            access_token=result.access_token,
            refresh_token=result.refresh_token,
            access_expires_in=access_token_expires_in(),
            refresh_expires_in=refresh_token_expires_in(),
        )

        return jsonify(asdict(response)), 200

    except AuthenticationError as exc:
        return _json_error(str(exc), 401)

@bp.get("/session")
@login_required
def current_session():
    """
    Return the current authenticated session identity and tenancy context.
    """

    return jsonify(
        {
            "session": asdict(
                current_session_service.get_current_session(
                    g.identity,
                )
            ),
        }
    ), 200
