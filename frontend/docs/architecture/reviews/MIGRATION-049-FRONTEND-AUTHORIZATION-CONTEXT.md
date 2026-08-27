# Migration 049 - Frontend Authorization Context Boundary

## 1. Migration Purpose

Migration 049 establishes the canonical frontend authorization boundary over
the effective permission strings hydrated from:

```text
GET /api/auth/session
```

The backend remains the security boundary. Frontend checks are usability-only
and support navigation visibility, route eligibility feedback, action
visibility, and consistent local permission checks.

This migration does not migrate tenant-aware query keys, redesign routes,
change backend authorization, or sweep feature-level buttons.

## 2. ADR Rules Applied

- ADR-006: authorization is tenant-derived from the authenticated session; tenant
  and branch ownership remain separate.
- ADR-007: frontend authorization consumes backend-originated permissions and
  does not hardcode role-name decisions in components.
- ADR-008: authorization is a shared infrastructure boundary with a public API.
- ADR-009: names use explicit service, provider, and hook terminology.

## 3. Clean Starting Baseline

Commands:

```bash
cd /home/thumbi/Hela360/frontend
npx tsc -b --pretty false
npm run build
```

Result:

```text
TypeScript errors: 0
Vite build: PASS
```

Existing warning recorded only:

```text
Some chunks are larger than 500 kB after minification.
```

## 4. Current Authorization Inventory

Frontend authorization surface before implementation:

- `frontend/src/authorization/PermissionProvider.tsx`: empty placeholder.
- `frontend/src/authorization/PermissionGuard.tsx`: empty placeholder.
- `frontend/src/authorization/RoleGuard.tsx`: empty placeholder.
- `frontend/src/authorization/index.ts`: empty placeholder.
- `frontend/src/navigation/helpers.ts`: pure navigation filtering by supplied
  permission strings.
- `frontend/src/hooks/useNavigation.ts`: active consumer, previously read
  `identity?.permissions ?? []`.
- `frontend/src/navigation/navigation.ts`: static navigation registry with
  `permission` metadata.
- `frontend/src/navigation/permissions.ts`: frontend navigation permission
  constants and a closed `Permission` type for navigation metadata.
- `frontend/src/routes/ProtectedRoute.tsx`: authentication-only route guard.
- `frontend/src/app/router.tsx`: no route-level permission metadata.
- `frontend/src/components/navigation/SidebarGroup.tsx`: presentation-only,
  no permission logic.
- `frontend/src/components/layout/UserMenu.tsx`: displays roles from identity;
  no authorization decision.

Search findings:

- permission-check implementations: navigation filtering only.
- role-name checks: none found in `frontend/src`.
- owner bypasses: none found in frontend authorization decisions.
- navigation filtering functions: `filterNavigation`,
  `filterNavigationSection`, `filterNavigationByPermissions`.
- route protection decisions: authentication and initialization only.
- component-level authorization conditions: none found.
- empty authorization placeholders: three component/provider placeholders and
  the authorization barrel.
- duplicate authorization helpers: none active.
- public authorization exports before migration: none.
- active consumer before migration: `useNavigation`.

## 5. Permission Source

The source is `authStore.permissions`, hydrated from
`AuthenticatedSession.permissions`, mapped by `authService.getCurrentSession()`
from `CurrentSessionResponse.session.permissions`.

Migration 047 records that backend permissions are:

- field name: `permissions`;
- runtime type: `string[]`;
- uniqueness: effective permissions are deduplicated by backend authorization
  context and returned as sorted strings;
- ordering: deterministic sorted order;
- canonical format: dot-notation strings returned by the backend;
- wildcard permissions: backend has reserved `*` semantics, but the current
  session contract returns effective strings only and the frontend does not
  duplicate wildcard matching;
- owner overrides: backend `AuthorizationService` applies owner/platform
  override behavior during authorization checks. The frontend does not recreate
  `isOwner` bypass logic;
- platform permissions: not distinguishable by frontend contract beyond the
  returned permission strings;
- null or missing semantics: missing/unauthenticated permissions are treated as
  an empty list;
- initialization semantics: checks deny before session hydration completes.

## 6. Permission-Code Type Disposition

Selected path:

```text
Path A - Permission codes are dynamic backend strings
```

Canonical frontend type:

```typescript
export type PermissionCode = string;
```

Reason: the verified current-session contract returns backend-owned effective
permission strings. The frontend must not maintain a closed union that can drift
from backend configuration.

`frontend/src/navigation/permissions.ts` remains navigation metadata. Its
`Permission` alias now resolves to `PermissionCode` so navigation metadata can
accept backend-owned dynamic permission strings without promoting the local
constant list into the authorization engine.

## 7. Pure Authorization Engine

Owner:

```text
frontend/src/authorization/authorizationService.ts
```

API:

```text
can(permissions, permission): boolean
cannot(permissions, permission): boolean
canAny(permissions, requiredPermissions): boolean
canAll(permissions, requiredPermissions): boolean
```

Behavior:

- accepts `ReadonlySet<PermissionCode>` or `readonly PermissionCode[]`;
- performs exact deterministic membership checks;
- safely denies absent permissions;
- denies empty requirement arrays for `canAny` and `canAll`;
- deduplicates duplicate effective permissions through `Set`;
- imports no React, stores, providers, storage, routes, APIs, tenant scope, or
  branch scope;
- does not inspect roles;
- does not implement wildcard semantics or owner bypasses.

## 8. AuthorizationProvider

Owner:

```text
frontend/src/providers/AuthorizationProvider.tsx
```

The provider consumes `authStore` session state only:

- `isAuthenticated`;
- `isInitializing`;
- `identity`;
- `permissions`.

It derives an immutable permission snapshot for the current render and exposes:

```text
permissions
isAuthorizationReady
can
canAny
canAll
cannot
```

During initialization, unauthenticated state, logout, and invalid session reset,
`permissions` is empty and every permission check denies.

## 9. Provider Composition

Updated composition:

```text
ThemeProvider
QueryProvider
AuthProvider
AuthorizationProvider
ShellProvider
ApplicationProvider
TooltipProvider
```

`AuthorizationProvider` is inside `AuthProvider`, mounted once, and does not
alter Query, Router, Shell, Tooltip, or authentication behavior.

## 10. Canonical Hook

Owner:

```text
frontend/src/hooks/useAuthorization.ts
```

Public boundary:

```text
frontend/src/authorization/index.ts
```

The hook consumes only `AuthorizationContext`, returns a typed
`AuthorizationContextValue`, and throws:

```text
useAuthorization must be used within an AuthorizationProvider.
```

It does not read stores, call APIs, inspect roles, or duplicate helper logic.

## 11. Navigation Integration

`frontend/src/hooks/useNavigation.ts` now consumes:

```text
useAuthorization().permissions
```

The static navigation registry, route paths, navigation ids, and navigation
permission metadata were not changed. Navigation filtering remains
usability-only and deny-safe during initialization.

## 12. ProtectedRoute Integration

Deferred.

`ProtectedRoute` is currently auth-only and `app/router.tsx` has no verified
route permission metadata or access-denied route. Adding permission enforcement
would require route-contract design beyond this boundary migration.

## 13. Component Gate Disposition

Deferred.

Existing active components do not duplicate permission rendering logic. Empty
placeholder files remain untouched except for the canonical authorization
barrel. No `Can`, `Authorized`, or `PermissionGate` primitive was introduced.

## 14. Role Data Disposition

Roles remain available for display, administration screens, session
information, and troubleshooting.

Verified frontend role usage is display-only:

```text
frontend/src/components/layout/UserMenu.tsx
```

No role-name authorization checks were found in `frontend/src`.

## 15. Owner Override Disposition

`Identity.isOwner` remains hydrated session data. The frontend does not use it
as an authorization bypass.

Owner and platform override behavior stays backend-owned in
`AuthorizationService`; frontend checks consume only the resulting effective
permission list.

## 16. Tenant And Branch Separation

Authorization Context does not switch tenants, select branches, validate branch
membership, build query scopes, set transport headers, or mutate storage.

Those responsibilities remain in auth hydration, shell state, query-scope, and
transport boundaries.

## 17. Backend Enforcement Findings

Sampled protected backend routes:

- `app/api/products.py`: permission decorators present.
- `app/api/customers.py`: permission decorators present.
- `app/api/suppliers.py`: permission decorators present.
- `app/api/sales.py`: permission decorators present for sales and customer
  helper endpoints.
- `app/auth/routes.py`: current-session endpoint requires authentication.

Potential backend gaps recorded, not fixed:

- `app/api/inventory.py`, `app/api/tenants.py`, `app/api/health.py`, and
  `app/api_sales.py` did not show matching permission decorators in the static
  scan.

The frontend authorization context is not presented as compensation for any
backend enforcement gap.

## 18. Tests And Static Verification

No frontend test infrastructure exists in the repository. No test package was
installed.

Static verification commands run:

```bash
rg "hasRole|role ===|roles\\.includes|isAdmin|isOwner" frontend/src
rg "hasPermission|can\\(|canAny|canAll|cannot" frontend/src
rg "permissions" frontend/src/navigation frontend/src/routes frontend/src/components
rg "AuthorizationProvider|useAuthorization" frontend/src
```

Confirmed:

- one canonical authorization context;
- one canonical authorization hook;
- pure engine reads no store or storage;
- migrated navigation does not inspect roles;
- no backend permission algorithm was duplicated;
- no tenant or branch scope ownership was added.

## 19. Files Inspected

Inspected:

- required ADRs 006 through 009;
- Migration 044, 047, and 048 reports;
- `frontend/src/authorization/`;
- `frontend/src/providers/`;
- `frontend/src/store/authStore.ts`;
- `frontend/src/types/auth.ts`;
- `frontend/src/hooks/useApplication.ts`;
- `frontend/src/hooks/useNavigation.ts`;
- `frontend/src/navigation/`;
- `frontend/src/routes/ProtectedRoute.tsx`;
- `frontend/src/app/router.tsx`;
- `frontend/src/components/`;
- `frontend/src/features/`;
- sampled backend route and authorization files.

## 20. Files Created

- `frontend/src/authorization/authorizationService.ts`
- `frontend/src/providers/AuthorizationProvider.tsx`
- `frontend/src/hooks/useAuthorization.ts`
- `frontend/docs/architecture/reviews/MIGRATION-049-FRONTEND-AUTHORIZATION-CONTEXT.md`

## 21. Files Modified

- `frontend/src/types/auth.ts`
- `frontend/src/authorization/index.ts`
- `frontend/src/providers/index.ts`
- `frontend/src/providers/AppProvider.tsx`
- `frontend/src/hooks/useNavigation.ts`
- `frontend/src/navigation/helpers.ts`
- `frontend/src/navigation/permissions.ts`

No backend source files were modified.

## 22. Verification Results

Before:

```text
npx tsc -b --pretty false: PASS
npm run build: PASS
```

After:

```text
npx tsc -b --pretty false: PASS
npm run build: PASS
```

Warning:

```text
Some chunks are larger than 500 kB after minification.
```

No new warning category was introduced.

## 23. Runtime Behavior Confirmation

Confirmed by implementation and static checks:

- effective permissions originate from session hydration;
- token-only pre-hydration state is not permissive;
- unauthenticated users have no frontend permissions;
- logout clears authorization because `authStore.logout()` clears
  `permissions`;
- refreshed session permissions replace the provider snapshot;
- navigation filtering uses the canonical authorization boundary;
- ProtectedRoute remains authentication-only;
- feature-level authorization remains deferred.

## 24. Invariants Verified

Verified:

1. Effective permissions originate from backend current-session response.
2. Frontend does not recompute effective permissions.
3. Roles are not used as permission substitutes.
4. Authorization engine is pure and stateless.
5. AuthorizationProvider consumes hydrated session state.
6. Authorization checks deny safely before hydration.
7. Logout clears authorization state.
8. Navigation filtering remains usability-only.
9. Backend remains the security boundary.
10. Tenant and branch responsibilities remain separate.
11. No domain query key was migrated.
12. No backend file was changed.
13. TypeScript remains at zero errors.
14. Production build remains successful.

## 25. Rollback Boundary

Rollback is limited to:

- remove `authorizationService`;
- remove `AuthorizationProvider`;
- remove `useAuthorization`;
- restore `useNavigation` to its previous direct permission input;
- remove public authorization/provider exports;
- remove this report.

## 26. Recommended Next Migration

Recommended next migration:

```text
Migration 050 - Route Permission Metadata And Access-Denied Boundary
```

Goal:

```text
Add verified route permission metadata and a non-login access-denied experience,
then align ProtectedRoute with useAuthorization without redesigning feature
pages.
```
