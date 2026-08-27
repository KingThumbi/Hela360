# Migration 005 - Current User Boundary

## 1. Migration Purpose

Migration 005 resolved the current-user contract mismatch and established the authentication initialization boundary without fabricating frontend identity.

The migration removed the invalid assumption that `CurrentUserResponse` contains an `identity` wrapper and stopped the frontend from calling an unverified current-user endpoint.

## 2. ADR Rules Applied

- ADR-001: authentication service remains the boundary for backend communication.
- ADR-004: `CurrentUserResponse` remains a transport DTO under `src/types/responses`.
- ADR-005: unsupported current-user retrieval is surfaced as an explicit service error rather than a fake anonymous user.
- ADR-006: tenant and branch context are not fabricated from token presence.
- ADR-007: authorization remains separate and is not implemented in this migration.
- ADR-008: hooks consume the service facade and do not call Axios or endpoints directly.
- ADR-009: `getCurrentUser()` uses business-oriented naming.

## 3. Backend Routes Searched

Searched backend route registrations and route decorators across `app/`.

Confirmed registered blueprints:

- `auth_bp` under `/api/auth`
- `health_bp`, `products_bp`, `customers_bp`, and `sales_bp` under `/api`

Confirmed auth route:

- `POST /api/auth/login`

No confirmed backend route was found for:

- `/api/auth/me`
- `/api/auth/current-user`
- `/api/users/me`
- `/api/session`
- `/api/profile`

## 4. Current-User Endpoint Disposition

No current-user endpoint is currently supported by verified backend route evidence.

`app/auth/schemas.py` defines `CurrentUserResponse`, but no route serializes or returns it.

## 5. JWT Identity Evidence

Backend JWTs contain verified claims:

- `user_id`
- `tenant_id`
- optional `branch_id`
- access-token `role`
- access-token `permissions`
- `session_id`
- token type and JWT metadata

These claims are created in `app/auth/jwt.py` and issued by `authentication_service._issue_tokens()`.

The frontend does not currently decode JWTs, and no accepted frontend token-decoding boundary was found.

## 6. Persisted Authentication State

Only tokens are persisted through `frontend/src/lib/storage.ts`:

- `hela360.access_token`
- `hela360.refresh_token`

No identity object is persisted locally.

## 7. Pre-Migration Current-User Flow

Before this migration:

```text
useCurrentUser
  -> authService.me()
  -> API_ENDPOINTS.AUTH.ME
  -> /auth/me
  -> hook expected query.data.identity
```

The backend route was unverified and the hook expected a wrapper not present in `CurrentUserResponse`.

## 8. Canonical Transport Contract

Canonical transport DTO:

```text
CurrentUserResponse
frontend/src/types/responses/current-user-response.ts
```

Shape:

- `id`
- `email`
- `username`
- `first_name`
- `last_name`
- `tenant_id`
- `branch_id`
- `role`
- `permissions`
- `is_owner`
- `is_active`

This DTO does not contain `{ identity: ... }`.

## 9. Canonical Application Identity Contract

Canonical frontend identity contract:

```text
Identity
frontend/src/types/auth.ts
```

Identity remains an application/session model, not a backend response wrapper.

No mapping from `CurrentUserResponse` to `Identity` was added because there is no supported current-user source.

## 10. Wrapper-Shape Disposition

The `{ identity: ... }` current-user wrapper is unsupported.

The hook no longer reads `query.data.identity`, and no replacement wrapper was introduced.

## 11. Selected Implementation Path

Selected path:

```text
Path C - No Supported Current-User Capability
```

Classification:

```text
Not currently supported
```

## 12. Service Behavior

`authService.getCurrentUser()` now explicitly rejects with:

```text
Current-user retrieval is not supported by the verified backend contract.
```

The legacy `me()` method remains only as a compatibility alias to the unsupported service method. It no longer calls `API_ENDPOINTS.AUTH.ME`.

`validateSession()` now depends on `getCurrentUser()` and therefore returns `false` until backend support exists.

## 13. Hook Behavior

`useCurrentUser()` now creates a disabled React Query using `QUERY_KEYS.auth.currentUser()`.

It does not:

- call Axios
- call `/auth/me`
- reshape DTOs
- decode tokens
- mutate auth store identity
- logout users because current-user retrieval is unsupported

## 14. Store Behavior

`authStore` now distinguishes:

- `identity`: loaded application identity, nullable
- `accessToken`: token state, nullable
- `refreshToken`: token state, nullable
- `isAuthenticated`: token-backed authenticated session state
- `isInitializing`: startup restoration state

`setTokens()` marks `isAuthenticated: true` while leaving `identity` unchanged.

## 15. Initialization Behavior

`AuthProvider` now completes initialization deterministically:

- no persisted tokens: `isInitializing` becomes `false`
- persisted tokens: tokens are restored and `isInitializing` becomes `false`
- restore failure: logout clears auth state and `isInitializing` becomes `false`

No identity is fabricated during reload.

## 16. Identity Availability

Identity remains unavailable after token-only login and reload until backend support exists.

Token presence is not treated as loaded identity.

## 17. Tenant and Branch Implications

No tenant or branch names are fabricated.

The backend JWT contains tenant and optional branch identifiers, but the frontend does not decode those claims in this migration.

Identity-dependent tenant and branch UI remains incomplete until a supported identity/session source exists.

## 18. Authorization Implications

Authorization remains incomplete.

Roles and permissions are present in verified backend access-token claims, but the frontend does not decode tokens and no authorization context was implemented.

Missing identity must not be treated as permission denial.

## 19. Files Inspected

Backend:

- `app/__init__.py`
- `app/auth/routes.py`
- `app/auth/__init__.py`
- `app/auth/schemas.py`
- `app/auth/jwt.py`
- `app/auth/decorators.py`
- `app/api/products.py`
- `app/api/customers.py`
- `app/api/sales.py`
- `app/api/utils.py`
- `app/services/tenant/auth/authentication_service.py`
- `app/services/tenant/auth/jwt_service.py`
- `app/services/tenant/auth/session_service.py`
- `app/services/tenant/auth/refresh_token_service.py`
- `app/services/tenant/auth/password_service.py`
- `app/services/tenant/auth/authorization_service.py`
- `app/services/tenant/auth/tests/`

Frontend:

- `frontend/src/hooks/queries/auth/useCurrentUser.ts`
- `frontend/src/hooks/queries/auth/useLogin.ts`
- `frontend/src/services/auth/authService.ts`
- `frontend/src/types/responses/current-user-response.ts`
- `frontend/src/types/responses/auth.ts`
- `frontend/src/types/responses/index.ts`
- `frontend/src/types/auth.ts`
- `frontend/src/store/authStore.ts`
- `frontend/src/providers/AuthProvider.tsx`
- `frontend/src/providers/ApplicationProvider.tsx`
- `frontend/src/routes/ProtectedRoute.tsx`
- `frontend/src/api/endpoints.ts`
- `frontend/src/api/interceptors.ts`
- `frontend/src/api/refresh.ts`
- `frontend/src/lib/storage.ts`
- `frontend/src/lib/queryKeys.ts`
- `frontend/src/lib/queryInvalidation.ts`
- `frontend/src/hooks/useNavigation.ts`
- `frontend/src/hooks/useUserMenu.ts`
- `frontend/src/hooks/useCurrentBranch.ts`

## 20. Files Created

- `frontend/docs/architecture/reviews/MIGRATION-005-CURRENT-USER-BOUNDARY.md`

## 21. Files Modified

- `frontend/src/services/auth/authService.ts`
- `frontend/src/hooks/queries/auth/useCurrentUser.ts`
- `frontend/src/store/authStore.ts`
- `frontend/src/providers/AuthProvider.tsx`

## 22. Compiler Errors Before

Pre-migration requested baseline:

```text
253 TypeScript errors
```

Observed pre-migration count:

```text
253 TypeScript errors
```

## 23. Compiler Errors After

Observed post-migration count:

```text
251 TypeScript errors
```

## 24. Net Reduction

```text
2 TypeScript errors
```

## 25. Current-User Diagnostics Before and After

Before:

```text
src/hooks/queries/auth/useCurrentUser.ts(32,21): Property 'identity' does not exist on type 'NoInfer<CurrentUserResponse>'.
src/hooks/queries/auth/useCurrentUser.ts(33,33): Property 'identity' does not exist on type 'CurrentUserResponse'.
```

After:

```text
No current-user identity-wrapper diagnostics remain.
```

## 26. New Diagnostics

No new TypeScript diagnostics were introduced by this migration.

Remaining auth-adjacent diagnostics are pre-existing and outside this migration:

- duplicate auth hook barrel exports
- missing login component modules
- application provider/context export mismatch
- protected route constant/context typing issues

## 27. Invariants Verified

- Current-user transport and application contracts remain distinct.
- Backend response shapes were not modified.
- Hooks do not transform `CurrentUserResponse`.
- Identity is not fabricated.
- Token presence and identity availability remain separate states.
- Authentication and authorization remain separate.
- Initialization completes deterministically.
- Services remain the backend abstraction boundary.
- No unsupported endpoint call was added.
- No tenant, branch, role, or permission data was invented.
- Provider, route, navigation, and authorization architecture were not redesigned.
- Canonical DTO ownership remains intact.

## 28. Rollback Boundary

Rollback is limited to:

- `frontend/src/services/auth/authService.ts`
- `frontend/src/hooks/queries/auth/useCurrentUser.ts`
- `frontend/src/store/authStore.ts`
- `frontend/src/providers/AuthProvider.tsx`
- this migration report

No backend rollback is required.

## 29. Remaining Authentication Blockers

- Backend current-user/session endpoint is missing.
- Frontend identity cannot be loaded after login or reload.
- Tenant and branch display names are unavailable.
- Authorization context cannot be populated without supported identity/session data.
- Refresh, logout, password recovery, and password change routes remain partially evidenced or unverified.

## 30. Backend Work Required

Implement and document a supported current-user or session endpoint, for example:

```text
GET /api/auth/me
```

The backend contract should explicitly define method, auth requirement, tenant scope, branch scope, response payload, and error behavior.

Alternatively, formally approve a frontend JWT-decoding boundary with the exact verified claims allowed for frontend session restoration.

## 31. Recommended Next Migration

Migration 006 should address authentication public exports and provider composition blockers before authorization work begins.

Recommended scope:

- normalize auth hook barrel exports
- stabilize provider public barrels
- resolve `useApplication` / `ApplicationProvider` context typing
- keep authorization and navigation behavior out of scope
