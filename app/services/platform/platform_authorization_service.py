"""
Hela360 Platform Authorization Service
======================================

Canonical authorization resolution for Hela360 Office identities.

Architectural boundaries
------------------------
* Operates only on PlatformUser, PlatformRole and PlatformPermission records.
* Never reads tenant User, Role or Permission records.
* Carries no tenant or branch scope.
* Authorization derives from persisted platform role assignments.
* The canonical "*" permission grants the platform-wide system override.
* Authorization contexts contain no ORM instances.
* No JWT creation, session management or authentication workflow.
* No commits or rollbacks are performed.

Transaction ownership remains with the caller.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.auth.exceptions import (
    AccountInactiveError,
    PermissionDeniedError,
    UserNotFoundError,
)
from app.models import PlatformUser
from app.services.platform.platform_permission_policy import (
    SYSTEM_PERMISSION,
    is_valid_platform_permission,
)


@dataclass(
    frozen=True,
    slots=True,
)
class PlatformAuthorizationContext:
    """
    Immutable effective authorization context for one PlatformUser.
    """

    platform_user_id: str
    roles: tuple[str, ...]
    permissions: tuple[str, ...]

    @property
    def has_global_override(
        self,
    ) -> bool:
        """Return whether the canonical system override is effective."""

        return (
            SYSTEM_PERMISSION
            in self.permissions
        )

    def has_permission(
        self,
        permission: str,
    ) -> bool:
        """
        Evaluate one canonical platform permission against this context.
        """

        normalized = str(
            permission or ""
        ).strip()

        if not normalized:
            return False

        if not is_valid_platform_permission(
            normalized
        ):
            return False

        return (
            self.has_global_override
            or normalized
            in self.permissions
        )

    def has_any_permission(
        self,
        permissions: tuple[str, ...]
        | list[str]
        | set[str]
        | frozenset[str],
    ) -> bool:
        """Return whether any requested permission is effective."""

        return any(
            self.has_permission(permission)
            for permission in permissions
        )

    def has_all_permissions(
        self,
        permissions: tuple[str, ...]
        | list[str]
        | set[str]
        | frozenset[str],
    ) -> bool:
        """Return whether every requested permission is effective."""

        return all(
            self.has_permission(permission)
            for permission in permissions
        )


class PlatformAuthorizationService:
    """
    Resolve and enforce Hela360 Office authorization.

    Platform authorization is independent of tenant authorization.
    """

    def __init__(
        self,
        session,
    ) -> None:
        self.session = session

    def context_for_user(
        self,
        platform_user_id: str,
    ) -> PlatformAuthorizationContext:
        """
        Resolve the effective authorization context for one PlatformUser.

        Raises
        ------
        UserNotFoundError
            When the platform identity does not exist.

        AccountInactiveError
            When the platform identity is disabled.
        """

        user = self.session.get(
            PlatformUser,
            platform_user_id,
        )

        if user is None:
            raise UserNotFoundError(
                "Platform user not found."
            )

        if user.is_active is not True:
            raise AccountInactiveError(
                "Platform user is inactive."
            )

        roles = tuple(
            sorted(
                {
                    str(role.code)
                    for role in user.roles
                }
            )
        )

        permissions = tuple(
            sorted(
                {
                    str(permission.code)
                    for role in user.roles
                    for permission
                    in role.permissions
                }
            )
        )

        return PlatformAuthorizationContext(
            platform_user_id=str(
                user.id
            ),
            roles=roles,
            permissions=permissions,
        )

    def roles_for_user(
        self,
        platform_user_id: str,
    ) -> tuple[str, ...]:
        """Return effective platform role codes."""

        return self.context_for_user(
            platform_user_id
        ).roles

    def permissions_for_user(
        self,
        platform_user_id: str,
    ) -> tuple[str, ...]:
        """Return effective platform permission codes."""

        return self.context_for_user(
            platform_user_id
        ).permissions

    def has_permission(
        self,
        platform_user_id: str,
        permission: str,
    ) -> bool:
        """Return whether the user satisfies one platform permission."""

        normalized = self._require_permission_code(
            permission
        )

        return self.context_for_user(
            platform_user_id
        ).has_permission(
            normalized
        )

    def has_any_permission(
        self,
        platform_user_id: str,
        permissions: tuple[str, ...]
        | list[str]
        | set[str]
        | frozenset[str],
    ) -> bool:
        """Return whether the user satisfies any requested permission."""

        normalized = tuple(
            self._require_permission_code(
                permission
            )
            for permission in permissions
        )

        return self.context_for_user(
            platform_user_id
        ).has_any_permission(
            normalized
        )

    def has_all_permissions(
        self,
        platform_user_id: str,
        permissions: tuple[str, ...]
        | list[str]
        | set[str]
        | frozenset[str],
    ) -> bool:
        """Return whether the user satisfies every requested permission."""

        normalized = tuple(
            self._require_permission_code(
                permission
            )
            for permission in permissions
        )

        return self.context_for_user(
            platform_user_id
        ).has_all_permissions(
            normalized
        )

    def require_permission(
        self,
        platform_user_id: str,
        permission: str,
    ) -> PlatformAuthorizationContext:
        """
        Require one platform permission and return the resolved context.
        """

        normalized = self._require_permission_code(
            permission
        )

        context = self.context_for_user(
            platform_user_id
        )

        if context.has_permission(
            normalized
        ):
            return context

        raise PermissionDeniedError(
            "Platform permission required: "
            f"{normalized}"
        )

    @staticmethod
    def _require_permission_code(
        permission: str,
    ) -> str:
        """
        Normalize and validate a canonical platform permission code.

        Rejecting unknown codes prevents authorization typos from silently
        becoming policy.
        """

        normalized = str(
            permission or ""
        ).strip()

        if not normalized:
            raise ValueError(
                "Platform permission is required."
            )

        if not is_valid_platform_permission(
            normalized
        ):
            raise ValueError(
                "Unknown platform permission: "
                f"{normalized}"
            )

        return normalized


__all__ = [
    "PlatformAuthorizationContext",
    "PlatformAuthorizationService",
]
