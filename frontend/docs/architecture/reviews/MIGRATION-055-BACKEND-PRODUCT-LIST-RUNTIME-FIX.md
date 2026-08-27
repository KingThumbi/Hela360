# Migration 055 - Backend Product List Runtime Fix

## 1. Migration Purpose

Migration 055 fixes the backend runtime contract for:

```text
GET /api/products
```

The migration is intentionally narrow. It makes the Product list endpoint
reliably executable for the operational Product page introduced in Migration
054 without redesigning Product API behavior, frontend architecture, Inventory,
Procurement, authorization, or unsupported Product mutations.

## 2. Runtime Defect Found

The Product list route used `query` before it was initialized.

Before the fix, the route read authenticated identity and then applied search,
active, and product type filters to `query`, but no Product query had been
created.

## 3. Exact Root Cause

Root cause:

```text
query = query.filter(...)
```

appeared before any assignment to `query`.

The route also read `identity.branch_id`, but Product is tenant-wide and the
branch value was not used.

## 4. Product List Route Before

Before:

- route: `GET /products`
- permission: `products.view`
- tenant id was resolved from authenticated identity
- branch id was read but unused
- `query` was first referenced in the search branch before initialization
- filters were intended for `search`, `is_active`, and `product_type`
- response envelope was `{ ok, count, items }`

## 5. Product List Route After

After:

```python
query = Product.query.filter_by(
    tenant_id=tenant_id,
)
```

is initialized before any client filters are applied.

The endpoint still returns:

```json
{
  "ok": true,
  "count": 0,
  "items": []
}
```

## 6. Query Initialization Disposition

The query is initialized exactly once from `Product.query` and scoped by the
authenticated tenant id before search, active-state, product-type, ordering, and
pagination are applied.

No client-supplied tenant id is accepted.

## 7. Tenant-Scope Behavior

Product list is tenant-scoped by:

```text
Product.tenant_id == identity.tenant_id
```

Tests verify that Tenant A does not see Tenant B products and Tenant A search
cannot return Tenant B matches.

## 8. Search Behavior

Search behavior is preserved.

The route searches only the existing supported fields:

- `Product.name`
- `Product.internal_sku`
- `Product.generic_name`
- `Product.supplier_sku`

Whitespace-only search is treated as no search filter.

## 9. Pagination Behavior

The route now accepts:

- `page`
- `per_page`

Defaults:

- `page = 1`
- `per_page = 25`

Both must be positive integers. Invalid values return the existing JSON error
shape with status 400.

`count` remains the tenant-scoped filtered total, while `items` contains the
requested page.

## 10. Response Envelope

The response envelope remains:

```text
{ ok: true, count: number, items: Product[] }
```

This matches `frontend/src/services/products/productService.ts`, which maps
`count` and `items` into the frontend `PaginatedResponse<Product>` shape.

## 11. Permission Behavior

The route remains protected by:

```text
@require_permission("products.view")
```

The decorator was not weakened or replaced.

## 12. Serializer Verification

The list endpoint still serializes each item through `_serialize_product`.

Verified serialized fields include:

- `id`
- `tenant_id`
- `internal_sku`
- `supplier_sku`
- `name`
- `generic_name`
- `description`
- `product_type`
- pricing fields
- inventory flags
- `requires_prescription`
- `category`
- `brand`
- `unit`
- `codes`
- `is_active`
- timestamps

No serializer fields were added or removed.

## 13. Detail And By-Code Regression Result

`GET /api/products/<id>` and `GET /api/products/by-code/<code_value>` were not
modified.

Regression tests verify both still return the expected tenant-scoped Product
payload.

## 14. Tests Added

Added:

```text
app/api/tests/test_products_list_contract.py
```

Coverage includes:

- empty list envelope
- permitted Product list request
- missing permission rejection
- serialized Product fields
- search match
- search no-match
- tenant isolation
- tenant-scoped pagination count
- invalid pagination rejection
- detail/by-code regression checks

## 15. Test Results

Command:

```bash
venv/bin/python -m pytest app/api/tests/test_products_list_contract.py -q
```

Result:

```text
8 passed
```

Warnings:

```text
4 SQLAlchemy relationship overlap warnings
```

These warnings are pre-existing model relationship warnings and were not
addressed in this Product route migration.

## 16. Backend Compile Result

Commands:

```bash
venv/bin/python -m py_compile app/api/products.py
venv/bin/python -m compileall app
```

Result:

```text
PASS
```

## 17. Startup And Route Listing Result

Command:

```bash
venv/bin/flask routes
```

Result:

```text
BLOCKED
```

The app factory still fails during auth service import because the current
environment lacks `argon2`.

## 18. Known Environment Blocker

Known blocker:

```text
ModuleNotFoundError: No module named 'argon2'
```

No packages were installed in this migration.

## 19. Frontend Contract Verification

Inspected:

- `frontend/src/services/products/productService.ts`
- `frontend/src/types/requests/list-products-request.ts`
- `frontend/src/hooks/queries/products/useProducts.ts`
- Product feature files from Migration 054

The backend response now matches the established frontend service contract.

No frontend workaround is required.

## 20. Frontend Source Changed Confirmation

No files under `frontend/src/` were modified in Migration 055.

Only backend route/test source and migration documentation were changed.

## 21. Frontend TypeScript Result

Command:

```bash
cd frontend
npx tsc -b --pretty false
```

Result:

```text
TypeScript errors: 0
PASS
```

## 22. Frontend Vite Result

Command:

```bash
cd frontend
npm run build
```

Result:

```text
Vite build: PASS
```

Existing warning remains:

```text
Some chunks are larger than 500 kB after minification.
```

## 23. Files Inspected

- `app/api/products.py`
- `app/models/product.py`
- `app/models/tenant.py`
- `app/auth/permissions.py`
- `app/services/tenant/auth/decorators.py`
- `app/services/tenant/procurement/tests/test_supplier_contract.py`
- `frontend/src/services/products/productService.ts`
- `frontend/src/types/entities/product.ts`
- `frontend/src/types/requests/list-products-request.ts`
- `frontend/docs/architecture/reviews/MIGRATION-054-PRODUCT-OPERATIONAL-PAGE.md`

## 24. Files Created

- `app/api/tests/test_products_list_contract.py`
- `frontend/docs/architecture/reviews/MIGRATION-055-BACKEND-PRODUCT-LIST-RUNTIME-FIX.md`

## 25. Files Modified

- `app/api/products.py`

## 26. Runtime Verification

Targeted Flask test-client verification succeeded for:

```text
authenticated tenant
  -> GET /api/products
  -> 200
  -> { ok, count, items }
```

Search, pagination, tenant isolation, permission denial, detail, and by-code
paths were covered by the focused test file.

Full app startup remains blocked by missing `argon2`.

## 27. Invariants Verified

- Product list query is initialized deterministically.
- Tenant isolation is enforced server-side.
- Client cannot choose another tenant.
- Search operates inside tenant scope.
- Pagination operates inside tenant scope.
- Product list response shape remains stable.
- `products.view` remains enforced.
- Product detail/by-code behavior remains unchanged.
- Product create behavior remains unchanged.
- Frontend Product architecture remains unchanged.
- Inventory and Procurement behavior remain unchanged.
- Unsupported Product mutations were not added.
- Frontend TypeScript remains clean.
- Frontend production build remains successful.

## 28. Rollback Boundary

Rollback is limited to:

- reverting the `list_products` query/pagination changes in
  `app/api/products.py`;
- removing `app/api/tests/test_products_list_contract.py`;
- removing this migration report.

No frontend source rollback is required.

## 29. Recommended Next Migration

Recommended next migration:

```text
Migration 056 - Product List Runtime Verification Against Full App Environment
```

after the environment dependency gap for `argon2` is resolved.
