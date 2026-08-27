from __future__ import annotations

from app.services.platform.system_role_provisioning_service import (
    SystemRoleProvisioningResult,
    SystemRoleSyncItem,
)


def test_system_role_sync_item_changed_when_created():
    item = SystemRoleSyncItem(
        code="admin",
        created=True,
        metadata_updated=False,
        permissions_added=(),
        permissions_removed=(),
    )

    assert item.changed is True


def test_system_role_sync_item_unchanged():
    item = SystemRoleSyncItem(
        code="admin",
        created=False,
        metadata_updated=False,
        permissions_added=(),
        permissions_removed=(),
    )

    assert item.changed is False


def test_provisioning_result_changed():
    result = SystemRoleProvisioningResult(
        tenant_id="tenant-1",
        roles=(
            SystemRoleSyncItem(
                code="admin",
                created=False,
                metadata_updated=False,
                permissions_added=("products.view",),
                permissions_removed=(),
            ),
        ),
    )

    assert result.changed is True


def test_tenant_administrator_policy_includes_every_canonical_permission():
    from app.auth.permissions import ALL_PERMISSIONS
    from app.services.platform.system_role_policy import (
        TENANT_ADMINISTRATOR_ROLE,
    )

    assert (
        TENANT_ADMINISTRATOR_ROLE.permissions
        == frozenset(ALL_PERMISSIONS)
    )
