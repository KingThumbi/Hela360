# Migration 019 - Supplier Query Key Boundary

## 1. Migration Purpose

Migration 019 aligns the Supplier query-key namespace with ADR-003 and the verified Supplier hook contracts.

This migration is Supplier query-key only. It does not modify Supplier services, Supplier response mapping, backend files, invalidation policy, UI, navigation, or unrelated domain key namespaces.

## 2. ADR Rules Applied

- ADR-002: Supplier hooks consume services and use centralized query-key factories.
- ADR-003: every cache key originates from `src/lib/queryKeys.ts`; mutation hooks do not determine invalidation policy.
- ADR-006: tenant-scoped data must be cache-isolated; this remains unresolved in the current cross-domain key architecture.
- ADR-008: query keys are shared infrastructure and remain outside feature/service implementation details.
- ADR-009: key factory names use clear business-domain terminology.

## 3. Existing Supplier Key Hierarchy

Before this migration:

```typescript
suppliers: {
  root: ["suppliers"] as const,
  list: () => [...QUERY_KEYS.suppliers.root, "list"] as const,
  detail: (id) => [...QUERY_KEYS.suppliers.root, id] as const,
}
```

Problem:

```text
useSuppliers passed PaginationRequest params to QUERY_KEYS.suppliers.list(params), but list accepted no arguments.
```

The list key therefore could not distinguish different Supplier pages/searches and produced a TypeScript diagnostic.

## 4. Canonical Supplier Key Hierarchy

After this migration:

```typescript
suppliers.root
suppliers.lists()
suppliers.list(params?)
suppliers.details()
suppliers.detail(id)
```

This follows ADR-003 root-derived hierarchy while keeping `root`, `list`, and `detail` available for existing hook usage.

## 5. Root Key

Canonical Supplier root:

```typescript
QUERY_KEYS.suppliers.root
```

Value:

```text
["suppliers"]
```

Root invalidation still matches all Supplier descendant keys.

## 6. List Key

Canonical list key signature:

```typescript
QUERY_KEYS.suppliers.list(params?: PaginationRequest)
```

Shape:

```text
["suppliers", "list", normalizedParams]
```

`QUERY_KEYS.suppliers.lists()` returns the list namespace:

```text
["suppliers", "list"]
```

## 7. Detail Key

Canonical detail key signature:

```typescript
QUERY_KEYS.suppliers.detail(id: string | number)
```

Shape:

```text
["suppliers", "detail", id]
```

`QUERY_KEYS.suppliers.details()` returns the detail namespace:

```text
["suppliers", "detail"]
```

## 8. List Parameter Contract

The list key accepts the verified existing query input used by `useSuppliers`:

```typescript
PaginationRequest
```

Current fields:

- `page`
- `per_page`
- `search`
- `q`

No `SupplierFilters` type was created because no additional canonical Supplier-specific frontend list request exists.

Backend `SupplierListFilters` supports `is_active`, but the current frontend `PaginationRequest` and `useSuppliers` hook do not expose that field. Adding it would require a separate verified Supplier list-query request migration.

## 9. Parameter Normalization

Supplier list key parameters are normalized in `queryKeys.ts`.

Rules:

- default `page` is `1`
- default `per_page` is `25`
- `search` and `q` are trimmed
- empty `search` and `q` are omitted
- omitted optional fields produce stable equivalent keys
- normalized parameter objects are frozen
- no functions, Axios configs, URLSearchParams, or class instances are included

Example:

```text
QUERY_KEYS.suppliers.list({})
QUERY_KEYS.suppliers.list({ page: 1, per_page: 25 })
```

Both produce equivalent normalized pagination content.

## 10. Tenant-Scope Disposition

Tenant scope is unresolved in this Supplier-only migration.

Evidence:

- ADR-006 requires tenant-scoped data to be cache-isolated.
- `api/interceptors.ts` attaches tenant headers from storage.
- `authStore` stores an `identity` with `tenantId`.
- No current domain key namespace includes tenant scope.
- No canonical tenant-aware query-key helper exists.
- No stable `useTenant` hook exists in the current source tree.
- `queryKeys.ts` is a static factory and must not read localStorage or call React hooks.

Disposition:

```text
Path C - Tenant scoping not yet implementable narrowly
```

This migration fixes Supplier list/detail hierarchy and documents tenant cache isolation for a later cross-domain query-scope migration.

## 11. Branch-Scope Disposition

Supplier is verified as tenant-owned and tenant-wide.

No `branch_id` exists on the Supplier backend contract.

No branch component was added to Supplier keys.

## 12. Invalidation Compatibility

`invalidateSuppliers` remains unchanged:

```typescript
QUERY_KEYS.suppliers.root
```

Because all Supplier list and detail keys still derive from `["suppliers"]`, root invalidation continues to cover Supplier lists and details.

No hook directly calls `queryClient.invalidateQueries`.

## 13. Hooks Migrated

No Supplier hook behavior changed.

`useSuppliers` already called:

```typescript
QUERY_KEYS.suppliers.list(params)
```

This migration updates the key factory to match that verified hook contract.

`useSupplier` continues to call:

```typescript
QUERY_KEYS.suppliers.detail(id)
```

No query function, service method, enabled logic, mutation function, invalidation helper, or lifecycle behavior changed.

## 14. Files Inspected

- `frontend/src/lib/queryKeys.ts`
- `frontend/src/lib/queryInvalidation.ts`
- `frontend/src/hooks/queries/suppliers/useSuppliers.ts`
- `frontend/src/hooks/queries/suppliers/useSupplier.ts`
- `frontend/src/hooks/queries/suppliers/useCreateSupplier.ts`
- `frontend/src/hooks/queries/suppliers/useUpdateSupplier.ts`
- `frontend/src/hooks/queries/suppliers/useDeleteSupplier.ts`
- `frontend/src/services/suppliers/`
- `frontend/src/types/requests/pagination-request.ts`
- `frontend/src/types/api/`
- `frontend/src/store/authStore.ts`
- `frontend/src/store/shellStore.ts`
- `frontend/src/providers/ShellProvider.tsx`
- `frontend/src/hooks/useCurrentBranch.ts`
- `frontend/src/api/interceptors.ts`
- `frontend/src/lib/storage.ts`

## 15. Files Created

- `frontend/docs/architecture/reviews/MIGRATION-019-SUPPLIER-QUERY-KEY-BOUNDARY.md`

## 16. Files Modified

- `frontend/src/lib/queryKeys.ts`

## 17. Compiler Errors Before

Baseline:

```text
196 TypeScript errors
```

Supplier query-key diagnostic before:

```text
src/hooks/queries/suppliers/useSuppliers.ts(66,31): error TS2554: Expected 0 arguments, but got 1.
```

## 18. Compiler Errors After

Post-migration:

```text
195 TypeScript errors
```

Net reduction:

```text
1
```

Supplier query-key diagnostic after:

```text
Resolved.
```

## 19. New Diagnostics

No new diagnostics were introduced.

## 20. Remaining Supplier Blockers

No Supplier service/hook/query-key diagnostics remain.

Remaining lines containing Supplier are not Supplier domain query-key blockers:

- Procurement `SupplierDelivery` frontend-only assumptions.
- Navigation ID backlog for `"suppliers"`.
- Missing tenant-scoped query-key architecture across all domains.

## 21. Runtime And Cache Behavior

Supplier data fetching behavior remains equivalent.

Cache behavior improves for Supplier list queries:

- different pages now receive distinct query keys
- different `per_page` values now receive distinct query keys
- different search terms now receive distinct query keys
- Supplier root invalidation still refreshes list and detail descendants

Tenant cache isolation is not fully resolved and remains documented for a later architecture-wide migration.

## 22. Invariants Verified

- Every active Supplier query key originates from `queryKeys.ts`.
- Supplier list keys include verified list parameters.
- Supplier detail keys include Supplier identity.
- Supplier root invalidation covers list and detail keys.
- Supplier keys are deterministic and serializable.
- Tenant scope is documented as unresolved instead of fabricated.
- Supplier does not incorrectly require branch ownership.
- Supplier hooks own no hardcoded query arrays.
- Supplier services contain no cache logic.
- Supplier hooks do not determine invalidation policy.
- No Supplier service method changed.
- No Supplier response mapping changed.
- No backend file changed.
- No unrelated domain key changed.

## 23. Rollback Boundary

Rollback is limited to:

- `frontend/src/lib/queryKeys.ts`
- `frontend/docs/architecture/reviews/MIGRATION-019-SUPPLIER-QUERY-KEY-BOUNDARY.md`

## 24. Recommended Next Migration

Recommended next migration:

```text
Migration 020 - Customer Service Facade and Response Boundary
```

Rationale:

Customer hooks still show the same facade/response-envelope drift already fixed for Supplier: missing `findById`, create/update `ApiResponse<Customer>` envelope mismatches, and list query-key parameter drift.
