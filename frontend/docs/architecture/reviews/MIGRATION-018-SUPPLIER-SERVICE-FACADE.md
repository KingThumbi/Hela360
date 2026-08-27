# Migration 018 - Supplier Service Facade

## 1. Migration Purpose

Migration 018 restores the canonical Supplier public service facade required by ADR-001 and aligns Supplier hooks with verified backend response envelopes.

This migration is Supplier-only. It does not modify backend files, query keys, invalidation policy, Supplier UI, or unrelated domains.

## 2. ADR Requirements Applied

- ADR-001: domain services expose business-oriented facade methods and hide HTTP/envelope details from hooks.
- ADR-002: query hooks consume service methods and do not perform transport unwrapping.
- ADR-003: mutation hooks continue using centralized invalidation helpers.
- ADR-004: Supplier entity and request DTO ownership remains under `src/types`.
- ADR-008: the Supplier service barrel exposes the public domain boundary.
- ADR-009: service methods use clear business names.

## 3. Backend Endpoints Verified

Verified Supplier backend routes:

- `GET /api/suppliers`
- `POST /api/suppliers`
- `GET /api/suppliers/<id>`
- `PATCH /api/suppliers/<id>`
- `POST /api/suppliers/<id>/deactivate`
- `POST /api/suppliers/<id>/reactivate`

No hard-delete endpoint is implemented.

No Supplier products, purchase-history, performance, or `/activate` endpoint was verified.

## 4. Existing Supplier Service Methods

Before this migration, `frontend/src/services/suppliers/supplierService.ts` inherited generic BaseService methods and exposed unsupported Supplier-local methods:

- inherited `list`
- inherited `paginate`
- inherited `get`
- inherited `create`
- inherited `update`
- inherited `delete`
- unsupported `products`
- unsupported `purchaseHistory`
- unsupported `performance`
- unsupported `activate`
- unsupported `deactivate`

Supplier hooks called generic BaseService names directly:

- `useSuppliers` -> `supplierService.paginate`
- `useSupplier` -> `supplierService.findById`
- `useCreateSupplier` -> `supplierService.create`
- `useUpdateSupplier` -> `supplierService.update`
- `useDeleteSupplier` -> `supplierService.delete`

`findById` was never part of the current BaseService implementation.

## 5. BaseService Response Behavior

`BaseService` was inspected and left unchanged.

Current behavior:

- `list` returns `ApiResponse<TEntity[]>`
- `paginate` returns `PaginatedResponse<TEntity>`
- `get` returns `ApiResponse<TEntity>`
- `create` returns `ApiResponse<TEntity>`
- `update` uses HTTP `PUT` and returns `ApiResponse<TEntity>`
- `patch` uses HTTP `PATCH` and returns `ApiResponse<TEntity>`
- `delete` uses HTTP `DELETE` and returns `ApiResponse<void>`
- transport helpers return Axios responses

The verified Supplier backend does not use `ApiResponse<T>` with `data`. It uses `item` for single-entity responses and `items` plus `pagination` for lists.

## 6. Canonical Public Facade

Canonical Supplier service owner:

```text
frontend/src/services/suppliers/supplierService.ts
```

Canonical public import path:

```typescript
import { supplierService } from "@/services/suppliers";
```

Established facade methods:

- `listSuppliers`
- `getSupplier`
- `createSupplier`
- `updateSupplier`
- `deactivateSupplier`
- `reactivateSupplier`

No `deleteSupplier` facade method was added because the backend does not support hard deletion.

No `findById` Supplier method was added or retained as canonical.

## 7. Method Contract Table

| Method | Backend operation | Return type | Envelope handling |
| --- | --- | --- | --- |
| `listSuppliers(params?)` | `GET /suppliers` | `PaginatedResponse<Supplier>` | unwraps `items`; maps `page_size` to `per_page` |
| `getSupplier(id)` | `GET /suppliers/<id>` | `Supplier` | unwraps `item` |
| `createSupplier(payload)` | `POST /suppliers` | `Supplier` | unwraps `item` |
| `updateSupplier(id, payload)` | `PATCH /suppliers/<id>` | `Supplier` | unwraps `item` |
| `deactivateSupplier(id)` | `POST /suppliers/<id>/deactivate` | `Supplier` | unwraps `item` |
| `reactivateSupplier(id)` | `POST /suppliers/<id>/reactivate` | `Supplier` | unwraps `item` |

## 8. Response Envelope Handling

Single-entity Supplier backend responses use:

```text
{ ok: true, item: Supplier }
```

Create also includes `message`.

The service unwraps `item` and returns `Supplier` to hooks.

List backend responses use:

```text
{ ok: true, items: Supplier[], pagination: { page, page_size, total, pages, has_next, has_prev } }
```

The service returns canonical `PaginatedResponse<Supplier>` and maps backend `page_size` to frontend `per_page`.

Hooks do not unwrap API envelopes.

## 9. Delete Hook Disposition

`useDeleteSupplier` was classified as an unsupported endpoint / compatibility naming mismatch.

Before this migration, it called inherited `supplierService.delete(id)`, which would issue unsupported `DELETE /suppliers/<id>`.

This migration redirects the transitional hook to:

```text
supplierService.deactivateSupplier(id)
```

The hook name remains unchanged to avoid broad UI/API churn in this migration. The documentation and hook comment now describe it as deactivation compatibility.

## 10. Public Service Barrel

`frontend/src/services/suppliers/index.ts` now exports exactly one Supplier runtime service instance:

```typescript
export { supplierService } from "./supplierService";
```

The barrel no longer re-exports canonical Supplier entity or request DTOs. Those remain owned by:

- `frontend/src/types/entities/`
- `frontend/src/types/requests/`

The barrel does not expose BaseService or internal transport helpers.

## 11. Hooks Migrated

Updated Supplier hooks:

- `useSuppliers` now calls `supplierService.listSuppliers`
- `useSupplier` now calls `supplierService.getSupplier`
- `useCreateSupplier` now calls `supplierService.createSupplier`
- `useUpdateSupplier` now calls `supplierService.updateSupplier`
- `useDeleteSupplier` now calls `supplierService.deactivateSupplier`

Query keys and invalidation helpers were not modified.

## 12. Files Inspected

- `frontend/src/services/suppliers/supplierService.ts`
- `frontend/src/services/suppliers/index.ts`
- `frontend/src/services/base/BaseService.ts`
- `frontend/src/services/base/query.ts`
- `frontend/src/services/base/request.ts`
- `frontend/src/hooks/queries/suppliers/`
- `frontend/src/hooks/queries/common/`
- `frontend/src/lib/queryKeys.ts`
- `frontend/src/lib/queryInvalidation.ts`
- `frontend/src/types/api/`
- `frontend/src/types/entities/supplier.ts`
- `frontend/src/types/requests/create-supplier-request.ts`
- `frontend/src/types/requests/update-supplier-request.ts`
- `frontend/src/types/requests/pagination-request.ts`
- `app/api/suppliers.py`
- `app/services/tenant/procurement/supplier_service.py`
- `app/schemas/supplier.py`
- `app/serializers/supplier.py`
- `app/models/supplier.py`

## 13. Files Created

- `frontend/docs/architecture/reviews/MIGRATION-018-SUPPLIER-SERVICE-FACADE.md`

## 14. Files Modified

- `frontend/src/services/suppliers/supplierService.ts`
- `frontend/src/services/suppliers/index.ts`
- `frontend/src/hooks/queries/suppliers/useSuppliers.ts`
- `frontend/src/hooks/queries/suppliers/useSupplier.ts`
- `frontend/src/hooks/queries/suppliers/useCreateSupplier.ts`
- `frontend/src/hooks/queries/suppliers/useUpdateSupplier.ts`
- `frontend/src/hooks/queries/suppliers/useDeleteSupplier.ts`

## 15. Compiler Errors Before

Baseline:

```text
199 TypeScript errors
```

Supplier diagnostics before:

- `supplierService.findById` did not exist.
- create hook expected `Supplier` but received `ApiResponse<Supplier>`.
- update hook expected `Supplier` but received `ApiResponse<Supplier>`.
- Supplier list query key was called with params but accepts no arguments.
- delete hook used unsupported inherited hard-delete behavior.

## 16. Compiler Errors After

Post-migration:

```text
196 TypeScript errors
```

Net reduction:

```text
3
```

Supplier diagnostics after:

- `useSuppliers` still calls `QUERY_KEYS.suppliers.list(params)` while the key currently accepts no arguments.

That query-key signature issue is explicitly deferred by this migration.

## 17. Newly Exposed Query-Key Diagnostics

No newly exposed Supplier query-key diagnostics were introduced.

The existing Supplier list query-key diagnostic remains:

```text
src/hooks/queries/suppliers/useSuppliers.ts(66,31): error TS2554: Expected 0 arguments, but got 1.
```

## 18. New Diagnostics

No new diagnostics were introduced.

## 19. Remaining Supplier Blockers

- Supplier list query-key signature does not accept pagination params.
- Supplier navigation ID remains part of the broader navigation ID backlog.
- Generic common hook helper diagnostics remain outside Supplier service ownership.

## 20. Runtime Behavior Confirmation

Supplier hooks now receive domain values from the service facade:

- `Supplier`
- `PaginatedResponse<Supplier>`

Transport-envelope unwrapping occurs inside Supplier service methods.

The only runtime behavior correction is `useDeleteSupplier`: it now uses the verified backend deactivation operation instead of an unsupported hard-delete endpoint.

## 21. Invariants Verified

- Supplier exposes one public service facade instance.
- Supplier facade uses business-oriented method names.
- Supplier hooks call only the Supplier facade through `@/services/suppliers`.
- Hooks receive domain values, not transport envelopes.
- Transport unwrapping occurs in the service.
- BaseService generic naming no longer leaks into Supplier hooks.
- No hard-delete method was invented.
- Supplier lifecycle reflects verified deactivate/reactivate backend operations.
- Supplier type ownership remains under `src/types`.
- Supplier service contains no React or TanStack Query logic.
- No query key was changed.
- No invalidation policy was changed.
- No backend file was changed.
- No unrelated domain was changed.

## 22. Rollback Boundary

Rollback is limited to:

- `frontend/src/services/suppliers/supplierService.ts`
- `frontend/src/services/suppliers/index.ts`
- `frontend/src/hooks/queries/suppliers/useSuppliers.ts`
- `frontend/src/hooks/queries/suppliers/useSupplier.ts`
- `frontend/src/hooks/queries/suppliers/useCreateSupplier.ts`
- `frontend/src/hooks/queries/suppliers/useUpdateSupplier.ts`
- `frontend/src/hooks/queries/suppliers/useDeleteSupplier.ts`
- `frontend/docs/architecture/reviews/MIGRATION-018-SUPPLIER-SERVICE-FACADE.md`

## 23. Recommended Next Migration

Recommended next migration:

```text
Migration 019 - Supplier Query Key Boundary
```

Rationale:

The remaining Supplier-specific TypeScript diagnostic is the list query-key signature mismatch, and this migration explicitly kept query keys out of scope.
