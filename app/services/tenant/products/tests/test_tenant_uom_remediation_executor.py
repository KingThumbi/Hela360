from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app import create_app
from app.extensions import db
from app.models import (
    CanonicalUnitOfMeasure,
    Product,
    ProductUnit,
    Tenant,
    UnitOfMeasure,
    User,
)
from app.services.common.audit_actions import AuditAction
from app.services.common.audit_modules import AuditModule
from app.services.platform.canonical_uom_catalogue_service import (
    CanonicalUOMCatalogueService,
)
from app.services.tenant.products import (
    LINK_EXISTING_UOM,
    TenantUOMRemediationExecutionError,
    TenantUOMRemediationExecutor,
)
from app.services.tenant.products.tenant_uom_audit_service import (
    MIXED_PRODUCT_SEMANTICS,
    SAFE_TO_LINK,
)
from app.services.tenant.products.tenant_uom_remediation_review_service import (
    TenantUOMRemediationReviewService,
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


# ==================================================================
# C5E3B — real database LINK_EXISTING_UOM execution contract
# ==================================================================


@pytest.fixture()
def integration_app():
    app = create_app()
    app.config.update(TESTING=True)
    return app


class ExecutionAuditSpy:
    def __init__(self):
        self.calls = []

    def log(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            id=str(uuid4())
        )


def _db_tenant(name: str) -> Tenant:
    suffix = uuid4().hex[:8].upper()

    tenant = Tenant(
        legal_name=name,
        display_name=name,
        business_code=f"EX{suffix}",
        workspace_slug=(
            f"uom-executor-{uuid4().hex}"
        ),
    )

    db.session.add(tenant)
    db.session.flush()

    return tenant


def _db_user(
    *,
    tenant: Tenant,
    name: str,
) -> User:
    user = User(
        tenant_id=str(tenant.id),
        first_name=name,
        password_hash="test-password-hash",
        is_active=True,
    )

    db.session.add(user)
    db.session.flush()

    return user


def _db_canonical(
    code: str,
) -> CanonicalUnitOfMeasure:
    return (
        db.session.query(
            CanonicalUnitOfMeasure
        )
        .filter(
            CanonicalUnitOfMeasure.code == code
        )
        .one()
    )


def _db_unit(
    *,
    tenant: Tenant,
    code: str,
    name: str,
) -> UnitOfMeasure:
    unit = UnitOfMeasure(
        tenant_id=str(tenant.id),
        canonical_uom_id=None,
        code=code,
        name=name,
        base_factor=Decimal("1"),
    )

    db.session.add(unit)
    db.session.flush()

    return unit


def _db_product(
    *,
    tenant: Tenant,
    unit: UnitOfMeasure,
    sku: str,
    name: str,
) -> tuple[Product, ProductUnit]:
    product = Product(
        tenant_id=str(tenant.id),
        unit_id=str(unit.id),
        internal_sku=sku,
        name=name,
        product_type="stockable",
        track_inventory=True,
        track_batches=True,
        track_expiry=True,
        requires_prescription=False,
        allow_negative_stock=False,
        reorder_level=Decimal("0"),
        reorder_qty=Decimal("0"),
        is_active=True,
    )

    db.session.add(product)
    db.session.flush()

    product_unit = ProductUnit(
        tenant_id=str(tenant.id),
        product_id=str(product.id),
        unit_id=str(unit.id),
        conversion_factor_to_base=Decimal("1"),
        is_base=True,
        can_sell=True,
        can_receive=True,
        is_active=True,
    )

    db.session.add(product_unit)
    db.session.flush()

    return product, product_unit


def _prepare_execution_catalogue():
    CanonicalUOMCatalogueService(
        db.session
    ).synchronize()


def _approved_link_fixture():
    tenant = _db_tenant(
        "UOM Executor Tenant"
    )

    creator = _db_user(
        tenant=tenant,
        name="Creator",
    )
    reviewer = _db_user(
        tenant=tenant,
        name="Reviewer",
    )
    executor_user = _db_user(
        tenant=tenant,
        name="Executor",
    )

    source = _db_unit(
        tenant=tenant,
        code="TAB",
        name="Tablet",
    )

    product, product_unit = _db_product(
        tenant=tenant,
        unit=source,
        sku=f"EXEC-TAB-{uuid4().hex[:8]}",
        name="Paracetamol Tablets 500mg",
    )

    canonical = _db_canonical("TAB")

    review_audit = ExecutionAuditSpy()

    review_service = (
        TenantUOMRemediationReviewService(
            db.session,
            audit_service=review_audit,
        )
    )

    review = review_service.create_pending_review(
        tenant_id=str(tenant.id),
        source_uom_id=str(source.id),
        created_by=str(creator.id),
    )

    review_service.approve_review(
        tenant_id=str(tenant.id),
        review_id=str(review.id),
        reviewed_by=str(reviewer.id),
        selected_action=LINK_EXISTING_UOM,
        selected_canonical_uom_id=str(
            canonical.id
        ),
        review_reason=(
            "Approved for canonical UOM linkage."
        ),
    )

    return SimpleNamespace(
        tenant=tenant,
        creator=creator,
        reviewer=reviewer,
        executor=executor_user,
        source=source,
        product=product,
        product_unit=product_unit,
        canonical=canonical,
        review=review,
        review_service=review_service,
    )


def test_execute_link_existing_uom_changes_only_canonical_link(
    integration_app,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()
        fixture = _approved_link_fixture()

        source = fixture.source
        product = fixture.product
        product_unit = fixture.product_unit
        review = fixture.review

        product_before = {
            "unit_id": product.unit_id,
        }

        product_unit_before = {
            "id": str(product_unit.id),
            "unit_id": product_unit.unit_id,
            "conversion_factor_to_base": Decimal(
                str(
                    product_unit
                    .conversion_factor_to_base
                )
            ),
            "is_base": product_unit.is_base,
            "can_sell": product_unit.can_sell,
            "can_receive":
                product_unit.can_receive,
            "is_active":
                product_unit.is_active,
        }

        audit = ExecutionAuditSpy()

        service = TenantUOMRemediationExecutor(
            db.session,
            review_service=(
                fixture.review_service
            ),
            audit_service=audit,
        )

        result = (
            service.execute_link_existing_uom(
                tenant_id=str(
                    fixture.tenant.id
                ),
                review_id=str(review.id),
                executed_by=str(
                    fixture.executor.id
                ),
            )
        )

        assert result.status == "executed"
        assert result.changed is True
        assert (
            result.selected_action
            == LINK_EXISTING_UOM
        )
        assert (
            result.selected_canonical_uom_id
            == str(fixture.canonical.id)
        )

        assert (
            source.canonical_uom_id
            == str(fixture.canonical.id)
        )

        assert review.status == "executed"
        assert review.executed_by == str(
            fixture.executor.id
        )
        assert review.executed_at is not None

        summary = review.execution_summary

        assert (
            summary["action"]
            == LINK_EXISTING_UOM
        )
        assert (
            summary["audit_classification"]
            == SAFE_TO_LINK
        )
        assert (
            summary["source_uom_id"]
            == str(source.id)
        )
        assert (
            summary["canonical_uom_id"]
            == str(fixture.canonical.id)
        )
        assert (
            summary["operational_link_changed"]
            is True
        )
        assert summary["product_changes"] == 0
        assert (
            summary["product_unit_changes"]
            == 0
        )
        assert (
            summary["historical_records_changed"]
            == 0
        )

        assert (
            product.unit_id
            == product_before["unit_id"]
        )

        assert (
            str(product_unit.id)
            == product_unit_before["id"]
        )
        assert (
            product_unit.unit_id
            == product_unit_before["unit_id"]
        )
        assert Decimal(
            str(
                product_unit
                .conversion_factor_to_base
            )
        ) == product_unit_before[
            "conversion_factor_to_base"
        ]
        assert (
            product_unit.is_base
            == product_unit_before["is_base"]
        )
        assert (
            product_unit.can_sell
            == product_unit_before["can_sell"]
        )
        assert (
            product_unit.can_receive
            == product_unit_before[
                "can_receive"
            ]
        )
        assert (
            product_unit.is_active
            == product_unit_before[
                "is_active"
            ]
        )

        assert len(audit.calls) == 1

        call = audit.calls[0]

        assert (
            call["module"]
            == AuditModule.CATALOGUE
        )
        assert (
            call["action"]
            == AuditAction
            .UOM_REMEDIATION_REVIEW_EXECUTED
        )
        assert call["commit"] is False
        assert (
            call["tenant_id"]
            == str(fixture.tenant.id)
        )
        assert (
            call["entity_id"]
            == str(review.id)
        )
        assert (
            call["user_id"]
            == str(fixture.executor.id)
        )

        db.session.rollback()


def test_execute_link_existing_uom_rejects_replay(
    integration_app,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()
        fixture = _approved_link_fixture()

        service = TenantUOMRemediationExecutor(
            db.session,
            review_service=(
                fixture.review_service
            ),
            audit_service=ExecutionAuditSpy(),
        )

        service.execute_link_existing_uom(
            tenant_id=str(fixture.tenant.id),
            review_id=str(fixture.review.id),
            executed_by=str(
                fixture.executor.id
            ),
        )

        with pytest.raises(
            TenantUOMRemediationExecutionError
        ) as exc:
            service.execute_link_existing_uom(
                tenant_id=str(
                    fixture.tenant.id
                ),
                review_id=str(
                    fixture.review.id
                ),
                executed_by=str(
                    fixture.executor.id
                ),
            )

        assert exc.value.status_code == 409
        assert "already" in str(
            exc.value
        ).lower()

        db.session.rollback()


def test_execute_link_existing_uom_rejects_stale_review(
    integration_app,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()
        fixture = _approved_link_fixture()

        fixture.product.name = (
            "Changed Product Semantics"
        )
        db.session.flush()

        service = TenantUOMRemediationExecutor(
            db.session,
            review_service=(
                fixture.review_service
            ),
            audit_service=ExecutionAuditSpy(),
        )

        with pytest.raises(
            TenantUOMRemediationExecutionError
        ) as exc:
            service.execute_link_existing_uom(
                tenant_id=str(
                    fixture.tenant.id
                ),
                review_id=str(
                    fixture.review.id
                ),
                executed_by=str(
                    fixture.executor.id
                ),
            )

        assert exc.value.status_code == 409
        assert "stale" in str(
            exc.value
        ).lower()

        assert (
            fixture.source.canonical_uom_id
            is None
        )
        assert fixture.review.status == "approved"

        db.session.rollback()


def test_execute_link_existing_uom_rejects_non_link_action(
    integration_app,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()
        fixture = _approved_link_fixture()

        fixture.review.selected_action = (
            "NO_ACTION"
        )
        db.session.flush()

        service = TenantUOMRemediationExecutor(
            db.session,
            review_service=(
                fixture.review_service
            ),
            audit_service=ExecutionAuditSpy(),
        )

        with pytest.raises(
            TenantUOMRemediationExecutionError
        ) as exc:
            service.execute_link_existing_uom(
                tenant_id=str(
                    fixture.tenant.id
                ),
                review_id=str(
                    fixture.review.id
                ),
                executed_by=str(
                    fixture.executor.id
                ),
            )

        assert exc.value.status_code == 409

        assert (
            fixture.source.canonical_uom_id
            is None
        )
        assert fixture.review.status == "approved"

        db.session.rollback()


def test_execute_link_existing_uom_defends_safe_classification(
    integration_app,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()
        fixture = _approved_link_fixture()

        fixture.review.audit_classification = (
            MIXED_PRODUCT_SEMANTICS
        )
        db.session.flush()

        service = TenantUOMRemediationExecutor(
            db.session,
            review_service=(
                fixture.review_service
            ),
            audit_service=ExecutionAuditSpy(),
        )

        with pytest.raises(
            TenantUOMRemediationExecutionError
        ) as exc:
            service.execute_link_existing_uom(
                tenant_id=str(
                    fixture.tenant.id
                ),
                review_id=str(
                    fixture.review.id
                ),
                executed_by=str(
                    fixture.executor.id
                ),
            )

        assert exc.value.status_code == 409
        assert "safe_to_link" in str(
            exc.value
        ).lower()

        assert (
            fixture.source.canonical_uom_id
            is None
        )

        db.session.rollback()


def test_execute_link_existing_uom_requires_canonical_target(
    integration_app,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()
        fixture = _approved_link_fixture()

        fixture.review.selected_canonical_uom_id = (
            None
        )
        db.session.flush()

        service = TenantUOMRemediationExecutor(
            db.session,
            review_service=(
                fixture.review_service
            ),
            audit_service=ExecutionAuditSpy(),
        )

        with pytest.raises(
            TenantUOMRemediationExecutionError
        ) as exc:
            service.execute_link_existing_uom(
                tenant_id=str(
                    fixture.tenant.id
                ),
                review_id=str(
                    fixture.review.id
                ),
                executed_by=str(
                    fixture.executor.id
                ),
            )

        assert exc.value.status_code == 409
        assert "canonical uom" in str(
            exc.value
        ).lower()

        assert (
            fixture.source.canonical_uom_id
            is None
        )

        db.session.rollback()


def test_execute_link_existing_uom_rejects_already_linked_source(
    integration_app,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()
        fixture = _approved_link_fixture()

        fixture.source.canonical_uom_id = str(
            fixture.canonical.id
        )
        db.session.flush()

        service = TenantUOMRemediationExecutor(
            db.session,
            review_service=(
                fixture.review_service
            ),
            audit_service=ExecutionAuditSpy(),
        )

        with pytest.raises(
            TenantUOMRemediationExecutionError
        ) as exc:
            service.execute_link_existing_uom(
                tenant_id=str(
                    fixture.tenant.id
                ),
                review_id=str(
                    fixture.review.id
                ),
                executed_by=str(
                    fixture.executor.id
                ),
            )

        assert exc.value.status_code == 409
        assert fixture.review.status == "approved"

        db.session.rollback()


def test_execute_link_existing_uom_rejects_inactive_canonical_target(
    integration_app,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()
        fixture = _approved_link_fixture()

        fixture.canonical.is_active = False
        db.session.flush()

        # Isolate canonical-target validation from the planner's
        # broader stale-state protection.
        fixture.review_service.assess_staleness = (
            lambda **_kwargs:
                SimpleNamespace(is_stale=False)
        )

        service = TenantUOMRemediationExecutor(
            db.session,
            review_service=fixture.review_service,
            audit_service=ExecutionAuditSpy(),
        )

        with pytest.raises(
            TenantUOMRemediationExecutionError
        ) as exc:
            service.execute_link_existing_uom(
                tenant_id=str(fixture.tenant.id),
                review_id=str(fixture.review.id),
                executed_by=str(
                    fixture.executor.id
                ),
            )

        assert exc.value.status_code == 404
        assert "inactive" in str(
            exc.value
        ).lower()

        assert (
            fixture.source.canonical_uom_id
            is None
        )
        assert fixture.review.status == "approved"

        db.session.rollback()
