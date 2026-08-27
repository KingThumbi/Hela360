# Migration 046 - Current Session Identity and Scope Source Alignment

## 1. Migration Purpose

Migration 046 inspects the current authenticated-session architecture and
determines whether the frontend can safely establish one canonical source for:

- frontend identity
- active tenant identity
- active branch identity
- transport tenant and branch headers
- future scoped TanStack Query keys

This migration is inspection-first and is classified as blocked. No active
domain query keys were migrated.

## 2. Selected Path

Selected path:

```text
Path C - No verified identity source exists
```

Classification:

```text
Blocked architecture migration
```

Reason:

```text
The backend currently registers POST /api/auth/login only. No registered
current-session/current-user endpoint was found, and the frontend has no
accepted JWT decoding boundary that can produce the current Identity contract.
```

## 3. Baseline Verification

Pre-migration verification:

```bash
cd /home/thumbi/Hela360/frontend
npx tsc -b --pretty false
npm run build
```

Result:

```text
TypeScript exit code: 0
Vite build exit code: 0
```

Observed warning:

```text
Some chunks are larger than 500 kB after minification.
```

The chunk-size warning is unchanged and was not addressed.

## 4. Frontend Identity Contract

Current owner:

```text
frontend/src/types/auth.ts
```

`Identity` fields:

- `id`
- `username`
- `fullName`
- `email`
- `avatarUrl?`
- `isActive`
- `tenantId`
- `tenantName`
- `branchId`
- `branchName`
- `roles`
- `permissions`

Important finding:

```text
The frontend Identity contract requires tenantName, branchName, fullName,
roles, and permissions. The verified login response does not provide them, and
the verified JWT claims do not provide tenantName, branchName, or fullName.
```

## 5. Token State

Current owner:

```text
frontend/src/store/authStore.ts
```

Token fields:

- `accessToken: string | null`
- `refreshToken: string | null`

Authentication flags:

- `isAuthenticated`
- `isLoading`
- `isInitializing`

Actions:

- `login(identity, accessToken, refreshToken)`
- `hydrate(identity, accessToken, refreshToken)`
- `updateIdentity(identity)`
- `setTokens(accessToken, refreshToken)`
- `setLoading(loading)`
- `setInitializing(initializing)`
- `reset()`
- `logout()`

Token-only behavior:

```text
setTokens() marks isAuthenticated true and leaves identity unchanged.
```

This preserves token-backed authentication without fabricating identity.

## 6. Login Flow

Current owners:

```text
frontend/src/services/auth/authService.ts
frontend/src/hooks/queries/auth/useLogin.ts
frontend/src/features/auth/components/LoginForm.tsx
```

Verified behavior:

- `AuthService.login()` posts to `API_ENDPOINTS.AUTH.LOGIN`.
- `AuthService.login()` maps snake_case backend token fields into `LoginResult`.
- `LoginResult.identity` remains optional.
- `useLogin()` calls `authStore.login()` only when identity exists.
- `useLogin()` otherwise calls `authStore.setTokens()`.
- `LoginForm` currently submits `tenant_id: null` and `branch_id: null`.

Disposition:

```text
Login cannot be the canonical frontend identity source because the verified
login response is token-only.
```

## 7. Startup Initialization

Current owner:

```text
frontend/src/providers/AuthProvider.tsx
```

Behavior:

- no persisted tokens: `isInitializing` becomes false
- persisted tokens: tokens are restored with `setTokens()`
- restore failure: local auth state logs out

Identity persistence:

```text
No Identity object is persisted.
```

Startup implication:

```text
An authenticated token-backed session can exist with identity === null.
```

## 8. Persistence Keys

Current owner:

```text
frontend/src/lib/storage.ts
frontend/src/constants/storage.ts
```

Authentication keys:

- `hela360.access_token`
- `hela360.refresh_token`

Tenant and branch keys:

- `hela360.tenant.id`
- `hela360.branch.id`

Logout/session reset:

```text
storage.clearSession()
  -> remove access token
  -> remove refresh token
  -> remove tenant id
  -> remove branch id
```

Important finding:

```text
No current frontend login or identity flow writes tenant or branch storage.
```

## 9. Transport Scope Source

Current owner:

```text
frontend/src/api/interceptors.ts
```

Headers:

- `Authorization`
- `X-Tenant-ID`
- `X-Branch-ID`
- `X-Request-ID`

Current tenant header source:

```text
storage.getTenantId()
```

Current branch header source:

```text
storage.getBranchId()
```

Disposition:

```text
Transport scope is storage-backed, while query scope is identity/shell-backed.
These remain duplicate sources of truth.
```

## 10. Query Scope Source

Current owner:

```text
frontend/src/hooks/useQueryScope.ts
```

Tenant source:

```text
authStore.identity?.tenantId
```

Branch source:

```text
shellStore.selectedBranchId
```

Readiness semantics:

- no tenant identity: tenant scope is unavailable
- no branch selection: branch scope is unavailable
- no placeholder tenant or branch is generated

Disposition:

```text
Migration 045 query-scope foundation remains valid, but active scoped queries
must wait until identity and transport scope are reconciled.
```

## 11. Shell Branch State

Current owners:

```text
frontend/src/store/shellStore.ts
frontend/src/hooks/useCurrentBranch.ts
frontend/src/hooks/useInitializeShell.ts
```

Behavior:

- `selectedBranchId` is stored in shell state.
- `useInitializeShell()` restores branch from storage into shell state.
- `useCurrentBranch()` derives placeholder branch display information from the
  selected branch id.
- `setBranch()` updates shell state only.

Important finding:

```text
Branch restoration is storage-to-shell only. Branch selection is not currently
persisted back to storage by the shell hook/store.
```

## 12. Backend Route Registration

Auth blueprint registration:

```text
app/auth/__init__.py registers auth bp at /api/auth
app/__init__.py registers auth_bp at /api/auth
```

Registered auth route found:

| Route | Method | Response | Classification |
| --- | --- | --- | --- |
| `/api/auth/login` | POST | `LoginResponse` token pair | Confirmed |

No registered route found for:

- `/api/auth/me`
- `/api/auth/current`
- `/api/auth/current-user`
- `/api/auth/session`
- `/api/auth/profile`
- `/api/auth/whoami`
- `/api/auth/refresh`
- `/api/auth/logout`

Schemas and services exist for some of these concepts, but route registration
is the required support boundary for frontend use.

## 13. Current-Session Endpoint Decision

Potential current-user/session endpoint classification:

```text
Unsupported
```

Evidence:

- `app/auth/schemas.py` defines `CurrentUserResponse`.
- `frontend/src/types/responses/current-user-response.ts` mirrors that DTO.
- `AuthService.getCurrentUser()` intentionally rejects.
- `useCurrentUser()` is disabled.
- no route decorator or route registration returns `CurrentUserResponse`.

Disposition:

```text
Do not invent a current-user endpoint and do not wire AuthProvider to /auth/me.
```

## 14. JWT Claim Inventory

Backend owner:

```text
app/auth/jwt.py
```

Access-token claims deliberately emitted:

- `sub`
- `user_id`
- `tenant_id`
- `session_id`
- `type`
- `jti`
- `iat`
- `nbf`
- `exp`
- `iss`
- `aud`
- optional `branch_id`
- optional `role`
- optional `permissions`

Refresh-token claims deliberately emitted:

- `sub`
- `user_id`
- `tenant_id`
- `session_id`
- `type`
- `jti`
- `iat`
- `nbf`
- `exp`
- `iss`
- `aud`

Refresh tokens intentionally omit:

- `branch_id`
- `role`
- `permissions`

## 15. JWT Claim Decision

JWT claims are not sufficient for this frontend migration.

Reasons:

- the frontend has no accepted token-decoding owner
- no frontend token-claims type exists
- no frontend validation boundary exists
- the current `Identity` contract requires names not present in JWT claims
- refresh tokens omit branch and authorization data
- `/api/auth/refresh` is not currently registered even though service support
  exists
- decoding claims would not resolve tenantName, branchName, or fullName

Disposition:

```text
Do not decode JWTs in this migration.
```

## 16. Canonical Session Concepts

The following concepts are distinct:

| Concept | Current disposition |
| --- | --- |
| `LoginResponse` | Backend transport DTO for login token response. |
| `CurrentSessionResponse` | Not implemented. Needed for canonical frontend session restore. |
| `CurrentUserResponse` | Schema/DTO exists, but no registered backend route returns it. |
| `Identity` | Frontend application identity model. Cannot be built from login response. |
| `AuthenticatedSession` | Not implemented as a frontend contract. |
| `TokenPair` | Backend/internal and frontend token result concepts exist, but not a full identity source. |

## 17. Required Backend Contract

Recommended backend endpoint:

```text
GET /api/auth/session
```

Required properties:

- authenticated route protected by current access token
- returns the current user id
- returns username/email/name fields needed by `Identity`
- returns tenant id
- returns tenant display name
- returns active branch id when applicable
- returns active branch display name when applicable
- returns roles
- returns permissions
- returns active/inactive account state
- returns no fabricated branch when the user/session has no active branch
- uses a documented response DTO such as `CurrentSessionResponse`

This endpoint should be the canonical source for frontend identity, tenant
scope, branch scope, and post-token startup restoration.

## 18. Frontend Follow-Up Contract

After a backend session endpoint is registered, the frontend should:

- add a canonical `CurrentSessionResponse` DTO under `src/types/responses`
- map `CurrentSessionResponse` to `Identity` inside `authService`
- expose `authService.getCurrentSession()` or `getCurrentIdentity()`
- update `AuthProvider` to resolve token-only startup through that method
- store tenant and branch transport values from the verified session source
- update shell selected branch only from verified session or explicit branch
  switch
- leave Authorization Context for a later migration
- leave domain query-key migration for a later migration

## 19. Files Inspected

Frontend:

- `frontend/src/types/auth.ts`
- `frontend/src/types/requests/`
- `frontend/src/types/responses/`
- `frontend/src/services/auth/authService.ts`
- `frontend/src/hooks/queries/auth/`
- `frontend/src/store/authStore.ts`
- `frontend/src/providers/AuthProvider.tsx`
- `frontend/src/providers/ApplicationProvider.tsx`
- `frontend/src/hooks/useApplication.ts`
- `frontend/src/hooks/useQueryScope.ts`
- `frontend/src/hooks/useTenant.ts`
- `frontend/src/hooks/useCurrentBranch.ts`
- `frontend/src/hooks/useInitializeShell.ts`
- `frontend/src/store/shellStore.ts`
- `frontend/src/lib/storage.ts`
- `frontend/src/api/interceptors.ts`
- `frontend/src/api/refresh.ts`
- `frontend/src/features/auth/components/LoginForm.tsx`

Backend:

- `app/__init__.py`
- `app/auth/__init__.py`
- `app/auth/routes.py`
- `app/auth/schemas.py`
- `app/auth/jwt.py`
- `app/auth/decorators.py`
- `app/services/tenant/auth/authentication_service.py`
- `app/services/tenant/auth/jwt_service.py`
- `app/services/tenant/auth/session_service.py`
- `app/services/tenant/auth/refresh_token_service.py`
- `app/services/tenant/auth/tests/`
- `app/api/`
- `app/schemas/`
- `app/serializers/`
- `app/models/`

## 20. Files Created

- `frontend/docs/architecture/reviews/MIGRATION-046-CURRENT-SESSION-IDENTITY-SCOPE-ALIGNMENT.md`

## 21. Files Modified

No runtime source files were modified.

## 22. Explicit Non-Changes

This migration did not:

- modify backend source
- invent a current-user endpoint
- decode JWTs
- fabricate identity
- change login behavior
- change refresh behavior
- change logout behavior
- change route protection
- change transport headers
- migrate domain query keys
- implement Authorization Context
- alter providers or stores broadly
- weaken TypeScript settings

## 23. Post-Migration Verification

Post-migration verification:

```bash
cd /home/thumbi/Hela360/frontend
npx tsc -b --pretty false
npm run build
```

Result:

```text
TypeScript exit code: 0
Vite build exit code: 0
```

Observed warning:

```text
Some chunks are larger than 500 kB after minification.
```

No source behavior changed.

## 24. Recommended Next Migration

Recommended next migration:

```text
Migration 047 - Backend Current Session Endpoint Contract
```

Goal:

```text
Implement and register a backend current-session endpoint, then wire the
frontend to hydrate Identity, tenant scope, branch scope, and transport scope
from that single verified response.
```
