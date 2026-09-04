from __future__ import annotations

import pytest

from app.extensions import db
from app.models import (
    PlatformPermission,
    PlatformRole,
    PlatformRolePermission,
    PlatformUser,
    PlatformUserRole,
)


@pytest.fixture
def platform_user():
    user = PlatformUser(
        email="platform-user@example.invalid",
        username="platform-user",
        first_name="Platform",
        last_name="User",
        password_hash="test-hash",
        is_active=True,
    )

    db.session.add(user)
    db.session.flush()

    return user


@pytest.fixture
def platform_role():
    role = PlatformRole(
        code="catalogue_manager",
        name="Catalogue Manager",
        description="Manages governed catalogue data.",
        is_system=True,
    )

    db.session.add(role)
    db.session.flush()

    return role


@pytest.fixture
def platform_permission():
    permission = PlatformPermission(
        code="platform.catalogue.read",
        name="Read Platform Catalogue",
        module_code="catalogue",
        description="Read governed Master Catalogue data.",
    )

    db.session.add(permission)
    db.session.flush()

    return permission


def test_platform_user_is_global_and_active(
    platform_user,
):
    assert "tenant_id" not in (
        PlatformUser.__table__.columns
    )

    assert platform_user.is_active is True
    assert platform_user.email == (
        "platform-user@example.invalid"
    )


def test_platform_user_role_assignment(
    platform_user,
    platform_role,
):
    assignment = PlatformUserRole(
        platform_user_id=platform_user.id,
        platform_role_id=platform_role.id,
        assigned_by_platform_user_id=platform_user.id,
        assignment_reason="Test assignment.",
    )

    db.session.add(assignment)
    db.session.flush()
    db.session.expire_all()

    persisted = db.session.get(
        PlatformUser,
        platform_user.id,
    )

    assert persisted is not None

    assert {
        role.code
        for role in persisted.roles
    } == {
        "catalogue_manager",
    }


def test_platform_role_permission_assignment(
    platform_user,
    platform_role,
    platform_permission,
):
    assignment = PlatformRolePermission(
        platform_role_id=platform_role.id,
        platform_permission_id=platform_permission.id,
        assigned_by_platform_user_id=platform_user.id,
        assignment_reason="Test permission grant.",
    )

    db.session.add(assignment)
    db.session.flush()
    db.session.expire_all()

    persisted = db.session.get(
        PlatformRole,
        platform_role.id,
    )

    assert persisted is not None

    assert {
        permission.code
        for permission in persisted.permissions
    } == {
        "platform.catalogue.read",
    }


def test_platform_assignment_provenance(
    platform_user,
    platform_role,
):
    assignment = PlatformUserRole(
        platform_user_id=platform_user.id,
        platform_role_id=platform_role.id,
        assigned_by_platform_user_id=platform_user.id,
        assignment_reason="Delegated by platform administrator.",
    )

    db.session.add(assignment)
    db.session.flush()

    assert (
        assignment.assigned_by_platform_user_id
        == platform_user.id
    )

    assert (
        assignment.assignment_reason
        == "Delegated by platform administrator."
    )


def test_platform_models_do_not_reference_tenant_tables():
    platform_tables = {
        PlatformUser.__table__.name,
        PlatformRole.__table__.name,
        PlatformPermission.__table__.name,
        PlatformUserRole.__table__.name,
        PlatformRolePermission.__table__.name,
    }

    assert platform_tables == {
        "platform_users",
        "platform_roles",
        "platform_permissions",
        "platform_user_roles",
        "platform_role_permissions",
    }

    for model in (
        PlatformUser,
        PlatformRole,
        PlatformPermission,
    ):
        assert "tenant_id" not in model.__table__.columns
