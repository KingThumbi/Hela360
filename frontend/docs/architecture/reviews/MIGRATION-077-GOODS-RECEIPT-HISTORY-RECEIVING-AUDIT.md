# Migration 077 - Goods Receipt History / Receiving Audit

Date: 2026-08-09

Status: Complete

## 1. Migration Purpose

Migration 077 adds read-only receiving audit functionality for persisted Goods Receipts.

Store and pharmacy staff with receiving permission can now answer what was received, when, into which Warehouse, from which Supplier, by whom, under which supplier reference, and which receipt detail should be opened for audit.

## 2. ADR Rules

- ADR-001: Goods Receipt aggregate read behavior remains behind `GoodsReceiptService`.
- ADR-002: frontend pages consume query hooks only.
- ADR-003: query keys and invalidation remain centralized.
- ADR-004: list projection uses a dedicated `GoodsReceiptSummary`.
- ADR-005: malformed filters use normalized error responses.
- ADR-006: tenant and branch are server-derived.
- ADR-007: history uses explicit receiving authorization.
- ADR-008: Inventory owns receiving; Procurement remains closed.
- ADR-009: names use Goods Receipt and Receiving History language.

## 3. Baseline

Baseline before implementation:

```text
venv/bin/python -m compileall app: PASS
cd frontend && npx tsc -b --pretty false: PASS
cd frontend && npm run build: PASS
```

Known warning:

```text
Some chunks are larger than 500 kB after minification.
```

## 4. GoodsReceipt Model

`GoodsReceipt` fields:

- `id`
- `tenant_id`
- `branch_id`
- `warehouse_id`
- `supplier_id`
- `receipt_number`
- `supplier_reference`
- `idempotency_key`
- `request_fingerprint`
- `received_at`
- `status`
- `notes`
- `received_by`
- `created_at`
- `updated_at`

`GoodsReceiptItem` fields:

- `id`
- `goods_receipt_id`
- `product_id`
- `batch_id`
- `line_number`
- `quantity`
- `batch_number`
- `manufacture_date`
- `expiry_date`
- `unit_cost`
- `supplier_batch_reference`
- `created_at`
- `updated_at`

## 5. Existing Detail Disposition

Existing detail endpoint:

```text
GET /api/inventory/goods-receipts/<receipt_id>
```

It remains protected by:

```text
inventory.receive
```

Detail remains the canonical full receiving document surface and includes item lines and unit costs.

## 6. Permission Decision

History uses:

```text
inventory.receive
```

Reason: history exposes cost-bearing receiving documents through `total_cost`, and detail already uses `inventory.receive`.

No broader `inventory.read` projection was introduced.

## 7. List Endpoint

Added:

```text
GET /api/inventory/goods-receipts
```

Properties:

- authenticated
- protected by `inventory.receive`
- tenant server-derived
- branch mandatory
- branch-scoped
- paginated
- filtered server-side
- summary-only
- read-only

## 8. Query Service Ownership

Owner:

```text
app/services/tenant/inventory/goods_receipt_service.py
```

`GoodsReceiptService` now owns create, detail, and list for the Goods Receipt aggregate.

No third service and no Procurement service were created.

## 9. Pagination

Supported parameters:

- `page`
- `per_page`

Both must be positive integers.

Response envelope:

```text
{ ok: true, items: GoodsReceiptSummary[], pagination: {...} }
```

## 10. Ordering

Default ordering:

```text
received_at DESC, id DESC
```

No arbitrary sort fields were added.

## 11. Search

Server search supports:

- `receipt_number`
- `supplier_reference`
- `Supplier.name`
- `Supplier.supplier_code`

Product item search was not added to keep the list query narrow.

## 12. Date Filters

Supported filters:

- `date_from`
- `date_to`

Dates are `YYYY-MM-DD`.

Semantics are inclusive across the full received day.

Malformed dates and reversed ranges return `400`.

## 13. Warehouse Filter

Supported:

```text
warehouse_id
```

The Warehouse must belong to the authenticated tenant and current branch and be active.

## 14. Supplier Filter

Supported:

```text
supplier_id
```

The Supplier must belong to the authenticated tenant.

Branch scoping remains on `GoodsReceipt`.

## 15. Status Filter Disposition

No status filter was added.

Migration 075 defined only one effective lifecycle state:

```text
received
```

## 16. Receiver Filter Disposition

No `received_by` filter was added.

Receiver appears in row projection, but staff filtering is deferred until a verified operational requirement exists.

## 17. Summary Projection

History rows return:

- `id`
- `receipt_number`
- `received_at`
- `status`
- `warehouse`
- nullable `supplier`
- `supplier_reference`
- `item_count`
- `total_cost`
- nullable `received_by`
- timestamps

They do not return full receipt items.

## 18. Supplier Null Behavior

Receipts without Supplier return:

```text
supplier: null
```

The frontend renders this as:

```text
No supplier
```

No fake Supplier entity is invented.

## 19. Item Count

`item_count` is derived server-side from persisted `GoodsReceiptItem` rows.

The frontend does not count detail items for list rows.

## 20. Total Quantity Disposition

No aggregate total quantity was exposed.

Reason: receipt lines may represent different Products and unit semantics.

## 21. Total Cost / Cost Authorization

`total_cost` is included because the endpoint is protected by `inventory.receive`.

It is calculated server-side from persisted:

```text
sum(quantity * unit_cost)
```

The frontend only formats the value for display.

It is not labeled as invoice total, amount payable, or supplier balance.

## 22. Receipt Reference

History uses the existing canonical `receipt_number`.

No document numbering redesign was introduced.

## 23. Notes And Idempotency Visibility

History rows omit:

- `notes`
- `idempotency_key`
- `request_fingerprint`

Detail remains the place for operational notes.

## 24. Backend Tests

Added Goods Receipt history coverage for:

- permission enforcement
- tenant and branch isolation
- summary projection
- null Supplier semantics
- pagination
- newest-first ordering
- stable secondary ordering
- search
- inclusive date filters
- filter validation
- Warehouse filter
- Supplier tenant safety

## 25. Frontend GoodsReceiptSummary

Added:

```text
frontend/src/types/responses/goods-receipt-summary.ts
```

This keeps the list projection distinct from full `GoodsReceipt`.

## 26. ListGoodsReceiptsRequest

Added:

```text
frontend/src/types/requests/list-goods-receipts-request.ts
```

Fields:

- `page`
- `per_page`
- `search`
- `date_from`
- `date_to`
- `warehouse_id`
- `supplier_id`

## 27. Service Method

Added:

```text
inventoryService.listGoodsReceipts(params)
```

Return type:

```text
PaginatedResponse<GoodsReceiptSummary>
```

## 28. Query Keys

Added branch-scoped list keys:

```text
tenant -> branch -> inventory -> goods-receipts -> list -> normalizedParams
```

Existing detail keys remain:

```text
tenant -> branch -> inventory -> goods-receipts -> detail -> receiptId
```

## 29. Hook

Added:

```text
useGoodsReceipts(params)
```

It uses branch scope, readiness checks, canonical service access, and canonical query keys.

## 30. Public Hook Boundary

Inventory public hook boundary now includes:

- `useCreateGoodsReceipt`
- `useGoodsReceipt`
- `useGoodsReceipts`
- `useInventory`
- `useInventoryBatches`
- `useInventoryMovements`

Unsupported adjustment, stock-count, and transfer hooks remain closed.

## 31. Mutation Invalidation

No page-level invalidation was added.

Existing `useCreateGoodsReceipt` calls:

```text
invalidateInventoryOperations(queryClient, branchScope)
```

Because receipt list keys live under the branch inventory root, create-receipt invalidation now covers Goods Receipt history.

## 32. Route

Added:

```text
/inventory/receipts
```

Existing routes remain:

```text
/inventory/receive
/inventory/receipts/:receiptId
```

No `/procurement/receipts` route was created.

## 33. Route Permission

Route permission:

```text
/inventory/receipts -> inventory.receive
```

Detail and receive routes also remain under `inventory.receive`.

## 34. Inventory Integration

The Inventory page now shows:

- Receive Stock
- Receiving History

Both are permission-gated by `inventory.receive`.

## 35. History Page

Created:

```text
frontend/src/features/inventory/pages/GoodsReceiptHistoryPage.tsx
```

Features:

- search
- received date range
- Warehouse filter
- Supplier search and filter
- pagination
- refresh
- loading state
- error state
- empty states

## 36. Table

Columns:

- Receipt
- Received
- Warehouse
- Supplier
- Supplier Ref
- Items
- Value
- Received By
- Status
- Action

Rows provide only a `View Receipt` action.

## 37. Filters

Filters are server-backed.

Supplier selection uses canonical `useSuppliers()` with search.

Warehouse selection uses canonical `useWarehouses()`.

## 38. Detail Navigation

Every history row links to:

```text
/inventory/receipts/:receiptId
```

The detail page now has a Receiving History back-link.

The Receive Stock page also links to Receiving History.

## 39. Activity Navigation

Inventory Activity now recognizes:

```text
reference.type === "goods_receipt"
```

It links to the Goods Receipt detail only when the user has `inventory.receive`.

Otherwise the neutral reference text remains.

## 40. Procurement Boundary

Procurement remains closed.

Static checks found no Procurement, Purchase Order, or Accounts Payable coupling in `frontend/src/features/inventory` or `app/api/inventory.py`.

The old private Procurement Goods Receipt hook files still exist but remain outside the public Inventory receiving path.

## 41. AP Boundary

No invoice status, payment due, credit terms, supplier balance, supplier invoice, or payable behavior was introduced.

## 42. Schema Disposition

No schema migration was required.

Alembic source head remains:

```text
c3d4e5f6a7b8
```

## 43. Local DB State

Local PostgreSQL during final verification:

```text
pg_lsclusters: 16/main 5432 down
pg_isready -h localhost -p 5432: no response
```

Alembic source heads:

```text
FLASK_APP=app:create_app venv/bin/flask db heads: c3d4e5f6a7b8 (head)
```

`flask db current` could not connect because PostgreSQL was down.

## 44. Runtime Smoke

Live browser/API smoke against local PostgreSQL was not run because the local database cluster was down.

Isolated contract tests and frontend compile/build verification were used.

## 45. Backend Compile

```text
venv/bin/python -m compileall app: PASS
```

`flask routes` also passed and showed:

```text
inventory.list_goods_receipts GET /api/inventory/goods-receipts
```

## 46. Regression Totals

Goods Receipt plus adjacent Inventory:

```text
64 passed, 4 warnings
```

Auth suite:

```text
129 passed
```

Targeted API/procurement regression bundle:

```text
192 passed, 4 warnings
```

## 47. Frontend TypeScript

```text
cd frontend && npx tsc -b --pretty false: PASS
```

## 48. Frontend Build

```text
cd frontend && npm run build: PASS
```

## 49. Warnings

Known Vite warning remains:

```text
Some chunks are larger than 500 kB after minification.
```

Known SQLAlchemy relationship overlap warnings remain:

- `RolePermission.role`
- `RolePermission.permission`
- `UserRole.user`
- `UserRole.role`

## 50. Files Inspected

Inspected ADR-001 through ADR-009, Migrations 039, 073, 074, 075, and 076, Goods Receipt models, serializer, API routes, service, tests, Inventory page, query keys, invalidation, service facade, existing Goods Receipt frontend types, and route/permission registries.

## 51. Files Created

- `frontend/src/features/inventory/pages/GoodsReceiptHistoryPage.tsx`
- `frontend/src/hooks/queries/inventory/useGoodsReceipts.ts`
- `frontend/src/types/requests/list-goods-receipts-request.ts`
- `frontend/src/types/responses/goods-receipt-summary.ts`
- `frontend/docs/architecture/reviews/MIGRATION-077-GOODS-RECEIPT-HISTORY-RECEIVING-AUDIT.md`

## 52. Files Modified

- `app/api/inventory.py`
- `app/api/tests/test_goods_receipt_contract.py`
- `app/serializers/goods_receipt.py`
- `app/services/tenant/inventory/__init__.py`
- `app/services/tenant/inventory/goods_receipt_service.py`
- `frontend/src/app/router.tsx`
- `frontend/src/features/inventory/index.ts`
- `frontend/src/features/inventory/pages/GoodsReceiptDetailPage.tsx`
- `frontend/src/features/inventory/pages/InventoryPage.tsx`
- `frontend/src/features/inventory/pages/ReceiveStockPage.tsx`
- `frontend/src/hooks/queries/inventory/index.ts`
- `frontend/src/lib/queryKeys.ts`
- `frontend/src/routes/permissions.ts`
- `frontend/src/routes/routes.ts`
- `frontend/src/services/inventory/inventoryService.ts`
- `frontend/src/types/requests/index.ts`
- `frontend/src/types/responses/index.ts`

## 53. Remaining Receiving Blockers

Still deferred:

- receipt edit
- cancel
- reversal
- return to supplier
- Purchase Orders
- Procurement activation
- AP/invoices
- receiving approval workflow
- PDF/export
- document numbering redesign

## 54. Invariants Verified

- Goods Receipt history is read-only.
- Tenant is server-derived.
- Branch is mandatory.
- Cross-tenant receipts are excluded.
- Cross-branch receipts are excluded.
- Warehouse filter is branch-validated.
- Supplier filter is tenant-safe.
- Summary projection is server-derived.
- Cost visibility remains under `inventory.receive`.
- Detail remains the full receipt view.
- Activity links Goods Receipt references only for receiving-authorized users.
- No row mutations were added.
- Procurement remains closed.
- AP remains unsupported.
- Create receipt invalidates history through branch inventory root keys.
- TypeScript remains clean.
- Production build remains successful.

## 55. Rollback Boundary

Rollback removes the list endpoint/service/tests, summary serializer, frontend summary/request types, list service method, list query keys/hook, `/inventory/receipts` page/route/permission entry, Inventory page history link, Activity Goods Receipt reference link, and receive/detail history back-links.

No database rollback is needed.

## 56. Recommended Next Migration

Recommended next migration:

```text
Migration 078 - Inventory Adjustment Backend Contract
```

This should remain Inventory-owned and should not activate Procurement or AP.
