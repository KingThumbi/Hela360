# Migration 036 - Sales Type Ownership

## 1. Migration Purpose

Migration 036 establishes canonical frontend ownership for verified
Sales-related shared types and records unsupported frontend Sales assumptions.

This migration is inspection-first. Source changes were limited to shared type
ownership and transitional type barrels. No Sales service runtime method, query
key, invalidation helper, feature behavior, or backend source was changed.

## 2. ADR Rules Applied

- ADR-001: services consume shared DTOs and entities rather than owning them.
- ADR-002: hooks may consume shared types, but unsupported operations are not
  made real by type creation alone.
- ADR-003: Sales query keys and invalidation remain unchanged.
- ADR-004: entities live under `src/types/entities`, request DTOs under
  `src/types/requests`, and runtime values under `src/types/enums`.
- ADR-005: no error behavior was changed.
- ADR-006: tenant, branch, cashier, and warehouse fields follow verified
  backend ownership.
- ADR-008: `src/types/sales` is retained only as a transitional re-export
  boundary.
- ADR-009: new files use kebab-case naming.
- ADR-010: workflow/event behavior remains deferred.

## 3. Initial Sales Diagnostics

Frontend compiler baseline before this migration:

```text
98 TypeScript errors
```

Sales diagnostics included:

- missing request exports: `CompleteSaleRequest`, `SuspendSaleRequest`,
  `ResumeSaleRequest`, `VoidSaleRequest`, `RefundSaleRequest`
- missing entity exports: `Receipt`, `SaleRefund`, `SalesDashboard`
- service method mismatches: `createSale`, `completeSale`, `refundSale`,
  `resumeSale`, `suspendSale`, `voidSale`, `getSale`, `listSales`,
  `getReceipt`, `listReceipts`, `getSalePayment`, `listSalePayments`,
  `getDashboard`
- query-key mismatches: `QUERY_KEYS.sales.sale`, `QUERY_KEYS.sales.sales`,
  `QUERY_KEYS.sales.receipts(params)`
- unused import: `SalePayment` in `useSalePayments`
- service barrel mismatches: empty decomposed Sales service files exported as
  concrete services
- unsupported response projection imports: `DailySalesSummary`,
  `CashierSummary`, and `SalesDashboard`

## 4. Backend Sales Models Verified

Verified in `app/models/pos.py` and the initial schema migration:

| Model | Table | Ownership | API exposure |
| --- | --- | --- | --- |
| `Sale` | `sales` | tenant, branch, warehouse, till, cashier; optional customer | serialized by checkout helper |
| `SaleItem` | `sale_items` | belongs to sale and product; optional batch | nested inside serialized sale |
| `SalePayment` | `sale_payments` | belongs to sale and payment method; received by user | nested inside serialized sale |
| `PaymentMethod` | `payment_methods` | tenant-owned dynamic records | referenced by id in checkout |
| `SaleRefund` | `sale_refunds` | tenant, sale, branch, warehouse, till, cashier; optional customer | summarized by refund route |
| `SaleRefundItem` | `sale_refund_items` | belongs to refund, sale, sale item, product; optional batch | not directly serialized by route |
| `SaleActionRequest` | `sale_action_requests` | tenant and sale workflow approval request | service evidence only; no route verified here |

Primary keys are string UUIDs from `UUIDPrimaryKeyMixin`.

## 5. Backend Sales Routes Verified

Registered routes in `app/api/sales.py`:

| Operation | Route | Method | Permission | Envelope | Confidence |
| --- | --- | --- | --- | --- | --- |
| Checkout sale | `/api/sales/checkout` | `POST` | `sales.create` | `{ ok, message, item, shift_id }` | Confirmed |
| Refund sale | `/api/sales/<sale_id>/refund` | `POST` | `sales.refund` | `{ ok, message, refund }` | Confirmed |

Unsupported or insufficient route evidence:

- list sales
- get sale
- update draft sale
- complete sale
- suspend sale
- resume sale
- void sale as a registered API route
- list sale payments
- get sale payment
- add sale payment
- get receipt
- list receipts
- sales dashboard

Filtering and summary helper functions exist in `app/api/sales.py`, and void
execution helper code exists behind `SaleApprovalService`, but no registered
route was verified for those frontend hook assumptions.

## 6. Serializer Shapes

Verified `Sale` serializer fields:

- `id`
- `tenant_id`
- `sale_number`
- `status`
- `branch_id`
- `warehouse_id`
- `till_id`
- `customer_id`
- `cashier_id`
- `subtotal`
- `discount_amount`
- `tax_amount`
- `total_amount`
- `paid_amount`
- `balance_due`
- `refunded_amount`
- `refund_status`
- `refund_count`
- `refundable_amount`
- `sold_at`
- `created_at`
- `updated_at`
- `items`
- `payments`

Decimal values are serialized as strings.

Verified `SaleItem` serializer fields:

- `id`
- `sale_id`
- `product_id`
- `product_name`
- `sku`
- `quantity`
- `unit_price`
- `discount_amount`
- `tax_amount`
- `line_total`
- `created_at`

Verified `SalePayment` serializer fields:

- `id`
- `sale_id`
- `payment_method_id`
- `amount`
- `reference`
- `paid_at`
- `received_by`
- `created_at`
- `notes`

Verified refund route result fields:

- `id`
- `refund_number`
- `status`
- `refund_total_amount`
- `stock_returned`

## 7. Request Schemas

No backend schema module was found for Sales. Request contracts are route-local.

Verified checkout body:

- `warehouse_id`, required
- `till_id`, required
- `customer_id`, optional
- `notes`, optional
- `items`, required non-empty array
- `payments`, array

Verified checkout item fields:

- `product_id` or `barcode`, one required
- `quantity`, required positive decimal
- `unit_price`, optional when product price exists
- `discount_amount`, optional non-negative decimal
- `tax_amount`, optional non-negative decimal

Verified checkout payment fields:

- `payment_method_id`, required
- `amount`, required positive decimal
- `reference`, optional

Verified refund route:

- path parameter: `sale_id`
- body `items`, required non-empty array
- body `reason`, optional for direct refund route
- body `notes`, optional

Verified refund item fields:

- `sale_item_id`, required
- `quantity`, required positive decimal
- `return_to_stock`, optional, defaults true
- `condition_note`, optional

## 8. Frontend Contracts Found

Existing canonical files found and realigned:

- `frontend/src/types/entities/sale.ts`
- `frontend/src/types/entities/sale-item.ts`
- `frontend/src/types/entities/sale-payment.ts`
- `frontend/src/types/requests/create-sale-request.ts`
- `frontend/src/types/requests/create-sale-item-request.ts`
- `frontend/src/types/requests/create-sale-payment-request.ts`
- `frontend/src/types/requests/update-sale-request.ts`
- `frontend/src/types/enums/sale-status.ts`
- `frontend/src/types/enums/payment-method.ts`

New verified files:

- `frontend/src/types/entities/sale-refund.ts`
- `frontend/src/types/requests/refund-sale-request.ts`

Compatibility files retained:

- `frontend/src/types/sales/entities.ts`
- `frontend/src/types/sales/requests.ts`
- `frontend/src/types/sales/enums.ts`
- `frontend/src/types/sales/responses.ts`
- `frontend/src/types/sales/index.ts`

## 9. Duplicate and Unsupported Definitions

The pre-existing Sales contracts used camelCase frontend fields and invented
uppercase status/payment values. They were replaced with canonical snake_case
contracts matching the verified backend serializer and request payloads.

`src/types/sales/` contained empty placeholders. It now re-exports canonical
types only and does not define competing Sales contracts.

`legacySalesService` still imports unsupported `DailySalesSummary` and
`CashierSummary` through `@/types/domains/sales`; this is documented as a
service/projection backlog item, not fixed here.

## 10. Canonical Dispositions

`Sale`: canonical entity under `src/types/entities/sale.ts`.

`SaleItem`: canonical nested entity/value object under
`src/types/entities/sale-item.ts`; verified as nested inside Sale responses, not
as independently addressable.

`SalePayment`: canonical nested payment record under
`src/types/entities/sale-payment.ts`; it does not replace any Finance payment
type.

`Receipt`: unsupported. No stable receipt JSON payload or registered receipt
route was verified. No `Receipt` type was created.

`SaleRefund`: canonical refund result entity under
`src/types/entities/sale-refund.ts`, based on the verified refund route result
and persisted model evidence.

`CreateSaleRequest`: canonical checkout request under
`src/types/requests/create-sale-request.ts`.

`UpdateSaleRequest`: retained as an unsupported compatibility type using
`Partial<CreateSaleRequest>`. No update route was verified.

`RefundSaleRequest`: canonical refund request under
`src/types/requests/refund-sale-request.ts`.

`CompleteSaleRequest`, `SuspendSaleRequest`, `ResumeSaleRequest`, and
`VoidSaleRequest`: unsupported. No request DTOs were created.

`SalesDashboard`: unsupported. No verified dashboard endpoint or response
projection was found.

## 11. Status and Runtime Values

Verified Sales status values include:

- `completed`
- `paid`
- `partially_paid`
- `voided`
- `partially_refunded`
- `refunded`

Canonical runtime values:

```text
frontend/src/types/enums/sale-status.ts::SALE_STATUSES
```

`PaymentMethod` is not a finite runtime enum. The backend stores tenant-owned
payment method records and checkout accepts `payment_method_id`. The
compatibility type is therefore `string`.

## 12. Barrels Updated

Updated:

- `frontend/src/types/entities/index.ts`
- `frontend/src/types/requests/index.ts`
- `frontend/src/types/enums/index.ts`
- `frontend/src/types/sales/entities.ts`
- `frontend/src/types/sales/requests.ts`
- `frontend/src/types/sales/enums.ts`
- `frontend/src/types/sales/responses.ts`
- `frontend/src/types/sales/index.ts`

No Sales service barrel was changed.

## 13. Files Inspected

Backend:

- `app/models/pos.py`
- `app/models/__init__.py`
- `app/api/sales.py`
- `app/services/tenant/pos/refund_service.py`
- `app/services/tenant/pos/sale_approval_service.py`
- `app/services/tenant/pos/`
- `app/schemas/`
- `app/serializers/`
- `app/auth/permissions.py`
- `migrations/versions/19b1ccd035ac_initial_schema.py`

Frontend:

- `frontend/src/types/entities/`
- `frontend/src/types/requests/`
- `frontend/src/types/responses/`
- `frontend/src/types/enums/`
- `frontend/src/types/domains/sales.ts`
- `frontend/src/types/sales/`
- `frontend/src/services/sales/`
- `frontend/src/hooks/queries/sales/`
- `frontend/src/features/sales/`
- `frontend/src/features/finance/`
- `frontend/src/api/endpoints.ts`
- `frontend/src/lib/queryKeys.ts`
- `frontend/src/lib/queryInvalidation.ts`

Architecture:

- ADR-001 through ADR-006
- ADR-008 through ADR-010
- `FRONTEND_ARCHITECTURAL_BASELINE.md`
- `ADR_COMPLIANCE_MATRIX.md`
- `CANONICAL_FRONTEND_ARCHITECTURE.md`
- `MIGRATION-001-TYPE-FOUNDATION.md`

## 14. Files Created

- `frontend/src/types/entities/sale-refund.ts`
- `frontend/src/types/requests/refund-sale-request.ts`
- `frontend/docs/architecture/reviews/MIGRATION-036-SALES-TYPE-OWNERSHIP.md`

## 15. Files Modified

- `frontend/src/types/entities/sale.ts`
- `frontend/src/types/entities/sale-item.ts`
- `frontend/src/types/entities/sale-payment.ts`
- `frontend/src/types/entities/index.ts`
- `frontend/src/types/requests/create-sale-request.ts`
- `frontend/src/types/requests/create-sale-item-request.ts`
- `frontend/src/types/requests/create-sale-payment-request.ts`
- `frontend/src/types/requests/update-sale-request.ts`
- `frontend/src/types/requests/index.ts`
- `frontend/src/types/enums/sale-status.ts`
- `frontend/src/types/enums/payment-method.ts`
- `frontend/src/types/enums/index.ts`
- `frontend/src/types/sales/entities.ts`
- `frontend/src/types/sales/requests.ts`
- `frontend/src/types/sales/responses.ts`
- `frontend/src/types/sales/enums.ts`
- `frontend/src/types/sales/index.ts`

## 16. Compiler Errors

Before:

```text
98 TypeScript errors
```

After:

```text
96 TypeScript errors
```

Net reduction:

```text
2 errors
```

Removed Sales diagnostics:

- missing `SaleRefund` export from `@/types/entities`
- missing `RefundSaleRequest` export from `@/types/requests`

## 17. Build Verification

Commands run:

```bash
npx tsc -b --pretty false
npm run build
```

`npx tsc -b --pretty false` reports 96 remaining TypeScript errors.

`npm run build` exits with code 2 because `tsc -b` still fails on the remaining
global backlog. Vite bundling does not run.

## 18. Newly Exposed Diagnostics

No new diagnostics were introduced by this migration.

The remaining Sales diagnostics are pre-existing service/query/projection
backlog and now exclude the verified refund type missing-export errors.

## 19. Remaining Sales Blockers

- `salesService` facade reconstruction remains unresolved.
- Empty decomposed service modules are still exported as if implemented.
- `createSale` should be reconciled with the verified checkout route.
- list/detail Sales routes were not verified.
- payment query routes were not verified.
- receipt routes and JSON receipt payloads were not verified.
- dashboard route/projection was not verified.
- complete/suspend/resume/void workflow routes were not verified.
- Sales query keys still use hook names not present in `queryKeys.ts`.
- `DailySalesSummary` and `CashierSummary` remain unsupported projection
  imports in the legacy service.

## 20. Runtime Behavior Confirmation

Expected runtime behavior change:

```text
none
```

This migration changed TypeScript type declarations and type barrels only. It
did not alter services, hooks, API endpoints, cache keys, invalidation,
features, authentication, authorization, or backend files.

## 21. Invariants Verified

- Sales entities have canonical owners under `src/types/entities`.
- Sales requests have canonical owners under `src/types/requests`.
- Sales response projections were not created without backend support.
- Sales runtime values were created only for verified finite Sale statuses.
- Payment method values were not invented as a finite enum.
- Services do not gain new runtime behavior.
- Hooks do not gain new workflow behavior.
- Sale and SaleItem ownership remains distinct.
- Sales and Finance payment ownership does not conflict.
- Type-only compatibility exports are used in `src/types/sales`.
- No service method changed.
- No query key or invalidation policy changed.
- No backend file changed.
- No unrelated domain source was modified.

## 22. Rollback Boundary

Rollback is limited to the Sales type files listed in Files Created and Files
Modified, plus this review document.

## 23. Recommended Migration 037 Scope

Recommended next migration:

```text
Migration 037 - Sales Service Facade Disposition
```

Scope:

- decide whether `salesService.checkout` or `createSale` is canonical for the
  verified checkout route;
- remove or explicitly block unsupported Sales hook paths;
- resolve empty Sales service barrel exports;
- defer receipt/dashboard/list/detail/payment workflows unless backend route
  evidence is added.

