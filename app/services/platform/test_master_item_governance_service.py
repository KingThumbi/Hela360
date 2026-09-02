from __future__ import annotations

from types import SimpleNamespace

import pytest
from sqlalchemy.orm import Session

from app import create_app
from app.extensions import db
from app.models import MasterItem
from app.services.common.audit_actions import AuditAction
from app.services.common.audit_modules import AuditModule
from app.services.platform.master_item_governance_service import (
    MasterItemApprovalConflictError,
    MasterItemGovernanceError,
    MasterItemGovernanceNotFoundError,
    PlatformMasterItemGovernanceService,
)


@pytest.fixture()
def catalogue_session():
    app = create_app()

    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()

        session = Session(
            bind=connection,
            expire_on_commit=False,
        )

        try:
            yield session
        finally:
            session.close()
            transaction.rollback()
            connection.close()


class AuditSpy:
    def __init__(self) -> None:
        self.calls = []

    def log(self, **kwargs):
        self.calls.append(kwargs)

        return SimpleNamespace(
            id=1,
        )


def _master_item(
    *,
    code: str,
    review_status: str,
) -> MasterItem:
    return MasterItem(
        master_code=code,
        canonical_name=f"Test {code}",
        review_status=review_status,
        is_active=True,
    )


def test_approve_draft_master_item(
    catalogue_session,
):
    item = _master_item(
        code="TEST-HMI-APPROVE",
        review_status="draft",
    )

    catalogue_session.add(item)
    catalogue_session.flush()

    audit = AuditSpy()

    result = (
        PlatformMasterItemGovernanceService(
            catalogue_session,
            audit_service=audit,
        ).approve_item(
            master_item_id=item.id,
            user_id="platform-user-1",
            session_id="session-1",
        )
    )

    assert result.master_item.id == item.id

    assert (
        result.master_item.review_status
        == "approved"
    )

    assert len(audit.calls) == 1

    event = audit.calls[0]

    assert event["module"] == AuditModule.CATALOGUE

    assert (
        event["action"]
        == AuditAction
        .MASTER_CATALOGUE_ITEM_APPROVED
    )

    assert event["entity_type"] == "MasterItem"
    assert event["entity_id"] == item.id

    assert event["tenant_id"] is None
    assert event["branch_id"] is None

    assert event["user_id"] == "platform-user-1"
    assert event["session_id"] == "session-1"

    assert event["old_values"] == {
        "review_status": "draft",
    }

    assert event["new_values"] == {
        "review_status": "approved",
    }

    assert event["commit"] is False


def test_approved_item_cannot_be_approved_again(
    catalogue_session,
):
    item = _master_item(
        code="TEST-HMI-ALREADY-APPROVED",
        review_status="approved",
    )

    catalogue_session.add(item)
    catalogue_session.flush()

    audit = AuditSpy()

    service = PlatformMasterItemGovernanceService(
        catalogue_session,
        audit_service=audit,
    )

    with pytest.raises(
        MasterItemApprovalConflictError,
        match="Only draft Master Items can be approved",
    ):
        service.approve_item(
            master_item_id=item.id,
            user_id="platform-user-1",
            session_id="session-1",
        )

    assert item.review_status == "approved"

    assert audit.calls == []


def test_approval_returns_not_found_for_missing_item(
    catalogue_session,
):
    service = PlatformMasterItemGovernanceService(
        catalogue_session,
        audit_service=AuditSpy(),
    )

    with pytest.raises(
        MasterItemGovernanceNotFoundError,
        match="Master Item not found",
    ):
        service.approve_item(
            master_item_id=(
                "00000000-0000-0000-0000-000000000000"
            ),
        )


def test_approval_requires_master_item_id(
    catalogue_session,
):
    service = PlatformMasterItemGovernanceService(
        catalogue_session,
        audit_service=AuditSpy(),
    )

    with pytest.raises(
        MasterItemGovernanceError,
        match="Master item id is required",
    ):
        service.approve_item(
            master_item_id="",
        )
