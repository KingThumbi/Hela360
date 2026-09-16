from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from flask import Flask

from app.api.errors import register_error_handlers
from app.api.products import bp as products_bp
from app.services.tenant.products import (
    TenantUOMRemediationReviewError,
)


@pytest.fixture()
def app_context():
    app = Flask(__name__)
    app.config.update(TESTING=True)

    app.register_blueprint(
        products_bp,
        url_prefix="/api",
    )
    register_error_handlers(app)

    yield app


@pytest.fixture()
def identity():
    return SimpleNamespace(
        user_id="user-1",
        tenant_id="tenant-1",
        branch_id="branch-1",
    )


@pytest.fixture()
def client(
    app_context,
    identity,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "app.services.tenant.auth.decorators."
        "get_current_identity",
        lambda: identity,
    )
    monkeypatch.setattr(
        "app.auth.jwt.get_current_identity",
        lambda: identity,
    )
    monkeypatch.setattr(
        "app.api.products.get_current_identity",
        lambda: identity,
    )
    monkeypatch.setattr(
        "app.services.tenant.auth.decorators."
        "authorization_service.authorize",
        lambda *args, **kwargs: None,
    )

    return app_context.test_client()


def _review(
    *,
    review_id="review-1",
    status="pending",
):
    now = datetime(
        2026,
        9,
        16,
        12,
        0,
        tzinfo=timezone.utc,
    )

    return SimpleNamespace(
        id=review_id,
        tenant_id="tenant-1",
        source_uom_id="unit-1",
        status=status,
        audit_classification="SAFE_TO_LINK",
        recommended_action="LINK_EXISTING_UOM",
        suggested_canonical_code="TAB",
        selected_action=None,
        selected_canonical_uom_id=None,
        planner_version="3F.6C5E1",
        planner_fingerprint="a" * 64,
        planner_snapshot={
            "source_code": "TAB",
            "source_name": "Tablet",
        },
        created_by="user-1",
        reviewed_by=None,
        reviewed_at=None,
        review_reason=None,
        created_at=now,
        updated_at=now,
    )


def _decision():
    now = datetime(
        2026,
        9,
        16,
        12,
        0,
        tzinfo=timezone.utc,
    )

    return SimpleNamespace(
        id="decision-1",
        review_id="review-1",
        tenant_id="tenant-1",
        product_id="product-1",
        source_product_unit_id="product-unit-1",
        recommended_action=(
            "REVIEW_OPERATIONAL_UNIT"
        ),
        suggested_canonical_code="TAB",
        selected_action=None,
        target_canonical_uom_id=None,
        target_tenant_uom_id=None,
        preserve_historical_unit=True,
        review_note=None,
        created_at=now,
        updated_at=now,
    )


def _staleness(*, stale=False):
    reasons = (
        ("planner_fingerprint_changed",)
        if stale
        else ()
    )

    return SimpleNamespace(
        review_id="review-1",
        tenant_id="tenant-1",
        source_uom_id="unit-1",
        is_stale=stale,
        reasons=reasons,
        stored_planner_version="3F.6C5E1",
        current_planner_version="3F.6C5E1",
        stored_fingerprint="a" * 64,
        current_fingerprint=(
            "b" * 64
            if stale
            else "a" * 64
        ),
        current_snapshot={
            "source_code": "TAB",
            "source_name": "Tablet",
        },
    )


def test_review_list_uses_authenticated_tenant(
    client,
    monkeypatch,
):
    calls = []

    class FakeService:
        def __init__(self, session):
            self.session = session

        def list_reviews(
            self,
            *,
            tenant_id,
            status=None,
        ):
            calls.append(
                {
                    "tenant_id": tenant_id,
                    "status": status,
                }
            )
            return (
                _review(),
            )

    monkeypatch.setattr(
        "app.api.products."
        "TenantUOMRemediationReviewService",
        FakeService,
    )

    response = client.get(
        "/api/products/uom-remediation-reviews"
    )

    assert response.status_code == 200
    assert response.json["ok"] is True
    assert response.json["count"] == 1

    assert calls == [
        {
            "tenant_id": "tenant-1",
            "status": None,
        }
    ]

    item = response.json["items"][0]

    assert item["id"] == "review-1"
    assert item["tenant_id"] == "tenant-1"
    assert item["status"] == "pending"
    assert (
        item["planner_fingerprint"]
        == "a" * 64
    )


def test_review_list_passes_status_filter(
    client,
    monkeypatch,
):
    calls = []

    class FakeService:
        def __init__(self, session):
            self.session = session

        def list_reviews(
            self,
            *,
            tenant_id,
            status=None,
        ):
            calls.append(
                (tenant_id, status)
            )
            return ()

    monkeypatch.setattr(
        "app.api.products."
        "TenantUOMRemediationReviewService",
        FakeService,
    )

    response = client.get(
        "/api/products/uom-remediation-reviews"
        "?status=approved"
    )

    assert response.status_code == 200
    assert response.json == {
        "ok": True,
        "count": 0,
        "items": [],
    }

    assert calls == [
        ("tenant-1", "approved")
    ]


def test_review_list_returns_service_validation_error(
    client,
    monkeypatch,
):
    class FakeService:
        def __init__(self, session):
            self.session = session

        def list_reviews(self, **kwargs):
            raise TenantUOMRemediationReviewError(
                "Unsupported remediation review status.",
                400,
            )

    monkeypatch.setattr(
        "app.api.products."
        "TenantUOMRemediationReviewService",
        FakeService,
    )

    response = client.get(
        "/api/products/uom-remediation-reviews"
        "?status=invalid"
    )

    assert response.status_code == 400
    assert response.json == {
        "ok": False,
        "error": (
            "Unsupported remediation review status."
        ),
    }


def test_review_detail_returns_staleness_and_decisions(
    client,
    monkeypatch,
):
    calls = []

    class FakeService:
        def __init__(self, session):
            self.session = session

        def get_review_detail(
            self,
            *,
            tenant_id,
            review_id,
            include_staleness,
        ):
            calls.append(
                {
                    "tenant_id": tenant_id,
                    "review_id": review_id,
                    "include_staleness":
                        include_staleness,
                }
            )

            return {
                "review": _review(),
                "product_decisions": (
                    _decision(),
                ),
                "staleness": _staleness(
                    stale=True
                ),
            }

    monkeypatch.setattr(
        "app.api.products."
        "TenantUOMRemediationReviewService",
        FakeService,
    )

    response = client.get(
        "/api/products/"
        "uom-remediation-reviews/review-1"
    )

    assert response.status_code == 200
    assert response.json["ok"] is True

    assert calls == [
        {
            "tenant_id": "tenant-1",
            "review_id": "review-1",
            "include_staleness": True,
        }
    ]

    assert (
        response.json["item"]["id"]
        == "review-1"
    )

    assert len(
        response.json["product_decisions"]
    ) == 1

    assert (
        response.json[
            "product_decisions"
        ][0]["product_id"]
        == "product-1"
    )

    assert (
        response.json["staleness"][
            "is_stale"
        ]
        is True
    )

    assert response.json[
        "staleness"
    ]["reasons"] == [
        "planner_fingerprint_changed"
    ]


def test_review_detail_returns_tenant_scoped_not_found(
    client,
    monkeypatch,
):
    class FakeService:
        def __init__(self, session):
            self.session = session

        def get_review_detail(
            self,
            **kwargs,
        ):
            raise TenantUOMRemediationReviewError(
                "UOM remediation review was not found.",
                404,
            )

    monkeypatch.setattr(
        "app.api.products."
        "TenantUOMRemediationReviewService",
        FakeService,
    )

    response = client.get(
        "/api/products/"
        "uom-remediation-reviews/missing"
    )

    assert response.status_code == 404
    assert response.json == {
        "ok": False,
        "error": (
            "UOM remediation review was not found."
        ),
    }
