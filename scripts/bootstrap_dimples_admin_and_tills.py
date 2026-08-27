"""
Dimples Pharmacy Operational Bootstrap
======================================

Idempotent operational bootstrap for the existing Dimples Pharmacy tenant.

Responsibilities
----------------
- Validate the Dimples tenant, Roysambu branch and warehouse.
- Provision the configured Roysambu tills.
- Synchronize Hela360's canonical permission catalogue.
- Synchronize canonical built-in tenant roles.
- Create or repair the Dimples tenant administrator.
- Assign the canonical tenant Administrator role.

Architectural boundaries
------------------------
- Hela360 platform/back-office administration is outside this script.
- Tenant authorization policy comes from Hela360's canonical IAM policy.
- No authorization policy is copied from another tenant.
- No user is cloned from another operational user.
- Existing administrator credentials are preserved.
"""

from __future__ import annotations

from dotenv import load_dotenv
from sqlalchemy import select

load_dotenv("/home/thumbi/Hela360/.env")

from app import create_app
from app.extensions import db
from app.models import (
    Branch,
    Role,
    Tenant,
    Till,
    User,
    Warehouse,
)
from app.services.platform.permission_catalogue_service import (
    PermissionCatalogueService,
)
from app.services.platform.system_role_policy import (
    TENANT_ADMINISTRATOR_ROLE,
)
from app.services.platform.system_role_provisioning_service import (
    SystemRoleProvisioningService,
)
from app.services.tenant.auth.password_service import (
    hash_password,
)


# ============================================================================
# Tenant configuration
# ============================================================================

DIMPLES_TENANT_ID = "c99e5eb7-6d56-4024-ae1d-5782daeed340"
DIMPLES_BRANCH_ID = "7a0eed0f-6564-4ec7-b82a-61490d96c433"
DIMPLES_WAREHOUSE_ID = "e81b0b5d-14f6-46c1-b4aa-f037e680364c"


# ============================================================================
# Administrator
# ============================================================================

ADMIN_USERNAME = "michael"
ADMIN_EMAIL = "michael@dimplespharmacy.com"

ADMIN_FIRST_NAME = "Michael"
ADMIN_LAST_NAME = "Karanja"

# Initial credential only.
#
# This value is used only when the administrator does not yet exist.
# Re-running this bootstrap MUST NOT reset an existing administrator password.
ADMIN_INITIAL_PASSWORD = "Michael@2026"


# ============================================================================
# Tills
# ============================================================================

TILLS = (
    {
        "code": "ROY-TILL-01",
        "name": "Roysambu Till 1",
    },
    {
        "code": "ROY-TILL-02",
        "name": "Roysambu Till 2",
    },
)


# ============================================================================
# Till provisioning
# ============================================================================


def provision_tills() -> list[Till]:
    """
    Create or synchronize the configured Dimples Roysambu tills.
    """

    tills: list[Till] = []

    for definition in TILLS:
        till = db.session.scalar(
            select(Till).where(
                Till.tenant_id == DIMPLES_TENANT_ID,
                Till.branch_id == DIMPLES_BRANCH_ID,
                Till.code == definition["code"],
            )
        )

        if till is None:
            till = Till(
                tenant_id=DIMPLES_TENANT_ID,
                branch_id=DIMPLES_BRANCH_ID,
                warehouse_id=DIMPLES_WAREHOUSE_ID,
                code=definition["code"],
                name=definition["name"],
                is_active=True,
            )

            db.session.add(till)
            db.session.flush()

            print(
                "CREATED TILL:",
                till.code,
            )

        else:
            till.name = definition["name"]
            till.warehouse_id = DIMPLES_WAREHOUSE_ID
            till.is_active = True

            print(
                "TILL ALREADY EXISTS:",
                till.code,
            )

        tills.append(till)

    return tills


# ============================================================================
# Canonical IAM provisioning
# ============================================================================


def provision_canonical_iam() -> Role:
    """
    Synchronize Hela360's canonical tenant IAM policy for Dimples.

    Permission definitions and built-in tenant roles originate from Hela360's
    canonical policy modules. No other tenant is used as a template.
    """

    permission_result = PermissionCatalogueService(
        db.session
    ).synchronize()

    print()
    print("PERMISSION CATALOGUE")
    print("-" * 76)
    print(
        "Created:   ",
        len(permission_result.created),
    )
    print(
        "Updated:   ",
        len(permission_result.updated),
    )
    print(
        "Unchanged: ",
        len(permission_result.unchanged),
    )
    print(
        "Unexpected:",
        len(permission_result.unexpected),
    )

    role_result = SystemRoleProvisioningService(
        db.session
    ).synchronize(
        tenant_id=DIMPLES_TENANT_ID,
    )

    print()
    print("SYSTEM ROLES")
    print("-" * 76)

    for item in role_result.roles:
        print(
            item.code,
            "| created:",
            item.created,
            "| metadata updated:",
            item.metadata_updated,
            "| permissions added:",
            len(item.permissions_added),
            "| permissions removed:",
            len(item.permissions_removed),
        )

    admin_role = db.session.scalar(
        select(Role).where(
            Role.tenant_id == DIMPLES_TENANT_ID,
            Role.code == TENANT_ADMINISTRATOR_ROLE.code,
        )
    )

    if admin_role is None:
        raise RuntimeError(
            "Canonical tenant Administrator role was not provisioned."
        )

    return admin_role


# ============================================================================
# Administrator provisioning
# ============================================================================


def provision_administrator(
    *,
    admin_role: Role,
) -> User:
    """
    Create or repair the Dimples tenant administrator.

    Existing credentials are intentionally preserved. The initial password is
    set only when creating the administrator for the first time.
    """

    user = db.session.scalar(
        select(User).where(
            User.tenant_id == DIMPLES_TENANT_ID,
            (
                (User.username == ADMIN_USERNAME)
                | (User.email == ADMIN_EMAIL)
            ),
        )
    )

    if user is None:
        user = User(
            tenant_id=DIMPLES_TENANT_ID,
            branch_id=DIMPLES_BRANCH_ID,
            username=ADMIN_USERNAME,
            email=ADMIN_EMAIL,
            first_name=ADMIN_FIRST_NAME,
            last_name=ADMIN_LAST_NAME,
            password_hash=hash_password(
                ADMIN_INITIAL_PASSWORD
            ),
            is_owner=False,
            is_active=True,
        )

        user.roles = [
            admin_role,
        ]

        db.session.add(user)
        db.session.flush()

        print(
            "CREATED TENANT ADMINISTRATOR:",
            user.username,
        )

        return user

    # ------------------------------------------------------------------
    # Existing administrator repair
    # ------------------------------------------------------------------

    user.username = ADMIN_USERNAME
    user.email = ADMIN_EMAIL
    user.first_name = ADMIN_FIRST_NAME
    user.last_name = ADMIN_LAST_NAME
    user.branch_id = DIMPLES_BRANCH_ID
    user.is_active = True

    # Tenant Administrator and Hela360 platform administrator are separate
    # concepts. Do not manufacture a platform/owner bypass here.
    user.is_owner = False

    if admin_role not in user.roles:
        user.roles.append(admin_role)

    db.session.flush()

    print(
        "TENANT ADMINISTRATOR ALREADY EXISTS; REPAIRED:",
        user.username,
    )

    return user


# ============================================================================
# Bootstrap
# ============================================================================


def main() -> None:
    app = create_app()

    with app.app_context():
        try:
            tenant = db.session.get(
                Tenant,
                DIMPLES_TENANT_ID,
            )

            branch = db.session.get(
                Branch,
                DIMPLES_BRANCH_ID,
            )

            warehouse = db.session.get(
                Warehouse,
                DIMPLES_WAREHOUSE_ID,
            )

            if tenant is None:
                raise RuntimeError(
                    "Dimples tenant not found."
                )

            if branch is None:
                raise RuntimeError(
                    "Dimples Roysambu branch not found."
                )

            if warehouse is None:
                raise RuntimeError(
                    "Dimples Roysambu warehouse not found."
                )

            if str(branch.tenant_id) != DIMPLES_TENANT_ID:
                raise RuntimeError(
                    "Branch does not belong to Dimples."
                )

            if str(warehouse.tenant_id) != DIMPLES_TENANT_ID:
                raise RuntimeError(
                    "Warehouse does not belong to Dimples."
                )

            # --------------------------------------------------------------
            # Operational resources
            # --------------------------------------------------------------

            tills = provision_tills()

            # --------------------------------------------------------------
            # Canonical tenant IAM
            # --------------------------------------------------------------

            admin_role = provision_canonical_iam()

            administrator = provision_administrator(
                admin_role=admin_role,
            )

            db.session.commit()

            # --------------------------------------------------------------
            # Result
            # --------------------------------------------------------------

            print()
            print("=" * 76)
            print("DIMPLES PHARMACY OPERATIONAL BOOTSTRAP")
            print("=" * 76)

            print()
            print("TENANT")
            print("-" * 76)
            print(
                "Name:       ",
                tenant.legal_name,
            )
            print(
                "Workspace:  ",
                tenant.workspace_slug,
            )
            print(
                "Branch:     ",
                branch.name,
            )
            print(
                "Warehouse:  ",
                warehouse.name,
            )

            print()
            print("TILLS")
            print("-" * 76)

            for till in tills:
                print(
                    till.code,
                    "|",
                    till.name,
                    "|",
                    till.id,
                )

            print()
            print("TENANT ADMINISTRATOR")
            print("-" * 76)
            print(
                "User ID:    ",
                administrator.id,
            )
            print(
                "Username:   ",
                administrator.username,
            )
            print(
                "Email:      ",
                administrator.email,
            )
            print(
                "Name:       ",
                f"{administrator.first_name} "
                f"{administrator.last_name or ''}".strip(),
            )
            print(
                "Role:       ",
                admin_role.name,
            )
            print(
                "Role code:  ",
                admin_role.code,
            )
            print(
                "Tenant ID:  ",
                administrator.tenant_id,
            )
            print(
                "Branch ID:  ",
                administrator.branch_id,
            )

            print()
            print("ROLE PERMISSIONS")
            print("-" * 76)

            for permission in sorted(
                admin_role.permissions,
                key=lambda item: item.code,
            ):
                print(
                    " -",
                    permission.code,
                )

            print()
            print("DIMPLES BOOTSTRAP: PASS")

        except Exception:
            db.session.rollback()
            raise


if __name__ == "__main__":
    main()
