# Migration 038 - Compiler Architecture Rebaseline

## 1. Migration Purpose

Migration 038 is an inspection-only rebaseline of the remaining frontend
TypeScript compiler diagnostics after Migration 037 removed the active Sales
service, Sales hook, and Sales domain type diagnostics.

No source fixes were implemented in this migration.

## 2. Commands

Compiler baseline command:

```bash
cd /home/thumbi/Hela360/frontend
npx tsc -b --pretty false 2>&1 | tee /tmp/hela360-migration-038-errors.txt
grep -c "error TS" /tmp/hela360-migration-038-errors.txt
```

Build command:

```bash
npm run build
```

## 3. Current Compiler Total

Current compiler total:

```text
63 TypeScript errors
```

This matches the expected post-Migration-037 baseline.

## 4. Build Result

`npm run build` exits with code `2`.

The build script is:

```text
tsc -b && vite build
```

The build still stops during `tsc -b`. Vite does not run.

## 5. Errors By Diagnostic Code

| Code | Count | Primary meaning in this baseline |
| --- | ---: | --- |
| TS2305 | 28 | Missing named exports from type/service barrels |
| TS2339 | 15 | Missing service methods or query-key members |
| TS2307 | 4 | Missing `@/types/apis` module |
| TS2551 | 4 | Dashboard service method naming mismatch |
| TS2554 | 4 | Query-key functions called with unsupported params |
| TS2614 | 2 | Administration barrel exports nonexistent type names |
| TS2686 | 2 | React UMD global used in module file |
| TS6133 | 2 | Unused generic/type import |
| TS1484 | 1 | Type-only import required |
| TS2322 | 1 | Response envelope not assignable to paginated response |

## 6. Errors By Top-Level Source Directory

| Directory | Count |
| --- | ---: |
| `src/hooks` | 58 |
| `src/services` | 2 |
| `src/lib` | 1 |
| `src/main.tsx` | 2 |

## 7. Errors By Domain

| Domain | Count |
| --- | ---: |
| Procurement | 33 |
| Inventory | 16 |
| Dashboard | 8 |
| Administration | 2 |
| App entry | 2 |
| Shared hooks | 1 |
| Shared query factory | 1 |

## 8. Errors By File

| Count | File |
| ---: | --- |
| 4 | `src/hooks/queries/procurement/useProcurementDashboard.ts` |
| 3 | `src/hooks/queries/inventory/useAdjustStock.ts` |
| 3 | `src/hooks/queries/inventory/useReceiveStock.ts` |
| 3 | `src/hooks/queries/inventory/useStockCount.ts` |
| 3 | `src/hooks/queries/inventory/useTransferStock.ts` |
| 3 | `src/hooks/queries/procurement/useCancelPurchaseOrder.ts` |
| 3 | `src/hooks/queries/procurement/useGoodsReceipts.ts` |
| 3 | `src/hooks/queries/procurement/usePurchaseOrders.ts` |
| 3 | `src/hooks/queries/procurement/usePurchaseRequisition.ts` |
| 3 | `src/hooks/queries/procurement/usePurchaseRequisitions.ts` |
| 3 | `src/hooks/queries/procurement/useReceivePurchaseOrder.ts` |
| 3 | `src/hooks/queries/procurement/useSupplierDeliveries.ts` |
| 2 | `src/hooks/queries/dashboard/useDashboardActivity.ts` |
| 2 | `src/hooks/queries/dashboard/useDashboardAlerts.ts` |
| 2 | `src/hooks/queries/dashboard/useDashboardMetrics.ts` |
| 2 | `src/hooks/queries/dashboard/useDashboardOverview.ts` |
| 2 | `src/hooks/queries/inventory/useStockMovements.ts` |
| 2 | `src/hooks/queries/procurement/useApprovePurchaseOrder.ts` |
| 2 | `src/hooks/queries/procurement/useCreatePurchaseOrder.ts` |
| 2 | `src/hooks/queries/procurement/useGoodsReceipt.ts` |
| 2 | `src/hooks/queries/procurement/usePurchaseOrder.ts` |
| 2 | `src/main.tsx` |
| 2 | `src/services/administration/index.ts` |
| 1 | `src/hooks/queries/inventory/useInventory.ts` |
| 1 | `src/hooks/queries/inventory/useStockItem.ts` |
| 1 | `src/hooks/useTheme.ts` |
| 1 | `src/lib/queryFactory.ts` |

## 9. Errors By Architectural Cluster

| Cluster | Count | ADRs | Primary diagnosis |
| --- | ---: | --- | --- |
| Procurement type ownership | 16 | ADR-004, ADR-009 | Procurement entities/DTOs are service-local or absent from canonical `src/types` barrels. |
| Inventory workflow assumptions | 14 | ADR-001, ADR-002, ADR-004, ADR-010 | Inventory hooks assume workflow DTOs/entities and facade methods without a verified registered backend route. |
| Procurement service/capability boundary | 9 | ADR-001, ADR-002, ADR-008, ADR-010 | Hooks call missing services or missing business methods; several capabilities are not evidenced by registered backend routes. |
| Dashboard API response boundary | 8 | ADR-001, ADR-004, ADR-009 | Dashboard hooks import stale `@/types/apis` and expect `get*` facade names while the service exposes short names and service-local response types. |
| Procurement query-key boundary | 6 | ADR-003, ADR-006, ADR-009 | Hooks pass params to no-arg keys or call nonexistent procurement key members. |
| Strict TypeScript cleanup | 4 | ADR-004, ADR-009 | Local type-only/import/generic/React module issues. |
| Administration type/export boundary | 2 | ADR-004, ADR-007, ADR-008 | Administration barrel exports enum-like names not actually owned/exported by service files or canonical types. |
| Inventory query-key boundary | 2 | ADR-003, ADR-006, ADR-009 | Inventory hooks pass params to no-arg key functions. |
| Procurement response-envelope boundary | 1 | ADR-001, ADR-002, ADR-004 | Purchase order list service returns an `ApiResponse` envelope where hook expects `PaginatedResponse`. |
| Procurement unsupported placeholder residue | 1 | ADR-004, ADR-010 | `ProcurementDashboard` import is unused because the assumed dashboard service/type/key contract is absent. |

## 10. Diagnostic Category Counts

| Category requested | Count | Evidence |
| --- | ---: | --- |
| Missing exports | 30 | TS2305 plus TS2614 |
| Missing modules | 4 | `@/types/apis` in dashboard hooks |
| Service method mismatches | 15 | Dashboard `get*`, inventory workflow names, procurement service method names |
| Invalid prop contracts | 0 | No component prop diagnostics remain |
| Unused imports or variables | 2 | `ProcurementDashboard`, `TData` |
| Response-envelope mismatches | 1 | `ApiResponse<PurchaseOrder[]>` vs `PaginatedResponse<PurchaseOrder>` |
| Query-key mismatches | 8 | Four TS2554 param calls plus four missing procurement key members |
| Unsupported backend assumptions | 24 | Inventory workflows and procurement dashboard/requisition/delivery assumptions without active registered backend routes |
| Provider/context mismatches | 0 | No active provider/context compiler diagnostics remain |
| Authorization gaps | 0 active compiler errors | ADR-007 remains architecturally incomplete, but not in this compiler baseline |
| Barrel or module-boundary drift | 36 | Missing exports from type/service barrels plus stale module import and administration barrel drift |

## 11. Complete Error Classification

Each remaining compiler diagnostic is assigned exactly one primary cluster.

| # | File:line | Code | Concise diagnostic | Cluster | Likely root cause | ADR | Backend verification | Supported? | Fix mode |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `src/hooks/queries/dashboard/useDashboardActivity.ts:45` | TS2307 | Missing `@/types/apis` | Dashboard API response boundary | Stale response import path | ADR-004 | Required for payload shape | Unknown | Source-level later |
| 2 | `src/hooks/queries/dashboard/useDashboardActivity.ts:86` | TS2551 | Missing `dashboardService.getActivity` | Dashboard API response boundary | Hook expects facade wrapper; service exposes `activity` | ADR-001 | Required for route existence | Unknown | Source-level later |
| 3 | `src/hooks/queries/dashboard/useDashboardAlerts.ts:44` | TS2307 | Missing `@/types/apis` | Dashboard API response boundary | Stale response import path | ADR-004 | Required for payload shape | Unknown | Source-level later |
| 4 | `src/hooks/queries/dashboard/useDashboardAlerts.ts:85` | TS2551 | Missing `dashboardService.getAlerts` | Dashboard API response boundary | Hook expects facade wrapper; service exposes `alerts` | ADR-001 | Required for route existence | Unknown | Source-level later |
| 5 | `src/hooks/queries/dashboard/useDashboardMetrics.ts:44` | TS2307 | Missing `@/types/apis` | Dashboard API response boundary | Stale response import path | ADR-004 | Required for payload shape | Unknown | Source-level later |
| 6 | `src/hooks/queries/dashboard/useDashboardMetrics.ts:85` | TS2551 | Missing `dashboardService.getMetrics` | Dashboard API response boundary | Hook expects facade wrapper; service exposes `metrics` | ADR-001 | Required for route existence | Unknown | Source-level later |
| 7 | `src/hooks/queries/dashboard/useDashboardOverview.ts:35` | TS2307 | Missing `@/types/apis` | Dashboard API response boundary | Stale response import path | ADR-004 | Required for payload shape | Unknown | Source-level later |
| 8 | `src/hooks/queries/dashboard/useDashboardOverview.ts:73` | TS2551 | Missing `dashboardService.getOverview` | Dashboard API response boundary | Hook expects facade wrapper; service exposes `overview` | ADR-001 | Required for route existence | Unknown | Source-level later |
| 9 | `src/hooks/queries/inventory/useAdjustStock.ts:41` | TS2305 | Missing `StockAdjustment` | Inventory workflow assumptions | Workflow entity not canonically owned | ADR-004 | Required | Not verified | Source-level later |
| 10 | `src/hooks/queries/inventory/useAdjustStock.ts:45` | TS2305 | Missing `AdjustStockRequest` | Inventory workflow assumptions | Workflow DTO not canonically owned | ADR-004 | Required | Not verified | Source-level later |
| 11 | `src/hooks/queries/inventory/useAdjustStock.ts:63` | TS2339 | Missing `inventoryService.adjustStock` | Inventory workflow assumptions | Hook assumes unsupported business method | ADR-001 | Required | Not verified | Source-level later |
| 12 | `src/hooks/queries/inventory/useInventory.ts:66` | TS2554 | Inventory list key passed params | Inventory query-key boundary | Query-key registry has no param signature | ADR-003 | No | N/A | Source-level later |
| 13 | `src/hooks/queries/inventory/useReceiveStock.ts:39` | TS2305 | Missing `GoodsReceipt` | Inventory workflow assumptions | Inventory hook imports procurement concept from entity barrel | ADR-004 | Required | Not verified | Source-level later |
| 14 | `src/hooks/queries/inventory/useReceiveStock.ts:43` | TS2305 | Missing `ReceiveStockRequest` | Inventory workflow assumptions | Workflow DTO not canonically owned | ADR-004 | Required | Not verified | Source-level later |
| 15 | `src/hooks/queries/inventory/useReceiveStock.ts:61` | TS2339 | Missing `inventoryService.receiveStock` | Inventory workflow assumptions | Hook assumes unsupported receive workflow | ADR-001 | Required | Not verified | Source-level later |
| 16 | `src/hooks/queries/inventory/useStockCount.ts:42` | TS2305 | Missing `StockCount` | Inventory workflow assumptions | Workflow entity not canonically owned | ADR-004 | Required | Not verified | Source-level later |
| 17 | `src/hooks/queries/inventory/useStockCount.ts:46` | TS2305 | Missing `StockCountRequest` | Inventory workflow assumptions | Workflow DTO not canonically owned | ADR-004 | Required | Not verified | Source-level later |
| 18 | `src/hooks/queries/inventory/useStockCount.ts:64` | TS2339 | Missing `inventoryService.stockCount` | Inventory workflow assumptions | Hook assumes unsupported stock-count workflow | ADR-001 | Required | Not verified | Source-level later |
| 19 | `src/hooks/queries/inventory/useStockItem.ts:66` | TS2339 | Missing `inventoryService.findById` | Inventory workflow assumptions | Hook bypasses ADR business facade naming | ADR-001 | Required | Not verified | Source-level later |
| 20 | `src/hooks/queries/inventory/useStockMovements.ts:72` | TS2554 | Inventory movements key passed params | Inventory query-key boundary | Query-key registry has no param signature | ADR-003 | No | N/A | Source-level later |
| 21 | `src/hooks/queries/inventory/useStockMovements.ts:75` | TS2339 | Missing `inventoryService.stockMovements` | Inventory workflow assumptions | Hook expects facade wrapper; service exposes `movements` | ADR-001 | Required | Not verified | Source-level later |
| 22 | `src/hooks/queries/inventory/useTransferStock.ts:38` | TS2305 | Missing `StockTransfer` | Inventory workflow assumptions | Workflow entity not canonically owned | ADR-004 | Required | Not verified | Source-level later |
| 23 | `src/hooks/queries/inventory/useTransferStock.ts:42` | TS2305 | Missing `TransferStockRequest` | Inventory workflow assumptions | Workflow DTO not canonically owned | ADR-004 | Required | Not verified | Source-level later |
| 24 | `src/hooks/queries/inventory/useTransferStock.ts:60` | TS2339 | Missing `inventoryService.transferStock` | Inventory workflow assumptions | Hook assumes unsupported transfer workflow | ADR-001 | Required | Not verified | Source-level later |
| 25 | `src/hooks/queries/procurement/useApprovePurchaseOrder.ts:38` | TS2305 | Missing `PurchaseOrder` | Procurement type ownership | Entity is service-local, not canonical | ADR-004 | Required | Not verified | Source-level later |
| 26 | `src/hooks/queries/procurement/useApprovePurchaseOrder.ts:42` | TS2305 | Missing `ApprovePurchaseOrderRequest` | Procurement type ownership | DTO missing from canonical requests | ADR-004 | Required | Not verified | Source-level later |
| 27 | `src/hooks/queries/procurement/useCancelPurchaseOrder.ts:42` | TS2305 | Missing `PurchaseOrder` | Procurement type ownership | Entity is service-local, not canonical | ADR-004 | Required | Not verified | Source-level later |
| 28 | `src/hooks/queries/procurement/useCancelPurchaseOrder.ts:46` | TS2305 | Missing `CancelPurchaseOrderRequest` | Procurement type ownership | DTO missing from canonical requests | ADR-004 | Required | Not verified | Source-level later |
| 29 | `src/hooks/queries/procurement/useCancelPurchaseOrder.ts:64` | TS2339 | Missing `cancelPurchaseOrder` | Procurement service/capability boundary | Service exposes `cancel`, hook expects business wrapper | ADR-001 | Required | Not verified | Source-level later |
| 30 | `src/hooks/queries/procurement/useCreatePurchaseOrder.ts:38` | TS2305 | Missing `PurchaseOrder` | Procurement type ownership | Entity is service-local, not canonical | ADR-004 | Required | Not verified | Source-level later |
| 31 | `src/hooks/queries/procurement/useCreatePurchaseOrder.ts:42` | TS2305 | Missing `CreatePurchaseOrderRequest` | Procurement type ownership | DTO missing from canonical requests | ADR-004 | Required | Not verified | Source-level later |
| 32 | `src/hooks/queries/procurement/useGoodsReceipt.ts:32` | TS2305 | Missing `GoodsReceipt` | Procurement type ownership | Entity is service-local, not canonical | ADR-004 | Required | Not verified | Source-level later |
| 33 | `src/hooks/queries/procurement/useGoodsReceipt.ts:59` | TS2339 | Missing `getGoodsReceipt` | Procurement service/capability boundary | Service exposes generic/base names, not wrapper | ADR-001 | Required | Not verified | Source-level later |
| 34 | `src/hooks/queries/procurement/useGoodsReceipts.ts:36` | TS2305 | Missing `GoodsReceipt` | Procurement type ownership | Entity is service-local, not canonical | ADR-004 | Required | Not verified | Source-level later |
| 35 | `src/hooks/queries/procurement/useGoodsReceipts.ts:60` | TS2554 | Goods receipts key passed params | Procurement query-key boundary | Query-key registry has no param signature | ADR-003 | No | N/A | Source-level later |
| 36 | `src/hooks/queries/procurement/useGoodsReceipts.ts:64` | TS2339 | Missing `listGoodsReceipts` | Procurement service/capability boundary | Service lacks business wrapper | ADR-001 | Required | Not verified | Source-level later |
| 37 | `src/hooks/queries/procurement/useProcurementDashboard.ts:36` | TS2305 | Missing `procurementDashboardService` | Procurement service/capability boundary | Assumed dashboard service is absent from public barrel | ADR-001 | Required | Not verified | Source-level later |
| 38 | `src/hooks/queries/procurement/useProcurementDashboard.ts:39` | TS6133 | Unused `ProcurementDashboard` | Procurement unsupported placeholder residue | Imported value is stranded by absent service/type/key contract | ADR-010 | Required | Not verified | Source-level later |
| 39 | `src/hooks/queries/procurement/useProcurementDashboard.ts:40` | TS2305 | Missing `ProcurementDashboard` | Procurement type ownership | Dashboard projection not canonically owned | ADR-004 | Required | Not verified | Source-level later |
| 40 | `src/hooks/queries/procurement/useProcurementDashboard.ts:51` | TS2339 | Missing procurement dashboard key | Procurement query-key boundary | Query-key registry has no dashboard key | ADR-003 | Required | Not verified | Source-level later |
| 41 | `src/hooks/queries/procurement/usePurchaseOrder.ts:39` | TS2305 | Missing `PurchaseOrder` | Procurement type ownership | Entity is service-local, not canonical | ADR-004 | Required | Not verified | Source-level later |
| 42 | `src/hooks/queries/procurement/usePurchaseOrder.ts:67` | TS2339 | Missing `purchaseOrderService.findById` | Procurement service/capability boundary | Hook uses generic name not provided by facade | ADR-001 | Required | Not verified | Source-level later |
| 43 | `src/hooks/queries/procurement/usePurchaseOrders.ts:33` | TS2305 | Missing `PurchaseOrder` | Procurement type ownership | Entity is service-local, not canonical | ADR-004 | Required | Not verified | Source-level later |
| 44 | `src/hooks/queries/procurement/usePurchaseOrders.ts:56` | TS2554 | Purchase orders key passed params | Procurement query-key boundary | Query-key registry has no param signature | ADR-003 | No | N/A | Source-level later |
| 45 | `src/hooks/queries/procurement/usePurchaseOrders.ts:59` | TS2322 | `ApiResponse` not `PaginatedResponse` | Procurement response-envelope boundary | Service/hook disagree on list response boundary | ADR-001 | Required | Not verified | Source-level later |
| 46 | `src/hooks/queries/procurement/usePurchaseRequisition.ts:28` | TS2305 | Missing `purchaseRequisitionService` | Procurement service/capability boundary | Assumed service absent from public barrel | ADR-001 | Required | Not verified | Source-level later |
| 47 | `src/hooks/queries/procurement/usePurchaseRequisition.ts:32` | TS2305 | Missing `PurchaseRequisition` | Procurement type ownership | Entity not canonically owned | ADR-004 | Required | Not verified | Source-level later |
| 48 | `src/hooks/queries/procurement/usePurchaseRequisition.ts:57` | TS2339 | Missing purchase requisition key | Procurement query-key boundary | Query-key registry has no requisition detail key | ADR-003 | Required | Not verified | Source-level later |
| 49 | `src/hooks/queries/procurement/usePurchaseRequisitions.ts:32` | TS2305 | Missing `purchaseRequisitionService` | Procurement service/capability boundary | Assumed service absent from public barrel | ADR-001 | Required | Not verified | Source-level later |
| 50 | `src/hooks/queries/procurement/usePurchaseRequisitions.ts:36` | TS2305 | Missing `PurchaseRequisition` | Procurement type ownership | Entity not canonically owned | ADR-004 | Required | Not verified | Source-level later |
| 51 | `src/hooks/queries/procurement/usePurchaseRequisitions.ts:62` | TS2339 | Missing purchase requisitions key | Procurement query-key boundary | Query-key registry has no requisition list key | ADR-003 | Required | Not verified | Source-level later |
| 52 | `src/hooks/queries/procurement/useReceivePurchaseOrder.ts:40` | TS2305 | Missing `GoodsReceipt` | Procurement type ownership | Entity is service-local, not canonical | ADR-004 | Required | Not verified | Source-level later |
| 53 | `src/hooks/queries/procurement/useReceivePurchaseOrder.ts:44` | TS2305 | Missing `ReceivePurchaseOrderRequest` | Procurement type ownership | DTO missing from canonical requests | ADR-004 | Required | Not verified | Source-level later |
| 54 | `src/hooks/queries/procurement/useReceivePurchaseOrder.ts:62` | TS2339 | Missing `purchaseOrderService.receive` | Procurement service/capability boundary | Assumed workflow method absent | ADR-010 | Required | Not verified | Source-level later |
| 55 | `src/hooks/queries/procurement/useSupplierDeliveries.ts:31` | TS2305 | Missing `supplierDeliveryService` | Procurement service/capability boundary | Assumed service absent from public barrel | ADR-001 | Required | Not verified | Source-level later |
| 56 | `src/hooks/queries/procurement/useSupplierDeliveries.ts:35` | TS2305 | Missing `SupplierDelivery` | Procurement type ownership | Entity not canonically owned | ADR-004 | Required | Not verified | Source-level later |
| 57 | `src/hooks/queries/procurement/useSupplierDeliveries.ts:58` | TS2339 | Missing supplier deliveries key | Procurement query-key boundary | Query-key registry has no supplier deliveries key | ADR-003 | Required | Not verified | Source-level later |
| 58 | `src/hooks/useTheme.ts:4` | TS1484 | `ThemeMode` must be type-only | Strict TypeScript cleanup | `verbatimModuleSyntax` import alignment | ADR-004 | No | N/A | Source-level later |
| 59 | `src/lib/queryFactory.ts:116` | TS6133 | Unused generic `TData` | Strict TypeScript cleanup | Isolated generic declaration drift | ADR-009 | No | N/A | Source-level later |
| 60 | `src/main.tsx:11` | TS2686 | React UMD global | Strict TypeScript cleanup | JSX file lacks module-level React import under current setup | ADR-008 | No | N/A | Source-level later |
| 61 | `src/main.tsx:15` | TS2686 | React UMD global | Strict TypeScript cleanup | JSX file lacks module-level React import under current setup | ADR-008 | No | N/A | Source-level later |
| 62 | `src/services/administration/index.ts:32` | TS2614 | Missing `UserStatus` export | Administration type/export boundary | Enum-like type is absent from service and canonical type barrel | ADR-004 | Required for admin backend | Unknown | Source-level later |
| 63 | `src/services/administration/index.ts:65` | TS2614 | Missing `PermissionCategory` export | Administration type/export boundary | Enum-like type is absent from service and canonical type barrel | ADR-004 | Required for admin backend | Unknown | Source-level later |

## 12. Sales Verification

Compiler log searches for the following returned no matches:

```text
src/services/sales
src/hooks/queries/sales
src/types/domains/sales
src/types/entities/sale
src/types/requests/*sale
```

Migration 037 removed all active Sales compiler diagnostics.

Source searches show:

- `frontend/src/services/sales/index.ts` publicly exports only `salesService`
  and `SalesService` from `./salesService`.
- `legacySalesService.ts` remains as a private transitional file with 232
  lines.
- `salesQueryService.ts`, `salesWorkflowService.ts`, `paymentService.ts`,
  `receiptService.ts`, and `salesDashboardService.ts` remain zero-line private
  placeholders.
- No stale public exports or active hook/feature imports were found for those
  Sales transitional files.

Sales should not be revisited until a new active compiler diagnostic or backend
contract need appears.

## 13. Unsupported Capability Findings

Active registered backend blueprints in `app/__init__.py` currently include:

```text
auth, health, products, customers, sales, suppliers
```

No active registered inventory, purchase order, goods receipt, purchase
requisition, supplier delivery, procurement dashboard, or dashboard blueprint
was verified from the current registration evidence.

| Capability | Publicly exported? | Active UI consumer found? | Backend evidence | Disposition |
| --- | --- | --- | --- | --- |
| `GoodsReceipt` | Hook barrel exports goods receipt hooks; service-local type exported from `services/procurement` | No feature/app consumer found by search | Service file exists; no registered backend blueprint verified | Capability-boundary or backend-contract inspection before implementation |
| `PurchaseOrder` | Hook barrel exports purchase order hooks; service-local type exported from `services/procurement` | No feature/app consumer found by search | Service file exists; no registered backend blueprint verified | Type/service disposition, not speculative implementation |
| `PurchaseRequisition` | Hooks are publicly exported | No feature/app consumer found by search | No service or registered backend route verified | Capability-disposition migration recommended |
| `SupplierDelivery` | Hook is publicly exported | No feature/app consumer found by search | No service or registered backend route verified | Capability-disposition migration recommended |
| `ProcurementDashboard` | Hook is publicly exported | No feature/app consumer found by search | No service or registered backend route verified | Capability-disposition migration recommended |
| Sales `Receipt` | Sales unsupported hooks remain private except not in public barrel | No active compiler diagnostics | No verified route | No current Sales migration needed |
| `SalesDashboard` | Sales dashboard hook remains private | No active compiler diagnostics | No verified route | No current Sales migration needed |
| Customer update | Public hook removed in Migration 034; local rejecting placeholder remains | No active compiler diagnostics | No update route in `app/api/customers.py` | No current migration needed |
| Product update | Local rejecting placeholder remains | No active compiler diagnostics | No update route in `app/api/products.py` | No current migration needed |
| Product delete | Local disposition depends on prior migration; no active compiler diagnostics | No active compiler diagnostics | No delete route in `app/api/products.py` | No current migration needed |
| Inventory adjustment | Public hook exists | No feature/app consumer found by search | No registered inventory API route | Capability-disposition migration recommended |
| Inventory transfer | Public hook exists | No feature/app consumer found by search | No registered inventory API route | Capability-disposition migration recommended |
| Stock count | Public hook exists | No feature/app consumer found by search | No registered inventory API route | Capability-disposition migration recommended |
| Stock receive | Public hook exists | No feature/app consumer found by search | No registered inventory API route | Capability-disposition migration recommended |

## 14. Administration Findings

Administration now contributes only two compiler errors:

- `UserStatus` is exported from `services/administration/index.ts`, but
  `userService.ts` does not export that symbol.
- `PermissionCategory` is exported from `services/administration/index.ts`, but
  `permissionService.ts` does not export that symbol.

The likely root is unresolved administration type ownership, not a complete
administration facade failure in the current compiler baseline.

Backend verification is still required before adding canonical administration
entities/enums because the active Flask blueprint registration does not show
administration user/role/permission/branch/tenant APIs.

## 15. Authorization Findings

No active compiler diagnostics involve:

```text
authorization/
ProtectedRoute
Permission
Role
permissions
useApplication
```

Architecturally, ADR-007 still requires a centralized authorization context and
authorization service, and the current `authorization/` area remains a major
future concern. It is not the strongest next compiler migration because it does
not own any of the current 63 diagnostics.

Important distinction:

- Backend enforcement remains the security boundary.
- Frontend authorization is for route protection, navigation filtering, feature
  visibility, and action enablement.
- Provider/context requirements should be handled only after active compiler
  diagnostics or a direct feature requirement reintroduces the layer.

## 16. Inventory Findings

Inventory contributes 16 diagnostics:

- 14 are workflow/type/service assumptions around adjust, receive, transfer,
  stock count, stock item, and stock movements.
- 2 are query-key parameter mismatches.

The inventory service exists under `services/products/inventoryService.ts`,
which is still a domain ownership smell. More importantly, no registered
inventory API blueprint was verified. Therefore the safest next inventory work
is a capability-boundary disposition, not adding request/entity shims or facade
methods for unverified workflows.

## 17. Procurement Findings

Procurement is the largest cluster at 33 diagnostics:

- 16 type ownership errors.
- 9 service/capability boundary errors.
- 6 query-key boundary errors.
- 1 response-envelope error.
- 1 unsupported placeholder residue error.

`purchaseOrderService.ts` and `goodsReceiptService.ts` contain service-local
types and methods, but no active registered purchase order or goods receipt
backend blueprint was verified. `purchaseRequisitionService`,
`supplierDeliveryService`, and `procurementDashboardService` are not publicly
exported and no matching registered backend evidence was found.

The strongest next migration should classify procurement capabilities before
adding canonical types or service wrappers.

## 18. Component And Page Findings

No remaining diagnostics involve missing `Page`, `Form`, `Header`, `Footer`,
`Illustration`, `Table`, `Dialog`, or `Modal` exports.

`src/main.tsx` has two app-entry React import diagnostics, but those are local
strict/module cleanup issues rather than feature/page export boundary failures.

## 19. Strict TypeScript Cleanup Findings

Genuinely isolated strict-TypeScript cleanup candidates:

| File | Diagnostic | Safe narrow migration? |
| --- | --- | --- |
| `src/hooks/useTheme.ts` | `ThemeMode` requires `import type` | Yes |
| `src/lib/queryFactory.ts` | Unused generic `TData` | Yes, but avoid changing shared factory behavior casually |
| `src/main.tsx` | React UMD global at two JSX lines | Yes |

`useProcurementDashboard.ts` has a TS6133 unused import, but it is not a pure
cleanup. It is evidence of a missing procurement dashboard contract.

## 20. Architectural Dependency Map

Dependency order from the accepted ADRs:

```text
ADR-001 services
  -> ADR-002 hooks
  -> ADR-003 query keys/invalidation
  -> ADR-004 type ownership
  -> ADR-005 error handling
  -> ADR-006 tenant/branch
  -> ADR-007 authorization
  -> ADR-008 module boundaries
  -> ADR-009 naming
  -> ADR-010 workflows
```

Practical order for the current 63 diagnostics:

```text
1. Capability disposition where backend evidence is absent
2. Canonical type ownership for verified retained capabilities
3. Service facade response boundary for verified retained capabilities
4. Hook public barrel/query-key cleanup after capability decisions
5. Isolated strict cleanup
6. Administration/authorization only when active diagnostics or feature scope returns
```

## 21. Ranked Migration Candidates

| Rank | Candidate | Cluster | Error count | Why here |
| ---: | --- | --- | ---: | --- |
| 1 | Migration 039 - Procurement Capability Boundary Disposition | Procurement service/capability and unsupported placeholders | 19 directly, 33 affected | Largest cluster; prevents fabricating requisition, delivery, dashboard, PO, or GRN behavior without backend contracts |
| 2 | Migration 040 - Procurement Type Ownership For Retained Contracts | Procurement type ownership | 16 | Only after 039 decides which procurement contracts are retained |
| 3 | Migration 041 - Procurement Service Facade And Response Boundary | Procurement service and envelope boundary | 10 | Depends on 039 and 040; should expose only verified operations |
| 4 | Migration 042 - Procurement Query-Key Public Hook Boundary | Procurement query keys/barrels | 6 | Depends on capability and facade decisions |
| 5 | Migration 043 - Inventory Capability Boundary Disposition | Inventory workflow assumptions | 14 | Second-largest unsupported backend assumption cluster |
| 6 | Migration 044 - Inventory Query-Key Boundary | Inventory query-key boundary | 2 | Narrow follow-up after inventory capability disposition |
| 7 | Migration 045 - Dashboard Response Boundary And Facade Naming | Dashboard API response boundary | 8 | Compact cluster, but backend route verification is needed |
| 8 | Migration 046 - Administration Enum Export Disposition | Administration type/export boundary | 2 | Small, isolated admin barrel/type issue |
| 9 | Migration 047 - Main Entry React Module Alignment | Strict TypeScript cleanup | 2 | Local app-entry cleanup |
| 10 | Migration 048 - Theme Type-Only Import Alignment | Strict TypeScript cleanup | 1 | Very narrow strict cleanup |

## 22. Recommended Next Migration

Recommended Migration 039:

```text
Migration 039 - Procurement Capability Boundary Disposition
```

Rationale:

- Procurement is the largest remaining domain at 33 diagnostics.
- Several procurement hooks assume unsupported or absent capabilities:
  purchase requisitions, supplier deliveries, and procurement dashboard.
- Current backend registration evidence does not show purchase order, goods
  receipt, requisition, delivery, or procurement dashboard APIs.
- A disposition-first migration creates a narrow rollback boundary and prevents
  placeholder type/service shims from hiding unsupported product decisions.
- It should reduce or clarify up to 19 direct service/query-key/unsupported
  diagnostics and unblock truthful type ownership work.

Stop conditions for Migration 039:

- Do not add backend routes.
- Do not create canonical procurement types for unsupported capabilities.
- Do not add query keys for unsupported capabilities.
- Do not implement missing services.
- Retain only public hooks that map to verified or intentionally retained
  frontend contracts.

## 23. Recommended Migration Sequence

| Migration | Title | Primary cluster | Initial file scope | ADRs | Backend verification | Mode | Current count | Resolves | Stop conditions | Prerequisites | Sequence rationale |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- |
| 039 | Procurement Capability Boundary Disposition | Procurement unsupported capability boundary | `hooks/queries/procurement`, `services/procurement/index.ts`, backend registration files | 001, 002, 008, 010 | Required | Implementation with inspection | 19 direct / 33 affected | Missing procurement services, unsupported public hooks, unsupported keys | No backend routes or speculative services | 038 | Biggest coherent risk; avoids fabricated procurement contracts |
| 040 | Procurement Type Ownership For Retained Contracts | Procurement type ownership | `types/entities`, `types/requests`, retained procurement hooks/services | 004, 009 | Required | Implementation | 16 | Missing `PurchaseOrder`, `GoodsReceipt`, retained DTO exports | Do not create types for capabilities disposed in 039 | 039 | Types need capability decisions first |
| 041 | Procurement Service Facade And Response Boundary | Procurement service facade and envelopes | `services/procurement`, retained procurement hooks | 001, 002, 004, 009 | Required | Implementation | 10 | Business method wrappers, response unwrapping | No unverified route exposure | 039, 040 | Service boundary depends on retained DTOs/entities |
| 042 | Procurement Query-Key Public Hook Boundary | Procurement query keys/barrels | `lib/queryKeys.ts`, `hooks/queries/procurement/index.ts`, retained hooks | 003, 006, 009 | Partial | Implementation | 6 | Param/key drift and public hook exports | No keys for unsupported endpoints | 039-041 | Query keys should follow retained hooks |
| 043 | Inventory Capability Boundary Disposition | Inventory workflow assumptions | `hooks/queries/inventory`, `services/products/inventoryService.ts`, backend registration files | 001, 002, 008, 010 | Required | Implementation with inspection | 14 | Unsupported adjust/receive/transfer/count assumptions | No inventory route fabrication | 039 | Second-largest unsupported capability cluster |
| 044 | Inventory Query-Key Boundary | Inventory query keys | `lib/queryKeys.ts`, retained inventory hooks | 003, 006, 009 | No for key shape, yes for data scope | Implementation | 2 | Inventory list/movement param mismatch | Preserve invalidation policy | 043 | Small key cleanup after capability disposition |
| 045 | Dashboard Response Boundary And Facade Naming | Dashboard response/service boundary | `hooks/queries/dashboard`, `services/dashboard/dashboardService.ts`, `types/responses` | 001, 004, 009 | Required | Implementation | 8 | `@/types/apis` and `get*` facade mismatch | No dashboard endpoints without backend evidence | 038 | Compact cluster, lower risk after procurement/inventory |
| 046 | Administration Enum Export Disposition | Administration barrel/type exports | `services/administration/index.ts`, admin type owners | 004, 007, 008 | Required before expanding | Implementation | 2 | `UserStatus`, `PermissionCategory` export drift | Do not implement full authz/admin layer | 038 | Isolated but not as impactful |
| 047 | Main Entry React Module Alignment | Strict TypeScript cleanup | `src/main.tsx` | 008, 009 | No | Implementation | 2 | React UMD diagnostics | Only app-entry import/module fix | 038 | Safe local cleanup |
| 048 | Theme Type-Only Import Alignment | Strict TypeScript cleanup | `src/hooks/useTheme.ts` | 004 | No | Implementation | 1 | TS1484 | Type-only import only | 038 | Safe local cleanup |
| 049 | Query Factory Generic Cleanup | Strict TypeScript cleanup | `src/lib/queryFactory.ts` | 002, 003, 009 | No | Implementation | 1 | Unused generic | Avoid API behavior change | 038 | Shared helper risk deserves its own small migration |

## 24. Isolated Safe Cleanup Candidates

These are intentionally ranked below major architecture work unless a user wants
small cleanup passes:

1. `src/hooks/useTheme.ts` type-only import alignment, 1 error.
2. `src/main.tsx` React module import alignment, 2 errors.
3. `src/lib/queryFactory.ts` unused generic cleanup, 1 error.
4. `src/services/administration/index.ts` remove or relocate `UserStatus` and
   `PermissionCategory` exports, 2 errors. This is small but should respect
   ADR-004/ADR-007 ownership rather than silently deleting public API.

## 25. Compiler Trend

| Baseline | Errors | Delta from previous |
| --- | ---: | ---: |
| Initial | 294 | - |
| Migration 001 | 274 | -20 |
| Migration 002 | 262 | -12 |
| Migration 003 | 257 | -5 |
| Migration 004 | 253 | -4 |
| Migration 005 | 251 | -2 |
| Migration 006 | 246 | -5 |
| Migration 007 | 239 | -7 |
| Migration 008 | 236 | -3 |
| Migration 011 | 228 | -8 |
| Migration 012 | 218 | -10 |
| Migration 013 | 211 | -7 |
| Migration 014 | 207 | -4 |
| Migration 015 | 199 | -8 |
| Migration 018 | 196 | -3 |
| Migration 019 | 195 | -1 |
| Migration 020 | 193 | -2 |
| Migration 021 | 192 | -1 |
| Migration 022 | 190 | -2 |
| Migration 023 | 189 | -1 |
| Migration 024 | 188 | -1 |
| Migration 025 | 149 | -39 |
| Migration 026 | 145 | -4 |
| Migration 027 | 143 | -2 |
| Migration 028 | 111 | -32 |
| Migration 029 | 107 | -4 |
| Migration 030 | 106 | -1 |
| Migration 031 | 105 | -1 |
| Migration 032 | 104 | -1 |
| Migration 033 | 100 | -4 |
| Migration 034 | 99 | -1 |
| Migration 035 | 98 | -1 |
| Migration 036 | 96 | -2 |
| Migration 037 | 63 | -33 |
| Migration 038 | 63 | 0 |

Totals:

- Total reduction from initial: 231 errors.
- Percentage reduction from initial: 78.57%.
- Remaining percentage of initial baseline: 21.43%.
- Largest reductions: Migration 025 (-39), Migration 037 (-33),
  Migration 028 (-32), Migration 001 (-20), Migration 002 (-12).
- Recent Migration 033 through 038 reduction: 37 errors over 6 migrations,
  averaging 6.17 errors per migration. Migration 038 was intentionally zero.

Report verification note:

- The known trend values were taken from the migration brief and current
  migration reports where practical.
- Older architecture reports still described ADR-008 as empty, but current
  `ADR-008-frontend-module-boundaries.md` is present and non-empty. This report
  uses the current ADR-008 as authoritative.

## 26. Major Risks

- Creating procurement or inventory DTOs before capability disposition would
  hide unsupported backend assumptions.
- Adding query keys for unsupported views would make speculative frontend state
  look canonical.
- Implementing service wrappers around unregistered routes would violate
  ADR-001 and ADR-010.
- Treating administration enum exports as a local barrel cleanup could skip the
  real authorization/type ownership question.
- Bulk strict cleanup could obscure the few remaining true architecture
  clusters.

## 27. Unresolved Backend Requirements

Backend verification is required for:

- Purchase orders list/detail/create/approve/cancel/receive.
- Goods receipts list/detail.
- Purchase requisitions list/detail.
- Supplier deliveries list.
- Procurement dashboard.
- Inventory list/detail/movements/adjust/receive/transfer/count.
- Dashboard overview/metrics/alerts/activity.
- Administration users/roles/permissions/branches/tenants.

Active registered backend evidence currently confirms products, customers,
sales, suppliers, auth, and health routes, but not the domains above.

## 28. Files Inspected

Architecture:

- `frontend/docs/architecture/adr/ADR-001-service-layer-architecture.md`
- `frontend/docs/architecture/adr/ADR-002-query-hook-architecture.md`
- `frontend/docs/architecture/adr/ADR-003-cache-invalidation-strategy.md`
- `frontend/docs/architecture/adr/ADR-004-type-system-organization.md`
- `frontend/docs/architecture/adr/ADR-005-error-handling-strategy.md`
- `frontend/docs/architecture/adr/ADR-006-multi-tenant-architecture.md`
- `frontend/docs/architecture/adr/ADR-007-authorization-architecture.md`
- `frontend/docs/architecture/adr/ADR-008-frontend-module-boundaries.md`
- `frontend/docs/architecture/adr/ADR-009-enterprise-naming-conventions.md`
- `frontend/docs/architecture/adr/ADR-010-domain-event-architecture.md`
- `frontend/docs/architecture/reviews/FRONTEND_ARCHITECTURAL_BASELINE.md`
- `frontend/docs/architecture/reviews/ADR_COMPLIANCE_MATRIX.md`
- `frontend/docs/architecture/reviews/CANONICAL_FRONTEND_ARCHITECTURE.md`
- `frontend/docs/architecture/reviews/MIGRATION-037-SALES-SERVICE-FACADE.md`

Frontend source inspected without modification:

- `frontend/src/hooks/queries/dashboard/`
- `frontend/src/hooks/queries/inventory/`
- `frontend/src/hooks/queries/procurement/`
- `frontend/src/hooks/queries/sales/`
- `frontend/src/services/dashboard/dashboardService.ts`
- `frontend/src/services/products/inventoryService.ts`
- `frontend/src/services/procurement/`
- `frontend/src/services/sales/`
- `frontend/src/services/administration/`
- `frontend/src/lib/queryKeys.ts`
- `frontend/src/lib/queryInvalidation.ts`
- `frontend/src/main.tsx`
- `frontend/src/hooks/useTheme.ts`
- `frontend/src/lib/queryFactory.ts`

Backend source inspected without modification:

- `app/__init__.py`
- `app/api/products.py`
- `app/api/customers.py`
- `app/api/sales.py`
- `app/api/suppliers.py`
- `app/api_sales.py`
- `app/models/inventory.py`
- `app/services/tenant/procurement/`

## 29. Source Files Changed Confirmation

No frontend source files were changed.

No backend source files were changed.

No TypeScript configuration, package file, JavaScript source file, test file,
or migration file was changed.

The only file created by this migration is:

```text
frontend/docs/architecture/reviews/MIGRATION-038-COMPILER-REBASELINE.md
```

## 30. Rollback Boundary

Rollback for this migration is limited to deleting the review document:

```text
frontend/docs/architecture/reviews/MIGRATION-038-COMPILER-REBASELINE.md
```

No source rollback is required because this migration did not modify source.

