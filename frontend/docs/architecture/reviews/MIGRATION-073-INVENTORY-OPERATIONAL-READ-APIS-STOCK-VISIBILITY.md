# Migration 073 - Inventory Operational Read APIs and Stock Visibility

## 1. Migration Purpose
Migration 073 activates read-only operational Inventory visibility for branch users through server-owned stock and batch read APIs plus a branch-scoped frontend Inventory page.

## 2. ADR Rules
The migration follows ADR-001 through ADR-009: services own business/API boundaries, hooks own query access, query keys and invalidation are centralized, frontend types have canonical owners, authorization is explicit, tenant/branch scope is server-derived, and unsupported Inventory mutations remain closed.

## 3. Baseline
Baseline passed before changes: `venv/bin/python -m compileall app`, `npx tsc -b --pretty false`, and `npm run build`. The known Vite large chunk warning remained.

## 4. StockBalance Model
`StockBalance` has `id`, `tenant_id`, `branch_id`, `warehouse_id`, `product_id`, `quantity_on_hand`, `quantity_reserved`, `quantity_available`, `avg_unit_cost`, `created_at`, and `updated_at`. Uniqueness is `(tenant_id, warehouse_id, product_id)`.

## 5. InventoryBatch Model
`InventoryBatch` has `id`, `tenant_id`, `product_id`, `warehouse_id`, `batch_number`, `expiry_date`, `manufacture_date`, `unit_cost`, `quantity_on_hand`, `quantity_reserved`, `status`, `received_at`, `created_at`, and `updated_at`. It has no `branch_id`; branch scope is derived through Warehouse/StockBalance.

## 6. Warehouse Model
`Warehouse` has `id`, `tenant_id`, `branch_id`, `code`, `name`, `warehouse_type`, `is_active`, `created_at`, and `updated_at`.

## 7. Permission Decision
Inventory read APIs use verified permission `inventory.read`.

## 8. Warehouse Endpoint Permission Disposition
`GET /api/warehouses` was aligned from POS-specific `sales.create` to `inventory.read`, because warehouse visibility is required for Inventory users who may not have checkout permission.

## 9. Query Service
Canonical backend read owner: `app/services/tenant/inventory/inventory_query_service.py`.

## 10. Stock List Endpoint
Created `GET /api/inventory`, authenticated and protected by `inventory.read`, tenant-safe, branch-scoped, warehouse-filterable, searchable, paginated, and read-only.

## 11. Stock Projection
The list projection returns StockBalance quantities, nested Product identity/configuration, nested Warehouse identity, batch count, expired batch count, expiring batch count, earliest sellable expiry date, low/out status, expired-stock flag, and sellable/expired derived quantities.

## 12. StockBalance Uniqueness
A Product may appear once per Warehouse. The API does not merge balances across Warehouses.

## 13. Search
Search is server-backed against Product `name`, `internal_sku`, `generic_name`, and `supplier_sku`.

## 14. Warehouse Filter
`warehouse_id` is optional. When provided, the server verifies tenant, current branch, and active Warehouse status.

## 15. Stock Status Filters
Supported server filters: `in_stock`, `out_of_stock`, `low_stock`, and `expired_stock`. No persisted StockStatus enum was introduced.

## 16. Low-Stock Semantics
Low stock is derived server-side as `quantity_available <= Product.reorder_level`, only when `reorder_level > 0` and the row is not out of stock.

## 17. Out-of-Stock Semantics
Out of stock is derived server-side as `quantity_available <= 0`.

## 18. Physical/Available/Sellable Quantity Disposition
`quantity_on_hand`, `quantity_reserved`, and `quantity_available` come from StockBalance. `sellable_quantity` is derived from non-expired available batches using the POS expiry rule; it is separate because StockBalance may include physically expired stock.

## 19. Expired Quantity
`expired_quantity` is derived from non-zero batches whose `expiry_date` is before the operational date. No StockBalance mutation occurs.

## 20. Expiry Filter Semantics
No hardcoded "expiring soon" threshold was added. The API supports caller-supplied `expires_before=YYYY-MM-DD`.

## 21. Earliest Expiry
`earliest_sellable_expiry_date` is the earliest expiry date among sellable batches only. Expired and non-sellable null-expiry batches are excluded.

## 22. Batch Count
`batch_count` counts non-zero physical batches for the StockBalance Product/Warehouse pair.

## 23. Detail Endpoint
No standalone stock detail endpoint was created. The batch endpoint returns the selected stock projection with its batch list.

## 24. Batch Endpoint
Created `GET /api/inventory/stock/<stock_balance_id>/batches`, protected by `inventory.read`.

## 25. Batch Projection
Batch projection returns id, batch number, expiry/manufacture/received dates, on-hand/reserved/available quantities, status, `is_expired`, `is_sellable`, `days_to_expiry`, and timestamps.

## 26. Cost Visibility
Cost fields are omitted. `avg_unit_cost` and `unit_cost` remain commercially sensitive until a verified cost-visibility permission exists.

## 27. Expired Batch Visibility
Expired non-zero batches remain visible and are marked `is_expired: true`.

## 28. Zero-Quantity Batch Disposition
Batch list defaults to non-zero batches. `include_zero=true` is supported for explicit inspection.

## 29. Batch Ordering
Batches are ordered non-expired first by expiry date, null-expiry after dated non-expired rows, and expired rows last.

## 30. Movement Read Disposition
InventoryMovement read APIs remain deferred. No movement-history page or endpoint was activated.

## 31. Backend Tests
Added tests for authentication, permission, branch requirement, tenant/branch isolation, warehouse filter validation, pagination, search, quantity projection, stock status filters, expiry derivation, empty result, multi-warehouse separation, batch projection, zero-batch opt-in, and batch isolation.

## 32. Frontend Previous Inventory Disposition
Migration 040 had closed public Inventory hooks because no backend API existed. Migration 073 reopens only verified read hooks and leaves speculative write hooks unsupported.

## 33. Canonical Frontend Stock Type
Created `InventoryStockSummary` under `frontend/src/types/responses`. Raw `InventoryItem` remains the StockBalance entity type.

## 34. InventoryBatch Type
Created read-only `InventoryBatchSummary` under `frontend/src/types/responses`.

## 35. ListInventoryRequest
Created `ListInventoryRequest` with `page`, `per_page`, `search`, `warehouse_id`, `stock_status`, and `expires_before`.

## 36. Inventory Service
Created canonical `frontend/src/services/inventory/inventoryService.ts` with `listStock()` and `getStockBatches()` only.

## 37. Query Keys
Inventory list/detail/batch keys are branch-scoped through `QUERY_KEYS.inventory.branchRoot(scope)`.

## 38. Hooks
Created verified hooks `useInventory(params)` and `useInventoryBatches(stockBalanceId)`.

## 39. Public Hook Boundary
`frontend/src/hooks/queries/inventory/index.ts` exports only `useInventory` and `useInventoryBatches`. Unsupported mutation hooks remain closed.

## 40. Route Permission
`/inventory` route metadata uses `inventory.read`.

## 41. Route
Activated the existing `/inventory` route with `InventoryPage` behind `ProtectedRoute`.

## 42. Navigation
Inventory navigation now derives `inventory.read` from route permission metadata.

## 43. Page
Created the read-only operational Inventory page with search, warehouse filter, stock status filter, expires-before filter, refresh, pagination, loading, error, and empty states.

## 44. Table
The table displays Product, SKU, Warehouse, on-hand, reserved, available, sellable, batch count, earliest expiry, and server-derived status indicators.

## 45. Batch Dialog
The row action opens a read-only batch dialog loaded on demand through `useInventoryBatches`.

## 46. Expiry/Low-Stock UX
The UI displays server-returned Expired, Expiring, Low, Out, Stocked, Prescription, Sellable, and Not sellable indicators without recalculating business truth.

## 47. Warehouse Filter
The page uses canonical `useWarehouses()` and does not hardcode Warehouses.

## 48. Invalidation Changes
`invalidateInventory` and `invalidateInventoryOperations` now support branch scope. `invalidateSalesOperations` invalidates branch-scoped Inventory after checkout/refund.

## 49. POS Integration
Successful POS checkout continues through existing Sales mutation and now refreshes Inventory reads through centralized invalidation.

## 50. Refund Integration
Successful refund continues through existing Sales refund mutation and refreshes branch Inventory reads through centralized invalidation.

## 51. Real DB State
No schema migration was required. PostgreSQL `16/main` is down on `localhost:5432`; `pg_isready` reports no response. `flask db heads` reports source head `b2c3d4e5f6a7`; `flask db current` cannot connect.

## 52. Runtime Smoke
Live `/inventory` runtime smoke was not run because local PostgreSQL is unavailable. Contract tests and frontend static/build verification were used.

## 53. Backend Compile
`venv/bin/python -m compileall app` passed.

## 54. Regression Totals
Auth suite passed: 129 tests. Targeted backend regression including Inventory read APIs, Prescription/Dispensing, Sales History, Receipt, POS, payment methods, Product list, Customer, Supplier, current session, and TillShift passed: 156 tests.

## 55. Frontend TypeScript
`npx tsc -b --pretty false` passed.

## 56. Frontend Build
`npm run build` passed. The known Vite large chunk warning remains.

## 57. Warnings
The known SQLAlchemy relationship overlap warnings remain unchanged: `RolePermission.role`, `RolePermission.permission`, `UserRole.user`, and `UserRole.role`.

## 58. Files Inspected
Inspected ADR-001 through ADR-009, Inventory/POS/Sales/Prescription migration reviews, Inventory/Product/Warehouse models, POS stock allocation, Warehouse API, permission registry, route registry, navigation, query keys, invalidation helpers, existing Inventory hooks, Product-owned legacy inventory service, Warehouse hooks, and page primitives.

## 59. Files Created
Created `app/api/inventory.py`, `app/services/tenant/inventory/inventory_query_service.py`, `app/api/tests/test_inventory_read_contract.py`, `frontend/src/types/requests/list-inventory-request.ts`, `frontend/src/types/responses/inventory-stock-summary.ts`, `frontend/src/types/responses/inventory-batch-summary.ts`, `frontend/src/services/inventory/inventoryService.ts`, `frontend/src/services/inventory/index.ts`, `frontend/src/hooks/queries/inventory/useInventoryBatches.ts`, `frontend/src/features/inventory/index.ts`, and this review document.

## 60. Files Modified
Modified `app/__init__.py`, `app/api/warehouses.py`, `app/api/tests/test_till_shift_contract.py`, `app/services/tenant/inventory/__init__.py`, `frontend/src/api/endpoints.ts`, `frontend/src/app/router.tsx`, `frontend/src/features/inventory/pages/InventoryPage.tsx`, `frontend/src/hooks/queries/inventory/index.ts`, `frontend/src/hooks/queries/inventory/useInventory.ts`, `frontend/src/hooks/queries/inventory/useStockItem.ts`, `frontend/src/lib/queryInvalidation.ts`, `frontend/src/lib/queryKeys.ts`, `frontend/src/navigation/navigation.ts`, `frontend/src/routes/permissions.ts`, `frontend/src/services/index.ts`, `frontend/src/services/products/inventoryService.ts`, `frontend/src/types/requests/index.ts`, and `frontend/src/types/responses/index.ts`.

## 61. Remaining Inventory Blockers
Remaining Inventory work includes receiving, adjustments, transfers, stock counts, write-offs, movement-history reads, valuation/cost visibility authorization, expiry disposal, reorder automation, and Procurement reactivation.

## 62. Invariants Verified
Inventory reads are tenant-safe and branch-scoped, Warehouse filters are validated, StockBalance remains aggregate authority, InventoryBatch remains batch authority, expired stock remains visible, POS expiry behavior is unchanged, low-stock status is server-derived, frontend does not calculate authoritative stock, Inventory UI is read-only, unsupported mutations remain closed, checkout/refund invalidate Inventory, Procurement remains inactive, TypeScript is clean, and production build succeeds.

## 63. Rollback Boundary
Rollback removes the Inventory read API/service/tests, frontend Inventory service/types/hooks/page/route wiring, Warehouse permission alignment, and branch-scoped inventory invalidation changes. No database rollback is needed.

## 64. Recommended Next Migration
Recommended next migration: Inventory movement read/audit API and stock activity visibility, before enabling Inventory mutations such as receiving or adjustments.
