# Migration 054 - Product Operational Page

## 1. Migration Purpose

Migration 054 activates Products as an operational ERP feature page using only
verified Product backend capabilities:

- list products
- get product
- create product
- lookup product by registered product code

Unsupported update, delete, deactivate, reactivate, Inventory, and Procurement
workflows remain unavailable.

## 2. ADR Rules Applied

- ADR-001: page components consume hooks instead of services.
- ADR-002: Product server state flows through canonical query/mutation hooks.
- ADR-003: no Product feature component constructs query keys or invalidates
  cache directly.
- ADR-004: Product entities and request DTOs remain under `src/types`.
- ADR-006: Product query identity remains tenant-scoped through Migration 052
  hook/key infrastructure.
- ADR-007: route and create action use backend-derived permissions.
- ADR-008: Products are owned by `frontend/src/features/products/`.
- ADR-009: filenames and public exports use explicit Product naming.

## 3. Starting Baseline

Commands:

```bash
cd /home/thumbi/Hela360/frontend
npx tsc -b --pretty false
npm run build
```

Result:

```text
TypeScript errors before: 0
Vite build before: PASS
```

Existing warning recorded only:

```text
Some chunks are larger than 500 kB after minification.
```

## 4. Existing Product UI Inventory

Existing Product feature work:

- `frontend/src/features/products/pages/ProductsPage.tsx` existed as a
  placeholder/empty page file.
- No Product table, form, detail dialog, create dialog, or Product feature
  barrel was present.
- Router rendered an inline Product placeholder behind the existing
  `products.view` route protection.

No substantial competing Product UI implementation was found.

## 5. Canonical Feature Owner

Product feature owner:

```text
frontend/src/features/products/
```

The router imports through:

```ts
import { ProductsPage } from "@/features/products";
```

## 6. Product Page Owner

Canonical page:

```text
frontend/src/features/products/pages/ProductsPage.tsx
```

The page uses:

- `useProducts`
- `useCreateProduct`
- `useProductByCode`
- `useAuthorization`
- shared page and UI primitives

It does not import `productService`, construct Product query keys, read storage,
or call QueryClient.

## 7. Table Fields

Default Product table fields:

- Product
- Internal SKU
- Supplier SKU
- Category
- Brand
- Unit
- Product Type
- Selling Price
- Tax
- Status
- Actions

Pharmacy-relevant verified fields such as generic name, manufacturer,
prescription requirement, and product type are visible in list/detail contexts.

## 8. Search And Pagination

Search uses `useProducts` with `ListProductsRequest.search`.

Pagination uses `page` and `per_page` through the canonical Product list hook.

No client-side filtering is used as the primary search implementation.

## 9. Product Detail

Product detail is implemented as a dialog using verified `Product` fields.

Displayed groups include:

- identity
- classification
- pricing
- inventory configuration
- prescription settings
- manufacturer/tax
- codes
- lifecycle

No unsupported edit/delete/lifecycle actions are exposed.

## 10. Create Flow

Create uses:

```text
useCreateProduct
CreateProductRequest
```

The form sends only verified create DTO fields and excludes server-owned fields
such as `id`, `tenant_id`, timestamps, and audit data.

## 11. Create Permission

Backend evidence:

```text
POST /api/products -> @require_permission("products.create")
```

Create Product is gated by:

```text
products.create
```

Route access remains gated by:

```text
products.view
```

## 12. Category Disposition

No separate category lookup endpoint was activated.

The verified create route accepts `category_id` or `category_name`, and creates
or reuses a category by name when an id is not supplied. The UI uses
`category_name` and does not hardcode ids.

## 13. Brand Disposition

No separate brand lookup endpoint was activated.

The verified create route accepts `brand_id` or `brand_name`, and creates or
reuses a brand by name when an id is not supplied. The UI uses `brand_name`.

## 14. Unit Disposition

No separate unit lookup endpoint was activated.

The verified create route accepts `unit_id` or `unit_code` plus `unit_name`,
and creates or reuses a unit when an id is not supplied. The UI uses
`unit_code` and `unit_name`.

## 15. Product-Code Disposition

Added:

```text
frontend/src/hooks/queries/products/useProductByCode.ts
```

This hook is narrow because:

- `productService.getProductByCode` already exists;
- `QUERY_KEYS.products.byCode(scope, code)` already exists;
- the key is tenant-scoped after Migration 052;
- the query is disabled while the code is blank.

The create form supports one optional Product code through the verified
`CreateProductRequest.codes` shape. No scanner hardware integration was added.

## 16. Pricing Disposition

Product decimal values are represented as string/number request inputs and
string/null response fields. The form keeps decimal values as strings and
performs only non-negative validation at the UI boundary.

No financial precision conversion was introduced.

## 17. Prescription Field Disposition

`requires_prescription` is exposed in the create form and detail/table display.

No prescription validation, dispensing, patient record, or pharmacist workflow
was introduced.

## 18. Inventory Configuration Disposition

The page displays and creates Product configuration flags:

- `track_inventory`
- `track_batches`
- `track_expiry`
- `allow_negative_stock`
- `reorder_level`
- `reorder_qty`

No operational stock, batch, expiry, warehouse, transfer, receive, or count
workflow was introduced.

## 19. Update/Delete Disposition

Migration 024 remains authoritative:

- Product update unsupported
- Product delete unsupported
- Product deactivate/reactivate unsupported

The Products feature imports none of:

- `useUpdateProduct`
- `useDeleteProduct`

No edit/delete/lifecycle UI is shown.

## 20. Tenant And Branch Behavior

Products remain tenant-wide and tenant-owned.

The feature does not:

- read tenant id directly;
- read browser storage;
- pass branch id;
- introduce branch filtering;
- construct Product query keys.

Tenant cache isolation is handled by the Product hooks and Migration 052 query
scope.

## 21. Route Activation

`/products` now renders the operational `ProductsPage`.

Route remains:

```text
PATHS.PRODUCTS.ROOT
```

Route permission remains:

```text
products.view
```

Navigation remains unchanged.

## 22. Authorization

Backend-derived authorization is used through `useAuthorization()`.

Create action:

```text
products.create
```

Route access:

```text
products.view
```

No role inference was added.

## 23. Form Validation

Added:

```text
frontend/src/validation/productSchema.ts
```

Validation includes:

- required `internal_sku`
- required `name`
- non-negative pricing inputs
- non-negative reorder inputs

No speculative enum validation was added for `product_type`.

## 24. Loading, Error, And Empty States

The page includes:

- initial loading
- background refresh affordance
- Product list error state
- empty Product list state
- search-empty state
- create mutation pending state
- by-code lookup loading/error/result states

## 25. Component Reuse

Reused shared Hela360 primitives:

- `Page`
- `PageHeader`
- `PageToolbar`
- `PageSection`
- `LoadingState`
- `EmptyState`
- `ErrorState`
- `Table`
- `Dialog`
- `Button`
- `Input`
- `Textarea`
- `Badge`

Supplier Migration 053 informed the page composition, but no generic CRUD
framework was introduced.

## 26. Files Inspected

- `app/api/products.py`
- `app/auth/permissions.py`
- `frontend/src/types/entities/product.ts`
- `frontend/src/types/requests/create-product-request.ts`
- `frontend/src/types/requests/list-products-request.ts`
- `frontend/src/services/products/productService.ts`
- `frontend/src/hooks/queries/products/`
- `frontend/src/lib/queryKeys.ts`
- `frontend/src/features/products/`
- `frontend/src/features/inventory/`
- `frontend/src/components/`
- `frontend/src/validation/`
- relevant ADRs and Product migration reports

## 27. Files Created

- `frontend/src/features/products/components/ProductDetailDialog.tsx`
- `frontend/src/features/products/components/ProductFormDialog.tsx`
- `frontend/src/features/products/components/ProductsTable.tsx`
- `frontend/src/features/products/index.ts`
- `frontend/src/hooks/queries/products/useProductByCode.ts`
- `frontend/src/validation/productSchema.ts`
- `frontend/docs/architecture/reviews/MIGRATION-054-PRODUCT-OPERATIONAL-PAGE.md`

## 28. Files Modified

- `frontend/src/features/products/pages/ProductsPage.tsx`
- `frontend/src/hooks/queries/products/index.ts`
- `frontend/src/app/router.tsx`

## 29. TypeScript Before And After

```text
TypeScript errors before: 0
TypeScript errors after: 0
```

## 30. Vite Before And After

```text
Vite build before: PASS
Vite build after: PASS
```

## 31. Warnings

Existing warning remains:

```text
Some chunks are larger than 500 kB after minification.
```

## 32. Runtime Verification

Full runtime verification was not performed because this migration does not
fabricate credentials or change the known backend environment dependency
posture. Static compile/build verification was completed.

## 33. Remaining Product Blockers

- Backend Product list route still has the previously documented `query`
  initialization defect.
- Product update/delete/lifecycle operations remain unsupported.
- No dedicated category, brand, or unit lookup UI was activated.
- No barcode scanner hardware integration exists.
- Inventory operational stock data remains future scope.

## 34. Invariants Verified

- Product remains tenant-wide.
- Product cache remains tenant-isolated through scoped hooks.
- Product components consume canonical hooks.
- Product components do not import services.
- Product components do not own query keys.
- Product components do not invalidate cache directly.
- Route uses `PATHS.PRODUCTS.ROOT`.
- Route remains protected by `products.view`.
- Create authorization uses verified `products.create`.
- Unsupported Product mutations remain unavailable.
- Product and Inventory remain separate.
- Product and Procurement remain separate.
- TypeScript remains at zero errors.
- Production build remains successful.
- No backend source changes were made.

## 35. Rollback Boundary

Rollback can remove the Product feature files, `useProductByCode`, the Product
validation schema, and the Product route page import while leaving the existing
Product service, hooks, query keys, backend routes, and Supplier migration
unchanged.

## 36. Recommended Next Migration

Recommended next migration:

```text
Migration 055 - Customer Operational Page and Route Activation
```
