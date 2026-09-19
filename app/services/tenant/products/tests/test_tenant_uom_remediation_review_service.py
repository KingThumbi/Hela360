from __future__ import annotations

from decimal import Decimal
from hashlib import sha256
import json
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app import create_app
from app.extensions import db
from app.models import (
    CanonicalUnitOfMeasure,
    Product,
    ProductUnit,
    Tenant,
    TenantUOMRemediationProductDecision,
    UnitOfMeasure,
    User,
)
from app.services.common.audit_actions import AuditAction
from app.services.common.audit_modules import AuditModule
from app.services.platform.canonical_uom_catalogue_service import (
    CanonicalUOMCatalogueService,
)
from app.services.tenant.products.tenant_uom_audit_service import (
    CUSTOM_UNMAPPED,
    DOSAGE_FORM_AS_UOM,
    LEGACY_PRODUCT_SPECIFIC,
    MIXED_PRODUCT_SEMANTICS,
    SAFE_TO_LINK,
)
from app.services.tenant.products.tenant_uom_remediation_planner import (
    LINK_EXISTING_UOM,
    SPLIT_CURRENT_PRODUCTS,
)
from app.services.tenant.products.tenant_uom_remediation_review_service import (
    KEEP_CURRENT_PRODUCT,
    KEEP_UNMAPPED,
    MOVE_CURRENT_PRODUCT,
    TenantUOMRemediationReviewError,
    TenantUOMRemediationReviewService,
)


@pytest.fixture()
def app():
    app = create_app()
    app.config.update(TESTING=True)
    return app


class AuditSpy:
    def __init__(self):
        self.calls = []

    def log(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(id=str(uuid4()))


def _tenant(name: str) -> Tenant:
    suffix = uuid4().hex[:8].upper()

    tenant = Tenant(
        legal_name=name,
        display_name=name,
        business_code=f"RV{suffix}",
        workspace_slug=(
            f"uom-review-{uuid4().hex}"
        ),
    )

    db.session.add(tenant)
    db.session.flush()

    return tenant


def _user(
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


def _canonical(code: str) -> CanonicalUnitOfMeasure:
    return (
        db.session.query(
            CanonicalUnitOfMeasure
        )
        .filter(
            CanonicalUnitOfMeasure.code == code
        )
        .one()
    )


def _unit(
    *,
    tenant: Tenant,
    code: str,
    name: str,
    canonical_code: str | None = None,
) -> UnitOfMeasure:
    canonical_id = None

    if canonical_code is not None:
        canonical_id = str(
            _canonical(canonical_code).id
        )

    unit = UnitOfMeasure(
        tenant_id=str(tenant.id),
        canonical_uom_id=canonical_id,
        code=code,
        name=name,
        base_factor=Decimal("1"),
    )

    db.session.add(unit)
    db.session.flush()

    return unit


def _product(
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


def _prepare_catalogue():
    CanonicalUOMCatalogueService(
        db.session
    ).synchronize()


def _safe_fixture():
    tenant = _tenant(
        "Safe Review Tenant"
    )
    creator = _user(
        tenant=tenant,
        name="Creator",
    )
    reviewer = _user(
        tenant=tenant,
        name="Reviewer",
    )

    source = _unit(
        tenant=tenant,
        code="TAB",
        name="Tablet",
    )

    product, product_unit = _product(
        tenant=tenant,
        unit=source,
        sku="REVIEW-SAFE-001",
        name="Paracetamol Tablets 500mg",
    )

    return (
        tenant,
        creator,
        reviewer,
        source,
        product,
        product_unit,
    )


def _mixed_fixture():
    tenant = _tenant(
        "Mixed Review Tenant"
    )
    creator = _user(
        tenant=tenant,
        name="Creator",
    )
    reviewer = _user(
        tenant=tenant,
        name="Reviewer",
    )

    source = _unit(
        tenant=tenant,
        code="TAB",
        name="Tablet",
    )

    tablet, tablet_unit = _product(
        tenant=tenant,
        unit=source,
        sku="REVIEW-MIX-001",
        name="Paracetamol Tablets 500mg",
    )

    capsule, capsule_unit = _product(
        tenant=tenant,
        unit=source,
        sku="REVIEW-MIX-002",
        name="Amoxicillin Capsules 500mg",
    )

    target = _unit(
        tenant=tenant,
        code="CAP-REVIEW",
        name="Capsule Review Target",
        canonical_code="CAP",
    )

    return (
        tenant,
        creator,
        reviewer,
        source,
        target,
        tablet,
        tablet_unit,
        capsule,
        capsule_unit,
    )



def _unresolved_fixture(
    *,
    code: str,
    name: str,
    sku: str,
    product_name: str,
):
    tenant = _tenant(
        f"Unresolved Review {uuid4().hex[:8]}"
    )

    creator = _user(
        tenant=tenant,
        name="Creator",
    )

    reviewer = _user(
        tenant=tenant,
        name="Reviewer",
    )

    source = _unit(
        tenant=tenant,
        code=code,
        name=name,
    )

    product, product_unit = _product(
        tenant=tenant,
        unit=source,
        sku=sku,
        name=product_name,
    )

    return (
        tenant,
        creator,
        reviewer,
        source,
        product,
        product_unit,
    )


def _service(audit=None):
    return TenantUOMRemediationReviewService(
        db.session,
        audit_service=(
            audit
            if audit is not None
            else AuditSpy()
        ),
    )



def test_keep_unmapped_is_valid_for_safe_to_link(app):
    with app.app_context():
        _prepare_catalogue()

        (
            tenant,
            creator,
            reviewer,
            source,
            product,
            product_unit,
        ) = _safe_fixture()

        service = _service()

        review = service.create_pending_review(
            tenant_id=str(tenant.id),
            source_uom_id=str(source.id),
            created_by=str(creator.id),
        )

        assert review.audit_classification == SAFE_TO_LINK

        source_before = source.canonical_uom_id
        product_before = product.unit_id
        product_unit_before = product_unit.unit_id

        approved = service.approve_review(
            tenant_id=str(tenant.id),
            review_id=review.id,
            reviewed_by=str(reviewer.id),
            selected_action=KEEP_UNMAPPED,
            review_reason=(
                "Retain this tenant vocabulary without "
                "canonical linkage."
            ),
        )

        assert approved.status == "approved"
        assert approved.selected_action == KEEP_UNMAPPED
        assert approved.selected_canonical_uom_id is None

        assert source.canonical_uom_id == source_before
        assert product.unit_id == product_before
        assert product_unit.unit_id == product_unit_before

        db.session.rollback()


@pytest.mark.parametrize(
    (
        "code",
        "name",
        "sku",
        "product_name",
        "expected_classification",
    ),
    [
        (
            "WHOLE",
            "Whole",
            "REVIEW-CUSTOM-001",
            "Custom Product",
            CUSTOM_UNMAPPED,
        ),
        (
            "Syrup",
            "Syrup",
            "REVIEW-DOSAGE-001",
            "Piriton Syrup 100ml",
            DOSAGE_FORM_AS_UOM,
        ),
        (
            "M084-TAB",
            "M084 Tablet",
            "REVIEW-LEGACY-001",
            "M084 Paracetamol Tablet",
            LEGACY_PRODUCT_SPECIFIC,
        ),
    ],
)
def test_keep_unmapped_is_valid_for_unresolved_classifications(
    app,
    code,
    name,
    sku,
    product_name,
    expected_classification,
):
    with app.app_context():
        _prepare_catalogue()

        (
            tenant,
            creator,
            reviewer,
            source,
            product,
            product_unit,
        ) = _unresolved_fixture(
            code=code,
            name=name,
            sku=sku,
            product_name=product_name,
        )

        service = _service()

        review = service.create_pending_review(
            tenant_id=str(tenant.id),
            source_uom_id=str(source.id),
            created_by=str(creator.id),
        )

        assert (
            review.audit_classification
            == expected_classification
        )

        source_before = source.canonical_uom_id
        product_before = product.unit_id
        product_unit_before = product_unit.unit_id

        approved = service.approve_review(
            tenant_id=str(tenant.id),
            review_id=review.id,
            reviewed_by=str(reviewer.id),
            selected_action=KEEP_UNMAPPED,
            review_reason=(
                "Evidence does not justify canonical linkage."
            ),
        )

        assert approved.status == "approved"
        assert approved.selected_action == KEEP_UNMAPPED
        assert approved.selected_canonical_uom_id is None

        assert source.canonical_uom_id == source_before
        assert product.unit_id == product_before
        assert product_unit.unit_id == product_unit_before

        db.session.rollback()


def test_keep_unmapped_rejects_canonical_target(app):
    with app.app_context():
        _prepare_catalogue()

        (
            tenant,
            creator,
            reviewer,
            source,
            _product,
            _product_unit,
        ) = _safe_fixture()

        service = _service()

        review = service.create_pending_review(
            tenant_id=str(tenant.id),
            source_uom_id=str(source.id),
            created_by=str(creator.id),
        )

        canonical = _canonical("TAB")

        with pytest.raises(
            TenantUOMRemediationReviewError
        ) as exc:
            service.approve_review(
                tenant_id=str(tenant.id),
                review_id=review.id,
                reviewed_by=str(reviewer.id),
                selected_action=KEEP_UNMAPPED,
                selected_canonical_uom_id=str(
                    canonical.id
                ),
            )

        assert exc.value.status_code == 400
        assert "cannot select a canonical UOM" in str(
            exc.value
        )

        assert review.status == "pending"

        db.session.rollback()


def test_keep_unmapped_rejects_product_decisions(app):
    with app.app_context():
        _prepare_catalogue()

        (
            tenant,
            creator,
            reviewer,
            source,
            product,
            _product_unit,
        ) = _safe_fixture()

        service = _service()

        review = service.create_pending_review(
            tenant_id=str(tenant.id),
            source_uom_id=str(source.id),
            created_by=str(creator.id),
        )

        with pytest.raises(
            TenantUOMRemediationReviewError
        ) as exc:
            service.approve_review(
                tenant_id=str(tenant.id),
                review_id=review.id,
                reviewed_by=str(reviewer.id),
                selected_action=KEEP_UNMAPPED,
                product_decisions=[
                    {
                        "product_id": str(product.id),
                        "selected_action":
                            KEEP_CURRENT_PRODUCT,
                    }
                ],
            )

        assert exc.value.status_code == 400
        assert (
            "does not accept product decisions"
            in str(exc.value)
        )

        assert review.status == "pending"

        db.session.rollback()


def test_keep_unmapped_rejected_for_mixed_semantics(app):
    with app.app_context():
        _prepare_catalogue()

        (
            tenant,
            creator,
            reviewer,
            source,
            _target,
            _tablet,
            _tablet_unit,
            _capsule,
            _capsule_unit,
        ) = _mixed_fixture()

        service = _service()

        review = service.create_pending_review(
            tenant_id=str(tenant.id),
            source_uom_id=str(source.id),
            created_by=str(creator.id),
        )

        assert (
            review.audit_classification
            == MIXED_PRODUCT_SEMANTICS
        )

        with pytest.raises(
            TenantUOMRemediationReviewError
        ) as exc:
            service.approve_review(
                tenant_id=str(tenant.id),
                review_id=review.id,
                reviewed_by=str(reviewer.id),
                selected_action=KEEP_UNMAPPED,
            )

        assert exc.value.status_code == 400
        assert "SPLIT_CURRENT_PRODUCTS" in str(
            exc.value
        )

        assert review.status == "pending"

        db.session.rollback()


def test_create_pending_review_snapshots_and_audits(app):
    with app.app_context():
        _prepare_catalogue()

        (
            tenant,
            creator,
            _reviewer,
            source,
            product,
            product_unit,
        ) = _safe_fixture()

        audit = AuditSpy()
        service = _service(audit)

        original_product_unit_id = product.unit_id
        original_pu_unit_id = product_unit.unit_id

        review = service.create_pending_review(
            tenant_id=str(tenant.id),
            source_uom_id=str(source.id),
            created_by=str(creator.id),
        )

        decisions = (
            db.session.query(
                TenantUOMRemediationProductDecision
            )
            .filter(
                TenantUOMRemediationProductDecision.review_id
                == review.id
            )
            .all()
        )

        assert review.status == "pending"
        assert (
            review.audit_classification
            == SAFE_TO_LINK
        )
        assert (
            review.recommended_action
            == LINK_EXISTING_UOM
        )
        assert len(decisions) == 1

        payload = json.dumps(
            review.planner_snapshot,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")

        expected = sha256(payload).hexdigest()

        assert review.planner_fingerprint == expected
        assert len(expected) == 64

        assert len(audit.calls) == 1

        call = audit.calls[0]

        assert (
            call["module"]
            == AuditModule.CATALOGUE
        )
        assert (
            call["action"]
            == AuditAction.UOM_REMEDIATION_REVIEW_CREATED
        )
        assert call["commit"] is False

        assert source.canonical_uom_id is None
        assert product.unit_id == original_product_unit_id
        assert product_unit.unit_id == original_pu_unit_id

        db.session.rollback()


def test_duplicate_active_review_is_rejected(app):
    with app.app_context():
        _prepare_catalogue()

        (
            tenant,
            creator,
            _reviewer,
            source,
            _product_row,
            _product_unit,
        ) = _safe_fixture()

        service = _service()

        service.create_pending_review(
            tenant_id=str(tenant.id),
            source_uom_id=str(source.id),
            created_by=str(creator.id),
        )

        with pytest.raises(
            TenantUOMRemediationReviewError
        ) as exc:
            service.create_pending_review(
                tenant_id=str(tenant.id),
                source_uom_id=str(source.id),
                created_by=str(creator.id),
            )

        assert exc.value.status_code == 409

        db.session.rollback()


def test_review_access_is_tenant_isolated(app):
    with app.app_context():
        _prepare_catalogue()

        (
            tenant,
            creator,
            _reviewer,
            source,
            _product_row,
            _product_unit,
        ) = _safe_fixture()

        other = _tenant(
            "Other Review Tenant"
        )
        other_user = _user(
            tenant=other,
            name="Other",
        )

        service = _service()

        review = service.create_pending_review(
            tenant_id=str(tenant.id),
            source_uom_id=str(source.id),
            created_by=str(creator.id),
        )

        with pytest.raises(
            TenantUOMRemediationReviewError
        ) as exc:
            service.get_review(
                tenant_id=str(other.id),
                review_id=review.id,
            )

        assert exc.value.status_code == 404

        canonical = _canonical("TAB")

        with pytest.raises(
            TenantUOMRemediationReviewError
        ) as exc:
            service.approve_review(
                tenant_id=str(tenant.id),
                review_id=review.id,
                reviewed_by=str(other_user.id),
                selected_action=LINK_EXISTING_UOM,
                selected_canonical_uom_id=str(
                    canonical.id
                ),
            )

        assert exc.value.status_code == 404

        db.session.rollback()


def test_creator_cannot_approve_own_review(app):
    with app.app_context():
        _prepare_catalogue()

        (
            tenant,
            creator,
            _reviewer,
            source,
            _product_row,
            _product_unit,
        ) = _safe_fixture()

        service = _service()

        review = service.create_pending_review(
            tenant_id=str(tenant.id),
            source_uom_id=str(source.id),
            created_by=str(creator.id),
        )

        canonical = _canonical("TAB")

        with pytest.raises(
            TenantUOMRemediationReviewError
        ) as exc:
            service.approve_review(
                tenant_id=str(tenant.id),
                review_id=review.id,
                reviewed_by=str(creator.id),
                selected_action=LINK_EXISTING_UOM,
                selected_canonical_uom_id=str(
                    canonical.id
                ),
            )

        assert exc.value.status_code == 409

        db.session.rollback()


def test_safe_review_approval_does_not_execute_remediation(app):
    with app.app_context():
        _prepare_catalogue()

        (
            tenant,
            creator,
            reviewer,
            source,
            product,
            product_unit,
        ) = _safe_fixture()

        audit = AuditSpy()
        service = _service(audit)

        review = service.create_pending_review(
            tenant_id=str(tenant.id),
            source_uom_id=str(source.id),
            created_by=str(creator.id),
        )

        source_id_before = product.unit_id
        pu_unit_before = product_unit.unit_id

        canonical = _canonical("TAB")

        approved = service.approve_review(
            tenant_id=str(tenant.id),
            review_id=review.id,
            reviewed_by=str(reviewer.id),
            selected_action=LINK_EXISTING_UOM,
            selected_canonical_uom_id=str(
                canonical.id
            ),
            review_reason=(
                "Reviewed against tenant product semantics."
            ),
        )

        assert approved.status == "approved"
        assert approved.reviewed_by == str(
            reviewer.id
        )
        assert (
            approved.selected_canonical_uom_id
            == str(canonical.id)
        )

        assert source.canonical_uom_id is None
        assert product.unit_id == source_id_before
        assert product_unit.unit_id == pu_unit_before

        assert len(audit.calls) == 2
        assert (
            audit.calls[-1]["action"]
            == AuditAction.UOM_REMEDIATION_REVIEW_APPROVED
        )
        assert audit.calls[-1]["commit"] is False

        db.session.rollback()


def test_mixed_review_requires_every_product_decision(app):
    with app.app_context():
        _prepare_catalogue()

        (
            tenant,
            creator,
            reviewer,
            source,
            target,
            tablet,
            _tablet_unit,
            _capsule,
            _capsule_unit,
        ) = _mixed_fixture()

        service = _service()

        review = service.create_pending_review(
            tenant_id=str(tenant.id),
            source_uom_id=str(source.id),
            created_by=str(creator.id),
        )

        assert (
            review.audit_classification
            == MIXED_PRODUCT_SEMANTICS
        )
        assert (
            review.recommended_action
            == SPLIT_CURRENT_PRODUCTS
        )

        with pytest.raises(
            TenantUOMRemediationReviewError
        ) as exc:
            service.approve_review(
                tenant_id=str(tenant.id),
                review_id=review.id,
                reviewed_by=str(reviewer.id),
                selected_action=SPLIT_CURRENT_PRODUCTS,
                product_decisions=[
                    {
                        "product_id": str(
                            tablet.id
                        ),
                        "selected_action":
                            MOVE_CURRENT_PRODUCT,
                        "target_tenant_uom_id":
                            str(target.id),
                    }
                ],
            )

        assert exc.value.status_code == 400

        db.session.rollback()


def test_mixed_review_cannot_be_globally_linked(app):
    with app.app_context():
        _prepare_catalogue()

        (
            tenant,
            creator,
            reviewer,
            source,
            _target,
            _tablet,
            _tablet_unit,
            _capsule,
            _capsule_unit,
        ) = _mixed_fixture()

        service = _service()

        review = service.create_pending_review(
            tenant_id=str(tenant.id),
            source_uom_id=str(source.id),
            created_by=str(creator.id),
        )

        canonical = _canonical("TAB")

        with pytest.raises(
            TenantUOMRemediationReviewError
        ) as exc:
            service.approve_review(
                tenant_id=str(tenant.id),
                review_id=review.id,
                reviewed_by=str(reviewer.id),
                selected_action=LINK_EXISTING_UOM,
                selected_canonical_uom_id=str(
                    canonical.id
                ),
            )

        assert exc.value.status_code == 400

        db.session.rollback()


def test_historical_product_unit_cannot_be_discarded(app):
    with app.app_context():
        _prepare_catalogue()

        (
            tenant,
            creator,
            reviewer,
            source,
            target,
            tablet,
            _tablet_unit,
            capsule,
            _capsule_unit,
        ) = _mixed_fixture()

        service = _service()

        review = service.create_pending_review(
            tenant_id=str(tenant.id),
            source_uom_id=str(source.id),
            created_by=str(creator.id),
        )

        snapshot = dict(
            review.planner_snapshot
        )
        products = [
            dict(item)
            for item in snapshot["products"]
        ]

        for item in products:
            if item["product_id"] == str(
                tablet.id
            ):
                item[
                    "historical_reference_count"
                ] = 1

        snapshot["products"] = products
        review.planner_snapshot = snapshot
        db.session.flush()

        decisions = [
            {
                "product_id": str(tablet.id),
                "selected_action":
                    MOVE_CURRENT_PRODUCT,
                "target_tenant_uom_id":
                    str(target.id),
                "preserve_historical_unit":
                    False,
            },
            {
                "product_id": str(capsule.id),
                "selected_action":
                    MOVE_CURRENT_PRODUCT,
                "target_tenant_uom_id":
                    str(target.id),
                "preserve_historical_unit":
                    True,
            },
        ]

        with pytest.raises(
            TenantUOMRemediationReviewError
        ) as exc:
            service.approve_review(
                tenant_id=str(tenant.id),
                review_id=review.id,
                reviewed_by=str(reviewer.id),
                selected_action=SPLIT_CURRENT_PRODUCTS,
                product_decisions=decisions,
            )

        assert exc.value.status_code == 400
        assert "must be preserved" in str(
            exc.value
        )

        db.session.rollback()


def test_rejected_review_is_terminal(app):
    with app.app_context():
        _prepare_catalogue()

        (
            tenant,
            creator,
            reviewer,
            source,
            _product_row,
            _product_unit,
        ) = _safe_fixture()

        audit = AuditSpy()
        service = _service(audit)

        review = service.create_pending_review(
            tenant_id=str(tenant.id),
            source_uom_id=str(source.id),
            created_by=str(creator.id),
        )

        rejected = service.reject_review(
            tenant_id=str(tenant.id),
            review_id=review.id,
            reviewed_by=str(reviewer.id),
            review_reason="Alias requires correction.",
        )

        assert rejected.status == "rejected"

        with pytest.raises(
            TenantUOMRemediationReviewError
        ) as exc:
            service.supersede_review(
                tenant_id=str(tenant.id),
                review_id=review.id,
                reviewed_by=str(reviewer.id),
                review_reason="Cannot reopen rejected review.",
            )

        assert exc.value.status_code == 409

        assert (
            audit.calls[-1]["action"]
            == AuditAction.UOM_REMEDIATION_REVIEW_REJECTED
        )

        db.session.rollback()


def test_pending_and_approved_reviews_can_be_superseded(app):
    with app.app_context():
        _prepare_catalogue()

        (
            tenant,
            creator,
            reviewer,
            source,
            _product_row,
            _product_unit,
        ) = _safe_fixture()

        audit = AuditSpy()
        service = _service(audit)

        pending = service.create_pending_review(
            tenant_id=str(tenant.id),
            source_uom_id=str(source.id),
            created_by=str(creator.id),
        )

        superseded = service.supersede_review(
            tenant_id=str(tenant.id),
            review_id=pending.id,
            reviewed_by=str(reviewer.id),
            review_reason="Planner evidence will be refreshed.",
        )

        assert superseded.status == "superseded"

        second = service.create_pending_review(
            tenant_id=str(tenant.id),
            source_uom_id=str(source.id),
            created_by=str(creator.id),
        )

        canonical = _canonical("TAB")

        approved = service.approve_review(
            tenant_id=str(tenant.id),
            review_id=second.id,
            reviewed_by=str(reviewer.id),
            selected_action=LINK_EXISTING_UOM,
            selected_canonical_uom_id=str(
                canonical.id
            ),
        )

        assert approved.status == "approved"

        superseded_approved = (
            service.supersede_review(
                tenant_id=str(tenant.id),
                review_id=approved.id,
                reviewed_by=str(reviewer.id),
                review_reason=(
                    "Source data changed before execution."
                ),
            )
        )

        assert (
            superseded_approved.status
            == "superseded"
        )

        assert (
            audit.calls[-1]["action"]
            == AuditAction.UOM_REMEDIATION_REVIEW_SUPERSEDED
        )

        db.session.rollback()


def test_new_review_is_not_stale(app):
    with app.app_context():
        _prepare_catalogue()

        (
            tenant,
            creator,
            _reviewer,
            source,
            _product_row,
            _product_unit,
        ) = _safe_fixture()

        service = _service()

        review = service.create_pending_review(
            tenant_id=str(tenant.id),
            source_uom_id=str(source.id),
            created_by=str(creator.id),
        )

        result = service.assess_staleness(
            tenant_id=str(tenant.id),
            review_id=review.id,
        )

        assert result.is_stale is False
        assert result.reasons == ()
        assert (
            result.stored_fingerprint
            == result.current_fingerprint
        )
        assert (
            result.stored_planner_version
            == result.current_planner_version
        )

        db.session.rollback()


def test_review_becomes_stale_when_product_semantics_change(app):
    with app.app_context():
        _prepare_catalogue()

        (
            tenant,
            creator,
            _reviewer,
            source,
            product,
            _product_unit,
        ) = _safe_fixture()

        service = _service()

        review = service.create_pending_review(
            tenant_id=str(tenant.id),
            source_uom_id=str(source.id),
            created_by=str(creator.id),
        )

        stored_snapshot = dict(
            review.planner_snapshot
        )
        stored_fingerprint = (
            review.planner_fingerprint
        )

        product.name = (
            "Paracetamol Capsules 500mg"
        )
        db.session.flush()

        result = service.assess_staleness(
            tenant_id=str(tenant.id),
            review_id=review.id,
        )

        assert result.is_stale is True
        assert (
            "planner_fingerprint_changed"
            in result.reasons
        )

        assert (
            result.current_fingerprint
            != stored_fingerprint
        )

        # Stored review evidence must remain unchanged.
        assert (
            review.planner_fingerprint
            == stored_fingerprint
        )
        assert (
            review.planner_snapshot
            == stored_snapshot
        )

        db.session.rollback()


def test_review_is_stale_when_planner_version_changes(app):
    with app.app_context():
        _prepare_catalogue()

        (
            tenant,
            creator,
            _reviewer,
            source,
            _product_row,
            _product_unit,
        ) = _safe_fixture()

        service = _service()

        review = service.create_pending_review(
            tenant_id=str(tenant.id),
            source_uom_id=str(source.id),
            created_by=str(creator.id),
        )

        review.planner_version = "older-version"
        db.session.flush()

        result = service.assess_staleness(
            tenant_id=str(tenant.id),
            review_id=review.id,
        )

        assert result.is_stale is True
        assert (
            "planner_version_changed"
            in result.reasons
        )

        db.session.rollback()


def test_staleness_assessment_is_tenant_isolated(app):
    with app.app_context():
        _prepare_catalogue()

        (
            tenant,
            creator,
            _reviewer,
            source,
            _product_row,
            _product_unit,
        ) = _safe_fixture()

        other = _tenant(
            "Staleness Other Tenant"
        )

        service = _service()

        review = service.create_pending_review(
            tenant_id=str(tenant.id),
            source_uom_id=str(source.id),
            created_by=str(creator.id),
        )

        with pytest.raises(
            TenantUOMRemediationReviewError
        ) as exc:
            service.assess_staleness(
                tenant_id=str(other.id),
                review_id=review.id,
            )

        assert exc.value.status_code == 404

        db.session.rollback()


def test_review_detail_includes_decisions_and_staleness(app):
    with app.app_context():
        _prepare_catalogue()

        (
            tenant,
            creator,
            _reviewer,
            source,
            _product_row,
            _product_unit,
        ) = _safe_fixture()

        service = _service()

        review = service.create_pending_review(
            tenant_id=str(tenant.id),
            source_uom_id=str(source.id),
            created_by=str(creator.id),
        )

        detail = service.get_review_detail(
            tenant_id=str(tenant.id),
            review_id=review.id,
        )

        assert detail["review"].id == review.id
        assert len(
            detail["product_decisions"]
        ) == 1
        assert (
            detail["staleness"].is_stale
            is False
        )

        without_staleness = (
            service.get_review_detail(
                tenant_id=str(tenant.id),
                review_id=review.id,
                include_staleness=False,
            )
        )

        assert (
            without_staleness["staleness"]
            is None
        )

        db.session.rollback()


def test_stale_review_cannot_be_approved(app):
    with app.app_context():
        _prepare_catalogue()

        (
            tenant,
            creator,
            reviewer,
            source,
            product,
            _product_unit,
        ) = _safe_fixture()

        service = _service()

        review = service.create_pending_review(
            tenant_id=str(tenant.id),
            source_uom_id=str(source.id),
            created_by=str(creator.id),
        )

        product.name = "Paracetamol Capsules 500mg"
        db.session.flush()

        canonical = _canonical("TAB")

        with pytest.raises(
            TenantUOMRemediationReviewError
        ) as exc:
            service.approve_review(
                tenant_id=str(tenant.id),
                review_id=review.id,
                reviewed_by=str(reviewer.id),
                selected_action=LINK_EXISTING_UOM,
                selected_canonical_uom_id=str(
                    canonical.id
                ),
            )

        assert exc.value.status_code == 409
        assert "stale" in str(exc.value).lower()
        assert review.status == "pending"

        db.session.rollback()


def test_mixed_move_requires_explicit_target_tenant_uom(app):
    with app.app_context():
        _prepare_catalogue()

        (
            tenant,
            creator,
            reviewer,
            source,
            _target,
            tablet,
            _tablet_unit,
            capsule,
            _capsule_unit,
        ) = _mixed_fixture()

        service = _service()

        review = service.create_pending_review(
            tenant_id=str(tenant.id),
            source_uom_id=str(source.id),
            created_by=str(creator.id),
        )

        canonical = _canonical("TAB")

        with pytest.raises(
            TenantUOMRemediationReviewError
        ) as exc:
            service.approve_review(
                tenant_id=str(tenant.id),
                review_id=str(review.id),
                reviewed_by=str(reviewer.id),
                selected_action=SPLIT_CURRENT_PRODUCTS,
                selected_canonical_uom_id=str(
                    canonical.id
                ),
                product_decisions=[
                    {
                        "product_id": str(
                            tablet.id
                        ),
                        "selected_action":
                            MOVE_CURRENT_PRODUCT,
                        "target_canonical_uom_id":
                            str(canonical.id),
                    },
                    {
                        "product_id": str(
                            capsule.id
                        ),
                        "selected_action":
                            KEEP_CURRENT_PRODUCT,
                    },
                ],
            )

        assert exc.value.status_code == 400
        assert "target_tenant_uom_id" in str(
            exc.value
        )

        db.session.rollback()



def test_mixed_move_rejects_unmapped_target_tenant_uom(app):
    with app.app_context():
        _prepare_catalogue()

        (
            tenant,
            creator,
            reviewer,
            source,
            _target,
            tablet,
            _tablet_unit,
            capsule,
            _capsule_unit,
        ) = _mixed_fixture()

        service = _service()

        review = service.create_pending_review(
            tenant_id=str(tenant.id),
            source_uom_id=str(source.id),
            created_by=str(creator.id),
        )

        tablet_canonical = _canonical("TAB")
        capsule_canonical = _canonical("CAP")

        unmapped_target = _unit(
            tenant=tenant,
            code="CAP-UNMAPPED",
            name="Capsule Unmapped Target",
        )

        with pytest.raises(
            TenantUOMRemediationReviewError
        ) as exc:
            service.approve_review(
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
                        "preserve_historical_unit": True,
                    },
                    {
                        "product_id": str(capsule.id),
                        "selected_action":
                            MOVE_CURRENT_PRODUCT,
                        "target_canonical_uom_id":
                            str(capsule_canonical.id),
                        "target_tenant_uom_id":
                            str(unmapped_target.id),
                        "preserve_historical_unit": True,
                    },
                ],
            )

        assert exc.value.status_code == 400
        assert "canonically mapped" in str(
            exc.value
        )

        assert review.status == "pending"
        assert unmapped_target.canonical_uom_id is None

        db.session.rollback()


def test_mixed_review_persists_keep_and_move_execution_decisions(app):
    with app.app_context():
        _prepare_catalogue()

        (
            tenant,
            creator,
            reviewer,
            source,
            target,
            tablet,
            tablet_unit,
            capsule,
            capsule_unit,
        ) = _mixed_fixture()

        service = _service()

        review = service.create_pending_review(
            tenant_id=str(tenant.id),
            source_uom_id=str(source.id),
            created_by=str(creator.id),
        )

        tablet_canonical = _canonical("TAB")
        capsule_canonical = _canonical("CAP")

        source_before = source.canonical_uom_id
        tablet_product_unit_before = tablet.unit_id
        capsule_product_unit_before = capsule.unit_id
        tablet_pu_unit_before = tablet_unit.unit_id
        capsule_pu_unit_before = capsule_unit.unit_id

        approved = service.approve_review(
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
                    "review_note":
                        "Tablet remains on source TAB UOM.",
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
                    "review_note":
                        "Capsule moves to CAP tenant UOM.",
                },
            ],
            review_reason=(
                "Split mixed tablet and capsule semantics."
            ),
        )

        assert approved.status == "approved"
        assert (
            approved.selected_action
            == SPLIT_CURRENT_PRODUCTS
        )
        assert (
            approved.selected_canonical_uom_id
            == str(tablet_canonical.id)
        )

        decisions = {
            str(row.product_id): row
            for row in (
                db.session.query(
                    TenantUOMRemediationProductDecision
                )
                .filter(
                    TenantUOMRemediationProductDecision.review_id
                    == str(review.id)
                )
                .all()
            )
        }

        tablet_decision = decisions[str(tablet.id)]
        capsule_decision = decisions[str(capsule.id)]

        assert (
            tablet_decision.selected_action
            == KEEP_CURRENT_PRODUCT
        )
        assert (
            tablet_decision.target_tenant_uom_id
            is None
        )
        assert (
            tablet_decision.target_canonical_uom_id
            is None
        )
        assert (
            tablet_decision.preserve_historical_unit
            is True
        )

        assert (
            capsule_decision.selected_action
            == MOVE_CURRENT_PRODUCT
        )
        assert (
            capsule_decision.target_tenant_uom_id
            == str(target.id)
        )
        assert (
            capsule_decision.target_canonical_uom_id
            == str(capsule_canonical.id)
        )
        assert (
            capsule_decision.preserve_historical_unit
            is True
        )

        # Approval remains review-only.
        assert source.canonical_uom_id == source_before

        assert (
            tablet.unit_id
            == tablet_product_unit_before
        )
        assert (
            capsule.unit_id
            == capsule_product_unit_before
        )

        assert (
            tablet_unit.unit_id
            == tablet_pu_unit_before
        )
        assert (
            capsule_unit.unit_id
            == capsule_pu_unit_before
        )

        db.session.rollback()
