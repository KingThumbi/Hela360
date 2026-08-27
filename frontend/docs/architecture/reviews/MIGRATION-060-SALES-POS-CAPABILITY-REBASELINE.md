# Migration 060 - Sales/POS Capability Rebaseline

## 1. Purpose

Migration 060 rebaselines the current Sales/POS backend runtime contract before
any POS page activation.

This migration is inspection-first and backend-contract-first. It does not
activate POS, Sales History, receipts, shift UI, Sales query reads, or new
frontend service methods.

## 2. ADR Rules Applied

- ADR-001: the frontend Sales facade remains limited to verified business
  operations.
- ADR-002: unsupported Sales query hooks remain non-operational.
- ADR-003: no Sales query keys or invalidation targets were invented.
- ADR-004: current canonical Sales types were compared against backend
  serializers and request payloads.
- ADR-005: the registered refund route had a narrow runtime defect corrected at
  the backend boundary.
- ADR-006: Sale ownership is branch-scoped and tenant-scoped.
- ADR-007: registered route decorators are the authorization source of truth.
- ADR-008: no dormant frontend Sales page was activated.
- ADR-009: new contract test naming follows the existing test convention.
- ADR-010: POS checkout and refund are workflows; missing workflow endpoints
  are documented rather than fabricated.

## 3. Starting Baseline

Baseline commands:

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

Existing frontend warning remains:

```text
Some chunks are larger than 500 kB after minification.
```

## 4. Registered Sales Routes

Command:

```bash
FLASK_APP=app:create_app venv/bin/flask routes | rg -i 'sales|refund|shift|till|payment'
```

Registered Sales/POS routes:

| Operation | Method | Path | Decorator | Service/helper | Envelope | Status |
| --- | --- | --- | --- | --- | --- | --- |
| POS checkout | POST | `/api/sales/checkout` | `@require_permission("sales.create")` | route-local helpers | `{ ok, message, item, shift_id }` | Partially implemented |
| Sale refund | POST | `/api/sales/<sale_id>/refund` | `@require_permission("sales.refund")` | `RefundService.create_refund` | `{ ok, message, refund }` | Verified operational after narrow fix |

Customer routes are also duplicated inside `app/api/sales.py` and register under
the Sales blueprint endpoint namespace. They are Customer capability, not
Sales/POS capability, and should be cleaned up separately.

No registered routes exist for:

- `GET /api/sales`
- `GET /api/sales/<id>`
- complete sale
- suspend sale
- resume sale
- void sale
- receipt
- list payment methods
- till selection
- open till shift
- close till shift
- cashier reconciliation

`app/api_sales.py` contains additional list/detail/shift code, but that
blueprint is not registered by the current application factory and is therefore
not operational API truth.

## 5. Sale Model

Table: `sales`

Persistent fields:

- `id`
- `tenant_id`
- `branch_id`
- `till_id`
- `shift_id`
- `warehouse_id`
- `customer_id`
- `sale_number`
- `sale_date`
- `sale_channel`
- `status`
- `subtotal`
- `discount_amount`
- `tax_amount`
- `total_amount`
- `paid_amount`
- `balance_due`
- `notes`
- `cashier_id`
- `refunded_amount`
- `refund_status`
- `created_at`
- `updated_at`

Requested field verification:

| Concept | Actual field |
| --- | --- |
| id | `id` |
| tenant | `tenant_id` |
| branch | `branch_id` |
| customer | `customer_id`, nullable |
| reference | `sale_number` |
| status | `status` |
| subtotal | `subtotal` |
| discount | `discount_amount` |
| tax | `tax_amount` |
| total | `total_amount` |
| paid amount | `paid_amount` |
| balance | `balance_due` |
| created by | `cashier_id` |
| completed by | no separate field |
| timestamps | `sale_date`, `created_at`, `updated_at` |

## 6. SaleItem Model

Table: `sale_items`

Fields:

- `id`
- `sale_id`
- `product_id`
- `batch_id`
- `quantity`
- `unit_price`
- `discount_amount`
- `tax_amount`
- `line_total`
- `cost_of_sale`
- `is_returned`

There is a `batch_id` field, but checkout does not choose a batch.

## 7. SalePayment Model

Table: `sale_payments`

Fields:

- `id`
- `sale_id`
- `payment_method_id`
- `amount`
- `reference_number`
- `paid_at`
- `received_by`

Multiple payments are supported during checkout because `payments` is an array
and the route persists one `SalePayment` per entry.

## 8. Refund Models

`SaleRefund` fields:

- `id`
- `tenant_id`
- `sale_id`
- `branch_id`
- `warehouse_id`
- `till_id`
- `cashier_id`
- `customer_id`
- `refund_number`
- `status`
- `refund_subtotal`
- `refund_discount_amount`
- `refund_tax_amount`
- `refund_total_amount`
- `stock_returned`
- `reason`
- `notes`
- `created_at`
- `updated_at`

`SaleRefundItem` fields:

- `id`
- `created_at`
- `tenant_id`
- `refund_id`
- `sale_id`
- `sale_item_id`
- `product_id`
- `batch_id`
- `quantity`
- `unit_price`
- `discount_amount`
- `tax_amount`
- `line_total`
- `return_to_stock`
- `condition_note`

## 9. SaleActionRequest Disposition

Table: `sale_action_requests`

Fields:

- `id`
- `tenant_id`
- `sale_id`
- `action_type`
- `status`
- `requested_by`
- `approved_by`
- `rejected_by`
- `request_reason`
- `decision_reason`
- `request_payload`
- `requires_approval`
- `approved_at`
- `rejected_at`
- `executed_at`
- `created_at`
- `updated_at`

Classification: `Partially implemented`.

Evidence: `SaleApprovalService` can create refund/void requests and process
approval/rejection in service code, but no registered API route exposes this
workflow. Its admin check is also incomplete and should not be treated as a
go-live approval boundary.

## 10. Branch Ownership

Sale ownership:

```text
tenant + branch
```

Evidence:

- `Sale.branch_id` is persisted and non-nullable.
- checkout derives `branch_id` from authenticated identity, not client payload.
- refund compares sale branch to authenticated branch.
- client cannot provide sale branch during checkout.
- a selected frontend branch must be established before future POS activation.
- Sales cannot safely operate tenant-wide without branch.

Future Sales cache contract should conceptually be:

```text
["tenant", tenantId, "branch", branchId, "sales", ...]
```

No query keys were changed in this migration.

## 11. Create-Sale Contract

Registered route:

```text
POST /api/sales/checkout
```

Request body:

- `warehouse_id`, required
- `till_id`, required
- `customer_id`, optional
- `notes`, optional
- `items`, required non-empty array
- `payments`, array

Item fields:

- `product_id` or `barcode`, one required
- `quantity`, required positive decimal
- `unit_price`, optional if Product has sale price
- `discount_amount`, optional non-negative decimal
- `tax_amount`, optional non-negative decimal

Payment fields:

- `payment_method_id`, required
- `amount`, required positive decimal
- `reference`, optional

Supported by evidence:

| Capability | Status |
| --- | --- |
| `customer_id` | Verified optional, tenant-scoped |
| `items` | Verified required |
| `product_id` | Verified |
| `barcode` | Verified through `ProductCode` |
| `quantity` | Verified positive decimal |
| `unit_price` | Partially implemented |
| discount | Partially implemented |
| tax | Partially implemented |
| payment | Verified as part of checkout |
| `payment_method_id` | Verified tenant-scoped |
| branch | Derived from identity |
| warehouse | Client supplies id, backend validates tenant only |
| prescription reference | Unsupported |

## 12. Pricing Authority

Classification:

```text
client supplies and server validates, else server derives from Product
```

Actual behavior:

- if item `unit_price` is provided, backend accepts any non-negative value;
- otherwise backend tries Product fields such as `default_sale_price`;
- `Product.min_sale_price` exists but is not enforced;
- discounts are accepted if non-negative and not greater than line subtotal;
- no discount permission check was found;
- no price override audit was found.

Risk:

```text
Critical POS contract gap for go-live.
```

A real POS workflow needs server-side price authority, min-price enforcement,
and auditable override permissions.

## 13. Totals Authority

Backend calculates:

- line subtotal;
- line total;
- sale subtotal;
- discount total;
- tax total;
- grand total;
- paid amount from payment rows;
- balance due.

Frontend does not send sale totals. This is a good boundary.

Remaining risk: backend trusts client-provided unit price, discount amount, and
tax amount.

## 14. Payment Contract

Payment is part of checkout.

Capabilities:

- multiple payments: verified;
- single payment: supported as a subset;
- separate add/list/get SalePayment endpoints: unsupported;
- refund payment: implemented as a negative `SalePayment` using the first
  original sale payment method;
- transaction/reference field: `reference_number`;
- received by: `received_by`;
- paid timestamp: `paid_at`.

## 15. Payment Method API Disposition

Payment methods are tenant-owned dynamic records:

- `payment_methods.tenant_id`
- `code`
- `name`
- `method_type`
- `is_active`

Frontend ability to fetch active payment methods:

```text
Missing endpoint
```

Seed/bootstrap infrastructure can create `cash`, `mpesa`, `card`, and `bank`,
but no registered API route was found for POS to list them. POS must not
hardcode a frontend enum.

## 16. Customer Linkage

`Sale.customer_id` is nullable.

Classification:

```text
Partially implemented
```

Evidence:

- anonymous/walk-in sale is possible by omitting `customer_id`;
- if supplied, checkout validates Customer id within the same tenant;
- refund carries through the original sale customer id;
- there is no explicit walk-in customer record semantic.

## 17. Product Validation

Checkout verifies:

- product exists by `product_id` and tenant;
- product exists by barcode via `ProductCode` and tenant;
- quantity is positive;
- sufficient stock balance exists;
- stock is sufficient.

Checkout does not verify:

- `Product.is_active`;
- `Product.requires_prescription`;
- `Product.track_inventory`;
- `Product.allow_negative_stock`;
- `Product.track_batches`;
- `Product.track_expiry`;
- min sale price;
- tax authority.

## 18. Inventory Effects

Classification:

```text
Partial
```

Checkout:

- checks `stock_balances`;
- prevents negative stock by requiring sufficient `quantity_on_hand`;
- reduces `quantity_on_hand`;
- updates `quantity_available` when present;
- creates an `InventoryMovement` with `movement_type="sale"`;
- uses tenant, branch, warehouse, product, sale reference, and cashier.

Gaps:

- no batch selection;
- no batch quantity decrement;
- no FEFO/FIFO;
- no `allow_negative_stock` branch;
- no non-stock product handling;
- no sale-to-inventory integration tests before this migration.

Refund:

- validates refundable quantity;
- can create `sale_refund_return` inventory movement when `return_to_stock`;
- does not update `StockBalance.quantity_on_hand`;
- therefore refund stock restoration is movement-only, not fully operational
  stock balance restoration.

## 19. Batch And Expiry

Classification:

```text
Persistence only
```

Evidence:

- `SaleItem.batch_id` exists;
- `SaleRefundItem.batch_id` exists;
- `InventoryBatch` stores `batch_number`, `expiry_date`, quantity and status;
- checkout does not select batch;
- checkout stock deduction does not decrement batch quantity;
- no FEFO/FIFO behavior was found.

Current Sales cannot safely operate against pharmacy batch/expiry stock.

## 20. Prescription Behavior

Classification:

```text
Unsupported
```

Evidence:

- `Product.requires_prescription` exists;
- checkout does not inspect it;
- request has no prescription reference;
- Sale/SaleItem do not persist prescription reference.

## 21. Sale Lifecycle

Actual backend values observed:

- model default: `completed`;
- checkout writes: `paid` or `partially_paid`;
- refund writes: `partially_refunded` or `refunded`;
- void helper writes: `voided`;
- refund status values: `not_refunded`, `partially_refunded`, `refunded`.

Only checkout and direct refund are registered routes.

## 22. Complete/Suspend/Resume/Void

| Operation | Classification | Evidence |
| --- | --- | --- |
| complete | unsupported | no registered route |
| suspend | unsupported | no registered route |
| resume | unsupported | no registered route |
| void | service-only | approval helper can void, no registered route |

## 23. Refund Contract

Registered route:

```text
POST /api/sales/<sale_id>/refund
```

Request:

- `items`, required non-empty array;
- `reason`, optional;
- `notes`, optional.

Item request:

- `sale_item_id`, required;
- `quantity`, required positive decimal;
- `return_to_stock`, optional default true;
- `condition_note`, optional.

Verified behavior:

- tenant isolation;
- branch isolation;
- full and partial refund logic;
- repeated refund quantity protection;
- max refundable amount protection based on paid amount;
- refund item persistence;
- refund payment as negative `SalePayment`;
- sale `refunded_amount` update;
- sale/refund status update.

Gaps:

- refund route had a broken service call signature and was fixed narrowly;
- no refund receipt endpoint;
- refund stock return does not update stock balance;
- direct refund does not require approval workflow.

## 24. Sale Read Capability

| Capability | Status |
| --- | --- |
| list sales | Backend-blocked |
| get sale | Backend-blocked |
| sale history | Backend-blocked |
| sales search | Backend-blocked |

`app/api_sales.py` has unregistered read code and is not operational truth.

## 25. Receipt Capability

Classification:

```text
Unsupported
```

No registered receipt JSON, HTML, printable, or PDF endpoint was found.

## 26. Till Model

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

Classification: `Persistence only`.

No registered API route exists to list/select/create tills.

## 27. TillShift Model

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

Checkout requires an open `TillShift` for the authenticated cashier and till.

Classification: `Partially implemented`.

No registered route exists to open or close a `TillShift`.

## 28. Shift Model

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

Classification: `Persistence only`.

`Sale.shift_id` points to `shifts.id`, but checkout returns the open
`TillShift.id` and does not assign `Sale.shift_id`. This is a high-priority
architecture ambiguity.

## 29. Till/Shift Routes

No registered route was found for:

- list tills;
- select till;
- open shift;
- close shift;
- current shift;
- shift report;
- cashier reconciliation.

`app/api_sales.py` contains unregistered shift code.

## 30. Sale-To-Shift Linkage

Sale stores:

- `shift_id`, nullable;
- `till_id`, non-null;
- `cashier_id`, non-null.

Checkout currently:

- requires open `TillShift`;
- returns `shift_id` as `TillShift.id`;
- does not persist that id into `Sale.shift_id`.

Classification:

```text
Partially implemented with reconciliation limitation
```

## 31. Audit Behavior

Checkout creates:

- Sale;
- SaleItem;
- SalePayment;
- InventoryMovement.

Refund creates:

- SaleRefund;
- SaleRefundItem;
- negative SalePayment;
- optional InventoryMovement.

No `AuditLog` writes were found in checkout/refund. `SaleActionRequest` is an
approval workflow persistence model, not a complete audit trail.

## 32. Authorization Matrix

| Operation | Backend permission | Registered route | Status |
| --- | --- | --- | --- |
| checkout sale | `sales.create` | yes | Partially implemented |
| refund sale | `sales.refund` | yes | Verified operational after fix |
| list sales | none verified | no | Backend-blocked |
| get sale | none verified | no | Backend-blocked |
| receipt | none verified | no | Unsupported |
| void sale | none verified | no | Service-only |
| suspend sale | none verified | no | Unsupported |
| resume sale | none verified | no | Unsupported |
| open/close shift | none verified | no | Backend-blocked |
| list payment methods | none verified | no | Backend-blocked |

Permission naming drift remains: frontend navigation references `sales.view`,
`sales.pos`, and `sales.void`, while backend registered routes use
`sales.create` and `sales.refund`.

## 33. Frontend Sales Inventory

Frontend files inspected:

- `frontend/src/features/sales/pages/SalesPage.tsx`: zero-byte placeholder.
- `frontend/src/services/sales/salesService.ts`: public `createSale` and
  `refundSale` only.
- `frontend/src/hooks/queries/sales/index.ts`: public `useSales`, `useSale`,
  `useCreateSale`, `useRefundSale`.
- `useSales` and `useSale`: explicitly reject unsupported read operations.
- private hooks for payments, receipts, dashboard, complete, suspend, resume,
  and void explicitly reject unsupported behavior.
- navigation has POS, Sales History, and Refund entries, but router does not
  activate those operational pages.

## 34. Frontend Service Contract

Public Sales facade remains:

```text
createSale
refundSale
```

No methods were added in Migration 060.

## 35. Canonical Type Drift

Frontend canonical types mostly match current serializers:

- `Sale`
- `SaleItem`
- `SalePayment`
- `SaleRefund`
- `CreateSaleRequest`
- `RefundSaleRequest`
- `SaleStatus`

Known drift:

- `Sale.shift_id` is persisted but not present on frontend `Sale`;
- `SaleItem.batch_id`, `cost_of_sale`, and `is_returned` are persisted but not
  in frontend `SaleItem`;
- `SaleRefund` route returns only summary fields, while the type includes
  optional persisted fields;
- `SaleStatus` contains frontend-friendly values not all verified as route
  transitions.

No type changes were made.

## 36. Query-Key Disposition

No Sales query keys were added or changed.

Because no registered Sales read APIs exist, future `createSale` and
`refundSale` invalidation should not fabricate Sales list/detail refreshes.
Potential future invalidation targets remain dependent on future backend work:

- branch-scoped Sales history;
- branch/warehouse stock balances;
- customer history;
- dashboard summaries;
- finance/cash reconciliation.

Product catalogue invalidation is not a substitute for inventory balance
invalidation.

## 37. POS Workflow Matrix

| Workflow step | Status |
| --- | --- |
| Select branch | Partial |
| Select/open till | Missing |
| Open cashier shift | Missing registered route |
| Find product | Verified via product id/barcode |
| Select customer/walk-in | Partial |
| Add SaleItem | Verified |
| Validate price | Partial |
| Validate stock | Partial |
| Select batch | Missing |
| Validate prescription | Missing |
| Calculate totals | Verified server-side |
| Select payment method | Missing fetch API |
| Record payment | Verified during checkout |
| Complete sale | Checkout only; no separate complete route |
| Deduct stock | Partial |
| Generate receipt | Missing |
| Refund sale | Verified after fix |
| Restore stock | Partial movement-only |
| Close shift | Missing registered route |
| Reconcile till | Missing |

## 38. Blockers

P0 - before any real sale:

- active branch context must be mandatory in the frontend;
- payment method listing endpoint is missing;
- till listing/selection endpoint is missing;
- open cashier `TillShift` lifecycle endpoint is missing;
- price authority is insufficient because client unit price can override;
- product active/min-price/prescription flags are not enforced;
- stock deduction is not batch-aware.

P1 - before Dimples go-live:

- FEFO/FIFO batch and expiry selection;
- receipt API;
- Sale list/detail/history API;
- refund stock-balance restoration;
- shift/till reconciliation model decision;
- audit trail;
- permission naming alignment;
- direct refund versus approval workflow policy.

P2 - after first internal prototype:

- dashboards and summaries;
- sales search filters;
- receipt PDF/print variants;
- richer refund UI/reporting;
- payment method administration UI.

## 39. Real DB Configuration Counts

Requested read-only counts were attempted for:

- `payment_methods`
- `tills`
- `till_shifts`
- `shifts`
- `warehouses`
- `stock_balances`
- `inventory_batches`

Result in this Codex shell:

```text
BLOCKED - PostgreSQL 16/main down, localhost:5432 no response.
```

No live business data was inserted.

## 40. First-Tenant Readiness Implications

Before POS can operate, the first tenant must have:

- active branch;
- active warehouse;
- active till;
- open cashier till shift;
- active payment methods;
- cashier user with `sales.create`;
- products;
- stock balances;
- eventually batch/expiry stock for pharmacy use.

Migration 060 did not seed any of this data.

## 41. Tests Run

Backend:

```bash
venv/bin/python -m compileall app
venv/bin/python -m pytest app/api/tests/test_sales_pos_contract.py -q
venv/bin/python -m pytest app/api/tests/test_sales_pos_contract.py app/api/tests/test_customers_contract.py app/api/tests/test_products_list_contract.py app/services/tenant/procurement/tests/test_supplier_contract.py app/services/tenant/auth/tests/test_current_session_service.py app/services/tenant/auth/tests/test_current_session_route.py -q
venv/bin/python -m pytest app/services/tenant/auth/tests -q
```

Results:

```text
Sales POS contract: 3 passed
Targeted regression: 41 passed
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

## 42. Files Inspected

- ADR-001 through ADR-010
- Migration 036, 037, 038, 044, 048, 049, 052, 059 reports
- `app/api/sales.py`
- `app/api_sales.py`
- `app/models/pos.py`
- `app/models/shift.py`
- `app/models/inventory.py`
- `app/models/product.py`
- `app/services/tenant/pos/refund_service.py`
- `app/services/tenant/pos/sale_approval_service.py`
- `app/auth/permissions.py`
- `frontend/src/services/sales/`
- `frontend/src/hooks/queries/sales/`
- `frontend/src/types/entities/sale*.ts`
- `frontend/src/types/requests/*sale*.ts`
- `frontend/src/navigation/navigation.ts`
- `frontend/src/routes/routes.ts`

## 43. Files Created

- `app/api/tests/test_sales_pos_contract.py`
- `frontend/docs/architecture/reviews/MIGRATION-060-SALES-POS-CAPABILITY-REBASELINE.md`

## 44. Files Modified

- `app/api/sales.py`
- `app/services/tenant/pos/sale_approval_service.py`

The backend modifications were limited to wiring the registered refund route
and approval refund execution path to the current `RefundService.create_refund`
identity-based contract.

## 45. Warnings

Known SQLAlchemy mapper overlap warnings remain:

- `RolePermission.role`
- `RolePermission.permission`
- `UserRole.user`
- `UserRole.role`

Known Vite large chunk warning remains.

## 46. Architecture Invariants

- No unsupported Sales capability was activated.
- Registered routes are the only operational API truth.
- Sale ownership is documented as tenant + branch.
- Pricing authority and risks are documented.
- Payment method ownership is documented.
- Inventory side effects are documented as partial.
- Batch/expiry status is documented as persistence only.
- Prescription enforcement is documented as unsupported.
- Till/shift ambiguity is documented.
- Frontend Sales service was not expanded.
- No Sales query keys were invented.
- No POS route was activated.
- TypeScript remains at zero errors.
- Production frontend build remains successful.

## 47. Rollback Boundary

Rollback for Migration 060 is limited to:

- remove `app/api/tests/test_sales_pos_contract.py`;
- revert the `RefundService.create_refund` call-site updates;
- remove this report.

No database migration or frontend runtime activation was introduced.

## 48. Recommended Next Migration Sequence

1. Migration 061 - Payment Method And Till Read API Boundary.
2. Migration 062 - TillShift Lifecycle Contract.
3. Migration 063 - POS Checkout Contract Hardening: price authority, product
   active checks, prescription checks, and branch/warehouse/till consistency.
4. Migration 064 - Inventory Batch/Expiry Sale Deduction Contract.
5. Migration 065 - Sales Read/Receipt API.
6. Migration 066 - POS Operational Page Activation.
