# Migration 011 - Frontend Supplier Type Ownership

## 1. Migration Purpose

Migration 011 establishes canonical frontend ownership for the verified backend Supplier contract created in Migration 010.

This migration creates only:

- `Supplier`
- `CreateSupplierRequest`
- `UpdateSupplierRequest`

It also removes invalid public supplier service-barrel exports for unsupported supplier contracts.

## 2. ADR Requirements Applied

- ADR-001: services must consume shared types and must not own business entities.
- ADR-004: reusable entity and request DTO types must live under `src/types/`.
- ADR-008: shared contracts are exposed through stable public barrels.
- ADR-009: type names use PascalCase; filenames use kebab-case.

## 3. Backend Supplier Sources Inspected

- `app/models/supplier.py`
- `app/api/suppliers.py`
- `app/schemas/supplier.py`
- `app/serializers/supplier.py`
- `app/services/tenant/procurement/supplier_service.py`
- `app/services/tenant/procurement/tests/test_supplier_contract.py`
- `migrations/versions/8f3b7c2a9d10_add_suppliers.py`
- `frontend/docs/architecture/reviews/MIGRATION-009-SUPPLIER-TYPE-OWNERSHIP.md`
- `frontend/docs/architecture/reviews/MIGRATION-010-BACKEND-SUPPLIER-CONTRACT.md`

## 4. Verified Serializer Response Shape

The backend serializer returns raw snake_case JSON:

```text
id
tenant_id
supplier_code
name
legal_name
contact_person
email
phone
alternate_phone
address_line_1
address_line_2
city
county_or_region
country
postal_code
tax_number
registration_number
payment_terms_days
credit_limit
currency
notes
is_active
created_at
updated_at
```

`credit_limit` is serialized as a string. Nullable database fields serialize as `null`. Timestamps serialize as ISO strings or `null`.

## 5. Verified Create Schema

Create accepts:

```text
supplier_code
name
legal_name
contact_person
email
phone
alternate_phone
address_line_1
address_line_2
city
county_or_region
country
postal_code
tax_number
registration_number
payment_terms_days
credit_limit
currency
notes
is_active
```

Required:

- `supplier_code`
- `name`

Server-derived and excluded:

- `id`
- `tenant_id`
- `created_at`
- `updated_at`

## 6. Verified Update Schema

Update accepts PATCH-style partial fields for:

```text
supplier_code
name
legal_name
contact_person
email
phone
alternate_phone
address_line_1
address_line_2
city
county_or_region
country
postal_code
tax_number
registration_number
payment_terms_days
credit_limit
currency
notes
is_active
```

The canonical frontend `UpdateSupplierRequest` intentionally excludes `is_active` because lifecycle is exposed through dedicated deactivate/reactivate workflow endpoints.

## 7. Canonical Supplier Entity

Owner:

```text
frontend/src/types/entities/supplier.ts
```

The entity uses snake_case because the current supplier service returns backend payloads directly and does not perform a camelCase mapping.

## 8. Canonical Create Request

Owner:

```text
frontend/src/types/requests/create-supplier-request.ts
```

Includes only fields accepted by the backend create schema. It excludes tenant ownership and server-generated fields.

## 9. Canonical Update Request

Owner:

```text
frontend/src/types/requests/update-supplier-request.ts
```

Represents a partial PATCH payload. It excludes tenant ownership, timestamps, IDs, and lifecycle activation fields.

## 10. Tenant Ownership Treatment

Supplier remains server-owned by tenant. `tenant_id` exists on `Supplier` responses but is absent from create/update request DTOs.

## 11. Branch Ownership Treatment

Supplier has no `branch_id` or branch ownership field. The verified backend contract is tenant-wide.

## 12. Lifecycle Representation

Lifecycle is represented by:

```text
is_active: boolean
```

No runtime status object or enum was introduced.

## 13. SupplierStatus Disposition

`SupplierStatus` was not created. The backend does not expose a status enum.

## 14. SupplierType Disposition

`SupplierType` was not created. The backend has no supplier type/category field.

## 15. SupplierContact Disposition

`SupplierContact` was not created. The backend uses flat contact fields.

## 16. SupplierSummary Disposition

`SupplierSummary` was not created. The backend has no summary projection endpoint.

## 17. Files Inspected

- backend Supplier model/schema/serializer/service/API/test/migration files
- `frontend/src/services/suppliers/supplierService.ts`
- `frontend/src/services/suppliers/index.ts`
- `frontend/src/hooks/queries/suppliers/*`
- `frontend/src/types/entities/*`
- `frontend/src/types/requests/*`
- `frontend/src/types/index.ts`
- `frontend/src/types/entities/index.ts`
- `frontend/src/types/requests/index.ts`

## 18. Files Created

- `frontend/src/types/entities/supplier.ts`
- `frontend/src/types/requests/create-supplier-request.ts`
- `frontend/src/types/requests/update-supplier-request.ts`
- `frontend/docs/architecture/reviews/MIGRATION-011-FRONTEND-SUPPLIER-TYPES.md`

## 19. Files Modified

- `frontend/src/types/entities/index.ts`
- `frontend/src/types/requests/index.ts`
- `frontend/src/services/suppliers/supplierService.ts`
- `frontend/src/services/suppliers/index.ts`

No backend files were modified during Migration 011.

## 20. Service-Local Definitions Removed

Removed service-local duplicate definitions from `supplierService.ts`:

- `Supplier`
- `CreateSupplierRequest`
- `UpdateSupplierRequest`

The service now imports those from canonical shared type owners.

## 21. Barrel Exports Corrected

Added canonical type exports:

- `Supplier` from `frontend/src/types/entities/index.ts`
- `CreateSupplierRequest` from `frontend/src/types/requests/index.ts`
- `UpdateSupplierRequest` from `frontend/src/types/requests/index.ts`

Removed unsupported supplier service-barrel exports:

- `SupplierStatus`
- `SupplierType`
- `SupplierSummary`
- `SupplierContact`
- `SupplierPerformance`

`SupplierPerformance` remains local inside `supplierService.ts` because an existing unsupported service method references it. It is not exported as a public shared supplier contract.

## 22. Imports Migrated

`supplierService.ts` now imports:

```typescript
import type { Supplier } from "@/types/entities";
import type {
  CreateSupplierRequest,
  UpdateSupplierRequest,
} from "@/types/requests";
```

Supplier hooks already imported from canonical barrels, so no hook runtime or import path change was required.

## 23. Backend/Frontend Naming Strategy

The canonical Supplier and request DTOs use backend snake_case.

Reason: the current supplier service does not map backend JSON to camelCase. Creating camelCase types would make the type system lie about runtime data and would require a service mapping redesign that is out of scope.

## 24. Compiler Errors Before

Baseline from the migration brief:

```text
236 TypeScript errors
```

Pre-edit `npm run build` also showed the expected Supplier missing-export and invalid service-barrel diagnostics.

## 25. Compiler Errors After

Post-migration count:

```text
228 TypeScript errors
```

Command used:

```bash
npx tsc -b --pretty false 2>&1 | grep -c "error TS"
```

## 26. Net Reduction

```text
8 fewer TypeScript errors
```

## 27. Supplier Diagnostics Before And After

Resolved missing canonical exports:

- missing `Supplier` from `@/types/entities`
- missing `CreateSupplierRequest` from `@/types/requests`
- missing `UpdateSupplierRequest` from `@/types/requests`

Resolved invalid supplier service-barrel exports:

- `SupplierStatus`
- `SupplierType`
- `SupplierSummary`
- `SupplierContact`

## 28. Newly Exposed Mismatches

The canonical `Supplier` type exposed existing supplier hook/service response-envelope mismatches:

```text
useCreateSupplier: Promise<ApiResponse<Supplier>> is not assignable to Promise<Supplier>
useUpdateSupplier: Promise<ApiResponse<Supplier>> is not assignable to Promise<Supplier>
```

These are service/hook behavior issues, not type ownership issues.

## 29. New Diagnostics

Newly visible Supplier diagnostics:

- create mutation expects bare `Supplier`, service returns `ApiResponse<Supplier>`
- update mutation expects bare `Supplier`, service returns `ApiResponse<Supplier>`

No new unsupported Supplier type was introduced.

## 30. Remaining Supplier Blockers

Remaining supplier-related diagnostics:

- `UseEntityOptions` missing from common query hooks
- `supplierService.findById` missing
- supplier query key list signature mismatch
- create/update response envelope mismatch
- procurement supplier delivery placeholders still missing unrelated contracts/services
- navigation ID union still excludes `suppliers`

These were explicitly deferred by the migration brief.

## 31. Invariants Verified

- `Supplier` has one canonical owner under `src/types/entities/`.
- `CreateSupplierRequest` has one canonical owner under `src/types/requests/`.
- `UpdateSupplierRequest` has one canonical owner under `src/types/requests/`.
- Supplier request DTOs do not include tenant ownership.
- Supplier has no branch field.
- Supplier lifecycle uses `is_active`.
- No canonical `SupplierStatus` exists.
- No canonical `SupplierType` exists.
- No canonical `SupplierContact` exists.
- No canonical `SupplierSummary` exists.
- Supplier service consumes canonical shared types.
- Supplier hook runtime behavior was not changed.
- Supplier service method names and endpoints were not changed.
- Query keys and invalidation were not changed.
- No backend file was modified during Migration 011.

## 32. Rollback Boundary

Rollback is limited to the three canonical Supplier type files, the type/service barrel edits, the supplier service type-import change, and this report.

## 33. Unrelated Argon2 Startup Blocker

The backend app startup blocker from Migration 010 remains unrelated:

```text
ModuleNotFoundError: No module named 'argon2'
```

This migration did not address backend dependencies.

## 34. Recommended Next Migration

Recommended Migration 012:

```text
Frontend Supplier Service Response Boundary
```

Suggested scope:

- decide whether supplier service returns raw `ApiResponse<Supplier>` or unwraps `item`;
- align create/update hooks with that decision;
- address supplier list pagination envelope only if included in that migration;
- keep `findById`, query-key redesign, invalidation, and lifecycle hook design separate unless explicitly scoped.
