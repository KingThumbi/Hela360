"""
Hela360 Super Admin Provisioning Service
========================================

Provision the root Hela360 platform administrator used by Hela360 Office.

Architectural boundaries
------------------------
* Super Admin is a PlatformUser, never a tenant User.
* Super Admin authority derives from the canonical ``super_admin`` PlatformRole.
* Canonical platform permissions and roles are synchronized before assignment.
* Passwords are validated and hashed through Hela360's PasswordService.
* Existing credentials are never replaced implicitly.
* Transaction ownership remains with the caller.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, or_, select

from app.models import (
    PlatformRole,
    PlatformUser,
    PlatformUserRole,
)
from app.services.platform.platform_permission_catalogue_service import (
    PlatformPermissionCatalogueService,
)
from app.services.platform.platform_role_policy import (
    SUPER_ADMIN_ROLE,
)
from app.services.platform.platform_role_provisioning_service import (
    PlatformRoleProvisioningService,
)
from app.services.tenant.auth.password_service import (
    PasswordService,
    password_service,
)


class SuperAdminProvisioningError(ValueError):
    """Raised when Super Admin provisioning cannot proceed safely."""


@dataclass(frozen=True, slots=True)
class SuperAdminProvisioningResult:
    """Result of one Super Admin provisioning operation."""

    platform_user_id: str
    email: str
    username: str
    user_created: bool
    role_assigned: bool
    permissions_synchronized: bool
    roles_synchronized: bool

    @property
    def changed(self) -> bool:
        return (
            self.user_created
            or self.role_assigned
            or self.permissions_synchronized
            or self.roles_synchronized
        )


class SuperAdminService:
    """
    Provision Hela360's root platform administrator.

    Transaction ownership remains with the caller.
    """

    def __init__(
        self,
        session,
        *,
        passwords: PasswordService | None = None,
    ) -> None:
        self.session = session
        self.passwords = passwords or password_service

    def provision(
        self,
        *,
        email: str,
        username: str,
        first_name: str,
        password: str,
        last_name: str | None = None,
    ) -> SuperAdminProvisioningResult:
        """
        Create or reconcile the canonical Super Admin identity.

        Existing users are never assigned a new password implicitly.
        """

        email = self._normalize_email(email)
        username = self._normalize_username(username)
        first_name = self._required_text(
            first_name,
            "first_name",
        )
        last_name = self._optional_text(last_name)

        permission_result = (
            PlatformPermissionCatalogueService(
                self.session
            ).synchronize()
        )

        role_result = PlatformRoleProvisioningService(
            self.session
        ).synchronize()

        user = self._resolve_existing_user(
            email=email,
            username=username,
        )

        user_created = False

        if user is None:
            self._validate_password(password)

            user = PlatformUser(
                email=email,
                username=username,
                first_name=first_name,
                last_name=last_name,
                password_hash=(
                    self.passwords.hash_password(
                        password
                    )
                ),
                is_active=True,
            )

            self.session.add(user)
            self.session.flush()

            user_created = True

        role = self.session.scalar(
            select(PlatformRole).where(
                PlatformRole.code
                == SUPER_ADMIN_ROLE.code
            )
        )

        if role is None:
            raise RuntimeError(
                "Canonical Super Admin role was not "
                "persisted during synchronization."
            )

        role_assigned = self._ensure_role_assignment(
            user=user,
            role=role,
        )

        return SuperAdminProvisioningResult(
            platform_user_id=str(user.id),
            email=str(user.email),
            username=str(user.username),
            user_created=user_created,
            role_assigned=role_assigned,
            permissions_synchronized=(
                permission_result.changed
            ),
            roles_synchronized=role_result.changed,
        )

    def _resolve_existing_user(
        self,
        *,
        email: str,
        username: str,
    ) -> PlatformUser | None:
        """
        Resolve an existing platform identity safely.

        Email and username are treated case-insensitively for provisioning
        even though the current database uniqueness indexes are case-sensitive.
        """

        users = list(
            self.session.scalars(
                select(PlatformUser).where(
                    or_(
                        func.lower(
                            PlatformUser.email
                        ) == email.lower(),
                        func.lower(
                            PlatformUser.username
                        ) == username.lower(),
                    )
                )
            ).all()
        )

        if not users:
            return None

        if len(users) > 1:
            raise SuperAdminProvisioningError(
                "The supplied email and username resolve "
                "to different platform users."
            )

        user = users[0]

        email_matches = (
            str(user.email).strip().lower()
            == email.lower()
        )

        username_matches = (
            str(user.username).strip().lower()
            == username.lower()
        )

        if not email_matches:
            raise SuperAdminProvisioningError(
                "The username is already assigned to "
                "another platform user."
            )

        if not username_matches:
            raise SuperAdminProvisioningError(
                "The email is already assigned to "
                "another platform user."
            )

        return user

    def _ensure_role_assignment(
        self,
        *,
        user: PlatformUser,
        role: PlatformRole,
    ) -> bool:
        """Ensure the user holds the canonical Super Admin role."""

        assignment = self.session.get(
            PlatformUserRole,
            {
                "platform_user_id": user.id,
                "platform_role_id": role.id,
            },
        )

        if assignment is not None:
            return False

        self.session.add(
            PlatformUserRole(
                platform_user_id=user.id,
                platform_role_id=role.id,
                assigned_by_platform_user_id=None,
                assignment_reason=(
                    "Root platform administrator bootstrap."
                ),
            )
        )

        self.session.flush()

        return True

    def _validate_password(
        self,
        password: str,
    ) -> None:
        """Validate a new Super Admin password."""

        if not isinstance(password, str) or not password:
            raise SuperAdminProvisioningError(
                "password is required."
            )

        result = self.passwords.validate_password(
            password
        )

        if result.valid:
            return

        raise SuperAdminProvisioningError(
            "Password does not satisfy the Hela360 "
            "password policy: "
            + " ".join(result.errors)
        )

    @staticmethod
    def _normalize_email(
        value: str,
    ) -> str:
        email = str(value or "").strip().lower()

        if not email:
            raise SuperAdminProvisioningError(
                "email is required."
            )

        if "@" not in email:
            raise SuperAdminProvisioningError(
                "A valid email address is required."
            )

        return email

    @staticmethod
    def _normalize_username(
        value: str,
    ) -> str:
        username = str(value or "").strip().lower()

        if not username:
            raise SuperAdminProvisioningError(
                "username is required."
            )

        return username

    @staticmethod
    def _required_text(
        value: str,
        field_name: str,
    ) -> str:
        normalized = str(value or "").strip()

        if not normalized:
            raise SuperAdminProvisioningError(
                f"{field_name} is required."
            )

        return normalized

    @staticmethod
    def _optional_text(
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = str(value).strip()

        return normalized or None


__all__ = [
    "SuperAdminProvisioningError",
    "SuperAdminProvisioningResult",
    "SuperAdminService",
]
