# Migration 065 - Batch-Aware Stock Deduction and Expiry Enforcement

## 1. Purpose

Migration 065 makes POS checkout consume real inventory from verified tenant,
branch, warehouse, Product, StockBalance, and InventoryBatch context.

This migration does not activate POS UI, add receipts, implement prescription
workflows, redesign Product pricing, or broadly activate Inventory frontend
modules.

## 2. Baseline

Baseline commands:

```text
venv/bin/python -m compileall app: PASS
npx tsc -b --pretty false: PASS
npm run build: PASS
```

The known Vite large-chunk warning remains unchanged.

## 3. Architecture Sources

Reviewed:

- ADR-001 Service Layer Architecture
- ADR-004 Type System Organization
- ADR-005 Error Handling Strategy
- ADR-006 Multi-Tenant Architecture
- ADR-008 Frontend Module Boundaries
- ADR-009 Enterprise Naming Conventions
- ADR-010 Domain Event Architecture
- Migration 015 Inventory Type Ownership
- Migration 040 Inventory Capability Disposition
- Migration 060 Sales/POS Capability Rebaseline
- Migration 062 Till/TillShift Lifecycle Contract
- Migration 063 Sale TillShift Attribution
- Migration 064 POS Price Integrity and Override Policy

## 4. Model Inventory

Verified `StockBalance` fields:

- `tenant_id`
- `branch_id`
- `warehouse_id`
- `product_id`
- `quantity_on_hand`
- `quantity_reserved`
- `quantity_available`
- `avg_unit_cost`

Verified `InventoryBatch` fields:

- `tenant_id`
- `product_id`
- `warehouse_id`
- `batch_number`
- `expiry_date`
- `manufacture_date`
- `unit_cost`
- `quantity_on_hand`
- `quantity_reserved`
- `status`
- `received_at`

Verified `InventoryMovement` fields:

- `tenant_id`
- `branch_id`
- `warehouse_id`
- `product_id`
- `batch_id`
- `movement_type`
- `quantity`
- `unit_cost`
- `unit_price`
- `reference_type`
- `reference_id`
- `notes`
- `created_by`

Verified Product inventory flags:

- `track_inventory`
- `track_batches`
- `track_expiry`
- `allow_negative_stock`

Verified `SaleItem.batch_id` exists, but a single field cannot truthfully
represent multi-batch allocation.

## 5. Till Warehouse Context

`Till` does not currently have `warehouse_id`.

Migration 065 therefore keeps checkout `warehouse_id` as the canonical warehouse
source, but only after the existing server validation proves the warehouse
belongs to the authenticated branch.

This is recorded as a schema gap for a later Till-to-warehouse migration.

## 6. Inventory Service Owner

Created:

```text
app/services/tenant/inventory/sale_stock_service.py
```

The Sales route no longer owns batch allocation. It orchestrates checkout and
delegates inventory allocation to `allocate_sale_stock(...)`.

## 7. Allocation Result

Internal structured result:

- `StockAllocationResult`
- `StockAllocationLine`

This is not exposed through the public API.

## 8. StockBalance Authority

`StockBalance.quantity_available` is treated as the persisted aggregate
available-stock authority.

After deduction, `quantity_on_hand` is decremented and `quantity_available` is
maintained as:

```text
quantity_on_hand - quantity_reserved
```

## 9. Batch Authority

For Products with `track_batches` or `track_expiry`, sellable stock must come
from eligible `InventoryBatch` rows in the same tenant, warehouse, and Product
context.

Batch available quantity is:

```text
quantity_on_hand - quantity_reserved
```

## 10. Expiry Semantics

Expired rule:

```text
expiry_date < operational_date
```

Batches expiring today remain sellable through the operational day.

If `Product.track_expiry` is true, null `expiry_date` is treated as unknown
expiry and is not sellable.

If `track_expiry` is false, null expiry may be used for non-expiring batch stock
and is ordered after dated stock.

## 11. FEFO

Migration 065 adopts deterministic FEFO for eligible batches:

```text
earliest non-expired expiry_date first
then received_at
then id
```

Expired batches never contribute to sellable availability.

## 12. Allocation Shape

One SaleItem may draw from multiple batches.

`InventoryMovement` rows are the canonical batch allocation trace. If the line
uses one batch, `SaleItem.batch_id` is populated for compatibility. If the line
spans multiple batches, `SaleItem.batch_id` remains null.

## 13. Concurrency Safety

The inventory service uses SQLAlchemy row locks:

- `StockBalance.with_for_update()`
- `InventoryBatch.with_for_update()`

The locks are acquired before final availability determination and mutation.

## 14. Transaction Boundary

Checkout still commits once through the Sales route.

The following are committed atomically:

- `Sale`
- `SaleItem`
- `SalePayment`
- `StockBalance`
- `InventoryBatch`
- `InventoryMovement`

On checkout failure, the existing rollback path reverts inventory mutations.

## 15. Movement Contract

Sale deduction movements use:

```text
movement_type = "sale"
quantity = negative allocated quantity
reference_type = "sale"
reference_id = sale.id
batch_id = allocated batch when applicable
```

This preserves the existing outbound ledger sign convention.

## 16. Unit Cost

Batch allocations use `InventoryBatch.unit_cost`.

StockBalance-only allocation uses `StockBalance.avg_unit_cost`.

No COGS or valuation redesign was introduced.

## 17. Product Tracking Policy

Inventory-tracked Products require StockBalance.

Products with `track_batches` or `track_expiry` require eligible batch stock.

Non-inventory Products do not require stock, do not create movements, and do not
invent stock.

## 18. Checkout Contract

Frontend checkout remains:

```text
product_id + quantity
```

The backend chooses eligible stock and batch allocation. No POS UI batch
selection was added.

## 19. Regression Preservation

Migration 064 price integrity remains unchanged:

- active Product required;
- tenant Product ownership required;
- `default_sale_price` is canonical;
- `min_sale_price` enforced;
- positive discount/tax rejected.

Migration 063 TillShift attribution remains unchanged.

Migration 061 Payment Method validation remains unchanged.

## 20. Refund Disposition

Refund stock restoration remains deferred.

Migration 065 only records current sale outbound allocation correctly. It does
not redesign refund inventory return behavior.

## 21. Local DB State

Repository migration head:

```text
flask db heads: 2f4a8b9c1d3e (head)
```

Local PostgreSQL state:

```text
pg_isready -h localhost -p 5432: no response
pg_lsclusters: 16/main down
```

`flask db current` and `flask db check` failed because the local database was
unreachable.

No schema migration was created for Migration 065.

## 22. Tests Added

Focused checkout inventory tests cover:

- tracked Product with valid stock succeeds;
- insufficient stock rejected;
- expired-only stock rejected;
- expired stock excluded when valid stock exists;
- FEFO multi-batch allocation;
- StockBalance decrement;
- batch quantity decrement;
- InventoryMovement batch IDs and negative sale quantities;
- tenant isolation;
- branch isolation;
- warehouse isolation;
- non-inventory Product without stock;
- rollback restores inventory after commit failure;
- Migration 064 price constraints still pass;
- Migration 063 TillShift attribution still passes.

## 23. Verification

Post-implementation verification:

```text
venv/bin/python -m compileall app: PASS
app/api/tests/test_till_shift_contract.py: 38 passed
Sales/POS + Payment Method + Product + Customer + Supplier targeted tests: 33 passed
Current-session targeted tests: 13 passed
Auth suite: 129 passed
npx tsc -b --pretty false: PASS
npm run build: PASS
```

Known warnings:

- four existing SQLAlchemy relationship overlap warnings;
- known Vite large-chunk warning.

## 24. Static Verification

Static searches verified:

- `allocate_sale_stock(...)` owns batch allocation logic;
- expired stock is excluded in the inventory service;
- `with_for_update()` locks StockBalance and InventoryBatch rows;
- sale movements carry `batch_id`;
- no POS UI batch selection was added.

## 25. Remaining Technical Debt

Remaining inventory debt:

- Till does not yet own `warehouse_id`;
- `InventoryBatch` does not carry direct `branch_id`, so branch comes through
  the verified warehouse and StockBalance context;
- refund stock restoration remains a future migration;
- public Inventory APIs remain unactivated;
- prescription validation remains separate from batch/expiry integrity;
- existing SQLAlchemy relationship overlap warnings remain separate cleanup.

## 26. Outcome

Migration 065 closes the POS checkout aggregate-stock gap for tracked Products.

Checkout can no longer sell expired-only batch stock or ignore batch
availability while aggregate StockBalance appears sufficient. Eligible batch
stock is allocated deterministically and inventory records remain transactionally
consistent with the Sale.
