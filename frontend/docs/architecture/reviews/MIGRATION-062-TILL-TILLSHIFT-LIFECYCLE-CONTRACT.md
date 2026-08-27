# Migration 062 - Till and TillShift Lifecycle Contract

## 1. Purpose

Migration 062 establishes the backend contract and frontend foundations required
for cashier till operation before POS page activation.

Implemented flow:

```text
authenticated user -> selected branch -> active branch tills -> open TillShift
-> checkout validates open TillShift -> close TillShift -> reconciliation
```

This migration does not activate the POS frontend page, receipt functionality,
inventory batch/expiry handling, Sales checkout redesign, or a `Shift` /
`TillShift` merge.

## 2. ADR Rules Applied

- ADR-001: lifecycle logic lives in a POS service, not in route handlers.
- ADR-004: reusable frontend Till and TillShift contracts live under
  `src/types`.
- ADR-005: domain errors use the centralized API error handler.
- ADR-006: tenant and branch scope are server-derived from authenticated
  identity and branch-scoped in frontend query keys.
- ADR-007: endpoints use verified `sales.create` POS authorization.
- ADR-008: no POS feature page, route, navigation item, or checkout UI was
  activated.
- ADR-009: names use canonical Till/TillShift terminology.

## 3. Starting Baseline

Baseline before implementation:

```text
venv/bin/python -m compileall app: PASS
npx tsc -b --pretty false: PASS
npm run build: PASS
```

The existing Vite large-chunk warning was present and not addressed.

## 4. Till Model

Model: `app.models.pos.Till`

Table: `tills`

Fields:

- `id`
- `tenant_id`
- `branch_id`
- `code`
- `name`
- `is_active`
- `created_at`
- `updated_at`

No `warehouse_id` field exists on Till.

## 5. Till Ownership

Till is tenant + branch owned.

Evidence:

- `tenant_id` is non-nullable and indexed.
- `branch_id` is non-nullable and indexed.
- uniqueness is scoped to tenant + branch + code.

## 6. Till Constraints

Constraint:

```text
uq_tills_tenant_branch_code
```

Implications:

- multiple tills may exist in the same branch if codes differ;
- the same code may exist in another branch or tenant;
- `is_active` is the operational availability flag;
- no warehouse association exists;
- no cashier/user assignment exists on Till.

## 7. TillShift Model

Model: `app.models.shift.TillShift`

Table: `till_shifts`

Fields:

- `id`
- `tenant_id`
- `branch_id`
- `till_id`
- `cashier_id`
- `status`
- `opening_float`
- `closing_cash`
- `notes`
- `opened_at`
- `closed_at`
- `created_at`
- `updated_at`

Absent persistent fields:

- `opening_cash`
- `user_id`
- `expected_cash`
- `cash_difference`

## 8. TillShift Ownership

TillShift is tenant + branch + till + cashier owned.

The model uses `db.UUID(as_uuid=True)` columns for TillShift identifiers. The
surrounding core models use string UUID primary keys, so the service normalizes
string UUIDs to UUID values at the TillShift boundary.

## 9. Shift Model Disposition

Model: `app.models.pos.Shift`

Table: `shifts`

Fields:

- `id`
- `tenant_id`
- `branch_id`
- `till_id`
- `opened_by`
- `opened_at`
- `opening_float`
- `closed_by`
- `closed_at`
- `closing_cash_expected`
- `closing_cash_counted`
- `variance_amount`
- `status`
- `created_at`
- `updated_at`

`Shift` remains separate persistence. It overlaps conceptually with TillShift,
but checkout currently uses TillShift. Migration 062 did not merge, delete, or
reinterpret `Shift`.

## 10. Canonical POS Shift Owner

Canonical POS lifecycle owner for this migration:

```text
TillShift
```

Reason: registered checkout already requires an open `TillShift` and returns
the active `TillShift.id` as `shift_id` in the checkout response.

## 11. Sale Linkage

`Sale` stores:

- `tenant_id`
- `branch_id`
- `till_id`
- `shift_id`
- `warehouse_id`
- `cashier_id`

`Sale.shift_id` references `shifts.id`, not `till_shifts.id`.

Current classification:

```text
POS control gap
```

Checkout can verify an open TillShift, but the Sale row cannot be directly
attributed to the exact TillShift without a future schema migration. Migration
062 does not alter Sale schema.

## 12. Authorization Matrix

No verified `tills.*`, `till_shifts.*`, or `pos.*` backend permission exists.

Implemented permission:

| Operation | Permission |
| --- | --- |
| view active branch tills | `sales.create` |
| view current TillShift | `sales.create` |
| open TillShift | `sales.create` |
| close TillShift | `sales.create` |

Rationale: these endpoints exist to support POS checkout, which is already
protected by `sales.create`.

## 13. Branch Context

Tenant, branch, and cashier are derived from authenticated identity. The
frontend already attaches `X-Branch-ID` through the centralized interceptor,
and hooks derive branch query scope from `useQueryScope()`.

The backend rejects lifecycle operations when authenticated branch context is
missing.

## 14. Till Read Endpoint

Registered endpoint:

```text
GET /api/tills
```

Behavior:

- authenticated;
- authorized by `sales.create`;
- tenant derived server-side;
- branch derived server-side;
- active tills only;
- deterministic order by code, name, created_at;
- no mutation;
- no cross-branch leakage.

## 15. Till Response

Response envelope:

```json
{
  "ok": true,
  "items": []
}
```

Item fields:

- `id`
- `branch_id`
- `code`
- `name`
- `is_active`

`warehouse_id` is absent because the model has no warehouse field.

## 16. Current Shift Endpoint

Registered endpoint:

```text
GET /api/till-shifts/current
```

Optional query parameter:

```text
till_id
```

Returns the current open TillShift for the authenticated cashier in the current
branch, or `item: null` when no open shift exists.

## 17. Open Request

Request shape:

```json
{
  "till_id": "...",
  "opening_float": "0.00",
  "notes": null
}
```

Tenant, branch, and cashier are not accepted from the client.

## 18. Open Rules

Implemented rules:

- branch context is required;
- Till must exist;
- Till must belong to authenticated tenant;
- Till must belong to authenticated branch;
- Till must be active;
- opening float must be a valid non-negative money value;
- one open TillShift per till in the current branch;
- one open TillShift per cashier in the current branch.

## 19. Open Endpoint

Registered endpoint:

```text
POST /api/till-shifts/open
```

The route is thin and delegates lifecycle behavior to
`TillShiftService.open_shift()`.

## 20. Close Request

Request shape:

```json
{
  "closing_cash": "0.00",
  "notes": null
}
```

`expected_cash` and `cash_difference` are not accepted from the client.

## 21. Reconciliation Authority

The backend can calculate a partial cash reconciliation:

```text
opening_float + cash SalePayment total during shift window = expected_cash
closing_cash - expected_cash = cash_difference
```

The calculation joins `SalePayment`, `Sale`, and `PaymentMethod` where:

- Sale matches tenant, branch, till, and cashier;
- SalePayment is between `opened_at` and server close time;
- PaymentMethod belongs to tenant;
- PaymentMethod `method_type` is `cash`.

Because Sale lacks a direct `till_shift_id`, reconciliation is attribution by
tenant/branch/till/cashier/time window rather than direct shift foreign key.

## 22. Close Endpoint

Registered endpoint:

```text
POST /api/till-shifts/<shift_id>/close
```

Behavior:

- authenticated;
- authorized by `sales.create`;
- tenant, branch, cashier isolated;
- shift must exist and be open;
- repeated close is rejected;
- closing timestamp is server-owned;
- reconciliation is server-derived.

## 23. TillShift Response

Item fields:

- `id`
- `branch_id`
- `till_id`
- `cashier_id`
- `status`
- `opening_float`
- `closing_cash`
- `notes`
- `opened_at`
- `closed_at`
- `created_at`
- `updated_at`

Close responses additionally include:

- `reconciliation.opening_float`
- `reconciliation.cash_sales_total`
- `reconciliation.expected_cash`
- `reconciliation.closing_cash`
- `reconciliation.cash_difference`

## 24. Checkout Validation

Checkout validation was narrowed to require:

- active Till exists;
- Till belongs to authenticated tenant;
- Till belongs to authenticated branch;
- TillShift exists;
- TillShift belongs to authenticated tenant;
- TillShift belongs to authenticated branch;
- TillShift belongs to authenticated till;
- TillShift belongs to authenticated cashier;
- TillShift status is `open`;
- TillShift `closed_at` is null.

Checkout payload shape was not redesigned.

## 25. Mandatory Branch Behavior

Checkout already rejected missing authenticated branch context. Migration 062
keeps that requirement and adds branch matching for Till and Warehouse.

## 26. Till Concurrency

Multiple tills per branch are supported by the Till uniqueness constraint:

```text
tenant_id + branch_id + code
```

Migration 062 permits concurrent operation across different tills.

## 27. Cashier Concurrency

Implemented rule:

```text
one open TillShift per cashier per branch
```

This was present as lifecycle intent in dormant `app/api_sales.py` and matches
the need for a cashier's single active POS session.

## 28. Frontend Type Ownership

Created canonical entities:

- `frontend/src/types/entities/till.ts`
- `frontend/src/types/entities/till-shift.ts`

Created request DTOs:

- `OpenTillShiftRequest`
- `CloseTillShiftRequest`

No ambiguous frontend `Shift` type was reused for TillShift.

## 29. Frontend Services

Created service facades:

- `tillService.listTills()`
- `tillShiftService.getCurrent()`
- `tillShiftService.open(payload)`
- `tillShiftService.close(id, payload)`

Services remain tenant/branch transport agnostic.

## 30. Frontend Hooks

Created foundation-only hooks:

- `useTills`
- `useCurrentTillShift`
- `useOpenTillShift`
- `useCloseTillShift`

No POS UI was activated.

## 31. Branch Query Keys

Query key shapes:

```text
["tenant", tenantId, "branch", branchId, "tills", "list"]
["tenant", tenantId, "branch", branchId, "till-shifts", "current"]
```

Disabled keys use the identity-disabled namespace.

## 32. Invalidation

Opening and closing TillShift invalidates:

```text
QUERY_KEYS.tillShifts.root(branchScope)
```

Till list is not invalidated because open-shift state is not embedded in Till
responses.

## 33. Real DB Counts

PostgreSQL was not reachable from this Codex shell:

```text
16/main down
localhost:5432 - no response
```

Read-only counts for tills, till_shifts, shifts, branches, and warehouses were
not executed.

## 34. First-Tenant Readiness

Classification from this shell:

```text
Unknown
```

Minimum pre-POS configuration remains:

- active tenant;
- active branch;
- active warehouse for checkout;
- active Till;
- cashier user with `sales.create`;
- open TillShift;
- active payment methods;
- sellable products;
- stock balances.

No seed data was executed.

## 35. Tests Added

Added:

```text
app/api/tests/test_till_shift_contract.py
```

Coverage includes:

- authentication required;
- permission required;
- branch context required;
- active current-branch Till listing;
- inactive and cross-branch Till rejection;
- open TillShift success;
- conflicting open shift rejection;
- opening cash validation;
- current open TillShift;
- no open shift response;
- close TillShift success;
- repeated close rejection;
- cross-branch close isolation;
- reconciliation calculation;
- checkout rejection for closed TillShift;
- checkout acceptance for valid open TillShift.

## 36. Test Results

Targeted current-session/Product/Supplier/Customer/Sales/Payment Method/Till
bundle:

```text
62 passed, 4 warnings
```

Auth suite:

```text
129 passed
```

## 37. Backend Compile

```text
venv/bin/python -m compileall app: PASS
```

## 38. Frontend TypeScript

```text
npx tsc -b --pretty false: PASS
```

## 39. Frontend Build

```text
npm run build: PASS
```

Known warning:

```text
Some chunks are larger than 500 kB after minification.
```

## 40. Warnings

Existing SQLAlchemy mapper overlap warnings remain:

- `RolePermission.role`
- `RolePermission.permission`
- `UserRole.user`
- `UserRole.role`

These are not blocking this migration and were not fixed.

## 41. Source Files Inspected

- `app/models/pos.py`
- `app/models/shift.py`
- `app/api/sales.py`
- `app/api_sales.py`
- `app/auth/permissions.py`
- `app/services/tenant/auth/decorators.py`
- `frontend/src/api/interceptors.ts`
- `frontend/src/lib/queryScope.ts`
- `frontend/src/hooks/useQueryScope.ts`
- `frontend/src/lib/queryKeys.ts`

## 42. Source Files Created

- `app/api/tills.py`
- `app/api/tests/test_till_shift_contract.py`
- `app/serializers/till.py`
- `app/serializers/till_shift.py`
- `app/services/tenant/pos/till_shift_service.py`
- `frontend/src/types/entities/till.ts`
- `frontend/src/types/entities/till-shift.ts`
- `frontend/src/types/requests/till-shift-request.ts`
- `frontend/src/services/tills/tillService.ts`
- `frontend/src/services/tills/tillShiftService.ts`
- `frontend/src/services/tills/index.ts`
- `frontend/src/hooks/queries/tills/useTills.ts`
- `frontend/src/hooks/queries/tills/useCurrentTillShift.ts`
- `frontend/src/hooks/queries/tills/useOpenTillShift.ts`
- `frontend/src/hooks/queries/tills/useCloseTillShift.ts`
- `frontend/src/hooks/queries/tills/index.ts`

## 43. Source Files Modified

- `app/__init__.py`
- `app/api/errors.py`
- `app/api/sales.py`
- `app/serializers/__init__.py`
- `app/services/tenant/pos/__init__.py`
- `frontend/src/api/endpoints.ts`
- `frontend/src/lib/queryKeys.ts`
- `frontend/src/lib/queryInvalidation.ts`
- `frontend/src/types/entities/index.ts`
- `frontend/src/types/requests/index.ts`
- `frontend/src/services/index.ts`
- `frontend/src/hooks/queries/index.ts`

## 44. Remaining POS Blockers

- Sale lacks direct `till_shift_id`.
- `Shift` and `TillShift` overlap conceptually.
- Real database Till/TillShift readiness could not be verified from this shell.
- POS UI remains inactive.
- Inventory batch/expiry and sale-stock integration remain future work.
- Existing SQLAlchemy mapper overlap warnings remain separate technical debt.

## 45. Invariants Verified

- Till is tenant + branch scoped.
- TillShift is the operational POS shift owner for checkout.
- Legacy `Shift` remains separate.
- Tenant, branch, and cashier are server-derived.
- Client cannot operate another branch's Till.
- Inactive Till cannot start a shift.
- Checkout cannot use a closed or invalid TillShift.
- TillShift status and timestamps are server-owned.
- Cash reconciliation is server-derived where current schema permits.
- Frontend Till/TillShift cache is branch-scoped.
- No POS UI is activated.
- No Inventory/batch work was mixed in.
- TypeScript remains at zero errors.
- Production frontend build remains successful.

## 46. Rollback Boundary

Rollback is limited to the new Till/TillShift route, service, serializer, tests,
frontend type/service/hook foundation, query key additions, and the narrow
checkout validation changes. No database schema migration was introduced.

## 47. Recommended Next Migration

Recommended next migration:

```text
Migration 063 - POS Checkout UI Foundation Against Verified Backend Contracts
```

Prerequisite decision before full activation: whether to add a direct
`sales.till_shift_id` foreign key or otherwise formalize Sale-to-TillShift
attribution.
