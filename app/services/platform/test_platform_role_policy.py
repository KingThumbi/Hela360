from app.services.platform.platform_permission_policy import (
    ALL_PLATFORM_PERMISSIONS,
    SYSTEM_PERMISSION,
)
from app.services.platform.platform_role_policy import (
    AUDITOR_ROLE,
    CATALOGUE_MANAGER_ROLE,
    OFFICE_ADMIN_ROLE,
    SUPER_ADMIN_ROLE,
    SUPPLIER_INTELLIGENCE_MANAGER_ROLE,
    SYSTEM_PLATFORM_ROLES,
    TENANT_OPERATIONS_MANAGER_ROLE,
    get_platform_role,
)


def test_platform_role_codes_are_unique():
    codes = [
        role.code
        for role in SYSTEM_PLATFORM_ROLES
    ]

    assert len(codes) == len(set(codes))


def test_every_role_references_canonical_permissions():
    for role in SYSTEM_PLATFORM_ROLES:
        assert role.permissions <= (
            ALL_PLATFORM_PERMISSIONS
        )


def test_super_admin_has_only_system_override():
    assert SUPER_ADMIN_ROLE.permissions == frozenset({
        SYSTEM_PERMISSION,
    })


def test_office_admin_has_every_explicit_permission():
    assert SYSTEM_PERMISSION not in (
        OFFICE_ADMIN_ROLE.permissions
    )

    assert OFFICE_ADMIN_ROLE.permissions == (
        ALL_PLATFORM_PERMISSIONS
        - {
            SYSTEM_PERMISSION,
        }
    )


def test_catalogue_manager_policy():
    assert {
        "platform.office.access",
        "platform.catalogue.read",
        "platform.catalogue.review",
        "platform.catalogue.approve",
        "platform.catalogue.manage",
    } <= CATALOGUE_MANAGER_ROLE.permissions


def test_supplier_manager_policy():
    assert {
        "platform.office.access",
        "platform.suppliers.read",
        "platform.suppliers.manage",
    } <= SUPPLIER_INTELLIGENCE_MANAGER_ROLE.permissions


def test_tenant_operations_policy():
    assert {
        "platform.office.access",
        "platform.tenants.read",
        "platform.tenants.manage",
    } <= TENANT_OPERATIONS_MANAGER_ROLE.permissions


def test_auditor_has_no_write_permissions():
    assert AUDITOR_ROLE.permissions == frozenset({
        "platform.office.access",
        "platform.catalogue.read",
        "platform.suppliers.read",
        "platform.tenants.read",
        "platform.audit.read",
        "platform.roles.read",
        "platform.users.read",
        "platform.settings.read",
    })


def test_platform_role_lookup_normalizes_code():
    assert (
        get_platform_role(" SUPER_ADMIN ")
        == SUPER_ADMIN_ROLE
    )


def test_unknown_platform_role_returns_none():
    assert get_platform_role("cashier") is None
