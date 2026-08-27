# Migration 081 - Stock Adjustment Operational UI

## 1. Migration Purpose

Activate the Migration 080 Stock Adjustment backend contract in the frontend with controlled manual adjustment and Stock Count variance-posting workflows.

## 2. ADR Rules

Stock Adjustment is an Inventory-owned, posted-only, immutable correction document. The UI must not edit/delete/reverse adjustments, create unknown batches, calculate authoritative stock, or redefine Stock Count variances.

## 3. Baseline

- `venv/bin/python -m compileall app`: PASS
- `npx tsc -b --pretty false`: PASS
- `npm run build`: PASS
- Known warning: Vite large chunk warning remains.

## 4. Migration 080 Contract Consumed

The UI consumes `inventory.adjust`, `/api/inventory/stock-adjustments`, `/api/inventory/stock-adjustments/<id>`, and `/api/inventory/stock-counts/<count_id>/adjust`.

## 5. Frontend Foundation

Migration 080 types, services, hooks, query keys, and invalidation helpers were reused. No duplicate Stock Adjustment client contract was created.

## 6. Routes

- `/inventory/stock-adjustments`
- `/inventory/stock-adjustments/new`
- `/inventory/stock-adjustments/:adjustmentId`

## 7. Permission

All Stock Adjustment routes require `inventory.adjust`.

## 8. Inventory Integration

The Inventory page exposes a permission-gated Stock Adjustments action. Activity rows now label `stock_adjustment` and link to adjustment detail when permitted.

## 9. List Page

The list page uses `useStockAdjustments` and server pagination.

## 10. List Filters/Columns

Filters: Warehouse, reason, source, date range. Columns: Adjustment #, Posted, Warehouse, Reason, Source, Items, Posted By, Action.

## 11. Source Display

Manual adjustments display as Manual. Stock Count-sourced adjustments display the server-projected Stock Count reference when available.

## 12. Manual Create Flow

The create page captures Warehouse, reason code, reason notes, notes, current stock row, exact existing batch when required, signed quantity delta, and line reason.

## 13. Branch Readiness

The UI blocks when branch scope is unavailable.

## 14. Warehouse Selection

Warehouse selection uses `useWarehouses`. Backend compatibility was narrowed to allow `inventory.adjust` to list active current-branch Warehouses.

## 15. Stock/Product Selection

Manual adjustments select from current Inventory stock rows via `useInventory`, giving Product and StockBalance context.

## 16. Batch Selection

Batch-tracked or expiry-tracked Products require selecting an existing batch through `useInventoryBatches`. Users never type arbitrary `batch_id`.

## 17. Signed Delta UX

The input is labeled Quantity Adjustment. Positive values increase stock; negative values decrease stock. The UI never asks for New Quantity.

## 18. Positive/Negative Semantics

Positive manual adjustments are not Goods Receipts. Negative manual adjustments are not refunds or supplier returns.

## 19. Reserved-Stock UX

Current reserved values are displayed. Backend remains authoritative for reservation and negative-stock rejection.

## 20. Reasons

Manual reason codes use the verified Migration 080 code set except `stock_count`, which is reserved for the Stock Count endpoint.

## 21. Multiple-Line Behavior

Multiple lines are supported. Duplicate Product+batch identity is blocked client-side and remains blocked server-side.

## 22. Idempotency Lifecycle

Manual and count-derived posting retain a stable idempotency key for retry. Edited manual payloads after an attempted submit get a new key.

## 23. Confirmation

Both workflows use `AlertDialog` before posting.

## 24. Manual Success/Detail

Successful manual posting navigates to immutable adjustment detail using the persisted adjustment id.

## 25. Immutability

Detail is read-only. No edit, delete, repost, reverse, approval, or draft workflow was added.

## 26. Source Navigation

Adjustment detail links to source Stock Count only when the source exists and the user has `inventory.count`.

## 27. Stock Count Post Adjustment Eligibility

The action is shown only when the count is completed, the user has `inventory.adjust`, nonzero variance exists, and no server-projected adjustment link exists.

## 28. Stock Count Confirmation

The confirmation states that posting creates a separate Stock Adjustment, changes inventory quantities, and leaves the Stock Count unchanged.

## 29. Count-Derived Payload Boundary

The frontend sends only count identity plus idempotency/reason metadata. It sends no Product, batch, snapshot, expected, counted, or variance quantities.

## 30. Zero Variance

Zero-variance completed counts show that no stock adjustment is required and do not expose a posting action.

## 31. Already-Adjusted State

Stock Count detail/list payloads now include a nullable adjustment link. Already-adjusted counts show View Adjustment and do not expose a second posting action.

## 32. Stale-Stock Failure

Server rejection is surfaced through normalized error messaging; the UI does not alter count variance or offer force posting.

## 33. Stock Count Invariants

Snapshot, Expected, Physical Count, and Variance remain read-only server values after adjustment posting.

## 34. Inventory Invalidation

The canonical mutation hooks invalidate Inventory stock, batches, movements, Stock Adjustment lists/details, and Stock Count lists/details when sourced from a count.

## 35. Activity Integration

`stock_adjustment` movements appear in Inventory Activity with a human-readable label and permission-aware adjustment detail link.

## 36. Permission Dependencies

Adjustment routes require `inventory.adjust`. Manual creation also consumes current Inventory stock and batch reads; operational roles should include `inventory.read` for full stock context.

## 37. Cost/Valuation Disposition

No cost, valuation, loss/gain, COGS, or journal wording is shown.

## 38. Unknown/Expired Batch Behavior

Unknown batch creation remains unsupported. Expired existing batches remain selectable and are labeled Expired.

## 39. Error Handling

Permission, invalid Warehouse/Product, batch required/not found, duplicate line, negative/reserved-stock violation, duplicate count posting, non-completed count, zero variance, idempotency conflict, and stale-stock errors are surfaced without clearing manual draft lines.

## 40. Draft Preservation

Manual draft inputs remain on failure. No localStorage/sessionStorage draft persistence was added.

## 41. Legacy useAdjustStock Disposition

`useAdjustStock` and `useTransferStock` remain private legacy hook files, are not exported, and are not used by the operational UI.

## 42. Route/Navigation Ownership

Routes live under Inventory. The sidebar was not cluttered with a new top-level item.

## 43. Backend Corrections

No adjustment posting semantics changed. Narrow backend support added: Warehouse list accepts `inventory.adjust`; Stock Count serializers expose nullable adjustment links.

## 44. Local DB State

Source head is `e5f6a7b8c9d0`. `flask db current` could not run because local PostgreSQL is down/not accepting connections.

## 45. Runtime Smoke

No live operational stock correction was posted because local PostgreSQL is unavailable and the brief warns against creating real corrections in non-disposable data.

## 46. Backend Tests

Adjacent Inventory/backend tests: `151 passed, 4 known SQLAlchemy overlap warnings`.

## 47. Frontend TypeScript

`npx tsc -b --pretty false`: PASS.

## 48. Frontend Build

`npm run build`: PASS.

## 49. Warnings

Known SQLAlchemy overlap warnings remain separate technical debt. Known Vite large chunk warning remains.

## 50. Files Inspected

Inventory pages, Stock Count pages, route registry, route permissions, Migration 080 hooks/types/services, Stock Count serializers/services, Warehouse API, and Stock Adjustment contract tests.

## 51. Files Created

- `frontend/src/features/inventory/pages/StockAdjustmentsPage.tsx`
- `frontend/src/features/inventory/pages/CreateStockAdjustmentPage.tsx`
- `frontend/src/features/inventory/pages/StockAdjustmentDetailPage.tsx`
- `frontend/docs/architecture/reviews/MIGRATION-081-STOCK-ADJUSTMENT-OPERATIONAL-UI.md`

## 52. Files Modified

Routes, route permissions, inventory feature exports, Inventory page, Stock Count detail page, Stock Count frontend types, Warehouse API, Stock Count serializer/service, and focused backend tests.

## 53. Remaining Adjustment Blockers

Manual UI currently targets existing Inventory stock context. Positive creation for non-batch Products without a StockBalance remains backend-supported but not exposed in this first UI because it would require a broader Product-search permission contract.

## 54. Invariants Verified

The UI uses `inventory.adjust`, signed deltas, exact batch selection, server-derived Stock Count posting, immutable detail, idempotency hooks, Inventory invalidation, Activity visibility, no financial wording, no Procurement activation, zero TypeScript errors, and successful production build.

## 55. Rollback Boundary

Rollback is frontend route/page removal plus the narrow Warehouse/Stock Count projection compatibility edits. No Alembic revision was added.

## 56. Recommended Next Migration

Migration 082 - Sales/POS operational slice hardening toward pharmacy inventory integration.
