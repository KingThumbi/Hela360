from __future__ import annotations

import pytest
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app import create_app
from app.extensions import db
from app.models import (
    PlatformPermission,
    PlatformRole,
    PlatformRolePermission,
    PlatformUserRole,
)
from app.services.platform.platform_permission_catalogue_service import (
    PlatformPermissionCatalogueService,
)
from app.services.platform.platform_permission_policy import (
    SYSTEM_PERMISSION,
)
from app.services.platform.platform_role_policy import (
    OFFICE_ADMIN_ROLE,
    SUPER_ADMIN_ROLE,
    SYSTEM_PLATFORM_ROLES,
)
from app.services.platform.platform_role_provisioning_service import (
    PlatformRoleProvisioningService,
)


@pytest.fixture()
def platform_session():
    app = create_app()

    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()

        session = Session(
            bind=connection,
            expire_on_commit=False,
        )

        try:
            session.execute(
                delete(PlatformUserRole)
            )
            session.execute(
                delete(PlatformRolePermission)
            )
            session.execute(
                delete(PlatformRole)
            )
            session.execute(
                delete(PlatformPermission)
            )
            session.flush()

            yield session
        finally:
            session.close()
            transaction.rollback()
            connection.close()


def _synchronize_permissions(
    platform_session,
):
    PlatformPermissionCatalogueService(
        platform_session
    ).synchronize()


def test_synchronize_creates_system_roles(
    platform_session,
):
    _synchronize_permissions(
        platform_session
    )

    service = PlatformRoleProvisioningService(
        platform_session
    )

    result = service.synchronize()

    persisted_codes = set(
        platform_session.scalars(
            select(PlatformRole.code)
        ).all()
    )

    assert {
        role.code
        for role in SYSTEM_PLATFORM_ROLES
    } <= persisted_codes

    assert result.changed is True


def test_role_synchronization_is_idempotent(
    platform_session,
):
    _synchronize_permissions(
        platform_session
    )

    service = PlatformRoleProvisioningService(
        platform_session
    )

    service.synchronize()
    second = service.synchronize()

    assert second.changed is False


def test_super_admin_receives_only_system_permission(
    platform_session,
):
    _synchronize_permissions(
        platform_session
    )

    PlatformRoleProvisioningService(
        platform_session
    ).synchronize()

    role = platform_session.scalar(
        select(PlatformRole).where(
            PlatformRole.code
            == SUPER_ADMIN_ROLE.code
        )
    )

    assert role is not None

    assert {
        permission.code
        for permission in role.permissions
    } == {
        SYSTEM_PERMISSION,
    }


def test_office_admin_has_no_system_override(
    platform_session,
):
    _synchronize_permissions(
        platform_session
    )

    PlatformRoleProvisioningService(
        platform_session
    ).synchronize()

    role = platform_session.scalar(
        select(PlatformRole).where(
            PlatformRole.code
            == OFFICE_ADMIN_ROLE.code
        )
    )

    assert role is not None

    codes = {
        permission.code
        for permission in role.permissions
    }

    assert SYSTEM_PERMISSION not in codes

    assert codes == set(
        OFFICE_ADMIN_ROLE.permissions
    )


def test_synchronize_repairs_system_role_permissions(
    platform_session,
):
    _synchronize_permissions(
        platform_session
    )

    service = PlatformRoleProvisioningService(
        platform_session
    )

    service.synchronize()

    role = platform_session.scalar(
        select(PlatformRole).where(
            PlatformRole.code == "auditor"
        )
    )

    extra_permission = platform_session.scalar(
        select(PlatformPermission).where(
            PlatformPermission.code
            == "platform.users.create"
        )
    )

    assert role is not None
    assert extra_permission is not None

    role.permissions.append(
        extra_permission
    )

    platform_session.flush()

    result = service.synchronize()

    assert "platform.users.create" not in {
        permission.code
        for permission in role.permissions
    }

    item = next(
        item
        for item in result.roles
        if item.code == "auditor"
    )

    assert (
        "platform.users.create"
        in item.permissions_removed
    )


def test_custom_platform_role_is_untouched(
    platform_session,
):
    _synchronize_permissions(
        platform_session
    )

    custom = PlatformRole(
        code="custom_support",
        name="Custom Support",
        description="Custom platform role.",
        is_system=False,
    )

    platform_session.add(custom)
    platform_session.flush()

    PlatformRoleProvisioningService(
        platform_session
    ).synchronize()

    persisted = platform_session.get(
        PlatformRole,
        custom.id,
    )

    assert persisted is not None
    assert persisted.name == "Custom Support"
    assert persisted.is_system is False
