# Migration 040 - Inventory Capability Disposition

## 1. Migration Purpose

Migration 040 aligns the public Inventory frontend boundary with verified
backend capabilities.

This migration is capability-disposition-first. It does not create Inventory
routes, workflow DTOs, entities, service methods, query keys, invalidation
rules, fake query data, or backend contracts.

## 2. ADR Rules Applied

- ADR-001: public service boundaries must expose verified business operations.
- ADR-002: hooks must not issue unsupported network requests.
- ADR-003: query keys remain centralized and unchanged.
- ADR-004: Inventory workflow types must not be fabricated.
- ADR-005: unsupported operations reject without presentation behavior.
- ADR-006: tenant/branch context remains backend/API-layer owned.
- ADR-008: public module boundaries expose only stable contracts.
- ADR-009: Inventory names remain business-oriented but unsupported names are
  not made public.
- ADR-010: workflows must map to backend-supported operations.

## 3. Compiler Baseline

Pre-migration command:

```bash
cd /home/thumbi/Hela360/frontend
npx tsc -b --pretty false 2>&1 | tee /tmp/hela360-migration-040-errors.txt
grep -c "error TS" /tmp/hela360-migration-040-errors.txt
```

Pre-migration total:

```text
30 TypeScript errors
```

## 4. Initial Inventory Diagnostics

Direct Inventory diagnostics before this migration:

```text
16 errors
```

| Category | Count |
| --- | ---: |
| Missing unsupported workflow/entity/request exports | 8 |
| Missing Inventory service methods | 6 |
| Inventory query-key parameter mismatches | 2 |

Affected files:

- `useAdjustStock.ts`
- `useInventory.ts`
- `useReceiveStock.ts`
- `useStockCount.ts`
- `useStockItem.ts`
- `useStockMovements.ts`
- `useTransferStock.ts`

## 5. Backend Capability Matrix

Current active app-factory registrations in `app/__init__.py`:

```text
auth, health, products, customers, sales, suppliers
```

`app/api/inventory.py` exists on disk but is not registered in the active
application factory. It did not provide registered Inventory API evidence.

| Capability | Model | Schema | Serializer | Route | Service | Test | Classification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Inventory balance/list | `StockBalance` | None | None | None registered | None | None | Partial persistence only |
| Inventory item detail | `StockBalance` | None | None | None registered | None | None | Partial persistence only |
| Inventory movements | `InventoryMovement` | None | None | None registered | POS/Sales internal writes only | None | Partial persistence only |
| Stock adjustment | None verified | None | None | None registered | None | None | Frontend-only assumption |
| Stock receipt | None verified | None | None | None registered | None | None | Frontend-only assumption |
| Stock transfer | None verified | None | None | None registered | None | None | Frontend-only assumption |
| Stock count | None verified | None | None | None registered | None | None | Unsupported |
| Goods Receipt integration | None | None | None | None registered | None | None | Unsupported |
| Low-stock reporting | `StockBalance` partial | None | None | None registered | None | None | Partial persistence only |
| Expiry reporting | `InventoryBatch` partial | None | None | None registered | None | None | Partial persistence only |

Internal POS/Sales code updates `StockBalance` and creates
`InventoryMovement` rows during sales and refunds. That is not a public
Inventory API contract.

## 6. InventoryItem Disposition

`InventoryItem` remains canonical under `src/types/entities`.

It is a truthful persistence-backed entity from Migration 015, but no active
registered frontend API currently exposes it through an Inventory capability.

## 7. InventoryMovement Disposition

`InventoryMovement` remains canonical under `src/types/entities`.

It is persistence-backed and internally written by Sales/POS backend workflows,
but no active registered Inventory movement list API is verified.

## 8. Inventory List/Detail Disposition

Inventory list and item-detail hooks are not publicly operational.

Private hooks retained:

- `useInventory`
- `useStockItem`

Disposition:

- removed from public Inventory hook barrel;
- private queries are disabled with `enabled: false`;
- private queries use existing Inventory query keys only;
- no service request is issued;
- no fake data is returned.

## 9. Stock Adjustment Disposition

Stock adjustment is unsupported as a public frontend capability.

Private hook retained:

- `useAdjustStock`

Disposition:

- removed from public Inventory hook barrel;
- mutation rejects explicitly;
- no service request is issued;
- no invalidation runs;
- no `StockAdjustment` or `AdjustStockRequest` type was created.

## 10. Stock Receipt Disposition

Stock receipt is unsupported as a public frontend capability.

Private hook retained:

- `useReceiveStock`

Disposition:

- removed from public Inventory hook barrel;
- mutation rejects explicitly;
- no service request is issued;
- no invalidation runs;
- no `ReceiveStockRequest` type was created.

## 11. Stock Transfer Disposition

Stock transfer is unsupported as a public frontend capability.

Private hook retained:

- `useTransferStock`

Disposition:

- removed from public Inventory hook barrel;
- mutation rejects explicitly;
- no service request is issued;
- no invalidation runs;
- no `StockTransfer` or `TransferStockRequest` type was created.

## 12. Stock Count Disposition

Stock count is unsupported as a public frontend capability.

Private hook retained:

- `useStockCount`

Disposition:

- removed from public Inventory hook barrel;
- mutation rejects explicitly;
- no service request is issued;
- no invalidation runs;
- no `StockCount` or `StockCountRequest` type was created.

## 13. Goods Receipt Disposition

Goods Receipt remains unsupported and future Procurement-owned.

Migration 016 classified Goods Receipt as a frontend-only assumption. Migration
039 kept Procurement Goods Receipt files private and blocked. This migration
removed the remaining Inventory hook dependency on `GoodsReceipt` without
creating a Goods Receipt entity or redirecting the operation to
`InventoryMovement`.

## 14. Low-Stock And Expiry Disposition

Low-stock and expiry reporting remain unsupported as public Inventory
capabilities.

`InventoryBatch` and `StockBalance` persistence can support future designs, but
no registered API, serializer, response projection, or hook contract was
verified in this migration.

## 15. Frontend Type Inventory

Verified canonical types preserved:

- `InventoryItem`
- `InventoryMovement`

Unsupported workflow/request symbols not created:

- `InventoryAdjustment`
- `StockAdjustment`
- `StockTransfer`
- `StockCount`
- `AdjustStockRequest`
- `ReceiveStockRequest`
- `TransferStockRequest`
- `StockCountRequest`
- `GoodsReceipt`
- `GoodsReceiptItem`

No type barrel was modified because `InventoryItem` and `InventoryMovement`
were already correct and the failing imports were removed from blocked hooks.

## 16. Service Inventory

| Service | File | Public before | Public after | HTTP calls | Backend match |
| --- | --- | --- | --- | --- | --- |
| `inventoryService` | `services/products/inventoryService.ts` | Exported through `services/products` | Not public through Product barrel | Yes, to Inventory endpoint constants | No registered backend route |
| `stockService` | None | No | No | N/A | None |
| Inventory facade | None | No | No | N/A | None |

The existing `inventoryService` file remains preserved as private unfinished
source. No Product service runtime behavior was changed.

## 17. Hook Inventory

| Hook | Public before | Public after | Runtime behavior after |
| --- | --- | --- | --- |
| `useInventory` | Yes | No | Disabled query; no service call |
| `useStockItem` | Yes | No | Disabled query; no service call |
| `useStockMovements` | Yes | No | Disabled query; no service call |
| `useAdjustStock` | Yes | No | Rejecting mutation; no service call or invalidation |
| `useReceiveStock` | Yes | No | Rejecting mutation; no service call or invalidation |
| `useTransferStock` | Yes | No | Rejecting mutation; no service call or invalidation |
| `useStockCount` | Yes | No | Rejecting mutation; no service call or invalidation |

## 18. Active Page Consumers

Current route evidence:

- `frontend/src/app/router.tsx` routes `/inventory` to
  `<div>Inventory Module (Coming Soon)</div>`.
- `frontend/src/features/inventory/pages/InventoryPage.tsx` is zero lines.
- `frontend/src/navigation/navigation.ts` contains Inventory navigation
  metadata, but it was not modified.

No active page, route, or feature consumer imports the Inventory hook barrel or
Inventory service runtime.

## 19. Service Barrel Before And After

Before:

- `frontend/src/services/products/index.ts` exported `inventoryService` as a
  transitional Inventory runtime from the Product service barrel.

After:

- the Product service barrel exports only `productService`;
- no public Inventory runtime service is exposed;
- no Product service implementation behavior was changed.

There is no `frontend/src/services/inventory/index.ts` file in the current tree.

## 20. Hook Barrel Before And After

Before:

- Inventory hook barrel exported list/detail/movements queries and stock
  workflow mutations.

After:

```typescript
export {};
```

No unsupported Inventory hook is publicly operational.

## 21. Unsupported Deep-Import Behavior

Searches found no active external imports of Inventory hooks or
`inventoryService`.

Private unsupported query hooks remain importable only by direct path. If
directly called, query hooks are disabled with `enabled: false` and
`retry: false`. Private unsupported mutation hooks reject explicitly and do not
run invalidation.

## 22. Placeholder-Page Disposition

The routed Inventory page remains a placeholder. It does not import Inventory
hooks and does not trigger unsupported network calls.

Routes and navigation entries were intentionally left unchanged.

## 23. Type-Barrel Disposition

No type barrel was modified.

Preserved exports:

- `InventoryItem`
- `InventoryMovement`

No unsupported workflow type export was added.

## 24. Query-Key Disposition

`frontend/src/lib/queryKeys.ts` was not modified.

Private disabled hooks use existing Inventory query-key factories only:

- `QUERY_KEYS.inventory.list()`
- `QUERY_KEYS.inventory.detail(id)`
- `QUERY_KEYS.inventory.movements()`

No keys were added for adjustments, receipts, transfers, or stock counts.

## 25. Invalidation Disposition

`frontend/src/lib/queryInvalidation.ts` was not modified.

Unsupported Inventory mutations no longer call
`invalidateInventoryOperations` because they never perform a successful backend
mutation.

## 26. Product Boundary Confirmation

Product remains distinct from Inventory.

`productService` remains publicly exported from `@/services/products`. Product
runtime behavior was not modified. Inventory stock fields were not moved into
Product, and the Product service implementation was not changed.

## 27. Procurement Boundary Confirmation

Migration 039 remains intact.

Procurement public service and hook barrels remain empty. Goods Receipt remains
unsupported and private; no Procurement file was modified by Migration 040.

## 28. Files Inspected

Architecture and reports:

- ADR-001 through ADR-006
- ADR-008 through ADR-010
- Migration 015
- Migration 016
- Migration 038
- Migration 039

Backend:

- `app/__init__.py`
- `app/api/`
- `app/models/inventory.py`
- `app/schemas/`
- `app/serializers/`
- `app/services/tenant/inventory/`
- `app/services/tenant/procurement/`
- `app/services/tenant/pos/`
- `app/auth/`
- `migrations/`

Frontend:

- `frontend/src/hooks/queries/inventory/`
- `frontend/src/services/products/inventoryService.ts`
- `frontend/src/services/products/index.ts`
- `frontend/src/features/inventory/`
- `frontend/src/app/router.tsx`
- `frontend/src/navigation/navigation.ts`
- `frontend/src/types/`
- Procurement and Supplier boundaries for confirmation

## 29. Files Created

- `frontend/docs/architecture/reviews/MIGRATION-040-INVENTORY-CAPABILITY-DISPOSITION.md`

## 30. Files Modified

- `frontend/src/hooks/queries/inventory/index.ts`
- `frontend/src/hooks/queries/inventory/useAdjustStock.ts`
- `frontend/src/hooks/queries/inventory/useInventory.ts`
- `frontend/src/hooks/queries/inventory/useReceiveStock.ts`
- `frontend/src/hooks/queries/inventory/useStockCount.ts`
- `frontend/src/hooks/queries/inventory/useStockItem.ts`
- `frontend/src/hooks/queries/inventory/useStockMovements.ts`
- `frontend/src/hooks/queries/inventory/useTransferStock.ts`
- `frontend/src/services/products/index.ts`

## 31. Compiler Results

Before:

```text
30
```

After:

```text
14
```

Net reduction:

```text
16
```

`npm run build` still exits with code `2` because the remaining dashboard,
strict TypeScript, and administration diagnostics still stop `tsc -b`. Vite
does not run.

## 32. Inventory Diagnostics Before And After

Before:

```text
16 direct Inventory diagnostics
```

After:

```text
0 direct Inventory diagnostics
```

Searches for Inventory diagnostic terms after migration returned no compiler
diagnostics.

## 33. Newly Exposed Diagnostics

None.

The post-migration diagnostic set is a strict subset of the pre-migration set.

## 34. New Diagnostics

None.

## 35. Remaining Inventory Blockers

Inventory can become operational only after backend support exists for one or
more public Inventory capabilities.

Required backend evidence:

- registered blueprint/routes;
- request schemas for workflows;
- serializers or response projections;
- tenant/branch authorization behavior;
- service contract;
- pagination/envelope contract;
- tests.

## 36. Runtime Behavior Confirmation

The public Inventory hook barrel exports no hooks.

No public Inventory runtime service is exported.

Private unsupported Inventory query hooks are inert and do not automatically
fetch or retry. Private unsupported mutation hooks reject and do not invalidate.

No fake data is returned.

## 37. Invariants Verified

- Inventory public APIs expose no unsupported backend capability.
- `InventoryItem` and `InventoryMovement` remain canonical persistence entities.
- Unsupported Inventory workflows are not public.
- Unsupported query hooks do not issue automatic requests.
- Unsupported mutation hooks issue no requests and no invalidation.
- Goods Receipt remains Procurement-owned and unsupported.
- Missing workflow DTOs were not fabricated.
- No fake query or mutation data is returned.
- Product ownership remains distinct.
- Procurement Migration 039 remains intact.
- Query keys are unchanged.
- Invalidation policy is unchanged.
- Routes and navigation are unchanged.
- Backend files are unchanged.
- Future Inventory source is preserved where safe.

## 38. Rollback Boundary

Rollback is limited to:

- restoring the previous exports in `hooks/queries/inventory/index.ts`;
- restoring the previous private Inventory hook implementations;
- restoring the previous transitional `inventoryService` export in
  `services/products/index.ts`;
- deleting this report.

No backend rollback is required.

## 39. Recommended Next Migration

Recommended Migration 041:

```text
Dashboard Response Boundary And Facade Naming
```

Reason:

The remaining compiler baseline is 14 errors. Dashboard is now the largest
coherent remaining cluster with 8 diagnostics: four stale `@/types/apis`
imports and four `DashboardService` method-name mismatches.

