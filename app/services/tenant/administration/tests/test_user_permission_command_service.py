from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import select

from app import create_app
from app.extensions import db
from app.models import (
    AuditLog,
    Permission,
    Role,
    RolePermission,
    Tenant,
    User,
    UserPermission,
    UserRole,
)


@pytest.fixture()
def app():
    app = create_app()
    app.config.update(TESTING=True)
    return app


def _permission(code: str) -> Permission:
    existing = db.session.execute(
        select(Permission).where(
            Permission.code == code
        )
    ).scalar_one_or_none()

    if existing is not None:
        return existing

    permission = Permission(
        code=code,
        name=code,
        module_code=code.split(".", 1)[0],
        description=f"Test permission {code}",
    )

    db.session.add(permission)
    db.session.flush()

    return permission


@pytest.fixture()
def iam_state(app):
    with app.app_context():
        suffix = uuid4().hex[:12]

        tenant_a = Tenant(
            legal_name="Permission Tenant A",
            display_name="Permission Tenant A",
            workspace_slug=(
                f"permission-tenant-a-{suffix}"
            ),
        )
        tenant_b = Tenant(
            legal_name="Permission Tenant B",
            display_name="Permission Tenant B",
            workspace_slug=(
                f"permission-tenant-b-{suffix}"
            ),
        )

        db.session.add_all(
            [tenant_a, tenant_b]
        )
        db.session.flush()

        actor = User(
            tenant_id=tenant_a.id,
            first_name="Tenant",
            last_name="Administrator",
            username=f"permission-admin-{suffix}",
            password_hash="test-only",
            is_owner=False,
            is_active=True,
        )
        owner = User(
            tenant_id=tenant_a.id,
            first_name="Tenant",
            last_name="Owner",
            username=f"permission-owner-{suffix}",
            password_hash="test-only",
            is_owner=True,
            is_active=True,
        )
        cashier = User(
            tenant_id=tenant_a.id,
            first_name="Jane",
            last_name="Cashier",
            username=f"permission-cashier-{suffix}",
            password_hash="test-only",
            is_owner=False,
            is_active=True,
        )
        foreign_user = User(
            tenant_id=tenant_b.id,
            first_name="Foreign",
            last_name="Cashier",
            username=f"foreign-cashier-{suffix}",
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

        editable = _permission(
            "products.edit"
        )
        unavailable = _permission(
            "products.delete"
        )

        delegated_role = Role(
            tenant_id=tenant_a.id,
            code=f"permission-manager-{suffix}",
            name="Permission Manager",
            description="Test delegated administrator",
            is_system=False,
        )

        db.session.add(delegated_role)
        db.session.flush()

        db.session.add(
            RolePermission(
                role_id=delegated_role.id,
                permission_id=editable.id,
            )
        )
        db.session.add(
            UserRole(
                user_id=actor.id,
                role_id=delegated_role.id,
                assigned_by_user_id=owner.id,
                assignment_reason="Test delegation.",
            )
        )

        db.session.flush()

        yield {
            "tenant_a": str(tenant_a.id),
            "tenant_b": str(tenant_b.id),
            "actor": str(actor.id),
            "owner": str(owner.id),
            "cashier": str(cashier.id),
            "foreign_user": str(
                foreign_user.id
            ),
            "editable_code": editable.code,
            "editable_id": str(editable.id),
            "unavailable_code": (
                unavailable.code
            ),
            "unavailable_id": str(
                unavailable.id
            ),
        }

        db.session.rollback()


def _service():
    from app.services.tenant.administration.user_permission_command_service import (
        TenantAdministrationPermissionAssignmentError,
        TenantAdministrationUserPermissionCommandService,
    )

    return (
        TenantAdministrationUserPermissionCommandService(
            db.session
        ),
        TenantAdministrationPermissionAssignmentError,
    )


def _override(
    *,
    user_id: str,
    permission_id: str,
) -> UserPermission | None:
    return db.session.execute(
        select(UserPermission).where(
            UserPermission.user_id == user_id,
            UserPermission.permission_id
            == permission_id,
        )
    ).scalar_one_or_none()


def test_non_owner_can_directly_allow_permission_they_possess(
    iam_state,
):
    service, _ = _service()

    result = service.set_override(
        tenant_id=iam_state["tenant_a"],
        actor_user_id=iam_state["actor"],
        target_user_id=iam_state["cashier"],
        permission_code=iam_state[
            "editable_code"
        ],
        effect="allow",
        reason="Delegated product editing.",
    )

    db.session.flush()

    override = _override(
        user_id=iam_state["cashier"],
        permission_id=iam_state[
            "editable_id"
        ],
    )

    assert override is not None
    assert override.effect == "allow"
    assert (
        str(override.assigned_by_user_id)
        == iam_state["actor"]
    )
    assert (
        override.assignment_reason
        == "Delegated product editing."
    )
    assert result.previous_effect is None
    assert result.effect == "allow"
    assert result.changed is True


def test_non_owner_can_directly_deny_permission_they_possess(
    iam_state,
):
    service, _ = _service()

    result = service.set_override(
        tenant_id=iam_state["tenant_a"],
        actor_user_id=iam_state["actor"],
        target_user_id=iam_state["cashier"],
        permission_code=iam_state[
            "editable_code"
        ],
        effect="deny",
        reason="Restrict product editing.",
    )

    override = _override(
        user_id=iam_state["cashier"],
        permission_id=iam_state[
            "editable_id"
        ],
    )

    assert override is not None
    assert override.effect == "deny"
    assert result.effect == "deny"


def test_inherit_removes_existing_override(
    iam_state,
):
    service, _ = _service()

    service.set_override(
        tenant_id=iam_state["tenant_a"],
        actor_user_id=iam_state["actor"],
        target_user_id=iam_state["cashier"],
        permission_code=iam_state[
            "editable_code"
        ],
        effect="allow",
        reason="Temporary exception.",
    )

    result = service.set_override(
        tenant_id=iam_state["tenant_a"],
        actor_user_id=iam_state["actor"],
        target_user_id=iam_state["cashier"],
        permission_code=iam_state[
            "editable_code"
        ],
        effect="inherit",
        reason="Return to role policy.",
    )

    assert _override(
        user_id=iam_state["cashier"],
        permission_id=iam_state[
            "editable_id"
        ],
    ) is None

    assert result.previous_effect == "allow"
    assert result.effect is None
    assert result.changed is True


def test_override_change_is_idempotent(
    iam_state,
):
    service, _ = _service()

    service.set_override(
        tenant_id=iam_state["tenant_a"],
        actor_user_id=iam_state["actor"],
        target_user_id=iam_state["cashier"],
        permission_code=iam_state[
            "editable_code"
        ],
        effect="allow",
        reason="Initial reason.",
    )

    audit_count_before = (
        db.session.query(AuditLog).count()
    )

    result = service.set_override(
        tenant_id=iam_state["tenant_a"],
        actor_user_id=iam_state["actor"],
        target_user_id=iam_state["cashier"],
        permission_code=iam_state[
            "editable_code"
        ],
        effect="allow",
        reason="Should not rewrite.",
    )

    audit_count_after = (
        db.session.query(AuditLog).count()
    )

    assert result.changed is False
    assert audit_count_after == (
        audit_count_before
    )

    override = _override(
        user_id=iam_state["cashier"],
        permission_id=iam_state[
            "editable_id"
        ],
    )

    assert (
        override.assignment_reason
        == "Initial reason."
    )


def test_non_owner_cannot_change_permission_they_do_not_possess(
    iam_state,
):
    service, error_type = _service()

    with pytest.raises(
        error_type,
        match="only change permissions they themselves possess",
    ):
        service.set_override(
            tenant_id=iam_state["tenant_a"],
            actor_user_id=iam_state["actor"],
            target_user_id=iam_state["cashier"],
            permission_code=iam_state[
                "unavailable_code"
            ],
            effect="allow",
        )


def test_owner_can_change_permission_without_possessing_it_explicitly(
    iam_state,
):
    service, _ = _service()

    result = service.set_override(
        tenant_id=iam_state["tenant_a"],
        actor_user_id=iam_state["owner"],
        target_user_id=iam_state["cashier"],
        permission_code=iam_state[
            "unavailable_code"
        ],
        effect="allow",
        reason="Owner exception.",
    )

    assert result.effect == "allow"

    override = _override(
        user_id=iam_state["cashier"],
        permission_id=iam_state[
            "unavailable_id"
        ],
    )

    assert override is not None
    assert override.effect == "allow"


def test_non_owner_cannot_change_owner_permissions(
    iam_state,
):
    service, error_type = _service()

    with pytest.raises(
        error_type,
        match="Only the tenant owner",
    ):
        service.set_override(
            tenant_id=iam_state["tenant_a"],
            actor_user_id=iam_state["actor"],
            target_user_id=iam_state["owner"],
            permission_code=iam_state[
                "editable_code"
            ],
            effect="deny",
        )


def test_cross_tenant_target_is_rejected(
    iam_state,
):
    service, error_type = _service()

    with pytest.raises(
        error_type,
        match="User not found",
    ):
        service.set_override(
            tenant_id=iam_state["tenant_a"],
            actor_user_id=iam_state["actor"],
            target_user_id=iam_state[
                "foreign_user"
            ],
            permission_code=iam_state[
                "editable_code"
            ],
            effect="allow",
        )


def test_noncanonical_permission_is_rejected(
    iam_state,
):
    service, error_type = _service()

    with pytest.raises(
        error_type,
        match="canonical tenant permission",
    ):
        service.set_override(
            tenant_id=iam_state["tenant_a"],
            actor_user_id=iam_state["owner"],
            target_user_id=iam_state["cashier"],
            permission_code="products.superpowers",
            effect="allow",
        )


def test_invalid_effect_is_rejected(
    iam_state,
):
    service, error_type = _service()

    with pytest.raises(
        error_type,
        match="allow, deny, or inherit",
    ):
        service.set_override(
            tenant_id=iam_state["tenant_a"],
            actor_user_id=iam_state["owner"],
            target_user_id=iam_state["cashier"],
            permission_code=iam_state[
                "editable_code"
            ],
            effect="maybe",
        )


def test_permission_changes_are_audited(
    iam_state,
):
    service, _ = _service()

    service.set_override(
        tenant_id=iam_state["tenant_a"],
        actor_user_id=iam_state["actor"],
        target_user_id=iam_state["cashier"],
        permission_code=iam_state[
            "editable_code"
        ],
        effect="allow",
        reason="Audit this permission grant.",
    )

    audit = (
        db.session.query(AuditLog)
        .filter(
            AuditLog.tenant_id
            == iam_state["tenant_a"],
            AuditLog.entity_type == "user",
            AuditLog.entity_id
            == iam_state["cashier"],
            AuditLog.action
            == "PERMISSION_GRANTED",
        )
        .one()
    )

    assert (
        str(audit.user_id)
        == iam_state["actor"]
    )
    assert audit.module_code == "AUTH"
    assert audit.old_values is None
    assert audit.new_values == {
        "permission_id": iam_state[
            "editable_id"
        ],
        "permission_code": iam_state[
            "editable_code"
        ],
        "effect": "allow",
    }
    assert audit.details[
        "target_user_id"
    ] == iam_state["cashier"]
    assert audit.reason == (
        "Audit this permission grant."
    )
