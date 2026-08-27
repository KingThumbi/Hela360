from __future__ import annotations

from types import SimpleNamespace

import pytest
from flask import Flask

from app.api.dashboard import bp as dashboard_bp
from app.api.errors import register_error_handlers


@pytest.fixture()
def app(monkeypatch: pytest.MonkeyPatch) -> Flask:
    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        SECRET_KEY="dashboard-contract-test",
    )

    app.register_blueprint(
        dashboard_bp,
        url_prefix="/api",
    )

    register_error_handlers(app)

    return app


def test_dashboard_route_is_registered(
    app: Flask,
) -> None:
    rules = {
        rule.rule
        for rule in app.url_map.iter_rules()
    }

    assert "/api/dashboard/overview" in rules
