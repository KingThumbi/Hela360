# Migration 034 - Customer Update Backend Contract Disposition

## 1. Migration Purpose

Migration 034 determines the truthful disposition of the remaining Customer
update mutation.

This migration is inspection-first. Source changes were made only after the
backend Customer update contract was inspected and found unsupported.

## 2. ADR Rules Applied

- ADR-001: the Customer service facade exposes only verified backend-backed
  business operations.
- ADR-002: mutation hooks invoke services only for supported service operations
  and do not fabricate backend behavior.
- ADR-003: cache invalidation remains centralized and unchanged.
- ADR-004: Customer DTO ownership remains under `src/types`.
- ADR-005: unsupported local mutation behavior fails explicitly.
- ADR-008: the public Customer hook barrel exposes supported public contracts.
- ADR-009: capability names continue to use explicit business language.

## 3. Initial Customer Update Diagnostic

Frontend compiler baseline before this migration:

```text
100 TypeScript errors
```

Customer update diagnostic before:

```text
src/hooks/queries/customers/useUpdateCustomer.ts(57,7): error TS2322: Type 'Promise<ApiResponse<Customer>>' is not assignable to type 'Promise<Customer>'.
```

Diagnostic details:

- diagnostic code: `TS2322`
- expected mutation result type: `Promise<Customer>`
- actual mutation result type: `Promise<ApiResponse<Customer>>`
- expected mutation variable type:
  `UpdateEntityPayload<UpdateCustomerRequest>`
- actual service method called: inherited `customerService.update(id, data)`
- inherited BaseService involvement: confirmed
- other Customer update diagnostics: none found

The diagnostic was caused by `useUpdateCustomer` calling the inherited generic
`BaseService.update` method. That method uses an unverified `PUT` transport
path and returns a transport envelope instead of the Customer facade's
domain-level `Customer` return type.

## 4. Backend Customer Routes Inspected

Registered Customer API:

- `app/api/customers.py`
- registered in `app/__init__.py` with `url_prefix="/api"`

Confirmed routes:

| Capability | Route | Method | Permission | Envelope | Confidence |
| --- | --- | --- | --- | --- | --- |
| List | `/api/customers` | `GET` | `customers.view` | `{ ok, count, items }` | Confirmed |
| Detail | `/api/customers/<customer_id>` | `GET` | `customers.view` | `{ ok, item }` or `{ ok: false, error }` | Confirmed |
| Create | `/api/customers` | `POST` | `customers.create` | `{ ok, message, item }` | Confirmed |
| Update | none found | none found | none registered | none found | Unsupported |

Duplicated Customer route code also exists inside `app/api/sales.py`, but that
duplicate route set contains only list, detail, and create Customer operations.
No `PATCH`, `PUT`, delete, deactivate, or reactivate Customer route was found
there either.

## 5. Backend Update Search Result

Searched backend areas:

- `app/api/customers.py`
- `app/api/sales.py`
- `app/models/`
- `app/schemas/`
- `app/serializers/`
- `app/services/`
- `app/auth/`
- `migrations/`

Search terms included:

- `update_customer`
- `edit_customer`
- `patch_customer`
- `put_customer`
- `customer_update`
- `/customer/<id>`
- `/customers/<id>`
- `PATCH`
- `PUT`
- `is_active`
- `deactivate_customer`
- `reactivate_customer`
- `delete_customer`

No registered Customer update route was found.

## 6. Partial Backend Evidence

Partial evidence found:

- `app/auth/permissions.py` defines `CUSTOMERS_EDIT = "customers.edit"`.
- `app/models/customer.py` contains mutable Customer columns.
- `migrations/versions/19b1ccd035ac_initial_schema.py` creates those Customer
  columns.
- `app/services/tenant/customers/customer_service.py` exists but is empty.
- `app/services/tenant/customers/__init__.py` exists but is empty.

Classification:

```text
Partial evidence only
```

The permission constant and mutable model fields do not prove a registered
route, schema, service method, transaction, tenant guard, response envelope, or
test-backed update capability.

## 7. Update Schema Evidence

No backend Customer update schema was found under the inspected backend schema,
serializer, or service areas.

Frontend update request owner:

```text
frontend/src/types/requests/update-customer-request.ts
```

Frontend request shape:

```typescript
export type UpdateCustomerRequest =
  Partial<CreateCustomerRequest>;
```

Frontend fields inherited from `CreateCustomerRequest`:

- `customer_number`
- `first_name`
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

Backend-accepted update fields:

```text
none verified
```

Required versus optional update semantics:

```text
Unsupported
```

No backend evidence establishes partial update, full replacement semantics,
immutable update fields, server-owned update fields, lifecycle fields,
normalization, validation rules, response status codes, transaction behavior,
or test coverage for Customer update.

## 8. Capability Decision Matrix

| Capability | Backend support | Frontend hook | Facade method | Disposition |
| --- | --- | --- | --- | --- |
| Update | Unsupported | `useUpdateCustomer` existed | none | Unsupported and not publicly exposed |
| Delete | Unsupported by prior evidence | `useDeleteCustomer` exists | none | Deferred; not changed in this update-only migration |
| Deactivate | Unsupported | none | none | Deferred pending backend implementation |
| Reactivate | Unsupported | none | none | Deferred pending backend implementation |

## 9. `updateCustomer` Disposition

No `customerService.updateCustomer` facade method was added.

The Customer service facade continues to expose only verified backend
capabilities:

- `listCustomers`
- `getCustomer`
- `createCustomer`

The inherited generic `customerService.update` method is not a verified Customer
business facade method and is no longer called by `useUpdateCustomer`.

## 10. `useUpdateCustomer` Disposition

`useUpdateCustomer` was removed from the public Customer hook barrel:

```text
frontend/src/hooks/queries/customers/index.ts
```

The local hook file was preserved:

```text
frontend/src/hooks/queries/customers/useUpdateCustomer.ts
```

If deep-imported, it now rejects with a clear backend-support error instead of
issuing a speculative inherited `PUT /customers/<id>` request.

This follows the unsupported mutation disposition established in Migration 024.

## 11. Public Hook Boundary

The public Customer hook barrel now exposes:

- `useCustomers`
- `useCustomer`
- `useCreateCustomer`
- `useDeleteCustomer`

It no longer exposes:

- `useUpdateCustomer`

`useDeleteCustomer` was not changed in this migration because the requested
scope was Customer update disposition only and no compiler diagnostic originated
from Customer delete.

## 12. Files Changed

- `frontend/src/hooks/queries/customers/index.ts`
- `frontend/src/hooks/queries/customers/useUpdateCustomer.ts`
- `frontend/docs/architecture/reviews/MIGRATION-034-CUSTOMER-UPDATE-DISPOSITION.md`

## 13. Compiler Errors After

Frontend compiler count after this migration:

```text
99 TypeScript errors
```

Net reduction:

```text
1 error
```

Customer update diagnostics after:

```text
none
```

No new Customer update diagnostic was introduced.

## 14. Backend Files Unchanged Confirmation

No backend source files were modified.

Backend Customer update support remains absent from the registered Customer API.

## 15. Runtime Behavior Confirmation

No supported Customer runtime behavior changed.

Verified Customer list, detail, and create service/hook behavior is unchanged.
Customer query keys and cache invalidation policy are unchanged.

Unsupported local Customer update behavior now fails explicitly if deep-imported
instead of sending an unsupported request.

## 16. Remaining Customer Blockers

- Customer update requires a verified backend route, request schema, response
  envelope, permission, tenant behavior, transaction behavior, and tests before
  frontend support can be restored.
- Customer delete remains unsupported by backend evidence and is outside this
  migration's source-change scope.
- Customer lifecycle operations require verified backend deactivate/reactivate
  routes before frontend support can be added.

## 17. Rollback Boundary

Rollback is limited to:

- `frontend/src/hooks/queries/customers/index.ts`
- `frontend/src/hooks/queries/customers/useUpdateCustomer.ts`
- this review document

