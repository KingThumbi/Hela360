# Migration 080 - Stock Adjustment Backend Contract

Date: 2026-08-09

Status: Complete

## 1. Migration Purpose

Migration 080 establishes the backend contract for auditable Stock Adjustments.

Stock Adjustment is the posting workflow that corrects inventory quantities. It is separate from Stock Count, which remains observation-only.

## 2. ADR Rules

- ADR-001: adjustment posting is owned by an Inventory service.
- ADR-004: request/entity/response types are canonical and exported.
- ADR-005: validation and conflict errors use existing API error handling.
- ADR-006: tenant and branch are server-derived.
- ADR-007: posting uses explicit `inventory.adjust`.
- ADR-008: frontend work is foundation only, no UI route/page.
- ADR-009: naming uses Stock Adjustment, signed delta, and Stock Count source language.

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

## 4. Previous Adjustment Assumptions

Search found no existing backend Stock Adjustment aggregate.

Existing adjustment evidence was limited to frontend permission/navigation scaffolding. The stale Stock Adjustment navigation entry was removed so Migration 080 does not activate UI.

## 5. Stock Adjustment Entity Decision

Added durable Inventory-owned aggregate:

- `StockAdjustment`
- `StockAdjustmentItem`

InventoryMovement alone is not the adjustment document.

## 6. Header

`StockAdjustment` stores tenant, branch, Warehouse, adjustment number, reason, source, status, idempotency key, request fingerprint, posting actor/timestamp, notes, and timestamps.

## 7. Lifecycle

Initial lifecycle is posted-only:

```text
posted
```

No draft, approval, rejection, repost, update, or delete lifecycle was introduced.

## 8. Permission

All create/list/detail endpoints use:

```text
inventory.adjust
```

## 9. Reason Semantics

Reason codes are finite:

- `stock_count`
- `damage`
- `expiry`
- `breakage`
- `correction`
- `opening_balance`
- `other`

Optional free-text reason and notes are also supported.

## 10. Stock Count Relationship

Stock Count may be a source through:

```text
source_type = stock_count
source_id = stock_count.id
```

Stock Count data is not rewritten.

## 11. Duplicate Count-Posting Prevention

Database uniqueness on:

```text
tenant_id, source_type, source_id
```

prevents a completed Stock Count from being adjusted more than once.

The service also checks under lock before posting.

## 12. Stock Count Line Derivation

Stock Count-derived adjustments are server-derived from persisted final `variance_quantity`.

Client-provided variance quantities are not accepted.

## 13. Manual Adjustment Contract

Manual endpoint accepts:

- Warehouse
- reason code
- optional reason/notes
- idempotency key
- line items

Tenant, branch, and user are server-owned.

## 14. Item Identity

Manual item identity is Product plus optional Batch.

Duplicate Product+Batch lines in one adjustment are rejected.

## 15. Delta Semantics

Items use signed `quantity_delta`:

- positive delta increases physical stock
- negative delta decreases physical stock

Set-quantity semantics were not mixed into this API.

## 16. Batch Rule

Batch/expiry Products require exact existing `batch_id`.

Non-batch Products must not include `batch_id`.

## 17. Unknown-Batch Disposition

Unknown physical batch creation remains deferred.

Migration 080 adjusts existing batches only.

## 18. Expired Batch Behavior

Expired batches can be adjusted because they remain physical stock.

Expiry continues to affect sellability elsewhere.

## 19. Positive Adjustment

Positive deltas increase `StockBalance.quantity_on_hand`.

For batch lines, they also increase `InventoryBatch.quantity_on_hand`.

## 20. Negative Adjustment

Negative deltas reduce on-hand stock only if the resulting physical quantity remains valid.

No clamping is performed.

## 21. Reserved-Stock Safety

Adjustment rejects results where:

```text
quantity_on_hand < quantity_reserved
```

for StockBalance or InventoryBatch.

## 22. Aggregate/Batch Consistency

Batch line adjustments update both the exact batch and aggregate StockBalance by the same signed delta.

## 23. Cost Disposition

Stock Adjustment is quantity-only.

`avg_unit_cost` is preserved. Goods Receipt remains the cost-bearing acquisition workflow.

## 24. Movement Type/Reference

Every posted adjustment creates InventoryMovement:

```text
movement_type = stock_adjustment
reference_type = stock_adjustment
reference_id = stock_adjustment.id
quantity = signed delta
```

## 25. Line Trace

Adjustment items store `stock_count_item_id` for Stock Count-derived lines.

InventoryMovement references the adjustment document.

## 26. Duplicate-Line Handling

The API rejects duplicate Product+Batch identities before posting.

The database also enforces uniqueness within an adjustment.

## 27. Idempotency

Idempotency is tenant-scoped.

Same key and same payload returns the existing adjustment without double-posting. Same key and changed payload returns conflict.

## 28. Concurrency

Posting locks Stock Count, StockBalance, and InventoryBatch rows where applicable.

## 29. Atomicity

Adjustment document, items, stock updates, batch updates, and movements are committed together.

On failure, the service rolls back.

## 30. Immutability

Posted adjustments cannot be edited, deleted, or reposted.

No update/delete endpoint exists.

## 31. Manual Endpoint

Added:

```text
POST /api/inventory/stock-adjustments
```

## 32. Stock Count Posting Endpoint

Added:

```text
POST /api/inventory/stock-counts/<count_id>/adjust
```

It posts all nonzero persisted variances for a completed Stock Count.

## 33. Zero-Variance Behavior

Completed Stock Counts with no nonzero variance are rejected as no adjustment needed.

No zero-quantity InventoryMovement rows are created.

## 34. Full/Partial Posting Disposition

Stock Count-derived posting is all nonzero variances.

Partial variance posting was deferred.

## 35. Detail/List Endpoints

Added:

```text
GET /api/inventory/stock-adjustments
GET /api/inventory/stock-adjustments/<adjustment_id>
```

List supports pagination and Warehouse/reason/source/date filters.

## 36. Source Projection

Projection includes source type/id and minimal Stock Count reference when sourced from Stock Count.

## 37. Authorization/Read Disposition

Adjustment list and detail require `inventory.adjust`.

No general `inventory.read` exposure was added.

## 38. Stock Count Linkage

Stock Count lifecycle remains completed.

The adjustment source relationship provides audit linkage without changing count observations.

## 39. Activity Integration

Posted adjustments appear in Inventory Movement Activity as `stock_adjustment`.

No movement endpoint redesign was needed.

## 40. Inventory Read Integration

Because StockBalance and InventoryBatch are updated, existing inventory and batch read APIs reflect corrected stock after posting.

## 41. Observation Immutability

Stock Count item snapshot, expected, counted, and variance quantities are not modified during adjustment posting.

## 42. Stale-Posting Behavior

Stock Count-derived adjustments use persisted final variance.

If later stock movement makes a negative delta unsafe, posting is rejected instead of changing the variance.

## 43. API Errors

Contract errors include invalid Warehouse/Product/Batch, unsupported reason/source, idempotency conflict, duplicate lines, already adjusted Stock Count, non-completed Stock Count, no variance, and unsafe negative stock.

## 44. Tests

Added `app/api/tests/test_stock_adjustment_contract.py`.

Coverage includes permission, manual positive/negative adjustment, reserved safety, exact batch behavior, expired batch adjustment, cross-contract rejection, idempotency, Stock Count-derived variance posting, duplicate Stock Count posting prevention, open-count rejection, list, and detail.

## 45. Frontend Type/Service/Hook Foundation

Added Stock Adjustment entity, request, response, service, query hook, and mutation hook foundation.

No page or route was activated.

## 46. Query Keys

Added branch-scoped Stock Adjustment list/detail query keys under Inventory.

## 47. Invalidation

Stock Adjustment mutations invalidate Inventory stock/batch/movement namespaces plus Stock Adjustment caches.

Stock Count-derived adjustment also invalidates Stock Count caches.

## 48. UI Disposition

No Stock Adjustment UI was activated.

The stale navigation placeholder was removed.

## 49. Permission Registration

Alembic registers:

```text
inventory.adjust
```

with `ON CONFLICT (code) DO NOTHING`.

The permission is not auto-granted globally.

## 50. Alembic Revision

Added:

```text
e5f6a7b8c9d0_add_stock_adjustments.py
```

It follows:

```text
d4e5f6a7b8c9
```

Source head is now:

```text
e5f6a7b8c9d0
```

## 51. Historical Data

No historical backfill was added.

Stock Adjustments begin from Migration 080 forward.

## 52. Local DB State

PostgreSQL 16/main is currently down:

```text
pg_lsclusters: 16 main 5432 down
```

`flask db heads` reports:

```text
e5f6a7b8c9d0 (head)
```

`flask db current` could not be verified while PostgreSQL was down.

## 53. Backend Compile

Verification:

```text
venv/bin/python -m compileall app: PASS
venv/bin/python -m py_compile migrations/versions/e5f6a7b8c9d0_add_stock_adjustments.py: PASS
```

## 54. Regression Totals

Verification:

```text
Stock Adjustment contract tests: 9 passed, 4 warnings
Stock Adjustment + adjacent Inventory tests: 84 passed, 4 warnings
Auth suite: 129 passed
Broad backend contract suite: 213 passed, 4 warnings
```

## 55. Frontend TypeScript

Verification:

```text
cd frontend && npx tsc -b --pretty false: PASS
```

## 56. Frontend Build

Verification:

```text
cd frontend && npm run build: PASS
```

## 57. Warnings

Known warnings remain:

- SQLAlchemy overlap warnings for RolePermission/UserRole relationships
- Vite large chunk warning

These were not addressed in Migration 080.

## 58. Files Inspected

Inspected inventory write paths:

- `SaleStockService`
- `RefundStockService`
- `GoodsReceiptService`
- `StockCountService`

Also inspected route, serializer, schema, model, query key, invalidation, and hook foundations.

## 59. Files Created

Created:

- `app/api/tests/test_stock_adjustment_contract.py`
- `app/schemas/stock_adjustment.py`
- `app/serializers/stock_adjustment.py`
- `app/services/tenant/inventory/stock_adjustment_service.py`
- `frontend/src/hooks/queries/inventory/useCreateStockAdjustment.ts`
- `frontend/src/hooks/queries/inventory/useCreateStockAdjustmentFromCount.ts`
- `frontend/src/hooks/queries/inventory/useStockAdjustment.ts`
- `frontend/src/hooks/queries/inventory/useStockAdjustments.ts`
- `frontend/src/types/entities/stock-adjustment.ts`
- `frontend/src/types/requests/create-stock-adjustment-request.ts`
- `frontend/src/types/requests/list-stock-adjustments-request.ts`
- `frontend/src/types/responses/stock-adjustment-summary.ts`
- `migrations/versions/e5f6a7b8c9d0_add_stock_adjustments.py`

## 60. Files Modified

Modified:

- `app/api/inventory.py`
- `app/models/__init__.py`
- `app/models/inventory.py`
- `app/schemas/__init__.py`
- `app/serializers/__init__.py`
- `app/services/tenant/inventory/__init__.py`
- `frontend/src/api/endpoints.ts`
- `frontend/src/hooks/queries/inventory/index.ts`
- `frontend/src/lib/queryInvalidation.ts`
- `frontend/src/lib/queryKeys.ts`
- `frontend/src/navigation/navigation.ts`
- `frontend/src/services/inventory/inventoryService.ts`
- `frontend/src/types/entities/index.ts`
- `frontend/src/types/requests/index.ts`
- `frontend/src/types/responses/index.ts`

## 61. Remaining Adjustment Blockers

No Migration 080 contract blocker remains.

Live DB upgrade/smoke remains blocked by local PostgreSQL service state.

## 62. Invariants Verified

Verified:

- adjustment is durable
- Stock Count remains observation-only
- manual adjustment uses signed delta
- Stock Count adjustment derives delta from persisted variance
- tenant/branch/Warehouse isolation
- exact existing batch requirement
- negative stock/reservation safeguards
- average cost unchanged
- InventoryMovement for every applied delta
- atomic posting
- immutable posted document
- idempotency prevents double posting
- Stock Count cannot be adjusted twice
- completed Count observations remain unchanged
- Procurement remains closed
- no Adjustment UI activated
- TypeScript remains clean
- production build succeeds

## 63. Rollback Boundary

Rollback drops Stock Adjustment tables and indexes and removes the `inventory.adjust` permission row.

No existing inventory data is backfilled by Migration 080.

## 64. Recommended Next Migration

Recommended next migration:

```text
Migration 081 - Stock Adjustment Operational UI
```

That migration can activate manual adjustment and Stock Count variance posting surfaces using this backend contract.
