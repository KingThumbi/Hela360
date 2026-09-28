from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from flask import Flask

from app.api.errors import register_error_handlers
from app.api.products import bp as products_bp
from app.extensions import db
from app.models import (
    Branch,
    InventoryBatch,
    Product,
    StockAdjustment,
    StockAdjustmentItem,
    StockCount,
    StockCountItem,
    Tenant,
    User,
    Warehouse,
)


TENANT_ID = "tenant-a"
OTHER_TENANT_ID = "tenant-b"

BRANCH_ID = "branch-a"
OTHER_BRANCH_ID = "branch-b"

USER_ID = "user-a"

PRODUCT_ID = "product-a"
SECOND_PRODUCT_ID = "product-b"

WAREHOUSE_ID = "warehouse-a"
SECOND_WAREHOUSE_ID = "warehouse-b"
OTHER_BRANCH_WAREHOUSE_ID = "warehouse-c"

BATCH_ID = "batch-a"


@pytest.fixture()
def app_context():
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TESTING=True,
    )

    db.init_app(app)
    app.register_blueprint(
        products_bp,
        url_prefix="/api",
    )
    register_error_handlers(app)

    with app.app_context():
        Tenant.__table__.create(db.engine)
        Branch.__table__.create(db.engine)
        User.__table__.create(db.engine)
        Product.__table__.create(db.engine)
        Warehouse.__table__.create(db.engine)
        InventoryBatch.__table__.create(db.engine)
        StockCount.__table__.create(db.engine)
        StockCountItem.__table__.create(db.engine)
        StockAdjustment.__table__.create(db.engine)
        StockAdjustmentItem.__table__.create(db.engine)

        seed_data()

        yield app

        db.session.remove()

        StockAdjustmentItem.__table__.drop(
            db.engine
        )
        StockAdjustment.__table__.drop(
            db.engine
        )
        StockCountItem.__table__.drop(
            db.engine
        )
        StockCount.__table__.drop(
            db.engine
        )
        InventoryBatch.__table__.drop(
            db.engine
        )
        Warehouse.__table__.drop(
            db.engine
        )
        Product.__table__.drop(
            db.engine
        )
        User.__table__.drop(
            db.engine
        )
        Branch.__table__.drop(
            db.engine
        )
        Tenant.__table__.drop(
            db.engine
        )


@pytest.fixture()
def identity():
    return SimpleNamespace(
        user_id=USER_ID,
        tenant_id=TENANT_ID,
        branch_id=BRANCH_ID,
    )


@pytest.fixture()
def client(
    app_context,
    identity: SimpleNamespace,
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


def seed_data():
    started = datetime(
        2026,
        8,
        10,
        8,
        0,
        tzinfo=timezone.utc,
    )

    completed = datetime(
        2026,
        8,
        10,
        10,
        0,
        tzinfo=timezone.utc,
    )

    posted = datetime(
        2026,
        8,
        10,
        10,
        30,
        tzinfo=timezone.utc,
    )

    db.session.add_all(
        [
            Tenant(
                id=TENANT_ID,
                legal_name="Tenant A",
                display_name="Tenant A",
            ),
            Tenant(
                id=OTHER_TENANT_ID,
                legal_name="Tenant B",
                display_name="Tenant B",
            ),
            Branch(
                id=BRANCH_ID,
                tenant_id=TENANT_ID,
                code="BR-A",
                name="Branch A",
            ),
            Branch(
                id=OTHER_BRANCH_ID,
                tenant_id=TENANT_ID,
                code="BR-B",
                name="Branch B",
            ),
            User(
                id=USER_ID,
                tenant_id=TENANT_ID,
                branch_id=BRANCH_ID,
                first_name="Inventory",
                last_name="Auditor",
                email="inventory@example.test",
                username="inventory",
                password_hash="hash",
            ),
            Product(
                id=PRODUCT_ID,
                tenant_id=TENANT_ID,
                internal_sku="ASP-100",
                name="Aspirin 100mg",
                track_batches=True,
                track_expiry=True,
            ),
            Product(
                id=SECOND_PRODUCT_ID,
                tenant_id=TENANT_ID,
                internal_sku="ORS-001",
                name="ORS Sachet",
            ),
            Product(
                id="other-tenant-product",
                tenant_id=OTHER_TENANT_ID,
                internal_sku="OTHER",
                name="Other Tenant Product",
            ),
            Warehouse(
                id=WAREHOUSE_ID,
                tenant_id=TENANT_ID,
                branch_id=BRANCH_ID,
                code="MAIN",
                name="Main Warehouse",
            ),
            Warehouse(
                id=SECOND_WAREHOUSE_ID,
                tenant_id=TENANT_ID,
                branch_id=BRANCH_ID,
                code="FRONT",
                name="Front Store",
            ),
            Warehouse(
                id=OTHER_BRANCH_WAREHOUSE_ID,
                tenant_id=TENANT_ID,
                branch_id=OTHER_BRANCH_ID,
                code="OTHER",
                name="Other Branch Warehouse",
            ),
        ]
    )

    db.session.flush()

    batch = InventoryBatch(
        id=BATCH_ID,
        tenant_id=TENANT_ID,
        product_id=PRODUCT_ID,
        warehouse_id=WAREHOUSE_ID,
        batch_number="BATCH-1",
        expiry_date=date(
            2027,
            1,
            31,
        ),
        quantity_on_hand=Decimal(
            "12.0000"
        ),
        quantity_reserved=Decimal(
            "0.0000"
        ),
    )

    db.session.add(batch)
    db.session.flush()

    count = StockCount(
        id="count-a",
        tenant_id=TENANT_ID,
        branch_id=BRANCH_ID,
        warehouse_id=WAREHOUSE_ID,
        count_number="SC-2026-A",
        idempotency_key="count-a",
        request_fingerprint="a" * 64,
        scope_type="full",
        count_mode="blind",
        status="completed",
        snapshot_at=started,
        started_at=started,
        started_by=USER_ID,
        completed_at=completed,
        completed_by=USER_ID,
    )

    db.session.add(count)
    db.session.flush()

    line = StockCountItem(
        id="count-item-a",
        stock_count_id=count.id,
        product_id=PRODUCT_ID,
        batch_id=BATCH_ID,
        source_type="snapshot",
        line_number=1,
        snapshot_quantity=Decimal(
            "10.0000"
        ),
        expected_quantity=Decimal(
            "10.0000"
        ),
        counted_quantity=Decimal(
            "12.0000"
        ),
        counted_unit_quantity=Decimal(
            "2.0000"
        ),
        counted_unit_code_snapshot="BOX",
        counted_unit_name_snapshot="Box",
        counted_conversion_factor_to_base=Decimal(
            "6.000000"
        ),
        variance_quantity=Decimal(
            "2.0000"
        ),
        counted_at=completed,
        counted_by=USER_ID,
    )

    db.session.add(line)
    db.session.flush()

    adjustment = StockAdjustment(
        id="adjustment-a",
        tenant_id=TENANT_ID,
        branch_id=BRANCH_ID,
        warehouse_id=WAREHOUSE_ID,
        adjustment_number="SA-2026-A",
        reason_code="stock_count",
        reason="Stock count variance",
        source_type="stock_count",
        source_id=count.id,
        status="posted",
        idempotency_key="adjustment-a",
        request_fingerprint="b" * 64,
        posted_at=posted,
        posted_by=USER_ID,
    )

    db.session.add(adjustment)
    db.session.flush()

    db.session.add(
        StockAdjustmentItem(
            id="adjustment-item-a",
            stock_adjustment_id=(
                adjustment.id
            ),
            product_id=PRODUCT_ID,
            batch_id=BATCH_ID,
            stock_count_item_id=line.id,
            line_number=1,
            quantity_delta=Decimal(
                "2.0000"
            ),
            reason="Count variance",
        )
    )

    # Same product, other branch:
    # must never appear.
    other_count = StockCount(
        id="count-other-branch",
        tenant_id=TENANT_ID,
        branch_id=OTHER_BRANCH_ID,
        warehouse_id=(
            OTHER_BRANCH_WAREHOUSE_ID
        ),
        count_number="SC-OTHER-BRANCH",
        idempotency_key=(
            "count-other-branch"
        ),
        request_fingerprint="c" * 64,
        scope_type="full",
        count_mode="visible",
        status="completed",
        snapshot_at=started,
        started_at=started,
        started_by=USER_ID,
        completed_at=completed,
        completed_by=USER_ID,
    )

    db.session.add(other_count)
    db.session.flush()

    db.session.add(
        StockCountItem(
            id="other-branch-line",
            stock_count_id=(
                other_count.id
            ),
            product_id=PRODUCT_ID,
            source_type="snapshot",
            line_number=1,
            snapshot_quantity=Decimal(
                "5.0000"
            ),
            expected_quantity=Decimal(
                "5.0000"
            ),
            counted_quantity=Decimal(
                "5.0000"
            ),
            variance_quantity=Decimal(
                "0.0000"
            ),
        )
    )

    # Same branch/count domain,
    # different product: must not appear.
    second_count = StockCount(
        id="count-second-product",
        tenant_id=TENANT_ID,
        branch_id=BRANCH_ID,
        warehouse_id=(
            SECOND_WAREHOUSE_ID
        ),
        count_number="SC-OTHER-PRODUCT",
        idempotency_key=(
            "count-second-product"
        ),
        request_fingerprint="d" * 64,
        scope_type="full",
        count_mode="visible",
        status="completed",
        snapshot_at=started,
        started_at=started,
        started_by=USER_ID,
        completed_at=completed,
        completed_by=USER_ID,
    )

    db.session.add(second_count)
    db.session.flush()

    db.session.add(
        StockCountItem(
            id="second-product-line",
            stock_count_id=(
                second_count.id
            ),
            product_id=(
                SECOND_PRODUCT_ID
            ),
            source_type="snapshot",
            line_number=1,
            snapshot_quantity=Decimal(
                "4.0000"
            ),
            expected_quantity=Decimal(
                "4.0000"
            ),
            counted_quantity=Decimal(
                "4.0000"
            ),
            variance_quantity=Decimal(
                "0.0000"
            ),
        )
    )

    db.session.commit()


def test_stock_count_history_is_product_and_branch_scoped(
    client,
):
    response = client.get(
        (
            f"/api/products/{PRODUCT_ID}"
            "/history/stock-counts"
        )
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["ok"] is True
    assert len(payload["items"]) == 1

    item = payload["items"][0]

    assert item["stock_count"][
        "id"
    ] == "count-a"

    assert item["stock_count"][
        "count_number"
    ] == "SC-2026-A"

    assert item["stock_count"][
        "lifecycle"
    ] == "posted"

    assert item["warehouse"] == {
        "id": WAREHOUSE_ID,
        "code": "MAIN",
        "name": "Main Warehouse",
    }

    assert item["line"]["id"] == (
        "count-item-a"
    )

    assert item["line"][
        "snapshot_quantity"
    ] == "10.0000"

    assert item["line"][
        "expected_quantity"
    ] == "10.0000"

    assert item["line"][
        "counted_quantity"
    ] == "12.0000"

    assert item["line"][
        "variance_quantity"
    ] == "2.0000"

    assert item["line"][
        "counted_unit_quantity"
    ] == "2.0000"

    assert item["line"][
        "counted_unit_code"
    ] == "BOX"

    assert item["line"][
        "counted_conversion_factor_to_base"
    ] == "6.000000"

    assert item["line"]["batch"][
        "batch_number"
    ] == "BATCH-1"

    assert item["adjustment"] == {
        "id": "adjustment-a",
        "adjustment_number": (
            "SA-2026-A"
        ),
        "status": "posted",
        "posted_at": (
            "2026-08-10T10:30:00"
        ),
        "quantity_delta": "2.0000",
    }


def test_open_blind_count_hides_system_quantities(
    client,
):
    count = StockCount(
        id="count-open-blind",
        tenant_id=TENANT_ID,
        branch_id=BRANCH_ID,
        warehouse_id=WAREHOUSE_ID,
        count_number="SC-OPEN-BLIND",
        idempotency_key=(
            "count-open-blind"
        ),
        request_fingerprint="e" * 64,
        scope_type="full",
        count_mode="blind",
        status="open",
        snapshot_at=datetime(
            2026,
            8,
            11,
            8,
            0,
            tzinfo=timezone.utc,
        ),
        started_at=datetime(
            2026,
            8,
            11,
            8,
            0,
            tzinfo=timezone.utc,
        ),
        started_by=USER_ID,
    )

    db.session.add(count)
    db.session.flush()

    db.session.add(
        StockCountItem(
            id="count-open-blind-line",
            stock_count_id=count.id,
            product_id=PRODUCT_ID,
            batch_id=BATCH_ID,
            source_type="snapshot",
            line_number=1,
            snapshot_quantity=Decimal(
                "12.0000"
            ),
            expected_quantity=Decimal(
                "12.0000"
            ),
            counted_quantity=None,
            variance_quantity=None,
        )
    )

    db.session.commit()

    response = client.get(
        (
            f"/api/products/{PRODUCT_ID}"
            "/history/stock-counts"
        )
    )

    assert response.status_code == 200

    item = next(
        row
        for row in response.get_json()[
            "items"
        ]
        if row["stock_count"]["id"]
        == "count-open-blind"
    )

    assert item["stock_count"][
        "lifecycle"
    ] == "counting"

    line = item["line"]

    assert "snapshot_quantity" not in line
    assert "expected_quantity" not in line
    assert "variance_quantity" not in line


def test_stock_count_history_lifecycle_uses_whole_count_variance(
    client,
):
    started = datetime(
        2026,
        8,
        12,
        8,
        0,
        tzinfo=timezone.utc,
    )

    completed = datetime(
        2026,
        8,
        12,
        9,
        0,
        tzinfo=timezone.utc,
    )

    count = StockCount(
        id="count-cross-line-variance",
        tenant_id=TENANT_ID,
        branch_id=BRANCH_ID,
        warehouse_id=WAREHOUSE_ID,
        count_number="SC-CROSS-LINE",
        idempotency_key="count-cross-line-variance",
        request_fingerprint="f" * 64,
        scope_type="full",
        count_mode="visible",
        status="completed",
        snapshot_at=started,
        started_at=started,
        started_by=USER_ID,
        completed_at=completed,
        completed_by=USER_ID,
    )

    db.session.add(count)
    db.session.flush()

    db.session.add_all(
        [
            StockCountItem(
                id="count-cross-line-product-a",
                stock_count_id=count.id,
                product_id=PRODUCT_ID,
                source_type="snapshot",
                line_number=1,
                snapshot_quantity=Decimal(
                    "5.0000"
                ),
                expected_quantity=Decimal(
                    "5.0000"
                ),
                counted_quantity=Decimal(
                    "5.0000"
                ),
                variance_quantity=Decimal(
                    "0.0000"
                ),
                counted_at=completed,
                counted_by=USER_ID,
            ),
            StockCountItem(
                id="count-cross-line-product-b",
                stock_count_id=count.id,
                product_id=SECOND_PRODUCT_ID,
                source_type="snapshot",
                line_number=2,
                snapshot_quantity=Decimal(
                    "4.0000"
                ),
                expected_quantity=Decimal(
                    "4.0000"
                ),
                counted_quantity=Decimal(
                    "6.0000"
                ),
                variance_quantity=Decimal(
                    "2.0000"
                ),
                counted_at=completed,
                counted_by=USER_ID,
            ),
        ]
    )

    db.session.commit()

    response = client.get(
        (
            f"/api/products/{PRODUCT_ID}"
            "/history/stock-counts"
        )
    )

    assert response.status_code == 200

    item = next(
        row
        for row in response.get_json()["items"]
        if row["stock_count"]["id"]
        == "count-cross-line-variance"
    )

    assert item["line"][
        "variance_quantity"
    ] == "0.0000"

    assert item["stock_count"][
        "lifecycle"
    ] == "awaiting_posting"

    assert item["adjustment"] is None


def test_stock_count_history_supports_warehouse_and_date_filters(
    client,
):
    response = client.get(
        (
            f"/api/products/{PRODUCT_ID}"
            "/history/stock-counts"
            f"?warehouse_id={WAREHOUSE_ID}"
            "&date_from=2026-08-10"
            "&date_to=2026-08-10"
        )
    )

    assert response.status_code == 200

    ids = [
        item["stock_count"]["id"]
        for item in response.get_json()[
            "items"
        ]
    ]

    assert ids == ["count-a"]


def test_stock_count_history_is_paginated(
    client,
):
    response = client.get(
        (
            f"/api/products/{PRODUCT_ID}"
            "/history/stock-counts"
            "?page=1&per_page=1"
        )
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert len(payload["items"]) == 1

    assert payload["pagination"] == {
        "page": 1,
        "per_page": 1,
        "total": 1,
        "pages": 1,
        "has_prev": False,
        "has_next": False,
    }


def test_stock_count_history_rejects_cross_tenant_product(
    client,
):
    response = client.get(
        (
            "/api/products/"
            "other-tenant-product/"
            "history/stock-counts"
        )
    )

    assert response.status_code == 404
    assert response.get_json() == {
        "ok": False,
        "error": "Product not found.",
    }


def test_stock_count_history_requires_branch(
    client,
    identity: SimpleNamespace,
):
    identity.branch_id = None

    response = client.get(
        (
            f"/api/products/{PRODUCT_ID}"
            "/history/stock-counts"
        )
    )

    assert response.status_code == 400
    assert "branch" in (
        response.get_json()["error"]
    )


def test_stock_count_history_requires_inventory_count(
    app_context,
    identity: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
):
    captured = {}

    def deny(*args, **kwargs):
        captured["kwargs"] = kwargs

        from app.auth.exceptions import (
            PermissionDeniedError,
        )

        raise PermissionDeniedError(
            "denied"
        )

    monkeypatch.setattr(
        "app.services.tenant.auth.decorators."
        "get_current_identity",
        lambda: identity,
    )

    monkeypatch.setattr(
        "app.services.tenant.auth.decorators."
        "authorization_service.authorize",
        deny,
    )

    response = (
        app_context.test_client().get(
            (
                f"/api/products/{PRODUCT_ID}"
                "/history/stock-counts"
            )
        )
    )

    assert response.status_code == 403
    assert captured["kwargs"][
        "permission"
    ] == "inventory.count"
