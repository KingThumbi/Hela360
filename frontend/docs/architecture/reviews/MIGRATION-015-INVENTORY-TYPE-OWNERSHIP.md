# Migration 015 - Inventory Type Ownership

## 1. Migration Purpose

Migration 015 establishes canonical frontend ownership for verified Inventory shared types.

This migration is Inventory-only. It does not redesign the Inventory service facade, Product service facade, query keys, invalidation, stock workflows, transfers, adjustments, receipts, navigation, providers, or backend behavior.

## 2. ADR Rules Applied

- ADR-001: services consume shared types and do not own reusable business entities.
- ADR-004: business entities live under `src/types/entities`; request DTOs live under `src/types/requests`; response projections and enums exist only when supported by backend evidence.
- ADR-008: public barrels expose stable contracts and private implementation details remain private.
- ADR-009: type names use PascalCase and files use kebab-case.

## 3. Backend Inventory Models Verified

Verified models in `app/models/inventory.py`:

- `Warehouse`
- `InventoryBatch`
- `StockBalance`
- `InventoryMovement`

Verified migration evidence:

- `migrations/versions/19b1ccd035ac_initial_schema.py`

### Warehouse

- table: `warehouses`
- primary key: string UUID
- ownership: `tenant_id`, `branch_id`
- fields: `code`, `name`, `warehouse_type`, `is_active`
- uniqueness: `(tenant_id, branch_id, code)`
- directly returned by API: no verified endpoint

### InventoryBatch

- table: `inventory_batches`
- primary key: string UUID
- ownership: `tenant_id`, `warehouse_id`
- product relationship: `product_id`
- batch fields: `batch_number`, `expiry_date`, `manufacture_date`, `received_at`
- quantity fields: `quantity_on_hand`, `quantity_reserved`
- cost fields: `unit_cost`
- status: `status`, default `available`
- directly returned by API: no verified endpoint

### StockBalance

- table: `stock_balances`
- primary key: string UUID
- ownership: `tenant_id`, `branch_id`, `warehouse_id`
- product relationship: `product_id`
- quantity fields: `quantity_on_hand`, `quantity_reserved`, `quantity_available`
- valuation field: `avg_unit_cost`
- timestamps: `created_at`, `updated_at`
- uniqueness: `(tenant_id, warehouse_id, product_id)`
- directly returned by API: no verified endpoint

### InventoryMovement

- table: `inventory_movements`
- primary key: string UUID
- ownership: `tenant_id`, `branch_id`, `warehouse_id`
- product relationship: `product_id`
- batch relationship: nullable `batch_id`
- movement fields: `movement_type`, `quantity`, `unit_cost`, `unit_price`, `reference_type`, `reference_id`, `notes`, `created_by`
- timestamps: `created_at`, `updated_at`
- directly returned by API: no verified endpoint

## 4. Backend Inventory Endpoints Verified

`app/api/inventory.py` is currently empty.

No dedicated backend inventory route was verified for:

- list inventory
- get inventory item
- stock balance lookup
- inventory summary
- inventory valuation
- stock adjustment
- stock transfer
- stock receipt
- movement history
- low-stock list
- expiring-stock list
- warehouse inventory
- branch inventory

Partial evidence exists for internal POS stock behavior in `app/api/sales.py` and `app/services/tenant/pos/refund_service.py`:

- sale checkout subtracts from `StockBalance`
- sale void restores `StockBalance`
- sale/refund workflows create `InventoryMovement`

These are internal Sales/POS workflows, not public Inventory API contracts.

## 5. Product Versus Inventory Boundary

Product owns product identity, descriptive fields, commercial prices, product configuration, and inventory-control flags such as `track_inventory`, `track_batches`, `track_expiry`, `reorder_level`, and `reorder_qty`.

Inventory owns stock quantities, stock location, warehouse/branch balances, batches, movement ledger entries, and valuation fields.

`frontend/src/services/products/inventoryService.ts` is the current runtime service for inventory operations, but it lives under the Product service directory. This migration preserves runtime placement and documents that a later facade migration should decide whether Inventory deserves its own service boundary.

## 6. Serializer Response Shapes

No public backend Inventory serializer was verified.

Canonical entity field names therefore follow backend persistence snake_case rather than the current frontend service-local camelCase assumptions.

Decimal-like quantity and valuation fields are represented as strings to match the established serializer strategy used by Product and Customer migrations when backend numeric fields are exposed to JSON.

## 7. Request Schemas

No verified backend request schemas or routes exist for:

- `AdjustStockRequest`
- `TransferStockRequest`
- `ReceiveStockRequest`
- `CreateInventoryAdjustmentRequest`
- `InventoryAdjustmentRequest`
- stock count requests

No canonical Inventory request DTOs were created.

## 8. Current Frontend Inventory Definitions Found

Service-local definitions found in `frontend/src/services/products/inventoryService.ts`:

- `InventoryItem`
- `InventoryAdjustmentRequest`
- `BranchTransferRequest`
- `ReservationRequest`
- `ReleaseReservationRequest`
- `StockMovement`
- `Batch`
- `InventoryValuation`

Product service-local inventory-shaped definitions found in `frontend/src/services/products/productService.ts`:

- `InventorySummary`
- `StockMovement`

Product service barrel unsupported exports found in `frontend/src/services/products/index.ts`:

- `InventoryAdjustment`
- `InventoryMovement`
- `InventorySummary`
- `CreateInventoryAdjustmentRequest`
- `StockTransferRequest`

Hook imports found in `frontend/src/hooks/queries/inventory/*`:

- `InventoryItem`
- `StockMovement`
- `StockAdjustment`
- `StockTransfer`
- `StockCount`
- `GoodsReceipt`
- `AdjustStockRequest`
- `TransferStockRequest`
- `ReceiveStockRequest`
- `StockCountRequest`

## 9. Duplicate Contracts Found

Removed from service ownership:

- `InventoryItem`
- `StockMovement`

`StockMovement` was not preserved as a canonical alias. The backend model is `InventoryMovement`, so `useStockMovements` now consumes the canonical `InventoryMovement` type.

Local, unverified workflow request types remain service-local:

- `InventoryAdjustmentRequest`
- `BranchTransferRequest`
- `ReservationRequest`
- `ReleaseReservationRequest`

They were not exported through shared barrels.

## 10. Canonical Inventory Entities

Created:

- `frontend/src/types/entities/inventory-item.ts`
- `frontend/src/types/entities/inventory-movement.ts`

`InventoryItem` represents the stock balance business object backed by `app/models/inventory.py::StockBalance`.

`InventoryMovement` represents the movement ledger business object backed by `app/models/inventory.py::InventoryMovement`.

## 11. Canonical Request DTOs

No Inventory request DTOs were canonicalized because no public backend inventory workflow route or request schema was verified.

## 12. Canonical Response Projections

No Inventory response projections were canonicalized.

`InventorySummary`, `InventoryValuation`, `LowStockSummary`, and `ExpiringStockSummary` do not have verified backend Inventory response projections.

## 13. InventoryMovementType Disposition

`InventoryMovementType` was not created.

Backend movement values are currently raw strings created by Sales/POS workflows, with verified values including:

- `sale`
- `sale_void`
- `sale_refund_return`

No authoritative finite movement-type contract was found.

## 14. InventoryAdjustmentType Disposition

`InventoryAdjustmentType` was not created.

No verified backend stock adjustment route, schema, model, or finite adjustment type set was found.

## 15. InventorySummary Disposition

`InventorySummary` was not canonicalized.

The Product service has a local product-inventory method type for an unverified `/products/{id}/inventory` endpoint. That local shape was renamed to `ProductInventorySummary` to avoid implying shared Inventory ownership.

## 16. Service Ownership Observed

Current runtime service owner:

```text
frontend/src/services/products/inventoryService.ts
```

Current public barrel:

```text
frontend/src/services/products/index.ts
```

No `frontend/src/services/inventory/` service facade exists in the current source tree.

The runtime service location remains unchanged.

## 17. Files Inspected

- `app/models/inventory.py`
- `app/models/product.py`
- `app/models/pos.py`
- `app/models/__init__.py`
- `app/api/inventory.py`
- `app/api/sales.py`
- `app/api/products.py`
- `app/services/tenant/inventory/`
- `app/services/tenant/pos/inventory_service.py`
- `app/services/tenant/pos/refund_service.py`
- `app/schemas/`
- `app/serializers/`
- `migrations/versions/19b1ccd035ac_initial_schema.py`
- `frontend/src/services/products/inventoryService.ts`
- `frontend/src/services/products/productService.ts`
- `frontend/src/services/products/index.ts`
- `frontend/src/hooks/queries/inventory/*`
- `frontend/src/features/inventory/`
- `frontend/src/features/products/`
- `frontend/src/features/procurement/`
- `frontend/src/types/entities/*`
- `frontend/src/types/requests/*`
- `frontend/src/types/responses/*`
- `frontend/src/types/enums/*`
- Canonical frontend architecture review
- Migration 013 and 014 review documents
- ADR-001, ADR-004, ADR-008, ADR-009

## 18. Files Created

- `frontend/src/types/entities/inventory-item.ts`
- `frontend/src/types/entities/inventory-movement.ts`
- `frontend/docs/architecture/reviews/MIGRATION-015-INVENTORY-TYPE-OWNERSHIP.md`

## 19. Files Modified

- `frontend/src/types/entities/index.ts`
- `frontend/src/services/products/inventoryService.ts`
- `frontend/src/services/products/productService.ts`
- `frontend/src/services/products/index.ts`
- `frontend/src/hooks/queries/inventory/useStockMovements.ts`

No backend files were modified.

## 20. Service-Local Definitions Removed

Removed shared entity ownership from `inventoryService.ts`:

- `InventoryItem`
- `StockMovement`

Replaced with canonical imports:

- `InventoryItem`
- `InventoryMovement`

Removed Product service-local `StockMovement`.

Renamed Product service-local `InventorySummary` to `ProductInventorySummary` because no canonical Inventory summary projection is verified.

## 21. Barrels Updated

`frontend/src/types/entities/index.ts` now exports:

- `InventoryItem`
- `InventoryMovement`

`frontend/src/services/products/index.ts` now re-exports only supported inventory shared types from `@/types`:

- `InventoryItem`
- `InventoryMovement`

Unsupported Product service-barrel inventory exports were removed:

- `InventoryAdjustment`
- `InventorySummary`
- `CreateInventoryAdjustmentRequest`
- `StockTransferRequest`

## 22. Imports Migrated

- `inventoryService.ts` imports canonical `InventoryItem` and `InventoryMovement`.
- `productService.ts` imports canonical `InventoryMovement`.
- `useStockMovements.ts` imports canonical `InventoryMovement`.

`useInventory.ts` and `useStockItem.ts` already imported `InventoryItem` from the canonical entity barrel.

## 23. Backend/Frontend Naming Strategy

No public Inventory serializer is verified. Canonical entities use backend persistence snake_case.

The previous service-local `InventoryItem` and `StockMovement` shapes used camelCase fields without a verified service mapper. That mismatch is documented and left as a future service/API mapping decision.

## 24. Compiler Errors Before

Baseline:

```text
207 TypeScript errors
```

## 25. Compiler Errors After

Post-migration:

```text
199 TypeScript errors
```

Command:

```bash
npx tsc -b --pretty false 2>&1 | grep -c "error TS"
```

## 26. Net Reduction

```text
8 fewer TypeScript errors
```

## 27. Inventory Diagnostics Before And After

Before:

- missing `InventoryItem` export from `@/types/entities`: 2 diagnostics
- missing `StockMovement` export from `@/types/entities`: 1 diagnostic
- invalid Product service-barrel inventory exports: 5 diagnostics

After:

- missing `InventoryItem` export: 0 diagnostics
- missing `StockMovement` export: 0 diagnostics, because the hook now uses canonical `InventoryMovement`
- invalid Product service-barrel inventory exports: 0 diagnostics

## 28. Newly Exposed Mismatches

No new Inventory response-envelope diagnostics were introduced by this migration.

The remaining Inventory diagnostics are pre-existing deferred workflow/service/query-key mismatches.

## 29. Remaining Inventory Blockers

- `StockAdjustment` has no canonical entity because no backend adjustment model/API was verified.
- `AdjustStockRequest` has no canonical request because no backend adjustment route/schema was verified.
- `inventoryService.adjustStock` does not exist.
- `GoodsReceipt` is Procurement-owned and remains unresolved outside this migration.
- `ReceiveStockRequest` has no canonical request because no backend stock receipt route/schema was verified.
- `inventoryService.receiveStock` does not exist.
- `StockCount` and `StockCountRequest` have no verified backend workflow.
- `inventoryService.stockCount` does not exist.
- `StockTransfer` and `TransferStockRequest` have no verified backend transfer workflow.
- `inventoryService.transferStock` does not exist.
- `inventoryService.findById` does not exist.
- `useInventory` and `useStockMovements` still pass params to query-key functions that expect no arguments.
- `inventoryService.stockMovements` does not exist; current service method is `movements`.
- dedicated backend Inventory API endpoints are absent in `app/api/inventory.py`.

## 30. Runtime Behavior

Runtime behavior is unchanged.

No endpoint, service method, query key, invalidation helper, hook behavior, response unwrapping, mapping, or backend source was changed.

## 31. Invariants Verified

- Inventory entities have canonical ownership under `src/types/entities`.
- No Inventory request DTO was created without backend support.
- No Inventory response projection was created without backend support.
- No Inventory enum-like runtime value was created without backend support.
- Product and Inventory ownership remain distinct.
- Product service barrel no longer owns unsupported Inventory contracts.
- Inventory service consumes canonical entity types.
- Inventory hooks consume canonical entity types where backend-supported.
- Shared Inventory entity contracts are no longer defined in `inventoryService.ts`.
- Type-only imports and exports were used for shared contracts.
- No Inventory service method changed.
- No query key changed.
- No invalidation behavior changed.
- No backend file changed.
- No unrelated frontend domain behavior changed.

## 32. Rollback Boundary

Rollback is limited to the new Inventory entity files, entity barrel exports, inventory/product service type imports, Product service-barrel inventory type exports, the `useStockMovements` type import, and this report.

## 33. Recommended Next Migration

Recommended next migration:

```text
Migration 016 - Procurement Goods Receipt Type Ownership
```
