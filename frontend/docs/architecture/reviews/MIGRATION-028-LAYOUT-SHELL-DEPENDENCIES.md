# Migration 028 - Layout Shell Dependency Alignment

## 1. Migration Purpose

Migration 028 aligns the authenticated application layout shell with canonical
provider, navigation, store, constants, and component public boundaries.

This migration fixes layout-shell dependency drift only. It does not redesign
the application shell, navigation, authorization, routes, authentication,
state persistence, services, query hooks, query keys, invalidation, or backend
behavior.

## 2. ADR Rules Applied

- ADR-007: layout components do not implement permission, role, tenant, or
  branch authorization policy.
- ADR-008: layout dependencies flow through stable public component, hook,
  provider, store, and constants boundaries.
- ADR-009: component and hook names remain descriptive and consistent.
- Migration 006: root providers stay in `AppProvider`; layouts consume composed
  shell/application dependencies rather than mounting providers.
- Migration 025: navigation registry and IDs remain unchanged.
- Migration 026: navigation helper public boundary remains unchanged.
- Migration 027: Sidebar navigation components are consumed through their
  component boundary.

## 3. Layout Implementations Found

Active layout owner:

- `frontend/src/layouts/AppLayout.tsx`

Active shell components:

- `frontend/src/components/layout/AppShell.tsx`
- `frontend/src/components/layout/AppSidebar.tsx`
- `frontend/src/components/layout/AppTopbar.tsx`
- `frontend/src/components/layout/AppWorkspace.tsx`
- `frontend/src/components/layout/AppFooter.tsx`
- `frontend/src/components/layout/Breadcrumbs.tsx`
- `frontend/src/components/layout/BranchSelector.tsx`
- `frontend/src/components/layout/TenantSelector.tsx`
- `frontend/src/components/layout/NotificationMenu.tsx`
- `frontend/src/components/layout/ThemeToggle.tsx`
- `frontend/src/components/layout/UserMenu.tsx`

No second active authenticated layout shell was found.

## 4. Canonical AppLayout Owner

Canonical owner:

```text
frontend/src/layouts/AppLayout.tsx
```

It is mounted by `frontend/src/app/router.tsx` inside `ProtectedRoute` and
contains the authenticated route outlet boundary.

## 5. Canonical AppSidebar Owner

Canonical owner:

```text
frontend/src/components/layout/AppSidebar.tsx
```

It renders the canonical navigation registry and consumes navigation components
through `@/components/navigation`.

## 6. Provider Dependencies

Root providers remain composed by:

```text
frontend/src/providers/AppProvider.tsx
```

Layouts do not mount `AppProvider`, `ApplicationProvider`, `AuthProvider`,
`QueryProvider`, `ShellProvider`, or `ThemeProvider`.

The root TooltipProvider API drift was corrected from `delayDuration` to
`delay`, matching the local Base UI wrapper.

## 7. Shell-Store Dependencies

Canonical shell store owner:

```text
frontend/src/store/shellStore.ts
```

Layout-facing hooks consume shell store selectors:

- `useCurrentBranch`
- `useNotifications`
- `useTheme`
- `useUserMenu`

`useCurrentBranch` now exposes the selector state shape expected by
`BranchSelector`: `branches`, `isOpen`, `open`, and `close`, while preserving
selected branch ownership in `shellStore`.

## 8. Navigation Dependencies

Navigation registry, IDs, and helper algorithms were not changed.

`AppSidebar` continues to consume the canonical `navigation` registry from
`@/navigation`.

## 9. Component Public Boundaries

Aligned shell dependencies:

- `@/components/navigation`
- `@/components/ui/sidebar`
- `@/components/ui/command`
- `@/components/ui/dropdown-menu`
- `@/components/ui/popover`
- `@/components/ui/tooltip`
- `@/constants`

Created local UI boundaries for:

- `SidebarProvider`
- `SidebarInset`
- command selector primitives

## 10. Stale Imports Found

Stale or missing dependency paths found:

- `@/components/ui/sidebar`
- `@/components/ui/command`
- `@/constants/app`
- `@/hooks/useTenant`

Stale prop/API usage found:

- `SHELL.topbar.height`
- `SHELL.footer.height`
- `TooltipProvider delayDuration`
- `BreadcrumbLink asChild`
- missing `DropdownMenuHeader`
- `NotificationMenu` open callback shadowing the `open()` action
- `TenantSelector` open callback shadowing the `open()` action

## 11. Duplicate Shell/Provider Composition Found

No duplicate authenticated `AppLayout` was found.

`AppShell` mounts a local UI `SidebarProvider`, not a root application provider.
Root application providers remain outside layouts.

## 12. Router/Layout Disposition

Router paths and nesting were unchanged.

`AppLayout` remains mounted exactly once inside `ProtectedRoute`.

`AppWorkspace` now accepts shell children and keeps `<Outlet />` as a fallback,
preserving one routed content boundary.

## 13. Prop-Type Disposition

Corrected prop contracts:

- `AppShellProps` now explicitly accepts `children?: ReactNode`.
- `AppWorkspaceProps` now explicitly accepts `children?: ReactNode`.
- local UI trigger wrappers accept `asChild` and map it to Base UI `render`.

No broad `any` or ignored diagnostics were introduced.

## 14. Authorization Boundary Confirmation

No permission checks, role checks, tenant authorization checks, branch
authorization checks, feature flag policy, or route guard behavior were added.

`useTenant` is a shell-facing placeholder over authenticated identity data only;
it does not implement tenant switching authorization.

## 15. Styling and Runtime Confirmation

No layout Tailwind classes, route paths, navigation registry entries,
navigation IDs, menu order, labels, icons, or permission metadata were changed.

The new UI shims preserve the existing intended shell composition and trigger
rendering contract.

## 16. Files Inspected

- `frontend/src/layouts/AppLayout.tsx`
- `frontend/src/components/layout/AppShell.tsx`
- `frontend/src/components/layout/AppSidebar.tsx`
- `frontend/src/components/layout/AppTopbar.tsx`
- `frontend/src/components/layout/AppWorkspace.tsx`
- `frontend/src/components/layout/AppFooter.tsx`
- `frontend/src/components/layout/Breadcrumbs.tsx`
- `frontend/src/components/layout/BranchSelector.tsx`
- `frontend/src/components/layout/TenantSelector.tsx`
- `frontend/src/components/layout/NotificationMenu.tsx`
- `frontend/src/components/navigation/`
- `frontend/src/components/ui/`
- `frontend/src/providers/`
- `frontend/src/hooks/useApplication.ts`
- `frontend/src/hooks/useNavigation.ts`
- `frontend/src/hooks/useCurrentBranch.ts`
- `frontend/src/hooks/useNotifications.ts`
- `frontend/src/store/shellStore.ts`
- `frontend/src/app/App.tsx`
- `frontend/src/app/router.tsx`
- `frontend/src/main.tsx`
- `frontend/src/routes/`
- ADR-007
- ADR-008
- ADR-009
- Migration 006 report
- Migration 025 report
- Migration 026 report
- Migration 027 report

## 17. Files Created

- `frontend/src/components/ui/sidebar.tsx`
- `frontend/src/components/ui/command.tsx`
- `frontend/src/constants/app.ts`
- `frontend/src/hooks/useTenant.ts`
- `frontend/docs/architecture/reviews/MIGRATION-028-LAYOUT-SHELL-DEPENDENCIES.md`

## 18. Files Modified

- `frontend/src/components/layout/AppShell.tsx`
- `frontend/src/components/layout/AppWorkspace.tsx`
- `frontend/src/components/layout/Breadcrumbs.tsx`
- `frontend/src/components/layout/TenantSelector.tsx`
- `frontend/src/components/layout/NotificationMenu.tsx`
- `frontend/src/components/ui/popover.tsx`
- `frontend/src/components/ui/dropdown-menu.tsx`
- `frontend/src/components/ui/tooltip.tsx`
- `frontend/src/constants/index.ts`
- `frontend/src/hooks/useCurrentBranch.ts`
- `frontend/src/hooks/useNotifications.ts`
- `frontend/src/providers/AppProvider.tsx`

## 19. Compiler Errors Before

Frontend compiler baseline before this migration:

```text
143 TypeScript errors
```

## 20. Compiler Errors After

Frontend compiler count after this migration:

```text
111 TypeScript errors
```

## 21. Net Reduction

This migration reduced the frontend TypeScript baseline by:

```text
32 errors
```

## 22. Layout Diagnostics Before and After

Before:

- missing `@/components/ui/sidebar`
- missing `@/components/ui/command`
- missing `@/constants/app`
- missing `@/hooks/useTenant`
- stale `SHELL.topbar.height`
- stale `SHELL.footer.height`
- `AppShell` children prop mismatch
- `AppWorkspace` children prop mismatch
- breadcrumb hook/component shape mismatch
- branch selector hook shape mismatch
- notification hook shape mismatch
- missing `DropdownMenuHeader`
- stale `asChild` prop usage against Base UI wrappers
- `TooltipProvider delayDuration` API drift

After:

```text
No AppLayout/AppShell/AppSidebar/AppWorkspace/AppFooter/BranchSelector/
Breadcrumbs/NotificationMenu/TenantSelector/ThemeToggle/UserMenu dependency
diagnostics remain.
```

## 23. New Diagnostics

No new diagnostics were introduced by this migration.

## 24. Remaining Shell Blockers

No remaining layout-shell diagnostics were observed in the post-migration
compiler output.

Remaining global categories include:

- missing dashboard page export
- page component prop drift
- UI scroll-area unused import
- missing auth login subcomponents
- domain query/service/type contract drift
- deferred `src/lib/storage.ts` `erasableSyntaxOnly` diagnostic
- main React import drift

## 25. Invariants Verified

- The application shell has one canonical layout owner.
- Layout dependencies flow through public component/hook boundaries.
- Layouts consume hooks rather than raw contexts.
- Root providers are not mounted inside layouts.
- Shell state has one canonical store owner.
- Sidebar components use canonical public exports.
- Navigation registry and IDs remain unchanged.
- Layouts contain no business service or API logic.
- Layouts contain no cache invalidation logic.
- Authorization policy is not implemented in layout components.
- Route paths and nesting remain unchanged.
- Styling and responsive behavior remain unchanged.
- No backend file changed.
- No unrelated domain changed.

## 26. Rollback Boundary

Rollback is limited to:

- `frontend/src/components/layout/AppShell.tsx`
- `frontend/src/components/layout/AppWorkspace.tsx`
- `frontend/src/components/layout/Breadcrumbs.tsx`
- `frontend/src/components/layout/TenantSelector.tsx`
- `frontend/src/components/layout/NotificationMenu.tsx`
- `frontend/src/components/ui/sidebar.tsx`
- `frontend/src/components/ui/command.tsx`
- `frontend/src/components/ui/popover.tsx`
- `frontend/src/components/ui/dropdown-menu.tsx`
- `frontend/src/components/ui/tooltip.tsx`
- `frontend/src/constants/app.ts`
- `frontend/src/constants/index.ts`
- `frontend/src/hooks/useCurrentBranch.ts`
- `frontend/src/hooks/useNotifications.ts`
- `frontend/src/hooks/useTenant.ts`
- `frontend/src/providers/AppProvider.tsx`
- this review document

## 27. Recommended Next Migration

Recommended next migration:

```text
Migration 029 - Dashboard Route Export Alignment
```

Rationale:

The next top compiler diagnostic is the router importing
`DashboardPage` from `@/features/dashboard/DashboardPage` when that module does
not currently expose the requested named component.
