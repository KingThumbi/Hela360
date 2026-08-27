# Migration 003 - Authentication DTO Ownership

## 1. Migration Purpose

Migration 003 established canonical ownership and public exports for authentication request and response DTOs.

This migration addressed missing authentication DTO exports from `@/types/requests` and the invalid `@/types/apis` import path used by authentication consumers.

## 2. ADR Requirements Applied

- ADR-001: authentication services consume shared DTOs rather than owning reusable request or response contracts.
- ADR-004: request DTOs live under `src/types/requests/`; response DTOs live under `src/types/responses/`; generic API wrappers remain under `src/types/api/`.
- ADR-005: API error payloads remain separate from authentication response DTOs.
- ADR-006: authentication payloads carry tenant and branch context where backend evidence supports it.
- ADR-008: shared contracts have one owner and public barrels expose stable import surfaces.
- ADR-009: DTO names use PascalCase; files use kebab-case.

## 3. Backend Operations Inspected

Inspected backend files:

- `app/auth/routes.py`
- `app/auth/schemas.py`
- `app/services/tenant/auth/authentication_service.py`
- `app/services/tenant/auth/jwt_service.py`
- `app/services/tenant/auth/refresh_token_service.py`
- `app/services/tenant/auth/password_service.py`
- `app/api/errors.py`

Operation evidence:

| Operation | Route evidence | Backend service/schema evidence | Classification |
| --- | --- | --- | --- |
| Login | `POST /auth/login` in `app/auth/routes.py` | `LoginRequest`, `LoginResponse`, `authentication_service.login` | Confirmed |
| Refresh token | No route found in `app/auth/routes.py` | `RefreshTokenRequest`, `RefreshTokenResponse`, `authentication_service.refresh` | Partial evidence |
| Logout | No route found in `app/auth/routes.py` | `authentication_service.logout` | Partial evidence |
| Current user | No route found in `app/auth/routes.py` | `CurrentUserResponse` schema | Partial evidence |
| Forgot password | No route found | `ForgotPasswordRequest` schema | Partial evidence |
| Reset password | No route found | `ResetPasswordRequest` schema and password service evidence | Partial evidence |
| Change password | No route found | `ChangePasswordRequest` schema and password service evidence | Partial evidence |

## 4. Verified Backend Request Contracts

Confirmed login request:

- `email`: required
- `password`: required
- `tenant_id`: required by route access, typed nullable in schema
- `branch_id`: optional nullable
- `remember_me`: optional, default `false`
- `device_name`: optional nullable

Schema-backed request DTOs without confirmed route in `app/auth/routes.py`:

- `RefreshTokenRequest`: `refresh_token`
- `ForgotPasswordRequest`: `email`
- `ResetPasswordRequest`: `token`, `new_password`
- `ChangePasswordRequest`: `current_password`, `new_password`

## 5. Verified Backend Response Contracts

Confirmed login response:

- `access_token`
- `refresh_token`
- `access_expires_in`
- `refresh_expires_in`
- `token_type`

Schema-backed response DTOs without confirmed route in `app/auth/routes.py`:

- `RefreshTokenResponse`: `access_token`, `refresh_token`, `access_expires_in`, `refresh_expires_in`, `token_type`
- `CurrentUserResponse`: `id`, `email`, `username`, `first_name`, `last_name`, `tenant_id`, `branch_id`, `role`, `permissions`, `is_owner`, `is_active`

## 6. Unsupported or Missing Backend Operations

No route evidence was found in `app/auth/routes.py` for:

- `/auth/logout`
- `/auth/refresh`
- `/auth/me`
- `/auth/forgot-password`
- `/auth/reset-password`
- `/auth/change-password`

The endpoint registry and frontend service reference these paths. This migration preserved those existing frontend calls and did not change endpoint behavior.

## 7. Frontend Definitions Found

Definitions before migration:

- `src/types/auth.ts` defined `LoginRequest`, `RefreshTokenRequest`, `RefreshTokenResponse`, and `AuthResponse` with camelCase fields.
- `src/types/requests/auth.ts` defined grouped authentication request DTOs.
- `src/types/responses/auth.ts` defined grouped authentication response DTOs and used generic `ApiResponse` wrappers.
- `src/services/auth/authService.ts` imported auth responses from nonexistent `@/types/apis`.
- `src/hooks/queries/auth/useLogin.ts` imported `LoginResponse` from nonexistent `@/types/apis`.

## 8. Duplicate Contracts Found

Duplicate active request definitions were found for:

- `LoginRequest`
- `RefreshTokenRequest`

Duplicate active response definitions were found for:

- `RefreshTokenResponse`

The grouped files now re-export canonical definitions rather than redefining them.

## 9. Canonical Files Selected

Canonical request files:

- `src/types/requests/login-request.ts`
- `src/types/requests/refresh-token-request.ts`
- `src/types/requests/forgot-password-request.ts`
- `src/types/requests/reset-password-request.ts`
- `src/types/requests/change-password-request.ts`

Canonical response files:

- `src/types/responses/login-response.ts`
- `src/types/responses/refresh-token-response.ts`
- `src/types/responses/current-user-response.ts`

## 10. Canonical DTOs Established

Requests:

- `LoginRequest`
- `RefreshTokenRequest`
- `ForgotPasswordRequest`
- `ResetPasswordRequest`
- `ChangePasswordRequest`

Responses:

- `LoginResponse`
- `RefreshTokenResponse`
- `CurrentUserResponse`

## 11. Canonical Entity Dependencies

No reusable `User`, `Tenant`, `Branch`, `Role`, or `Permission` entity ownership was changed in this migration.

`CurrentUserResponse` is treated as an authentication response projection, not as a full reusable `User` entity.

## 12. Files Created

- `frontend/src/types/requests/login-request.ts`
- `frontend/src/types/requests/refresh-token-request.ts`
- `frontend/src/types/requests/forgot-password-request.ts`
- `frontend/src/types/requests/reset-password-request.ts`
- `frontend/src/types/requests/change-password-request.ts`
- `frontend/src/types/responses/login-response.ts`
- `frontend/src/types/responses/refresh-token-response.ts`
- `frontend/src/types/responses/current-user-response.ts`
- `frontend/docs/architecture/reviews/MIGRATION-003-AUTHENTICATION-DTO-OWNERSHIP.md`

## 13. Files Modified

- `frontend/src/types/requests/auth.ts`
- `frontend/src/types/responses/auth.ts`
- `frontend/src/types/requests/index.ts`
- `frontend/src/types/responses/index.ts`
- `frontend/src/types/auth.ts`
- `frontend/src/services/auth/authService.ts`
- `frontend/src/hooks/queries/auth/useLogin.ts`

## 14. Barrels Updated

Updated:

- `src/types/requests/index.ts`
- `src/types/responses/index.ts`

Transitional grouped barrels:

- `src/types/requests/auth.ts`
- `src/types/responses/auth.ts`
- `src/types/auth.ts`

## 15. Imports Migrated

Authentication imports changed from:

```typescript
import type { LoginResponse } from "@/types/apis";
```

to:

```typescript
import type { LoginResponse } from "@/types/responses";
```

Only authentication-related `@/types/apis` imports were changed.

## 16. Transitional Re-Exports

Transitional re-exports remain in:

- `src/types/requests/auth.ts`
- `src/types/responses/auth.ts`
- `src/types/auth.ts`

These point directly to canonical owners and do not redefine migrated DTOs.

## 17. Runtime Mismatches Documented

The backend login response is a raw snake_case token response and does not include an `identity` payload.

Existing frontend login hook code still expects:

- `response.identity`
- `response.accessToken`
- `response.refreshToken`

This migration intentionally did not transform response data, change auth store behavior, alter token persistence, or refactor login flow. The mismatch is now visible as shape diagnostics and should be handled by a later authentication runtime contract migration.

## 18. Build Command

```bash
npm run build
```

Measurement command:

```bash
npx tsc -b --pretty false
```

## 19. Compiler Errors Before

Pre-migration baseline:

```text
262 TypeScript errors
```

## 20. Compiler Errors After

Post-migration count:

```text
257 TypeScript errors
```

## 21. Net Reduction

```text
5 errors
```

## 22. Missing-Export Diagnostics Before and After

Overall `TS2305`:

- Before: 80
- After: 74

Authentication DTO missing-export diagnostics:

- Before: 8
- After: 0

Remaining authentication-adjacent missing exports:

- `authService` is still not exported from `@/services/auth`.

That service barrel issue was not changed because this migration was limited to DTO ownership.

## 23. New Diagnostics Introduced

Newly exposed shape diagnostics:

- `LoginResponse.identity` does not exist.
- `LoginResponse.accessToken` should be `access_token` according to backend evidence.
- `LoginResponse.refreshToken` should be `refresh_token` according to backend evidence.

These are real runtime contract mismatches, not DTO ownership defects.

## 24. Invariants Verified

Verified:

- Authentication requests live under `src/types/requests/`.
- Authentication responses live under `src/types/responses/`.
- Generic API wrappers remain under `src/types/api/`.
- Authentication service consumes shared DTOs.
- Stores and providers did not receive new DTO definitions.
- Every migrated DTO has one canonical interface definition.
- Barrels export only existing symbols.
- Type-only exports are used for DTOs.
- No authentication runtime behavior changed.
- No authorization architecture was implemented or altered.
- No unrelated feature modules were changed.

## 25. Rollback Boundary

Rollback is limited to:

- the new authentication request DTO files
- the new authentication response DTO files
- authentication type barrel changes
- authentication type import path changes
- this migration report

No backend behavior, providers, protected routes, token storage, refresh sequencing, or authorization behavior was changed.

## 26. Remaining Authentication Architecture Issues

Remaining issues:

- `src/services/auth/index.ts` is empty, so hooks cannot import `authService` through the public service barrel.
- Login runtime flow expects transformed identity and camelCase token fields, but backend login returns raw snake_case token fields.
- Endpoint registry contains auth routes not found in `app/auth/routes.py`.
- `CurrentUserResponse` is schema-backed but route evidence is missing.
- Auth identity ownership still depends on `src/types/auth.ts`; full entity migration was intentionally deferred.

## 27. Recommended Next Migration

Recommended next migration: authentication service public barrel and runtime response mapping decision.

Reason:

- The DTO ownership layer is now established.
- The next blocking auth errors are not missing DTOs; they are `authService` public-barrel exposure and the login response transformation mismatch.
- That migration should explicitly decide whether `AuthService.login()` returns raw backend `LoginResponse` or maps it into the frontend `Identity` session model.
