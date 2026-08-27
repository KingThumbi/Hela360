# Migration 078 - Stock Count Backend Contract

Date: 2026-08-09

Status: Complete

## 1. Migration Purpose

Migration 078 adds the backend contract for durable Stock Count documents.

Stock Count observes physical stock. It records discrepancy truth and does not post corrections to inventory. A later Stock Adjustment workflow is responsible for approving and posting discrepancy corrections.

## 2. ADR Rules

- ADR-001: Stock Count behavior is owned by `StockCountService`.
- ADR-004: backend and frontend type ownership stays explicit.
- ADR-005: invalid count payloads and filters return normalized errors.
- ADR-006: tenant and branch are server-derived.
- ADR-007: Stock Count uses an explicit `inventory.count` permission.
- ADR-008: frontend foundation is type/service/hook only; no UI activation.
- ADR-009: names use Stock Count language consistently.
- ADR-010: Stock Count records an operational document, not an implicit inventory event.

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

## 4. Previous Assumptions

Migration 040 classified Stock Count as unsupported/inert. Migration 078 replaces that placeholder with a canonical backend contract and frontend foundation.

No operational page, route, navigation entry, or fabricated update/delete behavior was added.

## 5. StockBalance Physical Basis

Stock Count uses:

```text
StockBalance.quantity_on_hand
```

It does not use `quantity_available` or sellable stock. Reserved inventory is physically present and remains countable.

## 6. Batch Counting Rule

Batch-aware products are counted by batch.

The snapshot source is:

```text
InventoryBatch.quantity_on_hand
```

Expired batches are included. Zero-quantity historical batches are excluded.

## 7. Unknown Physical Batch Disposition

Unknown physical batches are not created during Stock Count.

The system rejects selected batch-tracked products that have no system batch rows. Discovery and correction of unknown batches is deferred to a later adjustment/discovery workflow.

## 8. Entity Decision

Added durable entities:

- `StockCount`
- `StockCountItem`

They represent the count document and line-level physical observations.

## 9. StockCount Header

`StockCount` stores tenant, branch, Warehouse, count number, idempotency key, request fingerprint, scope type, lifecycle status, snapshot timestamp, actor timestamps, and notes.

## 10. StockCountItem

`StockCountItem` stores the counted Product, optional Batch, line number, snapshot quantity, expected quantity, counted quantity, variance quantity, counted actor/timestamp, and notes.

## 11. Numbering

Count numbers use:

```text
SC-<year>-<count id prefix>
```

They are unique per tenant.

## 12. Lifecycle

Supported statuses:

- `open`
- `completed`
- `cancelled`

## 13. Snapshot Semantics

Stock Count captures `snapshot_at` on creation and creates item lines from current physical system quantities.

Snapshot quantities remain historical; count entry updates expected quantities using movement reconciliation.

## 14. Count Scope

Supported scopes:

- full Warehouse count
- selected Product count

The Warehouse must be active and belong to the authenticated tenant and branch.

## 15. Zero-System Stock

Selected non-batch inventory products without a StockBalance row can be counted with a system quantity of zero.

Full Warehouse counts require countable stock lines.

## 16. Batch Snapshot

Batch-tracked or expiry-tracked products produce one line per nonzero system batch quantity.

The line stores the batch id and batch-visible fields in serializer output.

## 17. Stock/Batch Consistency

For batch-aware products, the summed nonzero batch quantities must match `StockBalance.quantity_on_hand`.

Mismatch returns a conflict instead of presenting misleading count lines.

## 18. Permission

All Stock Count endpoints are protected by:

```text
inventory.count
```

## 19. Permission Registration

Alembic registers `inventory.count` with `ON CONFLICT (code) DO NOTHING`.

The permission is not auto-granted globally.

## 20. Create Endpoint

Added:

```text
POST /api/inventory/stock-counts
```

The client supplies Warehouse, idempotency key, optional selected Product ids, and notes.

## 21. Overlapping Policy

Only one open Stock Count is allowed per Warehouse.

This avoids concurrent open count documents observing the same physical location.

## 22. Idempotency

Create is idempotent by tenant and idempotency key.

The same key and same payload returns the existing count. The same key with a different payload returns conflict.

## 23. Detail/List

Added:

```text
GET /api/inventory/stock-counts
GET /api/inventory/stock-counts/<count_id>
```

Both are tenant-owned and branch-scoped.

List supports `page`, `per_page`, `status`, `warehouse_id`, `date_from`, and `date_to`.

## 24. Count Entry

Added:

```text
PUT /api/inventory/stock-counts/<count_id>/items/<item_id>
```

Only `counted_quantity` and optional notes are client-owned.

## 25. Quantity Validation

`counted_quantity` is required and must be non-negative.

System quantities, expected quantities, variance, tenant, branch, user, and timestamps are server-owned.

## 26. Variance

Variance is server-derived:

```text
variance_quantity = counted_quantity - expected_quantity
```

## 27. Recount Behavior

An open item can be counted again. The latest count entry recalculates expected quantity and variance at the new counted timestamp.

## 28. Uncounted

Uncounted lines keep `counted_quantity` and `variance_quantity` null.

Completion is blocked while any item remains uncounted.

## 29. Completion

Completion sets status and completion actor/timestamp only.

Completed counts are immutable through the service contract.

## 30. Complete Endpoint

Added:

```text
POST /api/inventory/stock-counts/<count_id>/complete
```

It requires all lines to be counted and does not mutate stock.

## 31. Stock Mutation

Stock Count does not update:

- `StockBalance`
- `InventoryBatch`
- `InventoryMovement`

No silent inventory rewrite was introduced.

## 32. Variance Summary

Serializer summaries include total, counted, uncounted, variance, positive variance, and negative variance item counts.

## 33. Batch Variance

Batch variance is stored per batch line.

No cross-batch netting or automatic transfer is performed.

## 34. Reserved Stock

Reserved stock remains part of physical stock.

Counts observe `quantity_on_hand`, so reserved units are not excluded.

## 35. Expired Stock

Expired batches are countable and visible, with `is_expired` included in serializer output.

## 36. Zero-Batch

Zero-quantity historical batches are excluded from generated count lines.

## 37. Live Movement Problem

Inventory can move after a count snapshot and before a line is physically counted.

Migration 078 keeps the snapshot, then reconciles expected quantity at item entry.

## 38. Movement Reconciliation

Expected quantity at count entry is:

```text
snapshot_quantity + net InventoryMovement quantity after snapshot_at through counted_at
```

Movement matching is tenant, branch, Warehouse, Product, and Batch aware.

## 39. Snapshot/Expected Terminology

`snapshot_quantity` is the system quantity at Stock Count creation.

`expected_quantity` is the reconciled system quantity at the time the line is counted.

## 40. Counted Timestamp

`counted_at` is server-generated when a count item is updated.

## 41. Locking

Update, complete, and cancel load the count with `FOR UPDATE`. Item update also locks the line.

## 42. Immutability

Completed and cancelled counts cannot be updated, completed again, or cancelled again.

## 43. Cancellation

Added:

```text
POST /api/inventory/stock-counts/<count_id>/cancel
```

Cancellation prevents a stuck open document from permanently blocking the Warehouse.

## 44. Future Adjustment

Stock Adjustment remains the future posting workflow for approved discrepancies.

Stock Count provides the discrepancy source of truth but does not approve or post the correction.

## 45. InventoryMovement

Stock Count reads `InventoryMovement` for live expected quantity reconciliation only.

It does not create movement rows.

## 46. Serializer

Added Stock Count serializers for detail and summary projections.

Detail includes Warehouse, lifecycle actors, summary, and item lines.

## 47. Cost Visibility

Stock Count responses do not expose cost or valuation data.

## 48. Frontend Type Foundation

Added frontend Stock Count entity, request, and response types.

## 49. Service Foundation

Added `inventoryService` methods for create, list, detail, item count entry, complete, and cancel.

## 50. Hook Foundation

Added query and mutation hooks:

- `useStockCounts`
- `useStockCount`
- `useCreateStockCount`
- `useUpdateStockCountItem`
- `useCompleteStockCount`
- `useCancelStockCount`

## 51. Query Keys

Stock Count list and detail keys are branch-scoped.

## 52. Invalidation

Stock Count mutation hooks invalidate Stock Count document caches only.

They intentionally do not invalidate broad stock balance, batch, or movement caches because count observation/completion does not mutate inventory.

## 53. Procurement Boundary

No Procurement Stock Count behavior was added.

Stock Count belongs to Inventory.

## 54. Tests

Added `app/api/tests/test_stock_count_contract.py`.

Covered permission, create snapshot, batch/expiry rules, cross-scope rejection, selected zero-system non-batch count, idempotency, open Warehouse conflict, item count entry, variance derivation, negative quantity rejection, completion, stock non-mutation, immutability, cancellation, list/detail scoping, and filter validation.

## 55. Alembic Revision

Added:

```text
d4e5f6a7b8c9_add_stock_counts.py
```

It follows:

```text
c3d4e5f6a7b8
```

Repository head is now:

```text
d4e5f6a7b8c9
```

## 56. Historical Data

The migration is additive.

No historical inventory data is rewritten.

## 57. Local DB

During the resumed closeout, PostgreSQL 16/main was down:

```text
pg_lsclusters: 16 main 5432 down
```

`flask db current` could not connect. `flask db check` is supported, but also could not connect while PostgreSQL was down.

`flask db heads` verified the repository head as `d4e5f6a7b8c9`.

## 58. Backend Compile

Verification:

```text
venv/bin/python -m compileall app: PASS
venv/bin/python -m py_compile migrations/versions/d4e5f6a7b8c9_add_stock_counts.py: PASS
```

## 59. Regression Totals

Verification:

```text
Stock Count + inventory targeted tests: 75 passed, 4 warnings
Auth suite: 129 passed
Current broad backend contract suite: 203 passed, 4 warnings
```

Warnings are the existing SQLAlchemy relationship overlap warnings.

## 60. Frontend TypeScript

Verification:

```text
cd frontend && npx tsc -b --pretty false: PASS
```

## 61. Frontend Build

Verification:

```text
cd frontend && npm run build: PASS
```

Known warning remains:

```text
Some chunks are larger than 500 kB after minification.
```

## 62. Warnings

Existing SQLAlchemy mapper overlap warnings remain:

- `RolePermission.role`
- `RolePermission.permission`
- `UserRole.user`
- `UserRole.role`

These are separate model-relationship cleanup technical debt and were not changed.

## 63. Files Inspected

Inspected architecture and migration context:

- ADR-001
- ADR-004
- ADR-005
- ADR-006
- ADR-007
- ADR-008
- ADR-009
- ADR-010
- Migration 015
- Migration 040
- Migration 065
- Migration 073
- Migration 074
- Migration 075
- Migration 077

## 64. Files Created

Created:

- `app/api/tests/test_stock_count_contract.py`
- `app/schemas/stock_count.py`
- `app/serializers/stock_count.py`
- `app/services/tenant/inventory/stock_count_service.py`
- `frontend/src/hooks/queries/inventory/useCancelStockCount.ts`
- `frontend/src/hooks/queries/inventory/useCompleteStockCount.ts`
- `frontend/src/hooks/queries/inventory/useCreateStockCount.ts`
- `frontend/src/hooks/queries/inventory/useStockCounts.ts`
- `frontend/src/hooks/queries/inventory/useUpdateStockCountItem.ts`
- `frontend/src/types/entities/stock-count.ts`
- `frontend/src/types/requests/create-stock-count-request.ts`
- `frontend/src/types/requests/list-stock-counts-request.ts`
- `frontend/src/types/requests/update-stock-count-item-request.ts`
- `frontend/src/types/responses/stock-count-summary.ts`
- `migrations/versions/d4e5f6a7b8c9_add_stock_counts.py`

## 65. Files Modified

Modified:

- `app/api/inventory.py`
- `app/auth/permissions.py`
- `app/models/__init__.py`
- `app/models/inventory.py`
- `app/schemas/__init__.py`
- `app/serializers/__init__.py`
- `app/services/tenant/inventory/__init__.py`
- `frontend/src/api/endpoints.ts`
- `frontend/src/hooks/queries/inventory/index.ts`
- `frontend/src/hooks/queries/inventory/useStockCount.ts`
- `frontend/src/lib/queryInvalidation.ts`
- `frontend/src/lib/queryKeys.ts`
- `frontend/src/services/inventory/inventoryService.ts`
- `frontend/src/types/entities/index.ts`
- `frontend/src/types/requests/index.ts`
- `frontend/src/types/responses/index.ts`

## 66. Remaining Blockers

No Migration 078 backend contract blockers remain.

Live PostgreSQL application of the new Alembic revision was not performed in the resumed closeout because the local PostgreSQL cluster was down and service start required an interactive sudo password.

## 67. Invariants

Verified contract invariants:

- tenant-owned
- branch-scoped
- Warehouse validated
- Product scope validated
- physical on-hand count basis
- batch-aware line generation
- expired batches included
- zero historical batches excluded
- unknown physical batch creation deferred
- system quantities server-derived
- variance server-derived
- no stock mutation
- no InventoryMovement posting
- completed/cancelled documents immutable
- live movement reconciliation defined
- no cross-tenant or cross-branch leaks

## 68. Rollback

Downgrade deletes the `inventory.count` permission and drops Stock Count tables and indexes.

No data outside the new Stock Count tables is mutated by the migration.

## 69. Recommended Next Migration

Recommended next migration:

```text
Migration 079 - Stock Count Operational UI
```

It should activate the Stock Count page using the verified backend contract and existing frontend type/service/hook foundation, while preserving the rule that Stock Count does not post inventory corrections.
