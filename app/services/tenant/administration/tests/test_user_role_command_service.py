from __future__ import annotations

import pytest
from uuid import uuid4

from app import create_app
from app.extensions import db
from app.models import (
    AuditLog,
    Permission,
    Role,
    RolePermission,
    Tenant,
    User,
    UserRole,
)


@pytest.fixture()
def app():
    app = create_app()
    app.config.update(TESTING=True)
    return app


@pytest.fixture()
def iam_state(app):
    with app.app_context():
        suffix = uuid4().hex[:12]

        tenant_a = Tenant(
            legal_name="Tenant A",
            display_name="Tenant A",
            workspace_slug=(
                f"tenant-a-role-command-{suffix}"
            ),
        )
        tenant_b = Tenant(
            legal_name="Tenant B",
            display_name="Tenant B",
            workspace_slug=(
                f"tenant-b-role-command-{suffix}"
            ),
        )

        db.session.add_all([tenant_a, tenant_b])
        db.session.flush()

        actor = User(
            tenant_id=tenant_a.id,
            first_name="Tenant",
            last_name="Administrator",
            username="tenant-admin",
            password_hash="test-only",
            is_owner=False,
            is_active=True,
        )

        owner = User(
            tenant_id=tenant_a.id,
            first_name="Tenant",
            last_name="Owner",
            username="tenant-owner",
            password_hash="test-only",
            is_owner=True,
            is_active=True,
        )

        cashier = User(
            tenant_id=tenant_a.id,
            first_name="Jane",
            last_name="Cashier",
            username="cashier",
            password_hash="test-only",
            is_owner=False,
            is_active=True,
        )

        foreign_user = User(
            tenant_id=tenant_b.id,
            first_name="Foreign",
            last_name="User",
            username="foreign-user",
            password_hash="test-only",
            is_owner=False,
            is_active=True,
        )

        db.session.add_all(
            [
                actor,
                owner,
                cashier,
                foreign_user,
            ]
        )
        db.session.flush()

        cashier_role = Role(
            tenant_id=tenant_a.id,
            code="cashier",
            name="Cashier",
            description="Cashier role",
            is_system=False,
        )

        manager_role = Role(
            tenant_id=tenant_a.id,
            code="manager",
            name="Manager",
            description="Manager role",
            is_system=False,
        )

        admin_role = Role(
            tenant_id=tenant_a.id,
            code="admin",
            name="Administrator",
            description="Canonical administrator role",
            is_system=True,
        )

        foreign_role = Role(
            tenant_id=tenant_b.id,
            code="foreign",
            name="Foreign Role",
            description="Other tenant role",
            is_system=False,
        )

        db.session.add_all(
            [
                cashier_role,
                manager_role,
                admin_role,
                foreign_role,
            ]
        )
        db.session.flush()

        db.session.add(
            UserRole(
                user_id=cashier.id,
                role_id=cashier_role.id,
                assigned_by_user_id=actor.id,
                assignment_reason="Initial cashier role.",
            )
        )

        db.session.flush()

        yield {
            "tenant_a": str(tenant_a.id),
            "tenant_b": str(tenant_b.id),
            "actor": str(actor.id),
            "owner": str(owner.id),
            "cashier": str(cashier.id),
            "foreign_user": str(foreign_user.id),
            "cashier_role": str(cashier_role.id),
            "manager_role": str(manager_role.id),
            "admin_role": str(admin_role.id),
            "foreign_role": str(foreign_role.id),
        }

        db.session.rollback()


def _service():
    from app.services.tenant.administration.user_role_command_service import (
        TenantAdministrationRoleAssignmentError,
        TenantAdministrationUserRoleCommandService,
    )

    return (
        TenantAdministrationUserRoleCommandService(db.session),
        TenantAdministrationRoleAssignmentError,
    )


def test_replace_roles_replaces_custom_role_set(iam_state):
    service, _ = _service()

    result = service.replace_roles(
        tenant_id=iam_state["tenant_a"],
        actor_user_id=iam_state["actor"],
        target_user_id=iam_state["cashier"],
        role_ids=[iam_state["manager_role"]],
        reason="Promoted to manager.",
    )

    db.session.flush()

    assignments = (
        db.session.query(UserRole)
        .filter(
            UserRole.user_id == iam_state["cashier"]
        )
        .all()
    )

    assert {
        str(item.role_id)
        for item in assignments
    } == {
        iam_state["manager_role"],
    }

    assert result.added_role_ids == (
        iam_state["manager_role"],
    )
    assert result.removed_role_ids == (
        iam_state["cashier_role"],
    )


def test_replace_roles_rejects_cross_tenant_target(iam_state):
    service, error_type = _service()

    with pytest.raises(
        error_type,
        match="User not found",
    ):
        service.replace_roles(
            tenant_id=iam_state["tenant_a"],
            actor_user_id=iam_state["actor"],
            target_user_id=iam_state["foreign_user"],
            role_ids=[iam_state["manager_role"]],
            reason="Invalid cross-tenant attempt.",
        )


def test_replace_roles_rejects_cross_tenant_role(iam_state):
    service, error_type = _service()

    with pytest.raises(
        error_type,
        match="Role not found",
    ):
        service.replace_roles(
            tenant_id=iam_state["tenant_a"],
            actor_user_id=iam_state["actor"],
            target_user_id=iam_state["cashier"],
            role_ids=[iam_state["foreign_role"]],
            reason="Invalid cross-tenant role.",
        )


def test_non_owner_cannot_assign_system_role(iam_state):
    service, error_type = _service()

    with pytest.raises(
        error_type,
        match="system role",
    ):
        service.replace_roles(
            tenant_id=iam_state["tenant_a"],
            actor_user_id=iam_state["actor"],
            target_user_id=iam_state["cashier"],
            role_ids=[iam_state["admin_role"]],
            reason="Attempted administrator promotion.",
        )


def test_non_owner_cannot_change_owner_roles(iam_state):
    service, error_type = _service()

    with pytest.raises(
        error_type,
        match="tenant owner",
    ):
        service.replace_roles(
            tenant_id=iam_state["tenant_a"],
            actor_user_id=iam_state["actor"],
            target_user_id=iam_state["owner"],
            role_ids=[iam_state["manager_role"]],
            reason="Attempted owner role change.",
        )


def test_owner_can_assign_system_role(iam_state):
    service, _ = _service()

    result = service.replace_roles(
        tenant_id=iam_state["tenant_a"],
        actor_user_id=iam_state["owner"],
        target_user_id=iam_state["cashier"],
        role_ids=[iam_state["admin_role"]],
        reason="Owner approved administrator access.",
    )

    db.session.flush()

    assert result.added_role_ids == (
        iam_state["admin_role"],
    )


def test_role_changes_preserve_assignment_provenance(iam_state):
    service, _ = _service()

    service.replace_roles(
        tenant_id=iam_state["tenant_a"],
        actor_user_id=iam_state["actor"],
        target_user_id=iam_state["cashier"],
        role_ids=[iam_state["manager_role"]],
        reason="Operational responsibility changed.",
    )

    db.session.flush()

    assignment = (
        db.session.query(UserRole)
        .filter(
            UserRole.user_id == iam_state["cashier"],
            UserRole.role_id == iam_state["manager_role"],
        )
        .one()
    )

    assert str(assignment.assigned_by_user_id) == iam_state["actor"]
    assert (
        assignment.assignment_reason
        == "Operational responsibility changed."
    )


def test_role_changes_write_add_and_remove_audit_events(iam_state):
    service, _ = _service()

    service.replace_roles(
        tenant_id=iam_state["tenant_a"],
        actor_user_id=iam_state["actor"],
        target_user_id=iam_state["cashier"],
        role_ids=[iam_state["manager_role"]],
        reason="Operational responsibility changed.",
    )

    db.session.flush()

    events = (
        db.session.query(AuditLog)
        .filter(
            AuditLog.tenant_id == iam_state["tenant_a"],
            AuditLog.entity_id == iam_state["cashier"],
        )
        .order_by(AuditLog.id.asc())
        .all()
    )

    assert [event.action for event in events] == [
        "ROLE_REMOVED",
        "ROLE_ASSIGNED",
    ]

    assert all(
        event.user_id == iam_state["actor"]
        for event in events
    )

    assert all(
        event.reason
        == "Operational responsibility changed."
        for event in events
    )


def test_replace_roles_is_idempotent(iam_state):
    service, _ = _service()

    first = service.replace_roles(
        tenant_id=iam_state["tenant_a"],
        actor_user_id=iam_state["actor"],
        target_user_id=iam_state["cashier"],
        role_ids=[iam_state["cashier_role"]],
        reason="No role change.",
    )

    db.session.flush()

    assert first.added_role_ids == ()
    assert first.removed_role_ids == ()

    events = (
        db.session.query(AuditLog)
        .filter(
            AuditLog.tenant_id == iam_state["tenant_a"],
            AuditLog.entity_id == iam_state["cashier"],
        )
        .all()
    )

    assert events == []


def test_role_change_refreshes_target_authorization_context(
    iam_state,
):
    service, _ = _service()

    calls = []

    class AuthorizationSpy:
        def refresh_context(
            self,
            user,
            *,
            tenant_id=None,
        ):
            calls.append(
                (
                    str(user),
                    str(tenant_id),
                )
            )

    # The command boundary must explicitly refresh the target user's
    # authorization snapshot after a successful role-set change.
    service.authorization = AuthorizationSpy()

    service.replace_roles(
        tenant_id=iam_state["tenant_a"],
        actor_user_id=iam_state["actor"],
        target_user_id=iam_state["cashier"],
        role_ids=[iam_state["manager_role"]],
        reason="Authorization refresh test.",
    )

    db.session.flush()

    assert calls == [
        (
            iam_state["cashier"],
            iam_state["tenant_a"],
        )
    ]
