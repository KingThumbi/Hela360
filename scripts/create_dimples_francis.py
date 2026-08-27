from __future__ import annotations

from sqlalchemy import inspect

from dotenv import load_dotenv

load_dotenv("/home/thumbi/Hela360/.env")

from app import create_app
from app.extensions import db
from app.models import (
    Branch,
    Permission,
    Role,
    Tenant,
    User,
    UserPermission,
)
from app.services.tenant.auth.password_service import (
    hash_password,
)


# ============================================================================
# Source authorization template
# ============================================================================

SOURCE_TENANT_ID = "b5a256f7-8bec-4c40-b048-91c23749390b"
SOURCE_USERNAME = "cashier2"


# ============================================================================
# Target Dimples account
# ============================================================================

TARGET_TENANT_ID = "c99e5eb7-6d56-4024-ae1d-5782daeed340"
TARGET_BRANCH_ID = "7a0eed0f-6564-4ec7-b82a-61490d96c433"

TARGET_USERNAME = "francis"
TARGET_EMAIL = "francis@dimplespharmacy.com"
TARGET_PASSWORD = "Francis@2026"


# ============================================================================
# Helpers
# ============================================================================

SYSTEM_COLUMNS = {
    "id",
    "created_at",
    "updated_at",
}


def copy_scalar_columns(
    source,
    target,
    *,
    exclude: set[str] | None = None,
) -> None:
    excluded = SYSTEM_COLUMNS | (exclude or set())

    for column in inspect(type(source)).columns:
        name = column.key

        if name in excluded:
            continue

        if not hasattr(target, name):
            continue

        setattr(
            target,
            name,
            getattr(source, name),
        )


def permission_for_target(
    source_permission: Permission,
) -> Permission:
    """
    Resolve a Permission equivalent for the target tenant.

    Supports either:
    - globally shared Permission rows; or
    - tenant-owned Permission rows.
    """

    mapper = inspect(Permission)
    column_names = {
        column.key
        for column in mapper.columns
    }

    # ------------------------------------------------------------------------
    # Global permission catalogue
    # ------------------------------------------------------------------------

    if "tenant_id" not in column_names:
        return source_permission

    # ------------------------------------------------------------------------
    # Tenant-owned permission catalogue
    # ------------------------------------------------------------------------

    target_permission = (
        Permission.query
        .filter_by(
            tenant_id=TARGET_TENANT_ID,
            code=source_permission.code,
        )
        .first()
    )

    if target_permission is not None:
        return target_permission

    target_permission = Permission()

    copy_scalar_columns(
        source_permission,
        target_permission,
        exclude={
            "tenant_id",
        },
    )

    target_permission.tenant_id = TARGET_TENANT_ID

    db.session.add(target_permission)
    db.session.flush()

    print(
        "CREATED PERMISSION:",
        target_permission.code,
    )

    return target_permission


# ============================================================================
# Bootstrap
# ============================================================================

def main() -> None:
    app = create_app()

    with app.app_context():
        try:
            # ----------------------------------------------------------------
            # Validate target tenant + branch
            # ----------------------------------------------------------------

            tenant = db.session.get(
                Tenant,
                TARGET_TENANT_ID,
            )

            if tenant is None:
                raise RuntimeError(
                    "Dimples Pharmacy tenant was not found."
                )

            branch = db.session.get(
                Branch,
                TARGET_BRANCH_ID,
            )

            if branch is None:
                raise RuntimeError(
                    "Dimples Roysambu branch was not found."
                )

            if str(branch.tenant_id) != TARGET_TENANT_ID:
                raise RuntimeError(
                    "Target branch does not belong to "
                    "Dimples Pharmacy Limited."
                )

            # ----------------------------------------------------------------
            # Source cashier
            # ----------------------------------------------------------------

            source_user = (
                User.query
                .filter_by(
                    tenant_id=SOURCE_TENANT_ID,
                    username=SOURCE_USERNAME,
                )
                .first()
            )

            if source_user is None:
                raise RuntimeError(
                    "Demo cashier2 was not found."
                )

            source_cashier_role = next(
                (
                    role
                    for role in source_user.roles
                    if role.code == "cashier"
                ),
                None,
            )

            if source_cashier_role is None:
                raise RuntimeError(
                    "Demo cashier2 does not have "
                    "the cashier role."
                )

            # ----------------------------------------------------------------
            # Target Cashier role
            # ----------------------------------------------------------------

            target_role = (
                Role.query
                .filter_by(
                    tenant_id=TARGET_TENANT_ID,
                    code="cashier",
                )
                .first()
            )

            if target_role is None:
                target_role = Role()

                copy_scalar_columns(
                    source_cashier_role,
                    target_role,
                    exclude={
                        "tenant_id",
                    },
                )

                target_role.tenant_id = TARGET_TENANT_ID

                db.session.add(target_role)
                db.session.flush()

                print("CREATED ROLE: cashier")

            # ----------------------------------------------------------------
            # Clone role permissions
            # ----------------------------------------------------------------

            target_role_permissions = []

            for source_permission in source_cashier_role.permissions:
                target_permission = permission_for_target(
                    source_permission,
                )

                target_role_permissions.append(
                    target_permission
                )

            target_role.permissions = target_role_permissions

            # ----------------------------------------------------------------
            # Prevent duplicate Francis account
            # ----------------------------------------------------------------

            existing = (
                User.query
                .filter(
                    User.tenant_id == TARGET_TENANT_ID,
                    (
                        (User.username == TARGET_USERNAME)
                        | (User.email == TARGET_EMAIL)
                    ),
                )
                .first()
            )

            if existing is not None:
                raise RuntimeError(
                    "Francis already exists in the "
                    "Dimples tenant."
                )

            # ----------------------------------------------------------------
            # Create Francis using cashier2 as a safe model template
            # ----------------------------------------------------------------

            francis = User()

            copy_scalar_columns(
                source_user,
                francis,
                exclude={
                    "tenant_id",
                    "branch_id",
                    "username",
                    "email",
                    "password_hash",
                },
            )

            francis.tenant_id = TARGET_TENANT_ID
            francis.branch_id = TARGET_BRANCH_ID

            francis.username = TARGET_USERNAME
            francis.email = TARGET_EMAIL
            francis.password_hash = hash_password(
                TARGET_PASSWORD
            )

            # Defensive normalization for fields that exist in this model.
            if hasattr(francis, "is_active"):
                francis.is_active = True

            if hasattr(francis, "is_disabled"):
                francis.is_disabled = False

            if hasattr(francis, "is_locked"):
                francis.is_locked = False

            if hasattr(francis, "is_owner"):
                francis.is_owner = False

            if hasattr(francis, "is_platform_admin"):
                francis.is_platform_admin = False

            if hasattr(francis, "status"):
                francis.status = "active"

            francis.roles = [
                target_role,
            ]

            db.session.add(francis)
            db.session.flush()

            print(
                "CREATED USER:",
                francis.username,
            )

            # ----------------------------------------------------------------
            # Clone cashier2 direct permission overrides
            # ----------------------------------------------------------------

            source_overrides = (
                UserPermission.query
                .filter_by(
                    user_id=str(source_user.id),
                )
                .all()
            )

            for source_override in source_overrides:
                source_permission = getattr(
                    source_override,
                    "permission",
                    None,
                )

                if source_permission is None:
                    source_permission = db.session.get(
                        Permission,
                        source_override.permission_id,
                    )

                if source_permission is None:
                    raise RuntimeError(
                        "A cashier2 permission override "
                        "references a missing permission."
                    )

                target_permission = permission_for_target(
                    source_permission,
                )

                target_override = UserPermission()

                copy_scalar_columns(
                    source_override,
                    target_override,
                    exclude={
                        "tenant_id",
                        "user_id",
                        "permission_id",
                    },
                )

                if hasattr(
                    target_override,
                    "tenant_id",
                ):
                    target_override.tenant_id = (
                        TARGET_TENANT_ID
                    )

                target_override.user_id = str(
                    francis.id
                )

                target_override.permission_id = str(
                    target_permission.id
                )

                db.session.add(
                    target_override
                )

                print(
                    "CLONED OVERRIDE:",
                    target_permission.code,
                )

            # ----------------------------------------------------------------
            # Commit
            # ----------------------------------------------------------------

            db.session.commit()

            print()
            print("=" * 76)
            print("DIMPLES CASHIER CREATED")
            print("=" * 76)

            print("User ID:    ", francis.id)
            print("Username:   ", francis.username)
            print("Email:      ", francis.email)
            print("Tenant ID:  ", francis.tenant_id)
            print("Branch ID:  ", francis.branch_id)
            print("Role:       ", target_role.name)
            print()
            print(
                "Temporary password:",
                TARGET_PASSWORD,
            )

            print()
            print("ROLE PERMISSIONS")
            print("-" * 76)

            for permission in sorted(
                target_role.permissions,
                key=lambda item: item.code,
            ):
                print(
                    " -",
                    permission.code,
                )

            print()
            print("DIRECT OVERRIDES")
            print("-" * 76)

            overrides = (
                UserPermission.query
                .filter_by(
                    user_id=str(francis.id),
                )
                .all()
            )

            if not overrides:
                print("(none)")
            else:
                for override in overrides:
                    permission = db.session.get(
                        Permission,
                        override.permission_id,
                    )

                    print(
                        " -",
                        permission.code
                        if permission
                        else override.permission_id,
                    )

            print()
            print(
                "DIMPLES FRANCIS CREATION: PASS"
            )

        except Exception:
            db.session.rollback()
            raise


if __name__ == "__main__":
    main()
