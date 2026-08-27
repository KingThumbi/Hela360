# Migration 009 - Supplier Type Ownership Inspection

## 1. Migration Purpose

Migration 009 inspected whether supplier-related shared types could be moved to canonical frontend ownership under `src/types/`.

The migration stopped without source type changes because no backend supplier model, supplier API route, or supplier payload contract could be verified. Creating canonical `Supplier`, supplier request DTOs, enum-like values, contact objects, or summary projections from frontend-only service assumptions would violate the migration stop conditions and ADR-004 single-ownership rules.

## 2. ADR Rules Applied

- ADR-001: supplier service behavior and public methods were not changed.
- ADR-004: shared business types must have one canonical owner under `src/types/`; services must not own reusable entity contracts after migration.
- ADR-008: module boundaries require stable public contracts and prohibit speculative public APIs.
- ADR-009: canonical names must follow verified business terminology, not unverified barrel names.

## 3. Backend Supplier Model Verified

No backend supplier model was found.

Searches across `app/` for `Supplier`, `supplier`, `suppliers`, `vendor`, `vendors`, `SupplierStatus`, `SupplierType`, `SupplierContact`, and `SupplierSummary` found only:

- `app/api/products.py`: `supplier_sku` product field handling
- `app/models/product.py`: `supplier_sku = db.Column(db.String(60))`

No SQLAlchemy `Supplier` model, supplier primary key, tenant/branch fields, contact fields, status/type fields, payment terms, credit terms, timestamps, audit fields, relationships, or serializer contract could be verified.

## 4. Backend Supplier Endpoints Verified

No backend supplier API endpoints were found.

The frontend endpoint registry declares `/suppliers` in `frontend/src/api/endpoints.ts`, but no matching Flask route, blueprint, schema, serializer, service, or test was found under `app/`.

The expected endpoint families were not verifiable:

- list suppliers
- get supplier
- create supplier
- update supplier
- delete supplier
- activate/deactivate supplier
- supplier contacts
- supplier summary/performance

## 5. Procurement Backend Evidence

`app/services/tenant/procurement/procurement_service.py` and `app/services/tenant/procurement/__init__.py` are empty.

They do not provide supplier persistence, payload, or projection evidence.

## 6. Persistence Model Versus API Payload

No persistence model or API payload distinction can be made yet.

The only backend supplier-related persisted field verified is product-level `supplier_sku`, which is not a supplier entity contract.

## 7. Frontend Supplier Type Definitions Found

The frontend currently defines supplier contracts inside `frontend/src/services/suppliers/supplierService.ts`:

- `Supplier`
- `CreateSupplierRequest`
- `UpdateSupplierRequest`
- `SupplierProduct`
- `SupplierPerformance`

The supplier service barrel also attempts to export missing symbols:

- `SupplierStatus`
- `SupplierType`
- `SupplierSummary`
- `SupplierContact`

Those missing names have no active definition in `supplierService.ts` and no verified backend contract.

## 8. Duplicate Contracts Found

One active frontend `Supplier` definition was found, and it is service-local.

One active frontend `CreateSupplierRequest` definition was found, and it is service-local.

One active frontend `UpdateSupplierRequest` definition was found, and it is service-local.

No hook-local supplier DTO definitions were found.

## 9. Canonical Supplier Entity

No canonical `Supplier` entity was created.

Intended owner once backend evidence exists:

```text
frontend/src/types/entities/supplier.ts
```

Reason for deferral: the backend does not currently verify the supplier entity fields, nullability, tenant/branch ownership, audit fields, or response shape.

## 10. Canonical Request DTOs

No canonical supplier request DTOs were created.

Intended owners once backend evidence exists:

```text
frontend/src/types/requests/create-supplier-request.ts
frontend/src/types/requests/update-supplier-request.ts
```

Reason for deferral: the backend does not currently verify accepted create/update payload fields.

## 11. SupplierStatus Disposition

Unsupported.

No backend status field, enum values, boolean-to-status mapping, or API payload evidence was found. No `SupplierStatus` type or runtime constant was created.

## 12. SupplierType Disposition

Unsupported.

No backend supplier type/category field or values were found. No `SupplierType` type or runtime constant was created.

## 13. SupplierContact Disposition

Unsupported.

Frontend service-local `Supplier` has flat contact-like fields, but no backend nested supplier contact entity, value object, response, or relationship was found. No `SupplierContact` type was created.

## 14. SupplierSummary Disposition

Unsupported.

No backend supplier summary endpoint or response projection was found. No `SupplierSummary` type was created.

## 15. Canonical Files Created

None.

The migration did not create speculative type files.

## 16. Source Files Modified

None.

Only this inspection report was created.

## 17. Barrels Updated

None.

The supplier service barrel still has invalid exports for unsupported supplier symbols, but correcting them would require a source change after the migration stop condition was met.

## 18. Imports Migrated

None.

Supplier hooks already import `Supplier` from `@/types/entities` and supplier request DTOs from `@/types/requests`, but the canonical files were not created because the backend contract is unverified.

## 19. Compatibility Re-exports

None.

No compatibility re-export was introduced because there is no verified canonical supplier type to re-export.

## 20. Unsupported or Obsolete Symbols

Unsupported pending backend contract evidence:

- `Supplier`
- `CreateSupplierRequest`
- `UpdateSupplierRequest`
- `SupplierStatus`
- `SupplierType`
- `SupplierContact`
- `SupplierSummary`

Frontend-only service-local symbols retained but not promoted:

- `SupplierProduct`
- `SupplierPerformance`

## 21. Compiler Errors Before

Pre-migration baseline from Migration 008:

```text
236 TypeScript errors
```

## 22. Compiler Errors After

Post-inspection count:

```text
236 TypeScript errors
```

`npm run build` still fails because the broader baseline remains.

## 23. Net Reduction

```text
0 TypeScript errors
```

This migration intentionally made no source changes.

## 24. Supplier Missing-Export Diagnostics Before and After

Before:

```text
src/hooks/queries/suppliers/useCreateSupplier.ts(...): Module '"@/types/entities"' has no exported member 'Supplier'.
src/hooks/queries/suppliers/useCreateSupplier.ts(...): '"@/types/requests"' has no exported member named 'CreateSupplierRequest'.
src/hooks/queries/suppliers/useSupplier.ts(...): Module '"@/types/entities"' has no exported member 'Supplier'.
src/hooks/queries/suppliers/useSuppliers.ts(...): Module '"@/types/entities"' has no exported member 'Supplier'.
src/hooks/queries/suppliers/useUpdateSupplier.ts(...): Module '"@/types/entities"' has no exported member 'Supplier'.
src/hooks/queries/suppliers/useUpdateSupplier.ts(...): '"@/types/requests"' has no exported member named 'UpdateSupplierRequest'.
src/services/suppliers/index.ts(...): Module '"./supplierService"' has no exported member 'SupplierStatus'.
src/services/suppliers/index.ts(...): '"./supplierService"' has no exported member named 'SupplierType'.
src/services/suppliers/index.ts(...): Module '"./supplierService"' has no exported member 'SupplierSummary'.
src/services/suppliers/index.ts(...): Module '"./supplierService"' has no exported member 'SupplierContact'.
```

After:

```text
Unchanged.
```

## 25. Newly Exposed Shape Mismatches

None.

No canonical supplier shape was introduced.

## 26. New Diagnostics

None.

No source files were modified.

## 27. Remaining Supplier Blockers

- no backend supplier model
- no backend supplier API route
- no backend supplier create/update payload contract
- missing `Supplier` export from `@/types/entities`
- missing `CreateSupplierRequest` export from `@/types/requests`
- missing `UpdateSupplierRequest` export from `@/types/requests`
- missing `UseEntityOptions` export from common hooks
- `supplierService.findById` does not exist
- `QUERY_KEYS.suppliers.list` does not accept params
- supplier service barrel exports unsupported missing names

## 28. Invariants Verified

- No speculative supplier entity was created.
- No speculative supplier request DTO was created.
- No speculative supplier enum was created.
- No speculative supplier contact or summary projection was created.
- Supplier service runtime behavior was unchanged.
- Supplier hook runtime behavior was unchanged.
- Query keys and invalidation were unchanged.
- Backend behavior was unchanged.
- No unrelated domain source file changed.
- Type-only/runtime export boundaries were not made worse.

## 29. Rollback Boundary

Rollback is limited to this report:

```text
frontend/docs/architecture/reviews/MIGRATION-009-SUPPLIER-TYPE-OWNERSHIP.md
```

## 30. Recommended Next Migration

Add or verify the backend supplier contract first, then rerun supplier type ownership.

Once backend evidence exists, the next supplier type migration can safely create:

- `frontend/src/types/entities/supplier.ts`
- `frontend/src/types/requests/create-supplier-request.ts`
- `frontend/src/types/requests/update-supplier-request.ts`

Only after that should supplier service-local type definitions and supplier barrels be aligned to canonical shared types.
