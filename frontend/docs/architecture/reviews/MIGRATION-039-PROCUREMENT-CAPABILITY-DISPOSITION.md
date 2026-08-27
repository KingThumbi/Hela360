# Migration 039 - Procurement Capability Disposition

## 1. Migration Purpose

Migration 039 aligns the public Procurement frontend boundary with verified
backend capabilities.

The migration is capability-disposition-first. It does not create Procurement
entities, requests, responses, services, query keys, invalidation rules, routes,
navigation entries, backend routes, or fake query data.

## 2. ADR Rules Applied

- ADR-001: public service facades must expose verified business operations and
  hide speculative backend details.
- ADR-002: hooks must communicate through services and must not issue
  unsupported requests.
- ADR-003: query keys remain centralized; no new keys were added.
- ADR-004: reusable business types must be canonical and must not be fabricated
  from frontend-only assumptions.
- ADR-005: unsupported operations surface errors without presentation logic.
- ADR-006: tenant and branch behavior remains backend/API-layer owned.
- ADR-007: backend enforcement remains authoritative.
- ADR-008: public module boundaries expose only stable public contracts.
- ADR-009: naming follows business concepts but does not justify unsupported
  contracts.
- ADR-010: workflows must map to backend-supported business operations.

## 3. Compiler Baseline

Pre-migration command:

```bash
cd /home/thumbi/Hela360/frontend
npx tsc -b --pretty false 2>&1 | tee /tmp/hela360-migration-039-errors.txt
grep -c "error TS" /tmp/hela360-migration-039-errors.txt
```

Pre-migration total:

```text
63 TypeScript errors
```

## 4. Initial Procurement Diagnostics

Direct Procurement diagnostics before this migration:

```text
33 errors
```

Categories:

| Category | Count |
| --- | ---: |
| Missing canonical Procurement type/request exports | 16 |
| Missing Procurement service methods/services | 9 |
| Procurement query-key mismatches | 6 |
| Procurement response-envelope mismatch | 1 |
| Unsupported dashboard placeholder residue | 1 |

Affected files:

- `useApprovePurchaseOrder.ts`
- `useCancelPurchaseOrder.ts`
- `useCreatePurchaseOrder.ts`
- `useGoodsReceipt.ts`
- `useGoodsReceipts.ts`
- `useProcurementDashboard.ts`
- `usePurchaseOrder.ts`
- `usePurchaseOrders.ts`
- `usePurchaseRequisition.ts`
- `usePurchaseRequisitions.ts`
- `useReceivePurchaseOrder.ts`
- `useSupplierDeliveries.ts`

## 5. Backend Capability Matrix

Current active app-factory registrations in `app/__init__.py`:

```text
auth, health, products, customers, sales, suppliers
```

`app/api/inventory.py` exists on disk but is not registered in the active
application factory. No active Procurement blueprint is registered.

| Capability | Model | Schema | Serializer | Route | Service | Test | Classification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Supplier management | `Supplier` | Supplier schemas | `serialize_supplier` | Registered `/api/suppliers` routes | `supplier_service` | Supplier contract tests | Confirmed backend capability |
| Purchase Orders | None | None | None | None registered | Frontend-only service; no backend service | None | Frontend-only assumption |
| Purchase Requisitions | None | None | None | None registered | None | None | Unsupported |
| Goods Receipts | None | None | None | None registered | Frontend-only service; no backend service | None | Frontend-only assumption |
| Supplier Deliveries | None | None | None | None registered | None | None | Unsupported |
| Procurement Dashboard | None | None | None | None registered | None | None | Unsupported |

Searches for Purchase Order, Purchase Requisition, Goods Receipt, Supplier
Delivery, and Procurement Dashboard backend terms returned no supporting
contract evidence in `app/api`, `app/models`, `app/schemas`, `app/serializers`,
`app/services/tenant/procurement`, `app/services/tenant/inventory`,
`app/services/tenant/finance`, `app/auth`, or `migrations`.

## 6. Supplier Capability Confirmation

Supplier remains the only verified procurement-area backend capability.

Supplier remains publicly exposed through:

- `@/services/suppliers`
- `@/hooks/queries/suppliers`
- `@/types/entities/supplier`
- `@/types/requests/create-supplier-request`
- `@/types/requests/update-supplier-request`

No Supplier source, behavior, query keys, or type contracts were modified.

## 7. Purchase Order Disposition

Purchase Orders are not publicly operational.

Frontend files retained privately:

- `services/procurement/purchaseOrderService.ts`
- `hooks/queries/procurement/usePurchaseOrders.ts`
- `hooks/queries/procurement/usePurchaseOrder.ts`
- `hooks/queries/procurement/useCreatePurchaseOrder.ts`
- `hooks/queries/procurement/useApprovePurchaseOrder.ts`
- `hooks/queries/procurement/useReceivePurchaseOrder.ts`
- `hooks/queries/procurement/useCancelPurchaseOrder.ts`

Disposition:

- removed from public Procurement service barrel;
- removed from public Procurement hook barrel;
- private query hooks are disabled and do not issue requests;
- private mutation hooks reject explicitly and do not invalidate caches;
- no Purchase Order entity or request DTO was created.

Backend work required to activate: model, schema, serializer, registered routes,
service contract, authorization, tests, and response envelope.

## 8. Purchase Requisition Disposition

Purchase Requisitions are unsupported.

Frontend files retained privately:

- `hooks/queries/procurement/usePurchaseRequisitions.ts`
- `hooks/queries/procurement/usePurchaseRequisition.ts`

Disposition:

- removed from public Procurement hook barrel;
- private query hooks are disabled and do not issue requests;
- no service, query key, entity, or request DTO was created.

## 9. Goods Receipt Disposition

Goods Receipts are not publicly operational.

Frontend files retained privately:

- `services/procurement/goodsReceiptService.ts`
- `hooks/queries/procurement/useGoodsReceipts.ts`
- `hooks/queries/procurement/useGoodsReceipt.ts`

Disposition:

- removed from public Procurement service barrel;
- removed from public Procurement hook barrel;
- private query hooks are disabled and do not issue requests;
- no Goods Receipt entity or request DTO was created.

The remaining compiler reference to `GoodsReceipt` after this migration is in
`hooks/queries/inventory/useReceiveStock.ts`, which belongs to the Inventory
workflow cluster and was intentionally not modified.

## 10. Supplier Delivery Disposition

Supplier Deliveries are unsupported.

Frontend file retained privately:

- `hooks/queries/procurement/useSupplierDeliveries.ts`

Disposition:

- removed from public Procurement hook barrel;
- private query hook is disabled and does not issue requests;
- no service, query key, entity, request DTO, or response projection was created.

## 11. Procurement Dashboard Disposition

Procurement Dashboard is unsupported.

Frontend file retained privately:

- `hooks/queries/procurement/useProcurementDashboard.ts`

Disposition:

- removed from public Procurement hook barrel;
- private query hook is disabled and does not issue requests;
- no service, query key, entity, or response projection was created.

## 12. Frontend Type Inventory

Current unsupported definitions remain service-local only:

- `PurchaseOrder`
- `PurchaseOrderItem`
- `PurchaseOrderStatus`
- `CreatePurchaseOrderRequest`
- `UpdatePurchaseOrderRequest`
- `GoodsReceipt`
- `GoodsReceiptItem`
- `GoodsReceiptStatus`
- `CreateGoodsReceiptRequest`

No canonical `src/types` Procurement entities, requests, responses, or enums
were added.

No type barrel was changed because the current compiler diagnostics came from
unsupported hook imports, not invalid existing type-barrel exports.

## 13. Frontend Service Inventory

| Service | File | Public before | Public after | HTTP calls | Backend match |
| --- | --- | --- | --- | --- | --- |
| PurchaseOrderService | `services/procurement/purchaseOrderService.ts` | Yes | No | Yes, to purchase-order endpoint constants | No registered backend contract |
| GoodsReceiptService | `services/procurement/goodsReceiptService.ts` | Yes | No | Yes, to goods-receipt endpoint constants | No registered backend contract |
| purchaseRequisitionService | None | No | No | N/A | None |
| supplierDeliveryService | None | No | No | N/A | None |
| procurementDashboardService | None | No | No | N/A | None |
| procurementService | None | No | No | N/A | None |

Unsupported implementation files were preserved as private unfinished source.

## 14. Frontend Hook Inventory

| Hook | Public before | Public after | Service/request behavior after |
| --- | --- | --- | --- |
| `usePurchaseOrders` | Yes | No | Disabled query; no service call |
| `usePurchaseOrder` | Yes | No | Disabled query; no service call |
| `useCreatePurchaseOrder` | Yes | No | Rejecting mutation; no service call or invalidation |
| `useApprovePurchaseOrder` | Yes | No | Rejecting mutation; no service call or invalidation |
| `useReceivePurchaseOrder` | Yes | No | Rejecting mutation; no service call or invalidation |
| `useCancelPurchaseOrder` | Yes | No | Rejecting mutation; no service call or invalidation |
| `usePurchaseRequisitions` | Yes | No | Disabled query; no service call |
| `usePurchaseRequisition` | Yes | No | Disabled query; no service call |
| `useGoodsReceipts` | Yes | No | Disabled query; no service call |
| `useGoodsReceipt` | Yes | No | Disabled query; no service call |
| `useSupplierDeliveries` | Yes | No | Disabled query; no service call |
| `useProcurementDashboard` | Yes | No | Disabled query; no service call |

## 15. Page And Route Consumers

Current route evidence:

- `frontend/src/app/router.tsx` routes `/procurement` to
  `<div>Procurement Module (Coming Soon)</div>`.
- `frontend/src/features/procurement/pages/ProcurementPage.tsx` is zero lines.
- `frontend/src/navigation/navigation.ts` still contains Procurement navigation
  metadata, but it was not modified.

Searches found no active page, route, or feature consumer importing the public
Procurement hook barrel or Procurement service barrel.

## 16. Service Barrel Before And After

Before:

- exported `PurchaseOrderService` and `purchaseOrderService`;
- exported service-local Purchase Order types/DTOs;
- exported `GoodsReceiptService` and `goodsReceiptService`;
- exported service-local Goods Receipt types/DTOs.

After:

```typescript
export {};
```

No Procurement service is publicly operational. Supplier is not re-exported
through Procurement.

## 17. Hook Barrel Before And After

Before:

- exported Purchase Order query/mutation hooks;
- exported Purchase Requisition hooks;
- exported Goods Receipt hooks;
- exported Supplier Delivery hook;
- exported Procurement Dashboard hook.

After:

```typescript
export {};
```

No unsupported Procurement hook is publicly operational.

## 18. Unsupported Deep-Import Behavior

No active external deep imports of private Procurement hooks or services were
found under `frontend/src`.

Private unsupported hooks remain importable only by direct path. If directly
called, they do not issue HTTP requests. Query hooks are disabled with
`enabled: false` and `retry: false`. Mutation hooks reject explicitly and do not
run invalidation.

## 19. Placeholder-Page Disposition

The routed Procurement page remains a placeholder. It does not import
unsupported hooks and does not trigger unsupported network calls.

Routes and navigation entries were intentionally left unchanged.

## 20. Type-Barrel Disposition

No type barrel was modified.

Unsupported Procurement symbols were not added to:

- `types/entities/index.ts`
- `types/requests/index.ts`
- `types/responses/index.ts`
- `types/enums/index.ts`
- `types/index.ts`

## 21. Query-Key Disposition

`frontend/src/lib/queryKeys.ts` was not modified.

No keys were added for:

- Purchase Requisitions
- Supplier Deliveries
- Procurement Dashboard

Private disabled hooks use existing procurement keys only. No unsupported key
was fabricated.

## 22. Invalidation Disposition

`frontend/src/lib/queryInvalidation.ts` was not modified.

Unsupported Procurement mutation hooks no longer call
`invalidateProcurementOperations` because they never perform a successful
backend mutation.

## 23. Files Inspected

Architecture and migration reports:

- ADR-001 through ADR-010
- Migration 009, 010, 011, 016, 017, 018, 019, and 038 reports

Backend:

- `app/__init__.py`
- `app/api/`
- `app/models/`
- `app/schemas/`
- `app/serializers/`
- `app/services/tenant/procurement/`
- `app/services/tenant/inventory/`
- `app/services/tenant/finance/`
- `app/auth/`
- `migrations/`

Frontend:

- `frontend/src/services/procurement/`
- `frontend/src/hooks/queries/procurement/`
- `frontend/src/features/procurement/`
- `frontend/src/app/router.tsx`
- `frontend/src/navigation/navigation.ts`
- `frontend/src/types/`
- Supplier services, hooks, types, and query-key area for boundary confirmation

## 24. Files Created

- `frontend/docs/architecture/reviews/MIGRATION-039-PROCUREMENT-CAPABILITY-DISPOSITION.md`

## 25. Files Modified

- `frontend/src/services/procurement/index.ts`
- `frontend/src/hooks/queries/procurement/index.ts`
- `frontend/src/hooks/queries/procurement/useApprovePurchaseOrder.ts`
- `frontend/src/hooks/queries/procurement/useCancelPurchaseOrder.ts`
- `frontend/src/hooks/queries/procurement/useCreatePurchaseOrder.ts`
- `frontend/src/hooks/queries/procurement/useGoodsReceipt.ts`
- `frontend/src/hooks/queries/procurement/useGoodsReceipts.ts`
- `frontend/src/hooks/queries/procurement/useProcurementDashboard.ts`
- `frontend/src/hooks/queries/procurement/usePurchaseOrder.ts`
- `frontend/src/hooks/queries/procurement/usePurchaseOrders.ts`
- `frontend/src/hooks/queries/procurement/usePurchaseRequisition.ts`
- `frontend/src/hooks/queries/procurement/usePurchaseRequisitions.ts`
- `frontend/src/hooks/queries/procurement/useReceivePurchaseOrder.ts`
- `frontend/src/hooks/queries/procurement/useSupplierDeliveries.ts`

## 26. Compiler Results

Before:

```text
63
```

After:

```text
30
```

Net reduction:

```text
33
```

`npm run build` still exits with code `2` because the remaining unrelated
dashboard, inventory, strict TypeScript, and administration errors still stop
`tsc -b`. Vite does not run.

## 27. Procurement Diagnostics Before And After

Before:

```text
33 direct Procurement diagnostics
```

After:

```text
0 direct Procurement diagnostics
```

Searches for these after-migration patterns returned no diagnostics:

```text
src/hooks/queries/procurement
src/services/procurement
PurchaseOrder
PurchaseRequisition
SupplierDelivery
ProcurementDashboard
```

The only remaining `GoodsReceipt` compiler diagnostic is:

```text
src/hooks/queries/inventory/useReceiveStock.ts
```

That belongs to the Inventory workflow cluster and was outside Migration 039.

## 28. Newly Exposed Diagnostics

None.

The post-migration diagnostic set is a strict subset of the pre-migration set.

## 29. New Diagnostics

None.

## 30. Remaining Procurement Blockers

Procurement can become operational only after backend support exists for one or
more Procurement capabilities beyond Supplier.

Required backend evidence for future activation:

- persistence model;
- request schema;
- serializer/projection;
- registered route;
- tenant and authorization enforcement;
- service contract;
- tests;
- response envelope and pagination contract.

## 31. Runtime Behavior Confirmation

The public Procurement service barrel exports no runtime service.

The public Procurement hook barrel exports no hook.

Private unsupported query hooks are inert and do not automatically fetch or
retry. Private unsupported mutation hooks reject and do not invalidate.

No fake data is returned.

## 32. Invariants Verified

- Procurement public APIs expose no unsupported backend capability.
- Supplier remains independent and verified under Supplier modules.
- Unsupported Procurement services are private.
- Unsupported Procurement hooks are private and blocked.
- Unsupported Procurement types were not fabricated.
- No speculative endpoint was added.
- No query key was added.
- No invalidation policy was changed.
- Routes and navigation entries were unchanged.
- Backend files were unchanged.
- Unfinished future source was preserved.

## 33. Rollback Boundary

Rollback is limited to:

- restoring the previous exports in `services/procurement/index.ts`;
- restoring the previous exports in `hooks/queries/procurement/index.ts`;
- restoring the previous private hook implementations listed above;
- deleting this report.

No backend rollback is required.

## 34. Recommended Next Migration

Recommended Migration 040:

```text
Inventory Capability Boundary Disposition
```

Reason:

The remaining compiler baseline is 30 errors, and Inventory is now the largest
remaining unsupported capability cluster. It includes adjust, receive, transfer,
stock count, stock item, stock movements, missing inventory DTOs/entities, and
query-key parameter drift. Migration 039 intentionally left Inventory untouched.

