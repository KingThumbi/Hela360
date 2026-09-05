"""
Hela360 Platform Authentication Decorators
==========================================

Request authentication for Hela360 Office.

Architectural boundaries
------------------------
* Accepts Platform access JWTs only.
* Never resolves tenant JWT Identity.
* Never reads tenant UserSession.
* Requires an active PlatformSession.
* Resolves authorization from current persisted Platform IAM state.
* Stores request-scoped Platform identity on flask.g.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from functools import wraps
from typing import Callable, TypeVar

from flask import g

from app.auth.exceptions import (
    AccountInactiveError,
    MissingTokenError,
    SessionExpiredError,
    SessionNotFoundError,
    SessionRevokedError,
)
from app.auth.jwt import get_bearer_token
from app.extensions import db
from app.models import PlatformUser
from app.services.platform.platform_authentication_service import (
    PLATFORM_OFFICE_ACCESS_PERMISSION,
)
from app.services.platform.platform_authorization_service import (
    PlatformAuthorizationContext,
    PlatformAuthorizationService,
)
from app.services.platform.platform_jwt_service import (
    PlatformJWTService,
)
from app.services.platform.platform_session_service import (
    PlatformSessionService,
)


F = TypeVar(
    "F",
    bound=Callable,
)


@dataclass(
    frozen=True,
    slots=True,
)
class PlatformRequestIdentity:
    """
    Authenticated Hela360 Office request identity.

    Authorization is derived from current persisted Platform IAM state rather
    than trusting stale access-token permissions as the authorization boundary.
    """

    platform_user_id: str
    session_id: str
    authorization: PlatformAuthorizationContext


def get_current_platform_identity(
) -> PlatformRequestIdentity | None:
    """Return the request-scoped Platform identity when already resolved."""

    return getattr(
        g,
        "platform_identity",
        None,
    )


def resolve_platform_identity(
) -> PlatformRequestIdentity:
    """
    Resolve and validate the current Hela360 Office request identity.
    """

    token = get_bearer_token()

    if token is None:
        raise MissingTokenError()

    jwt_service = PlatformJWTService()

    payload = (
        jwt_service
        .decode_access_token(
            token
        )
    )

    platform_user_id = (
        jwt_service
        .extract_platform_user_id(
            payload
        )
    )

    session_id = (
        jwt_service
        .extract_session_id(
            payload
        )
    )

    session_service = (
        PlatformSessionService(
            db.session
        )
    )

    auth_session = (
        session_service.get(
            str(session_id)
        )
    )

    if auth_session is None:
        raise SessionNotFoundError()

    if (
        str(
            auth_session.platform_user_id
        )
        != str(
            platform_user_id
        )
    ):
        raise SessionNotFoundError(
            "Platform session ownership is invalid."
        )

    if auth_session.revoked_at is not None:
        raise SessionRevokedError()

    expires_at = (
        auth_session.expires_at
    )

    if expires_at.tzinfo is None:
        expires_at = (
            expires_at.replace(
                tzinfo=UTC
            )
        )

    if expires_at <= datetime.now(UTC):
        raise SessionExpiredError()

    user = db.session.get(
        PlatformUser,
        str(platform_user_id),
    )

    if user is None:
        raise SessionNotFoundError(
            "Platform identity no longer exists."
        )

    if user.is_active is not True:
        raise AccountInactiveError(
            "Platform user is inactive."
        )

    authorization = (
        PlatformAuthorizationService(
            db.session
        )
        .require_permission(
            str(platform_user_id),
            PLATFORM_OFFICE_ACCESS_PERMISSION,
        )
    )

    identity = PlatformRequestIdentity(
        platform_user_id=(
            str(platform_user_id)
        ),
        session_id=(
            str(session_id)
        ),
        authorization=(
            authorization
        ),
    )

    g.platform_identity = identity

    return identity


def platform_login_required(
    view: F,
) -> F:
    """Require a valid active Hela360 Office Platform identity."""

    @wraps(view)
    def wrapped(
        *args,
        **kwargs,
    ):
        resolve_platform_identity()

        return view(
            *args,
            **kwargs,
        )

    return wrapped  # type: ignore[return-value]


def require_platform_permission(
    permission: str,
):
    """
    Require one explicit canonical Platform permission.

    platform.office.access remains implicitly required by Platform identity
    resolution before action-specific authorization is evaluated.
    """

    def decorator(
        view: F,
    ) -> F:
        @wraps(view)
        def wrapped(
            *args,
            **kwargs,
        ):
            identity = (
                get_current_platform_identity()
            )

            if identity is None:
                identity = (
                    resolve_platform_identity()
                )

            PlatformAuthorizationService(
                db.session
            ).require_permission(
                identity.platform_user_id,
                permission,
            )

            return view(
                *args,
                **kwargs,
            )

        return wrapped  # type: ignore[return-value]

    return decorator


__all__ = [
    "PlatformRequestIdentity",
    "get_current_platform_identity",
    "platform_login_required",
    "require_platform_permission",
    "resolve_platform_identity",
]
