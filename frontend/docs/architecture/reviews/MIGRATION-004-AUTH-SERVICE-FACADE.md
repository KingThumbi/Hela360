# Migration 004 - Auth Service Facade

## 1. Migration Purpose

Migration 004 established the public authentication service facade and moved verified backend login token-name conversion into the service layer.

The migration resolved:

- missing `authService` exports from `@/services/auth`
- hook-level assumptions that `LoginResponse` used frontend camelCase token fields
- hook-level dependence on backend transport field names

## 2. ADR Requirements Applied

- ADR-001: services hide backend response shape and perform DTO conversion where required.
- ADR-004: backend transport DTOs remain under `src/types/responses`; application/session result types remain distinct.
- ADR-005: errors continue through the API/interceptor normalization path.
- ADR-006: tenant and branch context must not be fabricated when absent from the login response.
- ADR-008: consumers import the authentication service through the public domain barrel.
- ADR-009: `authService` and `login()` preserve business-oriented naming.

## 3. Backend Login Contract Verified

Verified route:

```text
POST /auth/login
```

Verified request fields:

- `email`
- `password`
- `tenant_id`
- `branch_id`
- `remember_me`
- `device_name`

Verified successful response fields:

- `access_token`
- `refresh_token`
- `access_expires_in`
- `refresh_expires_in`
- `token_type`

No identity, tenant projection, branch projection, roles, or permissions payload is returned by the confirmed login route.

## 4. Existing Frontend Authentication Flow

Before migration:

```text
useLogin
  -> authService.login(LoginRequest)
  -> LoginResponse
  -> useLogin expected identity/accessToken/refreshToken
  -> authStore.login(identity, accessToken, refreshToken)
```

Problem:

`LoginResponse` now correctly represents the backend snake_case token response, but `useLogin` expected a frontend session object.

## 5. Service Facade Before Migration

`src/services/auth/authService.ts` defined:

- `AuthService`
- `authService`
- default `authService`

But `src/services/auth/index.ts` was empty, so consumers importing from `@/services/auth` failed.

## 6. Service Facade After Migration

`src/services/auth/index.ts` now exports:

```typescript
export {
  AuthService,
  authService,
} from "./authService";
```

No second singleton was introduced.

## 7. Canonical authService Owner

Canonical runtime owner:

```text
frontend/src/services/auth/authService.ts
```

Canonical singleton:

```typescript
authService
```

## 8. Canonical Public Barrel

Canonical public import path:

```typescript
import { authService } from "@/services/auth";
```

## 9. Raw LoginResponse Shape

`LoginResponse` remains the backend transport DTO:

```typescript
{
  access_token: string;
  refresh_token: string;
  access_expires_in: number;
  refresh_expires_in: number;
  token_type: string;
}
```

## 10. Application/Session Result Shape

Application-level result:

```typescript
LoginResult
```

Canonical location:

```text
frontend/src/types/auth.ts
```

Shape:

```typescript
{
  accessToken: string;
  refreshToken: string;
  accessExpiresIn: number;
  refreshExpiresIn: number;
  tokenType: string;
  identity?: Identity;
}
```

`LoginResult` is not an API response DTO.

## 11. Token Mapping

Mapping now occurs inside `AuthService.login()`:

- `access_token -> accessToken`
- `refresh_token -> refreshToken`
- `access_expires_in -> accessExpiresIn`
- `refresh_expires_in -> refreshExpiresIn`
- `token_type -> tokenType`

Hooks no longer translate backend token fields.

## 12. Identity Disposition

Identity is optional in `LoginResult`.

No identity object is fabricated because the confirmed backend login response does not return one.

`useLogin` now:

- calls `authStore.login(...)` only when `response.identity` exists
- otherwise calls `authStore.setTokens(...)`

This avoids inventing identity while preserving the existing store contract.

## 13. Tenant/Branch Disposition

The confirmed login response does not include tenant or branch projections.

No tenant or branch fields were invented or mapped during this migration.

## 14. Unsupported Operations

The following service methods remain present but route evidence was not confirmed in `app/auth/routes.py`:

- `logout`
- `refreshToken`
- `me`
- `forgotPassword`
- `resetPassword`
- `changePassword`

Their runtime behavior was not changed.

## 15. Files Inspected

Backend:

- `app/auth/routes.py`
- `app/auth/schemas.py`
- `app/services/tenant/auth/authentication_service.py`
- auth JWT/token service evidence

Frontend:

- `frontend/src/services/auth/authService.ts`
- `frontend/src/services/auth/index.ts`
- `frontend/src/hooks/queries/auth/useLogin.ts`
- `frontend/src/hooks/queries/auth/useCurrentUser.ts`
- `frontend/src/store/authStore.ts`
- `frontend/src/providers/AuthProvider.tsx`
- `frontend/src/api/refresh.ts`
- `frontend/src/api/interceptors.ts`
- canonical auth request/response DTO files

## 16. Files Created

- `frontend/docs/architecture/reviews/MIGRATION-004-AUTH-SERVICE-FACADE.md`

## 17. Files Modified

- `frontend/src/services/auth/authService.ts`
- `frontend/src/services/auth/index.ts`
- `frontend/src/hooks/queries/auth/useLogin.ts`
- `frontend/src/types/auth.ts`

## 18. Imports Updated

`useLogin` now imports:

```typescript
import type { LoginResult } from "@/types/auth";
```

No direct-file `authService` imports were introduced.

## 19. Runtime Behavior Preserved

Preserved:

- endpoint URLs
- HTTP methods
- token storage implementation
- refresh sequencing
- API interceptors
- providers
- protected routes
- navigation
- authorization behavior

Changed only at the service/hook boundary:

- login transport response is mapped to a frontend token result in `AuthService`
- `useLogin` no longer assumes identity exists

## 20. Compiler Errors Before

Pre-migration baseline:

```text
257 TypeScript errors
```

## 21. Compiler Errors After

Post-migration count:

```text
253 TypeScript errors
```

## 22. Net Reduction

```text
4 errors
```

## 23. Auth-Service Export Diagnostics Before and After

Before:

- 3 diagnostics for missing `authService` export from `@/services/auth`

After:

- 0 diagnostics for missing `authService` export from `@/services/auth`

## 24. Login Mapping Diagnostics Before and After

Before:

- `LoginResponse.identity` missing
- `LoginResponse.accessToken` missing
- `LoginResponse.refreshToken` missing

After:

- 0 login mapping diagnostics in `useLogin`

## 25. New Diagnostics

Two current-user identity-wrapper diagnostics are now visible:

- `useCurrentUser` expects `CurrentUserResponse.identity`
- canonical `CurrentUserResponse` is the backend-shaped response projection and does not include an `identity` wrapper

These were not fixed because current-user route behavior was not confirmed and this migration was limited to login response mapping.

## 26. Invariants Verified

Verified:

- Authentication consumers use the public auth service barrel.
- Exactly one `authService` singleton exists.
- `LoginResponse` remains the backend transport DTO.
- Backend token-name conversion occurs in `AuthService`.
- `useLogin` does not transform snake_case token fields.
- The store does not consume raw backend snake_case fields.
- No identity, tenant, branch, role, or permission data was fabricated.
- Authentication DTOs remain under canonical type ownership.
- No authentication endpoint behavior changed.
- No authorization logic was introduced.
- No provider or route architecture was redesigned.
- No unrelated module was intentionally changed.

## 27. Rollback Boundary

Rollback is limited to:

- `frontend/src/services/auth/authService.ts`
- `frontend/src/services/auth/index.ts`
- `frontend/src/hooks/queries/auth/useLogin.ts`
- `frontend/src/types/auth.ts`
- this migration report

## 28. Remaining Authentication Architecture Issues

Remaining issues:

- `/auth/me`, `/auth/refresh`, `/auth/logout`, and password endpoints remain unconfirmed in backend routes.
- `useCurrentUser` expects an `identity` wrapper that the canonical `CurrentUserResponse` does not provide.
- Login establishes tokens without identity when the backend response contains tokens only.
- A later migration must decide whether identity is loaded from a confirmed current-user endpoint, decoded from JWT under an ADR-approved rule, or represented as a distinct authentication initialization state.

## 29. Recommended Next Migration

Recommended next migration: Current-user contract and authentication initialization boundary.

Reason:

- Login token mapping is now isolated in the service layer.
- The remaining authentication diagnostics are about the unconfirmed current-user response shape and identity initialization.
- That migration should verify or defer `/auth/me` before changing hooks or providers.
