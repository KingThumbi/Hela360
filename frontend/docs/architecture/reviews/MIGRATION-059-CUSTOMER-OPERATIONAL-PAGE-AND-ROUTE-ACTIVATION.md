# Migration 059 - Customer Operational Page And Route Activation

## 1. Purpose

Migration 059 activates the Customer operational slice after the local runtime
foundation was verified in Migration 058.

The migration follows the proven Supplier/Product vertical-slice pattern:

- canonical backend `Customer` entity;
- canonical frontend `Customer` entity contract;
- `customerService`;
- tenant-scoped `useCustomers`, `useCustomer`, and `useCreateCustomer`;
- `customers.view` route protection;
- server-backed search and pagination;
- operational list, detail, and create UI states.

No fabricated update/delete UI was added because the backend Customer API does
not expose verified update or delete routes.

## 2. Backend Contract

Updated:

- `app/api/customers.py`

The Customer list endpoint remains tenant-scoped and now applies the same
server-backed pagination contract used by the Product list endpoint:

- positive `page`;
- positive `per_page`;
- filtered tenant-scoped `count`;
- ordered page window;
- unchanged response envelope: `{ ok, count, items }`.

Existing supported operations:

- `GET /customers`
- `GET /customers/<customer_id>`
- `POST /customers`

Unsupported operations intentionally remain unsupported:

- update;
- delete;
- deactivate/reactivate lifecycle.

## 3. Frontend Activation

Added:

- `frontend/src/features/customers/index.ts`
- `frontend/src/features/customers/components/CustomersTable.tsx`
- `frontend/src/features/customers/components/CustomerDetailDialog.tsx`
- `frontend/src/features/customers/components/CustomerFormDialog.tsx`
- `frontend/src/validation/customerSchema.ts`

Updated:

- `frontend/src/features/customers/pages/CustomersPage.tsx`
- `frontend/src/app/router.tsx`

The `/customers` route now renders `CustomersPage` behind the existing
`customers.view` route permission requirement.

## 4. Customer Page Capabilities

The activated page provides:

- loading state;
- error state with retry;
- empty state;
- search-empty state;
- server-backed pagination controls;
- refresh action;
- permission-gated create action;
- customer table;
- detail dialog backed by `useCustomer`;
- create dialog backed by `useCreateCustomer`.

The table exposes only a view action. No edit, delete, deactivate, or
reactivate actions are rendered.

## 5. Customer Create Surface

The create dialog supports the verified backend create payload:

- `customer_number` optional;
- `first_name` required;
- `last_name`;
- `other_names`;
- `phone`;
- `email`;
- `gender`;
- `date_of_birth`;
- `id_number`;
- `address`;
- `city`.

If `customer_number` is omitted, the backend generates it.

## 6. Contract Tests

Added:

- `app/api/tests/test_customers_contract.py`

Coverage:

- empty list envelope;
- tenant-scoped list serialization;
- tenant-scoped search;
- search across supported fields;
- server-backed pagination;
- invalid pagination rejection;
- tenant-scoped detail lookup;
- create uses authenticated tenant;
- create accepts ISO `date_of_birth`;
- invalid `date_of_birth` rejection;
- duplicate phone rejection;
- missing permission rejection.

## 7. Verification

Backend compile:

```bash
venv/bin/python -m compileall app
```

Result:

```text
PASS
```

Targeted regression:

```bash
venv/bin/python -m pytest \
  app/services/tenant/auth/tests/test_current_session_service.py \
  app/services/tenant/auth/tests/test_current_session_route.py \
  app/api/tests/test_products_list_contract.py \
  app/services/tenant/procurement/tests/test_supplier_contract.py \
  app/api/tests/test_customers_contract.py \
  -q
```

Result:

```text
38 passed
```

Auth suite:

```bash
venv/bin/python -m pytest app/services/tenant/auth/tests -q
```

Result:

```text
129 passed
```

Frontend type check:

```bash
cd frontend
npx tsc -b --pretty false
```

Result:

```text
PASS
```

Frontend production build:

```bash
cd frontend
npm run build
```

Result:

```text
PASS
```

Existing warning remains:

```text
Some chunks are larger than 500 kB after minification.
```

## 8. Remaining Technical Debt

Existing SQLAlchemy mapper overlap warnings were observed and not fixed:

- `RolePermission.role`
- `RolePermission.permission`
- `UserRole.user`
- `UserRole.role`

These remain a separate model-relationship cleanup concern and do not block
Customer activation.

## 9. Next Direction

After Customer activation, the next architecture slice should move into the
Sales/POS operational path, followed by the Inventory backend/API layer needed
for pharmacy stock, batches, expiry, receiving, stock counts, adjustments, and
sale-stock integration.
