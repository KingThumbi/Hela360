# Migration 083 - Pharmacy Inventory Backend/API Layer Hardening

## 1. Scope

Migration 083 hardens the backend/API foundation for pharmacy pack and unit inventory handling.

It does not activate pack/unit UI controls.

## 2. Migration State Classification

Up to date at repository head `f6a7b8c9d0e1`.

## 3. Alembic State

`flask db heads` reports:

```text
f6a7b8c9d0e1 (head)
```

`flask db check` is supported but could not complete because local PostgreSQL on `localhost:5432` is unavailable in this session.

## 4. Local Database State

`pg_isready -h localhost -p 5432` reports no response.

No database upgrade was executed during Migration 083.

## 5. Base-Unit Decision

`StockBalance`, `InventoryBatch`, and `InventoryMovement` remain canonical base-quantity tables.

Product-specific pack conversion is owned by `ProductUnit`, not global `UnitOfMeasure.base_factor`.

## 6. Product Unit Model

Added `ProductUnit` as a tenant/product/unit conversion catalogue:

- `conversion_factor_to_base`
- `is_base`
- `can_sell`
- `can_receive`
- optional `sale_price`
- optional `minimum_sale_price`
- `is_active`

## 7. Product.unit_id Compatibility

`Product.unit_id` remains the legacy/default base unit pointer.

Existing products without configured `ProductUnit` resolve as base factor `1.000000`.

## 8. Historical Snapshot Strategy

Historical rows are not guessed or rewritten into pack conversions.

Migration backfills existing sale, refund, and receipt base quantities with factor 1.

## 9. Receiving Conversion

Goods Receipt line `quantity` remains the entered unit quantity.

`base_quantity` is stored separately and is used for batch, stock balance, and inventory movement writes.

`base_unit_cost` is stored as entered `unit_cost / conversion_factor_to_base`.

## 10. POS/Sale Conversion

Sale line `quantity` remains the entered unit quantity.

`base_quantity` is used for stock allocation and sale inventory movements.

Line pricing remains based on the entered sale unit.

## 11. Pricing

`ProductUnit.sale_price` and `ProductUnit.minimum_sale_price` can override product default/minimum sale price for that product unit.

If no ProductUnit price is present, existing Product pricing remains authoritative.

## 12. Refund Behavior

Refund item `quantity` remains entered sale-unit quantity.

Refund item `base_quantity` is prorated from the original sale item base quantity, and stock restoration uses that base quantity.

## 13. ProductCode / Barcode Disposition

`ProductCode.product_unit_id` is nullable.

Existing product-level codes remain valid.

Future barcode flows can identify product plus sale unit without changing the product-code uniqueness boundary.

## 14. Stock Count Compatibility

Stock Count remains base-quantity based.

No count UI or pack-entry behavior was activated.

## 15. Stock Adjustment Compatibility

Stock Adjustment remains base-quantity based.

No adjustment UI or pack-entry behavior was activated.

## 16. API Surface

Added read endpoint:

```text
GET /api/products/<product_id>/units
```

Protected by `products.view`.

## 17. Frontend Surface

Added type/service foundation only:

- `ProductUnit` entity type
- `productService.listProductUnits`
- optional `product_unit_id` request fields for sale and goods receipt requests
- goods receipt conversion snapshot fields

No UI activation was performed.

## 18. Migration Revision

Created:

```text
migrations/versions/f6a7b8c9d0e1_add_product_units.py
```

The migration is additive and includes factor-1 compatibility backfill.

## 19. Files Changed

Backend:

- `app/models/product.py`
- `app/models/inventory.py`
- `app/models/pos.py`
- `app/models/__init__.py`
- `app/api/products.py`
- `app/api/sales.py`
- `app/schemas/goods_receipt.py`
- `app/serializers/goods_receipt.py`
- `app/services/tenant/inventory/goods_receipt_service.py`
- `app/services/tenant/inventory/product_unit_conversion_service.py`
- `app/services/tenant/pos/refund_service.py`

Frontend:

- `frontend/src/types/entities/product-unit.ts`
- `frontend/src/types/entities/product.ts`
- `frontend/src/types/entities/index.ts`
- `frontend/src/types/entities/goods-receipt.ts`
- `frontend/src/types/requests/create-sale-item-request.ts`
- `frontend/src/types/requests/create-goods-receipt-request.ts`
- `frontend/src/services/products/productService.ts`

Tests and migration docs were updated.

## 20. Verification

Compile:

```text
venv/bin/python -m compileall app
PASS
```

Targeted backend:

```text
PYTHONPATH=. venv/bin/pytest app/api/tests/test_products_list_contract.py app/api/tests/test_goods_receipt_contract.py app/api/tests/test_sales_pos_contract.py app/api/tests/test_sales_receipt_contract.py app/api/tests/test_prescription_dispensing_contract.py app/api/tests/test_till_shift_contract.py app/api/tests/test_inventory_read_contract.py app/api/tests/test_inventory_movement_read_contract.py app/api/tests/test_stock_count_contract.py app/api/tests/test_stock_adjustment_contract.py
188 passed, 4 warnings
```

Auth suite:

```text
PYTHONPATH=. venv/bin/pytest app/services/tenant/auth/tests
129 passed
```

Frontend:

```text
npx tsc -b --pretty false
PASS

npm run build
PASS with existing large chunk warning
```

## 21. Remaining Technical Debt

Known SQLAlchemy mapper overlap warnings remain unchanged and out of scope:

- `RolePermission.role`
- `RolePermission.permission`
- `UserRole.user`
- `UserRole.role`

Local PostgreSQL was unavailable, so the new Alembic revision still needs runtime upgrade verification against PostgreSQL.

## 22. Seed / Bootstrap Inspection

Inspected `flask seed-initial` in `app/__init__.py`.

It seeds:

- tenant
- branch
- admin role/user
- payment methods: cash, M-Pesa, card, bank

It does not seed:

- products
- product units
- pack conversions
- customers
- suppliers
- inventory
- receipts
- sales

No seed command was executed.

## 23. First-Tenant Seed Readiness

Based on the last verified local counts, foundational tenant/branch/user data exists.

Operational Product, Customer, Supplier, and Sales data remains empty.

Product-unit readiness is schema/API ready but requires explicit operational product-unit seed/configuration later.

## 24. Blockers

PostgreSQL is offline on `localhost:5432`; runtime `flask db check`, `flask db current`, and `flask db upgrade` could not be completed in this session.

## 25. Recommended Next

Run PostgreSQL upgrade verification for `f6a7b8c9d0e1`, then continue with a dedicated pack/unit configuration UI or POS unit-selection migration.

## 26. Required 56-Point Record

1. Migration purpose: establish deterministic pharmacy unit/base-quantity semantics for backend/API inventory.
2. Baseline: backend compile, frontend TypeScript, frontend build, targeted backend, and auth suite pass; PostgreSQL runtime unavailable.
3. UnitOfMeasure inventory: `tenant_id`, `code`, `name`, `base_factor`; tenant-owned unit vocabulary, insufficient for product-specific pack conversion.
4. Product unit fields before 083: `unit_id` and free-text `pack_size`; no purchase unit, sale unit, base unit, or conversion factor field.
5. ProductCode findings: `code_type`, `code_value`, product FK, tenant/code uniqueness, multiple codes per Product allowed; before 083 no unit-level code mapping.
6. Quantity semantics before: stock balance, batch, and movement quantities were product quantities with no conversion distinction.
7. Sale quantity semantics: `SaleItem.quantity = 1` meant one current/default Product sale quantity; no pack/unit identity was persisted.
8. Goods Receipt quantity semantics: `GoodsReceiptItem.quantity = 10` could not distinguish 10 boxes, 10 strips, or 10 tablets.
9. Stock Count semantics: snapshot, expected, counted, and variance quantities remain canonical inventory/base quantities.
10. Adjustment semantics: `StockAdjustmentItem.quantity_delta` remains a base inventory delta.
11. Refund semantics: refund quantities remain commercial sale quantities; stock restoration now uses prorated persisted base quantity.
12. Canonical base-unit decision: all inventory stock tables use one Product base quantity.
13. Product-specific conversion decision: conversions belong to ProductUnit, not global UnitOfMeasure.
14. ProductUnit entity decision: introduced `product_units` as the smallest correct aggregate for direct-to-base conversion.
15. Conversion factor: `conversion_factor_to_base` is Decimal `Numeric(18,6)` and must be greater than zero.
16. Fractional quantity disposition: existing Decimal architecture is preserved; no pharmacy-only integer assumption was added.
17. Selling unit: multiple sellable units are represented by `ProductUnit.can_sell`.
18. Receiving unit: receivable units are represented by `ProductUnit.can_receive`.
19. Price ownership: `ProductUnit.sale_price` can own selling-unit price; Product price remains compatibility fallback.
20. Minimum-price disposition: `ProductUnit.minimum_sale_price` can own unit-specific minimum; Product minimum remains fallback.
21. Goods Receipt conversion: server resolves ProductUnit, stores commercial quantity, and posts base quantity to inventory.
22. Commercial/base quantity persistence: sale and receipt lines preserve entered quantity/unit snapshots and base quantity.
23. Sale conversion: checkout accepts optional `product_unit_id`; stock allocation receives base quantity.
24. Transaction snapshots: sale/receipt lines persist `product_unit_id`, unit snapshots, factor, and base quantity.
25. Refund behavior: partial refunds prorate from original `SaleItem.base_quantity`; current ProductUnit factors are not reused.
26. Dispensing behavior: prescription dispensing remains linked to commercial SaleItem; no dosage conversion was introduced.
27. FEFO behavior: SaleStockService continues FEFO allocation using converted base quantity.
28. Batch quantity semantics: `InventoryBatch.quantity_on_hand` and `InventoryBatch.unit_cost` are base quantity/base-unit cost.
29. POS availability disposition: existing availability remains base quantity; selected-unit projection is deferred.
30. ProductCode/unit mapping: nullable `ProductCode.product_unit_id` supports future box/strip/tablet code mapping.
31. Stock Count disposition: count posting remains base quantity; unit-aware count UI is deferred.
32. Stock Adjustment disposition: adjustment posting remains base delta; unit-aware adjustment UI is deferred.
33. Receiving cost conversion: entered unit cost is converted to `base_unit_cost = unit_cost / factor`.
34. Average-cost behavior: weighted average uses base quantity and base-unit cost.
35. Product unit API: added `GET /api/products/<product_id>/units` under `products.view`.
36. Compatibility behavior: omitted ProductUnit resolves to configured base ProductUnit or legacy factor 1.
37. Existing Product migration strategy: existing products with `unit_id` get factor-1 base ProductUnit; no guessed pack factors.
38. Historical Sale compatibility: old sale lines are backfilled with factor 1/base quantity equal to quantity.
39. Historical Goods Receipt compatibility: old receipt lines are backfilled with factor 1/base quantity equal to quantity.
40. Frontend type/service foundation: added ProductUnit type, request fields, response fields, and product service read method.
41. UI disposition: no pack/unit management UI, POS unit selector, or receiving unit selector was activated.
42. Alembic revision: `f6a7b8c9d0e1_add_product_units.py`.
43. Migration safety: additive schema, nullable FKs, factor-1 compatibility, no destructive quantity rewrite.
44. Local DB state: PostgreSQL on `localhost:5432` is down; upgrade/check/current could not be verified.
45. Backend tests: targeted backend contracts passed.
46. Regression totals: `188 passed, 4 warnings`; auth suite `129 passed`.
47. Frontend TypeScript: `npx tsc -b --pretty false` passed with zero errors.
48. Frontend build: `npm run build` passed with the known large-chunk warning.
49. Warnings: only the four known SQLAlchemy relationship overlap warnings remain.
50. Files inspected: ADRs, migration docs, Product/UOM/ProductCode models, inventory/POS models, sales API, goods receipt service, refund services, stock count/adjustment paths, seed command.
51. Files created: ProductUnit conversion service, Alembic revision, ProductUnit frontend type, Migration 083 review.
52. Files modified: product/inventory/POS models, products/sales APIs, goods receipt schema/serializer/service, refund service, relevant tests, frontend request/entity/service types.
53. Remaining pharmacy inventory blockers: PostgreSQL upgrade verification, pack/unit CRUD/configuration workflow, POS/receiving/count/adjustment unit-aware UI, POS availability selected-unit projection, intact-pack policy.
54. Invariants verified: base inventory quantities, server-owned conversion, immutable transaction snapshots, no frontend conversion authority, no UI activation, TS/build pass.
55. Rollback boundary: the Alembic downgrade removes additive ProductUnit/snapshot columns and table; no user data was staged/committed.
56. Recommended next migration: PostgreSQL runtime upgrade verification for `f6a7b8c9d0e1`, then pack/unit configuration and selected-unit operational UI.
