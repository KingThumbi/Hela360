# Migration 082 - Sales/POS Pharmacy Inventory Hardening

## 1. Migration Purpose

Re-audit and harden the operational POS against the post-Migration 066 Inventory, Goods Receipt, Stock Count, Stock Adjustment, Refund, and Dispensing capabilities needed for a first live pharmacy tenant.

## 2. Baseline

- `venv/bin/python -m compileall app`: PASS
- `npx tsc -b --pretty false`: PASS
- `npm run build`: PASS
- Known warning: Vite large chunk warning remains.

## 3. Current POS Architecture

POS uses Product catalogue search/code lookup, Customer search, Payment Method lookup, Till/TillShift state, and the verified Sales checkout mutation. Checkout remains server authoritative.

## 4. Checkout Request Audit

The frontend sends `till_id`, optional `customer_id`, Product ids, quantities, prescription context, and payment ids/amounts. It does not send tenant, branch, cashier, trusted totals, batch id, StockBalance id, authoritative price overrides, discount, or tax.

## 5. Product/Stock Visibility Decision

Migration 082 adds a narrow Sales-owned POS availability endpoint instead of granting cashiers broad Inventory reads.

## 6. Till/Warehouse Scope

`GET /api/sales/availability` accepts `till_id` and Product ids. The backend verifies the Till belongs to the authenticated tenant/branch and derives the Till Warehouse server-side.

## 7. Tracked/Non-Tracked Behavior

Inventory-tracked Products receive a stock status and sellable quantity. Non-inventory Products are reported as `not_tracked` and remain sellable without stock allocation.

## 8. Sellable Quantity Semantics

The endpoint returns minimal `sellable_quantity` using checkout-aligned semantics. Batch/expiry Products use eligible batch availability, not aggregate on-hand.

## 9. Batch/Expiry Behavior

Expired stock is never counted as sellable. POS does not expose batch selection; FEFO allocation remains backend-owned during checkout.

## 10. Adjustment Integration

Stock Adjustment posting invalidates Inventory and branch Sales caches, so POS availability refreshes after adjustment operations.

## 11. Receiving Integration

Goods Receipt/receiving invalidation flows through Inventory operations and now also invalidates branch Sales availability context.

## 12. Refund Integration

Refunds already use Sales operation invalidation, refreshing Sales and Inventory caches. Restored valid batch stock can become sellable; restored expired stock remains unsellable by checkout and availability semantics.

## 13. Stock Count Disposition

Stock Count remains observation-only. Its hooks do not mutate or deliberately invalidate POS stock availability.

## 14. Concurrency

Checkout remains protected by backend row locks in stock allocation. Availability is informational and may become stale between browsing and checkout.

## 15. Quantity/Cart Behavior

The POS cart merges duplicate Products, keeps decimal-compatible quantity entry, blocks non-positive cart quantities, and checks displayed sellable quantity before submit when available.

## 16. Price Authority

The frontend displays estimated totals only. Checkout uses backend current Product price and rejects stale client price compatibility fields when present.

## 17. Prescription Regression

Prescription-required Products still require a Customer and prescriber name in the POS before checkout. Server-side dispensing validation remains authoritative.

## 18. Checkout Errors

Stock-related checkout failures are normalized to prompt the cashier to review quantities and retry. TillShift and price-change errors are surfaced with operational wording and trigger availability/shift refresh.

## 19. TillShift Behavior

Checkout remains blocked without an open TillShift. Availability browsing requires an active Till with a Warehouse, but not an open shift.

## 20. Customer Behavior

Walk-in non-prescription sales remain valid with no Customer. Prescription sales require Customer context.

## 21. Receipt/History Invalidation

Checkout success continues to invalidate Sales and Inventory operation caches and navigates to persisted receipt data through the existing receipt route.

## 22. Permission Dependency Decision

The new availability endpoint is protected by `sales.create`. Cashiers do not need broad `inventory.read` just to see POS sellability indicators.

## 23. POS Availability Endpoint

Added `GET /api/sales/availability`. It returns Product id, Warehouse id, tracking flags, Rx flag, active flag, status, sellable quantity, low-stock flag, out-of-stock flag, expired-only flag, and earliest sellable expiry date. It exposes no costs, batches, reservations, or movement history.

## 24. Frontend Type/Service/Hook Changes

Added `PosProductAvailability`, Sales service availability method, and `usePosProductAvailability`.

## 25. Query Keys

Availability uses a branch/Till-scoped Sales query key: branch scope, `sales`, `availability`, Till id, normalized Product ids.

## 26. Backend Tests

Focused availability tests cover permission, Till/Warehouse scoping, sellable batch stock, expired-only stock, non-inventory Product behavior, and cross-branch Till rejection.

## 27. Frontend UX Verification

POS now distinguishes Rx, non-stock, in-stock, low-stock, out-of-stock, expired-only, and checking-stock states using server-backed data.

## 28. Schema Disposition

No Alembic revision or schema change was required.

## 29. Local DB State

Source head is `e5f6a7b8c9d0`. `flask db current` could not run because local PostgreSQL is down/not accepting connections.

## 30. Runtime Smoke

No live stock mutation smoke was performed because local PostgreSQL is unavailable and operational stock should not be mutated in non-disposable data.

## 31. Backend Regression

Regression suite run: `182 passed, 4 known SQLAlchemy overlap warnings`.

## 32. Frontend TypeScript

`npx tsc -b --pretty false`: PASS.

## 33. Frontend Build

`npm run build`: PASS.

## 34. Warnings

Known SQLAlchemy relationship overlap warnings remain separate technical debt. Known Vite chunk-size warning remains.

## 35. Files Inspected

POS page, Sales hooks/services, Product hooks, Inventory hooks/services, checkout request types, Sales checkout route, Sale stock allocation service, Inventory read service, query keys, invalidation, and POS/till tests.

## 36. Files Created

- `frontend/src/hooks/queries/sales/usePosProductAvailability.ts`
- `frontend/src/types/responses/pos-product-availability.ts`
- `frontend/docs/architecture/reviews/MIGRATION-082-SALES-POS-PHARMACY-INVENTORY-HARDENING.md`

## 37. Files Modified

Sales API, POS page, Sales service, Sales hook exports, API endpoint registry, query keys, query invalidation, response exports, and POS/till contract tests.

## 38. Remaining POS/Pharmacy Blockers

Pack-size/unit-conversion semantics remain an MVP gap: Product has `pack_size` and Unit fields, but no verified pharmacy unit-conversion workflow. Receipt Product historical snapshot limitations remain unchanged.

## 39. Invariants Verified

Checkout remains stock authority; Till Warehouse is stock scope; expired stock is unsellable; FEFO remains backend-owned; frontend does not select batches; Goods Receipt/Refund/Adjustment invalidate POS availability; Stock Count remains observation-only; prescription and price authority remain intact; no Procurement coupling was introduced.

## 40. Rollback Boundary

Rollback is removal of the Sales availability endpoint, frontend availability hook/type/service/key usage, POS badges/guards, and related tests. No database rollback is required.

## 41. Recommended Next Migration

Migration 083 - Pharmacy Inventory backend/API layer for receiving, stock counts, adjustments, expiry monitoring, and sale-stock integration hardening.
