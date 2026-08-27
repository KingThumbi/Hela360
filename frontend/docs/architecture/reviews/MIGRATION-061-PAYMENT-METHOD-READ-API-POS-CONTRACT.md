# Migration 061 - Payment Method Read API POS Contract

## 1. Purpose

Migration 061 establishes the canonical tenant-safe Payment Method read
contract required by future POS checkout payment selection.

This migration does not activate POS UI, Sales History, Refund UI, receipt UI,
Till/TillShift lifecycle, inventory, batch/expiry, or Product pricing work.

## 2. ADR Rules Applied

- ADR-001: frontend access is through a narrow service facade.
- ADR-002: server state is exposed through a query hook.
- ADR-003: the query key is centralized in `queryKeys.ts`.
- ADR-004: `PaymentMethod` is a canonical entity under `src/types/entities`.
- ADR-005: existing API error handling is preserved.
- ADR-006: tenant identity is backend-derived and query-cache-scoped by tenant.
- ADR-007: backend authorization remains the security boundary.
- ADR-008: no frontend feature module was activated.
- ADR-009: naming follows current repository conventions.

## 3. Starting Baseline

Commands:

```bash
venv/bin/python -m compileall app
cd frontend
npx tsc -b --pretty false
npm run build
```

Result:

```text
Backend compile: PASS
TypeScript errors: 0
Vite build: PASS
```

Existing Vite warning remains:

```text
Some chunks are larger than 500 kB after minification.
```

## 4. PaymentMethod Model

Model:

```text
app.models.pos.PaymentMethod
```

Table:

```text
payment_methods
```

Fields:

- `id`
- `tenant_id`
- `code`
- `name`
- `method_type`
- `is_active`
- `created_at`
- `updated_at`

## 5. Ownership

Payment Method ownership:

```text
tenant-owned
```

Evidence:

- `tenant_id` is non-nullable;
- `tenant_id` has a foreign key to `tenants.id`;
- no `branch_id` exists on `PaymentMethod`;
- checkout validates `PaymentMethod.tenant_id`.

Branch is intentionally excluded from the Payment Method query key.

## 6. Database Constraints

Model constraint:

```text
UniqueConstraint("tenant_id", "code", name="uq_payment_methods_tenant_code")
```

Implications:

- one tenant cannot have duplicate Payment Method codes;
- two different tenants may legitimately use the same code;
- `code`, `name`, `method_type`, and `is_active` are non-nullable;
- `is_active` defaults to true.

## 7. Checkout Validation

Checkout accepts payment method ids through:

```text
POST /api/sales/checkout
payments[].payment_method_id
```

Validation occurs in `app/api/sales.py`:

- `payment_method_id` is required for each payment;
- PaymentMethod is loaded by `id`;
- PaymentMethod is scoped by authenticated `tenant_id`;
- Migration 061 narrowed validation to active PaymentMethods only;
- payment `amount` must be positive;
- `reference` is optional;
- multiple payment methods can be used in one checkout.

## 8. Narrow Checkout Fix

Before Migration 061, checkout rejected nonexistent or cross-tenant payment
methods but accepted inactive tenant payment methods.

Migration 061 changed checkout validation to require:

```text
PaymentMethod.is_active == true
```

No other checkout behavior was redesigned.

## 9. Authorization Disposition

No verified backend `payment_methods.view` permission exists.

Frontend navigation contains `payment_methods.view`, but this is an
Administration/UI assumption and not a verified backend route permission.

For POS discovery, the read endpoint uses:

```text
sales.create
```

Rationale:

- the endpoint exists to supply IDs directly consumed by checkout;
- checkout itself is protected by `sales.create`;
- exposing active tenant tender IDs to a user who cannot create sales would not
  support the operational POS workflow.

## 10. Backend Service Owner

Canonical backend service:

```text
app/services/tenant/pos/payment_method_service.py
```

Public method:

```text
PaymentMethodService.list_active(tenant_id)
```

The API route remains thin and delegates retrieval to the service.

## 11. Endpoint

Canonical endpoint:

```text
GET /api/payment-methods
```

Registered route:

```text
payment_methods.list_payment_methods  GET  /api/payment-methods
```

Requirements satisfied:

- authenticated;
- authorized by `sales.create`;
- tenant derived from authenticated identity;
- no `tenant_id` request parameter;
- active records only;
- deterministic ordering;
- no mutation;
- no alias route.

## 12. Response Envelope

Shape:

```json
{
  "ok": true,
  "items": []
}
```

No pagination was added because Payment Methods are small tenant reference data.

## 13. Response Fields

Serializer:

```text
app/serializers/payment_method.py
```

Fields:

- `id`
- `code`
- `name`
- `method_type`
- `is_active`

`tenant_id`, timestamps, and internal audit fields are not exposed.

## 14. Ordering

Ordering:

```text
name ASC, code ASC, created_at ASC
```

No display-order field was introduced.

## 15. Tenant Isolation

Backend tests verify:

- Tenant A sees only Tenant A active methods;
- Tenant B methods are excluded;
- inactive methods are excluded;
- duplicate codes across tenants are allowed by model constraint and isolated
  by tenant scope.

## 16. Checkout Compatibility

Backend tests verify:

```text
ID returned by GET /api/payment-methods
→ accepted by checkout payment validation
```

The same backend-owned `PaymentMethod.id` is used by both the read endpoint and
checkout `payment_method_id`.

## 17. Backend Tests

Added:

```text
app/api/tests/test_payment_methods_contract.py
```

Coverage:

- authenticated active tenant list;
- unauthenticated request rejection;
- `sales.create` permission enforcement;
- tenant isolation;
- inactive exclusion;
- deterministic ordering;
- stable response envelope;
- required display/id fields;
- checkout compatibility;
- inactive checkout rejection.

## 18. Frontend Existing Contract Inventory

Pre-existing findings:

- Sales request DTO already used `payment_method_id`.
- `types/enums/payment-method.ts` exposed a string alias named
  `PaymentMethod`.
- `services/finance/paymentService.ts` contains a Finance-local
  `PaymentMethod` alias.
- frontend navigation references Administration payment method permissions, but
  no backend Administration Payment Method read API was verified.
- no POS page consumes Payment Methods yet.

Migration 061 renamed the old enum alias to `PaymentMethodCode` so the
canonical entity can own `PaymentMethod`.

The Finance service-local alias remains separate Finance cleanup debt.

## 19. Canonical Frontend Entity

Created:

```text
frontend/src/types/entities/payment-method.ts
```

Shape:

```typescript
interface PaymentMethod {
  id: string;
  code: string;
  name: string;
  method_type: string;
  is_active: boolean;
}
```

No `cash`, `mpesa`, `card`, or `bank` enum was created.

## 20. Frontend Service

Created:

```text
frontend/src/services/payment-methods/paymentMethodService.ts
```

Public method:

```text
listPaymentMethods()
```

The service:

- calls `API_ENDPOINTS.PAYMENT_METHODS.ROOT`;
- unwraps `{ ok, items }`;
- returns `PaymentMethod[]`;
- does not read auth state;
- does not build query keys;
- does not expose create/update/delete.

## 21. Frontend Hook

Created:

```text
frontend/src/hooks/queries/payment-methods/usePaymentMethods.ts
```

Behavior:

- uses `useQueryScope()`;
- waits for tenant readiness;
- uses the canonical tenant-scoped query key;
- calls `paymentMethodService.listPaymentMethods`;
- does not perform UI authorization;
- does not hardcode tender methods.

## 22. Query Key

Added:

```text
QUERY_KEYS.paymentMethods
```

Active list key:

```text
["tenant", tenantId, "payment-methods", "list"]
```

Disabled sentinel:

```text
["identity", "disabled", "payment-methods", "list"]
```

Branch id is not included because Payment Methods are tenant-owned.

## 23. Invalidation Disposition

No invalidation was added.

Payment Methods are read-only in Migration 061, and no verified mutation exists
in this scope. POS checkout should not invalidate Payment Methods.

## 24. Real DB Readiness

Read-only count attempted:

```text
payment_methods total
payment_methods active
```

Result:

```text
BLOCKED - PostgreSQL 16/main down, localhost:5432 no response.
```

No seed command was run.

## 25. First-Tenant Readiness

Classification:

```text
Unknown
```

The endpoint and contract are ready, but live first-tenant Payment Method
counts could not be inspected from this shell.

The first live tenant still needs active tender methods appropriate to the
branch's operations.

## 26. Verification

Backend:

```bash
venv/bin/python -m compileall app
venv/bin/python -m pytest app/api/tests/test_payment_methods_contract.py -q
venv/bin/python -m pytest app/api/tests/test_payment_methods_contract.py app/api/tests/test_sales_pos_contract.py app/api/tests/test_customers_contract.py app/api/tests/test_products_list_contract.py app/services/tenant/procurement/tests/test_supplier_contract.py app/services/tenant/auth/tests/test_current_session_service.py app/services/tenant/auth/tests/test_current_session_route.py -q
venv/bin/python -m pytest app/services/tenant/auth/tests -q
```

Results:

```text
Payment Method contract: 5 passed
Targeted regression: 46 passed
Auth suite: 129 passed
Backend compile: PASS
```

Frontend:

```bash
npx tsc -b --pretty false
npm run build
```

Results:

```text
TypeScript errors: 0
Vite build: PASS
```

## 27. Static Verification

Static searches verified:

- canonical entity: `frontend/src/types/entities/payment-method.ts`;
- canonical service: `frontend/src/services/payment-methods/paymentMethodService.ts`;
- canonical hook: `frontend/src/hooks/queries/payment-methods/usePaymentMethods.ts`;
- tenant-scoped key: `QUERY_KEYS.paymentMethods`;
- no POS payment options hardcoded in `frontend/src/features/sales`;
- no POS UI activation.

## 28. Files Inspected

- ADR-001 through ADR-009
- Migration 048, 049, 052, 058, 060 reports
- `app/models/pos.py`
- `app/api/sales.py`
- `app/auth/permissions.py`
- `app/__init__.py`
- `frontend/src/api/endpoints.ts`
- `frontend/src/types/entities/`
- `frontend/src/types/enums/payment-method.ts`
- `frontend/src/services/`
- `frontend/src/hooks/queries/`
- `frontend/src/lib/queryKeys.ts`
- `frontend/src/features/sales/`

## 29. Files Created

- `app/api/payment_methods.py`
- `app/api/tests/test_payment_methods_contract.py`
- `app/serializers/payment_method.py`
- `app/services/tenant/pos/payment_method_service.py`
- `frontend/src/types/entities/payment-method.ts`
- `frontend/src/services/payment-methods/paymentMethodService.ts`
- `frontend/src/services/payment-methods/index.ts`
- `frontend/src/hooks/queries/payment-methods/usePaymentMethods.ts`
- `frontend/src/hooks/queries/payment-methods/index.ts`
- `frontend/docs/architecture/reviews/MIGRATION-061-PAYMENT-METHOD-READ-API-POS-CONTRACT.md`

## 30. Files Modified

- `app/__init__.py`
- `app/api/sales.py`
- `app/serializers/__init__.py`
- `app/services/tenant/pos/__init__.py`
- `frontend/src/api/endpoints.ts`
- `frontend/src/lib/queryKeys.ts`
- `frontend/src/types/entities/index.ts`
- `frontend/src/types/enums/payment-method.ts`
- `frontend/src/types/enums/index.ts`
- `frontend/src/types/sales/enums.ts`
- `frontend/src/types/sales/index.ts`

## 31. Runtime Behavior Confirmation

Confirmed:

- `GET /api/payment-methods` is registered;
- endpoint returns active tenant records only;
- endpoint returns IDs checkout accepts;
- inactive PaymentMethods are rejected by checkout validation;
- frontend has a tenant-scoped hook ready for future POS selector use.

## 32. Remaining POS Blockers

Still blocked from Migration 060:

- Till/TillShift lifecycle;
- active branch requirement in POS UI;
- Product price authority;
- Product active/prescription enforcement;
- batch/expiry stock handling;
- receipt API;
- Sales read/history API;
- refund stock-balance restoration.

## 33. Architecture Invariants

- Payment Methods remain backend-owned reference data.
- Tenant is derived from authenticated identity.
- Client cannot select another tenant's Payment Methods.
- POS read contract returns active methods only.
- Checkout uses the same PaymentMethod IDs.
- No tender method is hardcoded in POS UI.
- Frontend service remains transport-only.
- Frontend query is tenant-scoped.
- Branch is excluded because PaymentMethod is tenant-owned.
- No Payment Method mutation API was fabricated.
- No POS page was activated.
- No Till/TillShift work was mixed in.
- No Inventory work was mixed in.
- TypeScript remains at zero errors.
- Production build remains successful.

## 34. Rollback Boundary

Rollback is limited to:

- unregister/remove `app/api/payment_methods.py`;
- remove `PaymentMethodService` and serializer;
- revert checkout active PaymentMethod validation;
- remove Payment Method frontend type/service/hook/query-key additions;
- remove this report.

No database migration was introduced.

## 35. Recommended Next Migration

Recommended next migration:

```text
Migration 062 - Till And TillShift Read/Lifecycle Contract
```

That migration should resolve how a cashier discovers tills and opens/closes the
shift required by checkout, without yet activating the full POS page.
