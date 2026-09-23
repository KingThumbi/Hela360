from __future__ import annotations

from types import SimpleNamespace

import pytest
from flask import Flask

from app.api.errors import register_error_handlers
from app.extensions import db


@pytest.fixture()
def app_context():
    from app.api.tenant_administration import (
        bp as administration_bp,
    )

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
        yield app


@pytest.fixture()
def client(
    app_context,
    monkeypatch: pytest.MonkeyPatch,
):
    identity = SimpleNamespace(
        user_id="actor-user",
        tenant_id="tenant-1",
        branch_id=None,
    )

    monkeypatch.setattr(
        "app.services.tenant.auth.decorators."
        "get_current_identity",
        lambda: identity,
    )

    monkeypatch.setattr(
        "app.api.utils.get_current_identity",
        lambda: identity,
    )

    monkeypatch.setattr(
        "app.services.tenant.auth.decorators."
        "authorization_service.authorize",
        lambda *args, **kwargs: None,
    )

    return app_context.test_client()


def test_permission_override_uses_authenticated_scope(
    client,
    monkeypatch,
):
    captured = {}

    result = SimpleNamespace(
        target_user_id="target-user",
        permission_id="permission-1",
        permission_code="products.units.edit",
        previous_effect=None,
        effect="allow",
        changed=True,
    )

    class FakeService:
        def __init__(self, session):
            captured["session"] = session

        def set_override(self, **kwargs):
            captured.update(kwargs)
            return result

    monkeypatch.setattr(
        "app.api.tenant_administration."
        "TenantAdministrationUserPermissionCommandService",
        FakeService,
    )

    response = client.put(
        "/api/administration/users/"
        "target-user/permissions/"
        "products.units.edit",
        json={
            "effect": "allow",
            "reason": "Cashier unit editing.",
            # These must never override authenticated scope.
            "tenant_id": "attacker-tenant",
            "actor_user_id": "attacker-user",
        },
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload == {
        "ok": True,
        "item": {
            "user_id": "target-user",
            "permission_id": "permission-1",
            "permission_code": (
                "products.units.edit"
            ),
            "previous_effect": None,
            "effect": "allow",
            "changed": True,
        },
    }

    assert captured[
        "tenant_id"
    ] == "tenant-1"

    assert captured[
        "actor_user_id"
    ] == "actor-user"

    assert captured[
        "target_user_id"
    ] == "target-user"

    assert captured[
        "permission_code"
    ] == "products.units.edit"

    assert captured["effect"] == "allow"

    assert captured[
        "reason"
    ] == "Cashier unit editing."


def test_permission_override_accepts_inherit(
    client,
    monkeypatch,
):
    captured = {}

    result = SimpleNamespace(
        target_user_id="target-user",
        permission_id="permission-1",
        permission_code="products.units.edit",
        previous_effect="allow",
        effect=None,
        changed=True,
    )

    class FakeService:
        def __init__(self, session):
            pass

        def set_override(self, **kwargs):
            captured.update(kwargs)
            return result

    monkeypatch.setattr(
        "app.api.tenant_administration."
        "TenantAdministrationUserPermissionCommandService",
        FakeService,
    )

    response = client.put(
        "/api/administration/users/"
        "target-user/permissions/"
        "products.units.edit",
        json={
            "effect": "inherit",
        },
    )

    assert response.status_code == 200

    assert captured["effect"] == "inherit"

    payload = response.get_json()

    assert payload["item"]["effect"] is None
    assert (
        payload["item"]["previous_effect"]
        == "allow"
    )


def test_permission_override_requires_effect_string(
    client,
):
    response = client.put(
        "/api/administration/users/"
        "target-user/permissions/"
        "products.units.edit",
        json={},
    )

    assert response.status_code == 400

    payload = response.get_json()

    assert payload["error"] == {
        "code": "INVALID_PERMISSION_ASSIGNMENT",
        "message": "effect must be a string.",
    }


def test_permission_override_rejects_non_string_reason(
    client,
):
    response = client.put(
        "/api/administration/users/"
        "target-user/permissions/"
        "products.units.edit",
        json={
            "effect": "allow",
            "reason": 123,
        },
    )

    assert response.status_code == 400

    payload = response.get_json()

    assert payload["error"] == {
        "code": "INVALID_PERMISSION_ASSIGNMENT",
        "message": "reason must be a string.",
    }


def test_permission_override_maps_command_rejection(
    client,
    monkeypatch,
):
    from app.services.tenant.administration import (
        TenantAdministrationPermissionAssignmentError,
    )

    class FakeService:
        def __init__(self, session):
            pass

        def set_override(self, **kwargs):
            raise (
                TenantAdministrationPermissionAssignmentError(
                    "Unsafe permission change."
                )
            )

    monkeypatch.setattr(
        "app.api.tenant_administration."
        "TenantAdministrationUserPermissionCommandService",
        FakeService,
    )

    response = client.put(
        "/api/administration/users/"
        "target-user/permissions/"
        "products.units.edit",
        json={
            "effect": "allow",
        },
    )

    assert response.status_code == 400

    payload = response.get_json()

    assert payload["error"] == {
        "code": "PERMISSION_ASSIGNMENT_REJECTED",
        "message": "Unsafe permission change.",
    }
