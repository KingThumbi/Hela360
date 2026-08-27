# Migration 008 - Supplier Hook Boundary

## 1. Migration Purpose

Migration 008 established a single supplier hook public boundary by removing the duplicate inline `useDeleteSupplier` implementation from the supplier hook barrel.

The migration resolved the `useDeleteSupplier` redeclaration/export conflict without changing supplier hook runtime behavior, supplier services, query keys, invalidation policy, DTOs, entities, or feature UI.

## 2. ADR Rules Applied

- ADR-002: supplier hooks remain query/mutation hooks that call services and invalidation helpers.
- ADR-003: cache invalidation policy remains centralized and unchanged.
- ADR-004: hook barrels do not define reusable supplier DTOs or entities.
- ADR-008: the supplier domain hook barrel is the public boundary for supplier hooks.
- ADR-009: hook names remain canonical `use*` names.

## 3. Supplier Hooks Found

Implemented supplier hooks:

- `useSuppliers`
- `useSupplier`
- `useCreateSupplier`
- `useUpdateSupplier`
- `useDeleteSupplier`

Hook implementation files:

- `frontend/src/hooks/queries/suppliers/useSuppliers.ts`
- `frontend/src/hooks/queries/suppliers/useSupplier.ts`
- `frontend/src/hooks/queries/suppliers/useCreateSupplier.ts`
- `frontend/src/hooks/queries/suppliers/useUpdateSupplier.ts`
- `frontend/src/hooks/queries/suppliers/useDeleteSupplier.ts`

## 4. Supplier Barrel Structure Before Migration

Before migration, `frontend/src/hooks/queries/suppliers/index.ts` contained:

- an inline `useDeleteSupplier` implementation
- a default export for that inline implementation
- re-exports for all supplier hook files, including `useDeleteSupplier` from `./useDeleteSupplier`

## 5. Duplicate Declarations Found

`useDeleteSupplier` was declared in two places:

- inline inside `frontend/src/hooks/queries/suppliers/index.ts`
- separately inside `frontend/src/hooks/queries/suppliers/useDeleteSupplier.ts`

## 6. Duplicate Exports Found

The supplier barrel exported `useDeleteSupplier` through:

- inline function export
- re-export from `./useDeleteSupplier`

This caused:

```text
Cannot redeclare exported variable 'useDeleteSupplier'
Export declaration conflicts with exported declaration of 'useDeleteSupplier'
```

## 7. Canonical Implementation Selected

Canonical implementation:

```text
frontend/src/hooks/queries/suppliers/useDeleteSupplier.ts
```

The inline and separate implementations were identical. The separate file was selected because every other supplier hook already uses one hook implementation file plus a barrel export.

## 8. Canonical Public Barrel

Canonical supplier hook public barrel:

```text
frontend/src/hooks/queries/suppliers/index.ts
```

It now exports each implemented supplier hook exactly once:

```typescript
export { useSuppliers } from "./useSuppliers";
export { useSupplier } from "./useSupplier";
export { useCreateSupplier } from "./useCreateSupplier";
export { useUpdateSupplier } from "./useUpdateSupplier";
export { useDeleteSupplier } from "./useDeleteSupplier";
```

## 9. Root Barrel Disposition

`frontend/src/hooks/queries/index.ts` continues to re-export the suppliers domain barrel:

```typescript
export * from "./suppliers";
```

No hook is redefined at the root barrel.

## 10. Files Inspected

- `frontend/src/hooks/queries/suppliers/`
- `frontend/src/hooks/queries/suppliers/index.ts`
- `frontend/src/hooks/queries/suppliers/useSuppliers.ts`
- `frontend/src/hooks/queries/suppliers/useSupplier.ts`
- `frontend/src/hooks/queries/suppliers/useCreateSupplier.ts`
- `frontend/src/hooks/queries/suppliers/useUpdateSupplier.ts`
- `frontend/src/hooks/queries/suppliers/useDeleteSupplier.ts`
- `frontend/src/hooks/queries/index.ts`
- `frontend/src/services/suppliers/`
- `frontend/src/features/procurement/`
- `frontend/src/features/suppliers/`

## 11. Files Created

- `frontend/docs/architecture/reviews/MIGRATION-008-SUPPLIER-HOOK-BOUNDARY.md`

## 12. Files Modified

- `frontend/src/hooks/queries/suppliers/index.ts`

## 13. Exports Removed or Corrected

Removed from `frontend/src/hooks/queries/suppliers/index.ts`:

- inline `useDeleteSupplier` implementation
- inline default export
- imports used only by that inline implementation

Preserved:

- export of `useDeleteSupplier` from `./useDeleteSupplier`

## 14. Runtime Behavior Confirmation

Supplier hook runtime behavior is unchanged.

The retained `useDeleteSupplier.ts` implementation is identical to the removed inline implementation and still calls:

- `useDeleteEntity`
- `supplierService.delete`
- `invalidateSuppliers`

No supplier service, DTO, entity, query key, or invalidation behavior was changed.

## 15. Compiler Errors Before

Pre-migration count:

```text
239 TypeScript errors
```

## 16. Compiler Errors After

Post-migration count:

```text
236 TypeScript errors
```

`npm run build` still fails because unrelated compiler errors remain.

## 17. Net Reduction

```text
3 TypeScript errors
```

## 18. Duplicate-Export Diagnostics Before and After

Before:

```text
src/hooks/queries/suppliers/index.ts(...): Cannot redeclare exported variable 'useDeleteSupplier'.
src/hooks/queries/suppliers/index.ts(...): Export declaration conflicts with exported declaration of 'useDeleteSupplier'.
```

After:

```text
No supplier duplicate-export diagnostics remain.
```

## 19. New Diagnostics

No new diagnostics were introduced.

## 20. Remaining Supplier Architecture Issues

Remaining supplier diagnostics are intentionally out of scope:

- missing `Supplier` entity export
- missing `CreateSupplierRequest`
- missing `UpdateSupplierRequest`
- missing `UseEntityOptions` export from common hooks
- `supplierService.findById` is not available on the current service facade
- supplier list query key signature mismatch
- supplier service barrel exports missing service-local type names

## 21. Invariants Verified

- Supplier hooks have one canonical public entry point.
- Each supplier hook is exported exactly once.
- The supplier barrel exports only existing hook symbols.
- No supplier service or DTO is owned by the hook barrel.
- No supplier hook implementation was fabricated.
- Query and mutation hook responsibilities remain unchanged.
- No direct Axios call was introduced.
- No cross-domain service import was introduced.
- No query-key or invalidation policy changed.
- No unrelated domain file changed.
- Runtime supplier behavior remains unchanged.
- Runtime exports comply with `verbatimModuleSyntax`.

## 22. Rollback Boundary

Rollback is limited to:

- `frontend/src/hooks/queries/suppliers/index.ts`
- this migration report

## 23. Recommended Next Migration

Migration 009 should address the next narrow supplier architecture blocker:

- canonical supplier type ownership, or
- common hook option exports such as `UseEntityOptions`,

without redesigning supplier services or query-key architecture in the same pass.
