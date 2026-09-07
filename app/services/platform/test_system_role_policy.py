from app.auth.permissions import ALL_PERMISSIONS

from app.services.platform.system_role_policy import (
    TENANT_ADMINISTRATOR_ROLE,
    get_system_role,
)


def test_tenant_administrator_receives_all_tenant_permissions():
    assert (
        TENANT_ADMINISTRATOR_ROLE.permissions
        == frozenset(ALL_PERMISSIONS)
    )


def test_tenant_administrator_does_not_use_wildcard():
    assert (
        "*"
        not in TENANT_ADMINISTRATOR_ROLE.permissions
    )


def test_get_system_role_resolves_admin():
    assert (
        get_system_role("admin")
        is TENANT_ADMINISTRATOR_ROLE
    )


def test_tenant_administrator_receives_goods_receipt_workflow_permissions():
    assert "inventory.receive" in TENANT_ADMINISTRATOR_ROLE.permissions
    assert "inventory.approve" in TENANT_ADMINISTRATOR_ROLE.permissions
    assert "inventory.post" in TENANT_ADMINISTRATOR_ROLE.permissions
