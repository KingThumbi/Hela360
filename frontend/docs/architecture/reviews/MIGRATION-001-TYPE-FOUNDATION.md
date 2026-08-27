# Migration 001 - Type Foundation

## 1. Selected Migration

Selected migration: Canonical API and Pagination Type Foundation.

This migration established canonical ownership for generic transport response, error, pagination metadata, paginated response, request config, and outbound pagination request contracts.

## 2. Why It Was Selected

This was the first safe architectural migration because it is foundational, bounded, supported by ADR-001, ADR-004, ADR-008, and ADR-009, and does not depend on unresolved Sales workflow contracts.

It directly targets a measurable compiler category: missing or inconsistent type exports from `@/types/response`, `@/types/pagination`, `@/types/api`, and `@/types/requests`.

## 3. ADR Rules Applied

- ADR-001: services consume shared types and do not own reusable business/API contracts.
- ADR-004: generic API wrappers belong under `src/types/api/`; request DTOs belong under `src/types/requests/`; each reusable type has one owner.
- ADR-009: file names use clear kebab-case naming where framework conventions do not override.
- ADR-010 was not directly implemented because this migration did not touch workflows.

## 4. ADR-008 Boundary Rules Applied

ADR-008 is now accepted and substantive.

Applied boundary rules:

- Every source file has one architectural owner.
- Shared type contracts belong under `src/types/`.
- Generic API wrappers belong to the shared type system, not services/hooks/components.
- Request contracts belong under `src/types/requests/`.
- Consumers should import through public module barrels.
- Temporary compatibility barrels are allowed only when documented and directed at a canonical owner.
- Feature modules may not own reusable request, response, or entity contracts.

ADR-008 conflicts with the previous canonical architecture report only where that report stated ADR-008 was empty. ADR-008 now wins and supersedes that assumption.

## 5. Backend Contracts Verified

Verified backend files:

- `app/api/products.py`
- `app/api/customers.py`
- `app/api/sales.py`
- `app/api_sales.py`

Verified list contract observations:

- Products list returns `{ ok, count, items }`.
- Customers list returns `{ ok, count, items }`.
- Sales list in `app/api_sales.py` accepts `page` and `per_page`.
- Sales list returns `{ ok, items, pagination, summary, filters }`.
- Sales pagination metadata contains `page`, `per_page`, `total`, `pages`, `has_prev`, and `has_next`.

No representative product/customer paginated envelope was verified. Therefore `PaginatedResponse<T>` was modeled only for the verified paginated transport envelope, while `ListResponse<T>` retains the verified non-paginated list shape.

## 6. Files Inspected

Frontend:

- `src/types/api.ts`
- `src/types/response.ts`
- `src/types/pagination.ts`
- `src/types/requests/index.ts`
- `src/types/requests/pagination.ts`
- `src/types/responses/index.ts`
- `src/types/responses/pagination.ts`
- `src/types/index.ts`
- consumers of `PaginationRequest`, `PaginationMeta`, `PaginatedResponse`, `ApiResponse`, and `ApiError`

Backend:

- `app/api/products.py`
- `app/api/customers.py`
- `app/api/sales.py`
- `app/api_sales.py`

Architecture:

- ADR-001 through ADR-010
- `FRONTEND_ARCHITECTURAL_BASELINE.md`
- `ADR_COMPLIANCE_MATRIX.md`
- `CANONICAL_FRONTEND_ARCHITECTURE.md`

## 7. Files Created

- `frontend/src/types/api/api-error.ts`
- `frontend/src/types/api/api-response.ts`
- `frontend/src/types/api/pagination.ts`
- `frontend/src/types/api/request-config.ts`
- `frontend/src/types/api/index.ts`
- `frontend/src/types/requests/pagination-request.ts`
- `frontend/docs/architecture/reviews/MIGRATION-001-TYPE-FOUNDATION.md`

## 8. Files Modified

- `frontend/src/types/api.ts`
- `frontend/src/types/response.ts`
- `frontend/src/types/pagination.ts`
- `frontend/src/types/requests/pagination.ts`
- `frontend/src/types/requests/index.ts`
- `frontend/src/types/index.ts`
- `frontend/src/services/base/BaseService.ts`
- Transport type imports under `frontend/src` that referenced `@/types/response` or `@/types/pagination`

No backend files were modified.

## 9. Canonical Symbols Established

Canonical API symbols under `src/types/api/`:

- `ApiError`
- `ValidationError`
- `ApiResponse`
- `ListResponse`
- `MutationResponse`
- `HealthResponse`
- `EmptyResponse`
- `PaginationMeta`
- `PaginatedResponse`
- `HttpMethod`
- `RequestConfig`
- `EntityId`

Canonical request symbol under `src/types/requests/`:

- `PaginationRequest`

## 10. Duplicates Removed or Converted to Re-Exports

The flat files below no longer define competing canonical symbols:

- `src/types/api.ts`
- `src/types/response.ts`
- `src/types/pagination.ts`
- `src/types/requests/pagination.ts`

They now re-export the canonical definitions.

## 11. Transitional Compatibility Exports

Transitional compatibility exports remain in:

- `src/types/api.ts`
- `src/types/response.ts`
- `src/types/pagination.ts`
- `src/types/requests/pagination.ts`

Removal plan:

1. Keep these shims until downstream imports are fully normalized.
2. Remove `src/types/response.ts` and `src/types/pagination.ts` imports first.
3. Remove flat `src/types/api.ts` only after `@/types/api` resolution is confirmed to use the directory barrel or after an agreed import convention is documented.

## 12. Pre-Build Error Count

Baseline from `FRONTEND_ARCHITECTURAL_BASELINE.md`: 294 TypeScript errors.

Baseline code counts:

- TS2305: 109
- TS2339: 41
- TS2322: 40
- TS2724: 14
- TS2614: 14
- TS2693: 11
- TS2554: 11
- TS6133: 10
- TS2307: 9
- TS7006: 7
- TS2551: 6
- TS2300: 6
- TS1294: 3
- TS2686: 2
- TS2349: 2
- TS2323: 2
- TS18046: 2
- Singleton codes: 5

## 13. Post-Build Error Count

Post-migration TypeScript count: 274 errors.

Post-migration code counts:

- TS2305: 80
- TS2339: 41
- TS2322: 41
- TS2307: 17
- TS2724: 14
- TS2614: 14
- TS2693: 11
- TS2554: 11
- TS6133: 10
- TS7006: 7
- TS2551: 6
- TS2300: 6
- TS1294: 3
- TS2686: 2
- TS2349: 2
- TS2323: 2
- TS18046: 2
- TS2739: 1
- TS2559: 1
- TS2484: 1
- TS2430: 1
- TS1484: 1

Net reduction: 20 errors.

## 14. Errors Resolved by Category

Resolved category: missing canonical API/pagination/request type exports.

Measured reductions:

- `TS2305` dropped from 109 to 80.
- Overall count dropped from 294 to 274.

The resolved errors primarily came from:

- `PaginationRequest` missing from `@/types/requests`.
- `PaginatedResponse` missing from `@/types/response`.
- Transport types split across non-canonical flat files.
- Consumers importing old transport type surfaces.

## 15. Errors Remaining by Category

Remaining architectural categories:

- Type ownership for business entities and domain DTOs.
- Service facade and method-name drift.
- Query-key function drift.
- Provider and route public-boundary drift.
- Navigation runtime/type compatibility.
- Error-code runtime contract.
- Missing UI/component modules.
- Barrel export mismatches.
- TypeScript `erasableSyntaxOnly` and `verbatimModuleSyntax` issues.

## 16. New Errors Introduced

No duplicate canonical-symbol errors or circular-export errors were introduced.

One remaining `TS2322` diagnostic now names the canonical `pagination` field on `PaginatedResponse<T>`:

- `usePurchaseOrders.ts` expects `PaginatedResponse<PurchaseOrder>`, while the current service returns `ApiResponse<PurchaseOrder[]>`.

This is not a new architectural category. It exposes the existing mismatch between hooks expecting paginated data and services returning non-paginated API responses.

## 17. Risks

- `@/types/api` currently resolves through the transitional flat `src/types/api.ts` file, which re-exports the canonical directory barrel.
- Some services still claim paginated responses for backend endpoints that are not verified as paginated.
- Existing consumers may still rely on old semantic assumptions such as `meta` instead of the verified `pagination` envelope.
- Product and customer backend list endpoints are not paginated, while some frontend hooks treat them as paginated.

## 18. Rollback Boundary

Rollback is limited to:

- the new `src/types/api/*` files
- `src/types/requests/pagination-request.ts`
- the transitional re-export edits in flat type files
- transport type import path rewrites
- `BaseService.count()` reading `response.pagination.total`
- this migration report

No backend behavior, feature logic, route logic, provider logic, or service facade behavior was changed.

## 19. Next Recommended Migration

Recommended next migration: runtime error contract foundation.

Reason:

- ADR-005 depends on the API error type foundation now established.
- The current build still has 11 `TS2693` errors from `ErrorCode` being used as a runtime value while defined as a type-only alias.
- Fixing this is bounded and does not require backend workflow assumptions.

Alternate next migration: authentication request/response DTO ownership, because auth DTO exports remain missing from `@/types/requests` and `@/types/apis` remains an incorrect import path.

## 20. Verification Commands Used

```bash
npm run build
npx tsc -b --pretty false
rg -c "error TS" /tmp/hela360-tsc-migration-001.log
rg -o "TS[0-9]+" /tmp/hela360-tsc-migration-001.log | sort | uniq -c | sort -nr
rg -n "(PaginationRequest|PaginationMeta|PaginatedResponse|ApiResponse|ApiError|Duplicate|circular|Circular)" /tmp/hela360-tsc-migration-001.log
rg -n "export (interface|type) (PaginationRequest|PaginationMeta|PaginatedResponse|ApiResponse|ApiError)|interface (PaginationRequest|PaginationMeta|PaginatedResponse|ApiResponse|ApiError)" frontend/src/types
rg -n "@/types/(response|pagination)" frontend/src
```
