# Migration 048 - Frontend Current-Session Hydration

## 1. Migration Purpose

Migration 048 consumes the verified backend current-session endpoint:

```text
GET /api/auth/session
```

It establishes frontend current-session transport DTO ownership, maps the
backend session aggregate into application session contracts, hydrates
token-backed sessions through `AuthProvider`, synchronizes tenant and branch
persistence, and aligns query-scope readiness with hydrated identity.

This migration does not implement Authorization Context, route permission
checks, navigation permission policy, or domain query-key migration.

## 2. ADR Rules Applied

- ADR-004: transport response DTOs live under `src/types/responses`.
- ADR-005: session errors propagate through the existing API error pipeline.
- ADR-006: tenant and branch scope derive from verified session state.
- ADR-007: roles and permissions remain inert until Authorization Context.
- ADR-008: service, hook, store, provider, and shell boundaries remain distinct.
- ADR-009: current-session names use explicit session terminology.

## 3. Starting Baseline

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

Existing warning:

```text
Some chunks are larger than 500 kB after minification.
```

## 4. Backend Contract Consumed

Exact envelope:

```typescript
interface CurrentSessionResponse {
  session: CurrentSession;
}
```

`session.user` fields:

- `id: string`
- `email: string | null`
- `username: string | null`
- `first_name: string`
- `last_name: string | null`
- `is_active: boolean`
- `is_locked: boolean`
- `is_owner: boolean`

`session.tenant` fields:

- `id: string`
- `name: string`
- `status: string`
- `is_active: boolean`

`session.roles` fields:

- `id: string`
- `name: string`
- `code: string`

`session.permissions`:

```text
string[]
```

`session.branches` fields:

- `id: string`
- `tenant_id: string`
- `name: string`
- `code: string`
- `is_active: boolean`

`session.default_branch_id`:

```text
string | null
```

Role, permission, and branch ordering is deterministic from the backend
service.

## 5. Transport DTO Ownership

Created:

```text
frontend/src/types/responses/current-session-response.ts
```

The DTO mirrors backend snake_case exactly and is exported from:

- `frontend/src/types/responses/index.ts`
- `frontend/src/types/responses/auth.ts`
- `frontend/src/types/index.ts` through the response barrel

## 6. CurrentUserResponse Disposition

`CurrentUserResponse` remains as a private historical DTO file, but it is no
longer exported from the public response barrel.

The active current-session transport contract is:

```text
CurrentSessionResponse
```

`useCurrentUser()` remains only as a compatibility projection from
`useCurrentSession()` and does not issue a separate request.

## 7. Identity Contract

Before this migration, `Identity` required unsupported fields:

- `fullName`
- `branchId`
- `branchName`

After this migration, `Identity` contains only verified user and tenant fields:

- `id`
- `username`
- `firstName`
- `lastName`
- `email`
- `avatarUrl?`
- `isActive`
- `isLocked`
- `isOwner`
- `tenantId`
- `tenantName`

Roles and permissions remain optional inert data on `Identity`; verified
session roles and permissions are stored separately in auth session state until
Authorization Context owns frontend policy.

## 8. Application Session Contract

Created in:

```text
frontend/src/types/auth.ts
```

Application result:

```text
AuthenticatedSession
```

Fields:

- `identity`
- `branches`
- `roles`
- `permissions`
- `defaultBranchId`

Accessible branches are session-derived data. Selected branch remains shell
state.

## 9. Auth Service Method

Added:

```text
authService.getCurrentSession()
```

The method calls:

```text
API_ENDPOINTS.AUTH.SESSION
```

It maps the raw `CurrentSessionResponse` into `AuthenticatedSession` and never
returns Axios response objects.

Compatibility:

- `authService.getCurrentUser()` returns `AuthenticatedSession.identity`
- `authService.me()` remains an alias to `getCurrentUser()`

## 10. Endpoint Registry

Added one endpoint:

```text
API_ENDPOINTS.AUTH.SESSION = "/auth/session"
```

No `/api` prefix was duplicated and no endpoint alias was added.

## 11. Query Key

Added:

```text
QUERY_KEYS.auth.currentSession()
```

Shape:

```text
["identity", "session"]
```

This is identity-scoped, not tenant-scoped, because tenant identity is derived
from the session response itself.

## 12. Hook Disposition

Created:

```text
frontend/src/hooks/queries/auth/useCurrentSession.ts
```

Public exports:

- `useCurrentSession`
- `useCurrentUser` compatibility projection

No duplicate independent current-session query was introduced.

## 13. AuthProvider Initialization

`AuthProvider` now hydrates deterministic session state:

```text
stored or in-memory tokens
  -> authService.getCurrentSession()
  -> AuthenticatedSession
  -> validate selected branch
  -> synchronize storage
  -> hydrate authStore
  -> settle isInitializing
```

No token-backed session is treated as identity-ready before successful
hydration.

Invalid session handling:

- clears tokens
- clears tenant storage
- clears branch storage
- clears selected branch
- logs out auth state
- settles initialization

## 14. Auth Store Changes

`authStore` now stores:

- `identity`
- `accessToken`
- `refreshToken`
- `accessibleBranches`
- `roles`
- `permissions`
- `defaultBranchId`
- authentication flags

Added action:

```text
hydrateSession(session, accessToken, refreshToken)
```

`setTokens()` preserves current initialization state so token refresh during
startup cannot mark the session ready before identity hydration finishes.

## 15. Accessible Branch Ownership

Canonical owner:

```text
authStore.accessibleBranches
```

Accessible branches are session-derived authorization context data.

Selected branch owner remains:

```text
shellStore.selectedBranchId
```

The two concepts remain separate.

## 16. Selected Branch Validation

On hydration:

- stored branch is retained only when present in accessible branches
- stored branch is cleared when tenant changes and is not valid
- `defaultBranchId` is selected only when non-null and accessible
- no first branch is selected automatically
- no selected branch is fabricated

`useCurrentBranch()` now resolves branch display data from accessible branches
instead of fabricating name/code from the selected id.

## 17. Tenant Persistence

After successful hydration:

```text
storage.setTenantId(session.identity.tenantId)
```

The verified backend tenant overwrites stale tenant storage.

## 18. Branch Persistence

After selected-branch validation:

- valid selected branch is persisted
- invalid/stale branch is removed
- no selected branch removes branch storage

Interceptors continue to read the canonical storage values.

## 19. Login Integration

Token-only login remains supported:

```text
login success
  -> persist tokens
  -> authStore.setTokens()
  -> set initialization true
  -> AuthProvider hydrates current session
```

The login request and login response DTOs were not changed.

## 20. Logout And Invalid Session

Logout and refresh invalidation now clear:

- auth state
- tenant storage
- branch storage
- selected branch

Existing query cache clearing remains in `useLogout`. Broader scoped-cache
reset work remains deferred until domain query keys are tenant-aware.

## 21. Query Scope Behavior

`useQueryScope()` now returns tenant readiness only when:

- auth initialization is complete
- hydrated identity has a tenant id

Branch readiness requires a validated selected branch from shell state.

The hook still reads no storage and implements no authorization policy.

## 22. Authorization Separation

Roles and permissions are stored as inert session data.

This migration did not:

- implement `can(...)`
- modify route permission enforcement
- modify navigation permission policy
- hide UI actions
- add frontend authorization decisions

## 23. Static Verification

Commands run:

```bash
rg "CurrentUserResponse|CurrentSessionResponse|AuthenticatedSession" frontend/src
rg "useCurrentUser|useCurrentSession" frontend/src
rg "tenantId|tenant_id" frontend/src/store frontend/src/providers frontend/src/api frontend/src/hooks
rg "branchId|branch_id" frontend/src/store frontend/src/providers frontend/src/api frontend/src/hooks
rg "localStorage|sessionStorage" frontend/src/hooks/useQueryScope.ts frontend/src/providers/AuthProvider.tsx
rg "roles|permissions" frontend/src/routes frontend/src/navigation frontend/src/components
```

Findings:

- one canonical public current-session transport DTO exists
- one service mapping exists
- one canonical session hook exists
- `useCurrentUser` is a compatibility projection
- no storage reads exist in `useQueryScope`
- no domain query keys were migrated
- roles/permissions remain outside Authorization Context

No frontend test infrastructure was found for additional unit tests.

## 24. Files Inspected

Inspected:

- `app/auth/schemas.py`
- `app/auth/routes.py`
- `app/services/tenant/auth/current_session_service.py`
- Migration 047 report
- frontend auth DTOs
- frontend auth service and hooks
- auth store
- shell store
- AuthProvider
- storage service
- API endpoints/interceptors/refresh
- query keys
- user/tenant/branch/query-scope hooks

## 25. Files Created

- `frontend/src/types/responses/current-session-response.ts`
- `frontend/src/hooks/queries/auth/useCurrentSession.ts`
- `frontend/docs/architecture/reviews/MIGRATION-048-FRONTEND-CURRENT-SESSION-HYDRATION.md`

## 26. Files Modified

- `frontend/src/types/auth.ts`
- `frontend/src/types/responses/index.ts`
- `frontend/src/types/responses/auth.ts`
- `frontend/src/api/endpoints.ts`
- `frontend/src/services/auth/authService.ts`
- `frontend/src/hooks/queries/auth/index.ts`
- `frontend/src/hooks/queries/auth/useCurrentUser.ts`
- `frontend/src/hooks/queries/auth/useLogin.ts`
- `frontend/src/hooks/queries/auth/useLogout.ts`
- `frontend/src/providers/AuthProvider.tsx`
- `frontend/src/store/authStore.ts`
- `frontend/src/hooks/useQueryScope.ts`
- `frontend/src/hooks/useCurrentBranch.ts`
- `frontend/src/components/layout/UserMenu.tsx`
- `frontend/src/api/refresh.ts`
- `frontend/src/lib/queryKeys.ts`

## 27. Verification Results

Pre-migration:

```text
npx tsc -b --pretty false: PASS
npm run build: PASS
```

Post-migration:

```text
npx tsc -b --pretty false: PASS
npm run build: PASS
```

Warning:

```text
Some chunks are larger than 500 kB after minification.
```

No new warning category was introduced.

## 28. Runtime Behavior Confirmation

Confirmed by implementation and static checks:

- current-session transport has one canonical DTO
- transport DTO uses backend snake_case
- auth service maps to application contracts
- identity derives from verified backend session data
- tenant persistence is server-derived
- branch selection is validated
- no first-branch auto-selection exists
- token-only sessions do not fabricate identity
- initialization settles deterministically
- domain query keys remain unchanged
- backend files were not modified by Migration 048

## 29. Remaining Work

Deferred:

- Authorization Context
- route/navigation/component permission policy
- domain tenant-aware query-key migration
- scoped cache clearing on tenant/branch switch
- frontend tests once a test harness exists

## 30. Rollback Boundary

Rollback is limited to frontend auth/session files changed in this migration:

- remove current-session DTO and hook
- restore auth service current-user unsupported behavior
- restore token-only AuthProvider initialization
- restore previous auth store shape
- remove current-session query key
- remove this report

No backend rollback is required for Migration 048.

## 31. Recommended Next Migration

Recommended next migration:

```text
Migration 049 - Frontend Authorization Context Boundary
```

Goal:

```text
Consume inert session roles and permissions through a centralized frontend
Authorization Context without changing backend authorization as the security
boundary.
```
