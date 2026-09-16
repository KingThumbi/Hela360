from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services.tenant.products import (
    LINK_EXISTING_UOM,
    TenantUOMRemediationExecutionError,
    TenantUOMRemediationExecutor,
)


def _review(
    *,
    status="approved",
    selected_action=LINK_EXISTING_UOM,
):
    return SimpleNamespace(
        id="review-1",
        tenant_id="tenant-1",
        source_uom_id="uom-1",
        status=status,
        selected_action=selected_action,
        planner_fingerprint="a" * 64,
    )


def _executor_user():
    return SimpleNamespace(
        id="user-1",
        tenant_id="tenant-1",
        is_active=True,
    )


def _session(*, user=None):
    session = MagicMock()

    query = session.query.return_value
    filtered = query.filter.return_value

    filtered.first.return_value = (
        _executor_user()
        if user is None
        else user
    )

    return session


class FakeReviewService:
    def __init__(
        self,
        *,
        review,
        stale=False,
        decision_count=0,
    ):
        self.review = review
        self.stale = stale
        self.decision_count = decision_count

        self.get_review_calls = []
        self.staleness_calls = []
        self.detail_calls = []

    def get_review(
        self,
        *,
        tenant_id,
        review_id,
    ):
        self.get_review_calls.append(
            {
                "tenant_id": tenant_id,
                "review_id": review_id,
            }
        )

        return self.review

    def assess_staleness(
        self,
        *,
        tenant_id,
        review_id,
    ):
        self.staleness_calls.append(
            {
                "tenant_id": tenant_id,
                "review_id": review_id,
            }
        )

        return SimpleNamespace(
            is_stale=self.stale,
        )

    def get_review_detail(
        self,
        *,
        tenant_id,
        review_id,
        include_staleness,
    ):
        self.detail_calls.append(
            {
                "tenant_id": tenant_id,
                "review_id": review_id,
                "include_staleness":
                    include_staleness,
            }
        )

        return {
            "review": self.review,
            "product_decisions": tuple(
                SimpleNamespace(
                    id=f"decision-{index}"
                )
                for index
                in range(self.decision_count)
            ),
            "staleness": None,
        }


def test_preflight_accepts_fresh_approved_review():
    review = _review()

    review_service = FakeReviewService(
        review=review,
        stale=False,
        decision_count=2,
    )

    session = _session()

    executor = TenantUOMRemediationExecutor(
        session,
        review_service=review_service,
    )

    result = executor.preflight(
        tenant_id="tenant-1",
        review_id="review-1",
        executed_by="user-1",
    )

    assert result.review_id == "review-1"
    assert result.tenant_id == "tenant-1"
    assert result.source_uom_id == "uom-1"
    assert result.status == "approved"
    assert result.selected_action == LINK_EXISTING_UOM
    assert result.product_decision_count == 2
    assert result.planner_fingerprint == "a" * 64
    assert result.is_stale is False
    assert result.can_execute is True

    assert review_service.staleness_calls == [
        {
            "tenant_id": "tenant-1",
            "review_id": "review-1",
        }
    ]

    assert review_service.detail_calls == [
        {
            "tenant_id": "tenant-1",
            "review_id": "review-1",
            "include_staleness": False,
        }
    ]

    session.add.assert_not_called()
    session.delete.assert_not_called()
    session.flush.assert_not_called()
    session.commit.assert_not_called()


@pytest.mark.parametrize(
    "status",
    [
        "pending",
        "rejected",
        "superseded",
    ],
)
def test_preflight_rejects_non_approved_review(
    status,
):
    review = _review(
        status=status,
    )

    review_service = FakeReviewService(
        review=review,
    )

    executor = TenantUOMRemediationExecutor(
        _session(),
        review_service=review_service,
    )

    with pytest.raises(
        TenantUOMRemediationExecutionError
    ) as exc:
        executor.preflight(
            tenant_id="tenant-1",
            review_id="review-1",
            executed_by="user-1",
        )

    assert exc.value.status_code == 409
    assert "approved" in str(exc.value).lower()

    assert review_service.staleness_calls == []
    assert review_service.detail_calls == []


def test_preflight_rejects_executed_replay():
    review = _review(
        status="executed",
    )

    review_service = FakeReviewService(
        review=review,
    )

    executor = TenantUOMRemediationExecutor(
        _session(),
        review_service=review_service,
    )

    with pytest.raises(
        TenantUOMRemediationExecutionError
    ) as exc:
        executor.preflight(
            tenant_id="tenant-1",
            review_id="review-1",
            executed_by="user-1",
        )

    assert exc.value.status_code == 409
    assert "already been executed" in str(
        exc.value
    ).lower()

    assert review_service.staleness_calls == []
    assert review_service.detail_calls == []


def test_preflight_rejects_stale_approval():
    review = _review()

    review_service = FakeReviewService(
        review=review,
        stale=True,
    )

    executor = TenantUOMRemediationExecutor(
        _session(),
        review_service=review_service,
    )

    with pytest.raises(
        TenantUOMRemediationExecutionError
    ) as exc:
        executor.preflight(
            tenant_id="tenant-1",
            review_id="review-1",
            executed_by="user-1",
        )

    assert exc.value.status_code == 409
    assert "stale" in str(exc.value).lower()

    assert review_service.detail_calls == []


def test_preflight_requires_selected_action():
    review = _review(
        selected_action=None,
    )

    review_service = FakeReviewService(
        review=review,
    )

    executor = TenantUOMRemediationExecutor(
        _session(),
        review_service=review_service,
    )

    with pytest.raises(
        TenantUOMRemediationExecutionError
    ) as exc:
        executor.preflight(
            tenant_id="tenant-1",
            review_id="review-1",
            executed_by="user-1",
        )

    assert exc.value.status_code == 409
    assert "selected action" in str(
        exc.value
    ).lower()

    assert review_service.staleness_calls == []


def test_preflight_rejects_unsupported_action():
    review = _review(
        selected_action="INVALID_EXECUTION_ACTION",
    )

    review_service = FakeReviewService(
        review=review,
    )

    executor = TenantUOMRemediationExecutor(
        _session(),
        review_service=review_service,
    )

    with pytest.raises(
        TenantUOMRemediationExecutionError
    ) as exc:
        executor.preflight(
            tenant_id="tenant-1",
            review_id="review-1",
            executed_by="user-1",
        )

    assert exc.value.status_code == 409
    assert "unsupported" in str(
        exc.value
    ).lower()

    assert review_service.staleness_calls == []


def test_preflight_requires_active_tenant_executor():
    review = _review()

    review_service = FakeReviewService(
        review=review,
    )

    session = MagicMock()
    session.query.return_value.filter.return_value.first.return_value = (
        None
    )

    executor = TenantUOMRemediationExecutor(
        session,
        review_service=review_service,
    )

    with pytest.raises(
        TenantUOMRemediationExecutionError
    ) as exc:
        executor.preflight(
            tenant_id="tenant-1",
            review_id="review-1",
            executed_by="missing-user",
        )

    assert exc.value.status_code == 404
    assert "executing user" in str(
        exc.value
    ).lower()

    assert review_service.staleness_calls == []
    assert review_service.detail_calls == []


def test_preflight_does_not_mutate_review():
    review = _review()

    before = {
        "status": review.status,
        "selected_action":
            review.selected_action,
        "planner_fingerprint":
            review.planner_fingerprint,
    }

    review_service = FakeReviewService(
        review=review,
        stale=False,
    )

    session = _session()

    executor = TenantUOMRemediationExecutor(
        session,
        review_service=review_service,
    )

    executor.preflight(
        tenant_id="tenant-1",
        review_id="review-1",
        executed_by="user-1",
    )

    assert review.status == before["status"]
    assert (
        review.selected_action
        == before["selected_action"]
    )
    assert (
        review.planner_fingerprint
        == before["planner_fingerprint"]
    )

    session.add.assert_not_called()
    session.delete.assert_not_called()
    session.flush.assert_not_called()
    session.commit.assert_not_called()
