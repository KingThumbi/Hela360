"""
Hela360 Platform Authentication Routes
======================================

HTTP authentication lifecycle for Hela360 Office.

Endpoints
---------
POST /api/platform-auth/login
POST /api/platform-auth/refresh
POST /api/platform-auth/logout
POST /api/platform-auth/logout-all
GET  /api/platform-auth/session
"""

from __future__ import annotations

from flask import jsonify, request

from app.auth.exceptions import (
    AuthenticationError,
    AuthorizationError,
)
from app.extensions import db
from app.models import PlatformUser
from app.platform_auth import bp
from app.platform_auth.decorators import (
    get_current_platform_identity,
    platform_login_required,
)
from app.services.platform.platform_authentication_service import (
    PlatformAuthenticationService,
)
from app.services.platform.platform_session_service import (
    PlatformSessionService,
)


def _json_body() -> dict:
    """
    Return one JSON object request body.

    Invalid or non-object JSON is treated as an empty payload so route-level
    required-field validation remains deterministic.
    """

    payload = request.get_json(
        silent=True
    )

    if not isinstance(
        payload,
        dict,
    ):
        return {}

    return payload


def _required_text(
    payload: dict,
    field: str,
) -> str:
    """Resolve one required non-empty string field."""

    value = payload.get(
        field
    )

    if not isinstance(
        value,
        str,
    ):
        raise ValueError(
            f"{field} is required."
        )

    normalized = value.strip()

    if not normalized:
        raise ValueError(
            f"{field} is required."
        )

    return normalized


def _client_ip() -> str | None:
    """Return the request IP without trusting arbitrary forwarded chains."""

    return request.remote_addr


def _commit_security_state_and_reraise(
    exc: Exception,
) -> None:
    """
    Preserve intentional authentication-security mutations before propagating.

    Login failures may have created PlatformLoginAttempt evidence. Refresh
    failures may intentionally revoke compromised token families or sessions.
    These mutations are part of the security outcome and must survive the HTTP
    error response.
    """

    try:
        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    raise exc


@bp.post("/login")
def login():
    """Authenticate one Hela360 Office PlatformUser."""

    payload = _json_body()

    identifier = (
        payload.get(
            "username_or_email"
        )
        or payload.get(
            "email"
        )
        or payload.get(
            "username"
        )
    )

    if not isinstance(
        identifier,
        str,
    ) or not identifier.strip():
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": (
                            "VALIDATION_ERROR"
                        ),
                        "message": (
                            "username_or_email "
                            "is required."
                        ),
                    },
                }
            ),
            400,
        )

    try:
        password = _required_text(
            payload,
            "password",
        )

    except ValueError as exc:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": (
                            "VALIDATION_ERROR"
                        ),
                        "message": str(exc),
                    },
                }
            ),
            400,
        )

    service = (
        PlatformAuthenticationService(
            db.session
        )
    )

    try:
        result = service.login(
            username_or_email=(
                identifier
            ),
            password=password,
            device_name=(
                payload.get(
                    "device_name"
                )
                if isinstance(
                    payload.get(
                        "device_name"
                    ),
                    str,
                )
                else None
            ),
            ip_address=(
                _client_ip()
            ),
            user_agent=(
                request.user_agent.string
                or None
            ),
        )

        db.session.commit()

    except (
        AuthenticationError,
        AuthorizationError,
    ) as exc:
        _commit_security_state_and_reraise(
            exc
        )

    return jsonify(
        {
            "success": True,
            "access_token": (
                result.access_token
            ),
            "refresh_token": (
                result.refresh_token
            ),
            "token_type": "Bearer",
            "user": {
                "id": str(
                    result.user.id
                ),
                "email": (
                    result.user.email
                ),
                "username": (
                    result.user.username
                ),
                "first_name": (
                    result.user.first_name
                ),
                "last_name": (
                    result.user.last_name
                ),
            },
            "authorization": {
                "roles": list(
                    result
                    .authorization
                    .roles
                ),
                "permissions": list(
                    result
                    .authorization
                    .permissions
                ),
            },
            "session": {
                "id": str(
                    result.session.id
                ),
                "expires_at": (
                    result
                    .session
                    .expires_at
                    .isoformat()
                ),
            },
        }
    )


@bp.post("/refresh")
def refresh():
    """Rotate one Hela360 Office refresh token."""

    payload = _json_body()

    try:
        refresh_token = (
            _required_text(
                payload,
                "refresh_token",
            )
        )

    except ValueError as exc:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": (
                            "VALIDATION_ERROR"
                        ),
                        "message": str(exc),
                    },
                }
            ),
            400,
        )

    service = (
        PlatformAuthenticationService(
            db.session
        )
    )

    try:
        result = service.refresh(
            refresh_token=(
                refresh_token
            ),
            ip_address=(
                _client_ip()
            ),
            user_agent=(
                request.user_agent.string
                or None
            ),
        )

        db.session.commit()

    except (
        AuthenticationError,
        AuthorizationError,
    ) as exc:
        _commit_security_state_and_reraise(
            exc
        )

    return jsonify(
        {
            "success": True,
            "access_token": (
                result.access_token
            ),
            "refresh_token": (
                result.refresh_token
            ),
            "token_type": "Bearer",
        }
    )


@bp.post("/logout")
def logout():
    """Terminate one Hela360 Office authentication session."""

    payload = _json_body()

    try:
        refresh_token = (
            _required_text(
                payload,
                "refresh_token",
            )
        )

    except ValueError as exc:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": (
                            "VALIDATION_ERROR"
                        ),
                        "message": str(exc),
                    },
                }
            ),
            400,
        )

    service = (
        PlatformAuthenticationService(
            db.session
        )
    )

    try:
        result = service.logout(
            refresh_token=(
                refresh_token
            )
        )

        db.session.commit()

    except (
        AuthenticationError,
        AuthorizationError,
    ) as exc:
        _commit_security_state_and_reraise(
            exc
        )

    return jsonify(
        {
            "success": True,
            "session_id": (
                result
                .platform_session_id
            ),
        }
    )


@bp.post("/logout-all")
@platform_login_required
def logout_all():
    """Terminate every session belonging to the current PlatformUser."""

    identity = (
        get_current_platform_identity()
    )

    if identity is None:
        raise RuntimeError(
            "Platform identity was not resolved."
        )

    result = (
        PlatformAuthenticationService(
            db.session
        ).logout_all(
            platform_user_id=(
                identity
                .platform_user_id
            ),
        )
    )

    db.session.commit()

    return jsonify(
        {
            "success": True,
            "refresh_tokens_revoked": (
                result
                .refresh_tokens_revoked
            ),
            "sessions_revoked": (
                result
                .sessions_revoked
            ),
        }
    )


@bp.get("/session")
@platform_login_required
def current_session():
    """
    Return the current Hela360 Office identity, authorization and session.
    """

    identity = (
        get_current_platform_identity()
    )

    if identity is None:
        raise RuntimeError(
            "Platform identity was not resolved."
        )

    user = db.session.get(
        PlatformUser,
        identity.platform_user_id,
    )

    if user is None:
        raise AuthenticationError(
            "Platform user not found."
        )

    auth_session = (
        PlatformSessionService(
            db.session
        ).get_active(
            identity.session_id
        )
    )

    if auth_session is None:
        raise AuthenticationError(
            "Platform session is not active."
        )

    return jsonify(
        {
            "success": True,
            "user": {
                "id": str(
                    user.id
                ),
                "email": user.email,
                "username": (
                    user.username
                ),
                "first_name": (
                    user.first_name
                ),
                "last_name": (
                    user.last_name
                ),
                "is_active": (
                    user.is_active
                    is True
                ),
            },
            "authorization": {
                "roles": list(
                    identity
                    .authorization
                    .roles
                ),
                "permissions": list(
                    identity
                    .authorization
                    .permissions
                ),
            },
            "session": {
                "id": str(
                    auth_session.id
                ),
                "expires_at": (
                    auth_session
                    .expires_at
                    .isoformat()
                ),
                "last_activity_at": (
                    auth_session
                    .last_activity_at
                    .isoformat()
                    if auth_session
                    .last_activity_at
                    else None
                ),
            },
        }
    )
