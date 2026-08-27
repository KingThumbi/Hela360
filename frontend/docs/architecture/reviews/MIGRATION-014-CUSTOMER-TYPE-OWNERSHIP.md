# Migration 014 - Customer Type Ownership

## 1. Migration Purpose

Migration 014 establishes canonical frontend ownership for verified Customer shared types.

This migration is Customer-only. Product, Supplier, Sales, Inventory, Procurement, Navigation, Providers, Authorization, query keys, invalidation, backend behavior, and Customer service method design remain out of scope.

## 2. ADR Rules Applied

- ADR-001: services consume shared types and do not own reusable business entities.
- ADR-004: business entities live under `src/types/entities`; request DTOs live under `src/types/requests`; response projections and enums exist only when supported by backend evidence.
- ADR-008: consumers use stable public barrels.
- ADR-009: type names use PascalCase and files use kebab-case.

## 3. Backend Customer Model Verified

Canonical model:

```text
app/models/customer.py::Customer
```

Persistence facts:

- table: `customers`
- primary key: string UUID from `UUIDPrimaryKeyMixin`
- tenant ownership: `tenant_id`, required, indexed, foreign key to `tenants.id`
- branch ownership: none on `Customer`
- customer reference: `customer_number`, required
- uniqueness: `(tenant_id, customer_number)` through `uq_customers_tenant_customer_number`
- name fields: `first_name`, `last_name`, `other_names`
- display name: serializer derives `full_name` by joining first name, other names, and last name
- phone fields: `phone`
- email fields: `email`
- address fields: flat `address`, `city`
- tax/registration fields: none
- customer category/type fields: none
- lifecycle: `is_active`
- loyalty: `loyalty_points`
- credit limit: none
- account balance: none
- pricing group: none
- notes: none
- timestamps: `created_at`, `updated_at`
- audit fields: none beyond timestamps
- nullable fields: `last_name`, `other_names`, `phone`, `email`, `gender`, `date_of_birth`, `id_number`, `address`, `city`
- relationships: none verified

The initial migration also contains the same table shape in `migrations/versions/19b1ccd035ac_initial_schema.py`.

## 4. Serializer Response Shape

`app/api/customers.py::_serialize_customer` returns raw snake_case JSON:

```text
id
tenant_id
customer_number
first_name
last_name
other_names
full_name
phone
email
gender
date_of_birth
id_number
address
city
loyalty_points
is_active
created_at
updated_at
```

`loyalty_points` serializes as a string. Timestamps and date fields serialize as ISO strings or `null`.

The duplicated Customer route section in `app/api/sales.py` uses the same Customer model and route shape.

## 5. Backend Customer Endpoints Verified

Confirmed:

- `GET /api/customers`
  - permission: `customers.view`
  - tenant scope from JWT identity
  - branch identity is read in `app/api/customers.py` but not applied to Customer filtering
  - query parameters: `search`, `is_active`
  - response: `{ ok: true, count, items: Customer[] }`
  - status codes: 200
  - service invoked: inline route implementation
  - confidence: Confirmed

- `GET /api/customers/<customer_id>`
  - permission: `customers.view`
  - tenant scope from JWT identity
  - response: `{ ok: true, item: Customer }` or `{ ok: false, error }`
  - status codes: 200, 404
  - service invoked: inline route implementation
  - confidence: Confirmed

- `POST /api/customers`
  - permission: `customers.create`
  - tenant scope from JWT identity
  - response: `{ ok: true, message, item: Customer }`
  - status codes: 201, 400, 409, 500
  - service invoked: inline route implementation
  - confidence: Confirmed

Insufficient evidence:

- update customer
- delete customer
- activate/deactivate customer
- dedicated customer search endpoint
- customer history endpoint
- customer balance endpoint
- customer summary projection
- separate customer addresses or contacts

## 6. Create Request

Canonical owner:

```text
frontend/src/types/requests/create-customer-request.ts
```

Required:

- `first_name`

Accepted optional fields:

- `customer_number`
- `last_name`
- `other_names`
- `phone`
- `email`
- `gender`
- `date_of_birth`
- `id_number`
- `address`
- `city`
- `is_active`

Server-owned and excluded:

- `id`
- `tenant_id`
- `branch_id`
- `created_at`
- `updated_at`
- audit fields
- `loyalty_points`
- account balance

## 7. Update Request

Canonical owner:

```text
frontend/src/types/requests/update-customer-request.ts
```

The current backend Customer API has no verified update route or update schema. The type is owned canonically to remove service-local DTO ownership and preserve the existing frontend update-hook type contract, but runtime API support remains a deferred Customer service/API backlog item.

## 8. Current Frontend Customer Definitions Found

Duplicate service-local shared contracts were found in:

```text
frontend/src/services/customers/customerService.ts
```

Removed from service ownership:

- `Customer`
- `CreateCustomerRequest`
- `UpdateCustomerRequest`

Unsupported public shared exports were found in:

```text
frontend/src/services/customers/index.ts
```

Removed from the Customer service barrel:

- `CustomerStatus`
- `CustomerStatistics`
- `CustomerBalance`

No hook-local Customer entity or request DTO definitions were found.

No Sales-local competing Customer interface was found in the inspected frontend Sales files.

## 9. Canonical Customer Entity

Canonical owner:

```text
frontend/src/types/entities/customer.ts
```

The entity follows backend serializer snake_case because `customerService` returns backend payloads directly and does not map fields to camelCase.

## 10. CustomerStatus Disposition

`CustomerStatus` was not created.

Backend lifecycle is represented by:

```text
is_active: boolean
```

No richer status enum or status-string contract was verified.

## 11. CustomerType Disposition

`CustomerType` was not created.

The backend has no verified customer type, category, account class, business/individual distinction, pricing group, or finite classification contract.

## 12. CustomerAddress Disposition

`CustomerAddress` was not created.

The backend uses flat `address` and `city` fields on Customer. No separate address model, nested serializer object, or address endpoint was verified.

## 13. CustomerContact Disposition

`CustomerContact` was not created.

The backend uses flat `phone` and `email` fields on Customer. No separate contact model, nested serializer object, or contact endpoint was verified.

## 14. CustomerSummary Disposition

`CustomerSummary` was not created.

No backend endpoint was verified that returns a distinct Customer summary projection.

## 15. CustomerHistory And CustomerBalance Disposition

`CustomerHistory` and canonical `CustomerBalance` response DTOs were not created.

The frontend service contains methods named `purchaseHistory` and `balance`, but no matching backend Customer endpoints were verified in the inspected Customer API. The existing local method return types were left service-local and removed from the service barrel.

## 16. Files Inspected

- `app/models/customer.py`
- `app/models/__init__.py`
- `app/api/customers.py`
- Customer route copy in `app/api/sales.py`
- `app/services/tenant/customers/customer_service.py`
- `app/services/`
- `app/schemas/`
- `app/serializers/`
- `migrations/versions/19b1ccd035ac_initial_schema.py`
- `frontend/src/services/customers/customerService.ts`
- `frontend/src/services/customers/index.ts`
- `frontend/src/hooks/queries/customers/*`
- `frontend/src/features/customers/`
- `frontend/src/features/sales/`
- `frontend/src/services/sales/`
- `frontend/src/types/entities/*`
- `frontend/src/types/requests/*`
- `frontend/src/types/responses/*`
- `frontend/src/types/enums/*`
- `frontend/src/types/index.ts`
- Canonical frontend architecture review
- Migration 011 and 013 review documents
- ADR-001, ADR-004, ADR-008, ADR-009

## 17. Files Created

- `frontend/src/types/entities/customer.ts`
- `frontend/src/types/requests/create-customer-request.ts`
- `frontend/src/types/requests/update-customer-request.ts`
- `frontend/docs/architecture/reviews/MIGRATION-014-CUSTOMER-TYPE-OWNERSHIP.md`

## 18. Files Modified

- `frontend/src/types/entities/index.ts`
- `frontend/src/types/requests/index.ts`
- `frontend/src/services/customers/customerService.ts`
- `frontend/src/services/customers/index.ts`

No backend files were modified.

## 19. Barrels Updated

- `frontend/src/types/entities/index.ts` now exports `Customer`.
- `frontend/src/types/requests/index.ts` now exports `CreateCustomerRequest` and `UpdateCustomerRequest`.
- `frontend/src/services/customers/index.ts` re-exports Customer shared types from `@/types` instead of `customerService.ts`.
- No Customer enum or Customer response barrel was updated because no supported enum or response projection exists.

## 20. Imports Migrated

`frontend/src/services/customers/customerService.ts` now imports:

- `Customer` from `@/types/entities`
- `CreateCustomerRequest` and `UpdateCustomerRequest` from `@/types/requests`

Customer hooks already imported shared types from canonical type barrels and required no import-path changes.

## 21. Compiler Errors Before

Baseline:

```text
211 TypeScript errors
```

## 22. Compiler Errors After

Post-migration:

```text
207 TypeScript errors
```

Command:

```bash
npx tsc -b --pretty false 2>&1 | grep -c "error TS"
```

## 23. Net Reduction

```text
4 fewer TypeScript errors
```

## 24. Customer Diagnostics Before And After

Before:

- missing `Customer` export from `@/types/entities`: 4 diagnostics
- missing `CreateCustomerRequest` export from `@/types/requests`: 1 diagnostic
- missing `UpdateCustomerRequest` export from `@/types/requests`: 1 diagnostic
- invalid `CustomerStatus`, `CustomerType`, `CustomerSummary`, `CustomerAddress`, or `CustomerContact` canonical exports: 0 diagnostics

After:

- missing `Customer` export: 0 diagnostics
- missing `CreateCustomerRequest` export: 0 diagnostics
- missing `UpdateCustomerRequest` export: 0 diagnostics
- unsupported Customer enum/summary/address/contact canonical exports: 0 diagnostics

## 25. Newly Exposed Mismatches

The compiler now reaches deferred Customer hook/service mismatches:

- `useCreateCustomer`: `customerService.create` returns `ApiResponse<Customer>`, while `useCreateEntity` expects `Customer`.
- `useUpdateCustomer`: `customerService.update` returns `ApiResponse<Customer>`, while `useUpdateEntity` expects `Customer`.

These are response-envelope issues and intentionally remain out of scope.

## 26. Remaining Customer Blockers

- `customerService.findById` does not exist.
- `useCustomers` passes `PaginationRequest` to a query-key function that currently expects no arguments.
- `customerService.paginate(params)` uses a BaseService query option shape that does not match `PaginationRequest`.
- Customer create/update mutation hooks still expose response-envelope mismatches.
- Customer update/delete/activate/deactivate routes are not verified in backend source.
- Customer history, balance, statistics, prescriptions, and loyalty service methods point at unverified backend endpoints.

## 27. Runtime Behavior

Runtime behavior is unchanged.

No endpoint, service method, query key, invalidation helper, hook behavior, response unwrapping, mapping, or backend source was changed.

## 28. Invariants Verified

- Customer has one canonical frontend entity owner under `src/types/entities`.
- Customer request DTOs live under `src/types/requests`.
- Customer response projections were not created without backend support.
- Customer enum-like contracts were not created without backend support.
- Customer service consumes canonical shared types.
- Customer hooks consume canonical shared types through existing type barrels.
- Shared Customer entity/request contracts are no longer defined in Customer service or hooks.
- Customer service barrel does not own shared Customer DTO definitions.
- Type-only imports and exports were used for shared contracts.
- No Customer service method changed.
- No Customer query key changed.
- No invalidation behavior changed.
- No backend file changed.
- No Product, Supplier, or unrelated domain source file changed.

## 29. Rollback Boundary

Rollback is limited to the Customer type files, Customer type barrel exports, Customer service type imports, Customer service-barrel Customer type exports, and this report.

## 30. Recommended Next Migration

Recommended next migration:

```text
Migration 015 - Inventory Type Ownership
```
