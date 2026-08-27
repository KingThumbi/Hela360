# Migration 026 - Navigation Helper Public Exports

## 1. Migration Purpose

Migration 026 establishes one canonical public boundary for navigation helper
functions and derived navigation data.

This migration resolves missing helper exports for `filterNavigation` and
`filterNavigationSection`, removes the stale `visibleNavigationItems` consumer,
and preserves the canonical navigation registry, IDs, route paths, menu order,
labels, icons, permissions, and runtime behavior.

It does not implement authorization policy, add authorization providers, change
routes, change navigation grouping, or modify services, query hooks, query keys,
invalidation, or backend files.

## 2. ADR Rules Applied

- ADR-007: frontend navigation visibility is usability-only; authorization
  decisions originate from the backend and should be delegated to an
  authorization boundary.
- ADR-008: navigation runtime helpers are owned by `src/navigation` and exposed
  through the navigation public barrel.
- ADR-009: helper names remain descriptive camelCase functions.
- Migration 025: navigation IDs and registry identity remain canonical and
  unchanged.

## 3. Helper Definitions Found

Canonical helper implementations found in:

```text
frontend/src/navigation/helpers.ts
```

Existing helpers:

- `flattenNavigation`
- `findNavigationItemById`
- `findNavigationItemByPath`
- `isNavigationItemActive`
- `findNavigationSection`
- `getProtectedNavigationItems`
- `filterNavigationByPermissions`
- `buildBreadcrumbs`

Missing helper names referenced by consumers:

- `filterNavigation`
- `filterNavigationSection`
- `visibleNavigationItems`

No duplicate helper implementations were found.

## 4. Helper Consumers Found

- `frontend/src/hooks/useNavigation.ts`
  - imports `filterNavigation`
  - imports `filterNavigationSection`
  - imports `flattenNavigation`
  - imports `navigation`
- `frontend/src/components/navigation/SidebarGroup.tsx`
  - imported `visibleNavigationItems`
- `frontend/src/hooks/useBreadcrumbs.ts`
  - imports `navigation`
- `frontend/src/navigation/index.ts`
  - exports the public navigation helper surface

## 5. Canonical Helper Owner

Canonical helper owner:

```text
frontend/src/navigation/helpers.ts
```

The public export surface is:

```text
frontend/src/navigation/index.ts
```

## 6. Structural Versus Authorization Helper Classification

Structural helpers:

- `flattenNavigation`
- `findNavigationItemById`
- `findNavigationItemByPath`
- `isNavigationItemActive`
- `findNavigationSection`
- `getProtectedNavigationItems`
- `buildBreadcrumbs`

Visibility helpers with caller-supplied permission data:

- `filterNavigation`
- `filterNavigationSection`
- `filterNavigationByPermissions`

Deferred or obsolete helper:

- `visibleNavigationItems`

## 7. `filterNavigation` Disposition

Disposition:

```text
Implemented as a pure navigation helper over caller-supplied permissions.
```

`filterNavigation` accepts grouped navigation sections and effective
permissions supplied by the caller. It does not import authorization providers,
stores, hooks, services, API clients, or query infrastructure.

It preserves section/item order and removes sections only when no child items
remain after filtering.

## 8. `filterNavigationSection` Disposition

Disposition:

```text
Implemented as a pure single-section helper.
```

`filterNavigationSection` accepts one `NavigationSection` and caller-supplied
permissions. It returns a section object with filtered items and does not mutate
the input section.

It does not remove the section itself; section removal remains the grouped
`filterNavigation` responsibility.

## 9. `visibleNavigationItems` Disposition

Disposition:

```text
Obsolete public symbol.
```

`visibleNavigationItems` had no implementation and only one consumer:

```text
frontend/src/components/navigation/SidebarGroup.tsx
```

Because the helper had no permission context and no accepted authorization
contract, this migration did not create a permissive global helper. The sidebar
now uses the `section.items` supplied to it.

## 10. `useNavigation` Disposition

`frontend/src/hooks/useNavigation.ts` now resolves its helper imports through
the navigation barrel because `filterNavigation` and `filterNavigationSection`
exist and are exported.

The hook continues to read the existing authenticated identity permissions from
`useAuthStore`. This migration did not add provider dependencies or redesign
the hook contract.

## 11. Public Navigation Barrel

`frontend/src/navigation/index.ts` now exports:

- `navigation`
- `PERMISSIONS`
- `NAVIGATION_ITEM_IDS`
- `NAVIGATION_SECTION_IDS`
- `NavigationItemId`
- `NavigationSectionId`
- `NAVIGATION_SECTION_LABELS`
- `NAVIGATION_SECTION_ORDER`
- `flattenNavigation`
- `findNavigationItemById`
- `findNavigationItemByPath`
- `findNavigationSection`
- `isNavigationItemActive`
- `getProtectedNavigationItems`
- `filterNavigation`
- `filterNavigationSection`
- `filterNavigationByPermissions`
- `buildBreadcrumbs`

Identifier types remain type-only exports.

## 12. Helpers Exported

Newly exported helpers:

- `filterNavigation`
- `filterNavigationSection`

Retained compatibility helper:

- `filterNavigationByPermissions`

## 13. Helpers Deferred

Deferred:

- authorization service/provider driven filtering
- role-based visibility checks
- feature flag filtering
- tenant or branch scoped visibility

Not exported:

- `visibleNavigationItems`

## 14. Sidebar Import Mismatch Disposition

Remaining sidebar component diagnostics:

- `SidebarGroup` imports `SidebarItem` as a named export while
  `SidebarItem.tsx` exports default.
- `SidebarItem` has an existing unused `depth` prop diagnostic.

These are component export/prop alignment issues and were not changed in this
navigation-helper migration.

## 15. Files Inspected

- `frontend/src/navigation/helpers.ts`
- `frontend/src/navigation/index.ts`
- `frontend/src/navigation/navigation.ts`
- `frontend/src/navigation/ids.ts`
- `frontend/src/navigation/sections.ts`
- `frontend/src/navigation/permissions.ts`
- `frontend/src/types/navigation.ts`
- `frontend/src/hooks/useNavigation.ts`
- `frontend/src/hooks/useBreadcrumbs.ts`
- `frontend/src/layouts/`
- `frontend/src/components/navigation/SidebarGroup.tsx`
- `frontend/src/components/navigation/SidebarItem.tsx`
- `frontend/src/authorization/`
- `frontend/src/providers/`
- ADR-007
- ADR-008
- ADR-009
- ADR compliance matrix
- canonical frontend architecture report
- Migration 025 report

## 16. Files Created

- `frontend/docs/architecture/reviews/MIGRATION-026-NAVIGATION-HELPER-EXPORTS.md`

## 17. Files Modified

- `frontend/src/navigation/helpers.ts`
- `frontend/src/navigation/index.ts`
- `frontend/src/components/navigation/SidebarGroup.tsx`

## 18. Compiler Errors Before

Frontend compiler baseline before this migration:

```text
149 TypeScript errors
```

## 19. Compiler Errors After

Frontend compiler count after this migration:

```text
145 TypeScript errors
```

## 20. Net Reduction

This migration reduced the frontend TypeScript baseline by:

```text
4 errors
```

## 21. Helper Diagnostics Before and After

Before:

```text
src/components/navigation/SidebarGroup.tsx: missing visibleNavigationItems
src/components/navigation/SidebarGroup.tsx: implicit any from unresolved items
src/hooks/useNavigation.ts: missing filterNavigation
src/hooks/useNavigation.ts: missing filterNavigationSection
```

After:

```text
No missing filterNavigation diagnostic remains.
No missing filterNavigationSection diagnostic remains.
No missing visibleNavigationItems diagnostic remains.
No helper-caused implicit any diagnostic remains in SidebarGroup.
```

## 22. New Diagnostics

No new diagnostics were introduced by this migration.

## 23. Remaining Navigation Blockers

Remaining navigation-adjacent diagnostics:

- `SidebarGroup` named/default `SidebarItem` import mismatch.
- `SidebarItem` unused `depth` prop.

Remaining global categories include incomplete UI component APIs, missing auth
login subcomponents, dashboard API type path drift, domain query/service
contract drift, sales service export drift, and the deferred
`src/lib/storage.ts` `erasableSyntaxOnly` diagnostic.

## 24. Runtime Behavior Confirmation

Navigation registry content was unchanged.

Unchanged:

- route paths
- navigation IDs
- section order
- item order
- labels
- icons
- permission metadata
- breadcrumb labels

## 25. Authorization Behavior Confirmation

No authorization provider, guard, service, role logic, feature flag logic, tenant
scope logic, or branch scope logic was added.

Filtering helpers only consume caller-supplied effective permissions and apply
existing navigation item permission metadata.

## 26. Invariants Verified

- Navigation helpers have one canonical runtime owner.
- Navigation barrel exports only existing helpers.
- Structural helpers remain separate from permission policy.
- Authorization evaluation remains outside the navigation registry.
- Filtering helpers are pure.
- Navigation order and structure remain unchanged except when filtered by
  caller-supplied permissions.
- Navigation helpers do not import React, providers, stores, services, API
  clients, or query infrastructure.
- No route path changed.
- No navigation ID changed.
- No authorization behavior was fabricated.
- No backend file changed.
- Runtime behavior remains unchanged except valid helper resolution.

## 27. Rollback Boundary

Rollback is limited to:

- `frontend/src/navigation/helpers.ts`
- `frontend/src/navigation/index.ts`
- `frontend/src/components/navigation/SidebarGroup.tsx`
- this review document

## 28. Recommended Next Migration

Recommended next migration:

```text
Migration 027 - Sidebar Component Export Alignment
```

Rationale:

The remaining navigation-adjacent compiler failures are now component export and
prop alignment issues, not navigation helper public-boundary issues.
