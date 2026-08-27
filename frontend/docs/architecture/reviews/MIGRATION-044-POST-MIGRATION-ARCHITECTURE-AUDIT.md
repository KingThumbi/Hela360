# Migration 044 - Post-Migration Architecture Audit

## 1. Migration Purpose

Migration 044 verifies the now-compiling frontend against ADR-001 through
ADR-010 and records the remaining public-boundary, transitional-source,
unsupported-capability, tenant-scope, authorization, route, and bundle risks.

This migration is inspection-first. No runtime source behavior was changed.

## 2. Clean Compiler And Build Baseline

Baseline verification:

```bash
cd /home/thumbi/Hela360/frontend
npx tsc -b --pretty false
npm run build
```

Result:

```text
TypeScript exit code: 0
TypeScript errors: 0
Vite build exit code: 0
dist/ output: generated
```

Generated production output observed:

```text
dist/index.html                                              0.45 kB
dist/assets/index-CVlsU70F.css                              79.93 kB
dist/assets/index-CXXQZlCT.js                              733.60 kB
```

Warning:

```text
Some chunks are larger than 500 kB after minification.
```

The warning was recorded only. Bundle optimization was intentionally deferred.

## 3. Public Barrel Audit

Public barrels compile and their exported symbols resolve.

Supported operational public barrels:

- `frontend/src/api/index.ts`
- `frontend/src/services/auth/index.ts`
- `frontend/src/services/products/index.ts`
- `frontend/src/services/customers/index.ts`
- `frontend/src/services/suppliers/index.ts`
- `frontend/src/services/sales/index.ts`
- `frontend/src/hooks/queries/auth/index.ts`
- `frontend/src/hooks/queries/products/index.ts`
- `frontend/src/hooks/queries/customers/index.ts`
- `frontend/src/hooks/queries/suppliers/index.ts`
- `frontend/src/hooks/queries/sales/index.ts`
- `frontend/src/navigation/index.ts`
- `frontend/src/providers/index.ts`
- `frontend/src/types/index.ts`

Closed unsupported public barrels:

- `frontend/src/services/procurement/index.ts`
- `frontend/src/services/dashboard/index.ts`
- `frontend/src/hooks/queries/procurement/index.ts`
- `frontend/src/hooks/queries/inventory/index.ts`
- `frontend/src/hooks/queries/dashboard/index.ts`

Empty placeholder barrels requiring manual review:

- `frontend/src/authorization/index.ts`
- `frontend/src/hooks/queries/administration/index.ts`
- `frontend/src/hooks/queries/finance/index.ts`
- `frontend/src/hooks/queries/reports/index.ts`
- `frontend/src/validation/index.ts`

Finding:

```text
No missing-export compiler failures remain. Some public barrels still expose
future service areas, notably finance and reports, whose backend support was
not verified in this audit.
```

## 4. Service Boundary Audit

Verified supported public service instances:

- `authService`
- `productService`
- `customerService`
- `supplierService`
- `salesService`

Closed unsupported service boundaries:

- Procurement has no public service export.
- Dashboard has no public service export.
- Inventory has no public service folder and no public hook barrel.

Transitional or future service implementations:

| File | Classification | Notes |
| --- | --- | --- |
| `services/sales/legacySalesService.ts` | Safe removal candidate | Unreferenced after canonical `salesService.ts`; still private source. |
| `services/sales/paymentService.ts` | Safe removal candidate | Zero-byte placeholder. |
| `services/sales/receiptService.ts` | Safe removal candidate | Zero-byte placeholder. |
| `services/sales/salesDashboardService.ts` | Safe removal candidate | Zero-byte placeholder. |
| `services/sales/salesQueryService.ts` | Safe removal candidate | Zero-byte placeholder. |
| `services/sales/salesWorkflowService.ts` | Safe removal candidate | Zero-byte placeholder. |
| `services/procurement/purchaseOrderService.ts` | Backend-blocked | Implemented private speculative service. |
| `services/procurement/goodsReceiptService.ts` | Backend-blocked | Implemented private speculative service. |
| `services/products/inventoryService.ts` | Backend-blocked | Private speculative Inventory service in Product domain folder. |
| `services/dashboard/dashboardService.ts` | Backend-blocked | Private speculative Dashboard service. |
| `services/products/categoryService.ts` | Requires manual review | Private service with no verified public barrel export. |
| `services/finance/*.ts` | Requires manual review | Publicly exported services but no registered backend route evidence captured. |
| `services/reports/reportService.ts` | Requires manual review | Publicly exported service but no registered backend route evidence captured. |

ADR-001 findings:

- Services do not import React, hooks, TanStack Query, query keys, or
  invalidation.
- Hooks call services rather than Axios directly.
- Public service instances inherit `BaseService` generic CRUD methods. That
  means unsupported transport-style methods may be callable even when the
  named facade methods are constrained. This is a residual boundary risk.

## 5. Hook Boundary Audit

Public supported hook barrels:

- Auth: `useCurrentUser`, `useLogin`, `useLogout`
- Products: `useProducts`, `useProduct`, `useCreateProduct`
- Customers: `useCustomers`, `useCustomer`, `useCreateCustomer`,
  `useDeleteCustomer`
- Suppliers: `useSuppliers`, `useSupplier`, `useCreateSupplier`,
  `useUpdateSupplier`, `useDeleteSupplier`
- Sales: `useSales`, `useSale`, `useCreateSale`, `useRefundSale`

Private unsupported hooks:

- Product update/delete are private and explicitly reject.
- Customer update is private and explicitly rejects.
- Procurement hooks are private and reject or remain disabled.
- Inventory hooks are private and reject or remain disabled.
- Dashboard hooks are private, disabled, and `retry: false`.
- Sales dashboard hook is private, rejects, but lacks `enabled: false` and
  `retry: false`.

Finding:

```text
Unsupported private hooks are not reachable through public barrels or active
pages. The private Sales dashboard hook should be aligned with the Dashboard
disabled-query pattern before it is ever exported or mounted.
```

## 6. Query-Key Audit

Canonical owner:

```text
frontend/src/lib/queryKeys.ts
```

Namespaces:

- `auth`
- `dashboard`
- `products`
- `customers`
- `suppliers`
- `inventory`
- `procurement`
- `sales`
- `finance`
- `administration`
- `reports`

Findings:

- Active hooks consume `QUERY_KEYS`; hardcoded query arrays were not observed in
  hooks/components.
- Product, Customer, and Supplier list keys normalize request parameters.
- Detail keys include entity identity.
- Inventory, Procurement, Dashboard, Finance, Administration, and Reports keys
  include future/dormant namespaces.
- Query keys do not include tenant or branch context. This is the known tenant
  cache-isolation gap from ADR-006.

## 7. Invalidation Audit

Canonical owner:

```text
frontend/src/lib/queryInvalidation.ts
```

Findings:

- Direct `invalidateQueries` usage is centralized in `queryInvalidation.ts`.
- Mutation hooks select invalidation helpers and do not hardcode arrays.
- Services contain no cache invalidation logic.
- Dormant future policies exist for Dashboard, Inventory, Procurement,
  Finance, Reports, and Administration.
- Unsupported rejecting mutations do not reach `onSuccess`, so their provided
  invalidation callbacks do not execute.

## 8. Type Ownership Audit

Canonical owners verified:

| Type | Owner |
| --- | --- |
| `Supplier` | `src/types/entities/supplier.ts` |
| `Product` | `src/types/entities/product.ts` |
| `Customer` | `src/types/entities/customer.ts` |
| `InventoryItem` | `src/types/entities/inventory-item.ts` |
| `InventoryMovement` | `src/types/entities/inventory-movement.ts` |
| `Sale` | `src/types/entities/sale.ts` |
| `SaleItem` | `src/types/entities/sale-item.ts` |
| `SalePayment` | `src/types/entities/sale-payment.ts` |
| `SaleRefund` | `src/types/entities/sale-refund.ts` |
| `CreateSaleRequest` | `src/types/requests/create-sale-request.ts` |
| `RefundSaleRequest` | `src/types/requests/refund-sale-request.ts` |
| `LoginRequest` | `src/types/requests/login-request.ts` |
| `LoginResponse` | `src/types/responses/login-response.ts` |
| `PaginationRequest` | `src/types/requests/pagination-request.ts` |
| `PaginatedResponse` | `src/types/api/pagination.ts` |
| `ErrorCode` | `src/types/enums/error-code.ts` |
| `SaleStatus` | `src/types/enums/sale-status.ts` |
| `NavigationSectionId` | `src/navigation/ids.ts` |
| `NavigationItemId` | `src/navigation/ids.ts` |

Findings:

- Canonical audited types are not duplicated as exported owners elsewhere.
- Service-local response-envelope interfaces remain private and acceptable.
- Empty type placeholders remain under entities/requests/responses.
- `src/types/sales/*` files are transitional compatibility barrels.
- `PaymentMethod` is truthfully a `string` because payment methods are
  tenant-owned backend records.

## 9. Error Architecture Audit

Canonical runtime error codes:

```text
frontend/src/types/enums/error-code.ts
```

Canonical application error normalization:

```text
frontend/src/lib/errors.ts
frontend/src/api/interceptors.ts
```

Findings:

- `ERROR_CODES` is a runtime constant and `ErrorCode` is derived from it.
- Axios errors are normalized through `AppError.fromAxios`.
- Session invalidation is centralized in `api/refresh.ts`.
- Unsupported operations currently throw generic `Error` instances with
  explicit unsupported-capability messages. A later migration can standardize
  these as `AppError`/domain errors.

## 10. Multi-Tenant Audit

Findings:

- `api/interceptors.ts` attaches `X-Tenant-ID` and `X-Branch-ID` from storage.
- Tenant context is currently derived from `Identity` in `useTenant`.
- Branch context is shell-store backed in `useCurrentBranch`.
- Services do not manually inject tenant/branch headers.
- Query keys do not include tenant or branch identity.
- Tenant/branch switching does not yet guarantee server-state cache partition
  or full invalidation.

Status:

```text
Partially compliant; tenant-aware transport exists, but query-cache isolation is unresolved.
```

## 11. Authorization Audit

Findings:

- Backend remains the security boundary.
- Navigation filters by `identity.permissions`.
- Route protection is currently authentication-only.
- `frontend/src/authorization/PermissionGuard.tsx`,
  `PermissionProvider.tsx`, `RoleGuard.tsx`, and `authorization/index.ts` are
  zero-byte placeholders.
- `ApplicationProvider` explicitly marks Authorization as future composition.
- No raw role-name checks were observed in active components.

Status:

```text
Partially implemented; missing centralized Authorization Context and route-level permission enforcement.
```

## 12. Module-Boundary Audit

Positive evidence:

- Services depend on API/client/types/base infrastructure only.
- Hooks depend on services, query keys, invalidation, and shared types.
- Components do not call services or Axios directly.
- Navigation helpers receive permissions as inputs.

Remaining boundary findings:

- `providers/ApplicationProvider.tsx` imports `ShellProvider` through a deep
  provider path rather than only through the public provider barrel.
- `types/navigation.ts` imports runtime-adjacent navigation ID and permission
  types from `navigation/`.
- `API_ENDPOINTS` publicly exposes speculative backend namespaces.
- Empty feature page files exist but router currently uses inline placeholders.

## 13. Naming Audit

Accepted transitional names:

- `useDeleteSupplier`: public compatibility name mapped to verified supplier
  deactivation.
- `filterNavigationByPermissions`: compatibility helper delegates to
  `filterNavigation`.

Private future names:

- `useDeleteProduct`
- `useUpdateProduct`
- `useUpdateCustomer`
- `useSalesDashboard`
- Procurement and Inventory workflow hook names

Misleading or dead names:

- `legacySalesService`
- zero-byte sales decomposition service files
- speculative endpoint namespaces for unsupported capabilities

## 14. Domain-Event Audit

Frontend domain events are not implemented.

Current workflow refresh is represented through centralized query invalidation.
No service was observed publishing frontend domain events. No event bus,
`publish`, `subscribe`, or domain-event runtime boundary was found.

Status:

```text
Deferred; ADR-010 is represented through workflow hooks and invalidation, not domain events.
```

## 15. Route And Navigation Audit

Active router paths:

- `/`
- `/login`
- `/dashboard`
- `/products`
- `/customers`
- `/inventory`
- `/sales`
- `/procurement`
- `/finance`
- `/reports`
- `/administration`
- `/settings`
- catch-all redirect

Navigation paths without matching route entries:

- `/sales/pos`
- `/sales/refunds`
- `/inventory/adjustments`
- `/warehouses`
- `/procurement/purchase-orders`
- `/procurement/suppliers`
- `/finance/expenses`
- `/finance/payments`
- `/finance/cashbook`
- `/reports/analytics`
- `/administration/users`
- `/administration/roles`
- `/administration/permissions`
- `/administration/branches`
- `/administration/warehouses`
- `/administration/payment-methods`
- `/settings/tenant`

Placeholder pages:

- Dashboard page returns `Dashboard Module (Coming Soon)`.
- Other routed modules render inline `Module (Coming Soon)` placeholders.
- Feature page files under several modules are zero-byte placeholders and are
  not wired into the router.

## 16. Unsupported Capability Audit

Unsupported capabilities not publicly operational:

- Procurement runtime service and hook barrels are closed.
- Inventory hook barrel is closed.
- Dashboard service and hook barrels are closed.
- Product update/delete hooks are private and reject.
- Customer update hook is private and rejects.
- Dashboard route is a placeholder and imports no Dashboard hook.

Known risk:

- `API_ENDPOINTS` still exposes unsupported endpoint constants.
- Public service instances inherit generic BaseService CRUD methods.
- `useSalesDashboard` is private but not disabled.

## 17. Dead And Transitional Source Inventory

Safe removal candidates after manual confirmation:

- zero-byte `services/sales/paymentService.ts`
- zero-byte `services/sales/receiptService.ts`
- zero-byte `services/sales/salesDashboardService.ts`
- zero-byte `services/sales/salesQueryService.ts`
- zero-byte `services/sales/salesWorkflowService.ts`
- zero-byte `authorization/*.tsx` and `authorization/index.ts` if not planned
  for the next Authorization migration
- zero-byte feature page placeholders not routed
- zero-byte empty type placeholder files
- `services/sales/legacySalesService.ts` if no historical import contract must
  be preserved

Backend-blocked keep candidates:

- `services/procurement/purchaseOrderService.ts`
- `services/procurement/goodsReceiptService.ts`
- `services/products/inventoryService.ts`
- `services/dashboard/dashboardService.ts`
- private Procurement, Inventory, Dashboard, and Sales dashboard hooks

Manual review candidates:

- public Finance services and Report service;
- Product category service;
- transitional `src/types/sales/*` compatibility barrels.

## 18. Bundle Warning Audit

Largest generated bundle:

```text
dist/assets/index-CXXQZlCT.js 733.60 kB
```

Likely causes:

- route tree is eagerly loaded;
- large UI/component dependencies are bundled into the main entry;
- no route-level lazy loading was observed in `app/router.tsx`.

No bundle optimization was performed.

## 19. Runtime Smoke Verification

Build smoke:

- application bootstrap compiles;
- production assets are emitted;
- `index.html`, JS, CSS, fonts, favicon, and icons exist under `dist/`.

Preview smoke:

- sandboxed preview failed to bind `127.0.0.1:4173` with `EPERM`;
- escalated preview started and printed `http://127.0.0.1:4173/`;
- sandboxed `curl` could not reach the escalated preview namespace;
- preview server was stopped with `Ctrl-C`.

Backend smoke was not attempted. No dependency installation was performed.

## 20. Updated ADR Compliance Matrix

| ADR | Status | Evidence | Remaining gaps | Follow-up |
| --- | --- | --- | --- | --- |
| ADR-001 Service Layer | Partially Compliant | Public supported facades exist; services have no React/query logic | inherited BaseService CRUD leakage; public Finance/Reports unverified; speculative private services | Service/public endpoint disposition |
| ADR-002 Query Hooks | Partially Compliant | Hooks use services and central invalidation | private `useSalesDashboard` lacks disabled guard; some unsupported private hooks retained | Unsupported hook hardening |
| ADR-003 Cache | Partially Compliant | Query keys and invalidation centralized | tenant/branch not in keys; dormant policies remain | Tenant-aware query scope |
| ADR-004 Types | Partially Compliant | Canonical audited types under `src/types` | empty placeholders and transitional barrels remain | Dead type shim removal |
| ADR-005 Errors | Partially Compliant | `AppError` and `ERROR_CODES` centralized | unsupported operations throw generic `Error` | Unsupported operation error standardization |
| ADR-006 Multi-Tenant | Partially Compliant | transport attaches tenant/branch headers | cache isolation unresolved; branch owner transitional | Tenant-aware cache migration |
| ADR-007 Authorization | Partially Implemented | navigation filters by identity permissions | no Authorization Context; route guards auth-only; guard files empty | Authorization Context Foundation |
| ADR-008 Module Boundaries | Partially Compliant | closed unsupported barrels; compile-safe public APIs | speculative endpoint constants; deep provider imports; empty page files | Dead/transitional boundary removal |
| ADR-009 Naming | Partially Compliant | canonical business facade names improved | misleading transitional names remain | Naming compatibility disposition |
| ADR-010 Domain Events | Deferred | workflow invalidation exists | no domain-event runtime | Domain-event design rebaseline |

## 21. Critical Remaining Risks

1. Tenant/branch cache isolation is not implemented in query keys.
2. Route-level authorization is not implemented beyond authentication.
3. Public endpoint registry exposes unsupported backend capabilities.
4. Inherited `BaseService` methods can expose transport-style operations on
   public service instances.
5. Navigation links exist for routes that are not registered.
6. Private Sales dashboard hook could fetch if deep-imported and mounted.
7. Finance and Reports public services need backend capability verification.

## 22. Safe Removal Candidates

Do not remove in Migration 044. Recommended later candidates:

- zero-byte Sales decomposition service files;
- zero-byte authorization placeholders after Authorization migration choice;
- zero-byte feature page placeholders if router keeps inline placeholders;
- empty type placeholder files;
- `legacySalesService.ts` after import-history confirmation.

## 23. Files Requiring Manual Review

- `frontend/src/api/endpoints.ts`
- `frontend/src/services/finance/index.ts`
- `frontend/src/services/reports/index.ts`
- `frontend/src/services/products/categoryService.ts`
- `frontend/src/services/products/inventoryService.ts`
- `frontend/src/services/procurement/*.ts`
- `frontend/src/services/dashboard/dashboardService.ts`
- `frontend/src/hooks/queries/sales/useSalesDashboard.ts`
- `frontend/src/routes/routes.ts`
- `frontend/src/navigation/navigation.ts`

## 24. Backend Blockers

- Backend Current User endpoint and Authorization Context contract.
- Registered Inventory API.
- Registered Procurement Purchase Order and Goods Receipt APIs.
- Registered Dashboard API.
- Registered Finance and Reports APIs, if those frontend services are to
  remain public.

## 25. Recommended Migration Sequence

1. Migration 045 - Tenant-Aware Query Scope
   - Purpose: add tenant/branch-safe server-state boundaries.
   - Scope: query-key design and invalidation behavior only.
   - ADRs: ADR-003, ADR-006.
   - Backend dependency: stable tenant/branch identity source.
   - Type: implementation.
   - Risk: high because it affects every server-state cache key.
   - Stop condition: active identity source remains ambiguous.

2. Migration 046 - Authorization Context Foundation
   - Purpose: centralize frontend permission evaluation for usability.
   - Scope: authorization provider/service/guards only.
   - ADRs: ADR-007, ADR-008.
   - Backend dependency: current-user or authorization-context endpoint.
   - Type: implementation.
   - Risk: medium.
   - Stop condition: backend permission payload is unresolved.

3. Migration 047 - Public Endpoint Registry Disposition
   - Purpose: close or classify unsupported endpoint constants.
   - Scope: `api/endpoints.ts` and service references only.
   - ADRs: ADR-001, ADR-008.
   - Backend dependency: route registry evidence.
   - Type: inspection plus narrow implementation.
   - Risk: medium.
   - Stop condition: endpoint constants are required by planned active work.

4. Migration 048 - Dead Transitional Boundary Removal
   - Purpose: remove proven dead zero-byte and obsolete private files.
   - Scope: files classified safe-removal in this report.
   - ADRs: ADR-004, ADR-008, ADR-009.
   - Backend dependency: none.
   - Type: implementation.
   - Risk: low to medium.
   - Stop condition: import history or planned ownership is uncertain.

5. Migration 049 - Route And Placeholder Disposition
   - Purpose: align navigation reachability with registered routes/placeholders.
   - Scope: route/navigation classification only.
   - ADRs: ADR-007, ADR-008, ADR-009.
   - Backend dependency: authorization context.
   - Type: inspection first.
   - Risk: medium.
   - Stop condition: product requirements for future routes are unclear.

6. Migration 050 - Bundle Code-Splitting
   - Purpose: address the Vite 500 kB chunk warning.
   - Scope: route-level lazy loading and dependency splitting.
   - ADRs: ADR-008.
   - Backend dependency: none.
   - Type: implementation.
   - Risk: medium.
   - Stop condition: route architecture is still in flux.

## 26. Files Inspected

Representative inspected areas:

- all ADRs `ADR-001` through `ADR-010`;
- baseline and recent migration reports;
- all public barrels under `src/api`, `src/authorization`, `src/components`,
  `src/features`, `src/hooks`, `src/navigation`, `src/providers`,
  `src/routes`, `src/services`, `src/store`, `src/types`, and
  `src/validation`;
- all service domain folders;
- `src/hooks/queries`;
- `src/lib/queryKeys.ts`;
- `src/lib/queryInvalidation.ts`;
- `src/lib/errors.ts`;
- `src/api`;
- `src/providers`;
- `src/store`;
- `src/routes`;
- `src/navigation`;
- `src/types`;
- active backend route files under `app/api`.

## 27. Source Files Changed

No runtime source files were changed.

## 28. Files Created

- `frontend/docs/architecture/reviews/MIGRATION-044-POST-MIGRATION-ARCHITECTURE-AUDIT.md`

## 29. Compiler Result Before And After

```text
Before audit: 0 TypeScript errors
After audit: 0 TypeScript errors
```

## 30. Build Result Before And After

```text
Before audit: npm run build passed
After audit: npm run build passed
```

## 31. Warnings

Only Vite chunk-size warning observed:

```text
Some chunks are larger than 500 kB after minification.
```

## 32. Invariants Verified

- TypeScript remains at zero errors.
- Production build remains successful.
- Closed unsupported barrels remain closed.
- Canonical audited type ownership remains intact.
- Services contain no React/query logic.
- Hooks contain no Axios or direct transport mapping.
- Query keys remain centrally owned.
- Invalidation remains centrally owned.
- Unsupported public operations are not active through UI.
- Backend remains the authorization security boundary.
- Tenant cache isolation gap is explicitly documented.
- No transitional source was removed.
- No backend file was changed.
- No feature behavior was changed.
- Next migration sequence follows ADR dependencies.

## 33. Rollback Boundary

Rollback is limited to removing this audit report.
