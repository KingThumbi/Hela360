# Migration 012 - Common Query Hook Option Contracts

## 1. Migration Purpose

Migration 012 establishes the canonical shared option contract for single-entity TanStack Query hooks.

The immediate compiler symptom was:

```text
Module '"@/hooks/queries/common"' has no exported member 'UseEntityOptions'
```

## 2. ADR Rules Applied

- ADR-002: query hooks own query execution and communicate through services.
- ADR-003: query keys remain centralized and hook-owned.
- ADR-004: business entities remain under `src/types`; hook infrastructure contracts stay with hook infrastructure.
- ADR-008: shared hook contracts are exported through stable public barrels.
- ADR-009: canonical hook option type names use PascalCase.

## 3. Common Option Types Found

Found existing canonical definition:

```text
frontend/src/hooks/queries/common/useEntity.ts::UseEntityOptions
```

Other common hooks use inline option types based on TanStack Query:

- `useEntityList`
- `usePaginatedQuery`
- `useSearchQuery`
- `useCreateEntity`
- `useUpdateEntity`
- `useDeleteEntity`

Only `UseEntityOptions` was already named and consumed by domain hooks.

## 4. Duplicate Option Contracts Found

No exact local duplicate of `UseEntityOptions` was found. The missing contract was an existing-but-unexported type.

Dashboard hooks define local dashboard-specific option aliases over `UseQueryOptions`; those were retained because they are outside single-entity hook scope.

## 5. Affected Hooks Inspected

Inspected:

- `frontend/src/hooks/queries/sales/useSale.ts`
- `frontend/src/hooks/queries/sales/useReceipt.ts`
- `frontend/src/hooks/queries/sales/useSalePayment.ts`
- `frontend/src/hooks/queries/suppliers/useSupplier.ts`
- `frontend/src/hooks/queries/products/useProduct.ts`
- `frontend/src/hooks/queries/customers/useCustomer.ts`
- `frontend/src/hooks/queries/inventory/useStockItem.ts`
- `frontend/src/hooks/queries/procurement/useGoodsReceipt.ts`
- `frontend/src/hooks/queries/procurement/usePurchaseOrder.ts`
- `frontend/src/hooks/queries/procurement/usePurchaseRequisition.ts`

All consumers use the same semantic shape:

```typescript
options?: UseEntityOptions<TEntity, TData>
```

Each hook owns its ID handling, query key, query function, and default `enabled: Boolean(id)` behavior.

## 6. Installed TanStack Query Version

Installed version:

```text
@tanstack/react-query ^5.101.2
```

The contract therefore uses v5 terminology, including `gcTime` rather than `cacheTime`.

## 7. Canonical Option Owner

Canonical owner:

```text
frontend/src/hooks/queries/common/useEntity.ts
```

Canonical export:

```text
frontend/src/hooks/queries/common/index.ts
```

## 8. Canonical Type Name

```text
UseEntityOptions
```

The name was preserved because consumers already used it and it matches the common `useEntity` hook.

## 9. Fields Exposed

The narrowed contract exposes:

- `enabled`
- `staleTime`
- `gcTime`
- `retry`
- `refetchOnWindowFocus`
- `refetchOnMount`
- `refetchOnReconnect`
- `select`
- `placeholderData`
- `initialData`

## 10. Fields Intentionally Hidden

Hidden hook-owned fields:

- `queryKey`
- `queryFn`

The contract does not expose service access, cache invalidation, query-key construction, URL construction, DTO ownership, or domain-specific options.

## 11. Generic Parameters Used

`UseEntityOptions` uses:

- `TQueryFnData`
- `TData`
- `TQueryKey`

`TData` is needed because affected hooks support selected query data through `select`. `TQueryKey` is used internally to stay assignable to `useEntity` and TanStack Query option typing without exposing query-key control to consumers.

## 12. Common Barrel Disposition

Updated:

```text
frontend/src/hooks/queries/common/index.ts
```

Added:

```typescript
export type {
  UseEntityOptions,
} from "./useEntity";
```

## 13. Higher-Level Barrel Disposition

`frontend/src/hooks/queries/index.ts` already re-exports `./common`. No higher-level barrel change was required.

No `frontend/src/hooks/index.ts` file was present to update.

## 14. Local Option Types Retained

Retained local dashboard option aliases because they are not exact single-entity option duplicates and were outside this migration.

## 15. Files Inspected

- `frontend/src/hooks/queries/common/*`
- `frontend/src/hooks/queries/*`
- `frontend/src/lib/queryFactory.ts`
- `frontend/src/lib/queryKeys.ts`
- `frontend/src/lib/queryClient.ts`
- ADR-002, ADR-003, ADR-004, ADR-008, ADR-009
- Migration 008 and 011 review documents

## 16. Files Created

- `frontend/docs/architecture/reviews/MIGRATION-012-COMMON-QUERY-HOOK-OPTIONS.md`

## 17. Files Modified

- `frontend/src/hooks/queries/common/useEntity.ts`
- `frontend/src/hooks/queries/common/index.ts`

No backend files were modified.

## 18. Imports Migrated

No hook import paths changed. Existing imports from `@/hooks/queries/common` now resolve because the common barrel exports the type.

## 19. Compiler Errors Before

Baseline:

```text
228 TypeScript errors
```

## 20. Compiler Errors After

Post-migration count:

```text
218 TypeScript errors
```

Command:

```bash
npx tsc -b --pretty false 2>&1 | grep -c "error TS"
```

## 21. Net Reduction

```text
10 fewer TypeScript errors
```

## 22. Missing UseEntityOptions Diagnostics Before And After

Before, `UseEntityOptions` was missing from the common hook barrel in these hooks:

- `useCustomer`
- `useProduct`
- `useStockItem`
- `useGoodsReceipt`
- `usePurchaseOrder`
- `usePurchaseRequisition`
- `useSupplier`
- `useSale`
- `useSalePayment`
- `useReceipt`

After:

```text
0 UseEntityOptions missing-export diagnostics
```

## 23. Newly Exposed Diagnostics

No new `UseEntityOptions` incompatibility diagnostics were introduced.

Previously masked downstream errors remain visible, including missing entity owners and missing service methods.

## 24. New Diagnostics

No new diagnostics were introduced by this migration.

The existing `queryFactory.ts` unused generic diagnostic remains:

```text
src/lib/queryFactory.ts(...): 'TData' is declared but its value is never read
```

That file was inspected but not modified because it is not required for this migration.

## 25. Remaining Hook Blockers

Remaining affected-hook blockers include:

- missing entity contracts such as `Customer`, `Product`, `Receipt`, `InventoryItem`, `GoodsReceipt`, `PurchaseOrder`, and `PurchaseRequisition`
- missing service methods such as `findById`, `getSale`, `getReceipt`, and `getSalePayment`
- query-key mismatches such as `QUERY_KEYS.sales.sale`
- supplier response-envelope mismatches from Migration 011

These are explicitly deferred.

## 26. Invariants Verified

- Shared query-hook options have one canonical owner.
- `UseEntityOptions` is exported as a type.
- Hooks still own query keys.
- Hooks still own query functions.
- Consumers cannot override `queryKey` or `queryFn`.
- Common options contain no domain business fields.
- Domain-specific dashboard option aliases remain local.
- No service method changed.
- No query key changed.
- No cache invalidation changed.
- No hook runtime behavior changed.
- No backend file changed.
- No unrelated domain was modified.
- Type-only exports comply with `verbatimModuleSyntax`.
- Generics are used by the contract and affected hook signatures.

## 27. Rollback Boundary

Rollback is limited to:

- the `UseEntityOptions` narrowing in `useEntity.ts`
- the type export in `common/index.ts`
- this migration report

## 28. Recommended Next Migration

Recommended next migration:

```text
Migration 013 — Product/Customer Entity Type Ownership
```

Reason: after `UseEntityOptions` is resolved, multiple remaining single-entity hooks are blocked by missing canonical entity/request type ownership for Product and Customer.
