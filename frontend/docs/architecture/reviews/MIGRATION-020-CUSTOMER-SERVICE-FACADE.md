# Migration 020 - Customer Service Facade

## 1. Migration Purpose

Migration 020 restores the verified Customer public service facade for backend-supported Customer operations and establishes a truthful transport-to-domain response boundary.

This migration is Customer-only. It does not modify backend files, query keys, invalidation policy, Customer UI, or unrelated domains.

## 2. ADR Rules Applied

- ADR-001: domain services expose business-oriented methods and hide transport envelopes from hooks.
- ADR-002: hooks consume services and do not unwrap API responses.
- ADR-003: mutation hooks continue using centralized invalidation helpers.
- ADR-004: Customer entity and request DTO ownership remains under `src/types`.
- ADR-008: the Customer service barrel exposes the public Customer service boundary.
- ADR-009: service method names use explicit business language.

## 3. Backend Customer Endpoints Verified

Verified in `app/api/customers.py`:

- `GET /api/customers`
- `GET /api/customers/<customer_id>`
- `POST /api/customers`

Duplicated Customer routes with the same shapes also exist in `app/api/sales.py`.

No backend route was verified for:

- `PATCH /api/customers/<id>`
- `PUT /api/customers/<id>`
- `DELETE /api/customers/<id>`
- deactivate customer
- reactivate customer
- customer history
- customer balance
- customer statistics
- customer loyalty
- customer prescriptions
- customer phone or national-ID lookup

## 4. Existing Customer Service Methods

Before this migration, `frontend/src/services/customers/customerService.ts` inherited generic BaseService methods and exposed unverified Customer-local methods:

- inherited `list`
- inherited `paginate`
- inherited `get`
- inherited `create`
- inherited `update`
- inherited `delete`
- unsupported `searchByPhone`
- unsupported `searchByNationalId`
- unsupported `statistics`
- unsupported `balance`
- unsupported `purchaseHistory`
- unsupported `prescriptions`
- unsupported `loyalty`

Customer hooks called generic BaseService names directly:

- `useCustomers` -> `customerService.paginate`
- `useCustomer` -> `customerService.findById`
- `useCreateCustomer` -> `customerService.create`
- `useUpdateCustomer` -> `customerService.update`
- `useDeleteCustomer` -> `customerService.delete`

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

The verified Customer backend uses `item` for single-entity responses and `count` plus `items` for the list response.

## 6. Canonical Public Facade

Canonical Customer service owner:

```text
frontend/src/services/customers/customerService.ts
```

Canonical public import path:

```typescript
import { customerService } from "@/services/customers";
```

Established facade methods:

- `listCustomers`
- `getCustomer`
- `createCustomer`

No `updateCustomer`, `deleteCustomer`, `deactivateCustomer`, or `reactivateCustomer` method was added because no matching backend route was verified.

No `findById` Customer method was added or retained as canonical.

## 7. Method Contract Table

| Method | Backend operation | Return type | Envelope handling |
| --- | --- | --- | --- |
| `listCustomers(params?)` | `GET /customers` | `PaginatedResponse<Customer>` | unwraps `items`; derives pagination from `count` and request params |
| `getCustomer(id)` | `GET /customers/<id>` | `Customer` | unwraps `item` |
| `createCustomer(payload)` | `POST /customers` | `Customer` | unwraps `item` |

## 8. Response Envelope Handling

Detail and create responses use:

```text
{ ok: true, item: Customer }
```

Create also includes `message`.

The service unwraps `item` and returns `Customer`.

The list endpoint returns:

```text
{ ok: true, count: number, items: Customer[] }
```

The service converts this verified list envelope to canonical `PaginatedResponse<Customer>` for the hook boundary. Because the backend does not return pagination metadata, the service derives:

- `page` from `PaginationRequest.page` or `1`
- `per_page` from `PaginationRequest.per_page` or returned item count
- `total` from backend `count`
- `pages`, `has_next`, and `has_prev` from those values

No hook unwraps API envelopes.

## 9. List Response Contract

Backend list response:

```text
{ ok, count, items }
```

Frontend service return:

```text
PaginatedResponse<Customer>
```

This is a Customer-specific service boundary adaptation. It does not change the canonical generic API types.

## 10. Detail Response Contract

Backend detail response:

```text
{ ok, item }
```

Frontend service return:

```text
Customer
```

## 11. Create Response Contract

Backend create response:

```text
{ ok, message, item }
```

Frontend service return:

```text
Customer
```

## 12. Update Response Contract

No backend update route or response envelope was verified.

`useUpdateCustomer` was left on its existing unresolved path and remains a Customer blocker.

No `updateCustomer` facade method was fabricated.

## 13. Lifecycle Operation Disposition

No Customer deactivate or reactivate backend route was verified.

No Customer lifecycle facade method was added.

Customer lifecycle remains represented only by the verified `is_active` response field and create-time `is_active` request field.

## 14. Delete Hook Disposition

No backend hard-delete route was verified.

`useDeleteCustomer` currently calls inherited `customerService.delete(id)`, which maps to unsupported `DELETE /customers/<id>`.

This migration leaves that hook unchanged because silently reinterpreting delete as deactivation is not supported by backend evidence and no deactivation endpoint exists.

## 15. History Disposition

Customer purchase history is unsupported in the verified backend Customer route set.

The unverified `purchaseHistory` service method was removed from the Customer service public surface.

No `CustomerHistory` type or response projection was created.

## 16. Balance Disposition

Customer balance is unsupported in the verified backend Customer route set.

The unverified `balance` service method and service-local `CustomerBalance` interface were removed from the Customer service public surface.

No `CustomerBalance` shared type or response projection was created.

## 17. Other Unsupported Operations

The following unverified Customer service methods were removed from the public surface:

- `searchByPhone`
- `searchByNationalId`
- `statistics`
- `prescriptions`
- `loyalty`

No placeholder responses or empty values were fabricated.

## 18. Public Service Barrel

`frontend/src/services/customers/index.ts` now exports only:

```typescript
export { customerService } from "./customerService";
```

The barrel no longer re-exports `Customer`, `CreateCustomerRequest`, or `UpdateCustomerRequest`. Those remain owned by `src/types`.

The barrel does not expose BaseService or transport helpers.

## 19. Hooks Migrated

Updated:

- `useCustomers` now calls `customerService.listCustomers`
- `useCustomer` now calls `customerService.getCustomer`
- `useCreateCustomer` now calls `customerService.createCustomer`

Left unchanged because backend support is not verified:

- `useUpdateCustomer`
- `useDeleteCustomer`

Query keys and invalidation helpers were not modified.

## 20. Files Inspected

- `frontend/src/services/customers/customerService.ts`
- `frontend/src/services/customers/index.ts`
- `frontend/src/services/base/BaseService.ts`
- `frontend/src/hooks/queries/customers/`
- `frontend/src/lib/queryKeys.ts`
- `frontend/src/lib/queryInvalidation.ts`
- `frontend/src/types/api/`
- `frontend/src/types/entities/customer.ts`
- `frontend/src/types/requests/create-customer-request.ts`
- `frontend/src/types/requests/update-customer-request.ts`
- `frontend/docs/architecture/reviews/MIGRATION-014-CUSTOMER-TYPE-OWNERSHIP.md`
- `frontend/docs/architecture/reviews/MIGRATION-018-SUPPLIER-SERVICE-FACADE.md`
- `app/api/customers.py`
- `app/api/sales.py`
- `app/models/customer.py`

## 21. Files Created

- `frontend/docs/architecture/reviews/MIGRATION-020-CUSTOMER-SERVICE-FACADE.md`

## 22. Files Modified

- `frontend/src/services/customers/customerService.ts`
- `frontend/src/services/customers/index.ts`
- `frontend/src/hooks/queries/customers/useCustomers.ts`
- `frontend/src/hooks/queries/customers/useCustomer.ts`
- `frontend/src/hooks/queries/customers/useCreateCustomer.ts`

## 23. Compiler Errors Before

Baseline:

```text
195 TypeScript errors
```

Customer diagnostics before:

- `customerService.findById` did not exist.
- create hook expected `Customer` but received `ApiResponse<Customer>`.
- update hook expected `Customer` but received `ApiResponse<Customer>`.
- Customer list query key was called with params but accepted no arguments.
- delete hook used unsupported inherited hard-delete behavior.

## 24. Compiler Errors After

Post-migration:

```text
193 TypeScript errors
```

Net reduction:

```text
2
```

Resolved:

- missing `findById` diagnostic for `useCustomer`
- create response-envelope diagnostic for `useCreateCustomer`

## 25. Remaining Customer Diagnostics

Remaining:

```text
src/hooks/queries/customers/useCustomers.ts(63,31): error TS2554: Expected 0 arguments, but got 1.
src/hooks/queries/customers/useUpdateCustomer.ts(57,7): error TS2322: Type 'Promise<ApiResponse<Customer>>' is not assignable to type 'Promise<Customer>'.
```

The query-key issue is deferred by this migration.

The update issue remains because no backend Customer update route was verified and no facade method was fabricated.

`useDeleteCustomer` remains an unsupported runtime assumption but does not currently produce a TypeScript diagnostic.

## 26. Newly Exposed Query-Key Diagnostics

No newly exposed Customer query-key diagnostics were introduced.

The existing Customer list query-key mismatch remains unchanged.

## 27. New Diagnostics

No new diagnostics were introduced.

## 28. Remaining Customer Blockers

- Customer list query-key signature does not accept pagination params.
- No verified backend update route.
- No verified backend delete route.
- No verified backend deactivate/reactivate route.
- No verified Customer history endpoint.
- No verified Customer balance endpoint.
- Customer navigation ID backlog remains outside this migration.

## 29. Runtime Behavior Confirmation

Verified Customer list/get/create hooks now receive domain values from the Customer service facade.

Transport unwrapping occurs inside the service.

No backend behavior changed.

No query-key or invalidation behavior changed.

Unsupported update/delete runtime assumptions remain deferred rather than hidden behind invented facade methods.

## 30. Invariants Verified

- Customer exposes one public runtime service instance.
- Verified Customer facade methods use business-oriented names.
- Verified Customer hooks call the facade.
- Hooks do not unwrap Customer API envelopes.
- Transport unwrapping occurs in Customer service methods.
- No unsupported Customer update/delete/lifecycle method was invented.
- Customer type ownership remains under `src/types`.
- Customer service contains no React or TanStack Query logic.
- No query key was changed.
- No invalidation policy was changed.
- No backend file was changed.
- No unrelated domain was changed.

## 31. Rollback Boundary

Rollback is limited to:

- `frontend/src/services/customers/customerService.ts`
- `frontend/src/services/customers/index.ts`
- `frontend/src/hooks/queries/customers/useCustomers.ts`
- `frontend/src/hooks/queries/customers/useCustomer.ts`
- `frontend/src/hooks/queries/customers/useCreateCustomer.ts`
- `frontend/docs/architecture/reviews/MIGRATION-020-CUSTOMER-SERVICE-FACADE.md`

## 32. Recommended Next Migration

Recommended next migration:

```text
Migration 021 - Customer Query Key Boundary
```

Rationale:

The remaining safe Customer diagnostic is the list query-key signature mismatch, matching the Supplier query-key migration pattern from Migration 019.
