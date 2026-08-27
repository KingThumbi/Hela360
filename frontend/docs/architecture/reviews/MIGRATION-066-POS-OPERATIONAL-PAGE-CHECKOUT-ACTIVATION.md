# Migration 066 - POS Operational Page and Checkout Activation

## 1. Migration Purpose

Migration 066 activates the cashier POS route against verified backend contracts.

The page supports branch readiness, active Till discovery, current/open
TillShift, explicit warehouse selection, Product search/code lookup, optional
Customer selection, active Payment Method selection, cart management, and
checkout submission.

## 2. ADR Rules

Applied ADR-001 through ADR-009:

- service and hook boundaries own API access;
- query keys remain centralized;
- route permission metadata owns page access;
- tenant and branch scope come from authenticated session/shell state;
- the sales feature owns POS UI;
- naming follows existing route and type conventions.

## 3. Baseline

Baseline:

```text
venv/bin/python -m compileall app: PASS
npx tsc -b --pretty false: PASS
npm run build: PASS
```

Known Vite large-chunk warning remained.

## 4. Existing POS UI Inventory

Found:

- `PATHS.SALES.POS = /sales/pos`
- navigation item "Point of Sale"
- canonical `useCreateSale`
- canonical Product, Customer, Till, TillShift, Payment Method hooks
- no `frontend/src/features/pos`
- no operational POS routed page
- no warehouse read hook/API

## 5. Canonical Feature Owner

Canonical owner:

```text
frontend/src/features/sales
```

Reason: Sales already owns checkout hooks and route structure.

## 6. Route Path

Operational route:

```text
/sales/pos
```

No new route string was invented.

## 7. Route Permission

Route permission:

```text
sales.create
```

Navigation now uses the same verified permission.

## 8. Branch Readiness

POS uses `useQueryScope()` and selected branch shell state.

If branch scope is not ready, POS operations are blocked and a branch selection
requirement is shown.

No local/session storage or URL branch fallback is used.

## 9. Till Loading

Tills load through `useTills()`.

The backend returns active branch tills only.

## 10. Till Selection

If a current open shift exists, the Till is derived from that shift.

If no shift exists, the cashier selects an active Till locally before opening a
shift.

## 11. Current TillShift

Current shift uses `useCurrentTillShift(selectedTillId)`.

The page handles loading, open, absent, and error states.

## 12. Open-Shift Flow

Open shift uses `useOpenTillShift()`.

Payload:

```text
till_id
opening_float
```

No tenant, branch, cashier, or raw shift ID input is exposed.

## 13. Warehouse Contract

Migration 065 found Till has no `warehouse_id`, while checkout requires
`warehouse_id`.

Migration 066 adds a narrow backend read endpoint:

```text
GET /api/warehouses
permission: sales.create
```

It returns active warehouses for the authenticated tenant and selected branch
only.

## 14. Product Search

Product search uses `useProducts()`.

Search is server-backed and requests active Products.

## 15. Code Lookup

Code lookup uses `useProductByCode()`.

No scanner-specific device API was added.

## 16. Cart Architecture

Cart state is feature-local React state in `PosPage`.

The cart stores Product snapshots and quantity only.

## 17. Quantity Behavior

Quantity supports positive decimal input.

The UI rejects zero, negative, and invalid quantities before submit while the
backend remains authoritative.

## 18. Display Price

The page displays `Product.default_sale_price` as current informational price.

Checkout does not trust or submit client totals.

## 19. Estimated Totals

Estimated total is UI-only.

Server-calculated totals from checkout remain authoritative.

## 20. Customer Behavior

Customer selection uses `useCustomers()`.

Customer is optional; walk-in checkout sends no fake `customer_id`.

## 21. Payment Method Behavior

Payment Methods use `usePaymentMethods()`.

No Cash, M-Pesa, Card, or Bank method is hardcoded.

## 22. Multi-Payment Behavior

The page supports one or more payment rows.

Each row sends:

```text
payment_method_id
amount
reference
```

## 23. Checkout DTO

Checkout payload uses the verified DTO:

```text
warehouse_id
till_id
customer_id?
items[]
payments[]
```

No tenant, branch, cashier, totals, discounts, taxes, or batch IDs are sent.

## 24. Till/TillShift IDs

Checkout uses `currentShift.till_id`.

TillShift ID is not manually entered or sent by the frontend.

## 25. Warehouse ID

Warehouse ID comes from explicit selection from `useWarehouses()`.

No first-warehouse auto-selection, raw UUID field, or storage fallback exists.

## 26. Checkout Hook

Checkout uses canonical `useCreateSale()`.

The POS page does not call `salesService` directly.

## 27. Duplicate Submit Protection

Checkout button is disabled while `useCreateSale` is pending.

Cart is not cleared before server success.

## 28. Success Behavior

On success:

- success toast is shown;
- returned Sale number is shown;
- cart clears;
- payments reset;
- customer selection clears;
- branch, open shift, and warehouse selection remain.

No receipt or history navigation is fabricated.

## 29. Error Behavior

Backend errors remain visible in the page.

Cart and payment rows are preserved on failure.

## 30. Price-Change Behavior

Server price authority remains unchanged.

If a stale cart is rejected, the backend error is displayed and the cashier can
refresh/search again.

## 31. Stock-Error Behavior

Insufficient/expired stock errors are displayed without clearing cart state.

Batch internals are not exposed as controls.

## 32. Batch Policy

No manual batch selector exists.

Backend FEFO allocation from Migration 065 remains authoritative.

## 33. Prescription Limitation

Products can show a prescription badge.

No prescription compliance workflow is implemented.

## 34. Authorization

POS route, Till/TillShift calls, warehouse read, Payment Methods, and checkout
align to `sales.create`.

## 35. Navigation

The existing Point of Sale navigation item remains in place and now resolves to
the operational route.

## 36. Loading/Empty/Error States

Covered states:

- no branch;
- no active tills;
- no open shift;
- no active warehouse;
- no matching products;
- no active payment methods;
- empty cart;
- checkout error.

## 37. Keyboard/Responsive Behavior

Search/code forms submit on Enter.

Layout prioritizes desktop cashier use and collapses to a single column at
narrow widths.

## 38. Local DB Migration State

Local PostgreSQL state:

```text
pg_isready: no response
pg_lsclusters: 16/main down
```

Alembic head:

```text
2f4a8b9c1d3e (head)
```

`flask db current` and `flask db check` fail because the database is
unreachable.

## 39. Runtime Smoke Result

Static app smoke:

```text
flask routes: PASS
```

Real login/POS runtime smoke was not executed because local PostgreSQL is down
and no live dev database session is available.

## 40. Backend Changes

Added:

- `GET /api/warehouses`
- `serialize_warehouse`
- app-factory registration

No checkout business logic was redesigned.

## 41. Backend Tests

Focused POS/TillShift suite:

```text
40 passed
```

The two added warehouse tests verify branch-scoped active warehouse listing and
`sales.create` permission.

## 42. Frontend Files Created

Created:

- `frontend/src/features/sales/pages/PosPage.tsx`
- `frontend/src/features/sales/index.ts`
- `frontend/src/types/entities/warehouse.ts`
- `frontend/src/services/warehouses/warehouseService.ts`
- `frontend/src/services/warehouses/index.ts`
- `frontend/src/hooks/queries/warehouses/useWarehouses.ts`
- `frontend/src/hooks/queries/warehouses/index.ts`

## 43. Frontend Files Modified

Modified:

- router
- route permissions
- navigation permission
- API endpoint registry
- query key registry
- hooks barrel
- entity barrel

## 44. TypeScript Result

```text
npx tsc -b --pretty false: PASS
```

## 45. Vite Build Result

```text
npm run build: PASS
```

## 46. Warnings

Known warnings remain:

- Vite large-chunk warning;
- existing SQLAlchemy RolePermission/UserRole relationship overlap warnings.

## 47. Remaining POS Blockers

Remaining blockers:

- local PostgreSQL unavailable for real runtime smoke;
- Till lacks `warehouse_id`, so warehouse selection is transitional;
- receipt/history/refund/prescription workflows remain out of scope.

## 48. Invariants Verified

Verified:

- POS requires branch readiness;
- POS requires open TillShift;
- Payment Methods come from backend;
- Product and Customer search use hooks;
- cart does not own authoritative price;
- server remains price and inventory authority;
- no batch selector;
- no discount/tax/override controls;
- no receipt/history fabrication;
- TypeScript and build pass.

## 49. Rollback Boundary

Rollback is limited to the new POS frontend route/page and the narrow warehouse
read contract.

No schema changes were introduced.

## 50. Recommended Next Migration

Recommended next migration:

```text
Migration 067 - Till Warehouse Attribution Contract
```

That should add canonical Till-to-warehouse ownership so POS no longer needs a
transitional explicit warehouse picker.
