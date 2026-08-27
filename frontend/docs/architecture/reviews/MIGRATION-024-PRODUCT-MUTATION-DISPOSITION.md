# Migration 024 - Product Mutation Disposition

## 1. Migration Purpose

Migration 024 determines the truthful disposition of remaining Product mutation capabilities:

- update Product
- delete Product
- activate Product
- deactivate Product
- reactivate Product

This migration is inspection-first. Source changes were made only to remove unsupported Product mutation hooks from the public hook boundary and prevent speculative backend calls.

## 2. ADR Rules Applied

- ADR-001: the Product service facade exposes only verified business capabilities.
- ADR-002: Product hooks must invoke services only for supported service operations and must not fabricate mutation behavior.
- ADR-004: Product DTO ownership remains under `src/types`.
- ADR-008: public barrels expose supported module contracts only.
- ADR-009: mutation capability names must reflect verified business operations.

## 3. Backend Mutation Routes Searched

Searched backend paths:

- `app/api/products.py`
- `app/models/`
- `app/schemas/`
- `app/serializers/`
- `app/services/`
- `app/auth/`
- `app/services/tenant/auth/`
- `tests/`
- `migrations/`

Search terms included:

- `update_product`
- `edit_product`
- `patch_product`
- `put_product`
- `delete_product`
- `archive_product`
- `activate_product`
- `deactivate_product`
- `reactivate_product`
- `is_active`
- `/products/<id>`
- `products/<product_id>`

## 4. Product Update Capability Classification

Classification:

```text
Unsupported
```

No registered backend route was found for:

- `PATCH /api/products/<id>`
- `PUT /api/products/<id>`
- `POST /api/products/<id>/update`
- any other Product update route

Permission constants include `products.edit`, but no registered Product update route or service method was found behind that permission.

## 5. Product Delete Capability Classification

Classification:

```text
Unsupported
```

No registered backend route was found for:

- `DELETE /api/products/<id>`

`app/services/tenant/auth/decorators.py` contains an illustrative decorator example showing `@app.delete("/products/<uuid:id>")`, but that file is an authorization-decorator module and the snippet is inside documentation text. It is not a registered Product API route.

Permission constants include `products.delete`, but no registered Product delete route or service method was found behind that permission.

## 6. Product Lifecycle Capability Classification

Classification:

```text
Unsupported
```

No registered backend route was found for:

- `POST /api/products/<id>/activate`
- `POST /api/products/<id>/deactivate`
- `POST /api/products/<id>/reactivate`
- archive lifecycle routes

The Product model has `is_active`, and the list route supports `is_active` filtering, but model fields and filters are not proof of a lifecycle mutation endpoint.

## 7. Request Schemas Found

No Product update, delete, activate, deactivate, or reactivate request schema was found.

Existing frontend `UpdateProductRequest` remains a canonical placeholder type under:

```text
frontend/src/types/requests/update-product-request.ts
```

It was not changed because no backend update schema exists to verify a narrower contract.

## 8. Response Envelopes Found

No Product mutation response envelope was found for update, delete, activate, deactivate, or reactivate.

Verified Product response envelopes remain limited to:

- list: `{ ok: true, count, items }`
- detail: `{ ok: true, item }`
- create: `{ ok: true, message, item }`
- by-code: `{ ok: true, item }`

## 9. Product Frontend Mutation Hooks Found

Found Product mutation hooks:

- `useCreateProduct`
- `useUpdateProduct`
- `useDeleteProduct`

`useCreateProduct` is supported by the verified backend create route and remains public.

`useUpdateProduct` and `useDeleteProduct` are unsupported by backend evidence.

## 10. Active Consumers Found

No active Product feature consumers were found for:

- `useUpdateProduct`
- `useDeleteProduct`

The unsupported hooks were exported only from:

```text
frontend/src/hooks/queries/products/index.ts
```

No Product feature form, page, or active route import was found for those hooks.

## 11. Capability Decision Matrix

| Capability | Backend support | Frontend hook | Facade method | Disposition |
| --- | --- | --- | --- | --- |
| Update | Unsupported | `useUpdateProduct` existed | none | Unsupported and not publicly exposed |
| Delete | Unsupported | `useDeleteProduct` existed | none | Unsupported and not publicly exposed |
| Deactivate | Unsupported | none | none | Deferred pending backend implementation |
| Reactivate | Unsupported | none | none | Deferred pending backend implementation |

## 12. `updateProduct` Disposition

No `updateProduct` facade method was added.

The Product service facade continues to expose only verified backend capabilities:

- `listProducts`
- `getProduct`
- `createProduct`
- `searchProducts`
- `getProductByCode`

## 13. `useUpdateProduct` Disposition

`useUpdateProduct` was removed from the public Product hook barrel.

The local file was preserved, but it no longer calls inherited `productService.update`. If deep-imported, it rejects with a clear backend-support error rather than issuing a speculative `PUT /products/<id>` request.

This removes the Product update response-envelope diagnostic without fabricating Product update support.

## 14. `deleteProduct` Disposition

No `deleteProduct` facade method was added.

No hard-delete or soft-delete backend route was verified.

## 15. `useDeleteProduct` Disposition

`useDeleteProduct` was removed from the public Product hook barrel.

The local file was preserved, but it no longer calls inherited `productService.delete`. If deep-imported, it rejects with a clear backend-support error rather than issuing a speculative `DELETE /products/<id>` request.

## 16. Deactivate and Reactivate Disposition

No `deactivateProduct` or `reactivateProduct` facade method was added.

No lifecycle hook was created.

No delete action was redirected to deactivation because no verified lifecycle endpoint or UI intent supports that interpretation.

## 17. Public Service Barrel Changes

No Product service barrel changes were required.

`frontend/src/services/products/index.ts` continues to export the canonical `productService` runtime instance and no unsupported Product mutation facade.

## 18. Public Hook Barrel Changes

`frontend/src/hooks/queries/products/index.ts` now publicly exports:

- `useProducts`
- `useProduct`
- `useCreateProduct`

It no longer publicly exports:

- `useUpdateProduct`
- `useDeleteProduct`

## 19. Source Files Inspected

- `app/api/products.py`
- `app/models/product.py`
- `app/models/`
- `app/schemas/`
- `app/serializers/`
- `app/services/`
- `app/auth/permissions.py`
- `app/services/tenant/auth/decorators.py`
- `app/__init__.py`
- `app/api/__init__.py`
- `migrations/`
- `frontend/src/services/products/productService.ts`
- `frontend/src/services/products/index.ts`
- `frontend/src/hooks/queries/products/useUpdateProduct.ts`
- `frontend/src/hooks/queries/products/useDeleteProduct.ts`
- `frontend/src/hooks/queries/products/index.ts`
- `frontend/src/features/products/`
- ADR-001
- ADR-002
- ADR-004
- ADR-008
- ADR-009
- Migration 013 report
- Migration 022 report
- Migration 023 report

## 20. Source Files Changed

- `frontend/src/hooks/queries/products/index.ts`
- `frontend/src/hooks/queries/products/useUpdateProduct.ts`
- `frontend/src/hooks/queries/products/useDeleteProduct.ts`

## 21. Compiler Errors Before

Frontend compiler baseline before this migration:

```text
189 TypeScript errors
```

Product mutation diagnostic before:

```text
src/hooks/queries/products/useUpdateProduct.ts(57,7): error TS2322
```

## 22. Compiler Errors After

Frontend compiler count after this migration:

```text
188 TypeScript errors
```

## 23. Net Reduction

This migration reduced the frontend TypeScript baseline by:

```text
1 error
```

## 24. Product Mutation Diagnostics Before and After

Before:

```text
useUpdateProduct expected Product but called inherited productService.update, which returns ApiResponse<Product>.
```

After:

```text
No Product mutation response-envelope diagnostic remains.
```

No `useDeleteProduct` compiler diagnostic existed before this migration, but it represented unsupported runtime behavior and is no longer publicly exported.

## 25. New Diagnostics

No new diagnostics were introduced by this migration.

## 26. Remaining Product Blockers

- Product update requires a verified backend update route and response envelope.
- Product delete requires a verified backend delete or lifecycle route and response envelope.
- Product deactivate/reactivate requires verified backend lifecycle routes.
- Product navigation ID remains part of the broader navigation backlog.
- Backend `GET /products` still contains the existing `query` initialization bug documented in prior Product migrations.

## 27. Runtime Behavior Confirmation

No supported Product runtime behavior changed.

Unsupported local update/delete hooks now fail explicitly instead of making unsupported HTTP requests if deep-imported. They are not exposed through the public Product hook barrel.

No Product service method, response mapping, query key, invalidation helper, feature form, navigation file, or backend source was changed.

## 28. Backend Files Unchanged Confirmation

No backend files were modified.

Backend Product mutation support remains absent in the registered Product API.

## 29. Invariants Verified

- Product facade exposes only verified backend capabilities.
- Product update does not exist in the facade because no backend update route exists.
- Product delete does not exist in the facade because no backend delete route exists.
- Product lifecycle methods do not exist in the facade because no backend lifecycle routes exist.
- Unsupported hooks are not presented as supported public APIs.
- No hook unwraps Product transport envelopes.
- Canonical Product DTO ownership remains under `src/types`.
- No backend behavior changed.
- No query key changed.
- No invalidation policy changed.
- No Product UI behavior was fabricated.
- No unrelated domain source was changed.

## 30. Rollback Boundary

Rollback is limited to:

- `frontend/src/hooks/queries/products/index.ts`
- `frontend/src/hooks/queries/products/useUpdateProduct.ts`
- `frontend/src/hooks/queries/products/useDeleteProduct.ts`
- this review document

## 31. Recommended Next Migration

Recommended next migration:

```text
Migration 025 - Navigation ID Boundary
```

Rationale:

The remaining Product-specific TypeScript diagnostic is the Product navigation ID mismatch, and Product update/delete now requires backend implementation before frontend support can be truthfully restored.
