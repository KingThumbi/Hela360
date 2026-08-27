# Migration 068 - Refund Stock Restoration and Operational UI

## 1. Migration Purpose

Migration 068 makes posted Sale refunds restore inventory truthfully and exposes
a focused operational refund workflow.

## 2. ADR Rules

Applied ADR-001, ADR-004, ADR-005, ADR-006, ADR-007, ADR-008, ADR-009, and
ADR-010.

Backend business rules remain authoritative. Frontend services and hooks expose
workflow contracts without implementing refund business logic.

## 3. Baseline

Baseline passed:

```text
venv/bin/python -m compileall app
npx tsc -b --pretty false
npm run build
```

The known Vite large-chunk warning remained.

## 4. Refund Models

`SaleRefund` fields include tenant, sale, branch, warehouse, till, cashier,
customer, `refund_number`, `status`, refund subtotal/discount/tax/total,
`stock_returned`, `reason`, `notes`, and timestamps.

`SaleRefundItem` fields include tenant, refund, sale, sale item, product, batch,
quantity, unit price, discount, tax, line total, `return_to_stock`,
`condition_note`, and `created_at`.

## 5. Existing Refund Behavior

The existing refund route created Refund and RefundItem rows, added a positive
return movement, created a negative SalePayment, and updated Sale refund status.

It did not restore StockBalance or InventoryBatch quantities.

## 6. Quantity Authority

Refund quantity authority remains backend-owned.

Remaining quantity is calculated from persisted posted `SaleRefundItem` rows:

```text
sale_item.quantity - sum(posted refund item quantity)
```

## 7. Full/Partial Support

Partial item quantities and full line refunds are supported.

Unsupported broad Sales History, receipt generation, and payment settlement
workflows were not added.

## 8. Original Stock Trace

Migration 065 sale movements were traceable by Sale/Product/Batch, but not by
SaleItem.

That was insufficient for repeated same-Product sale lines.

## 9. Same-Product Line Disposition

Added the narrow traceability contract:

```text
inventory_movements.sale_item_id -> sale_items.id
```

Existing rows may remain null. New checkout movements carry the generated
SaleItem ID before stock allocation.

## 10. Inventory Service Owner

Canonical inventory owner:

```text
app/services/tenant/inventory/refund_stock_service.py
```

`RefundService` orchestrates the refund; the inventory service restores stock.

## 11. Restoration Algorithm

For each stock-tracked refunded SaleItem:

1. load original negative sale movements for the SaleItem;
2. group original allocation by batch;
3. subtract prior positive refund movements for the SaleItem;
4. restore only remaining traceable quantity;
5. update StockBalance;
6. update original batches;
7. create positive refund return movements.

## 12. StockBalance Behavior

For tracked Products:

```text
quantity_on_hand += returned quantity
quantity_available = quantity_on_hand - quantity_reserved
```

Reserved quantity is not changed.

## 13. Batch Behavior

Returned quantity is restored to the original batch allocation.

Missing original batches are inventory integrity errors.

## 14. Expired Batch Behavior

Expired original batches are physically restored to their batch quantity.

Migration 065 sellability rules still exclude expired stock from future sales.

## 15. Movement Behavior

Return movements use:

```text
movement_type = sale_refund_return
reference_type = sale_refund
reference_id = refund.id
quantity = positive returned quantity
sale_item_id = original sale item
```

The Refund links back to the original Sale.

## 16. Valuation/Cost Disposition

Refund return movement `unit_cost` uses the original sale movement unit cost.

No COGS/accounting redesign was introduced.

## 17. Transaction Boundary

Refund rows, RefundItems, SalePayment adjustment, StockBalance, InventoryBatch,
InventoryMovement, and Sale status updates share one route transaction.

Any failure rolls the whole operation back.

## 18. Concurrency

The refund service locks Sale, SaleItems, original movements, prior refund
movements, StockBalance, and InventoryBatch rows with `with_for_update()` where
the underlying database supports it.

## 19. Repeated Refund Protection

Repeated refunds cannot exceed remaining item quantity or remaining paid amount.

Tests cover partial followed by partial, full after partial, and fully refunded
line rejection.

## 20. Tenant/Branch Isolation

Refund lookup and refund creation are tenant-scoped and branch-checked.

Cross-branch refunds return authorization errors.

## 21. Warehouse Authority

Refund stock restoration uses the original Sale/Warehouse and original
InventoryMovement allocation.

It does not use the cashier's current Till Warehouse.

## 22. TillShift Disposition

Original `Sale.till_shift_id` is unchanged.

Refund TillShift attribution remains a later financial/reconciliation concern.

## 23. Payment Reversal Disposition

The existing backend records a negative `SalePayment` using the original payment
method.

No external cash, card, M-Pesa, or bank reversal workflow was added. UI wording
says "Refund recorded" and "Inventory restored".

## 24. Sale Status Behavior

Partial refunds set `sale.status` to `partially_refunded`.

Fully refunded sales set `sale.status` to `refunded`.

`refund_status` mirrors partial/full refund state.

## 25. Serializer

The refund route still returns the verified compact refund result:

```text
id
refund_number
status
refund_total_amount
stock_returned
```

## 26. Refund Lookup/Read Contract

Added narrow read endpoint:

```text
GET /api/sales/<sale_id>
permission: sales.refund
```

`sale_id` can be the Sale ID or Sale number.

## 27. Frontend Types

`SaleItem` now includes optional refund projection fields:

```text
refunded_quantity
remaining_refundable_quantity
is_refundable
```

## 28. Service/Hook Changes

Added:

```text
salesService.getRefundableSale()
useRefundableSale()
```

`useRefundSale()` invalidates/refetches the exact branch-scoped refund lookup
key.

## 29. Query Scope

Refund lookup key is branch-scoped:

```text
tenant / tenantId / branch / branchId / sales / refund-lookup / saleId
```

No broad Sales list cache was activated.

## 30. Refund Route

Operational frontend route:

```text
/sales/refunds
permission: sales.refund
```

Existing navigation intent was reused.

## 31. Refund Page

The page supports:

- Sale number/ID lookup;
- Sale summary;
- refundable item quantities;
- reason;
- confirmation;
- submit;
- recorded refund result.

No Sales History browsing was added.

## 32. Quantity UX

The frontend blocks empty, zero, and over-remaining visible quantities.

The backend remains authoritative.

## 33. Confirmation

The confirmation states:

```text
This will record a refund and restore the selected quantities to inventory.
```

## 34. Success/Error Behavior

Success shows refund number/ID and amount, clears quantities, and refetches the
lookup projection.

Errors surface API messages while preserving the lookup context.

## 35. Financial Wording

The UI does not claim cash payout, card refund, M-Pesa reversal, receipt, or
credit-note generation.

## 36. Cache Invalidation

Refund success invalidates/refetches only the exact refund lookup query.

The page does not call QueryClient directly.

## 37. Prescription Disposition

Prescription return rules were not implemented.

This remains a future domain policy migration.

## 38. Backend Tests

Verified:

```text
app/api/tests/test_till_shift_contract.py: 61 passed
targeted regression set: 107 passed
auth suite: 129 passed
```

Covered stock restoration, original batch restoration, partial refund, repeated
refund protection, non-inventory products, missing batch rollback, untraceable
legacy movement rejection, permission, and branch isolation.

## 39. Frontend Verification

Verified:

```text
npx tsc -b --pretty false: PASS
npm run build: PASS
```

Known Vite large-chunk warning remained.

## 40. Local DB State

Alembic source head:

```text
7d9e2f4a6c8b
```

Local PostgreSQL was unavailable:

```text
16/main 5432 down
localhost:5432 - no response
```

`flask db current` and `flask db check` could not connect.

## 41. Runtime Smoke Result

Real local database checkout/refund smoke was not run because PostgreSQL was
down.

Targeted tests executed the full checkout-to-refund stock restoration flow
against isolated test databases.

## 42. Warnings

The four existing SQLAlchemy overlap warnings remain:

- `RolePermission.role`
- `RolePermission.permission`
- `UserRole.user`
- `UserRole.role`

Vite still warns about chunks larger than 500 kB.

## 43. Files Inspected

Inspected refund models, checkout stock service, refund service, sales API,
frontend Sales service/hooks/types/routes, ADRs, and prior Sales/POS migration
reviews.

## 44. Files Created

Created:

- `app/services/tenant/inventory/refund_stock_service.py`
- `migrations/versions/7d9e2f4a6c8b_add_inventory_movement_sale_item_trace.py`
- `frontend/src/hooks/queries/sales/useRefundableSale.ts`
- `frontend/src/features/sales/pages/RefundsPage.tsx`
- this review document

## 45. Files Modified

Modified inventory model, sales API, sale stock service, refund service, refund
tests, frontend Sales service/hooks/types/query keys, route permissions, router,
and Sales feature exports.

## 46. Remaining Blockers

Real PostgreSQL migration application is blocked until the local cluster is
started.

Historical sale movements without `sale_item_id` cannot be restored safely and
are rejected as untraceable inventory allocations.

## 47. Invariants Verified

Verified no over-refund, original batch restoration, StockBalance consistency,
positive refund movements, tenant/branch isolation, non-inventory no-op stock,
atomic rollback, and no fabricated receipt/payment reversal UI.

## 48. Rollback Boundary

The Alembic downgrade removes nullable `inventory_movements.sale_item_id`.

Runtime rollback is transaction-owned by the refund route.

## 49. Recommended Next Migration

Recommended next migration:

```text
Migration 069 - Refund Reconciliation Attribution and Real DB Upgrade Verification
```

That should apply pending migrations to PostgreSQL when available and address
refund TillShift/cash reconciliation semantics without changing inventory
restoration rules.
