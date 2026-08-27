# Migration 037 - Sales Service Facade

## 1. Migration Purpose

Migration 037 establishes the canonical public Sales service facade and aligns
Sales hooks with verified backend-supported operations only.

No backend source, Sales query-key definitions, invalidation policy, Sales UI,
or unrelated domain source was changed.

## 2. ADR Rules Applied

- ADR-001: Sales exposes one public business-oriented service facade.
- ADR-002: hooks call the Sales facade and do not unwrap transport envelopes.
- ADR-003: query keys and invalidation policy remain unchanged.
- ADR-004: Sales entities and DTOs remain under `src/types`.
- ADR-005: errors propagate; unsupported hooks reject explicitly.
- ADR-006: tenant, branch, cashier, and warehouse behavior remains backend-owned.
- ADR-008: only the canonical facade is publicly exported.
- ADR-009: service names use business language.
- ADR-010: unsupported workflow operations are not fabricated.

## 3. Initial Sales Service Diagnostics

Frontend compiler baseline before this migration:

```text
96 TypeScript errors
```

Sales service cluster before:

- missing empty service exports: `salesQueryService`, `salesWorkflowService`,
  `paymentService`, `receiptService`, `salesDashboardService`
- missing facade methods: `createSale`, `getSale`, `listSales`, `refundSale`,
  `completeSale`, `suspendSale`, `resumeSale`, `voidSale`, `getReceipt`,
  `listReceipts`, `getDashboard`, `getSalePayment`, `listSalePayments`
- unsupported request/entity imports: `CompleteSaleRequest`,
  `SuspendSaleRequest`, `ResumeSaleRequest`, `VoidSaleRequest`, `Receipt`,
  `SalesDashboard`
- stale Sales domain response imports from `@/types/apis/*`
- unused `SalePayment` import in an unsupported payment hook

## 4. Backend Routes Verified

Active registered Sales blueprint:

```text
app/api/sales.py
```

Registration:

```text
app/__init__.py registers app.api.sales under /api
```

Verified active routes:

| Operation | Route | Method | Permission | Envelope | Confidence |
| --- | --- | --- | --- | --- | --- |
| create sale / checkout | `/api/sales/checkout` | `POST` | `sales.create` | `{ ok, message, item, shift_id }` | Confirmed |
| refund sale | `/api/sales/<sale_id>/refund` | `POST` | `sales.refund` | `{ ok, message, refund }` | Confirmed |

`app/api_sales.py` contains list/detail route code, but it is not registered by
the current application factory. It was treated as partial evidence only and was
not exposed through the frontend facade.

## 5. Frontend Services Found

Found under `frontend/src/services/sales/`:

- `legacySalesService.ts`: only non-empty Sales transport implementation, but
  it exposes several unverified endpoints and returns transport envelopes.
- `salesQueryService.ts`: empty.
- `salesWorkflowService.ts`: empty.
- `paymentService.ts`: empty.
- `receiptService.ts`: empty.
- `salesDashboardService.ts`: empty.
- `refundService.ts`: separate speculative refund service with service-local
  types and unverified `/refunds` endpoints.
- `prescriptionService.ts`: non-empty but outside this Sales facade migration.

## 6. Canonical Public Sales Service

Canonical owner:

```text
frontend/src/services/sales/salesService.ts
```

Canonical public import path:

```typescript
import { salesService } from "@/services/sales";
```

Canonical facade methods:

- `createSale(payload): Promise<Sale>`
- `refundSale(saleId, payload): Promise<SaleRefund>`

No `listSales`, `getSale`, payment, receipt, dashboard, or workflow facade
method was added because no active registered backend route was verified.

## 7. Response Mapping

Create response:

```text
{ ok: true, message, item: Sale, shift_id }
```

Service return:

```text
Sale
```

Refund response:

```text
{ ok: true, message, refund: SaleRefund }
```

Service return:

```text
SaleRefund
```

Transport envelopes are unwrapped inside `salesService`. Hooks receive domain
values.

## 8. Operation Dispositions

List sales: unsupported in active registered backend. `app/api_sales.py` is not
registered.

Get sale: unsupported in active registered backend. `app/api_sales.py` is not
registered.

Payment operations: unsupported. No registered list/get/add SalePayment route
was verified.

Complete sale: unsupported. No active registered route was verified.

Suspend sale: unsupported. No backend route or schema was verified.

Resume sale: unsupported. No backend route or schema was verified.

Void sale: unsupported as a public active route. Approval-service helper code
exists, but no registered void route was verified.

Receipt: unsupported. No verified receipt JSON payload or active route was
found.

SalesDashboard: unsupported. No verified dashboard endpoint or projection was
found.

## 9. Legacy and Decomposed Service Disposition

`legacySalesService.ts` remains on disk as transitional user work. It is no
longer publicly exported from the Sales service barrel.

Empty decomposed service modules remain on disk but are no longer exported as
public runtime instances.

The Sales service barrel now exports only:

- `salesService`
- `SalesService`

## 10. Hook Disposition

Verified hooks migrated:

- `useCreateSale` now calls `salesService.createSale`.
- `useRefundSale` now routes `RefundSaleRequest.sale_id` into
  `salesService.refundSale(saleId, payload)`.

Unsupported local hooks retained but made explicit rejections:

- `useSales`
- `useSale`
- `useSalePayments`
- `useSalePayment`
- `useReceipt`
- `useReceipts`
- `useSalesDashboard`
- `useCompleteSale`
- `useSuspendSale`
- `useResumeSale`
- `useVoidSale`

These retained hooks do not issue speculative HTTP requests.

Public Sales hook barrel now exposes only:

- `useSales`
- `useSale`
- `useCreateSale`
- `useRefundSale`

`useSales` and `useSale` remain transitional public hooks but explicitly reject
until an active registered list/detail backend contract is restored.

## 11. Files Inspected

Backend:

- `app/__init__.py`
- `app/api/sales.py`
- `app/api_sales.py`
- `app/models/pos.py`
- `app/schemas/`
- `app/serializers/`
- `app/services/tenant/pos/`
- `migrations/`

Frontend:

- `frontend/src/services/sales/`
- `frontend/src/services/base/BaseService.ts`
- `frontend/src/hooks/queries/sales/`
- `frontend/src/types/entities/sale*.ts`
- `frontend/src/types/requests/create-sale-request.ts`
- `frontend/src/types/requests/refund-sale-request.ts`
- `frontend/src/types/domains/sales.ts`
- `frontend/src/api/endpoints.ts`
- `frontend/src/lib/queryKeys.ts`
- `frontend/src/lib/queryInvalidation.ts`

Architecture:

- ADR-001 through ADR-006
- ADR-008 through ADR-010
- Migration 036 report

## 12. Files Created

- `frontend/src/services/sales/salesService.ts`
- `frontend/docs/architecture/reviews/MIGRATION-037-SALES-SERVICE-FACADE.md`

## 13. Files Modified

- `frontend/src/services/sales/index.ts`
- `frontend/src/services/sales/legacySalesService.ts`
- `frontend/src/hooks/queries/sales/index.ts`
- `frontend/src/hooks/queries/sales/useCreateSale.ts`
- `frontend/src/hooks/queries/sales/useRefundSale.ts`
- `frontend/src/hooks/queries/sales/useSales.ts`
- `frontend/src/hooks/queries/sales/useSale.ts`
- `frontend/src/hooks/queries/sales/useSalePayments.ts`
- `frontend/src/hooks/queries/sales/useSalePayment.ts`
- `frontend/src/hooks/queries/sales/useReceipt.ts`
- `frontend/src/hooks/queries/sales/useReceipts.ts`
- `frontend/src/hooks/queries/sales/useSalesDashboard.ts`
- `frontend/src/hooks/queries/sales/useCompleteSale.ts`
- `frontend/src/hooks/queries/sales/useSuspendSale.ts`
- `frontend/src/hooks/queries/sales/useResumeSale.ts`
- `frontend/src/hooks/queries/sales/useVoidSale.ts`
- `frontend/src/types/domains/sales.ts`

## 14. Compiler Errors

Before:

```text
96 TypeScript errors
```

After:

```text
63 TypeScript errors
```

Net reduction:

```text
33 errors
```

No `src/hooks/queries/sales`, `src/services/sales`, or
`src/types/domains/sales` diagnostics remain.

## 15. Build Verification

Commands run:

```bash
npx tsc -b --pretty false
npm run build
```

`npx tsc -b --pretty false` reports 63 remaining TypeScript errors.

`npm run build` exits with code 2 because `tsc -b` still fails on unrelated
dashboard, inventory, procurement, theme, query factory, main entry, and
administration diagnostics.

## 16. Newly Exposed Diagnostics

No new diagnostics were introduced.

## 17. Remaining Sales Blockers

- Active backend list/detail routes are absent from the registered Sales
  blueprint.
- Payment routes are absent.
- Receipt route and JSON receipt contract are absent.
- Dashboard route and projection are absent.
- Complete/suspend/resume/void workflow endpoints are absent.
- `app/api_sales.py` contains unregistered partial list/detail code and needs a
  backend registration/ownership decision before frontend support can be
  restored.

## 18. Runtime Behavior Confirmation

Supported runtime behavior is now truthful:

- `createSale` posts to the verified checkout route and returns `Sale`.
- `refundSale` posts to the verified refund route and returns `SaleRefund`.

Unsupported local hooks reject before making network requests.

No query-key definitions, invalidation behavior, UI, backend code, or unrelated
domain source was changed.

## 19. Invariants Verified

- Sales has one canonical public service facade.
- Public methods use business-oriented names.
- Only verified active backend operations are exposed.
- Hooks call only the canonical facade for verified operations.
- Transport mapping occurs in the service.
- Services own no React or TanStack Query logic.
- Hooks own no URL construction or DTO mapping.
- Legacy implementation is transitional and not publicly exported.
- Receipt and dashboard remain unsupported.
- Workflow methods remain unsupported.
- Payment ownership remains distinct from Finance payments.
- Canonical Sales types remain under `src/types`.
- No query-key definitions changed.
- No invalidation policy changed.
- No backend file changed.

## 20. Rollback Boundary

Rollback is limited to:

- `frontend/src/services/sales/salesService.ts`
- `frontend/src/services/sales/index.ts`
- `frontend/src/services/sales/legacySalesService.ts`
- Sales hook files under `frontend/src/hooks/queries/sales/`
- `frontend/src/types/domains/sales.ts`
- this review document

## 21. Recommended Migration 038 Scope

Recommended next migration:

```text
Migration 038 - Dashboard Type API Import Alignment
```

Rationale:

The next visible compiler cluster is the dashboard hooks importing
`@/types/apis`, plus dashboard service method naming drift.

