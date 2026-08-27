# Migration 013 - Product Type Ownership

## 1. Migration Purpose

Migration 013 establishes canonical frontend ownership for verified Product shared types.

This migration is Product-only. Customer, Supplier, Sales, Inventory, Procurement, Navigation, Authorization, query keys, invalidation, backend behavior, and Product service method design remain out of scope.

## 2. ADR Rules Applied

- ADR-001: service modules consume shared types and do not own business entities.
- ADR-004: business entities live under `src/types/entities`; request DTOs live under `src/types/requests`; response projections and enums exist only when supported by backend evidence.
- ADR-008: consumers depend on public barrels rather than private implementation details.
- ADR-009: type names use PascalCase and files use kebab-case.

## 3. Backend Product Model Verified

Canonical model:

```text
app/models/product.py::Product
```

Persistence facts:

- table: `products`
- primary key: string UUID from `UUIDPrimaryKeyMixin`
- tenant ownership: `tenant_id`, required, indexed, foreign key to `tenants.id`
- branch ownership: none on `Product`
- uniqueness: `(tenant_id, internal_sku)` through `uq_products_tenant_internal_sku`
- category relationship: `category_id` to `product_categories.id`
- brand relationship: `brand_id` to `brands.id`
- unit relationship: `unit_id` to `units_of_measure.id`
- SKU/product-code fields: `internal_sku`, `supplier_sku`, and separate `ProductCode` rows
- barcode fields: no dedicated `barcode`; product codes are serialized through `codes`
- name/description: `name`, `generic_name`, `description`
- unit of measure: related `unit`
- sale price: `min_sale_price`, `default_sale_price`
- purchase/cost price: `cost_price`
- currency: no Product-level currency field
- tax fields: `tax_code`
- stock flags: `track_inventory`, `allow_negative_stock`
- reorder fields: `reorder_level`, `reorder_qty`
- pharmaceutical fields: `generic_name`, `track_batches`, `track_expiry`, `pack_size`, `manufacturer`, `country_of_origin`
- prescription requirement: `requires_prescription`
- lifecycle: `is_active`
- product type: raw string field `product_type`, default `stockable`
- timestamps: `created_at`, `updated_at`
- audit fields: none beyond timestamps on Product
- nullable fields: category/brand/unit IDs, supplier SKU, generic name, description, sale/cost price fields, tax code, pack size, manufacturer, country, image URL
- relationships serialized by lookup in `app/api/products.py::_serialize_product`

## 4. Serializer Response Shape

`app/api/products.py::_serialize_product` returns raw snake_case JSON:

```text
id
tenant_id
internal_sku
supplier_sku
name
generic_name
description
product_type
track_inventory
track_batches
track_expiry
requires_prescription
allow_negative_stock
reorder_level
reorder_qty
min_sale_price
default_sale_price
cost_price
tax_code
pack_size
manufacturer
country_of_origin
image_url
is_active
category
brand
unit
codes
created_at
updated_at
```

Decimal fields serialize as strings or `null`. Related `category`, `brand`, and `unit` serialize as small nested objects or `null`. Product codes serialize as a list of code objects.

## 5. Backend Product Endpoints Verified

Confirmed:

- `GET /api/products`
  - permission: `products.view`
  - tenant scope from JWT identity
  - branch identity is read but not applied to Product filtering
  - query parameters: `search`, `is_active`, `product_type`
  - response: `{ ok: true, count, items: Product[] }`
  - service method: inline route implementation
  - confidence: Confirmed, with an implementation bug because `query` is referenced before initialization

- `GET /api/products/<product_id>`
  - permission: `products.view`
  - tenant scope from JWT identity
  - response: `{ ok: true, item: Product }` or `{ ok: false, error }`
  - status codes: 200, 404
  - confidence: Confirmed

- `POST /api/products`
  - permission: `products.create`
  - tenant scope from JWT identity
  - response: `{ ok: true, message, item: Product }`
  - status codes: 201, 400, 404, 409, 500
  - confidence: Confirmed

- `GET /api/products/by-code/<code_value>`
  - permission: `products.view`
  - tenant scope from JWT identity
  - response: `{ ok: true, item: Product }` or `{ ok: false, error }`
  - status codes: 200, 404
  - confidence: Confirmed

Insufficient evidence:

- update product
- delete product
- activate/deactivate product
- distinct search endpoint
- categories API in the inspected Product route
- product summary projection
- inventory-related Product projection endpoints

## 6. Create Request

Canonical owner:

```text
frontend/src/types/requests/create-product-request.ts
```

Required:

- `internal_sku`
- `name`

Accepted optional fields:

- `supplier_sku`
- `generic_name`
- `description`
- `category_id` or `category_name`
- `brand_id` or `brand_name`
- `unit_id` or `unit_code` plus `unit_name`
- `product_type`
- `track_inventory`
- `track_batches`
- `track_expiry`
- `requires_prescription`
- `allow_negative_stock`
- `reorder_level`
- `reorder_qty`
- `min_sale_price`
- `default_sale_price`
- `cost_price`
- `tax_code`
- `pack_size`
- `manufacturer`
- `country_of_origin`
- `image_url`
- `is_active`
- `codes`

Server-owned and excluded:

- `id`
- `tenant_id`
- `branch_id`
- `created_at`
- `updated_at`
- audit fields

## 7. Update Request

Canonical owner:

```text
frontend/src/types/requests/update-product-request.ts
```

The current backend Product API has no verified update route or update schema. The type is owned canonically to remove service-local DTO ownership and preserve the existing frontend update-hook type contract, but its runtime API support remains a deferred Product service/API backlog item.

## 8. Current Frontend Product Definitions Found

Duplicate service-local shared contracts were found in:

```text
frontend/src/services/products/productService.ts
```

Removed from service ownership:

- `Product`
- `CreateProductRequest`
- `UpdateProductRequest`

Unsupported exports were found in:

```text
frontend/src/services/products/index.ts
```

Removed from the Product service barrel:

- `ProductStatus`
- `ProductType`
- `ProductSummary`

No hook-local Product entity or request DTO definitions were found.

## 9. Canonical Product Entity

Canonical owner:

```text
frontend/src/types/entities/product.ts
```

The entity follows backend serializer snake_case because `productService` returns backend JSON directly and does not map fields to camelCase.

## 10. ProductStatus Disposition

`ProductStatus` was not created.

Backend lifecycle is represented by:

```text
is_active: boolean
```

No richer status enum or status-string contract was verified.

## 11. ProductType Disposition

`ProductType` was not created.

Backend persistence exposes `product_type: string`, but no authoritative finite set of supported values was found. The canonical entity and request DTO therefore represent it as `string`.

## 12. ProductSummary Disposition

`ProductSummary` was not created.

No backend endpoint was verified that returns a distinct Product summary projection.

## 13. Files Inspected

- `app/models/product.py`
- `app/models/inventory.py`
- `app/models/base.py`
- `app/models/__init__.py`
- `app/api/products.py`
- `app/api/sales.py`
- `app/services/`
- `app/schemas/`
- `app/serializers/`
- `frontend/src/services/products/productService.ts`
- `frontend/src/services/products/index.ts`
- `frontend/src/hooks/queries/products/*`
- `frontend/src/features/products/`
- `frontend/src/features/inventory/`
- `frontend/src/types/entities/*`
- `frontend/src/types/requests/*`
- `frontend/src/types/responses/*`
- `frontend/src/types/enums/*`
- `frontend/src/types/index.ts`
- Migration 001, 011, and 012 review documents
- ADR-001, ADR-004, ADR-008, ADR-009

## 14. Files Created

- `frontend/src/types/entities/product.ts`
- `frontend/src/types/requests/create-product-request.ts`
- `frontend/src/types/requests/update-product-request.ts`
- `frontend/docs/architecture/reviews/MIGRATION-013-PRODUCT-TYPE-OWNERSHIP.md`

## 15. Files Modified

- `frontend/src/types/entities/index.ts`
- `frontend/src/types/requests/index.ts`
- `frontend/src/services/products/productService.ts`
- `frontend/src/services/products/index.ts`

No backend files were modified.

## 16. Barrels Updated

- `frontend/src/types/entities/index.ts` now exports `Product`.
- `frontend/src/types/requests/index.ts` now exports `CreateProductRequest` and `UpdateProductRequest`.
- `frontend/src/services/products/index.ts` re-exports Product shared types from `@/types` instead of `productService.ts`.
- No Product enum or Product response barrel was updated because no supported enum or summary projection exists.

## 17. Imports Migrated

`frontend/src/services/products/productService.ts` now imports:

- `Product` from `@/types/entities`
- `CreateProductRequest` and `UpdateProductRequest` from `@/types/requests`

Product hooks already imported shared types from canonical type barrels and required no import-path changes.

## 18. Compiler Errors Before

Baseline:

```text
218 TypeScript errors
```

## 19. Compiler Errors After

Post-migration:

```text
211 TypeScript errors
```

Command:

```bash
npx tsc -b --pretty false 2>&1 | grep -c "error TS"
```

## 20. Net Reduction

```text
7 fewer TypeScript errors
```

## 21. Product Diagnostics Before And After

Before:

- missing `Product` export from `@/types/entities`: 4 diagnostics
- missing `CreateProductRequest` export from `@/types/requests`: 1 diagnostic
- missing `UpdateProductRequest` export from `@/types/requests`: 1 diagnostic
- invalid `ProductStatus` service-barrel export: 1 diagnostic
- invalid `ProductType` service-barrel export: 1 diagnostic
- invalid `ProductSummary` service-barrel export: 1 diagnostic

After:

- missing `Product` export: 0 diagnostics
- missing `CreateProductRequest` export: 0 diagnostics
- missing `UpdateProductRequest` export: 0 diagnostics
- invalid `ProductStatus` export: 0 diagnostics
- invalid `ProductType` export: 0 diagnostics
- invalid `ProductSummary` export: 0 diagnostics

## 22. Newly Exposed Mismatches

The compiler now reaches deferred Product hook/service mismatches:

- `useCreateProduct`: `productService.create` returns `ApiResponse<Product>`, while `useCreateEntity` expects `Product`.
- `useUpdateProduct`: `productService.update` returns `ApiResponse<Product>`, while `useUpdateEntity` expects `Product`.

These are response-envelope issues and intentionally remain out of scope.

## 23. Remaining Product Blockers

- `productService.findById` does not exist.
- `useProducts` passes `PaginationRequest` to a query-key function that currently expects no arguments.
- `productService.paginate(params)` uses a BaseService query option shape that does not match `PaginationRequest`.
- Product create/update mutation hooks still expose response-envelope mismatches.
- Product API list route has a backend implementation bug: `query` is used before initialization.
- Product update/delete/activate/deactivate routes are not verified in backend source.
- Product-specific inventory service-barrel export diagnostics remain, but they belong to Inventory/Product cross-domain cleanup and were not changed.

## 24. Runtime Behavior

Runtime behavior is unchanged.

No endpoint, service method, query key, invalidation helper, hook behavior, response unwrapping, or backend source was changed.

## 25. Invariants Verified

- Product has one canonical frontend entity owner under `src/types/entities`.
- Product request DTOs live under `src/types/requests`.
- Product response projections were not created without backend support.
- Product enum-like contracts were not created without backend support.
- Product service consumes canonical shared types.
- Product hooks consume canonical shared types through existing type barrels.
- Shared Product types are no longer defined in Product service or hooks.
- Product service barrel does not own shared Product DTO definitions.
- Type-only imports and exports were used for shared contracts.
- No Product service method changed.
- No Product query key changed.
- No invalidation behavior changed.
- No backend file changed.
- No Customer or unrelated domain source file changed.

## 26. Rollback Boundary

Rollback is limited to the Product type files, Product type barrel exports, Product service type imports, Product service-barrel Product type exports, and this report.

## 27. Recommended Next Migration

Recommended next migration:

```text
Migration 014 - Customer Type Ownership
```
