# Migration 045 - Tenant-Aware Query Scope Architecture

## 1. Migration Purpose

Migration 045 establishes the canonical tenant and branch scope contract for
future TanStack Query cache keys.

This migration is foundation-only. It does not migrate active domain hooks to
scoped keys because the current frontend session cannot reliably establish a
stable authenticated identity after token-only login.

No backend files, endpoint paths, headers, response mapping, DTO mappings,
Authorization Context, route protection, unsupported capability hooks, or bundle
configuration were changed.

## 2. ADR Rules Applied

- ADR-002: hooks own query composition and consume services.
- ADR-003: query-key construction remains centralized infrastructure.
- ADR-004: reusable scope contracts live under `src/types`.
- ADR-006: tenant-owned cache data must be isolated by tenant and branch.
- ADR-007: authorization was not implemented in query scope.
- ADR-008: query scope is shared infrastructure, not domain service logic.
- ADR-009: scope names use explicit tenant and branch terminology.

## 3. Current Verified Baseline

Pre-migration verification:

```bash
cd /home/thumbi/Hela360/frontend
npx tsc -b --pretty false
npm run build
```

Result:

```text
TypeScript exit code: 0
Vite build exit code: 0
```

Observed Vite warning:

```text
Some chunks are larger than 500 kB after minification.
```

The warning is unchanged from Migration 044 and remains deferred.

## 4. Canonical Scope Owners

Application tenant owner:

```text
frontend/src/store/authStore.ts
identity.tenantId
```

Application branch owner:

```text
frontend/src/store/shellStore.ts
selectedBranchId
```

Transport header source:

```text
frontend/src/lib/storage.ts
tenant_id
branch_id
```

Transport attachment:

```text
frontend/src/api/interceptors.ts
X-Tenant-ID
X-Branch-ID
```

Current blocker:

```text
AuthService.login maps token-only responses when identity is absent, and
AuthService.getCurrentUser remains unsupported. Therefore app-owned tenant scope
can be null while authenticated transport tokens exist.
```

Because application scope and transport header scope are not yet reconciled,
active domain hook migration would risk disabling valid queries or creating
incorrectly scoped cache entries.

## 5. Canonical Scope Types

New owner:

```text
frontend/src/types/domains/query-scope.ts
```

Contracts:

```typescript
TenantQueryScope
BranchQueryScope
QueryScope
QueryScopeReadiness
```

The scope contracts are cache identity contracts only. They do not imply
transport headers, backend tenancy enforcement, authorization checks, tenant
switching, or branch switching.

## 6. Canonical Query-Key Shape

New owner:

```text
frontend/src/lib/queryScope.ts
```

Tenant-scoped shape:

```text
["tenant", tenantId, domain, ...segments]
```

Branch-scoped shape:

```text
["tenant", tenantId, "branch", branchId, domain, ...segments]
```

Platform/static shape:

```text
["platform", domain, ...segments]
```

Identity/session shape:

```text
["identity", ...segments]
```

The helpers trim and reject empty tenant, branch, and domain identifiers. They
do not fabricate `"default"`, `"unknown"`, or placeholder scope values.

## 7. Runtime Scope Hook

New owner:

```text
frontend/src/hooks/useQueryScope.ts
```

`useQueryScope()` reads only from canonical application state:

- `authStore.identity?.tenantId`
- `shellStore.selectedBranchId`

It does not read browser storage, Axios interceptors, services, endpoint
constants, localStorage, sessionStorage, or backend payloads.

It returns readiness booleans and nullable scope objects so future query hooks
can gate scoped keys without inventing missing scope:

```typescript
isTenantScopeReady
isBranchScopeReady
tenantScope
branchScope
```

## 8. Backend Scope Inventory

Verified from current backend models and route filters:

| Domain | Scope disposition |
| --- | --- |
| Authentication identity | Session/identity-scoped; establishes tenant and optional branch. |
| Products | Tenant-scoped; product, category, brand, unit, and code models include `tenant_id`. |
| Customers | Tenant-scoped; `Customer` includes `tenant_id` and no `branch_id`. |
| Suppliers | Tenant-scoped; `Supplier` includes `tenant_id` and no `branch_id`. |
| Sales/POS | Tenant and branch-scoped; sales, tills, shifts, and refunds include branch context. |
| Inventory | Tenant and branch-scoped for warehouses, stock balances, and stock movements. |
| Administration users | Tenant-scoped with optional user branch assignment. |
| Administration roles | Tenant-scoped. |
| Administration permissions | Platform/static permission catalog; no tenant column on `Permission`. |
| Branches | Tenant-scoped. |
| Tenants | Platform/administration scope; not a tenant-owned descendant key. |

This inventory supports a scope-first key architecture, but it also shows why
domain-by-domain migration needs explicit tenant and branch readiness rules.

## 9. Domains Migrated

No active domain hook was migrated in this migration.

Foundation created:

- scope types
- pure query-scope key helpers
- React scope-readiness hook
- public type exports
- architecture report

## 10. Domains Deferred

Deferred until the session identity contract is stable:

- Products
- Customers
- Suppliers
- Sales
- Inventory
- Procurement
- Dashboard
- Finance
- Reports
- Administration

Reason:

```text
Current login can produce authenticated token state without frontend identity.
Migrating active hooks now would make tenant-scoped hooks unable to form keys in
that state.
```

Unsupported or speculative domains also remain deferred for their existing
Migration 044 reasons.

## 11. Invalidation Compatibility

Existing owner remains unchanged:

```text
frontend/src/lib/queryInvalidation.ts
```

Existing invalidation remains unscoped and compatible with the current
unscoped `QUERY_KEYS` hierarchy.

Future scoped invalidation should add helpers that accept
`TenantQueryScope` or `BranchQueryScope` and invalidate scope-first prefixes.
For example:

```text
["tenant", tenantId, "products"]
["tenant", tenantId, "branch", branchId, "sales"]
```

No mutation hook behavior changed in this migration.

## 12. Tenant/Branch Switch Behavior

Tenant switching is not implemented in the current frontend.

Branch selection currently lives in Shell state and is restored from storage by
`useInitializeShell()`. Persisted branch transport state is not yet reconciled
with shell branch state in a complete lifecycle contract.

Future scoped keys naturally isolate branch-specific data because branch keys
include both tenant and branch identifiers before the domain segment.

## 13. Logout Cache Disposition

Existing logout behavior remains unchanged:

```text
useLogout -> authStore.logout() -> storage.clearSession() -> queryClient.clear()
```

`queryClient.clear()` disposes all current query cache entries on logout. This
is compatible with both current unscoped keys and future scoped keys.

## 14. Static Verification

Commands used during the migration:

```bash
rg "QUERY_KEYS\\." frontend/src/hooks frontend/src/features frontend/src/components
rg "queryKey:\\s*\\[" frontend/src
rg "invalidateQueries" frontend/src
rg "localStorage|sessionStorage" frontend/src/lib/queryKeys.ts
rg "use[A-Za-z]+\\(" frontend/src/lib/queryKeys.ts
```

Findings:

- Active hooks continue to use centralized `QUERY_KEYS`.
- Direct invalidation remains centralized in `queryInvalidation.ts`.
- `queryKeys.ts` does not read browser storage.
- `queryKeys.ts` does not call React hooks.

## 15. Files Created

- `frontend/src/types/domains/query-scope.ts`
- `frontend/src/lib/queryScope.ts`
- `frontend/src/hooks/useQueryScope.ts`
- `frontend/docs/architecture/reviews/MIGRATION-045-TENANT-AWARE-QUERY-SCOPE.md`

## 16. Files Modified

- `frontend/src/types/domains/index.ts`
- `frontend/src/types/index.ts`

## 17. Post-Migration Verification

Post-migration verification:

```bash
cd /home/thumbi/Hela360/frontend
npx tsc -b --pretty false
npm run build
```

Result:

```text
TypeScript exit code: 0
Vite build exit code: 0
```

Observed Vite warning:

```text
Some chunks are larger than 500 kB after minification.
```

No new compiler or build failures were introduced.

## 18. Explicit Non-Changes

This migration did not:

- modify backend files
- implement Authorization Context
- change endpoint constants or paths
- change request headers
- change service response mapping
- change DTO ownership
- change active query hooks
- change invalidation behavior
- enable unsupported capabilities
- optimize production bundles

## 19. Recommended Next Migration

Recommended next migration:

```text
Migration 046 - Current User / Session Identity Scope Alignment
```

Suggested goal:

```text
Make authenticated frontend identity, storage tenant/branch state, and transport
tenant/branch headers derive from one verified session source before migrating
active domain hooks to scoped query keys.
```
