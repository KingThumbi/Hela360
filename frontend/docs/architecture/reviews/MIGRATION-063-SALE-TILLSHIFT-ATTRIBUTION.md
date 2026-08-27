# Migration 063 - Sale TillShift Attribution

## 1. Purpose

Migration 063 makes new POS Sales directly attributable to the verified
TillShift used during checkout.

Target traceability after this migration:

```text
Sale -> tenant -> branch -> cashier -> Till -> TillShift -> SalePayment
```

This migration does not activate POS UI, change price override policy, implement
batch/expiry stock behavior, redesign TillShift, or merge legacy `Shift` with
`TillShift`.

## 2. ADR Rules Applied

- ADR-001: runtime behavior remains behind backend services and route
  boundaries.
- ADR-004: frontend Sale entity was aligned with the backend serializer.
- ADR-005: existing error handling behavior was preserved.
- ADR-006: tenant and branch isolation remain server-enforced.
- ADR-007: checkout authorization remains `sales.create`.
- ADR-008: no frontend feature page, route, or navigation activation was added.
- ADR-009: field naming uses explicit `till_shift_id`.
- ADR-010: checkout remains a backend workflow and persists the business fact
  created by that workflow.

## 3. Starting Baseline

Baseline commands:

```text
venv/bin/python -m compileall app: PASS
npx tsc -b --pretty false: PASS
npm run build: PASS
```

Existing Vite warning remains:

```text
Some chunks are larger than 500 kB after minification.
```

## 4. Sale Model Before

Before Migration 063, `Sale` fields included:

- `tenant_id`
- `branch_id`
- `till_id`
- `shift_id`
- `warehouse_id`
- `customer_id`
- `sale_number`
- `sale_date`
- `cashier_id`

`till_shift_id` was absent.

`shift_id` remains a reference to legacy `shifts.id`, not `till_shifts.id`.

## 5. Checkout TillShift Contract

Checkout request fields related to POS attribution:

- `warehouse_id`
- `till_id`

Server-derived attribution:

- tenant from authenticated identity;
- branch from authenticated identity;
- cashier from authenticated identity;
- TillShift from validated open-shift lookup.

The client does not send `till_shift_id`.

## 6. Canonical Attribution Decision

Canonical field:

```text
Sale.till_shift_id
```

Foreign key target:

```text
till_shifts.id
```

`Sale.till_id` is retained because it already exists and remains useful for
reporting and current checkout flow. Checkout persists both from the same
validated Till/TillShift contract.

## 7. New Model Field

Added to `app.models.pos.Sale`:

```text
till_shift_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("till_shifts.id"), index=True)
```

No SQLAlchemy relationship was added. The existing model style is column-first,
and avoiding new relationship overlap warnings was part of this migration's
safety boundary.

## 8. FK And Index Design

Alembic adds:

- nullable `sales.till_shift_id`;
- index `ix_sales_till_shift_id`;
- FK `fk_sales_till_shift_id_till_shifts` to `till_shifts.id`.

No on-delete override was added; the default database behavior prevents
deleting a TillShift that has attributed Sales.

## 9. Nullability

Database nullability:

```text
nullable=True
```

Runtime checkout requirement:

```text
new POS checkout Sales must persist a verified TillShift ID
```

This keeps historical Sales valid while tightening new POS writes.

## 10. Historical Sale Disposition

Historical Sales with null `till_shift_id` are classified as:

```text
legacy/unattributed
```

Migration 063 does not backfill from timestamps, does not create synthetic
TillShifts, and does not guess links.

## 11. Alembic Migration

Created:

```text
migrations/versions/2f4a8b9c1d3e_add_sale_till_shift_attribution.py
```

Revision:

```text
2f4a8b9c1d3e
```

Down revision:

```text
8f3b7c2a9d10
```

`venv/bin/python -m py_compile` passed for the migration file.

## 12. Relationship Ownership

No `Sale.till_shift` or `TillShift.sales` relationship was introduced.

Reason:

- current model ownership is mostly explicit FK columns;
- adding bidirectional relationships is not required for runtime attribution;
- no new mapper overlap warnings should be introduced in this migration.

## 13. Checkout Persistence

Checkout now sets:

```text
sale.till_shift_id = active_shift.id
```

The value comes from the already verified TillShift object returned by
`_require_open_shift()`.

The route does not trust a raw client-supplied `till_shift_id`.

## 14. Serializer Change

`serialize_sale()` now returns:

```text
till_shift_id
```

No nested TillShift object is embedded.

The checkout response still includes the existing top-level `shift_id` response
field for compatibility, but the serialized Sale item now carries canonical
`till_shift_id`.

## 15. Frontend Sale Entity Alignment

Updated:

```text
frontend/src/types/entities/sale.ts
```

Added:

```text
till_shift_id: string | null
```

No Sales query keys, hooks, or POS UI behavior were added.

## 16. Request DTO Disposition

`CreateSaleRequest` remains unchanged.

Reason:

- the verified checkout payload sends `till_id`;
- TillShift is server-derived from authenticated tenant, branch, cashier, and
  Till;
- adding client-supplied `till_shift_id` would create an unnecessary spoofing
  surface.

## 17. Reconciliation Before

Migration 062 reconciliation inferred shift cash totals by:

```text
tenant + branch + till + cashier + SalePayment time window
```

This could contaminate overlapping shifts or ambiguous historical data.

## 18. Reconciliation After

Migration 063 reconciliation uses direct attribution:

```text
Sale.till_shift_id == current TillShift.id
```

Only attributed Sales contribute to cash totals.

## 19. Historical Reconciliation Behavior

Sales with null `till_shift_id` do not contribute to direct TillShift
reconciliation.

This avoids silently mixing unrelated historical Sales into a close summary.

## 20. Payment Reconciliation

Cash reconciliation joins:

```text
Sale -> SalePayment -> PaymentMethod
```

Included payments must satisfy:

- Sale is attributed to the closing TillShift;
- PaymentMethod belongs to the tenant;
- PaymentMethod `method_type` is `cash`.

PaymentMethod IDs are not hardcoded.

## 21. Refund Reconciliation Limitation

Refund models currently have sale, branch, till, and cashier attribution, but no
direct TillShift or payment-return shift attribution.

Migration 063 does not invent refund-shift linkage. Refund reconciliation
impact remains a future POS control concern.

## 22. Cashier Attribution

TillShift stores `cashier_id`.

Checkout requires the authenticated user to match:

```text
TillShift.cashier_id
```

No supervisor override policy was introduced.

## 23. Tenant Isolation

Checkout only finds open shifts matching authenticated tenant:

```text
TillShift.tenant_id == identity.tenant_id
```

Tests verify that an open shift from another tenant does not create a Sale.

## 24. Branch Isolation

Checkout only finds open shifts matching authenticated branch:

```text
TillShift.branch_id == identity.branch_id
```

Tests verify that an open shift from another branch does not create a Sale.

## 25. Closed-Shift Validation

Checkout requires:

```text
TillShift.status == "open"
TillShift.closed_at is null
```

Tests verify a closed TillShift is rejected and no Sale is created.

## 26. Wrong-Till Validation

Checkout requires:

```text
TillShift.till_id == request.till_id
```

Tests verify an open TillShift for a different Till does not satisfy checkout.

## 27. Tests Added

Expanded:

```text
app/api/tests/test_till_shift_contract.py
```

Added/updated coverage:

- valid checkout persists `Sale.till_shift_id`;
- checkout response item exposes `till_shift_id`;
- cross-tenant TillShift rejected;
- cross-branch TillShift rejected;
- closed TillShift rejected;
- mismatched Till rejected;
- Sale retains correct branch;
- Sale retains correct cashier;
- Sale retains correct Till;
- reconciliation includes only Sales attributed to the closing TillShift;
- overlapping same-time shift Sales do not contaminate totals;
- non-cash payments are excluded from cash reconciliation.

## 28. Test Results

Focused Till/TillShift contract:

```text
19 passed, 4 warnings
```

Targeted backend regression:

```text
65 passed, 4 warnings
```

Auth suite:

```text
129 passed
```

## 29. Migration Application Result

Repository Alembic head:

```text
2f4a8b9c1d3e (head)
```

Local PostgreSQL state from this shell:

```text
16/main down
localhost:5432 - no response
```

`flask db current` could not connect. The migration was not applied to the
local PostgreSQL database from this shell.

## 30. Backend Compile

```text
venv/bin/python -m compileall app: PASS
```

## 31. Frontend TypeScript

```text
npx tsc -b --pretty false: PASS
```

## 32. Frontend Build

```text
npm run build: PASS
```

Known warning:

```text
Some chunks are larger than 500 kB after minification.
```

## 33. Warnings

Existing SQLAlchemy mapper overlap warnings remain:

- `RolePermission.role`
- `RolePermission.permission`
- `UserRole.user`
- `UserRole.role`

They were not modified in this migration.

## 34. Source Files Inspected

- `app/models/pos.py`
- `app/models/shift.py`
- `app/api/sales.py`
- `app/services/tenant/pos/till_shift_service.py`
- `frontend/src/types/entities/sale.ts`
- `frontend/src/types/requests/create-sale-request.ts`
- `migrations/versions/19b1ccd035ac_initial_schema.py`
- `migrations/versions/8f3b7c2a9d10_add_suppliers.py`

## 35. Source Files Created

- `migrations/versions/2f4a8b9c1d3e_add_sale_till_shift_attribution.py`
- `frontend/docs/architecture/reviews/MIGRATION-063-SALE-TILLSHIFT-ATTRIBUTION.md`

## 36. Source Files Modified

- `app/models/pos.py`
- `app/api/sales.py`
- `app/services/tenant/pos/till_shift_service.py`
- `app/api/tests/test_till_shift_contract.py`
- `frontend/src/types/entities/sale.ts`

## 37. Remaining POS Blockers

- The new migration still needs to be applied to the local PostgreSQL database
  when PostgreSQL is available.
- POS UI remains inactive.
- Refund cash-out/TillShift attribution remains unresolved.
- Price override/minimum-price policy remains deferred.
- Inventory batch/expiry/FEFO behavior remains deferred.
- Legacy `Shift` still exists separately from `TillShift`.

## 38. Invariants Verified

- New POS Sales are directly attributable to TillShift.
- Historical Sales remain valid via nullable database column.
- TillShift remains the canonical POS shift owner.
- Legacy `Shift` is unchanged.
- Tenant isolation is enforced.
- Branch isolation is enforced.
- Closed shifts cannot receive Sales.
- Till mismatch cannot be persisted.
- Reconciliation no longer relies on timestamp inference for attributed Sales.
- Cash reconciliation uses attributed SalePayments.
- No Sales read API was invented.
- No POS frontend UI was activated.
- Price policy remains unchanged.
- Inventory/batch behavior remains unchanged.
- TypeScript remains at zero errors.
- Production frontend build remains successful.

## 39. Rollback Boundary

Rollback is limited to:

- dropping `sales.till_shift_id`, its index, and its FK;
- removing checkout persistence of `active_shift.id`;
- removing `till_shift_id` from Sale serialization/frontend entity;
- reverting direct-attribution reconciliation to the prior behavior.

No historical backfill was performed.

## 40. Recommended Next Migration

Recommended next migration:

```text
Migration 064 - POS Price Integrity and Override Policy
```

This should define unit-price authority, minimum-price enforcement, discount
authorization, and supervisor override behavior before POS UI activation.
