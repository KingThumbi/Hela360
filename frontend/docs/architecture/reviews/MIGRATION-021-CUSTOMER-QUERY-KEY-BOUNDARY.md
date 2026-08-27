# Migration 021 - Customer Query Key Boundary

## 1. Migration Purpose

Migration 021 aligns the Customer query-key namespace with the architecture-first query-key rules and the verified Customer hook/service contracts.

This migration is Customer-only. It does not modify Customer service methods, backend routes, invalidation policy, Customer UI, or unrelated domains.

## 2. ADR Rules Applied

- ADR-002: hooks continue to use services and centralized query keys.
- ADR-003: query keys originate from `src/lib/queryKeys.ts` and use stable namespace hierarchies.
- ADR-006: tenant-owned data must be cache-isolated; no tenant context may be fabricated inside services.
- ADR-008: Customer hook and service ownership boundaries remain unchanged.
- ADR-009: query-key names use explicit domain language.

## 3. Previous Customer Key Hierarchy

Before this migration, the Customer namespace exposed:

```typescript
root: ["customers"]
list: () => ["customers", "list"]
detail: (id) => ["customers", id]
```

`useCustomers` passed pagination params to `QUERY_KEYS.customers.list(params)`, but the factory accepted no arguments. That produced a Customer query-key compiler diagnostic.

## 4. Canonical Customer Key Hierarchy

The canonical Customer hierarchy is now:

```typescript
root: ["customers"]
lists: () => ["customers", "list"]
list: (params?) => ["customers", "list", normalizedParams]
details: () => ["customers", "detail"]
detail: (id) => ["customers", "detail", id]
```

This mirrors the established Supplier list/detail shape without introducing branch scope or tenant reads inside the key factory.

## 5. Root Key

The Customer root remains:

```typescript
["customers"]
```

This keeps compatibility with existing broad invalidation calls that invalidate the Customer namespace root.

## 6. List Key Signature

The canonical Customer list key signature is:

```typescript
list: (params?: PaginationRequest) => readonly unknown[]
```

The list key includes normalized list params so different Customer list requests do not collide in TanStack Query cache.

## 7. Detail Key Signature

The canonical Customer detail key signature is:

```typescript
detail: (id: string | number) => readonly unknown[]
```

The detail key now includes an explicit `"detail"` segment before the id.

## 8. List Parameter Contract

The current frontend Customer hook and service contract uses `PaginationRequest`.

Verified backend `GET /customers` supports `search` and `is_active`, but the frontend Customer list boundary currently exposes only `PaginationRequest`. No Customer-specific list request type was added because no typed Customer-specific frontend filter contract exists in the migrated Customer hooks.

## 9. Parameter Normalization

Customer list keys use the shared pagination normalizer in `queryKeys.ts`.

The normalizer trims optional `search` and `q` values and omits empty strings from the final key object.

## 10. Default Parameter Values

Customer list keys default missing pagination values to:

- `page: 1`
- `per_page: 25`

These defaults create stable list keys for equivalent requests.

## 11. Tenant-Scope Disposition

Customer records are tenant-owned.

Verified backend evidence:

- `app/models/customer.py` includes `tenant_id`.
- `app/api/customers.py` obtains tenant context through `g.tenant_id`.

The current frontend architecture does not yet provide a stable tenant-aware query-key helper. `queryKeys.ts` remains pure and does not read browser storage, interceptors, or hooks.

Tenant cache isolation is therefore documented as an unresolved architecture boundary for a future tenant-context query-key migration.

## 12. Branch-Scope Disposition

Customer records are not branch-scoped in the verified model.

Verified backend evidence:

- `app/models/customer.py` does not include `branch_id`.
- `app/api/customers.py` reads branch context but does not apply it to Customer queries.

No branch id was added to Customer query keys.

## 13. Invalidation Compatibility

Existing invalidation remains compatible because Customer root is unchanged:

```typescript
QUERY_KEYS.customers.root
```

No invalidation helper behavior was changed in this migration.

## 14. Hooks Migrated

No hook edits were required in this migration.

Existing migrated hooks already use the canonical factories:

- `useCustomers` calls `QUERY_KEYS.customers.list(params)`
- `useCustomer` calls `QUERY_KEYS.customers.detail(id)`

## 15. Files Inspected

- `frontend/src/lib/queryKeys.ts`
- `frontend/src/lib/queryInvalidation.ts`
- `frontend/src/hooks/queries/customers/useCustomers.ts`
- `frontend/src/hooks/queries/customers/useCustomer.ts`
- `app/api/customers.py`
- `app/models/customer.py`
- ADR-002
- ADR-003
- ADR-006
- ADR-008
- ADR-009
- Migration 001 report
- Migration 014 report
- Migration 019 report
- Migration 020 report

## 16. Files Created

- `frontend/docs/architecture/reviews/MIGRATION-021-CUSTOMER-QUERY-KEY-BOUNDARY.md`

## 17. Files Modified

- `frontend/src/lib/queryKeys.ts`

## 18. Compiler Errors Before

Frontend compiler baseline before this migration:

```text
193 TypeScript errors
```

## 19. Compiler Errors After

Frontend compiler count after this migration:

```text
192 TypeScript errors
```

## 20. Net Reduction

This migration reduced the frontend TypeScript baseline by:

```text
1 error
```

## 21. Customer Query-Key Diagnostics Before and After

Before:

```text
useCustomers passed params to QUERY_KEYS.customers.list(params), but list accepted no arguments.
```

After:

```text
No Customer query-key arity diagnostic remains.
```

Remaining Customer diagnostics are unrelated to this query-key boundary:

```text
src/hooks/queries/customers/useUpdateCustomer.ts(57,7): error TS2322
src/navigation/navigation.ts(102,5): error TS2322
src/navigation/navigation.ts(106,9): error TS2322
```

## 22. New Diagnostics

No new diagnostics were introduced by this migration.

## 23. Remaining Customer Blockers

- `useUpdateCustomer` still expects `Promise<Customer>` while the inherited service update path returns `Promise<ApiResponse<Customer>>`.
- No verified Customer backend update route exists.
- Customer navigation ids remain outside the current `NavigationSectionId` and `NavigationItemId` unions.
- `useDeleteCustomer` still depends on an unsupported inherited delete route at runtime, but it does not currently produce a TypeScript diagnostic.

## 24. Runtime and Cache Behavior

Runtime fetching behavior is unchanged.

Customer list cache keys now distinguish normalized pagination and search params. Customer detail keys now live under a stable detail namespace.

## 25. Invariants Verified

- No backend files were modified.
- No Customer service method was added or renamed.
- No update, delete, deactivate, or reactivate behavior was fabricated.
- No branch scope was added to Customer keys.
- No tenant id was read from storage inside `queryKeys.ts`.
- Existing Customer root invalidation remains compatible.

## 26. Rollback Boundary

This migration can be rolled back by reverting:

- the Customer namespace changes in `frontend/src/lib/queryKeys.ts`
- this review document

No backend, service, or hook rollback is required.

## 27. Recommended Next Migration

Recommended next migration:

```text
Migration 022 - Product Service Facade and Query-Key Boundary
```

Product still has service facade and query-key diagnostics that mirror the now-resolved Supplier and Customer migration pattern.
