# Migration 069 - Refund Reconciliation Attribution and DB Upgrade

## 1. Migration Purpose
Migration 069 adds direct refund-to-TillShift attribution so cash reconciliation can subtract cash refunds from the shift that processed the refund, not from the original sale shift.

## 2. ADR Rules
The migration follows the established architecture-first constraints: canonical backend entities remain authoritative, tenant and branch context is server-derived, frontend types mirror backend response contracts, and unsupported update/delete/payment reversal behavior is not fabricated.

## 3. Baseline
Pre-change compile, frontend TypeScript, and frontend build were clean. Source head entering this migration was `7d9e2f4a6c8b`.

## 4. Refund Model Before
`SaleRefund` stored tenant, sale, branch, warehouse, till, cashier, customer, refund number, totals, status, stock return state, reason, notes, and timestamps. It did not store the operational TillShift that processed the refund.

## 5. Refund Route Context
Refund creation is still performed through the existing sales refund route and `RefundService`. The route uses authenticated identity context and returns a compact refund payload.

## 6. Attribution Decision
Refund attribution is direct and explicit: a posted refund now points to the current open `TillShift` for the authenticated cashier, branch, and tenant.

## 7. Field, FK, and Nullability
Added nullable `sale_refunds.till_shift_id` as a UUID foreign key to `till_shifts.id`, indexed for reconciliation queries. The column is nullable for historical rows, while runtime creation requires a current open shift for new operational refunds.

## 8. Migration Revision
Created Alembic revision `9a1b2c3d4e5f_add_refund_till_shift_attribution.py`.

## 9. Historical Refund Disposition
Existing refund history remains valid with `till_shift_id = NULL`. Historical rows are not backfilled in this migration.

## 10. Runtime Shift Requirement
New operational refunds require an open `TillShift` for the authenticated tenant, branch, and cashier. Missing or closed shift state returns a refund conflict.

## 11. Server-Derived Context
The refund shift is resolved server-side from authenticated identity. The client does not submit or control `till_shift_id`.

## 12. Serializer
The refund response now includes `till_shift_id` as a nullable string.

## 13. Frontend Type Alignment
`SaleRefund` frontend typing now includes `till_shift_id: string | null`.

## 14. Negative SalePayment Behavior
Refunds still create a negative `SalePayment` using the existing refund payment method resolution behavior.

## 15. Refund Tender Semantics
The negative payment is an internal financial ledger record only. This migration does not implement external M-Pesa, card, bank, or cash disbursement reversal workflows.

## 16. Multi-Payment Disposition
Tender allocation remains ambiguous for multi-payment sales. The current system chooses the first original sale payment by `paid_at ASC`; no proportional or tender-specific allocation logic was invented.

## 17. Reconciliation Before
Cash reconciliation summed cash `SalePayment.amount` through the original `Sale.till_shift_id`, which meant negative refund payments could reduce the original sale shift instead of the shift that processed the refund.

## 18. Reconciliation After
Cash reconciliation now computes `opening_float + positive cash sale payments attributed to the Sale shift - cash refund payments attributed to the Refund shift`.

## 19. Sale A / Refund B Behavior
If a sale is made in shift A and refunded in shift B, shift A keeps the original cash sale attribution and shift B receives the cash refund reduction.

## 20. No-Open and Closed-Shift Behavior
Refund submission is rejected when no matching open shift exists. Closed shifts are excluded by `status == "open"` and `closed_at IS NULL`.

## 21. Tenant and Branch Isolation
Open-shift lookup is scoped by tenant, branch, cashier, open status, and closed timestamp. Reconciliation also scopes refund rows by the shift tenant.

## 22. Inventory Restoration Regression
Refund stock restoration remains delegated to the existing inventory refund service and was covered by the targeted regression suite.

## 23. Transaction Atomicity
Refund creation, refund items, optional stock restoration, negative payment creation, and sale refund-status updates remain in one service transaction boundary.

## 24. Frontend Refund Page Shift Behavior
The Refunds page now reads `useCurrentTillShift()`, displays an open-shift-required alert when needed, shows shift status in the sale summary, and blocks refund submission without an open shift.

## 25. Financial Wording
UI and docs avoid claiming external payment reversals or receipts. The migration records internal operational refund attribution only.

## 26. Tests
Added and updated TillShift contract coverage for refund attribution, original sale shift preservation, missing open shift rejection, same-shift cash refund reconciliation, second-shift cash refund reconciliation, and non-cash refund behavior.

## 27. Live DB Starting Revision
Not re-verified in this session because local PostgreSQL `16/main` is down on `localhost:5432`.

## 28. Source Head
Repository Alembic head is `9a1b2c3d4e5f`.

## 29. Pending Migration Chain
Alembic history shows `19b1ccd035ac -> 8f3b7c2a9d10 -> 2f4a8b9c1d3e -> 6c2f9d8a1b4e -> 7d9e2f4a6c8b -> 9a1b2c3d4e5f`.

## 30. Safety Inspection
The Migration 069 Alembic revision is additive: it adds a nullable column, an index, and a foreign key. It does not drop or rewrite runtime data.

## 31. DB Upgrade Result
The real local DB upgrade was not executed because PostgreSQL is unavailable. `pg_lsclusters` reported `16/main` on port `5432` as `down`, and `pg_isready -h localhost -p 5432` returned no response. Attempting `pg_ctlcluster 16 main start` failed because it must be run as `postgres` or root.

## 32. Final Current and Head
`flask db heads` returned `9a1b2c3d4e5f (head)`. `flask db current` and `flask db check` could not connect to the database while PostgreSQL was down.

## 33. Schema Verification
Source schema and migration were inspected. Live schema verification is pending operator startup of PostgreSQL and `flask db upgrade`.

## 34. First-Tenant Readiness
First-tenant seed readiness could not be re-counted during this migration because the local database is offline. The last verified state remains foundational tenant, branch, and user present, with operational Product, Customer, Supplier, and Sales data empty.

## 35. Runtime Smoke
Runtime database smoke could not be re-run because PostgreSQL is offline.

## 36. Backend Compile
`venv/bin/python -m compileall app` passed.

## 37. Regression Totals
Targeted backend regression passed: 112 tests, 4 known SQLAlchemy relationship overlap warnings. Auth suite passed: 129 tests.

## 38. Frontend TypeScript
`npx tsc -b --pretty false` passed.

## 39. Frontend Build
`npm run build` passed. Vite reported the known large chunk warning.

## 40. Warnings
The remaining SQLAlchemy overlap warnings are unchanged and intentionally deferred: `RolePermission.role`, `RolePermission.permission`, `UserRole.user`, and `UserRole.role`.

## 41. Files Inspected
Inspected refund service, TillShift service, sales API, POS models, TillShift serializer, Refunds page, frontend sale-refund type, current migration chain, initial schema migration, and frontend shell bootstrap hook.

## 42. Files Created
Created `migrations/versions/9a1b2c3d4e5f_add_refund_till_shift_attribution.py` and this review document.

## 43. Files Modified
Modified `app/models/pos.py`, `app/services/tenant/pos/refund_service.py`, `app/services/tenant/pos/till_shift_service.py`, `app/serializers/till_shift.py`, `app/api/sales.py`, `frontend/src/types/entities/sale-refund.ts`, `frontend/src/features/sales/pages/RefundsPage.tsx`, `app/api/tests/test_till_shift_contract.py`, and `app/api/tests/test_sales_pos_contract.py`.

## 44. Remaining Financial and POS Blockers
External payment reversals, receipt issuance, detailed multi-payment refund allocation, Sales History activation, and full TillShift lifecycle refinements remain outside this migration.

## 45. Invariants Verified
Refunds preserve original `Sale.till_shift_id`, use direct `SaleRefund.till_shift_id` for refund processing shift, subtract only cash refund payment records from cash reconciliation, do not reduce cash for non-cash refund payment records, and keep stock restoration behavior intact.

## 46. Rollback Boundary
Rollback removes only the `sale_refunds.till_shift_id` foreign key, index, and column. Historical refund data remains otherwise untouched.

## 47. Recommended Next Migration
After operator DB upgrade verification for Migration 069, the recommended next migration is Sales/POS operational expansion with explicit attention to Sales History and payment/refund tender semantics.
