# Migration 029 - Login Component Export Alignment

## 1. Migration Purpose

Migration 029 restores the authentication login page component boundary.

The routed login page already expected four feature-local components:

- `LoginForm`
- `LoginHeader`
- `LoginFooter`
- `LoginIllustration`

Those component modules and their barrel were missing, producing four
`TS2307` diagnostics from `frontend/src/features/auth/LoginPage.tsx`.

## 2. ADR Rules Applied

- ADR-001: components do not call API clients or authentication services
  directly.
- ADR-002: login submission is performed through the canonical `useLogin`
  mutation hook.
- ADR-004: `LoginRequest` remains owned by `src/types/requests`.
- ADR-005: presentation error rendering stays in the form component.
- ADR-008: login-only components remain inside the auth feature boundary.
- ADR-009: component names use PascalCase and component files match component
  names.
- Migration 003: authentication DTO ownership remains unchanged.
- Migration 004: token mapping and token-only login semantics remain owned by
  `authService` and `useLogin`.
- Migration 005: identity is not fabricated during login.
- Migration 006: provider and store boundaries remain unchanged.
- Migration 028: layout-shell dependencies remain unchanged.

## 3. Login Pages Found

One active routed login page was found:

- `frontend/src/features/auth/LoginPage.tsx`

No active duplicate was found under:

- `frontend/src/pages/`
- `frontend/src/components/auth/`
- `frontend/src/features/auth/pages/`

`frontend/src/components/auth/` does not exist.

## 4. Canonical LoginPage Owner

Canonical owner:

```text
frontend/src/features/auth/LoginPage.tsx
```

It remains registered at the existing login route by
`frontend/src/app/router.tsx`.

No route path or router behavior was changed.

## 5. Expected Component Inventory

Before migration, `LoginPage` imported:

- `./components/LoginFooter`
- `./components/LoginForm`
- `./components/LoginHeader`
- `./components/LoginIllustration`

No matching modules existed.

No alternate implementations were found for:

- `AuthLayout`
- `AuthenticationLayout`
- `SignInForm`
- `LoginCard`
- `LoginPanel`

## 6. LoginForm Disposition

`LoginForm` was missing and essential to the current `LoginPage` JSX contract.

Created canonical owner:

```text
frontend/src/features/auth/components/LoginForm.tsx
```

`LoginForm` now owns:

- form state
- validation
- submission
- error presentation
- loading state

It consumes:

- `useLogin` from `@/hooks/queries/auth`
- `LoginRequest` from `@/types/requests`
- `loginSchema` and `LoginFormValues` from `@/validation/authSchema`

It does not call `authService`, `apiClient`, storage, or the auth store
directly.

## 7. LoginHeader Disposition

`LoginHeader` was missing and expected by the current page composition.

Created canonical owner:

```text
frontend/src/features/auth/components/LoginHeader.tsx
```

It is a presentation component only and uses existing application constants and
existing login-page text.

## 8. LoginFooter Disposition

`LoginFooter` was missing and expected by the current page composition.

Created canonical owner:

```text
frontend/src/features/auth/components/LoginFooter.tsx
```

It renders existing application name/version constants only.

No legal links, support links, registration links, or password reset links were
invented.

## 9. LoginIllustration Disposition

`LoginIllustration` was missing and expected by the current two-column login
layout.

Created canonical owner:

```text
frontend/src/features/auth/components/LoginIllustration.tsx
```

No image assets were created, downloaded, or referenced.

The component renders an existing brand panel using existing application
constants and login-page text.

## 10. Canonical Component Owner

Login-specific presentation components are owned by:

```text
frontend/src/features/auth/components/
```

They were not placed under global `src/components/` because no reuse outside
the auth feature was found.

## 11. Canonical Component Barrel

Created:

```text
frontend/src/features/auth/components/index.ts
```

The barrel exports each login component exactly once.

No DTOs, services, hooks, or private helper types are exported through this
component barrel.

## 12. LoginPage Import Changes

`LoginPage` now imports the four components from the feature-local component
barrel:

```typescript
import {
  LoginFooter,
  LoginForm,
  LoginHeader,
  LoginIllustration,
} from "./components";
```

The page JSX order, classes, route registration, and composition role were
preserved.

## 13. Login Behavior Confirmation

Canonical login behavior remains:

```text
LoginForm -> useLogin -> authService.login -> authStore token/session update
```

The form maps validated values into canonical `LoginRequest` fields:

- `username -> email`
- `password -> password`
- `rememberMe -> remember_me`
- `tenant_id: null`
- `branch_id: null`
- `device_name: null`

Token mapping remains in `AuthService.login()`.

Token-only login remains supported by `useLogin`.

No token persistence, identity handling, auth store behavior, endpoint, service
contract, query key, invalidation helper, provider, or route path was changed.

## 14. Asset Disposition

No visual asset was found for the login page.

No asset was added.

## 15. Prop-Type Ownership

None of the restored login components require public props.

No `LoginFormProps`, `LoginHeaderProps`, `LoginFooterProps`, or
`LoginIllustrationProps` interfaces were introduced.

`LoginRequest` was not duplicated.

## 16. Files Inspected

- `frontend/src/features/auth/`
- `frontend/src/components/`
- `frontend/src/hooks/queries/auth/`
- `frontend/src/services/auth/`
- `frontend/src/types/auth.ts`
- `frontend/src/types/requests/`
- `frontend/src/types/responses/`
- `frontend/src/routes/`
- `frontend/src/app/router.tsx`
- `frontend/src/store/authStore.ts`
- `frontend/src/validation/authSchema.ts`
- ADR-001
- ADR-002
- ADR-004
- ADR-005
- ADR-008
- ADR-009
- Migration 003
- Migration 004
- Migration 005
- Migration 006
- Migration 028

## 17. Files Created

- `frontend/src/features/auth/components/LoginForm.tsx`
- `frontend/src/features/auth/components/LoginHeader.tsx`
- `frontend/src/features/auth/components/LoginFooter.tsx`
- `frontend/src/features/auth/components/LoginIllustration.tsx`
- `frontend/src/features/auth/components/index.ts`
- `frontend/docs/architecture/reviews/MIGRATION-029-LOGIN-COMPONENT-EXPORTS.md`

## 18. Files Modified

- `frontend/src/features/auth/LoginPage.tsx`

## 19. Compiler Errors Before

Pre-migration baseline:

```text
111 TypeScript errors
```

## 20. Compiler Errors After

Post-migration result:

```text
107 TypeScript errors
```

## 21. Net Reduction

```text
111 -> 107
```

Net reduction:

```text
4 TypeScript errors
```

## 22. Login Component Diagnostics Before and After

Before:

- missing `./components/LoginFooter`
- missing `./components/LoginForm`
- missing `./components/LoginHeader`
- missing `./components/LoginIllustration`

After:

- no login component missing-module diagnostics remain
- no named/default login component export diagnostics remain
- no login component prop-type diagnostics remain

## 23. New Diagnostics

No new TypeScript diagnostics were introduced by the login components.

## 24. Remaining Auth Component Blockers

No remaining authentication component diagnostics were found after this
migration.

Authentication runtime capability remains limited by the previously documented
token-only backend login response and unsupported current-user endpoint, but
those are not component ownership blockers.

## 25. Invariants Verified

- One canonical routed login page remains.
- Login-specific components remain inside the auth feature.
- Every imported login component exists.
- Login submission uses the canonical `useLogin` hook.
- Components do not import services or API clients.
- DTO ownership remains unchanged.
- No registration or password recovery flow was added.
- No route path was changed.
- No provider behavior was changed.
- Styling structure and page composition were preserved.
- No backend file was modified.
- No unrelated compiler diagnostics were fixed.

## 26. Rollback Boundary

This migration can be rolled back by removing the new
`frontend/src/features/auth/components/` modules and restoring the prior
direct imports in `LoginPage`.

No service, hook, route, provider, store, backend, query key, invalidation, or
DTO rollback is required.

## 27. Recommended Next Migration

Recommended next migration:

```text
Dashboard Page Export Boundary
```

The next top-level compiler blocker is:

```text
src/app/router.tsx(8,10): Module '"@/features/dashboard/DashboardPage"' has no exported member 'DashboardPage'.
```
