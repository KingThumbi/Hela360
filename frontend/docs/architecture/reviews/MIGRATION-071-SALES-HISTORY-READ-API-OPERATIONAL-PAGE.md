# Migration 071 - Sales History Read API and Operational Page

## 1. Migration Purpose
Migration 071 activates a read-only Sales History vertical slice: backend list API, service-owned filtering/pagination, frontend service/hook boundary, protected route, and operational page.

## 2. ADR Rules
The migration follows ADR-001 through ADR-010: backend services own business/query logic, frontend services own HTTP, hooks own query access, query keys are centralized, route permissions are canonical, tenant/branch scope is enforced server-side, and unsupported Sales workflows remain absent.

## 3. Baseline
Baseline passed before changes: `venv/bin/python -m compileall app`, `npx tsc -b --pretty false`, and `npm run build`. The known Vite large chunk warning remained.

## 4. Sale Model Fields
Sales History uses persisted Sale identity, status, sale date, created timestamp, cashier id, Till/TillShift attribution, totals, paid amount, balance due, refund status, and refunded amount.

## 5. Existing Detail Route Disposition
`GET /api/sales/<sale_id>` remains the refund lookup route guarded by `sales.refund`. It was not converted into a general Sale detail endpoint.

## 6. Permission
The new list endpoint and frontend route use `sales.read`.

## 7. List Endpoint
Created `GET /api/sales`, returning the authenticated tenant and active branch Sales History list.

## 8. Query Service Owner
Canonical backend owner: `app/services/tenant/pos/sales_query_service.py`.

## 9. Pagination
Server pagination supports positive `page` and `per_page` values with response metadata: page, per_page, total, pages, has_next, and has_prev.

## 10. Search
Server search supports Sale number and customer number/name/phone. The frontend passes the search string without local filtering.

## 11. Date Filters
`date_from` and `date_to` are ISO date filters applied inclusively against `Sale.sale_date`.

## 12. Status Filter
Status filtering is allowlisted to persisted operational/refund statuses used by this read model. Unsupported statuses return validation errors.

## 13. Ordering
Sales are ordered newest first by `Sale.sale_date` and then `Sale.id`.

## 14. Sale Summary Projection
The list projection is intentionally narrow. It does not include SaleItems, payments, receipt lines, refund line details, prescriptions, stock movements, or accounting documents.

## 15. Customer Summary
Customer projection includes only id, customer number, display name, and phone. Walk-in Sales return `customer: null`.

## 16. Cashier Summary
Cashier projection includes id, username, email, and display name from the persisted cashier user.

## 17. Till Summary
Till projection includes id, code, and name when Till attribution exists.

## 18. Totals
Subtotal, discount amount, tax amount, total amount, paid amount, and balance due are serialized from persisted Sale decimal fields.

## 19. Refund Status
The list includes persisted refund status and refunded amount only as display fields. It does not introduce refund operations.

## 20. Response Envelope
The API response shape is `{ ok: true, items, pagination }`.

## 21. Backend Tests
Added focused Sales History contract tests for authentication, permission enforcement, `sales.read` route ownership, branch isolation, pagination, ordering, projection shape, search, status/date filters, invalid filters, and empty state.

## 22. Frontend Type Ownership
Canonical frontend Sale summary response type owner: `frontend/src/types/responses/sale-summary.ts`.

## 23. ListSalesRequest
Canonical request type owner: `frontend/src/types/requests/list-sales-request.ts`.

## 24. Sales Service
`salesService.listSales(params)` calls `GET /sales` and unwraps the backend envelope into `PaginatedResponse<SaleSummary>`.

## 25. Query Keys
Sales list keys are branch-scoped through `QUERY_KEYS.sales.list(branchScope, params)`. Receipt and refund lookup keys remain branch-scoped.

## 26. useSales
`useSales(params)` waits for branch scope readiness and calls `salesService.listSales(params)`.

## 27. Public Hook Boundary
The Sales hook barrel exports `useSales`, `useCreateSale`, `useRefundSale`, `useRefundableSale`, and `useReceipt`. Unsupported generic Sale detail hooks are not exported.

## 28. Route Permission
`/sales/history` is protected with `sales.read` in route permission metadata.

## 29. Route
Created the Sales History application route at `/sales/history`.

## 30. Navigation
Sales History navigation now derives from route permission metadata and uses `sales.read`, not the legacy `sales.view` constant.

## 31. Page
Created `frontend/src/features/sales/pages/SalesHistoryPage.tsx` as a read-only operational table page.

## 32. Table
The page displays Sale number, date, customer, cashier, Till, status, total, paid amount, balance due, and row action.

## 33. Filters
The page supports server-backed search, status, date_from, and date_to filters with pagination reset on filter changes.

## 34. Row Actions
The only row action is Receipt, linking to `/sales/receipt/:saleId`.

## 35. Receipt-Detail Disposition
Receipt remains the persisted printable sale document route. Sales History does not add a separate general Sale detail UI.

## 36. Decimal and Currency Display
The frontend formats persisted money strings for display only. It does not recalculate totals.

## 37. Invalidation Changes
Sales checkout/refund invalidation now uses centralized helpers and branch-scoped Sales keys while preserving broad legacy invalidation during the transition.

## 38. POS Integration
POS checkout continues to create Sales through the existing mutation path. Sales History only reads completed persisted Sales.

## 39. Refund Integration
Refund mutation invalidation now refreshes Sales list, receipt, and refund lookup caches for the active branch. No new refund behavior was added.

## 40. Real DB State
No schema migration was required. PostgreSQL `16/main` is currently down on `localhost:5432`; `pg_isready` reports no response.

## 41. Runtime Smoke
Live runtime smoke against local PostgreSQL was not available because the local cluster is offline. `flask db heads` reads source head `9a1b2c3d4e5f`; `flask db current` cannot connect.

## 42. Backend Compile
`venv/bin/python -m compileall app` passed.

## 43. Regression Totals
Auth suite passed: 129 tests. Targeted backend regression including Sales History, Receipt, POS, payment methods, Product list, Customer, Supplier, current session, and TillShift passed: 131 tests.

## 44. Frontend TypeScript
`npx tsc -b --pretty false` passed.

## 45. Frontend Build
`npm run build` passed. The known Vite large chunk warning remains.

## 46. Warnings
The known SQLAlchemy relationship overlap warnings remain unchanged and are deferred: `RolePermission.role`, `RolePermission.permission`, `UserRole.user`, and `UserRole.role`.

## 47. Files Inspected
Inspected ADR-001 through ADR-009, Sales/POS migration reviews 037, 049, 052, 060, 063, 066, 068, and 070, Sales API, POS services, Sales models, route registry, navigation permissions, query keys, invalidation helpers, Sales service, Sales hooks, and Sales feature pages.

## 48. Files Created
Created `app/services/tenant/pos/sales_query_service.py`, `app/api/tests/test_sales_history_contract.py`, `frontend/src/types/responses/sale-summary.ts`, `frontend/src/types/requests/list-sales-request.ts`, `frontend/src/features/sales/pages/SalesHistoryPage.tsx`, and this review document.

## 49. Files Modified
Modified `app/api/sales.py`, `app/services/tenant/pos/__init__.py`, `frontend/src/services/sales/salesService.ts`, `frontend/src/hooks/queries/sales/useSales.ts`, `frontend/src/hooks/queries/sales/useCreateSale.ts`, `frontend/src/hooks/queries/sales/useRefundSale.ts`, `frontend/src/hooks/queries/sales/index.ts`, `frontend/src/lib/queryKeys.ts`, `frontend/src/lib/queryInvalidation.ts`, `frontend/src/routes/routes.ts`, `frontend/src/routes/permissions.ts`, `frontend/src/navigation/navigation.ts`, `frontend/src/app/router.tsx`, `frontend/src/features/sales/index.ts`, `frontend/src/types/responses/index.ts`, and `frontend/src/types/requests/index.ts`.

## 50. Remaining Blockers
Remaining Sales/POS work includes general Sale detail/read model, historical document snapshots, sale editing/deleting/voiding, suspend/resume, accounting documents, export/reporting workflows, receipt delivery/PDF, payment reversals, prescription workflows, and inventory-facing operational pages.

## 51. Invariants Verified
Sales History is read-only, tenant and branch scoped, permissioned by `sales.read`, server filtered and paginated, cache scoped by branch, linked only to Receipt for row drill-in, and free of direct service/query/storage access in the feature page.

## 52. Rollback Boundary
Rollback removes the Sales History query service, endpoint, tests, frontend list types, service method, hook, route, navigation entry, page, and cache invalidation changes. No database rollback is needed.

## 53. Recommended Next Migration
Recommended next migration: Inventory backend/API layer for pharmacy stock receiving, batch/expiry operations, stock counts, adjustments, and sale-stock integration.
