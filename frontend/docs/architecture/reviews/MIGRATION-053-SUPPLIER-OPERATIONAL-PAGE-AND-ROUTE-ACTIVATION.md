# Migration 053 - Supplier Operational Page And Route Activation

## 1. Migration Purpose

Migration 053 activates the verified Supplier vertical slice as the first
complete operational ERP feature page.

The migration remains frontend-only and does not expand Procurement into
purchase orders, goods receipts, deliveries, analytics, invoices, or supplier
balances.

## 2. Baseline

Commands:

```bash
cd /home/thumbi/Hela360/frontend
npx tsc -b --pretty false
npm run build
```

Result:

```text
TypeScript errors: 0
Vite build: PASS
```

Existing Vite warning recorded only:

```text
Some chunks are larger than 500 kB after minification.
```

## 3. Existing Supplier Feature Work

No existing Supplier feature page, table, form, dialog, or feature barrel was
present under `frontend/src/features/suppliers/`.

Existing canonical Supplier architecture was preserved:

- `frontend/src/types/entities/supplier.ts`
- `frontend/src/types/requests/create-supplier-request.ts`
- `frontend/src/types/requests/update-supplier-request.ts`
- `frontend/src/services/suppliers/supplierService.ts`
- `frontend/src/hooks/queries/suppliers/`
- tenant-scoped Supplier query keys and invalidation from Migration 052

Active/inactive lifecycle source remains `Supplier.is_active`.

## 4. Canonical Feature Boundary

Supplier is owned by:

```text
frontend/src/features/suppliers/
```

The router imports through the feature public barrel:

```ts
import { SuppliersPage } from "@/features/suppliers";
```

The page consumes public architecture boundaries only:

- `@/hooks/queries/suppliers`
- `@/types`
- shared page/UI components
- `useAuthorization()`

It does not import Supplier services directly.

## 5. Operational Page

Added:

```text
frontend/src/features/suppliers/pages/SuppliersPage.tsx
```

The page provides:

- Supplier list
- server-backed search through `useSuppliers(params)`
- canonical pagination
- create Supplier dialog
- edit Supplier dialog
- detail dialog
- active/inactive lifecycle representation
- deactivate confirmation
- reactivate confirmation
- loading state
- empty state
- search empty state
- error state
- mutation pending state

No branch id is read, displayed as ownership, or passed to Supplier queries.

## 6. Supplier Table

Added:

```text
frontend/src/features/suppliers/components/SuppliersTable.tsx
```

Default columns:

- Supplier
- Code
- Contact
- Location
- Payment Terms
- Status
- Actions

Only verified `Supplier` entity fields are displayed.

## 7. Forms

Added:

```text
frontend/src/features/suppliers/components/SupplierFormDialog.tsx
frontend/src/validation/supplierSchema.ts
```

The form uses React Hook Form and Zod, matching existing frontend validation
conventions.

Create uses `CreateSupplierRequest`.

Update uses `UpdateSupplierRequest` and does not send the complete Supplier
entity.

Lifecycle `is_active` is not edited through the form. Deactivate/reactivate
remain dedicated operations.

## 8. Lifecycle

Existing compatibility hook retained:

```text
useDeleteSupplier
```

It continues to mean Supplier deactivation.

Added narrow verified hook:

```text
frontend/src/hooks/queries/suppliers/useReactivateSupplier.ts
```

It is allowed because:

- `supplierService.reactivateSupplier` already exists;
- the backend reactivate route is verified;
- Supplier invalidation is tenant-scoped;
- the hook follows the canonical common mutation pattern.

User-visible text uses:

```text
Deactivate
Reactivate
```

No hard-delete language is exposed.

## 9. Authorization

The page uses backend-derived permissions through `useAuthorization()`.

Verified Supplier permissions applied:

- `suppliers.create` controls Create Supplier visibility
- `suppliers.update` controls Edit visibility
- `suppliers.deactivate` controls Deactivate/Reactivate visibility

Route access uses `suppliers.view`.

## 10. Route Activation

Registered the existing canonical route:

```text
/procurement/suppliers
```

Files changed:

```text
frontend/src/app/router.tsx
frontend/src/routes/permissions.ts
```

Route chain:

```text
navigation Suppliers
  -> PATHS.PROCUREMENT.SUPPLIERS
  -> router route
  -> ProtectedRoute
  -> suppliers.view
  -> SuppliersPage
```

Navigation IDs and section labels were not changed.

## 11. Tenant and Branch Scope

Supplier server state remains tenant-wide through the canonical Supplier hooks.

The feature does not:

- pass tenant ids manually;
- read browser storage;
- inject tenant headers;
- construct query keys;
- use branch scope.

## 12. Verification

Static checks performed:

- TypeScript compile
- production build
- route metadata grep
- Supplier feature direct-service/query-key grep
- branch-id grep

Runtime backend verification was not performed because this migration did not
fabricate credentials or change the known environment dependency posture.
