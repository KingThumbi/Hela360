from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app import create_app
from app.extensions import db
from app.models import (
    Branch,
    CanonicalUnitOfMeasure,
    GoodsReceipt,
    GoodsReceiptItem,
    Product,
    ProductUnit,
    Tenant,
    TenantUOMRemediationProductDecision,
    UnitOfMeasure,
    User,
    Warehouse,
)
from app.services.common.audit_actions import AuditAction
from app.services.common.audit_modules import AuditModule
from app.services.platform.canonical_uom_catalogue_service import (
    CanonicalUOMCatalogueService,
)
from app.services.tenant.products import (
    LINK_EXISTING_UOM,
    NO_ACTION,
    PRESERVE_HISTORICAL_UNIT,
    SPLIT_CURRENT_PRODUCTS,
    TenantUOMRemediationExecutionError,
    TenantUOMRemediationExecutor,
)
from app.services.tenant.products.tenant_uom_audit_service import (
    CANONICALLY_LINKED,
    CUSTOM_UNMAPPED,
    DOSAGE_FORM_AS_UOM,
    HISTORICAL_ONLY,
    LEGACY_PRODUCT_SPECIFIC,
    MIXED_PRODUCT_SEMANTICS,
    SAFE_TO_LINK,
)
from app.services.tenant.products.tenant_uom_remediation_review_service import (
    KEEP_CURRENT_PRODUCT,
    KEEP_UNMAPPED,
    MOVE_CURRENT_PRODUCT,
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
    canonical_code: str | None = None,
) -> UnitOfMeasure:
    canonical_uom_id = None

    if canonical_code is not None:
        canonical_uom_id = str(
            _db_canonical(canonical_code).id
        )

    unit = UnitOfMeasure(
        tenant_id=str(tenant.id),
        canonical_uom_id=canonical_uom_id,
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


def _db_branch_and_warehouse(
    *,
    tenant: Tenant,
) -> tuple[Branch, Warehouse]:
    suffix = uuid4().hex[:8].upper()

    branch = Branch(
        tenant_id=str(tenant.id),
        code=f"BR{suffix}",
        name=f"Executor Branch {suffix}",
        is_active=True,
    )

    db.session.add(branch)
    db.session.flush()

    warehouse = Warehouse(
        tenant_id=str(tenant.id),
        branch_id=str(branch.id),
        code=f"WH{suffix}",
        name=f"Executor Warehouse {suffix}",
        warehouse_type="main",
        is_active=True,
    )

    db.session.add(warehouse)
    db.session.flush()

    return branch, warehouse


def _db_historical_receipt_evidence(
    *,
    tenant: Tenant,
    branch: Branch,
    warehouse: Warehouse,
    product: Product,
    product_unit: ProductUnit,
    source_uom: UnitOfMeasure,
    user: User,
) -> tuple[GoodsReceipt, GoodsReceiptItem]:
    now = datetime.now(timezone.utc)
    suffix = uuid4().hex

    receipt = GoodsReceipt(
        tenant_id=str(tenant.id),
        branch_id=str(branch.id),
        warehouse_id=str(warehouse.id),
        supplier_id=None,
        receipt_number=f"GRN-UOM-{suffix[:12]}",
        supplier_reference="UOM-HISTORY",
        idempotency_key=f"uom-history-{suffix}",
        request_fingerprint=(suffix * 2)[:64],
        created_by=str(user.id),
        received_at=now,
        received_by=str(user.id),
        status="received",
    )

    db.session.add(receipt)
    db.session.flush()

    item = GoodsReceiptItem(
        goods_receipt_id=str(receipt.id),
        product_id=str(product.id),
        product_unit_id=str(product_unit.id),
        batch_id=None,
        line_number=1,
        quantity=Decimal("5.0000"),
        received_quantity=Decimal("5.0000"),
        accepted_quantity=Decimal("5.0000"),
        rejected_quantity=Decimal("0.0000"),
        bonus_quantity=Decimal("0.0000"),
        base_quantity=Decimal("5.0000"),
        unit_code_snapshot=source_uom.code,
        unit_name_snapshot=source_uom.name,
        conversion_factor_to_base=Decimal("1.000000"),
        batch_number="UOM-HISTORY-BATCH",
        unit_cost=Decimal("12.50"),
        base_unit_cost=Decimal("12.50"),
    )

    db.session.add(item)
    db.session.flush()

    return receipt, item


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



@pytest.mark.parametrize(
    ("selected_action", "method_name"),
    [
        (
            LINK_EXISTING_UOM,
            "execute_link_existing_uom",
        ),
        (
            SPLIT_CURRENT_PRODUCTS,
            "execute_split_current_products",
        ),
        (
            KEEP_UNMAPPED,
            "execute_keep_unmapped",
        ),
        (
            PRESERVE_HISTORICAL_UNIT,
            "execute_preserve_historical_unit",
        ),
        (
            NO_ACTION,
            "execute_no_action",
        ),
    ],
)
def test_execute_review_dispatches_all_actions(
    selected_action,
    method_name,
):
    review_service = MagicMock()

    review_service.get_review.return_value = (
        SimpleNamespace(
            selected_action=selected_action,
        )
    )

    service = TenantUOMRemediationExecutor(
        MagicMock(),
        review_service=review_service,
        audit_service=MagicMock(),
    )

    expected = SimpleNamespace(
        selected_action=selected_action,
    )

    method = MagicMock(
        return_value=expected
    )

    setattr(
        service,
        method_name,
        method,
    )

    result = service.execute_review(
        tenant_id="tenant-1",
        review_id="review-1",
        executed_by="user-1",
    )

    assert result is expected

    review_service.get_review.assert_called_once_with(
        tenant_id="tenant-1",
        review_id="review-1",
    )

    method.assert_called_once_with(
        tenant_id="tenant-1",
        review_id="review-1",
        executed_by="user-1",
    )


@pytest.mark.parametrize(
    "selected_action",
    [
        None,
        "",
        "REVIEW_OPERATIONAL_UNIT",
        "REVIEW_LEGACY_UNIT",
        "UNKNOWN_ACTION",
    ],
)
def test_execute_review_rejects_non_executable_action(
    selected_action,
):
    review_service = MagicMock()

    review_service.get_review.return_value = (
        SimpleNamespace(
            selected_action=selected_action,
        )
    )

    service = TenantUOMRemediationExecutor(
        MagicMock(),
        review_service=review_service,
        audit_service=MagicMock(),
    )

    with pytest.raises(
        TenantUOMRemediationExecutionError
    ) as exc:
        service.execute_review(
            tenant_id="tenant-1",
            review_id="review-1",
            executed_by="user-1",
        )

    assert exc.value.status_code == 409

    assert (
        "supported executable action"
        in str(exc.value)
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




def _approved_keep_unmapped_fixture(
    *,
    code="WHOLE",
    name="Whole",
    sku=None,
    product_name="Custom Product",
):
    tenant = _db_tenant(
        f"UOM Keep Unmapped {uuid4().hex[:8]}"
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
        code=code,
        name=name,
    )

    product, product_unit = _db_product(
        tenant=tenant,
        unit=source,
        sku=(
            sku
            or f"KEEP-{uuid4().hex[:8]}"
        ),
        name=product_name,
    )

    review_service = TenantUOMRemediationReviewService(
        db.session,
        audit_service=ExecutionAuditSpy(),
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
        selected_action=KEEP_UNMAPPED,
        review_reason=(
            "Retain tenant-specific UOM without canonical linkage."
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
        review=review,
        review_service=review_service,
    )


def _approved_historical_preservation_fixture():
    tenant = _db_tenant(
        "UOM Historical Executor Tenant"
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
        code="HIST",
        name="Historical Unit",
    )

    product, historical_product_unit = _db_product(
        tenant=tenant,
        unit=source,
        sku=f"HIST-{uuid4().hex[:8]}",
        name="Historical Executor Product",
    )

    branch, warehouse = _db_branch_and_warehouse(
        tenant=tenant,
    )

    historical_receipt, historical_receipt_item = (
        _db_historical_receipt_evidence(
            tenant=tenant,
            branch=branch,
            warehouse=warehouse,
            product=product,
            product_unit=historical_product_unit,
            source_uom=source,
            user=creator,
        )
    )

    current_uom = _db_unit(
        tenant=tenant,
        code=f"EA-HIST-{uuid4().hex[:6].upper()}",
        name="Current Each Unit",
        canonical_code="EA",
    )

    current_product_unit = ProductUnit(
        tenant_id=str(tenant.id),
        product_id=str(product.id),
        unit_id=str(current_uom.id),
        conversion_factor_to_base=Decimal("1"),
        is_base=False,
        can_sell=True,
        can_receive=True,
        is_active=True,
    )

    db.session.add(current_product_unit)
    db.session.flush()

    historical_product_unit.is_base = False
    historical_product_unit.is_active = False
    historical_product_unit.can_sell = False
    historical_product_unit.can_receive = False

    db.session.flush()

    current_product_unit.is_base = True
    product.unit_id = str(current_uom.id)

    db.session.flush()

    review_service = TenantUOMRemediationReviewService(
        db.session,
        audit_service=ExecutionAuditSpy(),
    )

    review = review_service.create_pending_review(
        tenant_id=str(tenant.id),
        source_uom_id=str(source.id),
        created_by=str(creator.id),
    )

    assert review.audit_classification == HISTORICAL_ONLY

    review_service.approve_review(
        tenant_id=str(tenant.id),
        review_id=str(review.id),
        reviewed_by=str(reviewer.id),
        selected_action=PRESERVE_HISTORICAL_UNIT,
        review_reason=(
            "Preserve historical UOM and transactional evidence."
        ),
    )

    return SimpleNamespace(
        tenant=tenant,
        creator=creator,
        reviewer=reviewer,
        executor=executor_user,
        source=source,
        product=product,
        historical_product_unit=historical_product_unit,
        current_uom=current_uom,
        current_product_unit=current_product_unit,
        historical_receipt=historical_receipt,
        historical_receipt_item=historical_receipt_item,
        review=review,
        review_service=review_service,
    )


def _approved_no_action_fixture():
    tenant = _db_tenant(
        "UOM No Action Executor Tenant"
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
        code="EA",
        name="Each",
        canonical_code="EA",
    )

    product, product_unit = _db_product(
        tenant=tenant,
        unit=source,
        sku=f"NOACT-{uuid4().hex[:8]}",
        name="No Action Executor Product",
    )

    review_service = TenantUOMRemediationReviewService(
        db.session,
        audit_service=ExecutionAuditSpy(),
    )

    review = review_service.create_pending_review(
        tenant_id=str(tenant.id),
        source_uom_id=str(source.id),
        created_by=str(creator.id),
    )

    assert (
        review.audit_classification
        == CANONICALLY_LINKED
    )

    review_service.approve_review(
        tenant_id=str(tenant.id),
        review_id=str(review.id),
        reviewed_by=str(reviewer.id),
        selected_action=NO_ACTION,
        review_reason=(
            "Existing canonical linkage requires no mutation."
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
        review=review,
        review_service=review_service,
    )



@pytest.mark.parametrize(
    (
        "code",
        "name",
        "product_name",
        "expected_classification",
    ),
    [
        (
            "TAB",
            "Tablet",
            "Paracetamol Tablets 500mg",
            SAFE_TO_LINK,
        ),
        (
            "WHOLE",
            "Whole",
            "Custom Product",
            CUSTOM_UNMAPPED,
        ),
        (
            "Syrup",
            "Syrup",
            "Piriton Syrup 100ml",
            DOSAGE_FORM_AS_UOM,
        ),
        (
            "M084-TAB",
            "M084 Tablet",
            "M084 Paracetamol Tablet",
            LEGACY_PRODUCT_SPECIFIC,
        ),
    ],
)
def test_execute_keep_unmapped_is_non_mutating(
    integration_app,
    code,
    name,
    product_name,
    expected_classification,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()

        fixture = _approved_keep_unmapped_fixture(
            code=code,
            name=name,
            product_name=product_name,
        )

        assert (
            fixture.review.audit_classification
            == expected_classification
        )

        source_before = {
            "canonical_uom_id":
                fixture.source.canonical_uom_id,
            "code": fixture.source.code,
            "name": fixture.source.name,
        }

        product_before = fixture.product.unit_id

        product_unit_before = {
            "id": str(fixture.product_unit.id),
            "unit_id":
                str(fixture.product_unit.unit_id),
            "factor": Decimal(
                str(
                    fixture.product_unit
                    .conversion_factor_to_base
                )
            ),
            "is_base": fixture.product_unit.is_base,
            "is_active":
                fixture.product_unit.is_active,
            "can_sell": fixture.product_unit.can_sell,
            "can_receive":
                fixture.product_unit.can_receive,
        }

        audit = ExecutionAuditSpy()

        service = TenantUOMRemediationExecutor(
            db.session,
            review_service=fixture.review_service,
            audit_service=audit,
        )

        result = service.execute_keep_unmapped(
            tenant_id=str(fixture.tenant.id),
            review_id=str(fixture.review.id),
            executed_by=str(fixture.executor.id),
        )

        assert result.status == "executed"
        assert result.changed is False
        assert result.selected_action == KEEP_UNMAPPED
        assert result.selected_canonical_uom_id is None

        db.session.refresh(fixture.source)
        db.session.refresh(fixture.product)
        db.session.refresh(fixture.product_unit)
        db.session.refresh(fixture.review)

        assert (
            fixture.source.canonical_uom_id
            == source_before["canonical_uom_id"]
        )
        assert fixture.source.code == source_before["code"]
        assert fixture.source.name == source_before["name"]

        assert fixture.product.unit_id == product_before

        assert (
            str(fixture.product_unit.id)
            == product_unit_before["id"]
        )
        assert (
            str(fixture.product_unit.unit_id)
            == product_unit_before["unit_id"]
        )
        assert Decimal(
            str(
                fixture.product_unit
                .conversion_factor_to_base
            )
        ) == product_unit_before["factor"]
        assert (
            fixture.product_unit.is_base
            == product_unit_before["is_base"]
        )
        assert (
            fixture.product_unit.is_active
            == product_unit_before["is_active"]
        )
        assert (
            fixture.product_unit.can_sell
            == product_unit_before["can_sell"]
        )
        assert (
            fixture.product_unit.can_receive
            == product_unit_before["can_receive"]
        )

        assert fixture.review.status == "executed"
        assert (
            fixture.review.executed_by
            == str(fixture.executor.id)
        )
        assert fixture.review.executed_at is not None

        summary = fixture.review.execution_summary

        assert summary["action"] == KEEP_UNMAPPED
        assert (
            summary["audit_classification"]
            == expected_classification
        )
        assert (
            summary["operational_link_changed"]
            is False
        )
        assert summary["product_changes"] == 0
        assert summary["product_unit_changes"] == 0
        assert (
            summary["historical_records_changed"]
            == 0
        )
        assert (
            summary["selected_product_decision_count"]
            == 0
        )

        assert len(audit.calls) == 1
        assert (
            audit.calls[0]["action"]
            == AuditAction
            .UOM_REMEDIATION_REVIEW_EXECUTED
        )
        assert audit.calls[0]["commit"] is False

        db.session.rollback()


def test_execute_keep_unmapped_rejects_replay(
    integration_app,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()
        fixture = _approved_keep_unmapped_fixture()

        service = TenantUOMRemediationExecutor(
            db.session,
            review_service=fixture.review_service,
            audit_service=ExecutionAuditSpy(),
        )

        service.execute_keep_unmapped(
            tenant_id=str(fixture.tenant.id),
            review_id=str(fixture.review.id),
            executed_by=str(fixture.executor.id),
        )

        with pytest.raises(
            TenantUOMRemediationExecutionError
        ) as exc:
            service.execute_keep_unmapped(
                tenant_id=str(fixture.tenant.id),
                review_id=str(fixture.review.id),
                executed_by=str(fixture.executor.id),
            )

        assert exc.value.status_code == 409
        assert "already been executed" in str(
            exc.value
        )

        db.session.rollback()


def test_execute_keep_unmapped_rejects_stale_review(
    integration_app,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()
        fixture = _approved_keep_unmapped_fixture()

        fixture.source.name = "Whole Changed"
        db.session.flush()

        service = TenantUOMRemediationExecutor(
            db.session,
            review_service=fixture.review_service,
            audit_service=ExecutionAuditSpy(),
        )

        with pytest.raises(
            TenantUOMRemediationExecutionError
        ) as exc:
            service.execute_keep_unmapped(
                tenant_id=str(fixture.tenant.id),
                review_id=str(fixture.review.id),
                executed_by=str(fixture.executor.id),
            )

        assert exc.value.status_code == 409
        assert "stale" in str(exc.value).lower()
        assert fixture.review.status == "approved"

        db.session.rollback()


def test_execute_keep_unmapped_rejects_selected_canonical(
    integration_app,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()
        fixture = _approved_keep_unmapped_fixture()

        canonical = (
            db.session.query(CanonicalUnitOfMeasure)
            .filter(
                CanonicalUnitOfMeasure.code == "EA"
            )
            .one()
        )

        fixture.review.selected_canonical_uom_id = str(
            canonical.id
        )
        db.session.flush()

        service = TenantUOMRemediationExecutor(
            db.session,
            review_service=fixture.review_service,
            audit_service=ExecutionAuditSpy(),
        )

        with pytest.raises(
            TenantUOMRemediationExecutionError
        ) as exc:
            service.execute_keep_unmapped(
                tenant_id=str(fixture.tenant.id),
                review_id=str(fixture.review.id),
                executed_by=str(fixture.executor.id),
            )

        assert exc.value.status_code == 409
        assert "selected canonical" in str(
            exc.value
        ).lower()

        db.session.rollback()


def test_execute_keep_unmapped_rejects_product_decision_tamper(
    integration_app,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()
        fixture = _approved_keep_unmapped_fixture()

        decision = (
            db.session.query(
                TenantUOMRemediationProductDecision
            )
            .filter(
                TenantUOMRemediationProductDecision.review_id
                == str(fixture.review.id)
            )
            .one()
        )

        decision.review_note = "tampered"
        db.session.flush()

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
            service.execute_keep_unmapped(
                tenant_id=str(fixture.tenant.id),
                review_id=str(fixture.review.id),
                executed_by=str(fixture.executor.id),
            )

        assert exc.value.status_code == 409
        assert "product-level" in str(
            exc.value
        ).lower()
        assert fixture.review.status == "approved"

        db.session.rollback()


def test_execute_keep_unmapped_defends_locked_classification(
    integration_app,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()
        fixture = _approved_keep_unmapped_fixture()

        fixture.source.code = "TAB"
        fixture.source.name = "Tablet"
        db.session.flush()

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
            service.execute_keep_unmapped(
                tenant_id=str(fixture.tenant.id),
                review_id=str(fixture.review.id),
                executed_by=str(fixture.executor.id),
            )

        assert exc.value.status_code == 409
        assert "approved audit classification" in str(
            exc.value
        ).lower()
        assert fixture.review.status == "approved"

        db.session.rollback()


def test_execute_preserve_historical_unit_is_non_mutating(
    integration_app,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()
        fixture = (
            _approved_historical_preservation_fixture()
        )

        old_product_unit = (
            fixture.historical_product_unit
        )
        receipt_item = fixture.historical_receipt_item

        source_before = {
            "canonical_uom_id":
                fixture.source.canonical_uom_id,
            "code": fixture.source.code,
            "name": fixture.source.name,
        }

        product_before = {
            "unit_id": fixture.product.unit_id,
        }

        old_product_unit_before = {
            "id": str(old_product_unit.id),
            "unit_id": str(old_product_unit.unit_id),
            "factor": Decimal(
                str(
                    old_product_unit
                    .conversion_factor_to_base
                )
            ),
            "is_base": old_product_unit.is_base,
            "is_active": old_product_unit.is_active,
            "can_sell": old_product_unit.can_sell,
            "can_receive":
                old_product_unit.can_receive,
        }

        receipt_before = {
            "id": str(receipt_item.id),
            "product_unit_id":
                str(receipt_item.product_unit_id),
            "unit_code_snapshot":
                receipt_item.unit_code_snapshot,
            "unit_name_snapshot":
                receipt_item.unit_name_snapshot,
            "factor": Decimal(
                str(
                    receipt_item
                    .conversion_factor_to_base
                )
            ),
            "quantity": Decimal(
                str(receipt_item.quantity)
            ),
            "base_quantity": Decimal(
                str(receipt_item.base_quantity)
            ),
        }

        audit = ExecutionAuditSpy()

        service = TenantUOMRemediationExecutor(
            db.session,
            review_service=fixture.review_service,
            audit_service=audit,
        )

        result = (
            service.execute_preserve_historical_unit(
                tenant_id=str(fixture.tenant.id),
                review_id=str(fixture.review.id),
                executed_by=str(fixture.executor.id),
            )
        )

        assert result.status == "executed"
        assert result.changed is False
        assert (
            result.selected_action
            == PRESERVE_HISTORICAL_UNIT
        )

        db.session.refresh(fixture.source)
        db.session.refresh(fixture.product)
        db.session.refresh(old_product_unit)
        db.session.refresh(receipt_item)
        db.session.refresh(fixture.review)

        assert (
            fixture.source.canonical_uom_id
            == source_before["canonical_uom_id"]
        )
        assert fixture.source.code == source_before["code"]
        assert fixture.source.name == source_before["name"]

        assert (
            fixture.product.unit_id
            == product_before["unit_id"]
        )

        assert (
            str(old_product_unit.id)
            == old_product_unit_before["id"]
        )
        assert (
            str(old_product_unit.unit_id)
            == old_product_unit_before["unit_id"]
        )
        assert Decimal(
            str(
                old_product_unit
                .conversion_factor_to_base
            )
        ) == old_product_unit_before["factor"]
        assert (
            old_product_unit.is_base
            == old_product_unit_before["is_base"]
        )
        assert (
            old_product_unit.is_active
            == old_product_unit_before["is_active"]
        )
        assert (
            old_product_unit.can_sell
            == old_product_unit_before["can_sell"]
        )
        assert (
            old_product_unit.can_receive
            == old_product_unit_before["can_receive"]
        )

        assert (
            str(receipt_item.id)
            == receipt_before["id"]
        )
        assert (
            str(receipt_item.product_unit_id)
            == receipt_before["product_unit_id"]
        )
        assert (
            receipt_item.unit_code_snapshot
            == receipt_before["unit_code_snapshot"]
        )
        assert (
            receipt_item.unit_name_snapshot
            == receipt_before["unit_name_snapshot"]
        )
        assert Decimal(
            str(
                receipt_item
                .conversion_factor_to_base
            )
        ) == receipt_before["factor"]
        assert Decimal(
            str(receipt_item.quantity)
        ) == receipt_before["quantity"]
        assert Decimal(
            str(receipt_item.base_quantity)
        ) == receipt_before["base_quantity"]

        assert fixture.review.status == "executed"
        assert (
            fixture.review.executed_by
            == str(fixture.executor.id)
        )
        assert fixture.review.executed_at is not None

        summary = fixture.review.execution_summary

        assert (
            summary["action"]
            == PRESERVE_HISTORICAL_UNIT
        )
        assert (
            summary["audit_classification"]
            == HISTORICAL_ONLY
        )
        assert (
            summary["operational_link_changed"]
            is False
        )
        assert summary["product_changes"] == 0
        assert summary["product_unit_changes"] == 0
        assert (
            summary["historical_records_changed"]
            == 0
        )

        assert len(audit.calls) == 1
        assert (
            audit.calls[0]["action"]
            == AuditAction
            .UOM_REMEDIATION_REVIEW_EXECUTED
        )
        assert audit.calls[0]["commit"] is False

        db.session.rollback()


def test_execute_no_action_is_non_mutating(
    integration_app,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()
        fixture = _approved_no_action_fixture()

        source_before = {
            "canonical_uom_id":
                fixture.source.canonical_uom_id,
            "code": fixture.source.code,
            "name": fixture.source.name,
        }

        product_before = {
            "unit_id": fixture.product.unit_id,
        }

        product_unit_before = {
            "id": str(fixture.product_unit.id),
            "unit_id":
                str(fixture.product_unit.unit_id),
            "factor": Decimal(
                str(
                    fixture.product_unit
                    .conversion_factor_to_base
                )
            ),
            "is_base": fixture.product_unit.is_base,
            "is_active":
                fixture.product_unit.is_active,
            "can_sell": fixture.product_unit.can_sell,
            "can_receive":
                fixture.product_unit.can_receive,
        }

        audit = ExecutionAuditSpy()

        service = TenantUOMRemediationExecutor(
            db.session,
            review_service=fixture.review_service,
            audit_service=audit,
        )

        result = service.execute_no_action(
            tenant_id=str(fixture.tenant.id),
            review_id=str(fixture.review.id),
            executed_by=str(fixture.executor.id),
        )

        assert result.status == "executed"
        assert result.changed is False
        assert result.selected_action == NO_ACTION

        db.session.refresh(fixture.source)
        db.session.refresh(fixture.product)
        db.session.refresh(fixture.product_unit)
        db.session.refresh(fixture.review)

        assert (
            fixture.source.canonical_uom_id
            == source_before["canonical_uom_id"]
        )
        assert fixture.source.code == source_before["code"]
        assert fixture.source.name == source_before["name"]

        assert (
            fixture.product.unit_id
            == product_before["unit_id"]
        )

        assert (
            str(fixture.product_unit.id)
            == product_unit_before["id"]
        )
        assert (
            str(fixture.product_unit.unit_id)
            == product_unit_before["unit_id"]
        )
        assert Decimal(
            str(
                fixture.product_unit
                .conversion_factor_to_base
            )
        ) == product_unit_before["factor"]
        assert (
            fixture.product_unit.is_base
            == product_unit_before["is_base"]
        )
        assert (
            fixture.product_unit.is_active
            == product_unit_before["is_active"]
        )
        assert (
            fixture.product_unit.can_sell
            == product_unit_before["can_sell"]
        )
        assert (
            fixture.product_unit.can_receive
            == product_unit_before["can_receive"]
        )

        assert fixture.review.status == "executed"
        assert (
            fixture.review.executed_by
            == str(fixture.executor.id)
        )
        assert fixture.review.executed_at is not None

        summary = fixture.review.execution_summary

        assert summary["action"] == NO_ACTION
        assert (
            summary["audit_classification"]
            == CANONICALLY_LINKED
        )
        assert (
            summary["operational_link_changed"]
            is False
        )
        assert summary["product_changes"] == 0
        assert summary["product_unit_changes"] == 0
        assert (
            summary["historical_records_changed"]
            == 0
        )

        assert len(audit.calls) == 1
        assert (
            audit.calls[0]["action"]
            == AuditAction
            .UOM_REMEDIATION_REVIEW_EXECUTED
        )
        assert audit.calls[0]["commit"] is False

        db.session.rollback()



def test_execute_preserve_historical_unit_rejects_replay(
    integration_app,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()
        fixture = (
            _approved_historical_preservation_fixture()
        )

        service = TenantUOMRemediationExecutor(
            db.session,
            review_service=fixture.review_service,
            audit_service=ExecutionAuditSpy(),
        )

        service.execute_preserve_historical_unit(
            tenant_id=str(fixture.tenant.id),
            review_id=str(fixture.review.id),
            executed_by=str(fixture.executor.id),
        )

        with pytest.raises(
            TenantUOMRemediationExecutionError
        ) as exc:
            service.execute_preserve_historical_unit(
                tenant_id=str(fixture.tenant.id),
                review_id=str(fixture.review.id),
                executed_by=str(fixture.executor.id),
            )

        assert exc.value.status_code == 409
        assert "already been executed" in str(
            exc.value
        )

        db.session.rollback()


def test_execute_no_action_rejects_replay(
    integration_app,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()
        fixture = _approved_no_action_fixture()

        service = TenantUOMRemediationExecutor(
            db.session,
            review_service=fixture.review_service,
            audit_service=ExecutionAuditSpy(),
        )

        service.execute_no_action(
            tenant_id=str(fixture.tenant.id),
            review_id=str(fixture.review.id),
            executed_by=str(fixture.executor.id),
        )

        with pytest.raises(
            TenantUOMRemediationExecutionError
        ) as exc:
            service.execute_no_action(
                tenant_id=str(fixture.tenant.id),
                review_id=str(fixture.review.id),
                executed_by=str(fixture.executor.id),
            )

        assert exc.value.status_code == 409
        assert "already been executed" in str(
            exc.value
        )

        db.session.rollback()


def test_execute_preserve_historical_unit_rejects_stale_review(
    integration_app,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()
        fixture = (
            _approved_historical_preservation_fixture()
        )

        fixture.source.name = (
            "Historical Unit Changed After Approval"
        )
        db.session.flush()

        service = TenantUOMRemediationExecutor(
            db.session,
            review_service=fixture.review_service,
            audit_service=ExecutionAuditSpy(),
        )

        with pytest.raises(
            TenantUOMRemediationExecutionError
        ) as exc:
            service.execute_preserve_historical_unit(
                tenant_id=str(fixture.tenant.id),
                review_id=str(fixture.review.id),
                executed_by=str(fixture.executor.id),
            )

        assert exc.value.status_code == 409
        assert "stale" in str(exc.value).lower()
        assert fixture.review.status == "approved"

        db.session.rollback()


def test_execute_no_action_rejects_stale_review(
    integration_app,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()
        fixture = _approved_no_action_fixture()

        fixture.source.name = (
            "Each Changed After Approval"
        )
        db.session.flush()

        service = TenantUOMRemediationExecutor(
            db.session,
            review_service=fixture.review_service,
            audit_service=ExecutionAuditSpy(),
        )

        with pytest.raises(
            TenantUOMRemediationExecutionError
        ) as exc:
            service.execute_no_action(
                tenant_id=str(fixture.tenant.id),
                review_id=str(fixture.review.id),
                executed_by=str(fixture.executor.id),
            )

        assert exc.value.status_code == 409
        assert "stale" in str(exc.value).lower()
        assert fixture.review.status == "approved"

        db.session.rollback()


def test_execute_preserve_historical_unit_defends_classification(
    integration_app,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()
        fixture = (
            _approved_historical_preservation_fixture()
        )

        fixture.review.audit_classification = (
            SAFE_TO_LINK
        )
        db.session.flush()

        service = TenantUOMRemediationExecutor(
            db.session,
            review_service=fixture.review_service,
            audit_service=ExecutionAuditSpy(),
        )

        with pytest.raises(
            TenantUOMRemediationExecutionError
        ) as exc:
            service.execute_preserve_historical_unit(
                tenant_id=str(fixture.tenant.id),
                review_id=str(fixture.review.id),
                executed_by=str(fixture.executor.id),
            )

        assert exc.value.status_code == 409
        assert "historical_only" in str(
            exc.value
        ).lower()
        assert fixture.review.status == "approved"

        db.session.rollback()


def test_execute_no_action_defends_classification(
    integration_app,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()
        fixture = _approved_no_action_fixture()

        fixture.review.audit_classification = (
            SAFE_TO_LINK
        )
        db.session.flush()

        service = TenantUOMRemediationExecutor(
            db.session,
            review_service=fixture.review_service,
            audit_service=ExecutionAuditSpy(),
        )

        with pytest.raises(
            TenantUOMRemediationExecutionError
        ) as exc:
            service.execute_no_action(
                tenant_id=str(fixture.tenant.id),
                review_id=str(fixture.review.id),
                executed_by=str(fixture.executor.id),
            )

        assert exc.value.status_code == 409
        assert "canonically_linked" in str(
            exc.value
        ).lower()
        assert fixture.review.status == "approved"

        db.session.rollback()


def test_execute_preserve_historical_unit_defends_locked_state(
    integration_app,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()
        fixture = (
            _approved_historical_preservation_fixture()
        )

        # Remove the evidence that made the old UOM
        # HISTORICAL_ONLY. The post-lock authoritative audit
        # must independently reject execution.
        db.session.delete(
            fixture.historical_receipt_item
        )
        db.session.flush()

        # Isolate the executor's locked-state audit from the
        # planner fingerprint stale-state protection.
        fixture.review_service.assess_staleness = (
            lambda **_kwargs:
            SimpleNamespace(is_stale=False)
        )

        audit = ExecutionAuditSpy()

        service = TenantUOMRemediationExecutor(
            db.session,
            review_service=fixture.review_service,
            audit_service=audit,
        )

        with pytest.raises(
            TenantUOMRemediationExecutionError
        ) as exc:
            service.execute_preserve_historical_unit(
                tenant_id=str(fixture.tenant.id),
                review_id=str(fixture.review.id),
                executed_by=str(fixture.executor.id),
            )

        assert exc.value.status_code == 409
        assert "no longer" in str(exc.value).lower()
        assert "historical_only" in str(
            exc.value
        ).lower()

        assert fixture.review.status == "approved"
        assert len(audit.calls) == 0

        db.session.rollback()


def test_execute_no_action_defends_locked_state(
    integration_app,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()
        fixture = _approved_no_action_fixture()

        # Remove the canonical linkage after approval.
        # Because EA/Each remains a strict alias, the audit
        # becomes SAFE_TO_LINK rather than CANONICALLY_LINKED.
        fixture.source.canonical_uom_id = None
        db.session.flush()

        # Isolate the executor's locked-state audit from the
        # planner fingerprint stale-state protection.
        fixture.review_service.assess_staleness = (
            lambda **_kwargs:
            SimpleNamespace(is_stale=False)
        )

        audit = ExecutionAuditSpy()

        service = TenantUOMRemediationExecutor(
            db.session,
            review_service=fixture.review_service,
            audit_service=audit,
        )

        with pytest.raises(
            TenantUOMRemediationExecutionError
        ) as exc:
            service.execute_no_action(
                tenant_id=str(fixture.tenant.id),
                review_id=str(fixture.review.id),
                executed_by=str(fixture.executor.id),
            )

        assert exc.value.status_code == 409
        assert "no longer" in str(exc.value).lower()
        assert "canonically_linked" in str(
            exc.value
        ).lower()

        assert fixture.review.status == "approved"
        assert len(audit.calls) == 0

        db.session.rollback()


def _approved_split_fixture(
    *,
    with_history: bool = False,
):
    tenant = _db_tenant(
        "UOM Split Executor Tenant"
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

    tablet, tablet_unit = _db_product(
        tenant=tenant,
        unit=source,
        sku=f"SPLIT-TAB-{uuid4().hex[:8]}",
        name="Paracetamol Tablets 500mg",
    )

    capsule, capsule_unit = _db_product(
        tenant=tenant,
        unit=source,
        sku=f"SPLIT-CAP-{uuid4().hex[:8]}",
        name="Amoxicillin Capsules 500mg",
    )

    target = _db_unit(
        tenant=tenant,
        code="CAP-SPLIT",
        name="Capsule Split Target",
        canonical_code="CAP",
    )

    tablet_canonical = _db_canonical("TAB")
    capsule_canonical = _db_canonical("CAP")

    branch = None
    warehouse = None
    historical_receipt = None
    historical_receipt_item = None

    if with_history:
        branch, warehouse = (
            _db_branch_and_warehouse(
                tenant=tenant,
            )
        )

        (
            historical_receipt,
            historical_receipt_item,
        ) = _db_historical_receipt_evidence(
            tenant=tenant,
            branch=branch,
            warehouse=warehouse,
            product=capsule,
            product_unit=capsule_unit,
            source_uom=source,
            user=creator,
        )

    review_service = (
        TenantUOMRemediationReviewService(
            db.session,
            audit_service=ExecutionAuditSpy(),
        )
    )

    review = review_service.create_pending_review(
        tenant_id=str(tenant.id),
        source_uom_id=str(source.id),
        created_by=str(creator.id),
    )

    assert (
        review.audit_classification
        == MIXED_PRODUCT_SEMANTICS
    )

    review_service.approve_review(
        tenant_id=str(tenant.id),
        review_id=str(review.id),
        reviewed_by=str(reviewer.id),
        selected_action=SPLIT_CURRENT_PRODUCTS,
        selected_canonical_uom_id=str(
            tablet_canonical.id
        ),
        product_decisions=[
            {
                "product_id": str(tablet.id),
                "selected_action":
                    KEEP_CURRENT_PRODUCT,
                "preserve_historical_unit":
                    True,
            },
            {
                "product_id": str(capsule.id),
                "selected_action":
                    MOVE_CURRENT_PRODUCT,
                "target_canonical_uom_id":
                    str(capsule_canonical.id),
                "target_tenant_uom_id":
                    str(target.id),
                "preserve_historical_unit":
                    True,
            },
        ],
        review_reason=(
            "Split tablet and capsule semantics."
        ),
    )

    return SimpleNamespace(
        tenant=tenant,
        creator=creator,
        reviewer=reviewer,
        executor=executor_user,
        source=source,
        target=target,
        tablet=tablet,
        tablet_unit=tablet_unit,
        capsule=capsule,
        capsule_unit=capsule_unit,
        tablet_canonical=tablet_canonical,
        capsule_canonical=capsule_canonical,
        review=review,
        review_service=review_service,
        branch=branch,
        warehouse=warehouse,
        historical_receipt=historical_receipt,
        historical_receipt_item=historical_receipt_item,
    )


def test_execute_split_current_products_preserves_old_product_unit(
    integration_app,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()
        fixture = _approved_split_fixture()

        old_capsule_unit = fixture.capsule_unit

        old_id = str(old_capsule_unit.id)
        old_unit_id = str(
            old_capsule_unit.unit_id
        )
        old_factor = Decimal(
            str(
                old_capsule_unit
                .conversion_factor_to_base
            )
        )

        tablet_product_unit_id = (
            fixture.tablet.unit_id
        )
        tablet_base_id = str(
            fixture.tablet_unit.id
        )

        audit = ExecutionAuditSpy()

        service = TenantUOMRemediationExecutor(
            db.session,
            review_service=(
                fixture.review_service
            ),
            audit_service=audit,
        )

        result = (
            service.execute_split_current_products(
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
        )

        assert result.status == "executed"
        assert result.changed is True
        assert (
            result.selected_action
            == SPLIT_CURRENT_PRODUCTS
        )

        # KEEP_CURRENT_PRODUCT establishes the identity
        # retained by the source UOM.
        assert (
            fixture.source.canonical_uom_id
            == str(
                fixture.tablet_canonical.id
            )
        )

        # Tablet remains structurally unchanged.
        assert (
            fixture.tablet.unit_id
            == tablet_product_unit_id
        )
        assert (
            str(fixture.tablet_unit.id)
            == tablet_base_id
        )
        assert fixture.tablet_unit.is_base is True
        assert fixture.tablet_unit.is_active is True

        # Capsule now uses the explicit CAP tenant UOM.
        assert (
            fixture.capsule.unit_id
            == str(fixture.target.id)
        )

        # Old ProductUnit is historical evidence:
        # identity/unit/factor are immutable.
        assert str(old_capsule_unit.id) == old_id
        assert (
            str(old_capsule_unit.unit_id)
            == old_unit_id
        )
        assert Decimal(
            str(
                old_capsule_unit
                .conversion_factor_to_base
            )
        ) == old_factor

        assert old_capsule_unit.is_base is False
        assert old_capsule_unit.is_active is False
        assert old_capsule_unit.can_sell is False
        assert old_capsule_unit.can_receive is False

        new_base = (
            db.session.query(ProductUnit)
            .filter(
                ProductUnit.tenant_id
                == str(fixture.tenant.id),
                ProductUnit.product_id
                == str(fixture.capsule.id),
                ProductUnit.is_base.is_(True),
            )
            .one()
        )

        assert (
            new_base.unit_id
            == str(fixture.target.id)
        )
        assert Decimal(
            str(
                new_base
                .conversion_factor_to_base
            )
        ) == Decimal("1")
        assert new_base.is_active is True
        assert new_base.can_sell is True
        assert new_base.can_receive is True

        assert str(new_base.id) != old_id

        assert (
            fixture.review.status
            == "executed"
        )
        assert (
            fixture.review.executed_by
            == str(fixture.executor.id)
        )
        assert (
            fixture.review.executed_at
            is not None
        )

        summary = (
            fixture.review.execution_summary
        )

        assert (
            summary["action"]
            == SPLIT_CURRENT_PRODUCTS
        )
        assert (
            summary["keep_product_count"]
            == 1
        )
        assert (
            summary["moved_product_count"]
            == 1
        )
        assert (
            summary["historical_records_changed"]
            == 0
        )

        assert len(audit.calls) == 1
        assert (
            audit.calls[0]["action"]
            == AuditAction
            .UOM_REMEDIATION_REVIEW_EXECUTED
        )
        assert (
            audit.calls[0]["commit"]
            is False
        )

        db.session.rollback()



def test_execute_split_current_products_preserves_commercial_state(
    integration_app,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()
        fixture = _approved_split_fixture()

        old_base = fixture.capsule_unit

        old_base.can_sell = False
        old_base.can_receive = True
        old_base.sale_price = Decimal("125.50")
        old_base.minimum_sale_price = Decimal("110.00")

        db.session.flush()

        service = TenantUOMRemediationExecutor(
            db.session,
            review_service=fixture.review_service,
            audit_service=ExecutionAuditSpy(),
        )

        result = service.execute_split_current_products(
            tenant_id=str(fixture.tenant.id),
            review_id=str(fixture.review.id),
            executed_by=str(fixture.executor.id),
        )

        assert result.status == "executed"

        new_base = (
            db.session.query(ProductUnit)
            .filter(
                ProductUnit.tenant_id
                == str(fixture.tenant.id),
                ProductUnit.product_id
                == str(fixture.capsule.id),
                ProductUnit.is_base.is_(True),
            )
            .one()
        )

        assert (
            str(new_base.id)
            != str(old_base.id)
        )

        assert new_base.can_sell is False
        assert new_base.can_receive is True

        assert Decimal(
            str(new_base.sale_price)
        ) == Decimal("125.50")

        assert Decimal(
            str(new_base.minimum_sale_price)
        ) == Decimal("110.00")

        # Historical row identity and commercial values remain,
        # while operational eligibility is retired.
        db.session.refresh(old_base)

        assert old_base.is_base is False
        assert old_base.is_active is False
        assert old_base.can_sell is False
        assert old_base.can_receive is False

        assert Decimal(
            str(old_base.sale_price)
        ) == Decimal("125.50")

        assert Decimal(
            str(old_base.minimum_sale_price)
        ) == Decimal("110.00")

        db.session.rollback()


def test_execute_split_current_products_rejects_replay(
    integration_app,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()
        fixture = _approved_split_fixture()

        service = TenantUOMRemediationExecutor(
            db.session,
            review_service=fixture.review_service,
            audit_service=ExecutionAuditSpy(),
        )

        service.execute_split_current_products(
            tenant_id=str(fixture.tenant.id),
            review_id=str(fixture.review.id),
            executed_by=str(fixture.executor.id),
        )

        with pytest.raises(
            TenantUOMRemediationExecutionError
        ) as exc:
            service.execute_split_current_products(
                tenant_id=str(fixture.tenant.id),
                review_id=str(fixture.review.id),
                executed_by=str(fixture.executor.id),
            )

        assert exc.value.status_code == 409
        assert "already been executed" in str(
            exc.value
        )

        db.session.rollback()


def test_execute_split_current_products_rejects_stale_review(
    integration_app,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()
        fixture = _approved_split_fixture()

        fixture.source.name = "Changed After Approval"
        db.session.flush()

        service = TenantUOMRemediationExecutor(
            db.session,
            review_service=fixture.review_service,
            audit_service=ExecutionAuditSpy(),
        )

        with pytest.raises(
            TenantUOMRemediationExecutionError
        ) as exc:
            service.execute_split_current_products(
                tenant_id=str(fixture.tenant.id),
                review_id=str(fixture.review.id),
                executed_by=str(fixture.executor.id),
            )

        assert exc.value.status_code == 409
        assert "stale" in str(exc.value).lower()

        assert fixture.review.status == "approved"
        assert fixture.source.canonical_uom_id is None

        db.session.rollback()


def test_execute_split_current_products_defends_already_linked_source(
    integration_app,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()
        fixture = _approved_split_fixture()

        fixture.source.canonical_uom_id = str(
            fixture.tablet_canonical.id
        )
        db.session.flush()

        # Isolate the locked-state guard from planner staleness.
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
            service.execute_split_current_products(
                tenant_id=str(fixture.tenant.id),
                review_id=str(fixture.review.id),
                executed_by=str(fixture.executor.id),
            )

        assert exc.value.status_code == 409
        assert "already canonically linked" in str(
            exc.value
        )

        assert fixture.review.status == "approved"

        db.session.rollback()


def test_execute_split_current_products_defends_product_unit_drift(
    integration_app,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()
        fixture = _approved_split_fixture()

        original_source_product_unit_id = str(
            fixture.capsule_unit.id
        )

        replacement = ProductUnit(
            tenant_id=str(fixture.tenant.id),
            product_id=str(fixture.capsule.id),
            unit_id=str(fixture.target.id),
            conversion_factor_to_base=Decimal("1"),
            is_base=False,
            can_sell=True,
            can_receive=True,
            is_active=True,
        )

        db.session.add(replacement)
        db.session.flush()

        fixture.capsule_unit.is_base = False
        fixture.capsule_unit.is_active = False

        # Release the existing base row first. This mirrors the
        # database invariant enforced by the partial unique index.
        db.session.flush()

        replacement.is_base = True
        fixture.capsule.unit_id = str(
            fixture.target.id
        )

        db.session.flush()

        # Isolate execution's structural guards.
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
            service.execute_split_current_products(
                tenant_id=str(fixture.tenant.id),
                review_id=str(fixture.review.id),
                executed_by=str(fixture.executor.id),
            )

        assert exc.value.status_code == 409

        assert (
            "no longer uses the source" in str(exc.value)
            or "source ProductUnit" in str(exc.value)
        )

        old_row = db.session.get(
            ProductUnit,
            original_source_product_unit_id,
        )

        assert old_row is not None
        assert (
            str(old_row.unit_id)
            == str(fixture.source.id)
        )

        assert fixture.review.status == "approved"

        db.session.rollback()


def test_execute_split_current_products_promotes_existing_factor_one_target(
    integration_app,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()
        fixture = _approved_split_fixture()

        existing_target = ProductUnit(
            tenant_id=str(fixture.tenant.id),
            product_id=str(fixture.capsule.id),
            unit_id=str(fixture.target.id),
            conversion_factor_to_base=Decimal("1"),
            is_base=False,
            can_sell=False,
            can_receive=False,
            sale_price=Decimal("215.75"),
            minimum_sale_price=Decimal("199.00"),
            is_active=False,
        )

        db.session.add(existing_target)
        db.session.flush()

        existing_id = str(existing_target.id)
        old_id = str(fixture.capsule_unit.id)

        service = TenantUOMRemediationExecutor(
            db.session,
            review_service=fixture.review_service,
            audit_service=ExecutionAuditSpy(),
        )

        result = service.execute_split_current_products(
            tenant_id=str(fixture.tenant.id),
            review_id=str(fixture.review.id),
            executed_by=str(fixture.executor.id),
        )

        assert result.status == "executed"

        db.session.refresh(existing_target)
        db.session.refresh(fixture.capsule_unit)

        assert str(existing_target.id) == existing_id
        assert existing_target.is_base is True
        assert existing_target.is_active is True
        assert existing_target.can_sell is False
        assert existing_target.can_receive is False

        assert Decimal(
            str(existing_target.sale_price)
        ) == Decimal("215.75")

        assert Decimal(
            str(existing_target.minimum_sale_price)
        ) == Decimal("199.00")

        assert Decimal(
            str(existing_target.conversion_factor_to_base)
        ) == Decimal("1")

        assert fixture.capsule.unit_id == str(
            fixture.target.id
        )

        assert str(fixture.capsule_unit.id) == old_id
        assert fixture.capsule_unit.is_base is False
        assert fixture.capsule_unit.is_active is False

        rows = (
            db.session.query(ProductUnit)
            .filter(
                ProductUnit.tenant_id
                == str(fixture.tenant.id),
                ProductUnit.product_id
                == str(fixture.capsule.id),
            )
            .all()
        )

        assert len(rows) == 2

        db.session.rollback()



def test_execute_split_current_products_rejects_unmapped_target_drift(
    integration_app,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()
        fixture = _approved_split_fixture()

        assert (
            fixture.target.canonical_uom_id
            == str(fixture.capsule_canonical.id)
        )

        fixture.target.canonical_uom_id = None
        db.session.flush()

        # Isolate the executor's locked-state canonical guard.
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
            service.execute_split_current_products(
                tenant_id=str(fixture.tenant.id),
                review_id=str(fixture.review.id),
                executed_by=str(fixture.executor.id),
            )

        assert exc.value.status_code == 409
        assert "canonically mapped" in str(
            exc.value
        ).lower()

        assert fixture.review.status == "approved"
        assert (
            fixture.capsule.unit_id
            == str(fixture.source.id)
        )
        assert fixture.capsule_unit.is_base is True

        db.session.rollback()


def test_execute_split_current_products_rejects_non_one_existing_target_factor(
    integration_app,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()
        fixture = _approved_split_fixture()

        existing_target = ProductUnit(
            tenant_id=str(fixture.tenant.id),
            product_id=str(fixture.capsule.id),
            unit_id=str(fixture.target.id),
            conversion_factor_to_base=Decimal("10"),
            is_base=False,
            can_sell=True,
            can_receive=True,
            is_active=True,
        )

        db.session.add(existing_target)
        db.session.flush()

        target_id = str(existing_target.id)
        old_base_id = str(
            fixture.capsule_unit.id
        )
        old_product_unit_id = str(
            fixture.capsule.unit_id
        )

        service = TenantUOMRemediationExecutor(
            db.session,
            review_service=fixture.review_service,
            audit_service=ExecutionAuditSpy(),
        )

        with pytest.raises(
            TenantUOMRemediationExecutionError
        ) as exc:
            service.execute_split_current_products(
                tenant_id=str(fixture.tenant.id),
                review_id=str(fixture.review.id),
                executed_by=str(fixture.executor.id),
            )

        assert exc.value.status_code == 409
        assert "conversion factor" in str(
            exc.value
        ).lower()

        db.session.refresh(existing_target)
        db.session.refresh(fixture.capsule_unit)
        db.session.refresh(fixture.capsule)

        assert str(existing_target.id) == target_id
        assert Decimal(
            str(existing_target.conversion_factor_to_base)
        ) == Decimal("10")
        assert existing_target.is_base is False

        assert (
            str(fixture.capsule_unit.id)
            == old_base_id
        )
        assert fixture.capsule_unit.is_base is True
        assert (
            fixture.capsule.unit_id
            == old_product_unit_id
        )

        assert fixture.review.status == "approved"

        db.session.rollback()


def test_execute_split_current_products_preserves_goods_receipt_evidence(
    integration_app,
):
    with integration_app.app_context():
        _prepare_execution_catalogue()

        fixture = _approved_split_fixture(
            with_history=True
        )

        receipt_item = (
            fixture.historical_receipt_item
        )
        old_product_unit = (
            fixture.capsule_unit
        )

        assert receipt_item is not None
        assert fixture.historical_receipt is not None

        receipt_item_id = str(
            receipt_item.id
        )
        historical_product_unit_id = str(
            receipt_item.product_unit_id
        )

        old_product_unit_id = str(
            old_product_unit.id
        )
        old_unit_id = str(
            old_product_unit.unit_id
        )
        old_factor = Decimal(
            str(
                old_product_unit
                .conversion_factor_to_base
            )
        )

        snapshot_unit_code = (
            receipt_item.unit_code_snapshot
        )
        snapshot_unit_name = (
            receipt_item.unit_name_snapshot
        )
        snapshot_factor = Decimal(
            str(
                receipt_item
                .conversion_factor_to_base
            )
        )
        snapshot_base_quantity = Decimal(
            str(receipt_item.base_quantity)
        )
        snapshot_quantity = Decimal(
            str(receipt_item.quantity)
        )

        assert (
            historical_product_unit_id
            == old_product_unit_id
        )

        service = TenantUOMRemediationExecutor(
            db.session,
            review_service=fixture.review_service,
            audit_service=ExecutionAuditSpy(),
        )

        result = (
            service.execute_split_current_products(
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
        )

        assert result.status == "executed"

        db.session.refresh(receipt_item)
        db.session.refresh(old_product_unit)
        db.session.refresh(fixture.capsule)

        # The transactional evidence row itself survives.
        assert (
            str(receipt_item.id)
            == receipt_item_id
        )

        # The GRN still references the exact historical
        # ProductUnit that represented the received stock.
        assert (
            str(receipt_item.product_unit_id)
            == historical_product_unit_id
        )
        assert (
            str(receipt_item.product_unit_id)
            == old_product_unit_id
        )

        # Receipt snapshots remain immutable evidence.
        assert (
            receipt_item.unit_code_snapshot
            == snapshot_unit_code
        )
        assert (
            receipt_item.unit_name_snapshot
            == snapshot_unit_name
        )
        assert Decimal(
            str(
                receipt_item
                .conversion_factor_to_base
            )
        ) == snapshot_factor
        assert Decimal(
            str(receipt_item.base_quantity)
        ) == snapshot_base_quantity
        assert Decimal(
            str(receipt_item.quantity)
        ) == snapshot_quantity

        # The old ProductUnit remains the exact historical
        # identity referenced by the receipt.
        assert (
            str(old_product_unit.id)
            == old_product_unit_id
        )
        assert (
            str(old_product_unit.unit_id)
            == old_unit_id
        )
        assert Decimal(
            str(
                old_product_unit
                .conversion_factor_to_base
            )
        ) == old_factor

        # It is retired from current operations only.
        assert old_product_unit.is_base is False
        assert old_product_unit.is_active is False
        assert old_product_unit.can_sell is False
        assert old_product_unit.can_receive is False

        # Current product truth moves to CAP.
        assert (
            fixture.capsule.unit_id
            == str(fixture.target.id)
        )

        new_base = (
            db.session.query(ProductUnit)
            .filter(
                ProductUnit.tenant_id
                == str(fixture.tenant.id),
                ProductUnit.product_id
                == str(fixture.capsule.id),
                ProductUnit.is_base.is_(True),
            )
            .one()
        )

        assert (
            str(new_base.id)
            != old_product_unit_id
        )
        assert (
            new_base.unit_id
            == str(fixture.target.id)
        )
        assert Decimal(
            str(
                new_base
                .conversion_factor_to_base
            )
        ) == Decimal("1")
        assert new_base.is_active is True

        db.session.rollback()
