# Migration 075 - Goods Receipt Stock Receiving Backend Contract

Date: 2026-08-09

Status: Complete

## 1. Migration Purpose

Migration 075 establishes the first verified backend stock receiving command contract.

The migration creates a durable Goods Receipt document and an atomic Inventory-owned receiving workflow that can increase stock in a verified branch Warehouse without requiring Purchase Orders.

No receiving UI was activated.

## 2. ADR Rules

- ADR-001: backend business rules live behind a service owner; frontend services expose business methods.
- ADR-004: shared frontend types are created only from verified backend contracts.
- ADR-005: validation, conflict, and not-found errors use domain errors.
- ADR-006: tenant and branch are server-derived.
- ADR-007: mutation uses `inventory.receive`, not `inventory.read`.
- ADR-008: Procurement remains closed; Inventory owns the operational receiving boundary.
- ADR-009: names use explicit Goods Receipt language.
- ADR-010: receiving is a business command and stock received is a domain fact.

## 3. Baseline

Pre-implementation baseline:

```text
venv/bin/python -m compileall app: PASS
cd frontend && npx tsc -b --pretty false: PASS
cd frontend && npm run build: PASS
```

Known frontend warning:

```text
Some chunks are larger than 500 kB after minification.
```

## 4. Previous Migration 016 Disposition

Migration 016 classified Goods Receipt as:

```text
Frontend-only assumption
```

Migration 075 changes that classification for backend Inventory receiving by introducing canonical backend persistence, API, service, serializer, tests, and frontend contract foundation.

The old private Procurement frontend Goods Receipt assumptions remain closed behind empty public Procurement barrels.

## 5. Current Receiving Evidence Inventory

Operational:

- `GoodsReceipt`
- `GoodsReceiptItem`
- `GoodsReceiptService`
- `POST /api/inventory/goods-receipts`
- `GET /api/inventory/goods-receipts/<receipt_id>`
- `inventory.receive`
- `InventoryMovement.movement_type = "goods_receipt"`

Persistence only:

- `StockBalance`
- `InventoryBatch`
- `InventoryMovement`

Frontend-only/private assumption:

- `frontend/src/services/procurement/goodsReceiptService.ts`
- `frontend/src/hooks/queries/procurement/useGoodsReceipt.ts`
- `frontend/src/hooks/queries/procurement/useGoodsReceipts.ts`

Absent:

- Purchase Order backend contract
- Supplier invoice/accounts payable contract
- receiving UI
- receipt list/history endpoint
- reversal/correction endpoint

## 6. Inventory Model Contract

Receiving reuses current inventory truth:

- `Warehouse`: tenant, branch, active warehouse.
- `Product`: tenant, active state, `track_inventory`, `track_batches`, `track_expiry`.
- `Supplier`: tenant-owned optional supplier.
- `StockBalance`: warehouse/product stock quantities and average unit cost.
- `InventoryBatch`: batch number, expiry, manufacture date, unit cost, quantity, received timestamp.
- `InventoryMovement`: immutable signed movement audit.

## 7. Goods Receipt Entity Decision

Created canonical durable document models:

- `GoodsReceipt`
- `GoodsReceiptItem`

Reason: `InventoryMovement` rows alone are not a durable commercial/audit receipt document.

## 8. Ownership Decision

Canonical owner:

```text
Inventory receiving domain
```

Commercial procurement source:

```text
optional/future
```

Inventory receipt truth:

```text
GoodsReceipt
```

## 9. GoodsReceipt Header

Fields:

- `id`
- `tenant_id`
- `branch_id`
- `warehouse_id`
- nullable `supplier_id`
- `receipt_number`
- nullable `supplier_reference`
- `idempotency_key`
- `request_fingerprint`
- `received_at`
- `status`
- nullable `notes`
- `received_by`
- timestamps

## 10. GoodsReceiptItem

Fields:

- `id`
- `goods_receipt_id`
- `product_id`
- nullable `batch_id`
- `line_number`
- `quantity`
- nullable `batch_number`
- nullable `manufacture_date`
- nullable `expiry_date`
- `unit_cost`
- nullable `supplier_batch_reference`
- timestamps

## 11. Receipt Numbering

No reusable document numbering service exists.

Server-generated receipt number:

```text
GRN-<year>-<receipt id prefix>
```

This is stable and unique without introducing a second sequence subsystem. Future migration may replace it with a formal document numbering service.

## 12. Status Lifecycle

Minimal lifecycle:

```text
received
```

No draft, approval, posted, cancel, or reversal lifecycle was introduced.

## 13. Product Inventory Eligibility

Receiving rejects:

- cross-tenant Product
- inactive Product
- non-inventory-tracked Product

No fake StockBalance is created for non-inventory Products.

## 14. Batch Requirement

Product-driven:

- `track_batches` or `track_expiry`: `batch_number` required
- neither flag enabled: batch fields rejected

This avoids imposing pharmacy batch requirements on every product while preserving batch truth for batch/expiry tracked stock.

## 15. Expiry Requirement

Product-driven:

- `track_expiry`: `expiry_date` required
- otherwise expiry is not required

`InventoryBatch.expiry_date` remains nullable for non-expiring stock.

## 16. Expired-Stock Receiving Disposition

Migration 075 rejects already-expired receipt lines for ordinary receiving.

If a future reconciliation workflow must enter expired stock intentionally, that should be a separate adjustment/reconciliation command.

## 17. Quantity Validation

Each line requires:

```text
quantity > 0
```

Parsing uses `Decimal`, not float arithmetic.

## 18. Unit Cost

Each line requires:

```text
unit_cost >= 0
```

Unit cost is persisted on:

- `GoodsReceiptItem.unit_cost`
- `InventoryBatch.unit_cost`
- `InventoryMovement.unit_cost`

No financial ledger or payable side effect is created.

## 19. Average-Cost Disposition

`StockBalance.avg_unit_cost` is updated using weighted average cost:

```text
old_value = old_qty * old_avg_cost
received_value = received_qty * receipt_unit_cost
new_avg = (old_value + received_value) / (old_qty + received_qty)
```

If old quantity is zero or negative, the received unit cost becomes the new average cost.

Product selling prices are not changed.

## 20. Batch Identity

Canonical batch identity:

```text
tenant_id + warehouse_id + product_id + batch_number
```

Migration revision adds:

```text
uq_inventory_batches_tenant_warehouse_product_batch
```

## 21. Batch Metadata Conflicts

Existing batch receives are rejected when metadata conflicts:

- expiry date mismatch
- manufacture date mismatch
- unit cost mismatch

Historic batch metadata is never silently rewritten.

## 22. Warehouse Validation

Warehouse must:

- exist
- belong to authenticated tenant
- belong to authenticated branch
- be active

Client tenant and branch values are not accepted.

## 23. Supplier Validation

Supplier is optional.

If provided, Supplier must:

- exist
- belong to authenticated tenant
- be active

Supplier is not branch-scoped.

## 24. Supplier Reference

`supplier_reference` is optional free text for external delivery note, invoice number, or supplier reference.

It is not treated as a Purchase Order id.

## 25. Duplicate/Idempotency Strategy

`idempotency_key` is required.

The service stores a tenant-scoped unique idempotency key and request fingerprint.

Behavior:

- same tenant + same key + same payload: returns existing Goods Receipt and does not increase stock again
- same tenant + same key + different payload: `409 Conflict`

This prevents silent duplicate stock from retries or double-submit.

## 26. Concurrency Strategy

The service uses `with_for_update()` when updating:

- existing `StockBalance`
- existing matching `InventoryBatch`

Database uniqueness protects tenant-scoped receipt idempotency and batch identity.

## 27. Service Owner

Canonical owner:

```text
app/services/tenant/inventory/goods_receipt_service.py
```

Responsibilities:

- validate header
- validate items
- enforce idempotency
- create receipt
- create items
- create/update batch
- create/update stock balance
- create inventory movement
- commit atomically
- rollback on failure

## 28. Movement Type

Inbound movement type:

```text
goods_receipt
```

Quantity is positive.

## 29. Movement Reference

Each movement uses:

```text
reference_type = "goods_receipt"
reference_id = GoodsReceipt.id
```

## 30. Line Trace Disposition

No `InventoryMovement.goods_receipt_item_id` was added.

Reason: Migration 075 rejects duplicate product/batch lines per receipt. Movement reference plus product/batch is sufficient for this contract.

## 31. StockBalance Update

Existing balance:

- locked
- `quantity_on_hand` incremented
- `quantity_available` recalculated
- `quantity_reserved` unchanged
- `avg_unit_cost` recalculated

Missing balance:

- created with reserved zero
- on hand and available set from receipt quantity

## 32. Batch Update

Batch-tracked/expiry-tracked product:

- matching batch locked and incremented
- missing batch created

Non-batch/non-expiry product:

- no `InventoryBatch` row created

## 33. Transaction Boundary

One request commits atomically:

- `GoodsReceipt`
- `GoodsReceiptItem`
- `StockBalance`
- `InventoryBatch`
- `InventoryMovement`

Any failure rolls back all changes.

## 34. Immutability

No update, delete, reversal, or correction endpoint was added.

Corrections should be modeled later as adjustment/reversal workflows, not history edits.

## 35. Create Endpoint

```text
POST /api/inventory/goods-receipts
```

The route is thin:

```text
identity -> permission -> request schema -> GoodsReceiptService -> serializer
```

## 36. Permission

Create endpoint permission:

```text
inventory.receive
```

`inventory.read` is not used for mutation.

## 37. Permission Bootstrap

`inventory.receive` already exists in `app/auth/permissions.py`.

No automatic role grant was added. Administrators must assign it through the existing role-permission mechanism.

## 38. Request Schema

Canonical request:

```json
{
  "warehouse_id": "...",
  "supplier_id": "...",
  "supplier_reference": "DN-123",
  "received_at": "2026-08-09T10:00:00+00:00",
  "notes": "...",
  "idempotency_key": "...",
  "items": [
    {
      "product_id": "...",
      "quantity": "10",
      "batch_number": "ABC123",
      "manufacture_date": "2026-01-01",
      "expiry_date": "2027-12-31",
      "unit_cost": "250.00",
      "supplier_batch_reference": "..."
    }
  ]
}
```

Tenant, branch, and received-by are server-derived.

## 39. Response Serializer

Response envelope:

```text
{ ok: true, item: GoodsReceipt }
```

The item includes:

- receipt identity
- warehouse projection
- optional supplier projection
- received timestamp
- status
- received-by projection
- line items
- batch/product projections
- unit cost

## 40. Read-Back/Detail Disposition

Added:

```text
GET /api/inventory/goods-receipts/<receipt_id>
```

Protected by:

```text
inventory.receive
```

Reason: receipt detail includes unit cost, and no separate cost-read permission exists.

## 41. Receipt List Disposition

No list/history endpoint was added.

Reason: this migration is backend-contract-first and the next UI migration can define the exact list/history needs.

## 42. Cost-Read Authorization

Receipt detail is protected by `inventory.receive`, not `inventory.read`.

Existing inventory read endpoints continue omitting costs.

## 43. Inventory Read Integration

After receipt, existing reads reflect stock automatically:

- `GET /api/inventory`
- `GET /api/inventory/stock/<id>/batches`
- `GET /api/inventory/movements`

## 44. Backend Tests

Added:

```text
app/api/tests/test_goods_receipt_contract.py
```

Coverage includes:

- successful authorized receipt
- permission enforcement
- cross-tenant/cross-branch rejection
- supplier validation
- product eligibility
- quantity/cost validation
- batch creation
- existing batch increment
- batch metadata conflict
- duplicate line rejection
- idempotent replay
- idempotency conflict
- rollback on downstream failure
- receipt detail read-back
- inventory read/movement visibility after receipt

## 45. Frontend Type Ownership

Created canonical frontend types from verified backend truth:

- `GoodsReceipt`
- `GoodsReceiptItem`
- `CreateGoodsReceiptRequest`
- `CreateGoodsReceiptItemRequest`

## 46. Frontend Service Disposition

Inventory service now exposes:

- `createGoodsReceipt`
- `getGoodsReceipt`

No Procurement service was reopened.

## 47. Mutation Hook Disposition

Added:

```text
useCreateGoodsReceipt
```

No receiving page uses it yet.

## 48. Query-Key Disposition

Goods Receipt detail keys are branch-scoped under Inventory:

```text
tenant -> branch -> inventory -> goods-receipts -> detail
```

No Procurement query keys are used by the Inventory receiving hook.

## 49. Procurement Boundary Verification

Public Procurement barrels remain closed:

- `frontend/src/services/procurement/index.ts`
- `frontend/src/hooks/queries/procurement/index.ts`

No Procurement route, page, or navigation item was activated.

## 50. Inventory Invalidation

`useCreateGoodsReceipt` invalidates:

```text
invalidateInventoryOperations(queryClient, branchScope)
```

This refreshes branch Inventory stock, batches, and movement activity through the Inventory branch root.

## 51. Alembic Revision

Created:

```text
migrations/versions/c3d4e5f6a7b8_add_goods_receipts.py
```

Revision:

```text
c3d4e5f6a7b8
```

Down revision:

```text
b2c3d4e5f6a7
```

Changes:

- `goods_receipts`
- `goods_receipt_items`
- `uq_inventory_batches_tenant_warehouse_product_batch`

## 52. Historical Inventory Disposition

No backfill was added.

Existing stock and historical inventory movements remain valid legacy/opening inventory without Goods Receipt ancestry.

## 53. Local DB State

Local PostgreSQL remained down:

```text
16/main 5432 down
localhost:5432 - no response
```

Source head:

```text
c3d4e5f6a7b8 (head)
```

`flask db current` and `flask db check` could not connect.

## 54. Backend Compile

```text
venv/bin/python -m compileall app
PASS
```

```text
venv/bin/python -m py_compile migrations/versions/c3d4e5f6a7b8_add_goods_receipts.py
PASS
```

## 55. Regression Totals

Goods Receipt contract:

```text
23 passed, 4 warnings
```

Targeted backend regression:

```text
193 passed, 4 warnings
```

Auth suite:

```text
129 passed
```

## 56. Frontend TypeScript

```text
cd frontend && npx tsc -b --pretty false
PASS
```

## 57. Frontend Build

```text
cd frontend && npm run build
PASS
```

Known warning:

```text
Some chunks are larger than 500 kB after minification.
```

## 58. Warnings

Known SQLAlchemy mapper overlap warnings remain:

- `RolePermission.role`
- `RolePermission.permission`
- `UserRole.user`
- `UserRole.role`

They were not changed in Migration 075.

## 59. Files Inspected

Inspected:

- ADR-001
- ADR-004
- ADR-005
- ADR-006
- ADR-007
- ADR-008
- ADR-009
- ADR-010
- Migration 016
- Migration 017
- Migration 018
- Migration 039
- Migration 065
- Migration 073
- Migration 074
- inventory, product, supplier, warehouse, sale/refund stock services
- permission registry
- existing frontend Procurement private assumptions

## 60. Files Created

- `app/schemas/goods_receipt.py`
- `app/serializers/goods_receipt.py`
- `app/services/tenant/inventory/goods_receipt_service.py`
- `app/api/tests/test_goods_receipt_contract.py`
- `migrations/versions/c3d4e5f6a7b8_add_goods_receipts.py`
- `frontend/src/types/entities/goods-receipt.ts`
- `frontend/src/types/requests/create-goods-receipt-request.ts`
- `frontend/src/hooks/queries/inventory/useCreateGoodsReceipt.ts`
- `frontend/src/hooks/queries/inventory/useGoodsReceipt.ts`
- `frontend/docs/architecture/reviews/MIGRATION-075-GOODS-RECEIPT-STOCK-RECEIVING-BACKEND-CONTRACT.md`

## 61. Files Modified

- `app/models/inventory.py`
- `app/models/__init__.py`
- `app/api/inventory.py`
- `app/schemas/__init__.py`
- `app/serializers/__init__.py`
- `app/services/tenant/inventory/__init__.py`
- `frontend/src/api/endpoints.ts`
- `frontend/src/services/inventory/inventoryService.ts`
- `frontend/src/lib/queryKeys.ts`
- `frontend/src/types/entities/index.ts`
- `frontend/src/types/requests/index.ts`
- `frontend/src/hooks/queries/inventory/index.ts`

## 62. Remaining Receiving Blockers

- Apply migration to local PostgreSQL once the server is available.
- Receiving UI activation.
- Receipt list/history endpoint.
- Receipt reversal/correction workflow.
- Formal document numbering subsystem.
- Separate cost-read permission.
- Purchase Order integration.
- Supplier invoice/accounts payable integration.
- Stock transfer/count/adjustment workflows.
- Batch policy administration beyond current Product flags.

## 63. Invariants Verified

Verified:

- durable Goods Receipt document exists
- Inventory owns operational receiving
- Purchase Order is not required
- tenant is server-derived
- branch is server-derived
- warehouse is validated
- supplier is optional and tenant-safe
- product is tenant-safe and inventory-eligible
- quantities are positive Decimals
- batch identity is truthful
- stock balance and batch update atomically
- inbound InventoryMovement is created
- movement references Goods Receipt
- idempotency prevents silent double stock
- receipt is immutable after receipt
- POS/refund regressions pass
- Procurement frontend remains closed
- no receiving UI was activated
- TypeScript remains at zero errors
- frontend build passes

## 64. Rollback Boundary

Rollback is the Alembic downgrade for:

- `goods_receipt_items`
- `goods_receipts`
- `uq_inventory_batches_tenant_warehouse_product_batch`

No runtime source rollback was staged or committed.

## 65. Recommended Next Migration

Recommended next migration:

```text
Migration 076 - Goods Receipt / Stock Receiving Operational UI
```

It should build a permission-protected receiving page using the verified `GoodsReceipt` contract, without activating Purchase Orders or Procurement.
