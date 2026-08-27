# Migration 023 - Product Query Key Boundary

## 1. Migration Purpose

Migration 023 aligns the Product query-key namespace with ADR-003 and the verified Product list/detail contracts.

This migration is Product query-key only. It does not modify backend files, Product response mapping, Product update/delete behavior, invalidation policy, navigation, Product UI, or unrelated domain key namespaces.

## 2. ADR Rules Applied

- ADR-002: Product hooks consume services and centralized query-key factories.
- ADR-003: all Product keys originate from `src/lib/queryKeys.ts` and derive from the Product root namespace.
- ADR-006: tenant-scoped data must be cache-isolated; this remains unresolved in the current cross-domain key architecture.
- ADR-008: Product key construction remains shared infrastructure and reusable request contracts remain under `src/types`.
- ADR-009: key and request names use explicit Product business terminology.

## 3. Previous Product Key Hierarchy

Before this migration:

```typescript
products: {
  root: ["products"] as const,
  list: () => ["products", "list"] as const,
  detail: (id) => ["products", id] as const,
  categories: () => ["products", "categories"] as const,
}
```

Problem:

```text
useProducts passed params to QUERY_KEYS.products.list(params), but list accepted no arguments.
```

The previous list key could not distinguish different Product list inputs and produced a compiler diagnostic.

## 4. Canonical Product Key Hierarchy

The canonical Product hierarchy is now:

```typescript
products.root
products.lists()
products.list(params?)
products.details()
products.detail(id)
products.byCode(code)
```

This follows the Supplier and Customer list/detail structure while adding only the verified Product by-code lookup key.

## 5. Product Root Key

Canonical Product root:

```typescript
QUERY_KEYS.products.root
```

Value:

```text
["products"]
```

Root invalidation remains compatible with Product list, detail, and by-code descendant keys.

## 6. Product List Key Signature

Canonical list key signature:

```typescript
QUERY_KEYS.products.list(params?: ListProductsRequest)
```

Shape:

```text
["products", "list", normalizedParams]
```

`QUERY_KEYS.products.lists()` returns the collection namespace:

```text
["products", "list"]
```

## 7. Product Detail Key Signature

Canonical detail key signature:

```typescript
QUERY_KEYS.products.detail(id: string | number)
```

Shape:

```text
["products", "detail", id]
```

`QUERY_KEYS.products.details()` returns the detail namespace:

```text
["products", "detail"]
```

## 8. Product List Request Type

Product now owns a canonical list request contract:

```text
frontend/src/types/requests/list-products-request.ts
```

Type:

```typescript
ListProductsRequest
```

`PaginationRequest` was not sufficient because the verified Product backend list route supports Product-specific filters that generic pagination does not represent.

## 9. Verified List Fields

Verified Product list fields included in `ListProductsRequest`:

- `page`
- `per_page`
- `search`
- `is_active`
- `product_type`

`page` and `per_page` are part of the canonical frontend Product service/list contract. `search`, `is_active`, and `product_type` are supported by the current backend route.

Fields not included:

- `q`
- `category_id`
- `brand_id`
- `requires_prescription`
- `is_stock_item`
- `sort_by`
- `sort_order`

Those fields were not verified as Product list route filters in the current backend implementation.

## 10. Parameter Normalization

Product list keys use `normalizeListProductsRequest` in `queryKeys.ts`.

Rules:

- default `page` is `1`
- default `per_page` is `25`
- `search` is trimmed
- `product_type` is trimmed
- empty `search` and `product_type` are omitted
- `is_active` remains a boolean and is included only when explicitly provided
- normalized parameter objects are frozen
- no functions, services, Axios configs, URLSearchParams, class instances, stores, or hooks are included

## 11. Default Values

Product list key defaults:

```text
page: 1
per_page: 25
```

These defaults make equivalent list requests produce equivalent keys.

## 12. Search-Key Disposition

No separate Product search key was added.

Search uses the Product list endpoint:

```text
GET /products?search=...
```

Therefore search cache semantics are represented by:

```typescript
QUERY_KEYS.products.list({ search })
```

This avoids duplicate cache entries for semantically identical Product list requests.

## 13. By-Code-Key Disposition

The backend and Product service support:

```text
GET /products/by-code/<code_value>
productService.getProductByCode(code)
```

The key factory now exposes:

```typescript
QUERY_KEYS.products.byCode(code)
```

Shape:

```text
["products", "by-code", trimmedCode]
```

No hook currently consumes by-code lookup, so no hook was added or modified for this operation.

## 14. Tenant-Scope Disposition

Product records are tenant-owned.

Evidence:

- `app/models/product.py` includes `tenant_id`.
- Product backend routes derive tenant context from the authenticated identity.
- `api/interceptors.ts` attaches tenant headers from storage.
- `authStore` stores authenticated identity.

No narrow tenant-aware query-key helper currently exists. `queryKeys.ts` remains a pure static key factory and does not import stores, read storage, or call hooks.

Disposition:

```text
Path C - tenant cache isolation remains unresolved for a future cross-domain query-scope migration.
```

This migration does not claim full ADR-006 cache isolation compliance.

## 15. Branch-Scope Disposition

Product identity is tenant-wide, not branch-owned.

Evidence:

- `app/models/product.py` has `tenant_id` and no Product-level `branch_id`.
- The backend Product list route reads branch context but does not apply a Product branch filter.
- Branch-specific stock belongs to Inventory, not Product identity.

No branch id was added to Product entity keys.

## 16. Invalidation Compatibility

`invalidateProducts` remains unchanged:

```typescript
QUERY_KEYS.products.root
```

All Product descendant keys still derive from:

```text
["products"]
```

Root invalidation therefore continues to cover Product list, detail, and by-code keys.

## 17. Hooks Migrated

Updated:

- `useProducts` now accepts `ListProductsRequest`.

Existing Product hook key usage remains:

- `useProducts` calls `QUERY_KEYS.products.list(params)`
- `useProduct` calls `QUERY_KEYS.products.detail(id)`

No Product service calls, response mapping, enabled logic, mutation functions, invalidation helpers, update behavior, or delete behavior changed.

## 18. Files Inspected

- `frontend/src/lib/queryKeys.ts`
- `frontend/src/lib/queryInvalidation.ts`
- `frontend/src/hooks/queries/products/`
- `frontend/src/services/products/productService.ts`
- `frontend/src/types/requests/pagination-request.ts`
- `frontend/src/types/entities/product.ts`
- `frontend/src/store/authStore.ts`
- `frontend/src/store/shellStore.ts`
- `frontend/src/providers/`
- `frontend/src/api/interceptors.ts`
- `app/api/products.py`
- `app/models/product.py`
- ADR-002
- ADR-003
- ADR-006
- ADR-008
- ADR-009
- Migration 001 report
- Migration 013 report
- Migration 019 report
- Migration 021 report
- Migration 022 report

## 19. Files Created

- `frontend/src/types/requests/list-products-request.ts`
- `frontend/docs/architecture/reviews/MIGRATION-023-PRODUCT-QUERY-KEY-BOUNDARY.md`

## 20. Files Modified

- `frontend/src/lib/queryKeys.ts`
- `frontend/src/types/requests/index.ts`
- `frontend/src/services/products/productService.ts`
- `frontend/src/hooks/queries/products/useProducts.ts`

`productService.ts` changed only at the type boundary from `PaginationRequest` to `ListProductsRequest`; runtime behavior and response mapping were not changed.

## 21. Compiler Errors Before

Frontend compiler baseline before this migration:

```text
190 TypeScript errors
```

Product query-key diagnostic before:

```text
src/hooks/queries/products/useProducts.ts(62,30): error TS2554: Expected 0 arguments, but got 1.
```

## 22. Compiler Errors After

Frontend compiler count after this migration:

```text
189 TypeScript errors
```

## 23. Net Reduction

This migration reduced the frontend TypeScript baseline by:

```text
1 error
```

## 24. Product Key Diagnostics Before and After

Before:

```text
QUERY_KEYS.products.list(params) passed params to a factory that accepted no arguments.
```

After:

```text
No Product query-key arity diagnostic remains.
```

Remaining Product diagnostics are unrelated to this query-key boundary:

```text
src/hooks/queries/products/useUpdateProduct.ts(57,7): error TS2322
src/navigation/navigation.ts(71,9): error TS2322
```

## 25. New Diagnostics

No new diagnostics were introduced by this migration.

## 26. Remaining Product Blockers

- `useUpdateProduct` still depends on unsupported inherited `PUT /products/<id>` behavior and returns `ApiResponse<Product>` at the type boundary.
- No verified Product update route exists.
- `useDeleteProduct` still depends on unsupported inherited `DELETE /products/<id>` behavior at runtime.
- Product navigation ID remains part of the broader navigation backlog.
- Tenant cache isolation needs a cross-domain query-scope migration.
- Backend `GET /products` currently uses `query` before initialization.

## 27. Runtime and Cache Behavior

Runtime fetching behavior is unchanged.

Product list cache keys now distinguish normalized Product list params. Product detail keys now live under a stable detail namespace. Product by-code keys are available for the verified lookup operation without adding a new consumer.

## 28. Invariants Verified

- Every consumed Product key originates from `queryKeys.ts`.
- Product list keys include verified Product list parameters.
- Product detail keys include Product identity.
- Product search cache semantics use the list namespace.
- By-code key exists only for a verified backend/service operation.
- Product root invalidation covers Product descendant keys.
- Product keys are deterministic and serializable.
- Tenant scope is documented as unresolved rather than fabricated.
- Product keys do not include Inventory branch scope.
- Product hooks own no hardcoded query arrays.
- Product service contains no cache logic.
- Product response mapping did not change.
- No Product service runtime behavior changed.
- No backend file was changed.
- No unrelated domain key namespace was changed.

## 29. Rollback Boundary

Rollback is limited to:

- `frontend/src/lib/queryKeys.ts`
- `frontend/src/types/requests/list-products-request.ts`
- `frontend/src/types/requests/index.ts`
- `frontend/src/services/products/productService.ts`
- `frontend/src/hooks/queries/products/useProducts.ts`
- this review document

## 30. Recommended Next Migration

Recommended next migration:

```text
Migration 024 - Product Update/Delete Backend Contract Disposition
```

Rationale:

The remaining Product hook diagnostic is the unsupported update/envelope mismatch, and delete remains an unsupported runtime path.
