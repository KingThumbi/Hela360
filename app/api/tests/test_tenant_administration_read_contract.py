from __future__ import annotations

from types import SimpleNamespace

import pytest
from flask import Flask

from app.api.errors import register_error_handlers
from app.extensions import db
from app.models import (
    Permission,
    Role,
    RolePermission,
    Tenant,
    User,
    UserPermission,
    UserRole,
)


@pytest.fixture()
def app_context():
    # Import here deliberately.
    #
    # This contract test is being introduced before the production
    # Tenant Administration blueprint exists. The first RED run should
    # therefore fail during import until the feature boundary is created.
    from app.api.tenant_administration import bp as administration_bp

    app = Flask(__name__)

    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TESTING=True,
    )

    db.init_app(app)

    app.register_blueprint(
        administration_bp,
        url_prefix="/api/administration",
    )
    register_error_handlers(app)

    with app.app_context():
        Tenant.__table__.create(db.engine)
        Permission.__table__.create(db.engine)
        Role.__table__.create(db.engine)
        User.__table__.create(db.engine)
        RolePermission.__table__.create(db.engine)
        UserRole.__table__.create(db.engine)
        UserPermission.__table__.create(db.engine)

        db.session.add_all(
            [
                Tenant(
                    id="tenant-1",
                    legal_name="Tenant One",
                    display_name="Tenant One",
                ),
                Tenant(
                    id="tenant-2",
                    legal_name="Tenant Two",
                    display_name="Tenant Two",
                ),
            ]
        )

        db.session.flush()

        sales_read = Permission(
            id="permission-sales-read",
            code="sales.read",
            name="View sales",
            module_code="sales",
        )
        sales_create = Permission(
            id="permission-sales-create",
            code="sales.create",
            name="Create sales",
            module_code="sales",
        )
        users_read = Permission(
            id="permission-users-read",
            code="users.read",
            name="View users",
            module_code="users",
        )

        db.session.add_all(
            [
                sales_read,
                sales_create,
                users_read,
            ]
        )

        cashier_role = Role(
            id="role-cashier",
            tenant_id="tenant-1",
            name="Cashier",
            code="cashier",
            description="Tenant One cashier",
            is_system=False,
        )
        manager_role = Role(
            id="role-manager",
            tenant_id="tenant-1",
            name="Manager",
            code="manager",
            description="Tenant One manager",
            is_system=False,
        )
        foreign_role = Role(
            id="role-foreign",
            tenant_id="tenant-2",
            name="Foreign Role",
            code="foreign-role",
            description="Tenant Two role",
            is_system=False,
        )

        db.session.add_all(
            [
                cashier_role,
                manager_role,
                foreign_role,
            ]
        )
        db.session.flush()

        db.session.add_all(
            [
                RolePermission(
                    role_id=cashier_role.id,
                    permission_id=sales_create.id,
                ),
                RolePermission(
                    role_id=manager_role.id,
                    permission_id=sales_read.id,
                ),
                RolePermission(
                    role_id=manager_role.id,
                    permission_id=users_read.id,
                ),
            ]
        )

        current_admin = User(
            id="user-admin",
            tenant_id="tenant-1",
            first_name="Tenant",
            last_name="Admin",
            email="admin@tenant-one.test",
            username="admin",
            password_hash="test-only",
            is_owner=False,
            is_active=True,
        )

        cashier = User(
            id="user-cashier",
            tenant_id="tenant-1",
            first_name="Jane",
            last_name="Cashier",
            email="cashier@tenant-one.test",
            username="cashier",
            password_hash="test-only",
            is_owner=False,
            is_active=True,
        )

        foreign_user = User(
            id="user-foreign",
            tenant_id="tenant-2",
            first_name="Other",
            last_name="Tenant",
            email="staff@tenant-two.test",
            username="other-staff",
            password_hash="test-only",
            is_owner=False,
            is_active=True,
        )

        db.session.add_all(
            [
                current_admin,
                cashier,
                foreign_user,
            ]
        )
        db.session.flush()

        db.session.add(
            UserRole(
                user_id=cashier.id,
                role_id=cashier_role.id,
                assigned_by_user_id=current_admin.id,
                assignment_reason="Initial cashier assignment.",
            )
        )

        # Cashier receives sales.create from the role, but an explicit
        # deny removes it from effective permissions. sales.read is an
        # explicit allow so we can prove both override directions.
        db.session.add_all(
            [
                UserPermission(
                    user_id=cashier.id,
                    permission_id=sales_create.id,
                    effect="deny",
                    assigned_by_user_id=current_admin.id,
                    assignment_reason="Restricted sale creation.",
                ),
                UserPermission(
                    user_id=cashier.id,
                    permission_id=sales_read.id,
                    effect="allow",
                    assigned_by_user_id=current_admin.id,
                    assignment_reason="Allow sales visibility.",
                ),
            ]
        )

        db.session.commit()

        yield app

        db.session.remove()

        UserPermission.__table__.drop(db.engine)
        UserRole.__table__.drop(db.engine)
        RolePermission.__table__.drop(db.engine)
        User.__table__.drop(db.engine)
        Role.__table__.drop(db.engine)
        Permission.__table__.drop(db.engine)
        Tenant.__table__.drop(db.engine)


@pytest.fixture()
def client(app_context, monkeypatch: pytest.MonkeyPatch):
    identity = SimpleNamespace(
        user_id="user-admin",
        tenant_id="tenant-1",
        branch_id=None,
    )

    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.get_current_identity",
        lambda: identity,
    )

    monkeypatch.setattr(
        "app.api.utils.get_current_identity",
        lambda: identity,
    )

    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.authorization_service.authorize",
        lambda *args, **kwargs: None,
    )

    return app_context.test_client()


def test_user_list_is_tenant_scoped(client):
    response = client.get("/api/administration/users")

    assert response.status_code == 200
    assert response.json["ok"] is True

    ids = {
        item["id"]
        for item in response.json["items"]
    }

    assert "user-admin" in ids
    assert "user-cashier" in ids
    assert "user-foreign" not in ids


def test_user_detail_is_tenant_scoped(client):
    own_response = client.get(
        "/api/administration/users/user-cashier"
    )
    foreign_response = client.get(
        "/api/administration/users/user-foreign"
    )

    assert own_response.status_code == 200
    assert own_response.json["item"]["id"] == "user-cashier"

    # Do not reveal that another tenant's user exists.
    assert foreign_response.status_code == 404


def test_user_roles_returns_only_target_assignments(client):
    response = client.get(
        "/api/administration/users/user-cashier/roles"
    )

    assert response.status_code == 200
    assert response.json["ok"] is True

    assert response.json["items"] == [
        {
            "id": "role-cashier",
            "code": "cashier",
            "name": "Cashier",
            "is_system": False,
        }
    ]


def test_effective_permissions_respect_user_overrides(client):
    response = client.get(
        "/api/administration/users/"
        "user-cashier/effective-permissions"
    )

    assert response.status_code == 200
    assert response.json["ok"] is True

    codes = {
        item["code"]
        for item in response.json["items"]
    }

    # Explicit allow.
    assert "sales.read" in codes

    # Role grant removed by explicit deny.
    assert "sales.create" not in codes


def test_role_list_is_tenant_scoped(client):
    response = client.get("/api/administration/roles")

    assert response.status_code == 200
    assert response.json["ok"] is True

    ids = {
        item["id"]
        for item in response.json["items"]
    }

    assert "role-cashier" in ids
    assert "role-manager" in ids
    assert "role-foreign" not in ids


def test_role_replacement_endpoint_uses_authenticated_tenant_and_actor(
    app_context,
    monkeypatch: pytest.MonkeyPatch,
):
    identity = SimpleNamespace(
        user_id="user-admin",
        tenant_id="tenant-1",
        branch_id=None,
    )

    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.get_current_identity",
        lambda: identity,
    )

    monkeypatch.setattr(
        "app.api.utils.get_current_identity",
        lambda: identity,
    )

    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.authorization_service.authorize",
        lambda *args, **kwargs: None,
    )

    calls = {}

    class Result:
        target_user_id = "user-cashier"
        role_ids = ("role-manager",)
        added_role_ids = ("role-manager",)
        removed_role_ids = ("role-cashier",)
        changed = True

    class ServiceSpy:
        def __init__(self, session):
            calls["session"] = session

        def replace_roles(
            self,
            *,
            tenant_id,
            actor_user_id,
            target_user_id,
            role_ids,
            reason,
        ):
            calls.update(
                {
                    "tenant_id": tenant_id,
                    "actor_user_id": actor_user_id,
                    "target_user_id": target_user_id,
                    "role_ids": role_ids,
                    "reason": reason,
                }
            )
            return Result()

    monkeypatch.setattr(
        "app.api.tenant_administration."
        "TenantAdministrationUserRoleCommandService",
        ServiceSpy,
    )

    client = app_context.test_client()

    response = client.put(
        "/api/administration/users/user-cashier/roles",
        json={
            "role_ids": ["role-manager"],
            "reason": "Promoted.",
            "tenant_id": "tenant-2",
            "actor_user_id": "fake-actor",
        },
    )

    assert response.status_code == 200

    assert calls["tenant_id"] == "tenant-1"
    assert calls["actor_user_id"] == "user-admin"
    assert calls["target_user_id"] == "user-cashier"
    assert calls["role_ids"] == ["role-manager"]
    assert calls["reason"] == "Promoted."

    assert response.json == {
        "ok": True,
        "item": {
            "user_id": "user-cashier",
            "role_ids": ["role-manager"],
            "added_role_ids": ["role-manager"],
            "removed_role_ids": ["role-cashier"],
            "changed": True,
        },
    }


def test_role_replacement_rejects_missing_role_ids(client):
    response = client.put(
        "/api/administration/users/user-cashier/roles",
        json={
            "reason": "Missing roles.",
        },
    )

    assert response.status_code == 400
    assert response.json["ok"] is False
    assert (
        response.json["error"]["code"]
        == "INVALID_ROLE_ASSIGNMENT"
    )


def test_role_replacement_rejects_non_array_role_ids(client):
    response = client.put(
        "/api/administration/users/user-cashier/roles",
        json={
            "role_ids": "role-manager",
        },
    )

    assert response.status_code == 400
    assert response.json["ok"] is False
    assert (
        response.json["error"]["code"]
        == "INVALID_ROLE_ASSIGNMENT"
    )


def test_user_permission_management_exposes_sources(client):
    response = client.get(
        "/api/administration/users/user-cashier/permissions"
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["ok"] is True
    assert payload["count"] == 3

    by_code = {
        item["code"]: item
        for item in payload["items"]
    }

    # sales.create is granted by the Cashier role but explicitly denied.
    assert by_code["sales.create"] == {
        "id": "permission-sales-create",
        "code": "sales.create",
        "name": "Create sales",
        "module": "sales",
        "description": None,
        "role_inherited": True,
        "override_effect": "deny",
        "effective": False,
        "source": "direct_deny",
    }

    # sales.read is a direct user allow.
    assert by_code["sales.read"] == {
        "id": "permission-sales-read",
        "code": "sales.read",
        "name": "View sales",
        "module": "sales",
        "description": None,
        "role_inherited": False,
        "override_effect": "allow",
        "effective": True,
        "source": "direct_allow",
    }

    # users.read is present in the tenant catalogue but has no grant.
    assert by_code["users.read"] == {
        "id": "permission-users-read",
        "code": "users.read",
        "name": "View users",
        "module": "users",
        "description": None,
        "role_inherited": False,
        "override_effect": None,
        "effective": False,
        "source": "none",
    }


def test_user_permission_management_is_tenant_scoped(client):
    response = client.get(
        "/api/administration/users/user-foreign/permissions"
    )

    assert response.status_code == 404

