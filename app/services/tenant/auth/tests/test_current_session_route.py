"""
Route contract tests for GET /api/auth/session.
"""

from __future__ import annotations

import importlib
import sys
import types
from dataclasses import asdict
from types import SimpleNamespace

import pytest
from flask import Flask

from app.auth.jwt import Identity, JWTTokenType
from app.auth.schemas import (
    CurrentSessionResponse,
    CurrentSessionTenantResponse,
    CurrentSessionUserResponse,
)


@pytest.fixture
def auth_routes(monkeypatch: pytest.MonkeyPatch):
    fake_authentication_module = types.ModuleType(
        "app.services.tenant.auth.authentication_service"
    )
    fake_authentication_module.authentication_service = SimpleNamespace()
    monkeypatch.setitem(
        sys.modules,
        "app.services.tenant.auth.authentication_service",
        fake_authentication_module,
    )

    return importlib.import_module("app.auth.routes")


@pytest.fixture
def app(auth_routes):
    app = Flask(__name__)
    app.register_blueprint(
        auth_routes.bp,
        url_prefix="/api/auth",
    )

    return app


@pytest.fixture
def client(app):
    return app.test_client()


def identity() -> Identity:
    return Identity(
        user_id="user-1",
        tenant_id="tenant-1",
        branch_id=None,
        permissions=(),
        session_id="session-1",
        token_type=JWTTokenType.ACCESS,
        jti="jwt-1",
    )


def session_response() -> CurrentSessionResponse:
    return CurrentSessionResponse(
        user=CurrentSessionUserResponse(
            id="user-1",
            email="user@example.test",
            username="user",
            first_name="Ada",
            last_name="Lovelace",
            is_active=True,
            is_locked=False,
            is_owner=False,
            is_platform_admin=False,
        ),
        tenant=CurrentSessionTenantResponse(
            id="tenant-1",
            name="Tenant One",
            status="active",
            is_active=True,
        ),
        roles=[],
        permissions=[],
        branches=[],
        default_branch_id=None,
    )


def test_session_route_is_registered(app) -> None:
    rules = {
        (rule.rule, tuple(sorted(rule.methods)))
        for rule in app.url_map.iter_rules()
    }

    assert any(
        rule == "/api/auth/session" and "GET" in methods
        for rule, methods in rules
    )


def test_missing_token_is_rejected(
    client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.auth import decorators

    monkeypatch.setattr(
        decorators,
        "get_current_identity",
        lambda: None,
    )

    response = client.get("/api/auth/session")

    assert response.status_code == 401


def test_active_authenticated_user_receives_session(
    auth_routes,
    client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.auth import decorators

    monkeypatch.setattr(
        decorators,
        "get_current_identity",
        identity,
    )
    monkeypatch.setattr(
        auth_routes.current_session_service,
        "get_current_session",
        lambda _identity: session_response(),
    )

    response = client.get("/api/auth/session")

    assert response.status_code == 200
    assert response.get_json() == {
        "session": asdict(session_response()),
    }
