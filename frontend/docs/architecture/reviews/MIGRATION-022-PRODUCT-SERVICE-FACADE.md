# Migration 022 - Product Service Facade

## 1. Migration Purpose

Migration 022 restores the canonical Product public service facade required by ADR-001 and establishes a truthful Product transport-to-domain response boundary.

This migration is Product-service only. It does not modify backend files, Product query keys, invalidation policy, Product feature UI, canonical Product types, or unrelated domains.

## 2. ADR Rules Applied

- ADR-001: Product exposes business-oriented service methods and hides HTTP/envelope details from hooks.
- ADR-002: Product hooks consume services and do not unwrap transport responses.
- ADR-003: mutation hooks continue to use centralized invalidation helpers; no invalidation policy changed.
- ADR-004: Product entity and request DTO ownership remains under `src/types`.
- ADR-008: the Product service barrel exposes a controlled public service boundary.
- ADR-009: service method names use explicit business language.

## 3. Backend Product Endpoints Verified

Verified in `app/api/products.py`:

- `GET /api/products`
- `GET /api/products/<product_id>`
- `POST /api/products`
- `GET /api/products/by-code/<code_value>`

No backend route was verified for:

- `PUT /api/products/<id>`
- `PATCH /api/products/<id>`
- `DELETE /api/products/<id>`
- `POST /api/products/<id>/activate`
- `POST /api/products/<id>/deactivate`
- `POST /api/products/<id>/reactivate`
- `GET /api/products/<id>/inventory`
- `GET /api/products/<id>/movements`
- product pricing update
- product image upload or removal
- dedicated category or brand endpoints under Product

The list route currently reads authenticated tenant and branch context, but the verified Product model has `tenant_id` and no Product-level `branch_id`. The current route also contains a backend implementation bug because `query` is used before initialization; backend fixes are out of scope for this frontend migration.

## 4. Existing Product Service Methods

Before this migration, `frontend/src/services/products/productService.ts` inherited generic BaseService methods and exposed unverified Product-local methods:

- inherited `list`
- inherited `paginate`
- inherited `get`
- inherited `create`
- inherited `update`
- inherited `delete`
- inherited `search`
- unsupported `bySku`
- unsupported `byBarcode`
- unsupported `updatePrice`
- unsupported `inventory`
- unsupported `movements`
- unsupported `activate`
- unsupported `deactivate`
- unsupported `uploadImage`
- unsupported `removeImage`

Product hooks called generic BaseService names directly:

- `useProducts` -> `productService.paginate`
- `useProduct` -> `productService.findById`
- `useCreateProduct` -> `productService.create`
- `useUpdateProduct` -> `productService.update`
- `useDeleteProduct` -> `productService.delete`

`findById` is not implemented by the current BaseService.

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

The verified Product backend uses `item` for single-entity responses and `count` plus `items` for list responses.

## 6. Canonical Public Facade

Canonical Product service owner:

```text
frontend/src/services/products/productService.ts
```

Canonical public import path:

```typescript
import { productService } from "@/services/products";
```

Established facade methods:

- `listProducts`
- `getProduct`
- `createProduct`
- `searchProducts`
- `getProductByCode`

No `updateProduct`, `deleteProduct`, `activateProduct`, `deactivateProduct`, or `reactivateProduct` method was added because no matching backend route was verified.

No `findById` Product method was added or retained as canonical.

## 7. Method Contract Table

| Method | Backend operation | Return type | Envelope handling |
| --- | --- | --- | --- |
| `listProducts(params?)` | `GET /products` | `PaginatedResponse<Product>` | unwraps `items`; derives pagination from `count` and request params |
| `getProduct(id)` | `GET /products/<id>` | `Product` | unwraps `item` |
| `createProduct(payload)` | `POST /products` | `Product` | unwraps `item` |
| `searchProducts(search, params?)` | `GET /products?search=...` | `PaginatedResponse<Product>` | delegates to `listProducts` |
| `getProductByCode(code)` | `GET /products/by-code/<code>` | `Product` | unwraps `item` |

## 8. List Response Contract

Backend list response:

```text
{ ok: true, count: number, items: Product[] }
```

Frontend service return:

```text
PaginatedResponse<Product>
```

Because the backend does not return pagination metadata, the service derives:

- `page` from `PaginationRequest.page` or `1`
- `per_page` from `PaginationRequest.per_page` or returned item count
- `total` from backend `count`
- `pages`, `has_next`, and `has_prev` from those values

## 9. Detail Response Contract

Backend detail response:

```text
{ ok: true, item: Product }
```

Frontend service return:

```text
Product
```

## 10. Create Response Contract

Backend create response:

```text
{ ok: true, message: string, item: Product }
```

Frontend service return:

```text
Product
```

## 11. Update Response Contract

No backend Product update route or response envelope was verified.

`useUpdateProduct` was left on its existing unresolved path and remains a Product blocker.

No `updateProduct` facade method was fabricated.

## 12. Delete and Lifecycle Disposition

No backend hard-delete, activate, deactivate, or reactivate route was verified for Product.

`useDeleteProduct` currently calls inherited `productService.delete(id)`, which maps to unsupported `DELETE /products/<id>`.

This migration leaves that hook unchanged because silently converting delete into lifecycle behavior is unsupported by backend evidence and no Product lifecycle endpoint exists.

## 13. Search and Supporting-Operation Disposition

Search is supported through the verified list route's `search` query parameter. The service exposes `searchProducts(search, params?)` as a business-named wrapper around `listProducts`.

Product-code lookup is supported through `GET /products/by-code/<code_value>`, so the service exposes `getProductByCode(code)`.

The previous `bySku` and `byBarcode` methods were removed because no matching backend routes were verified. SKU and barcode-style identifiers may be represented as ProductCode rows, but the verified backend operation is product-code lookup.

Product category, brand, inventory, movement, pricing, and image operations remain unsupported in the verified Product route set.

## 14. Product and Inventory Boundary

Product owns Product identity and configuration.

Inventory shared entities remain owned by `src/types/entities` and are not re-exported from the Product service barrel.

The Product barrel still preserves the existing `inventoryService` runtime export as a transitional compatibility boundary because current Inventory hooks import it from `@/services/products`. This migration does not redesign Inventory service ownership.

## 15. Canonical Service Instance Owner

The only canonical Product runtime instance is:

```typescript
export const productService = new ProductService();
```

`ProductService` is internal to `productService.ts` and is not exported from the Product barrel.

## 16. Public Service Barrel

`frontend/src/services/products/index.ts` now exports:

```typescript
export { productService } from "./productService";
export { inventoryService } from "./inventoryService";
```

The second export is transitional for existing Inventory hooks.

The barrel no longer exports:

- `ProductService`
- Product entities
- Product request DTOs
- category services
- category service-local types
- Inventory shared entity types
- unsupported `ProductStatus`
- unsupported `ProductType`
- unsupported `ProductSummary`

## 17. Hooks Migrated

Updated:

- `useProducts` now calls `productService.listProducts`
- `useProduct` now calls `productService.getProduct`
- `useCreateProduct` now calls `productService.createProduct`

Left unchanged because backend support is not verified:

- `useUpdateProduct`
- `useDeleteProduct`

Product query keys and invalidation helpers were not modified.

## 18. Files Inspected

- `frontend/src/services/products/productService.ts`
- `frontend/src/services/products/index.ts`
- `frontend/src/services/products/categoryService.ts`
- `frontend/src/services/products/inventoryService.ts`
- `frontend/src/services/base/BaseService.ts`
- `frontend/src/hooks/queries/products/`
- `frontend/src/hooks/queries/inventory/`
- `frontend/src/types/entities/product.ts`
- `frontend/src/types/requests/create-product-request.ts`
- `frontend/src/types/requests/update-product-request.ts`
- `frontend/src/types/requests/pagination-request.ts`
- `frontend/src/types/api/`
- `app/api/products.py`
- `app/models/product.py`
- `app/services/tenant/auth/decorators.py`
- ADR-001
- ADR-002
- ADR-003
- ADR-004
- ADR-008
- ADR-009
- Migration 013 report
- Migration 018 report
- Migration 020 report

## 19. Files Created

- `frontend/docs/architecture/reviews/MIGRATION-022-PRODUCT-SERVICE-FACADE.md`

## 20. Files Modified

- `frontend/src/services/products/productService.ts`
- `frontend/src/services/products/index.ts`
- `frontend/src/hooks/queries/products/useProducts.ts`
- `frontend/src/hooks/queries/products/useProduct.ts`
- `frontend/src/hooks/queries/products/useCreateProduct.ts`

## 21. Compiler Errors Before

Frontend compiler baseline before this migration:

```text
192 TypeScript errors
```

Product diagnostics before:

- `productService.findById` did not exist.
- create hook expected `Product` but received `ApiResponse<Product>`.
- update hook expected `Product` but received `ApiResponse<Product>`.
- Product list query key was called with params but accepted no arguments.
- Product navigation ID remains part of the broader navigation ID backlog.

## 22. Compiler Errors After

Frontend compiler count after this migration:

```text
190 TypeScript errors
```

## 23. Net Reduction

This migration reduced the frontend TypeScript baseline by:

```text
2 errors
```

## 24. Product Diagnostics Before and After

Resolved:

- missing `findById` diagnostic for `useProduct`
- create response-envelope diagnostic for `useCreateProduct`

Remaining:

```text
src/hooks/queries/products/useProducts.ts(62,30): error TS2554
src/hooks/queries/products/useUpdateProduct.ts(57,7): error TS2322
src/navigation/navigation.ts(71,9): error TS2322
```

## 25. Newly Exposed Query-Key Diagnostics

No newly exposed Product query-key diagnostics were introduced.

The existing deferred Product query-key diagnostic remains:

```text
src/hooks/queries/products/useProducts.ts(62,30): error TS2554: Expected 0 arguments, but got 1.
```

## 26. New Diagnostics

No new diagnostics were introduced by this migration.

## 27. Remaining Product Blockers

- Product list query-key signature does not accept pagination params.
- `useUpdateProduct` still depends on unsupported inherited `PUT /products/<id>` behavior and returns `ApiResponse<Product>` at the type boundary.
- No verified Product update route exists.
- `useDeleteProduct` still depends on unsupported inherited `DELETE /products/<id>` behavior at runtime.
- Product navigation ID remains part of the broader navigation backlog.
- Backend `GET /products` contains a current implementation bug because `query` is used before initialization.

## 28. Runtime Behavior Confirmation

Product hooks migrated in this migration now receive domain values from the service facade:

- `Product`
- `PaginatedResponse<Product>`

Transport-envelope unwrapping occurs inside Product service methods.

Runtime fetching behavior becomes more truthful for list, detail, create, search, and by-code lookup. Unsupported update/delete/lifecycle behavior was not fabricated.

## 29. Invariants Verified

- Product exposes one canonical `productService` runtime instance.
- Product facade uses business-oriented method names.
- Migrated Product hooks call the Product facade through `@/services/products`.
- Migrated hooks receive domain values, not transport envelopes.
- Transport unwrapping and list mapping occur in the service.
- No Product `findById` facade was added.
- No unsupported Product update, delete, activate, deactivate, or reactivate facade was invented.
- Product canonical types remain under `src/types`.
- Inventory shared types are not owned by the Product barrel.
- Product service contains no React or TanStack Query logic.
- No Product query key was changed.
- No invalidation policy was changed.
- No backend file was changed.
- No unrelated domain source was changed.

## 30. Rollback Boundary

Rollback is limited to:

- `frontend/src/services/products/productService.ts`
- `frontend/src/services/products/index.ts`
- `frontend/src/hooks/queries/products/useProducts.ts`
- `frontend/src/hooks/queries/products/useProduct.ts`
- `frontend/src/hooks/queries/products/useCreateProduct.ts`
- this review document

## 31. Recommended Migration 023 Scope

Recommended next migration:

```text
Migration 023 - Product Query Key Boundary
```

Rationale:

The remaining Product-specific TypeScript diagnostic that can be resolved without backend changes is the Product list query-key signature mismatch.
