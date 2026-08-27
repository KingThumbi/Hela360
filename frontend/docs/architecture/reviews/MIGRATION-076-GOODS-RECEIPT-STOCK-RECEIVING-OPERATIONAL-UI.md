# Migration 076 - Goods Receipt Stock Receiving Operational UI

Date: 2026-08-09

Status: Complete

## 1. Migration Purpose

Migration 076 activates the Goods Receipt stock receiving user interface on top of the Migration 075 backend contract.

The operational user can receive stock into a branch Warehouse, optionally attach a Supplier, add inventory-tracked Products, capture quantity, unit cost, batch, manufacture, and expiry fields as required by Product flags, submit with an idempotency key, and read back the persisted Goods Receipt confirmation.

## 2. Scope

Activated:

- `/inventory/receive`
- `/inventory/receipts/:receiptId`
- Inventory page action to open receiving
- canonical Goods Receipt create mutation
- canonical Goods Receipt detail query

Deferred:

- Purchase Orders
- Procurement UI
- Accounts payable or supplier invoice workflows
- corrections and reversals
- returns to supplier
- stock counts, adjustments, and transfers
- receipt history/list view beyond strict confirmation
- PDF documents
- valuation reports
- broad cost visibility outside receiving permissions

## 3. ADR Rules

- Query hooks remain the only component data access boundary.
- Components do not import services, query keys, query clients, or storage.
- Mutation invalidation remains centralized in the hook layer.
- Tenant and branch scope are derived from canonical application scope.
- Receiving uses `inventory.receive`.
- Inventory root visibility remains `inventory.read`.
- Procurement remains closed.

## 4. Baseline

Pre-implementation baseline was already verified clean:

```text
venv/bin/python -m compileall app: PASS
cd frontend && npx tsc -b --pretty false: PASS
cd frontend && npm run build: PASS
```

Known frontend warning:

```text
Some chunks are larger than 500 kB after minification.
```

## 5. Backend Contract Consumed

Migration 076 consumes the Migration 075 contract:

- `POST /api/inventory/goods-receipts`
- `GET /api/inventory/goods-receipts/<receipt_id>`
- `CreateGoodsReceiptRequest`
- `GoodsReceipt`
- `useCreateGoodsReceipt`
- `useGoodsReceipt`

No backend semantics were changed.

## 6. Route Activation

Routes:

- `/inventory/receive`
- `/inventory/receipts/:receiptId`

Route registry:

- `PATHS.INVENTORY.RECEIVE`
- `PATHS.INVENTORY.RECEIPT`
- `PATHS.INVENTORY.receipt(receiptId)`

## 7. Permissions

Protected routes:

- `/inventory/receive`: `inventory.receive`
- `/inventory/receipts/:receiptId`: `inventory.receive`

Unchanged route:

- `/inventory`: `inventory.read`

The Inventory page Receive Stock action is also permission-gated by `authorization.can("inventory.receive")`.

## 8. Inventory Feature Ownership

The UI lives under:

```text
frontend/src/features/inventory
```

This keeps operational receiving in the Inventory vertical slice.

## 9. Branch Scope

The receive page uses `useQueryScope()`.

If branch scope is not ready, the page renders a branch-required empty state and does not submit receiving commands.

No `localStorage`, `sessionStorage`, or direct shell storage access was introduced.

## 10. Warehouse Selection

Warehouses come from canonical `useWarehouses()`.

Only active Warehouses are offered for selection.

The user must explicitly select a Warehouse before submitting.

## 11. Supplier Selection

Suppliers come from canonical `useSuppliers()`.

Supplier selection is optional.

Supplier search is server-backed through hook parameters, and inactive Suppliers are filtered out in the page.

The empty Supplier option represents no supplier or another receiving source.

## 12. Supplier Reference

The optional reference field is generic operational text.

The UI does not introduce Purchase Order language or behavior.

## 13. Received Date And Notes

The UI exposes:

- optional received datetime
- optional notes

These map to backend-supported `received_at` and `notes`.

## 14. Product Search

Products come from canonical `useProducts()`.

Product search is server-backed through hook parameters.

Only active, inventory-tracked Products can be added to a receipt.

## 15. Receipt Line State

Receipt line draft state is local UI state only.

The line draft contains:

- Product
- quantity
- unit cost
- batch number
- manufacture date
- expiry date
- supplier batch reference

## 16. Quantity And Cost

Quantity and unit cost are captured as decimal-compatible string inputs.

Client validation requires:

- quantity greater than zero
- unit cost greater than or equal to zero

The backend remains the final source of validation truth.

## 17. Batch And Expiry Rules

Product flags drive line requirements:

- `track_batches` or `track_expiry`: batch number required
- `track_expiry`: expiry date required
- neither flag enabled: batch fields are disabled and rejected by client validation

Manufacture date and supplier batch reference are shown only for batch-capable lines because the backend accepts them for Goods Receipt items.

## 18. Expired Stock Guard

The receive page rejects already-expired stock before submit.

This mirrors the ordinary receiving rule from Migration 075.

## 19. Duplicate Line Guard

Duplicate lines are rejected by Product plus batch number.

For non-batch Products, this prevents duplicate Product-only lines in a single receipt.

## 20. Idempotency Lifecycle

The page generates an idempotency key when a draft starts.

Behavior:

- unchanged retry reuses the same idempotency key
- changing a previously submitted draft regenerates the idempotency key
- successful submit resets the draft and creates a new key
- idempotency conflict responses regenerate the key and preserve the form

## 21. Submit And Retry Behavior

Submit is disabled while the create mutation is pending.

Validation failures show toasts and do not mutate.

Server errors show toasts and preserve the current draft for correction or retry.

## 22. Confirmation Read-Back

Successful creation navigates to:

```text
/inventory/receipts/:receiptId
```

The confirmation page reads persisted data through `useGoodsReceipt(receiptId)`.

It does not expose update, delete, reverse, approve, PDF, or print actions.

## 23. Cache Invalidation

The page uses `useCreateGoodsReceipt()`.

Cache invalidation remains centralized in the Inventory hook layer introduced before this migration.

No page-level `queryClient` access was added.

## 24. Cost Visibility

Unit cost is visible only in the `inventory.receive` route flow.

Migration 076 does not add cost columns to the Inventory stock or movement read pages.

## 25. Navigation

The Inventory page exposes a Receive Stock action only for users with `inventory.receive`.

No sidebar or top-level navigation item was added.

## 26. Empty, Loading, And Error States

The receiving page includes:

- branch-required empty state
- no-active-warehouses error state
- empty line state
- product query error state
- loading states for Warehouses and Products

The confirmation page includes:

- missing receipt id empty state
- loading state
- error state

## 27. Procurement Boundary

Procurement remains closed.

The UI does not import Procurement hooks or services and does not surface Purchase Order, AP, invoice, or supplier payment behavior.

## 28. Static Architecture Verification

Verified:

```text
rg "inventoryService|QUERY_KEYS|queryClient|localStorage|sessionStorage|purchase.?order|procurement" frontend/src/features/inventory
```

Result:

```text
No matches
```

Verified:

```text
rg "useAdjustStock|useStockCount|useTransferStock" frontend/src/features/inventory frontend/src/hooks/queries/inventory/index.ts
```

Result:

```text
No matches
```

Verified:

```text
rg "inventory.receive|Receive Stock|GoodsReceiptDetailPage|ReceiveStockPage" frontend/src/app frontend/src/features/inventory frontend/src/routes
```

Result:

- receive route registered
- detail route registered
- routes protected by `inventory.receive`
- Inventory page action permission-gated by `inventory.receive`

## 29. Backend Verification

Compile:

```text
venv/bin/python -m compileall app: PASS
```

Goods Receipt and adjacent Inventory contract tests:

```text
venv/bin/python -m pytest app/api/tests/test_goods_receipt_contract.py app/api/tests/test_inventory_read_contract.py app/api/tests/test_inventory_movement_read_contract.py -q
```

Result:

```text
52 passed
```

Auth suite:

```text
venv/bin/python -m pytest app/services/tenant/auth/tests -q
```

Result:

```text
129 passed
```

## 30. Frontend Verification

TypeScript:

```text
cd frontend && npx tsc -b --pretty false: PASS
```

Build:

```text
cd frontend && npm run build: PASS
```

Known frontend warning:

```text
Some chunks are larger than 500 kB after minification.
```

## 31. Local Database State

PostgreSQL was not online during Migration 076 final verification:

```text
pg_lsclusters: 16/main 5432 down
pg_isready -h localhost -p 5432: no response
```

Alembic source head:

```text
FLASK_APP=app:create_app venv/bin/flask db heads: c3d4e5f6a7b8 (head)
```

Database current revision could not be read because PostgreSQL was down:

```text
FLASK_APP=app:create_app venv/bin/flask db current: OperationalError
```

No seed/bootstrap data was executed.

## 32. Files Created

- `frontend/src/features/inventory/pages/ReceiveStockPage.tsx`
- `frontend/src/features/inventory/pages/GoodsReceiptDetailPage.tsx`
- `frontend/docs/architecture/reviews/MIGRATION-076-GOODS-RECEIPT-STOCK-RECEIVING-OPERATIONAL-UI.md`

## 33. Files Modified

- `frontend/src/app/router.tsx`
- `frontend/src/features/inventory/index.ts`
- `frontend/src/features/inventory/pages/InventoryPage.tsx`
- `frontend/src/routes/permissions.ts`
- `frontend/src/routes/routes.ts`

## 34. Remaining Technical Debt

The four known SQLAlchemy relationship overlap warnings remain outside this migration:

- `RolePermission.role`
- `RolePermission.permission`
- `UserRole.user`
- `UserRole.role`

They should be handled in a dedicated model-relationship cleanup migration.

## 35. Blockers

No Migration 076 implementation blocker remains.

Local PostgreSQL was down during final verification, so database current revision and live runtime DB read-back were not revalidated in this migration.

## 36. Classification

Migration 076 classification:

```text
Frontend operational activation complete
```

Goods Receipt receiving is now an Inventory-owned operational UI flow backed by the Migration 075 API contract.

## 37. Recommended Next Migration

Recommended next migration:

```text
Migration 077 - Goods Receipt History / Receiving Audit List
```

This should add a server-backed receipt history/list view only if backed by a verified backend read contract.
