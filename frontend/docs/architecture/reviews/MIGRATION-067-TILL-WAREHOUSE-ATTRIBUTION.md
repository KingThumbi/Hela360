# Migration 067 - Till Warehouse Attribution Contract

## 1. Migration Purpose

Migration 067 makes Till the canonical POS stock-location authority.

Checkout no longer trusts a browser-selected Warehouse. It derives the sale
Warehouse from the verified active Till assigned to the cashier's branch.

## 2. Scope

Implemented only the Till-to-Warehouse attribution contract.

No receipt work, refund stock restoration, prescriptions, broad Inventory admin,
pricing redesign, batch allocation redesign, or TillShift lifecycle redesign was
included.

## 3. Baseline

Pre-change verification remained green:

```text
venv/bin/python -m compileall app: PASS
npx tsc -b --pretty false: PASS
npm run build: PASS
```

The known Vite large-chunk warning remained.

## 4. Alembic Revision

New revision:

```text
6c2f9d8a1b4e_add_till_warehouse_attribution.py
```

Down revision:

```text
2f4a8b9c1d3e
```

## 5. Database Contract

Added:

```text
tills.warehouse_id -> warehouses.id
```

The column is nullable at database level for historical safety.

## 6. Runtime Contract

Operational POS Tills must have a valid Warehouse assignment.

Nullable storage does not mean nullable runtime behavior for active POS use.

## 7. Tenant Validation

Runtime validation requires the Till Warehouse to belong to the same tenant as
the authenticated cashier context.

## 8. Branch Validation

Runtime validation requires the Till Warehouse to belong to the same branch as
the authenticated cashier context.

## 9. Warehouse Active Validation

Runtime validation requires the Till Warehouse to be active.

Inactive Warehouses cannot back an operational TillShift or checkout.

## 10. Till Serializer

`GET /api/tills` now returns:

```text
warehouse_id
```

This exposes attribution without exposing Warehouse selection in POS.

## 11. Till List Behavior

Active Till listing is now operationally filtered.

Only active Tills with active, same-tenant, same-branch Warehouse attribution are
returned for POS use.

## 12. TillShift Open Behavior

Opening a TillShift validates the selected Till's Warehouse before creating the
shift.

## 13. Unconfigured Till Behavior

An active Till without `warehouse_id` is rejected for opening an operational
TillShift.

Error:

```text
Till is not configured with a warehouse.
```

## 14. Invalid Warehouse Behavior

Cross-tenant, cross-branch, and inactive Till Warehouse assignments are rejected.

Error:

```text
Till warehouse is not active for this branch.
```

## 15. Checkout Authority

Checkout derives Warehouse from:

```text
Till.warehouse_id
```

The request body is not authoritative for Warehouse selection.

## 16. Compatibility Field

`CreateSaleRequest.warehouse_id` remains accepted as an optional compatibility
field.

If supplied, it must match the selected Till Warehouse.

## 17. Mismatch Rejection

Checkout rejects a supplied Warehouse that does not match the selected Till.

Error:

```text
warehouse_id must match the selected till warehouse.
```

## 18. Omitted Warehouse Checkout

Checkout succeeds without client `warehouse_id` when the selected Till has valid
Warehouse attribution and an open shift exists.

## 19. Sale Attribution

Created Sale rows continue to store:

```text
sales.warehouse_id
```

The value now comes from the Till.

## 20. Stock Service Integration

`build_sale_item` still passes a Warehouse ID into stock allocation.

The supplied value is now the Till-derived Warehouse ID.

## 21. FEFO Behavior

FEFO and batch allocation behavior was left unchanged.

Migration 067 only changes the source of the Warehouse ID.

## 22. Price Behavior

Server-side product price validation remains unchanged.

No override or pricing redesign was introduced.

## 23. Payment Behavior

Payment validation and persistence remain unchanged.

## 24. TillShift Attribution

Sale-to-TillShift attribution remains unchanged.

Checkout still requires an open shift for the selected Till and cashier.

## 25. Frontend Entity

The canonical frontend Till entity now includes:

```text
warehouse_id: string | null
```

## 26. Frontend Request DTO

`CreateSaleRequest.warehouse_id` is now optional.

The POS page does not send it in the normal flow.

## 27. POS Warehouse Picker

Migration 066's manual Warehouse picker was removed from the POS normal flow.

Warehouse readiness is displayed from the selected/current Till instead.

## 28. Warehouse Hook Foundation

`useWarehouses()` and the Warehouse read API remain in place as verified
foundation.

POS no longer consumes them for checkout.

## 29. POS Readiness UI

POS blocks open shift and checkout when the selected Till has no Warehouse
assignment in the returned Till contract.

## 30. Loading State

Existing Till loading behavior remains.

The page does not invent fallback Warehouse values during loading.

## 31. Error State

Existing API error display remains.

Backend validation errors are surfaced through the same POS error path.

## 32. Empty State

The Till empty state now communicates absence of an active Till with a branch
Warehouse assignment.

## 33. Tests Added

Added coverage for:

- Till serializer `warehouse_id`
- invalid Till Warehouse filtering
- unconfigured Till open rejection
- cross-tenant Warehouse rejection
- cross-branch Warehouse rejection
- inactive Warehouse rejection
- checkout without client Warehouse
- mismatched client Warehouse rejection
- stock movement Warehouse attribution

## 34. Backend Verification

Verified:

```text
venv/bin/python -m py_compile migrations/versions/6c2f9d8a1b4e_add_till_warehouse_attribution.py: PASS
venv/bin/python -m compileall app: PASS
venv/bin/python -m pytest app/api/tests/test_till_shift_contract.py -q: 47 passed
```

## 35. Regression Verification

Verified:

```text
current-session/product/customer/supplier/payment/POS/Till contract tests: 93 passed
auth suite: 129 passed
```

## 36. Frontend Verification

Verified:

```text
npx tsc -b --pretty false: PASS
npm run build: PASS
```

The known Vite large-chunk warning remained.

## 37. Alembic Source State

Verified:

```text
FLASK_APP=app:create_app venv/bin/flask db heads
6c2f9d8a1b4e (head)
```

## 38. Local Database Application State

PostgreSQL was unavailable during final Migration 067 verification:

```text
pg_lsclusters: 16/main 5432 down
pg_isready -h localhost -p 5432: no response
```

`flask db current` and `flask db check` could not connect.

Migration application to the real local database is therefore not verified in
this migration run.

## 39. Seed and Bootstrap Inspection

Existing bootstrap command inspected without execution:

```text
flask seed-initial
```

It seeds an initial tenant, branch, administrator role/user, and payment
methods. It does not assign Warehouses to Tills.

No seed data was executed in Migration 067.

## 40. Remaining Technical Debt

The four existing SQLAlchemy relationship overlap warnings remain:

- `RolePermission.role`
- `RolePermission.permission`
- `UserRole.user`
- `UserRole.role`

These are model-relationship cleanup work for a later migration and were not
modified here.

## 41. Migration Classification

Source and test classification:

```text
Up to date
```

Operational database readiness:

```text
Pending local PostgreSQL availability and Alembic upgrade to 6c2f9d8a1b4e
```
