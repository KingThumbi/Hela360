from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest
from flask import Flask

from app.api.errors import register_error_handlers
from app.api.products import bp as products_bp
from app.auth.exceptions import PermissionDeniedError
from app.extensions import db
from app.models import (
    Brand,
    DispensingRecord,
    GoodsReceiptItem,
    InventoryBatch,
    InventoryMovement,
    Product,
    ProductCategory,
    ProductCode,
    ProductUnit,
    SaleItem,
    SaleRefundItem,
    StockAdjustmentItem,
    StockBalance,
    StockCountItem,
    TaxCode,
    Tenant,
    UnitOfMeasure,
)


@pytest.fixture()
def app_context():
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TESTING=True,
    )
    db.init_app(app)
    app.register_blueprint(products_bp, url_prefix="/api")
    register_error_handlers(app)

    with app.app_context():
        Tenant.__table__.create(db.engine)
        ProductCategory.__table__.create(db.engine)
        Brand.__table__.create(db.engine)
        UnitOfMeasure.__table__.create(db.engine)
        TaxCode.__table__.create(db.engine)
        Product.__table__.create(db.engine)

        # Product permanent-deletion eligibility inspects every direct
        # operational dependency even when no dependency rows exist.
        InventoryBatch.__table__.create(db.engine)
        StockBalance.__table__.create(db.engine)
        InventoryMovement.__table__.create(db.engine)
        GoodsReceiptItem.__table__.create(db.engine)
        StockCountItem.__table__.create(db.engine)
        StockAdjustmentItem.__table__.create(db.engine)
        SaleItem.__table__.create(db.engine)
        DispensingRecord.__table__.create(db.engine)
        SaleRefundItem.__table__.create(db.engine)

        ProductUnit.__table__.create(db.engine)
        ProductCode.__table__.create(db.engine)

        db.session.add_all(
            [
                Tenant(
                    id="tenant-1",
                    legal_name="Tenant 1",
                    display_name="Tenant 1",
                ),
                Tenant(
                    id="tenant-2",
                    legal_name="Tenant 2",
                    display_name="Tenant 2",
                ),
            ]
        )
        db.session.commit()

        yield app

        db.session.remove()
        ProductCode.__table__.drop(db.engine)
        ProductUnit.__table__.drop(db.engine)

        SaleRefundItem.__table__.drop(db.engine)
        DispensingRecord.__table__.drop(db.engine)
        SaleItem.__table__.drop(db.engine)
        StockAdjustmentItem.__table__.drop(db.engine)
        StockCountItem.__table__.drop(db.engine)
        GoodsReceiptItem.__table__.drop(db.engine)
        InventoryMovement.__table__.drop(db.engine)
        StockBalance.__table__.drop(db.engine)
        InventoryBatch.__table__.drop(db.engine)

        Product.__table__.drop(db.engine)
        TaxCode.__table__.drop(db.engine)
        UnitOfMeasure.__table__.drop(db.engine)
        Brand.__table__.drop(db.engine)
        ProductCategory.__table__.drop(db.engine)
        Tenant.__table__.drop(db.engine)


@pytest.fixture()
def client(app_context, monkeypatch: pytest.MonkeyPatch):
    identity = SimpleNamespace(
        user_id="user-1",
        tenant_id="tenant-1",
        branch_id="branch-1",
    )

    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.get_current_identity",
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
        "app.services.tenant.auth.decorators.authorization_service.authorize",
        lambda *args, **kwargs: None,
    )

    return app_context.test_client()


def add_product(
    tenant_id: str,
    sku: str,
    name: str,
    *,
    supplier_sku: str | None = None,
    generic_name: str | None = None,
    product_type: str = "stockable",
    is_active: bool = True,
) -> Product:
    product = Product(
        tenant_id=tenant_id,
        internal_sku=sku,
        supplier_sku=supplier_sku,
        name=name,
        generic_name=generic_name,
        product_type=product_type,
        is_active=is_active,
    )
    db.session.add(product)
    db.session.flush()
    return product


def test_product_list_empty_envelope(client):
    response = client.get("/api/products")

    assert response.status_code == 200
    assert response.json == {
        "ok": True,
        "count": 0,
        "items": [],
    }


def test_product_units_endpoint_lists_product_specific_units(client):
    unit = UnitOfMeasure(
        id="unit-box",
        tenant_id="tenant-1",
        code="BOX",
        name="Box",
    )
    product = Product(
        id="product-1",
        tenant_id="tenant-1",
        internal_sku="SKU-001",
        name="Paracetamol",
        unit_id="unit-box",
    )
    product_unit = ProductUnit(
        id="product-unit-1",
        tenant_id="tenant-1",
        product_id="product-1",
        unit_id="unit-box",
        conversion_factor_to_base=Decimal("10.000000"),
        is_base=False,
        can_sell=True,
        can_receive=True,
        sale_price=Decimal("120.00"),
        minimum_sale_price=Decimal("100.00"),
        is_active=True,
    )
    db.session.add_all([unit, product, product_unit])
    db.session.commit()

    response = client.get("/api/products/product-1/units")

    assert response.status_code == 200
    assert response.json["ok"] is True
    assert response.json["items"] == [
        {
            "id": "product-unit-1",
            "tenant_id": "tenant-1",
            "product_id": "product-1",
            "unit": {
                "id": "unit-box",
                "code": "BOX",
                "name": "Box",
            },
            "conversion_factor_to_base": "10.000000",
            "is_base": False,
            "can_sell": True,
            "can_receive": True,
            "sale_price": "120.00",
            "minimum_sale_price": "100.00",
            "is_active": True,
            "created_at": product_unit.created_at.isoformat(),
            "updated_at": product_unit.updated_at.isoformat(),
        }
    ]


def test_product_list_returns_serialized_tenant_products(client):
    add_product(
        "tenant-1",
        "SKU-001",
        "Paracetamol 500mg",
        supplier_sku="SUP-001",
        generic_name="Paracetamol",
    )
    add_product(
        "tenant-2",
        "SKU-002",
        "Hidden Tenant Product",
    )
    db.session.commit()

    response = client.get("/api/products")

    assert response.status_code == 200
    assert response.json["ok"] is True
    assert response.json["count"] == 1
    assert len(response.json["items"]) == 1

    item = response.json["items"][0]
    assert item["tenant_id"] == "tenant-1"
    assert item["internal_sku"] == "SKU-001"
    assert item["supplier_sku"] == "SUP-001"
    assert item["name"] == "Paracetamol 500mg"
    assert item["generic_name"] == "Paracetamol"
    assert item["product_type"] == "stockable"
    assert item["track_inventory"] is True
    assert item["requires_prescription"] is False
    assert item["category"] is None
    assert item["brand"] is None
    assert item["unit"] is None
    assert item["codes"] == []


def test_product_list_search_is_tenant_scoped(client):
    add_product(
        "tenant-1",
        "SKU-001",
        "Amoxicillin",
        generic_name="Amoxicillin",
    )
    add_product(
        "tenant-2",
        "SKU-002",
        "Tenant Two Match",
        supplier_sku="MATCH-ONLY-OTHER-TENANT",
    )
    db.session.commit()

    response = client.get("/api/products?search=match")

    assert response.status_code == 200
    assert response.json["ok"] is True
    assert response.json["count"] == 0
    assert response.json["items"] == []


def test_product_list_search_matches_supported_fields(client):
    add_product(
        "tenant-1",
        "SKU-001",
        "Cetirizine",
        supplier_sku="ALLERGY-001",
    )
    add_product(
        "tenant-1",
        "SKU-002",
        "Ibuprofen",
    )
    db.session.commit()

    response = client.get("/api/products?search=allergy")

    assert response.status_code == 200
    assert response.json["count"] == 1
    assert response.json["items"][0]["internal_sku"] == "SKU-001"


def test_product_list_pagination_count_is_tenant_scoped(client):
    add_product("tenant-1", "SKU-001", "Alpha")
    add_product("tenant-1", "SKU-002", "Beta")
    add_product("tenant-1", "SKU-003", "Gamma")
    add_product("tenant-2", "SKU-004", "Other Tenant")
    db.session.commit()

    response = client.get("/api/products?page=2&per_page=1")

    assert response.status_code == 200
    assert response.json["ok"] is True
    assert response.json["count"] == 3
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["name"] == "Beta"


def test_product_list_rejects_invalid_pagination(client):
    response = client.get("/api/products?page=0&per_page=25")

    assert response.status_code == 400
    assert response.json == {
        "ok": False,
        "error": "page must be a positive integer.",
    }


def test_product_list_missing_permission_is_rejected(
    app_context,
    monkeypatch: pytest.MonkeyPatch,
):
    identity = SimpleNamespace(
        user_id="user-1",
        tenant_id="tenant-1",
        branch_id=None,
    )

    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.get_current_identity",
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
        "app.services.tenant.auth.decorators.authorization_service.authorize",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            PermissionDeniedError("Permission denied.")
        ),
    )

    response = app_context.test_client().get("/api/products")

    assert response.status_code == 403
    assert response.json["error"]["code"] == "AUTHORIZATION_DENIED"


def test_product_detail_and_by_code_remain_tenant_scoped(client):
    product = add_product(
        "tenant-1",
        "SKU-001",
        "Insulin",
    )
    db.session.add(
        ProductCode(
            tenant_id="tenant-1",
            product_id=product.id,
            code_type="barcode",
            code_value="BAR-001",
            is_primary=True,
            generated_by_system=False,
        )
    )
    db.session.commit()

    detail_response = client.get(f"/api/products/{product.id}")
    code_response = client.get("/api/products/by-code/BAR-001")

    assert detail_response.status_code == 200
    assert detail_response.json["item"]["id"] == product.id
    assert code_response.status_code == 200
    assert code_response.json["item"]["id"] == product.id
    assert code_response.json["item"]["codes"][0]["code_value"] == "BAR-001"


# ============================================================================
# Product lifecycle contract
# ============================================================================


def test_archive_product_archives_active_product(client):
    product = add_product(
        "tenant-1",
        "ARCHIVE-001",
        "Archive Product",
    )
    product_id = product.id

    db.session.commit()

    response = client.post(
        f"/api/products/{product_id}/archive"
    )

    assert response.status_code == 200
    assert response.json["ok"] is True
    assert response.json["item"]["id"] == product_id
    assert response.json["item"]["tenant_id"] == "tenant-1"
    assert response.json["item"]["is_active"] is False

    db.session.expire_all()

    persisted = db.session.get(Product, product_id)

    assert persisted is not None
    assert persisted.is_active is False


def test_archive_product_is_idempotent(client):
    product = add_product(
        "tenant-1",
        "ARCHIVE-002",
        "Already Archived Product",
        is_active=False,
    )
    product_id = product.id

    db.session.commit()

    response = client.post(
        f"/api/products/{product_id}/archive"
    )

    assert response.status_code == 200
    assert response.json["ok"] is True
    assert response.json["item"]["id"] == product_id
    assert response.json["item"]["is_active"] is False

    db.session.expire_all()

    persisted = db.session.get(Product, product_id)

    assert persisted is not None
    assert persisted.is_active is False


def test_restore_product_restores_archived_product(client):
    product = add_product(
        "tenant-1",
        "RESTORE-001",
        "Restore Product",
        is_active=False,
    )
    product_id = product.id

    db.session.commit()

    response = client.post(
        f"/api/products/{product_id}/restore"
    )

    assert response.status_code == 200
    assert response.json["ok"] is True
    assert response.json["item"]["id"] == product_id
    assert response.json["item"]["tenant_id"] == "tenant-1"
    assert response.json["item"]["is_active"] is True

    db.session.expire_all()

    persisted = db.session.get(Product, product_id)

    assert persisted is not None
    assert persisted.is_active is True


def test_restore_product_is_idempotent(client):
    product = add_product(
        "tenant-1",
        "RESTORE-002",
        "Already Active Product",
        is_active=True,
    )
    product_id = product.id

    db.session.commit()

    response = client.post(
        f"/api/products/{product_id}/restore"
    )

    assert response.status_code == 200
    assert response.json["ok"] is True
    assert response.json["item"]["id"] == product_id
    assert response.json["item"]["is_active"] is True

    db.session.expire_all()

    persisted = db.session.get(Product, product_id)

    assert persisted is not None
    assert persisted.is_active is True


def test_archive_product_cannot_cross_tenant_boundary(client):
    product = add_product(
        "tenant-2",
        "OTHER-ARCHIVE-001",
        "Other Tenant Product",
    )
    product_id = product.id

    db.session.commit()

    response = client.post(
        f"/api/products/{product_id}/archive"
    )

    assert response.status_code == 404

    db.session.expire_all()

    persisted = db.session.get(Product, product_id)

    assert persisted is not None
    assert persisted.tenant_id == "tenant-2"
    assert persisted.is_active is True


def test_restore_product_cannot_cross_tenant_boundary(client):
    product = add_product(
        "tenant-2",
        "OTHER-RESTORE-001",
        "Other Tenant Archived Product",
        is_active=False,
    )
    product_id = product.id

    db.session.commit()

    response = client.post(
        f"/api/products/{product_id}/restore"
    )

    assert response.status_code == 404

    db.session.expire_all()

    persisted = db.session.get(Product, product_id)

    assert persisted is not None
    assert persisted.tenant_id == "tenant-2"
    assert persisted.is_active is False


def test_product_lifecycle_preserves_product_unit_state(client):
    unit = UnitOfMeasure(
        id="lifecycle-unit-box",
        tenant_id="tenant-1",
        code="LBOX",
        name="Lifecycle Box",
    )

    product = add_product(
        "tenant-1",
        "LIFECYCLE-UNIT-001",
        "Lifecycle Unit Product",
    )
    product_id = product.id

    product_unit = ProductUnit(
        id="lifecycle-product-unit",
        tenant_id="tenant-1",
        product_id=product_id,
        unit_id="lifecycle-unit-box",
        conversion_factor_to_base=Decimal("10.000000"),
        is_base=False,
        can_sell=True,
        can_receive=True,
        sale_price=Decimal("100.00"),
        minimum_sale_price=Decimal("90.00"),
        is_active=True,
    )

    db.session.add_all([unit, product_unit])
    db.session.commit()

    archive_response = client.post(
        f"/api/products/{product_id}/archive"
    )

    assert archive_response.status_code == 200

    db.session.expire_all()

    persisted_unit = db.session.get(
        ProductUnit,
        "lifecycle-product-unit",
    )

    assert persisted_unit is not None
    assert persisted_unit.is_active is True

    restore_response = client.post(
        f"/api/products/{product_id}/restore"
    )

    assert restore_response.status_code == 200

    db.session.expire_all()

    persisted_unit = db.session.get(
        ProductUnit,
        "lifecycle-product-unit",
    )

    assert persisted_unit is not None
    assert persisted_unit.is_active is True


# ============================================================================
# Product lifecycle authorization contract
# ============================================================================


@pytest.mark.parametrize(
    "action",
    [
        "archive",
        "restore",
    ],
)
def test_product_lifecycle_requires_authentication(
    app_context,
    monkeypatch: pytest.MonkeyPatch,
    action: str,
):
    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.get_current_identity",
        lambda: None,
    )

    monkeypatch.setattr(
        "app.auth.jwt.get_current_identity",
        lambda: None,
    )

    response = app_context.test_client().post(
        f"/api/products/product-1/{action}"
    )

    assert response.status_code == 401
    assert response.json["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.parametrize(
    "action",
    [
        "archive",
        "restore",
    ],
)
def test_product_lifecycle_requires_products_edit_permission(
    app_context,
    monkeypatch: pytest.MonkeyPatch,
    action: str,
):
    identity = SimpleNamespace(
        user_id="user-1",
        tenant_id="tenant-1",
        branch_id="branch-1",
    )

    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.get_current_identity",
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
        "app.services.tenant.auth.decorators.authorization_service.authorize",
        lambda *args, **kwargs: (
            _ for _ in ()
        ).throw(
            PermissionDeniedError(
                "Permission denied."
            )
        ),
    )

    response = app_context.test_client().post(
        f"/api/products/product-1/{action}"
    )

    assert response.status_code == 403
    assert (
        response.json["error"]["code"]
        == "AUTHORIZATION_DENIED"
    )


def test_new_product_always_starts_active(client):
    response = client.post(
        "/api/products",
        json={
            "internal_sku": "LIFECYCLE-CREATE-001",
            "name": "Lifecycle Creation Product",
            "is_active": False,
        },
    )

    assert response.status_code == 201
    assert response.json["ok"] is True
    assert response.json["item"]["is_active"] is True

    product_id = response.json["item"]["id"]

    persisted = db.session.get(
        Product,
        product_id,
    )

    assert persisted is not None
    assert persisted.is_active is True


# ============================================================================
# Product update contract
# ============================================================================


def test_update_product_changes_approved_fields(client):
    product = add_product(
        "tenant-1",
        "EDIT-API-001",
        "Old Product Name",
        supplier_sku="OLD-SUPPLIER",
    )
    product_id = product.id

    db.session.commit()

    response = client.patch(
        f"/api/products/{product_id}",
        json={
            "name": "Updated Product Name",
            "supplier_sku": "SUPPLIER-002",
            "generic_name": "Updated Generic",
            "default_sale_price": "125.50",
            "cost_price": "80.25",
            "reorder_level": "4",
            "reorder_qty": "12",
            "requires_prescription": True,
            "allow_negative_stock": True,
            "manufacturer": "Example Manufacturer",
        },
    )

    assert response.status_code == 200
    assert response.json["ok"] is True

    item = response.json["item"]

    assert item["id"] == product_id
    assert item["name"] == "Updated Product Name"
    assert item["supplier_sku"] == "SUPPLIER-002"
    assert item["generic_name"] == "Updated Generic"
    assert item["default_sale_price"] == "125.50"
    assert item["cost_price"] == "80.25"
    assert item["requires_prescription"] is True
    assert item["allow_negative_stock"] is True
    assert item["manufacturer"] == "Example Manufacturer"
    assert item["is_active"] is True


def test_update_product_accepts_same_tenant_category_brand_and_tax(client):
    category = ProductCategory(
        id="category-edit-1",
        tenant_id="tenant-1",
        name="Medicines",
        is_active=True,
    )

    brand = Brand(
        id="brand-edit-1",
        tenant_id="tenant-1",
        name="Example Brand",
        is_active=True,
    )

    tax_code = TaxCode(
        id="tax-edit-1",
        tenant_id="tenant-1",
        code="VAT16",
        name="VAT 16%",
        rate=Decimal("16.0000"),
        is_active=True,
    )

    product = add_product(
        "tenant-1",
        "EDIT-API-002",
        "Reference Product",
    )
    product_id = product.id

    db.session.add_all([
        category,
        brand,
        tax_code,
    ])
    db.session.commit()

    response = client.patch(
        f"/api/products/{product_id}",
        json={
            "category_id": category.id,
            "brand_id": brand.id,
            "tax_code": tax_code.code,
        },
    )

    assert response.status_code == 200
    assert response.json["ok"] is True

    item = response.json["item"]

    assert item["category"]["id"] == category.id
    assert item["brand"]["id"] == brand.id
    assert item["tax_code"] == "VAT16"


@pytest.mark.parametrize(
    "field,payload",
    [
        (
            "category_id",
            {
                "category_id": "category-other-tenant",
            },
        ),
        (
            "brand_id",
            {
                "brand_id": "brand-other-tenant",
            },
        ),
        (
            "tax_code",
            {
                "tax_code": "OTHER-VAT",
            },
        ),
    ],
)
def test_update_product_rejects_other_tenant_references(
    client,
    field,
    payload,
):
    db.session.add_all(
        [
            ProductCategory(
                id="category-other-tenant",
                tenant_id="tenant-2",
                name="Other Category",
                is_active=True,
            ),
            Brand(
                id="brand-other-tenant",
                tenant_id="tenant-2",
                name="Other Brand",
                is_active=True,
            ),
            TaxCode(
                id="tax-other-tenant",
                tenant_id="tenant-2",
                code="OTHER-VAT",
                name="Other VAT",
                rate=Decimal("10.0000"),
                is_active=True,
            ),
        ]
    )

    product = add_product(
        "tenant-1",
        f"EDIT-OTHER-{field}",
        "Tenant One Product",
    )

    db.session.commit()

    response = client.patch(
        f"/api/products/{product.id}",
        json=payload,
    )

    assert response.status_code == 400
    assert response.json["ok"] is False


@pytest.mark.parametrize(
    "payload",
    [
        {"internal_sku": "CHANGED-SKU"},
        {"product_type": "service"},
        {"track_inventory": False},
        {"track_batches": True},
        {"track_expiry": True},
        {"unit_id": "another-unit"},
        {"codes": []},
        {"is_active": False},
    ],
)
def test_update_product_rejects_structural_and_lifecycle_fields(
    client,
    payload,
):
    product = add_product(
        "tenant-1",
        "EDIT-PROTECTED-001",
        "Protected Product",
    )

    db.session.commit()

    response = client.patch(
        f"/api/products/{product.id}",
        json=payload,
    )

    assert response.status_code == 400
    assert response.json["ok"] is False


def test_update_product_cannot_cross_tenant_boundary(client):
    product = add_product(
        "tenant-2",
        "EDIT-OTHER-TENANT-001",
        "Other Tenant Product",
    )
    product_id = product.id

    db.session.commit()

    response = client.patch(
        f"/api/products/{product_id}",
        json={
            "name": "Illegal Change",
        },
    )

    assert response.status_code == 404

    db.session.expire_all()

    persisted = db.session.get(
        Product,
        product_id,
    )

    assert persisted is not None
    assert persisted.name == "Other Tenant Product"


def test_update_product_requires_authentication(
    app_context,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.get_current_identity",
        lambda: None,
    )

    monkeypatch.setattr(
        "app.auth.jwt.get_current_identity",
        lambda: None,
    )

    response = app_context.test_client().patch(
        "/api/products/product-1",
        json={
            "name": "Updated",
        },
    )

    assert response.status_code == 401


def test_update_product_requires_products_edit_permission(
    app_context,
    monkeypatch: pytest.MonkeyPatch,
):
    identity = SimpleNamespace(
        user_id="user-1",
        tenant_id="tenant-1",
        branch_id="branch-1",
    )

    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.get_current_identity",
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
        "app.services.tenant.auth.decorators.authorization_service.authorize",
        lambda *args, **kwargs: (
            _ for _ in ()
        ).throw(
            PermissionDeniedError(
                "Permission denied."
            )
        ),
    )

    response = app_context.test_client().patch(
        "/api/products/product-1",
        json={
            "name": "Updated",
        },
    )

    assert response.status_code == 403
    assert (
        response.json["error"]["code"]
        == "AUTHORIZATION_DENIED"
    )


# ============================================================================
# Product permanent deletion contract
# ============================================================================


def test_delete_product_permanently_deletes_archived_unused_product(client):
    product = add_product(
        "tenant-1",
        "DELETE-API-001",
        "Delete API Product",
        is_active=False,
    )
    product_id = product.id

    db.session.commit()

    response = client.delete(
        f"/api/products/{product_id}"
    )

    assert response.status_code == 200
    assert response.json == {
        "ok": True,
        "message": "Product permanently deleted.",
        "id": product_id,
    }

    db.session.expire_all()

    assert db.session.get(Product, product_id) is None


def test_delete_product_requires_archive_first(client):
    product = add_product(
        "tenant-1",
        "DELETE-ACTIVE-001",
        "Active Delete Product",
        is_active=True,
    )
    product_id = product.id

    db.session.commit()

    response = client.delete(
        f"/api/products/{product_id}"
    )

    assert response.status_code == 409
    assert response.json["ok"] is False
    assert response.json["code"] == "PRODUCT_DELETION_BLOCKED"
    assert response.json["blockers"] == []

    db.session.expire_all()

    persisted = db.session.get(Product, product_id)

    assert persisted is not None
    assert persisted.is_active is True


def test_delete_product_cannot_cross_tenant_boundary(client):
    product = add_product(
        "tenant-2",
        "DELETE-OTHER-001",
        "Other Tenant Delete Product",
        is_active=False,
    )
    product_id = product.id

    db.session.commit()

    response = client.delete(
        f"/api/products/{product_id}"
    )

    assert response.status_code == 404

    db.session.expire_all()

    persisted = db.session.get(Product, product_id)

    assert persisted is not None
    assert persisted.tenant_id == "tenant-2"


def test_delete_product_requires_products_delete_permission(
    app_context,
    monkeypatch: pytest.MonkeyPatch,
):
    identity = SimpleNamespace(
        user_id="user-1",
        tenant_id="tenant-1",
        branch_id="branch-1",
    )

    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.get_current_identity",
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

    captured = {}

    def deny_delete(*args, **kwargs):
        captured.update(kwargs)

        raise PermissionDeniedError(
            "Permission denied."
        )

    monkeypatch.setattr(
        "app.services.tenant.auth.decorators.authorization_service.authorize",
        deny_delete,
    )

    response = app_context.test_client().delete(
        "/api/products/product-1"
    )

    assert response.status_code == 403
    assert (
        response.json["error"]["code"]
        == "AUTHORIZATION_DENIED"
    )
    assert captured.get("permission") == "products.delete"
