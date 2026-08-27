# Migration 016 - Goods Receipt Type Ownership

## 1. Migration Purpose

Migration 016 determines whether Hela360 has a verified backend Goods Receipt business contract and whether canonical frontend Goods Receipt types can be safely created.

This migration is inspection-only. No canonical Goods Receipt frontend types were created because backend evidence is insufficient.

## 2. ADR Rules Applied

- ADR-001: services expose business operations and should not leak speculative backend assumptions.
- ADR-004: reusable business entities and DTOs belong under `src/types`, but only when a stable contract exists.
- ADR-008: module boundaries require public contracts to reflect real ownership.
- ADR-009: Goods Receipt names should be explicit and business-oriented, but naming does not justify inventing unsupported contracts.

## 3. Backend Files Searched

Searched and inspected:

- `app/models/`
- `app/api/`
- `app/schemas/`
- `app/serializers/`
- `app/services/tenant/procurement/`
- `app/services/tenant/inventory/`
- `app/services/tenant/pos/`
- `migrations/`
- `app/services/tenant/procurement/tests/`

Search terms included:

- `GoodsReceipt`
- `GoodsReceiptItem`
- `goods_receipt`
- `goods-receipt`
- `goods receipts`
- `GRN`
- `GRNItem`
- `receive_goods`
- `receive_stock`
- `stock_receipt`
- `PurchaseOrder`
- `PurchaseOrderItem`
- `procurement`
- `receiving`

## 4. Capability Classification

Goods Receipt support classification:

```text
Frontend-only assumption
```

No backend Goods Receipt model, table, migration, schema, serializer, route, service method, test, status contract, or inventory receipt workflow was verified.

## 5. Models Found

No Goods Receipt model was found.

Backend inventory models exist in `app/models/inventory.py`, but they are not Goods Receipt documents:

- `Warehouse`
- `InventoryBatch`
- `StockBalance`
- `InventoryMovement`

Backend procurement has Supplier support, but no Goods Receipt aggregate.

## 6. Migrations Found

No migration creates a Goods Receipt or Goods Receipt Item table.

`migrations/versions/19b1ccd035ac_initial_schema.py` creates inventory, product, sales, supplier-adjacent, and POS tables, but no Goods Receipt table.

`migrations/versions/8f3b7c2a9d10_add_suppliers.py` is Supplier-only.

## 7. Routes Found

No backend Goods Receipt route was found.

`app/api/inventory.py` is empty.

No route exists for:

- `GET /goods-receipts`
- `GET /goods-receipts/<id>`
- `POST /goods-receipts`
- `POST /purchase-orders/<id>/receive`
- `POST /goods-receipts/<id>/post`
- `POST /goods-receipts/<id>/reverse`
- Goods Receipt validation, print, batch, or summary endpoints

Frontend endpoint constants under `frontend/src/api/endpoints.ts` define `/goods-receipts`, but constants alone are not backend evidence.

## 8. Schemas Found

No Goods Receipt schema was found under `app/schemas/`.

Only Supplier schemas were present in the inspected schema area.

## 9. Serializers Found

No Goods Receipt serializer was found under `app/serializers/`.

Only Supplier serializers were present in the inspected serializer area.

## 10. Services Found

No backend Goods Receipt service was found.

`app/services/tenant/procurement/__init__.py` exports only:

- `SupplierService`
- `supplier_service`

`app/services/tenant/procurement/procurement_service.py` is empty.

`app/services/tenant/inventory/__init__.py` is empty.

POS services create inventory movements for sales/refunds, but they do not implement procurement receiving or Goods Receipt documents.

## 11. Tests Found

No Goods Receipt tests were found.

`app/services/tenant/procurement/tests/` contains Supplier contract tests only.

## 12. Purchase Order Relationship

No backend Purchase Order model, Purchase Order Item model, route, schema, serializer, or service contract was verified in this migration.

Frontend `purchaseOrderService.ts` defines purchase-order and receiving assumptions, but those are frontend-only.

## 13. Inventory Movement Relationship

Inventory movement persistence is verified through `app/models/inventory.py::InventoryMovement`.

Sales/POS workflows create inventory movement records for:

- `sale`
- `sale_void`
- `sale_refund_return`

No Goods Receipt workflow creates inventory movements.

## 14. Supplier Relationship

Supplier backend support exists from Migration 010.

No backend Goods Receipt relationship to Supplier was verified.

## 15. Branch And Warehouse Relationship

Inventory and POS models include branch and warehouse ownership.

No Goods Receipt branch or warehouse relationship was verified because no Goods Receipt model exists.

## 16. Authorization

No Goods Receipt permissions were verified in backend authorization.

Frontend route/service assumptions do not establish backend authorization.

## 17. Status And Lifecycle

No backend Goods Receipt status values were verified.

Frontend service-local values are speculative:

```text
DRAFT
POSTED
CANCELLED
```

## 18. Accounting And Payable Side Effects

No backend accounting, payable, supplier invoice, or finance side effect for Goods Receipt was verified.

## 19. Frontend Assumptions Found

Frontend service-local contracts in `frontend/src/services/procurement/goodsReceiptService.ts`:

- `GoodsReceiptStatus`
- `GoodsReceiptItem`
- `GoodsReceipt`
- `CreateGoodsReceiptRequest`
- `ReverseReceiptRequest`
- `ReceiptSummary`

Frontend service methods assume endpoints for:

- purchase order lookup
- posting
- reversing
- summary
- batches
- printing
- validation

Frontend hooks assume:

- `goodsReceiptService.getGoodsReceipt`
- `goodsReceiptService.listGoodsReceipts`
- `purchaseOrderService.receive`

Those methods do not exist on the current frontend services and no backend endpoints were verified.

## 20. Canonical Goods Receipt Disposition

`GoodsReceipt` was not created under `frontend/src/types/entities/`.

Reason:

- no backend model
- no backend serializer
- no backend route
- no backend service
- no stable response shape

## 21. GoodsReceiptItem Disposition

`GoodsReceiptItem` was not created.

Reason:

- no line-item table
- no line-item serializer
- no line-item request schema
- no verified purchase-order receiving workflow

## 22. CreateGoodsReceiptRequest Disposition

`CreateGoodsReceiptRequest` was not created.

Reason:

- no create Goods Receipt route
- no create schema
- no verified client-owned payload

## 23. ReceiveGoodsRequest Disposition

`ReceiveGoodsRequest` was not created.

Reason:

- no purchase-order receive route
- no goods-receipt receive service
- no inventory stock-receipt workflow
- no verified request fields

`ReceiveStockRequest` remains an Inventory workflow assumption and was not touched.

## 24. GoodsReceiptStatus Disposition

`GoodsReceiptStatus` was not created.

Reason:

- no backend lifecycle/status field
- no finite backend status value set
- no runtime status constants required by verified code

## 25. Product, Inventory, And Procurement Boundary

Product owns product identity and configuration.

Inventory owns stock balances and movement ledger records.

Procurement would own Purchase Orders and Goods Receipts once backend contracts exist.

Goods Receipt may eventually cause Inventory Movements, but it must not redefine `InventoryMovement`.

## 26. Files Created

- `frontend/docs/architecture/reviews/MIGRATION-016-GOODS-RECEIPT-TYPE-OWNERSHIP.md`

## 27. Files Modified

No source files were modified.

Only this inspection report was created.

## 28. Barrels Updated

No barrels were updated.

No unsupported type exports were removed during this migration because source implementation was stopped by missing backend evidence.

## 29. Compiler Errors Before

Baseline:

```text
199 TypeScript errors
```

## 30. Compiler Errors After

Post-migration:

```text
199 TypeScript errors
```

This migration intentionally performs no source type changes.

## 31. Net Reduction

```text
0 TypeScript errors
```

## 32. Procurement Diagnostics Before And After

No Procurement diagnostics were changed.

Remaining Goods Receipt-related diagnostics include missing `GoodsReceipt` exports and missing service methods such as:

- `goodsReceiptService.getGoodsReceipt`
- `goodsReceiptService.listGoodsReceipts`
- `purchaseOrderService.receive`

## 33. Newly Exposed Diagnostics

No diagnostics were newly exposed.

## 34. Remaining Procurement Blockers

- No backend Goods Receipt model.
- No backend Goods Receipt item model.
- No Goods Receipt database tables.
- No Goods Receipt serializer.
- No create/receive request schema.
- No Goods Receipt routes.
- No Goods Receipt service.
- No purchase-order receiving backend workflow.
- No inventory receipt workflow.
- No verified status lifecycle.
- Frontend procurement services and hooks are speculative.
- Purchase Order type ownership remains unresolved.
- Purchase Requisition type ownership remains unresolved.
- Query-key and response-envelope mismatches remain out of scope.

## 35. Invariants Verified

- No Goods Receipt type was created without backend evidence.
- Procurement remains the deferred owner for future Goods Receipt contracts.
- Inventory remains owner of stock balance and movement entities.
- Product remains owner of Product contracts.
- Purchase Order and Goods Receipt remain distinct.
- No request DTO was created without a verified outbound payload.
- No response projection was created without backend support.
- No status type was created without backend-supported values.
- No service method changed.
- No query key changed.
- No invalidation changed.
- No backend file changed.
- Runtime behavior remains unchanged.

## 36. Rollback Boundary

Rollback is limited to deleting this inspection report.

## 37. Backend Work Required

Before frontend Goods Receipt type ownership can proceed, backend work must define:

- Goods Receipt and Goods Receipt Item persistence models
- database migrations
- create/receive request schemas
- serializers
- routes
- procurement service workflow
- purchase-order linkage
- inventory movement side effects
- lifecycle/status values
- permissions
- tests

## 38. Recommended Next Migration

Recommended next migration:

```text
Migration 017 - Purchase Order Type Ownership Inspection
```
