# Migration 079 - Stock Count Operational UI

Date: 2026-08-09

Status: Complete

## 1. Migration Purpose

Migration 079 activates the Stock Count frontend workflow on top of the Migration 078 backend contract.

Authorized Inventory staff can list Stock Counts, create a Warehouse count snapshot, enter physical quantities, review server-derived expected quantity and variance, complete an open count, cancel an open count, and revisit immutable completed or cancelled documents.

## 2. ADR Rules

- ADR-001: UI calls the Inventory service only through canonical hooks.
- ADR-002: pages use query and mutation hooks, not direct services.
- ADR-003: mutation invalidation remains centralized.
- ADR-004: Stock Count types remain under `src/types`.
- ADR-005: API errors are rendered as page/toast presentation errors.
- ADR-006: tenant and branch scope come from canonical query scope.
- ADR-007: routes use explicit `inventory.count`.
- ADR-008: UI belongs to `frontend/src/features/inventory`.
- ADR-009: naming uses Stock Count, Snapshot Qty, Expected Qty, Physical Count, and Variance.

## 3. Baseline

Pre-implementation verification:

```text
venv/bin/python -m compileall app: PASS
cd frontend && npx tsc -b --pretty false: PASS
cd frontend && npm run build: PASS
```

Known warning:

```text
Some chunks are larger than 500 kB after minification.
```

## 4. Migration 078 Contract Consumed

Consumed endpoints:

- `POST /api/inventory/stock-counts`
- `GET /api/inventory/stock-counts`
- `GET /api/inventory/stock-counts/<count_id>`
- `PUT /api/inventory/stock-counts/<count_id>/items/<item_id>`
- `POST /api/inventory/stock-counts/<count_id>/complete`
- `POST /api/inventory/stock-counts/<count_id>/cancel`

Consumed semantics:

- observation only
- physical basis is `quantity_on_hand`
- expected quantity is server reconciled
- variance is server derived
- completion and cancellation do not adjust stock

## 5. Frontend Foundation

Migration 078 foundation was reused:

- `StockCount`
- `StockCountItem`
- `StockCountListItem`
- `CreateStockCountRequest`
- `UpdateStockCountItemRequest`
- `ListStockCountsRequest`
- `inventoryService` Stock Count methods
- `useStockCounts`
- `useStockCount`
- `useCreateStockCount`
- `useUpdateStockCountItem`
- `useCompleteStockCount`
- `useCancelStockCount`
- branch-scoped Stock Count query keys
- Stock Count-only invalidation

## 6. Feature Ownership

Pages live under:

```text
frontend/src/features/inventory/pages
```

No top-level Stock Count feature was introduced.

## 7. Routes

Activated:

- `/inventory/stock-counts`
- `/inventory/stock-counts/new`
- `/inventory/stock-counts/:countId`

Added route helpers:

- `PATHS.INVENTORY.STOCK_COUNTS`
- `PATHS.INVENTORY.STOCK_COUNT_NEW`
- `PATHS.INVENTORY.STOCK_COUNT`
- `PATHS.INVENTORY.stockCount(countId)`

## 8. Permission

All Stock Count routes use:

```text
inventory.count
```

They do not use `inventory.read`.

## 9. Inventory Integration

The Inventory root now shows a `Stock Counts` action for users with `inventory.count`.

Users with only `inventory.count` can use the direct Stock Count routes even if they cannot access `/inventory`.

## 10. Stock Count List

`StockCountsPage` uses `useStockCounts`.

It includes loading, error, empty, refresh, and paginated states.

## 11. List Filters

List filters match the backend contract:

- Warehouse
- status
- started date from
- started date to

No unsupported search filter was added.

## 12. List Columns

Columns:

- Count #
- Warehouse
- Status
- Started
- Started By
- Progress
- Variance Lines
- Completed
- Action

## 13. Progress/Variance Summaries

Progress uses server summary:

```text
counted_items / total_items
```

Variance displays server-provided variance line counts. The UI does not sum variance quantities across mixed Products or units.

## 14. Create Flow

`CreateStockCountPage` uses `useCreateStockCount`.

On success it navigates to:

```text
/inventory/stock-counts/:id
```

and the detail page reloads persisted server state.

## 15. Branch Readiness

Creation is blocked until canonical branch scope is ready.

No storage reads were introduced.

## 16. Warehouse Selection

Warehouses come from `useWarehouses`.

Only active branch Warehouses are offered.

## 17. Count Scope

Full Warehouse count is the default path.

Selected Product count is exposed before snapshot creation using the Migration 078 `product_ids` request shape. Product selection uses the existing Product hook only when selected scope is active.

## 18. Overlapping-Count UX

Backend conflict messages are shown as toast errors.

The UI does not attempt to create a second open count for the same Warehouse.

## 19. Create Success

Successful creation shows:

```text
Stock Count created.
```

No stock adjustment language is used.

## 20. Detail Page

`StockCountDetailPage` uses `useStockCount(countId)`.

It shows count reference, Warehouse, status, scope, snapshot/start timestamps, actor fields, notes, summaries, and item lines.

## 21. Terminology

The item table labels use:

- Snapshot Qty
- Expected Qty
- Physical Count
- Variance

## 22. Snapshot vs Expected Semantics

The detail page states that Expected Qty accounts for stock movements after the count snapshot.

The frontend does not recalculate expected quantity.

## 23. Item Table

The detail table shows:

- Product
- SKU
- Batch
- Expiry
- Snapshot Qty
- Expected Qty
- Physical Count
- Variance
- Counted By / At
- Action

## 24. Batch Behavior

Batch lines show batch number when present.

Non-batch lines show an em dash.

## 25. Expired Stock

Expired batches remain visible and countable.

The label is:

```text
Expired
```

## 26. Physical-Count Input

Physical Count is the only editable quantity.

Snapshot Qty, Expected Qty, and Variance are read-only.

## 27. Blank vs Zero

Blank input is not saved and remains not counted.

`0` is accepted as a real physical count of zero.

## 28. Row Update Behavior

Rows use explicit Save actions.

No mutation is sent on every keystroke.

## 29. Recount Behavior

Open counts allow saving a previously counted line again.

The backend returns the latest expected quantity, variance, counted actor, and counted timestamp.

## 30. Variance Presentation

Variance uses server values only.

Labels are neutral:

- Matched
- Over
- Short
- Not counted

## 31. Progress

Detail progress uses server summary:

```text
Counted X of Y
```

The completion button is disabled while `uncounted_items > 0`.

## 32. Completion Guard

Complete is visible only for open counts.

The backend remains authoritative if state is stale.

## 33. Completion Confirmation

Completion uses `AlertDialog`.

The confirmation states:

```text
Completing this count records the final physical observations and variances. It does not adjust inventory quantities.
```

## 34. Completion Behavior

Completion uses `useCompleteStockCount`.

On success, the detail refetches and becomes read-only.

## 35. Completed State

Completed counts display completed timestamp and actor.

Inputs and row Save actions are disabled.

No Apply Variance or Post Count action exists.

## 36. Cancellation

Cancel is visible only for open counts and uses `useCancelStockCount`.

The confirmation states that cancellation does not change inventory.

## 37. Cancelled State

Cancelled counts remain readable and immutable.

## 38. Adjustment Boundary

No Stock Adjustment UI was activated.

No action applies, posts, or corrects variance.

## 39. Unknown Batch Limitation

No Add Unknown Batch or Create Batch control was added.

The detail page operates only on persisted snapshot lines.

## 40. Zero-System Product Disposition

Selected non-batch zero-system Product counts are supported only at creation through `product_ids`.

There is no item-add endpoint, so the detail page does not add Products after snapshot creation.

## 41. Count Filtering/Search

Detail filters are local presentation filters over loaded count items:

- Product/SKU/batch text
- Uncounted
- Variance only
- Expired

They do not alter server count scope.

## 42. Keyboard Efficiency

Pressing Enter inside a Physical Count input saves that row only.

There is no global Enter completion.

## 43. Direct Route Access

Stock Count list/create/detail routes are protected by `inventory.count`.

The list page hides the `/inventory` back link unless the user also has `inventory.read`.

## 44. Warehouse Permission Compatibility

`GET /api/warehouses` now allows either:

```text
inventory.read
inventory.count
```

The endpoint remains tenant/branch scoped and active-Warehouse only.

## 45. Query-Key Boundary

Feature pages do not import `QUERY_KEYS`.

Components use canonical hooks.

## 46. Invalidation Behavior

Create, update line, complete, and cancel use Stock Count mutation hooks.

Those hooks call `invalidateStockCounts` only and do not invalidate Inventory stock, batches, or movements.

## 47. Activity Disposition

Stock Counts were not added to Inventory Movement Activity.

No movement occurs.

## 48. Cost Disposition

No cost, valuation, or variance value is displayed.

## 49. Error/Stale State

Errors are shown through `ErrorState` or toast.

Mutation conflicts refetch the detail so stale open pages become read-only if the server has completed or cancelled the count.

## 50. Concurrency UX

Concurrent line saves rely on server truth after refetch.

Same-line concurrent edits are last accepted server update wins; no optimistic locking was invented.

## 51. Navigation/Persistence

Open counts are server persisted.

No localStorage draft or silent cancellation on page leave was added.

## 52. Accessibility/Responsive Behavior

Physical Count inputs have labels.

Status and variance use text labels, not color alone.

Tables use horizontal scrolling for narrower screens.

## 53. Backend Corrections

One narrow backend alignment was required:

```text
GET /api/warehouses
```

now accepts `inventory.count` in addition to `inventory.read` so count-authorized users can select a Warehouse.

No Stock Count backend semantics changed.

## 54. Local DB State

PostgreSQL 16/main is currently down:

```text
pg_lsclusters: 16 main 5432 down
```

`flask db heads` reports:

```text
d4e5f6a7b8c9 (head)
```

`flask db current` could not connect while PostgreSQL was down.

## 55. Runtime Smoke

No live DB runtime Stock Count smoke was executed because PostgreSQL was unavailable.

The UI workflow was statically verified through TypeScript, route registration, and production build.

## 56. Backend Tests

Verification:

```text
venv/bin/python -m compileall app: PASS
Stock Count + adjacent Inventory/Till tests: 142 passed, 4 warnings
Auth suite: 129 passed
Broad backend contract suite: 204 passed, 4 warnings
```

## 57. Frontend TypeScript

Verification:

```text
cd frontend && npx tsc -b --pretty false: PASS
```

## 58. Frontend Build

Verification:

```text
cd frontend && npm run build: PASS
```

## 59. Warnings

Known warnings remain:

- SQLAlchemy relationship overlap warnings for `RolePermission.role`, `RolePermission.permission`, `UserRole.user`, and `UserRole.role`
- Vite large chunk warning

These were not addressed in Migration 079.

## 60. Files Inspected

Inspected:

- ADR-001 through ADR-009
- Migrations 073 through 078
- Stock Count frontend types, service methods, hooks, query keys, and invalidation
- Stock Count backend serializer/tests
- Inventory pages and route registry
- Warehouse endpoint and hook

## 61. Files Created

Created:

- `frontend/src/features/inventory/pages/StockCountsPage.tsx`
- `frontend/src/features/inventory/pages/CreateStockCountPage.tsx`
- `frontend/src/features/inventory/pages/StockCountDetailPage.tsx`
- `frontend/docs/architecture/reviews/MIGRATION-079-STOCK-COUNT-OPERATIONAL-UI.md`

## 62. Files Modified

Modified:

- `app/api/warehouses.py`
- `app/api/tests/test_till_shift_contract.py`
- `frontend/src/app/router.tsx`
- `frontend/src/features/inventory/index.ts`
- `frontend/src/features/inventory/pages/InventoryPage.tsx`
- `frontend/src/hooks/queries/products/useProducts.ts`
- `frontend/src/routes/permissions.ts`
- `frontend/src/routes/routes.ts`

## 63. Remaining Stock Count Blockers

No Migration 079 Stock Count UI blocker remains.

Live database smoke remains blocked by local PostgreSQL service state.

## 64. Invariants Verified

Verified:

- Stock Count UI uses `inventory.count`
- branch is session/query-scope owned
- Warehouse data is server-backed
- Snapshot Qty is read-only
- Expected Qty is server-owned
- Physical Count is user input
- Variance is server-owned
- blank and zero are distinct
- batch lines remain batch-specific
- expired batches remain countable
- completed/cancelled counts are immutable
- completion does not adjust stock
- cancellation does not adjust stock
- no InventoryMovement UI implication
- Stock Count mutations invalidate only Stock Count queries
- no Stock Adjustment UI is activated
- Procurement remains closed
- TypeScript remains clean
- production build succeeds

## 65. Rollback Boundary

Rollback is frontend-route/page removal plus reverting the narrow Warehouse permission compatibility change.

No Alembic revision was added in Migration 079.

## 66. Recommended Next Migration

Recommended next migration:

```text
Migration 080 - Stock Adjustment Backend Contract
```

That migration should define the explicit approval/posting path for approved Stock Count variances without changing the observation-only Stock Count contract.
