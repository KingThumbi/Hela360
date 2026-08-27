# Migration 006 - Authentication Provider Boundary

## 1. Migration Purpose

Migration 006 established the canonical provider public API and made authentication state consumable through a concrete typed application context.

The migration resolved the missing provider barrel export, the invalid raw `ApplicationContext` import, the `{}` context fallback diagnostic, duplicate shell provider composition, and the `unknown` authentication state in `ProtectedRoute`.

## 2. ADR Rules Applied

- ADR-008: provider modules expose stable public APIs through a controlled barrel.
- ADR-008: consumers use typed hooks instead of private implementation details.
- ADR-008: root composition is centralized and avoids duplicate provider mounting.
- ADR-009: provider components and hooks retain predictable PascalCase and `use*` naming.
- ADR-006: token-only authentication state remains separate from tenant and branch identity.
- ADR-007: authorization remains out of scope.

## 3. Provider Implementations Found

Found provider implementations:

- `AppProvider`: root composition provider.
- `ApplicationProvider`: typed application context for auth and shell.
- `AuthProvider`: authentication initialization provider.
- `ShellProvider`: enterprise shell context provider.
- `QueryProvider`: React Query provider.
- `ThemeProvider`: theme initializer provider.

No `AuthContext`, `AuthContextValue`, `useAuth`, or `useAuthentication` provider API was found.

## 4. Provider Barrels Found

`frontend/src/providers/index.ts` existed but was empty.

This caused:

```text
Module '"@/providers"' has no exported member 'AppProvider'.
```

## 5. Duplicate Composition Points

Before migration:

- `main.tsx` attempted to mount `AppProvider`.
- `AppProvider` mounted `ShellProvider`.
- `AppLayout` also mounted `ShellProvider`.
- deleted `frontend/src/app/providers.tsx` existed only as a deleted tracked path and was not imported.

After migration:

- `main.tsx` mounts `AppProvider` exactly once.
- `AppProvider` owns root provider composition.
- `AppLayout` renders layout only and no longer mounts `ShellProvider`.

## 6. Canonical Root Provider Selected

Canonical root provider:

```text
AppProvider
```

Canonical source:

```text
frontend/src/providers/AppProvider.tsx
```

`AppProvider` owns framework and application-wide composition.

## 7. Canonical Public Import Path

Canonical provider barrel:

```typescript
import { AppProvider } from "@/providers";
```

The barrel exports only existing provider symbols and type-only context contracts.

## 8. Application Context Contract

Canonical application context:

```typescript
interface ApplicationContextValue {
  auth: AuthStore;
  shell: ShellContextValue;
}
```

This avoids `unknown` and avoids deriving the contract through unstable hook return inference.

## 9. Authentication Context Contract

Authentication state is exposed as:

```text
AuthStore
frontend/src/store/authStore.ts
```

Migration 005 semantics are preserved:

- `accessToken` may exist.
- `refreshToken` may exist.
- `identity` may be `null`.
- `isAuthenticated` represents token-backed authenticated session state.
- `isInitializing` represents deterministic startup restoration state.

No authorization or permissions contract was added.

## 10. Context Access Strategy

Public context access is hook-only:

```typescript
useApplication()
  -> useApplicationContext()
```

Feature and route consumers should use `useApplication()`.

## 11. Raw Context Disposition

`ApplicationContext` remains internal to `ApplicationProvider.tsx`.

No consumer imports the raw context object.

## 12. AppProvider Disposition

`AppProvider` remains the root public composition provider.

It now composes:

```text
ThemeProvider
QueryProvider
AuthProvider
ShellProvider
ApplicationProvider
TooltipProvider
children
Toaster
```

## 13. ApplicationProvider Disposition

`ApplicationProvider` is retained because it has a distinct responsibility from `AppProvider`.

It does not compose framework providers. It exposes the typed application context from already-mounted auth and shell state.

## 14. AuthProvider Disposition

`AuthProvider` remains responsible only for authentication initialization.

No token persistence behavior, login behavior, identity behavior, current-user behavior, or authorization behavior was changed.

## 15. Main Entry-Point Composition

`frontend/src/main.tsx` continues to preserve `React.StrictMode` and mounts:

```tsx
<AppProvider>
  <App />
</AppProvider>
```

No deleted `src/app/providers.tsx` import remains.

## 16. Protected-Route Type Alignment

`ProtectedRoute` continues to consume:

```typescript
const { auth } = useApplication();
```

After this migration, `auth` is typed as `AuthStore`, so:

- `auth.isInitializing`
- `auth.isAuthenticated`

are no longer `unknown`.

No route protection semantics were changed.

## 17. Tooltip-Provider Disposition

The existing diagnostic remains:

```text
TooltipProvider delayDuration={250}
```

The installed tooltip provider type does not accept `delayDuration`.

This was documented but left unchanged because it is a third-party UI API mismatch and not required to establish the authentication/provider boundary.

## 18. Files Inspected

- `frontend/src/providers/`
- `frontend/src/providers/index.ts`
- `frontend/src/providers/AppProvider.tsx`
- `frontend/src/providers/ApplicationProvider.tsx`
- `frontend/src/providers/AuthProvider.tsx`
- `frontend/src/providers/ShellProvider.tsx`
- `frontend/src/providers/QueryProvider.tsx`
- `frontend/src/providers/ThemeProvider.tsx`
- `frontend/src/app/App.tsx`
- `frontend/src/app/router.tsx`
- `frontend/src/app/providers.tsx`
- `frontend/src/main.tsx`
- `frontend/src/hooks/useApplication.ts`
- `frontend/src/store/authStore.ts`
- `frontend/src/store/shellStore.ts`
- `frontend/src/routes/ProtectedRoute.tsx`
- `frontend/src/layouts/AppLayout.tsx`
- `frontend/src/services/auth/`
- `frontend/src/types/auth.ts`

## 19. Files Created

- `frontend/docs/architecture/reviews/MIGRATION-006-AUTH-PROVIDER-BOUNDARY.md`

## 20. Files Modified

- `frontend/src/providers/index.ts`
- `frontend/src/providers/AppProvider.tsx`
- `frontend/src/providers/ApplicationProvider.tsx`
- `frontend/src/hooks/useApplication.ts`
- `frontend/src/layouts/AppLayout.tsx`

## 21. Exports Removed or Corrected

Corrected `frontend/src/providers/index.ts` to export existing runtime providers:

- `AppProvider`
- `ApplicationProvider`
- `AuthProvider`
- `QueryProvider`
- `ShellProvider`
- `ThemeProvider`
- `useApplicationContext`
- `useShell`

Type-only exports:

- `ApplicationContextValue`
- `ShellContextValue`

No deleted provider module was re-exported.

## 22. Imports Migrated

`useApplication.ts` changed from importing raw `ApplicationContext` from the provider implementation to importing:

```typescript
import {
  useApplicationContext,
  type ApplicationContextValue,
} from "@/providers";
```

`AppLayout.tsx` no longer imports `ShellProvider`.

## 23. Compiler Errors Before

Pre-migration baseline:

```text
251 TypeScript errors
```

Provider-focused diagnostics before:

```text
ApplicationContext was not exported.
useApplication returned a value incompatible with ApplicationContextValue.
AppProvider was not exported from "@/providers".
auth was unknown in ProtectedRoute.
TooltipProvider delayDuration was unsupported.
APP_ROUTES was not exported from constants/auth.
```

## 24. Compiler Errors After

Post-migration count:

```text
246 TypeScript errors
```

`npm run build` still fails because unrelated compiler errors remain.

## 25. Net Reduction

```text
5 TypeScript errors
```

## 26. Provider Diagnostics Before and After

Resolved:

- missing `AppProvider` export from `@/providers`
- invalid raw `ApplicationContext` import
- `{}` missing `auth` and `shell` in `useApplication`
- `auth is of type unknown` for `auth.isInitializing`
- `auth is of type unknown` for `auth.isAuthenticated`

Remaining:

- `TooltipProvider` does not accept `delayDuration`
- `APP_ROUTES` is not exported from `constants/auth`

These were left for later migrations because they are not required to establish the provider/auth public boundary.

## 27. New Diagnostics

No new diagnostics were introduced.

## 28. Invariants Verified

- Provider composition has one canonical public root.
- Authentication state is exposed through `AuthStore`.
- Token-only sessions remain valid.
- Identity remains nullable.
- Authentication and authorization remain separate.
- Raw `ApplicationContext` is not imported by consumers.
- Consumers use a public hook boundary.
- Provider barrel exports only existing symbols.
- Deleted provider files were not restored.
- `ShellProvider` is not mounted twice.
- No backend behavior changed.
- No authentication runtime behavior changed.
- No identity, tenant, branch, role, or permission data was fabricated.

## 29. Rollback Boundary

Rollback is limited to:

- `frontend/src/providers/index.ts`
- `frontend/src/providers/AppProvider.tsx`
- `frontend/src/providers/ApplicationProvider.tsx`
- `frontend/src/hooks/useApplication.ts`
- `frontend/src/layouts/AppLayout.tsx`
- this migration report

## 30. Remaining Authentication and Provider Issues

- `TooltipProvider delayDuration` is incompatible with the installed tooltip provider type.
- `ProtectedRoute` imports `APP_ROUTES`, but `constants/auth.ts` exports `AUTH`.
- Auth hook barrel duplicates remain in `frontend/src/hooks/queries/auth/index.ts`.
- Current-user identity remains unsupported until backend current-user/session support exists.

## 31. Recommended Next Migration

Migration 007 should address route/constants and auth hook public exports:

- normalize `APP_ROUTES` versus `AUTH`
- remove duplicate auth hook barrel exports
- preserve route behavior
- keep authorization out of scope
