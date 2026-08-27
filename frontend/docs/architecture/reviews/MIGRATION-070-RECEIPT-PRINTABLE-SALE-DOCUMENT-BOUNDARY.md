# Migration 070 - Receipt and Printable Sale Document Boundary

## 1. Migration Purpose
Migration 070 establishes a truthful persisted Sale receipt projection and a printable frontend receipt presentation.

## 2. ADR Rules
The migration follows ADR-001 through ADR-010: backend services own business projection logic, frontend services hide HTTP, hooks own query access, query keys are centralized, shared types live under `src/types`, tenant/branch isolation is backend-enforced, and unsupported Sales History, fiscal, PDF, refund-document, and delivery workflows remain absent.

## 3. Baseline
Baseline passed before changes: `venv/bin/python -m compileall app`, `npx tsc -b --pretty false`, and `npm run build`. The existing Vite large chunk warning remained.

## 4. Existing Sale Serialization
`serialize_sale()` already returns Sale id, sale number, tenant/branch IDs, customer id, SaleItems, SalePayments, totals, status, TillShift id, timestamps, and cashier id. It is still a general Sale serializer, not a receipt document projection.

## 5. Sale Detail Route Disposition
`GET /api/sales/<sale_id>` remains refund-oriented. It is guarded by `sales.refund` and adds refundable item quantities. It was not overloaded for receipt viewing.

## 6. Receipt Endpoint Decision
Created a dedicated receipt endpoint: `GET /api/sales/<sale_id>/receipt`.

## 7. Authorization
The endpoint uses the verified backend read permission `sales.read`. Tenant and branch ownership are still enforced by the receipt service.

## 8. Backend Service Owner
Canonical owner: `app/services/tenant/pos/receipt_service.py`.

## 9. Receipt Projection
The response shape is `{ ok: true, receipt }`, where `receipt` contains `sale`, `seller`, `branch`, `customer`, `items`, `payments`, `totals`, `cashier`, `till`, and `till_shift`.

## 10. Sale Identity
The receipt uses persisted `Sale.id`, `Sale.sale_number`, `Sale.status`, `Sale.sale_date`, `Sale.created_at`, `Sale.till_shift_id`, `Sale.refund_status`, and `Sale.refunded_amount`.

## 11. Tenant Fields
Seller fields come from persisted Tenant data: display name, legal name, phone, email, and base currency. No tax PIN, registration number, or fiscal metadata is invented.

## 12. Branch Fields
Branch fields come from persisted Branch data: id, code, name, phone, email, address lines, city, county/state, and country.

## 13. Customer Fields
Customer is included only when `Sale.customer_id` exists. The projection includes customer id, customer number, full name, and phone. Walk-in sales return `customer: null`.

## 14. SaleItem Projection
Each line includes persisted SaleItem id, product id, quantity, unit price, discount, tax, and line total, plus display description and SKU resolved from the current Product record.

## 15. Product Historical-Name Disposition
`SaleItem` does not persist a product-name snapshot. The receipt uses current Product name/SKU for display and documents that historical product-name mutability remains a later document-snapshot concern.

## 16. Money Serialization
Backend money fields are serialized as strings from persisted Decimal values.

## 17. Totals
Totals come from persisted Sale fields: subtotal, discount amount, tax amount, total amount, paid amount, balance due, and tenant base currency.

## 18. Payments
Payment rows come from persisted `SalePayment` records and include amount, reference, paid timestamp, and payment method projection.

## 19. Payment-Method Display
Payment method display comes from persisted `PaymentMethod.name`, `code`, and `method_type`. No hardcoded tender labels are used.

## 20. Cashier and Till Context
Cashier comes from `Sale.cashier_id`; Till comes from `Sale.till_id`; TillShift comes from `Sale.till_shift_id`. The receipt UI displays names/codes rather than making raw UUIDs primary content.

## 21. Warehouse and Batch Disposition
Warehouse and batch data remain internal and are not shown on the standard POS receipt.

## 22. Refund Status Disposition
The receipt projection includes persisted Sale status/refund status fields but does not become refund history or a credit-note document.

## 23. Fiscal Wording
The UI uses neutral `Sales Receipt` wording. It does not claim Tax Invoice, KRA, eTIMS, or fiscal compliance.

## 24. Backend Tests
Added focused receipt tests for authentication, permission, successful current-tenant receipt, persisted totals, lines, split payments, customer/walk-in behavior, tenant/branch identity, cashier/Till context, cross-tenant rejection, cross-branch rejection, unknown Sale rejection, and endpoint permission.

## 25. Frontend Type Owner
Canonical receipt projection type owner: `frontend/src/types/responses/sale-receipt-response.ts`.

## 26. Service
`salesService.getReceipt(saleId)` calls `GET /sales/<sale_id>/receipt` and unwraps the backend envelope to return `SaleReceipt`.

## 27. Query Key
Receipt query key is branch-scoped through `QUERY_KEYS.sales.receipt(branchScope, saleId)`.

## 28. Hook
`useReceipt(saleId)` waits for branch scope readiness and calls `salesService.getReceipt`.

## 29. Receipt Component
`frontend/src/features/sales/components/SaleReceipt.tsx` renders the printable receipt projection.

## 30. Print Styling
`SaleReceiptPage` includes print CSS that hides app chrome and prints the `.sale-receipt` surface only.

## 31. Thermal Print Disposition
The print surface is sized for an 80mm-class browser print layout without printer-driver integration.

## 32. Route/Dialog Decision
Created a dedicated route: `/sales/receipt/:saleId`. This enables reprint by URL without introducing Sales History.

## 33. Route Permission
The frontend route is protected with `sales.read`, matching the backend endpoint.

## 34. POS Checkout Integration
POS checkout success now preserves the persisted Sale id and shows `View / Print Receipt`. The cashier controls navigation and printing.

## 35. Reprint Behavior
Revisiting `/sales/receipt/:saleId` fetches the persisted receipt projection again for authorized users in the active branch.

## 36. Tax and Currency Wording
Tax is displayed only if persisted `tax_amount` is non-zero. Currency uses Tenant `base_currency`; no conversion is implemented.

## 37. Frontend Static Checks
Static checks verified the receipt page uses the hook, fiscal terms are absent from the Sales feature, and printing is user-controlled. Older unsupported Sales hooks still contain placeholder/query-key references outside the receipt path.

## 38. Local DB State
No schema migration was required. PostgreSQL `16/main` remains down on `localhost:5432`; `flask db heads` reports source head `9a1b2c3d4e5f`, while `flask db current` cannot connect.

## 39. Runtime Smoke
No live checkout/print smoke was run because local PostgreSQL is unavailable. Receipt behavior was verified with API contract tests and frontend static/build checks.

## 40. Backend Compile
`venv/bin/python -m compileall app` passed.

## 41. Regression Totals
Auth suite passed: 129 tests. Targeted backend regression including Receipt passed: 121 tests. Focused receipt contract passed: 9 tests.

## 42. Frontend TypeScript
`npx tsc -b --pretty false` passed.

## 43. Frontend Build
`npm run build` passed. The known Vite large chunk warning remains.

## 44. Warnings
The known SQLAlchemy relationship overlap warnings remain unchanged: `RolePermission.role`, `RolePermission.permission`, `UserRole.user`, and `UserRole.role`.

## 45. Files Inspected
Inspected ADR-001 through ADR-010, Sales type/service reviews, POS/refund/reconciliation reviews, Sales API, POS models, Tenant/Branch/Customer/Product/Till/TillShift/User models, query keys, route registry, Sales hooks, Sales service, and POS page.

## 46. Files Created
Created `app/services/tenant/pos/receipt_service.py`, `app/api/tests/test_sales_receipt_contract.py`, `frontend/src/types/responses/sale-receipt-response.ts`, `frontend/src/features/sales/components/SaleReceipt.tsx`, `frontend/src/features/sales/pages/SaleReceiptPage.tsx`, and this review document.

## 47. Files Modified
Modified `app/api/sales.py`, `frontend/src/services/sales/salesService.ts`, `frontend/src/hooks/queries/sales/useReceipt.ts`, `frontend/src/hooks/queries/sales/index.ts`, `frontend/src/lib/queryKeys.ts`, `frontend/src/routes/routes.ts`, `frontend/src/routes/permissions.ts`, `frontend/src/app/router.tsx`, `frontend/src/features/sales/index.ts`, `frontend/src/features/sales/pages/PosPage.tsx`, and `frontend/src/types/responses/index.ts`.

## 48. Remaining Sales/POS Blockers
Sales History, document snapshots for historical product names, accounting invoices, credit notes, external reversals, receipt delivery, PDF generation, fiscal integrations, and refund receipt documents remain deferred.

## 49. Invariants Verified
Receipt data comes from persisted Sale rows, totals and payments are server-derived, tenant/branch isolation is enforced, receipt read is view-only, browser printing does not mutate Sale state, no fiscal claims are fabricated, no Sales History was introduced, and TypeScript/build remain clean.

## 50. Rollback Boundary
Rollback removes the new receipt endpoint/service/tests and frontend receipt route/type/service/hook/component wiring. No database rollback is needed.

## 51. Recommended Next Migration
Recommended next migration: Sales History read-only operational slice, using the receipt endpoint only as a detail/reprint destination and keeping financial document workflows separate.
