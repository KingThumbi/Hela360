# Migration 052 - Tenant-Scoped Active Queries

## 1. Migration Purpose

Migration 052 connects the tenant-aware query-scope foundation from Migration
045 to the currently supported tenant-owned server-state domains:

- Products
- Customers
- Suppliers

The goal is to prevent TanStack Query cache reuse across tenants while
preserving existing service transport behavior and mutation callback ordering.

No feature pages, routes, backend files, unsupported domains, auth/session
hydration, or query invalidation redesigns were introduced.

## 2. ADR Rules Applied

- ADR-002: query hooks continue to call services and compose TanStack Query.
- ADR-003: query keys remain centralized in `queryKeys.ts`; invalidation
  remains centralized in `queryInvalidation.ts`.
- ADR-006: tenant-owned server state must be cache-isolated by tenant.
- ADR-008: services remain cache/scope agnostic; hooks consume scope.
- ADR-009: query-key and invalidation names stay explicit.

## 3. Clean Starting Baseline

Commands:

```bash
cd /home/thumbi/Hela360/frontend
npx tsc -b --pretty false
npm run build
```

Result:

```text
TypeScript errors: 0
Vite build: PASS
```

Existing warning recorded only:

```text
Some chunks are larger than 500 kB after minification.
```

## 4. Canonical Scope Source

Canonical tenant scope source:

```text
GET /api/auth/session
  -> authStore.identity.tenantId
  -> useQueryScope().tenantScope
```

Verified:

- tenant id comes from hydrated authenticated identity;
- tenant readiness is false while auth initialization is active;
- branch selection remains independent in `shellStore.selectedBranchId`;
- Products, Customers, and Suppliers are tenant-wide, not branch-scoped;
- `useQueryScope()` reads no browser storage;
- no synthetic tenant ids are fabricated.

Transport consistency:

- Migration 048 synchronizes verified session tenant id to storage.
- `api/interceptors.ts` reads storage and attaches `X-Tenant-ID`.
- Query keys and transport tenant context therefore derive from the verified
  current session path.

## 5. Product Keys

Before:

```text
["products"]
["products", "list", normalizedParams]
["products", "detail", id]
["products", "by-code", code]
```

After:

```text
["tenant", tenantId, "products"]
["tenant", tenantId, "products", "list"]
["tenant", tenantId, "products", "list", normalizedParams]
["tenant", tenantId, "products", "detail"]
["tenant", tenantId, "products", "detail", id]
["tenant", tenantId, "products", "by-code", code]
```

Owner:

```text
frontend/src/lib/queryKeys.ts
```

The by-code key is tenant-aware, but no new by-code hook was added.

## 6. Customer Keys

Before:

```text
["customers"]
["customers", "list", normalizedParams]
["customers", "detail", id]
```

After:

```text
["tenant", tenantId, "customers"]
["tenant", tenantId, "customers", "list"]
["tenant", tenantId, "customers", "list", normalizedParams]
["tenant", tenantId, "customers", "detail"]
["tenant", tenantId, "customers", "detail", id]
```

## 7. Supplier Keys

Before:

```text
["suppliers"]
["suppliers", "list", normalizedParams]
["suppliers", "detail", id]
```

After:

```text
["tenant", tenantId, "suppliers"]
["tenant", tenantId, "suppliers", "list"]
["tenant", tenantId, "suppliers", "list", normalizedParams]
["tenant", tenantId, "suppliers", "detail"]
["tenant", tenantId, "suppliers", "detail", id]
```

## 8. Tenant-Wide Branch Disposition

Products, Customers, and Suppliers include `tenantId` in cache identity and do
not include selected branch.

Changing branch while staying in the same tenant therefore reuses the same
tenant-wide Product, Customer, and Supplier caches.

## 9. Hook Scope Integration

Migrated query hooks:

- `useProducts`
- `useProduct`
- `useCustomers`
- `useCustomer`
- `useSuppliers`
- `useSupplier`

Each hook now consumes `useQueryScope()` and only creates tenant-scoped keys
when `tenantScope` exists.

Before tenant readiness, hooks use stable identity-scoped disabled sentinel
keys:

```text
["identity", "disabled", domain, ...segments]
```

No fake tenant id such as `unknown`, `default`, or `none` is used.

## 10. Query Enablement Semantics

List hooks:

```text
enabled = isTenantScopeReady
```

Detail hooks:

```text
enabled = isTenantScopeReady && Boolean(id) && caller enabled option
```

Service query functions remain unchanged and are not called before tenant
readiness.

## 11. Product Invalidation

`invalidateProducts` now requires `TenantQueryScope` and invalidates:

```text
["tenant", tenantId, "products"]
```

This root covers only that tenant's Product list, detail, and by-code
descendants.

## 12. Customer Invalidation

`invalidateCustomers` now requires `TenantQueryScope` and invalidates:

```text
["tenant", tenantId, "customers"]
```

This root covers only that tenant's Customer list and detail descendants.

## 13. Supplier Invalidation

`invalidateSuppliers` now requires `TenantQueryScope` and invalidates:

```text
["tenant", tenantId, "suppliers"]
```

This root covers only that tenant's Supplier list and detail descendants.

## 14. Mutation Integration

Migrated operational mutations:

- `useCreateProduct`
- `useCreateCustomer`
- `useCreateSupplier`
- `useUpdateSupplier`
- `useDeleteSupplier`

Each mutation obtains `tenantScope` through `useQueryScope()`, preserves the
existing service method and payload, and invalidates only the active tenant root
after successful mutation.

Supplier `useDeleteSupplier` remains the transitional deactivation name.

Unsupported mutation disposition:

- Product update/delete placeholders remain unsupported and no longer pass
  Product invalidation callbacks.
- Customer update remains unsupported and no longer passes Customer invalidation.
- Customer delete was not migrated into tenant-scoped invalidation because this
  migration only verifies Customer create as active.

## 15. Tenant Switch Behavior

Tenant switching was not implemented.

Cache isolation now ensures:

```text
Tenant A product list key != Tenant B product list key
Tenant A customer detail 1 key != Tenant B customer detail 1 key
Tenant A supplier list key != Tenant B supplier list key
```

Prior-tenant inactive caches may remain in memory until garbage-collected or
cleared by logout, but they are no longer reused by another tenant.

## 16. Branch Switch Behavior

Branch switching does not alter Product, Customer, or Supplier keys because
these domains are tenant-wide.

Sales, Inventory, and future branch-owned domains remain deferred.

## 17. Logout Cache Disposition

Existing `useLogout()` already clears the QueryClient after local session
cleanup:

```text
queryClient.clear()
```

No logout cache behavior was changed.

## 18. Transport And Cache Scope Consistency

The HTTP tenant header and query cache tenant identity both originate from the
hydrated current session:

```text
current session -> authStore.identity.tenantId -> storage tenant id
current session -> authStore.identity.tenantId -> useQueryScope tenant id
```

No Product, Customer, or Supplier service method received tenant ids directly.
Services remain transport/scope agnostic.

## 19. Hardcoded-Key Audit

Commands:

```bash
rg "queryKey:\\s*\\[" frontend/src
rg "invalidateQueries" frontend/src
rg "\\[\"products\"" frontend/src
rg "\\[\"customers\"" frontend/src
rg "\\[\"suppliers\"" frontend/src
```

Findings:

- no raw Product, Customer, or Supplier array keys remain;
- direct `invalidateQueries` calls remain centralized in
  `queryInvalidation.ts`;
- no component owns Product, Customer, or Supplier invalidation.

## 20. Unsupported Domains Unchanged

No tenant-scoped keys were created for:

- Inventory
- Procurement
- Dashboard
- unsupported Sales read queries
- Finance
- Reports
- Administration

Cross-domain operation helpers that do not yet receive tenant scope no longer
globally invalidate newly scoped Customer or Supplier roots.

Full scoped Sales/Procurement invalidation remains deferred until those
operation hooks can supply the correct tenant or branch scope.

## 21. Administration Deferred

Administration queries remain deferred because users, roles, permissions,
branches, and tenants have mixed tenant/platform semantics and require a
separate verification migration.

## 22. Tests And Static Verification

No frontend test harness exists, so no unit tests were added.

Static verification confirmed:

- active Product, Customer, and Supplier query hooks consume `useQueryScope`;
- active Product, Customer, and Supplier keys include tenant identity;
- selected branch is absent from those keys;
- active mutations invalidate scoped roots;
- services remain query/cache agnostic.

## 23. Files Inspected

Inspected:

- ADR-002, ADR-003, ADR-006, ADR-008, ADR-009;
- Migration 019, 021, 023, 045, and 048 reports;
- `frontend/src/lib/queryKeys.ts`;
- `frontend/src/lib/queryScope.ts`;
- `frontend/src/lib/queryInvalidation.ts`;
- `frontend/src/hooks/useQueryScope.ts`;
- Product, Customer, and Supplier query hooks;
- Product, Customer, and Supplier services;
- auth/logout and query provider cache behavior;
- API interceptors and storage tenant synchronization.

## 24. Files Created

- `frontend/docs/architecture/reviews/MIGRATION-052-TENANT-SCOPED-ACTIVE-QUERIES.md`

## 25. Files Modified

- `frontend/src/lib/queryKeys.ts`
- `frontend/src/lib/queryInvalidation.ts`
- `frontend/src/hooks/queries/products/useProducts.ts`
- `frontend/src/hooks/queries/products/useProduct.ts`
- `frontend/src/hooks/queries/products/useCreateProduct.ts`
- `frontend/src/hooks/queries/products/useUpdateProduct.ts`
- `frontend/src/hooks/queries/products/useDeleteProduct.ts`
- `frontend/src/hooks/queries/customers/useCustomers.ts`
- `frontend/src/hooks/queries/customers/useCustomer.ts`
- `frontend/src/hooks/queries/customers/useCreateCustomer.ts`
- `frontend/src/hooks/queries/customers/useUpdateCustomer.ts`
- `frontend/src/hooks/queries/customers/useDeleteCustomer.ts`
- `frontend/src/hooks/queries/suppliers/useSuppliers.ts`
- `frontend/src/hooks/queries/suppliers/useSupplier.ts`
- `frontend/src/hooks/queries/suppliers/useCreateSupplier.ts`
- `frontend/src/hooks/queries/suppliers/useUpdateSupplier.ts`
- `frontend/src/hooks/queries/suppliers/useDeleteSupplier.ts`

No backend files were modified.

## 26. Verification Results

Before:

```text
npx tsc -b --pretty false: PASS
npm run build: PASS
```

After:

```text
npx tsc -b --pretty false: PASS
npm run build: PASS
```

Warning:

```text
Some chunks are larger than 500 kB after minification.
```

No new warning category was introduced.

## 27. Remaining Scope Work

Deferred:

- branch-scoped Sales/POS keys and invalidation;
- branch-scoped Inventory keys;
- Procurement route/page activation and scoped Supplier page usage;
- Dashboard/Finance/Reports scope verification;
- Administration mixed tenant/platform query scopes;
- full cross-domain scoped invalidation for Sales and Procurement operations.

## 28. Runtime Behavior Confirmation

Expected behavior:

- same tenant plus same normalized request produces the same key;
- different tenants never share Product, Customer, or Supplier keys;
- Product/Customer/Supplier queries do not run before tenant readiness;
- Product/Customer/Supplier mutations invalidate only the active tenant;
- branch changes do not duplicate tenant-wide caches;
- logout clears cached query data through the existing QueryClient clear path.

## 29. Invariants Verified

Verified:

1. Product cache is tenant-isolated.
2. Customer cache is tenant-isolated.
3. Supplier cache is tenant-isolated.
4. Tenant-wide cache identity ignores selected branch.
5. Different tenants cannot share list/detail keys.
6. Mutation invalidation cannot cross tenant boundaries for migrated mutations.
7. Query-key factories remain pure.
8. `queryKeys.ts` imports no React, stores, or storage.
9. Services remain scope agnostic.
10. Hooks derive scope from hydrated authenticated state.
11. No unsupported capability receives new active keys.
12. No route/page behavior changed.
13. No backend file changed.
14. TypeScript remains at zero errors.
15. Production build remains successful.

## 30. Rollback Boundary

Rollback is limited to:

- restore Product, Customer, and Supplier key factories to unscoped roots;
- restore Product, Customer, and Supplier query hooks to unscoped key usage;
- restore unscoped invalidation callbacks in migrated mutations;
- remove this report.

No backend rollback is required.

## 31. Recommended Next Migration

Recommended next migration:

```text
Migration 053 - Branch-Scoped Sales Operation Keys And Invalidation
```

Goal:

```text
Introduce tenant-and-branch cache identity for verified Sales/POS operation
hooks without activating unsupported sales read/list queries.
```

