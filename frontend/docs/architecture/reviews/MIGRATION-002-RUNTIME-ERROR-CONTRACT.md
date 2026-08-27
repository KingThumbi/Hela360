# Migration 002 - Runtime Error Contract Foundation

## 1. Migration Purpose

Migration 002 established the runtime error-code contract and normalized application error foundation required by ADR-005.

The immediate compiler symptom was `TS2693`, where `ErrorCode` was a type-only symbol but was used as a runtime namespace-like value in `src/lib/errors.ts`.

## 2. ADR Requirements Applied

- ADR-004: reusable contracts live under `src/types`; API payload contracts remain under `src/types/api`; reusable enum-like values belong under `src/types/enums`.
- ADR-005: services expose a common `AppError` shape with `code`, `message`, `category`, `details`, and `retryable`; validation errors preserve field-level information; hooks/components do not inspect raw HTTP status codes.
- ADR-008: shared contracts have one owner and consumers depend on public module boundaries.
- ADR-009: runtime constants use clear naming and TypeScript-compatible constant-backed values.

## 3. Inspected Definitions

Inspected frontend files:

- `frontend/src/lib/errors.ts`
- `frontend/src/types/api/api-error.ts`
- `frontend/src/types/api/index.ts`
- `frontend/src/types/api.ts`
- `frontend/src/types/enums/index.ts`
- `frontend/src/types/index.ts`
- `frontend/src/api/client.ts`
- `frontend/src/api/interceptors.ts`
- `frontend/src/api/refresh.ts`
- `frontend/src/services/base/BaseService.ts`
- `frontend/src/services/auth/authService.ts`
- `frontend/src/lib/queryClient.ts`
- `frontend/src/validation/*`

Search terms inspected:

- `ErrorCode`
- `ERROR_CODES`
- `ApiError`
- `ApplicationError`
- `AppError`
- `NormalizedError`
- `ValidationError`
- `AuthenticationError`
- `AuthorizationError`
- `TenantError`
- `BranchError`

## 4. Competing Contracts Found

Definitions found before migration:

- `ERROR_CODES` runtime object existed in `src/lib/errors.ts`.
- `ErrorCode` type alias existed in `src/lib/errors.ts`, derived from `ERROR_CODES`.
- `ApiError` and transport `ValidationError` existed in `src/types/api/api-error.ts`.
- `AppError` class existed in `src/lib/errors.ts`, but lacked ADR-005 `category` and `retryable` fields.
- `AppError.fromAxios` was called by `src/api/interceptors.ts`, but did not exist.

No second active `ErrorCode` definition was found elsewhere.

## 5. Canonical Owner Selected

Canonical owner:

```text
frontend/src/types/enums/error-code.ts
```

Reason:

- Error codes are runtime-backed enum-like values.
- ADR-004 assigns business/runtime enumerations to `src/types/enums/`.
- ADR-009 and `erasableSyntaxOnly` favor const-backed unions over TypeScript enums.

## 6. Runtime Constant Representation

Runtime constant:

```typescript
ERROR_CODES
```

Representation:

```typescript
export const ERROR_CODES = {
  UNKNOWN: "UNKNOWN",
  NETWORK: "NETWORK_ERROR",
  TIMEOUT: "TIMEOUT",
  VALIDATION: "VALIDATION_ERROR",
  AUTHENTICATION: "AUTHENTICATION_ERROR",
  AUTHORIZATION: "AUTHORIZATION_ERROR",
  FORBIDDEN: "FORBIDDEN",
  NOT_FOUND: "NOT_FOUND",
  CONFLICT: "CONFLICT",
  SERVER: "SERVER_ERROR",
  TENANT: "TENANT_ERROR",
  BRANCH: "BRANCH_ERROR",
} as const;
```

No error code from the previous runtime object was removed.

## 7. Compile-Time Type Representation

Compile-time type:

```typescript
ErrorCode
```

Representation:

```typescript
export type ErrorCode =
  (typeof ERROR_CODES)[keyof typeof ERROR_CODES];
```

Runtime comparisons now use `ERROR_CODES.*`, not `ErrorCode.*`.

## 8. Normalized Error Contract

Canonical normalized frontend error class:

```typescript
AppError
```

It now exposes:

- `code`
- `message`
- `category`
- `details`
- `retryable`
- `status`
- `validationErrors`

Categories:

- `network`
- `transport`
- `business`
- `validation`
- `system`

`ApiError` remains the transport/API error payload type under `src/types/api/`.

## 9. Files Created

- `frontend/src/types/enums/error-code.ts`
- `frontend/docs/architecture/reviews/MIGRATION-002-RUNTIME-ERROR-CONTRACT.md`

## 10. Files Modified

- `frontend/src/types/enums/index.ts`
- `frontend/src/types/index.ts`
- `frontend/src/lib/errors.ts`

No backend files were modified.

## 11. Imports Migrated

`src/lib/errors.ts` now imports:

- `ERROR_CODES` as a runtime value from `@/types/enums`
- `ErrorCode` as a type-only import from `@/types/enums`
- `ApiError` as a type-only import from `@/types/api`
- `AxiosError` as a type-only import from `axios`

## 12. Compatibility Re-Exports

`src/lib/errors.ts` re-exports `ERROR_CODES` and `ErrorCode` from the canonical enum owner.

This is transitional compatibility for any established imports from `@/lib/errors`. It does not redefine either symbol.

## 13. Error Codes Preserved

Preserved codes:

- `UNKNOWN`
- `NETWORK_ERROR`
- `TIMEOUT`
- `VALIDATION_ERROR`
- `AUTHENTICATION_ERROR`
- `AUTHORIZATION_ERROR`
- `FORBIDDEN`
- `NOT_FOUND`
- `CONFLICT`
- `SERVER_ERROR`
- `TENANT_ERROR`
- `BRANCH_ERROR`

## 14. Backend Error Evidence

Observed backend error shapes:

- `app/api/products.py`, `app/api/customers.py`, and `app/api/sales.py` commonly return `{ ok: false, error: string }`.
- `app/auth/routes.py` returns `{ ok: false, message: string }`.
- `app/api/errors.py` returns nested `{ error: { code, message } }` for authentication/authorization handlers.
- Backend codes observed include `INVALID_CREDENTIALS`, `ACCOUNT_LOCKED`, `ACCOUNT_UNAVAILABLE`, `USER_NOT_FOUND`, `AUTHENTICATION_ERROR`, `AUTHORIZATION_DENIED`, and `INTERNAL_SERVER_ERROR`.

The frontend normalization accepts all verified envelope shapes without changing backend behavior.

## 15. Build Command

```bash
npm run build
```

Additional measurement command:

```bash
npx tsc -b --pretty false
```

## 16. Compiler Errors Before

Pre-migration baseline from Migration 001:

```text
274 TypeScript errors
```

## 17. Compiler Errors After

Post-migration count:

```text
262 TypeScript errors
```

Net reduction:

```text
12 errors
```

## 18. TS2693 Count Before

Before:

```text
11 TS2693 errors
```

## 19. TS2693 Count After

After:

```text
0 TS2693 errors
```

## 20. New Diagnostics Introduced

No new error-contract diagnostics were introduced.

`TS2693` was eliminated. The remaining diagnostics are from pre-existing categories such as missing exports, service facade drift, query-key drift, navigation typing, provider boundaries, and feature/component missing modules.

## 21. Invariants Verified

Verified:

- Error codes have one canonical owner.
- Runtime error-code values exist at runtime.
- Compile-time `ErrorCode` is derived from runtime values.
- Generic API error payloads remain under `src/types/api/`.
- Error-normalization logic remains in `src/lib/errors.ts`, not in type modules.
- Services do not define reusable error-code contracts.
- Runtime comparisons use `ERROR_CODES.*`.
- No `ErrorCode.*` runtime access remains.
- Type-only imports are used for `ErrorCode`, `ApiError`, and `AxiosError`.
- No unrelated business logic changed.

## 22. Rollback Boundary

Rollback is limited to:

- `frontend/src/types/enums/error-code.ts`
- `frontend/src/types/enums/index.ts`
- `frontend/src/types/index.ts`
- `frontend/src/lib/errors.ts`
- this migration report

No backend behavior, feature logic, service facade logic, hook logic, provider logic, or navigation logic was changed.

## 23. Remaining Error Architecture Issues

Remaining architecture issues outside this migration:

- Centralized logging service is still future work.
- Some backend error codes are more specific than the frontend normalized categories.
- Components/providers still need broader presentation-error review later.
- Auth invalidation behavior exists in interceptors/refresh flow but should be revisited with the authorization/provider migration.

## 24. Recommended Next Migration

Recommended next migration: Authentication request/response DTO ownership.

Reason:

- Auth DTOs already exist under `src/types/requests/auth.ts` and `src/types/responses/auth.ts`, but barrels do not expose them consistently.
- Several remaining errors are bounded to missing auth request exports and incorrect `@/types/apis` imports.
- This is a type-ownership migration and does not require service facade reconstruction.

Alternative: provider public barrel foundation, because `AppProvider` remains missing from `@/providers`, but that touches provider composition and should follow a focused provider-boundary brief.
