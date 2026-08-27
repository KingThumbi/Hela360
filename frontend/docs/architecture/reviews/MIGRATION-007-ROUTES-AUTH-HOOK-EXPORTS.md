# Migration 007 - Routes and Authentication Hook Exports

## 1. Migration Purpose

Migration 007 established one canonical application-route constant contract and one canonical authentication hook public barrel.

The migration resolved the missing `APP_ROUTES` import in `ProtectedRoute` and removed duplicate authentication hook exports from the auth query barrel without changing route behavior or authentication behavior.

## 2. ADR Rules Applied

- ADR-002: query and mutation hooks remain domain-owned and communicate through services.
- ADR-007: no authorization behavior or permission checks were added.
- ADR-008: route constants and hook barrels expose stable public contracts.
- ADR-009: route constants use uppercase runtime constant naming and hooks retain `use*` names.

## 3. Route Constant Definitions Found

Found route-related constants:

- `PATHS` in `frontend/src/routes/routes.ts`
- `AUTH` in `frontend/src/constants/auth.ts`

`PATHS` is the broad application route path registry.

`AUTH` is an authentication constants object that includes auth-related route paths and endpoint-like values.

## 4. Duplicated Route Paths Found

Duplicated path literals were found in:

- `frontend/src/app/router.tsx`
- `frontend/src/hooks/useBreadcrumbs.ts`

Navigation and `SidebarLogo` already consumed `PATHS`.

This migration aligned `app/router.tsx` and `ProtectedRoute.tsx` with `PATHS`. `useBreadcrumbs.ts` was left unchanged because it was not required for the route/auth-hook public contract diagnostics.

## 5. Canonical Route Owner Selected

Canonical route owner:

```text
frontend/src/routes/routes.ts
```

This file contains route path values only and does not import React, providers, services, navigation, or authorization modules.

## 6. Canonical Runtime Constant Name

Canonical runtime route constant:

```typescript
PATHS
```

## 7. APP_ROUTES Disposition

`APP_ROUTES` was not defined in the current source.

It was treated as an obsolete/invalid consumer assumption and was not added as an alias.

`ProtectedRoute` now imports `PATHS` directly.

## 8. AUTH Disposition

`AUTH` remains an authentication configuration object in:

```text
frontend/src/constants/auth.ts
```

It is not the canonical application route contract because it mixes auth route values with authentication endpoint-like values such as `refreshEndpoint` and `meEndpoint`.

## 9. ProtectedRoute Import Before and After

Before:

```typescript
import { APP_ROUTES } from "@/constants/auth";
```

After:

```typescript
import { PATHS } from "@/routes/routes";
```

Default redirect remains:

```typescript
PATHS.LOGIN
```

which is still `/login`.

## 10. Authentication Hooks Found

Implemented auth hooks found:

- `useCurrentUser`
- `useLogin`
- `useLogout`

No implementations were found for:

- `useRefreshToken`
- `useForgotPassword`
- `useResetPassword`
- `useChangePassword`

`useRefreshToken` exists only as an auth-store selector name, not as an auth query/mutation hook.

## 11. Duplicate Hook Exports Found

`frontend/src/hooks/queries/auth/index.ts` exported each auth hook twice:

- named export from implementation file
- default alias under the same name

This caused duplicate identifier diagnostics for:

- `useCurrentUser`
- `useLogin`
- `useLogout`

## 12. Missing Hook Exports Found

No implemented auth hook was missing from the auth hook barrel.

No nonexistent auth hook export was present.

## 13. Canonical Auth-Hook Barrel

Canonical auth hook public barrel:

```text
frontend/src/hooks/queries/auth/index.ts
```

It now exports:

```typescript
export { useCurrentUser } from "./useCurrentUser";
export { useLogin } from "./useLogin";
export { useLogout } from "./useLogout";
```

Each implemented auth hook is exported exactly once.

## 14. Root Hook Barrel Disposition

`frontend/src/hooks/queries/index.ts` remains the root query-hook barrel and continues to re-export the auth domain barrel:

```typescript
export * from "./auth";
```

No competing auth hook public path was added.

## 15. Unsupported Auth Hooks

The following backend operations remain unverified from earlier migrations:

- refresh
- logout
- current user
- forgot password
- reset password
- change password

Existing hook implementations were preserved:

- `useLogout`
- `useCurrentUser`

No new hooks were created for unsupported operations.

`useCurrentUser` remains intentionally disabled per Migration 005.

## 16. Files Inspected

- `frontend/src/constants/`
- `frontend/src/constants/auth.ts`
- `frontend/src/constants/index.ts`
- `frontend/src/routes/routes.ts`
- `frontend/src/routes/ProtectedRoute.tsx`
- `frontend/src/app/App.tsx`
- `frontend/src/app/router.tsx`
- `frontend/src/navigation/`
- `frontend/src/features/auth/LoginPage.tsx`
- `frontend/src/hooks/queries/auth/`
- `frontend/src/hooks/queries/auth/index.ts`
- `frontend/src/hooks/queries/index.ts`
- `frontend/src/hooks/`
- `frontend/src/services/auth/`
- `frontend/src/providers/`

## 17. Files Created

- `frontend/docs/architecture/reviews/MIGRATION-007-ROUTES-AUTH-HOOK-EXPORTS.md`

## 18. Files Modified

- `frontend/src/routes/ProtectedRoute.tsx`
- `frontend/src/app/router.tsx`
- `frontend/src/hooks/queries/auth/index.ts`

## 19. Compatibility Re-Exports

No compatibility re-export was introduced.

`APP_ROUTES` was not aliased because it is not the verified canonical route object.

## 20. Compiler Errors Before

Pre-migration count:

```text
246 TypeScript errors
```

## 21. Compiler Errors After

Post-migration count:

```text
239 TypeScript errors
```

`npm run build` still fails because unrelated compiler errors remain.

## 22. Net Reduction

```text
7 TypeScript errors
```

## 23. Route Diagnostics Before and After

Before:

```text
src/routes/ProtectedRoute.tsx(34,10): Module '"@/constants/auth"' has no exported member 'APP_ROUTES'.
```

After:

```text
No APP_ROUTES diagnostic remains.
```

No default/named route export mismatch remains in the migration scope.

## 24. Auth-Hook Export Diagnostics Before and After

Before:

```text
Duplicate identifier 'useCurrentUser'.
Duplicate identifier 'useLogin'.
Duplicate identifier 'useLogout'.
```

After:

```text
No duplicate auth-hook export diagnostics remain.
```

Remaining duplicate hook export diagnostics are in the suppliers domain and are outside this migration.

## 25. New Diagnostics

No new diagnostics were introduced.

## 26. Invariants Verified

- Application route paths have one canonical runtime owner.
- Authentication configuration is not treated as the application route contract.
- `ProtectedRoute` consumes the canonical route constant.
- Route constants contain no React, service, provider, or authorization logic.
- Authentication hooks have one canonical public barrel.
- Each implemented auth hook is exported exactly once.
- Auth hook barrel exports only existing symbols.
- Unsupported backend operations remain unsupported.
- Hook runtime behavior is unchanged.
- No authorization behavior was added.
- Navigation registry was not redesigned.
- Runtime exports comply with `verbatimModuleSyntax`.
- No circular barrel imports were introduced.
- No unrelated domain files were modified.

## 27. Rollback Boundary

Rollback is limited to:

- `frontend/src/routes/ProtectedRoute.tsx`
- `frontend/src/app/router.tsx`
- `frontend/src/hooks/queries/auth/index.ts`
- this migration report

## 28. Remaining Route and Auth-Hook Issues

- `useBreadcrumbs.ts` still contains `/dashboard` literals.
- Supplier hook barrel still has duplicate `useDeleteSupplier` exports.
- Auth operations without confirmed backend routes remain unsupported.

## 29. Recommended Next Migration

Migration 008 should address the next narrow public-boundary category:

- supplier hook barrel duplicate exports, or
- route literal cleanup in breadcrumbs,

while continuing to avoid authorization, navigation redesign, and backend changes.
