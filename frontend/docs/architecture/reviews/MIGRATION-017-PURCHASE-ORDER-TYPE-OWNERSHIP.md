# Migration 017 - Purchase Order Type Ownership

## 1. Migration Purpose

Migration 017 determines whether Hela360 has a verified backend Purchase Order domain contract and whether canonical frontend Purchase Order types can be safely created.

This migration is inspection-only. No canonical Purchase Order frontend types were created because backend evidence is insufficient.

## 2. ADR Rules Applied

- ADR-001: services expose business operations and should not own reusable business entities.
- ADR-004: reusable entities, request DTOs, response DTOs, and enums belong under `src/types`, but only when a stable contract exists.
- ADR-008: public contracts must reflect real module ownership and must not export invented shared APIs.
- ADR-009: Purchase Order names should be explicit business names, but naming does not justify creating unsupported contracts.

## 3. Backend Files Searched

Searched and inspected:

- `app/models/`
- `app/api/`
- `app/schemas/`
- `app/serializers/`
- `app/services/tenant/procurement/`
- `app/services/tenant/inventory/`
- `app/services/tenant/finance/`
- `migrations/`
- `app/services/tenant/procurement/tests/`

Search terms included:

- `PurchaseOrder`
- `PurchaseOrderItem`
- `purchase_order`
- `purchase-order`
- `purchase orders`
- `PO`
- `po_number`
- `approve_purchase_order`
- `cancel_purchase_order`
- `receive_purchase_order`
- `procurement`
- `supplier_order`

## 4. Capability Classification

Purchase Order support classification:

```text
Frontend-only assumption
```

No backend Purchase Order model, table, migration, schema, serializer, route, service method, test, permission, numbering integration, status contract, approval workflow, receiving workflow, finance side effect, or Goods Receipt relationship was verified.

## 5. Models Found

No Purchase Order model was found.

No Purchase Order Item model was found.

Backend procurement currently has Supplier support:

- `app/models/supplier.py::Supplier`

Backend inventory persistence exists, but it is not a Purchase Order contract:

- `app/models/inventory.py::Warehouse`
- `app/models/inventory.py::InventoryBatch`
- `app/models/inventory.py::StockBalance`
- `app/models/inventory.py::InventoryMovement`

No verified model provides Purchase Order fields such as PO number, supplier order document, order date, expected delivery date, delivery location, currency, totals, approval fields, cancellation fields, ordered line items, received quantities, or outstanding quantities.

## 6. Migrations Found

No migration creates Purchase Order or Purchase Order Item tables.

Inspected migration evidence:

- `migrations/versions/19b1ccd035ac_initial_schema.py`
- `migrations/versions/8f3b7c2a9d10_add_suppliers.py`

The initial schema includes existing Product, Inventory, Sales/POS, tenant, branch, user, and related operational tables, but no Purchase Order aggregate.

The supplier migration is Supplier-only.

## 7. Schemas Found

No Purchase Order request schema was found under `app/schemas/`.

Only Supplier request/filter schemas were verified in the current procurement backend area:

- `CreateSupplierRequest`
- `UpdateSupplierRequest`
- `SupplierListFilters`

No verified schema exists for:

- `CreatePurchaseOrderRequest`
- `UpdatePurchaseOrderRequest`
- `ApprovePurchaseOrderRequest`
- `RejectPurchaseOrderRequest`
- `CancelPurchaseOrderRequest`
- `ReceivePurchaseOrderRequest`

## 8. Serializers Found

No Purchase Order serializer was found under `app/serializers/`.

Only Supplier serialization was verified:

- `app/serializers/supplier.py::serialize_supplier`

No response projection or envelope shape was verified for Purchase Orders.

## 9. Services Found

No backend Purchase Order service was found.

Verified procurement service files:

- `app/services/tenant/procurement/supplier_service.py` implements Supplier operations only.
- `app/services/tenant/procurement/procurement_service.py` is empty.
- `app/services/tenant/procurement/__init__.py` exports only `SupplierService` and `supplier_service`.

Verified inventory and finance service placeholders:

- `app/services/tenant/inventory/__init__.py` is empty.
- `app/services/tenant/finance/finance_service.py` is empty.
- `app/services/tenant/finance/__init__.py` is empty.

## 10. Routes Found

No backend Purchase Order route was found.

No route exists for:

- list Purchase Orders
- get Purchase Order
- create Purchase Order
- update draft Purchase Order
- submit Purchase Order
- approve Purchase Order
- reject Purchase Order
- cancel Purchase Order
- close Purchase Order
- receive against Purchase Order
- partial receipt
- supplier acknowledgment
- print/export Purchase Order

Frontend endpoint constants define `/purchase-orders`, `/purchase-orders/:id/approve`, and `/purchase-orders/:id/receive`, but endpoint constants alone are frontend assumptions, not backend route evidence.

## 11. Tests Found

No Purchase Order tests were found.

`app/services/tenant/procurement/tests/` contains Supplier contract tests only.

## 12. Supplier Relationship

Supplier backend support exists from Migration 010.

No backend Purchase Order relationship to Supplier was verified because no Purchase Order model or schema exists.

## 13. Branch Relationship

No Purchase Order branch ownership was verified.

Inventory and POS models include branch ownership, but no Purchase Order model specifies tenant, branch, warehouse, or delivery-location scope.

## 14. Warehouse And Delivery-Location Relationship

No Purchase Order warehouse or delivery-location relationship was verified.

Inventory models define warehouses and stock balances, but they do not represent supplier order documents.

## 15. Goods Receipt Relationship

No backend Goods Receipt relationship was verified.

Migration 016 classified Goods Receipt as a frontend-only assumption. This migration confirms that the Purchase Order side of the receiving relationship is also unsupported by backend evidence.

## 16. Finance Or Payable Side Effects

No backend finance, payable, supplier invoice, journal, accounting, or payment side effect was verified for Purchase Orders.

The finance service files inspected are empty placeholders.

## 17. Permissions

No backend Purchase Order permissions were verified.

Supplier permissions exist from Migration 010, but they do not authorize Purchase Order workflows.

## 18. Lifecycle And Status Values

No backend Purchase Order lifecycle or status values were verified.

The frontend service-local status union is speculative:

```text
DRAFT
SUBMITTED
APPROVED
ORDERED
PARTIALLY_RECEIVED
RECEIVED
CLOSED
CANCELLED
```

No canonical `PurchaseOrderStatus` was created.

## 19. Numbering Integration

No Purchase Order numbering service, `po_number` field, sequence, uniqueness constraint, or generated PO-number integration was verified.

## 20. Frontend Assumptions Found

Service-local definitions in `frontend/src/services/procurement/purchaseOrderService.ts`:

- `PurchaseOrderStatus`
- `PurchaseOrderItem`
- `PurchaseOrder`
- `CreatePurchaseOrderRequest`
- `UpdatePurchaseOrderRequest`
- `ApprovalRequest`
- `CancellationRequest`
- `PurchaseSummary`

Service-local methods assume:

- `submit`
- `approve`
- `cancel`
- `close`
- `receivingProgress`
- `summary`
- `print`
- `email`

The procurement service barrel currently re-exports these service-local type assumptions from `frontend/src/services/procurement/index.ts`.

Frontend hooks assume canonical shared types from `@/types/entities` and `@/types/requests`, but those canonical Purchase Order types do not exist.

## 21. Hook And Consumer Assumptions Found

Inspected frontend hooks under `frontend/src/hooks/queries/procurement/`:

- `usePurchaseOrders.ts`
- `usePurchaseOrder.ts`
- `useCreatePurchaseOrder.ts`
- `useApprovePurchaseOrder.ts`
- `useCancelPurchaseOrder.ts`
- `useReceivePurchaseOrder.ts`

Assumptions found:

- `PurchaseOrder` should be exported from `@/types/entities`.
- `CreatePurchaseOrderRequest` should be exported from `@/types/requests`.
- `ApprovePurchaseOrderRequest` should be exported from `@/types/requests`.
- `CancelPurchaseOrderRequest` should be exported from `@/types/requests`.
- `ReceivePurchaseOrderRequest` should be exported from `@/types/requests`.
- `purchaseOrderService.findById` exists.
- `purchaseOrderService.cancelPurchaseOrder` exists.
- `purchaseOrderService.receive` exists.
- `QUERY_KEYS.procurement.purchaseOrders` accepts pagination parameters.
- `purchaseOrderService.list(params)` returns `PaginatedResponse<PurchaseOrder>`.
- receiving a Purchase Order returns `GoodsReceipt`.

These assumptions are not backed by a verified backend contract.

## 22. PurchaseOrder Disposition

`PurchaseOrder` was not created under `frontend/src/types/entities/`.

Reason:

- no backend model
- no backend table
- no serializer
- no route
- no service method
- no stable entity shape
- no verified tenant or branch ownership

## 23. PurchaseOrderItem Disposition

`PurchaseOrderItem` was not created.

Reason:

- no line-item table
- no line-item schema
- no line-item serializer
- no verified ordered/received/outstanding quantity contract

## 24. Create And Update Request Disposition

`CreatePurchaseOrderRequest` was not created.

`UpdatePurchaseOrderRequest` was not created.

Reason:

- no create route
- no update route
- no request schema
- no verified client-owned payload fields
- no rules for server-owned PO number, calculated totals, status, audit fields, or tenant/branch ownership

## 25. Approval Request Disposition

`ApprovePurchaseOrderRequest` was not created.

`RejectPurchaseOrderRequest` was not created.

Reason:

- no submit route
- no approve route
- no reject route
- no approval schema
- no approval status transition contract
- no approved-by or audit behavior

Frontend `ApprovalRequest` remains a service-local assumption and was not promoted.

## 26. Cancellation Request Disposition

`CancelPurchaseOrderRequest` was not created.

Reason:

- no cancel route
- no cancellation schema
- no cancellation lifecycle contract
- no cancelled-by, cancelled-at, reason, or audit behavior

Frontend `CancellationRequest` remains a service-local assumption and was not promoted.

## 27. ReceivePurchaseOrderRequest Disposition

`ReceivePurchaseOrderRequest` was not created.

Reason:

- no backend Purchase Order receiving route
- no Goods Receipt backend contract
- no Inventory receipt workflow
- no verified request payload
- no verified partial receipt behavior
- no stock, batch, expiry, warehouse, payable, or audit side effects

## 28. PurchaseOrderStatus Disposition

`PurchaseOrderStatus` was not created under `frontend/src/types/enums/`.

Reason:

- no backend status field
- no finite backend value set
- no verified runtime status constants

## 29. PurchaseOrderSummary Disposition

`PurchaseOrderSummary` was not created.

Reason:

- no summary endpoint
- no summary serializer
- no response projection contract

The frontend service-local `PurchaseSummary` is not a verified shared response type.

## 30. Naming Resolution

`ReceivePurchaseOrderRequest`, `ReceiveGoodsRequest`, and `CreateGoodsReceiptRequest` were not aliased.

Current classification:

- `ReceivePurchaseOrderRequest`: speculative Purchase Order receiving operation.
- `ReceiveGoodsRequest`: no verified backend contract in the current source.
- `CreateGoodsReceiptRequest`: speculative Goods Receipt document creation request from frontend service-local code.
- `ReceiveStockRequest`: speculative Inventory workflow request from frontend inventory hooks.

These names may represent different workflow stages and must remain distinct until backend workflows define them.

## 31. Domain Boundary

Supplier owns supplier business identity.

Purchase Order would own supplier order documents, ordered line items, commercial terms, and approval lifecycle once implemented.

Goods Receipt would own physical receipt documents and receipt lines once implemented.

Inventory owns stock balances, batches, warehouses, and movement ledger entries.

Finance owns supplier invoices, payables, journals, and payment effects.

No Purchase Order types were placed in Supplier, Inventory, Goods Receipt, or Finance modules.

## 32. Files Created

- `frontend/docs/architecture/reviews/MIGRATION-017-PURCHASE-ORDER-TYPE-OWNERSHIP.md`

## 33. Files Modified

No source files were modified.

Only this inspection report was created.

## 34. Barrels Updated

No barrels were updated.

No unsupported type exports were added or removed during this migration because source implementation was stopped by missing backend evidence.

## 35. Compiler Errors Before

Baseline:

```text
199 TypeScript errors
```

## 36. Compiler Errors After

Post-migration:

```text
199 TypeScript errors
```

Net reduction:

```text
0
```

The unchanged count is expected for an inspection-only migration.

## 37. Procurement Diagnostics Before And After

Representative remaining Procurement diagnostics before and after:

- missing `PurchaseOrder` from `@/types/entities`
- missing `CreatePurchaseOrderRequest` from `@/types/requests`
- missing `ApprovePurchaseOrderRequest` from `@/types/requests`
- missing `CancelPurchaseOrderRequest` from `@/types/requests`
- missing `ReceivePurchaseOrderRequest` from `@/types/requests`
- `purchaseOrderService.findById` does not exist
- `purchaseOrderService.cancelPurchaseOrder` does not exist
- `purchaseOrderService.receive` does not exist
- `QUERY_KEYS.procurement.purchaseOrders` is called with parameters but accepts none
- `purchaseOrderService.list(params)` returns `ApiResponse<PurchaseOrder[]>`, not `PaginatedResponse<PurchaseOrder>`
- receiving hooks expect `GoodsReceipt`, which is also unsupported by backend evidence
- Purchase Requisition, Supplier Delivery, and Procurement Dashboard contracts remain unresolved

No Procurement diagnostics were intentionally fixed in this migration.

## 38. Newly Exposed Diagnostics

No newly exposed diagnostics were introduced.

## 39. New Diagnostics

No new diagnostics were introduced.

## 40. Remaining Procurement Blockers

- no backend Purchase Order model
- no backend Purchase Order Item model
- no Purchase Order migration/table
- no Purchase Order schemas
- no Purchase Order serializers
- no Purchase Order routes
- no Purchase Order service methods
- no Purchase Order permissions
- no Purchase Order lifecycle/status contract
- no Purchase Order numbering integration
- no Purchase Order receiving workflow
- no Goods Receipt backend contract
- no Purchase Requisition backend/frontend ownership decision
- no Supplier Delivery backend/frontend ownership decision
- no Procurement Dashboard service/export contract
- frontend service method names do not match hook expectations
- frontend query key shapes do not match hook calls
- frontend response-envelope assumptions do not match service return types

## 41. Invariants Verified

- No Purchase Order type was created without backend evidence.
- Procurement remains the future owner of Purchase Order contracts.
- Purchase Order and Goods Receipt remain distinct.
- Inventory remains the owner of stock balances, batches, warehouses, and movements.
- Supplier remains the owner of supplier identity.
- Finance remains the owner of payable/accounting projections.
- No request DTO was created without verified outbound fields.
- No response projection was created without a verified backend shape.
- No status values were promoted without backend-supported values.
- No shared types were moved into services or hooks.
- No service method was changed.
- No query key was changed.
- No invalidation behavior was changed.
- No backend source file was changed.
- Runtime behavior remains unchanged.
- Type-only import behavior was not modified.

## 42. Rollback Boundary

Rollback is limited to deleting this report:

```text
frontend/docs/architecture/reviews/MIGRATION-017-PURCHASE-ORDER-TYPE-OWNERSHIP.md
```

No runtime, backend, service, hook, query key, barrel, or type source file changes are part of this migration.

## 43. Backend Work Required

Before frontend canonical Purchase Order type ownership can proceed, the backend needs a stable Purchase Order contract covering at least:

- Purchase Order persistence model
- Purchase Order Item persistence model
- migration/table constraints
- tenant ownership
- branch or delivery-location ownership decision
- supplier relationship
- PO numbering strategy
- order and delivery date fields
- line item quantity and pricing fields
- totals calculation ownership
- lifecycle/status values
- request schemas
- response serializer
- route set
- service methods
- authorization permissions
- transaction boundaries
- inventory/Goods Receipt receiving side effects, if supported
- finance/payable side effects, if supported
- tests

## 44. Recommended Next Migration

Recommended next migration:

```text
Migration 018 - Purchase Requisition Type Ownership Inspection
```

Rationale:

Purchase Requisition diagnostics remain in the same Procurement backlog and should be classified before any Procurement source contract is promoted.
