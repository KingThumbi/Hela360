# Migration 030 - Dashboard Page Export Boundary

## 1. Migration Purpose

Migration 030 restores the canonical public page boundary for the Dashboard
route.

The router imported a named `DashboardPage` from
`@/features/dashboard/DashboardPage`, but the target module was an empty page
file and exported no runtime component.

## 2. ADR Rules Applied

- ADR-007: no dashboard authorization or permission behavior was changed.
- ADR-008: the Dashboard feature owns the routed Dashboard page and exposes it
  through a feature public barrel.
- ADR-009: `DashboardPage` uses PascalCase and the component file matches the
  component name.
- Migration 007: route paths remain owned by `PATHS`.
- Migration 025: dashboard navigation ID, label, icon, route, and permission
  metadata remain unchanged.
- Migration 028: `AppLayout` and `ProtectedRoute` nesting remain unchanged.
- Migration 029: page components are restored through narrow feature
  boundaries.

## 3. Router Diagnostic Inspected

Before migration:

```text
src/app/router.tsx(8,10): error TS2305: Module '"@/features/dashboard/DashboardPage"' has no exported member 'DashboardPage'.
```

Diagnostic classification:

- missing symbol: `DashboardPage`
- import path: `@/features/dashboard/DashboardPage`
- import style: named import
- route path: `PATHS.DASHBOARD`
- route element: `<DashboardPage />`
- lazy loading: not used
- module existence: module existed
- module export: requested symbol was absent
- second routed dashboard: none found

## 4. Dashboard Implementations Found

Found:

- `frontend/src/features/dashboard/DashboardPage.tsx`

The file existed but was empty.

No active duplicate Dashboard page was found under:

- `frontend/src/pages/`
- `frontend/src/components/dashboard/`
- `frontend/src/features/reports/`
- `frontend/src/app/`

Dashboard query hooks and services exist separately, but they are not consumed
by the routed page in this migration.

## 5. Canonical DashboardPage Owner

Canonical owner:

```text
frontend/src/features/dashboard/DashboardPage.tsx
```

## 6. Capability Classification

Classification:

```text
Placeholder page with invalid export boundary
```

The Dashboard feature had a routed page file but no exported page component.

The restored component is intentionally minimal and does not implement
metrics, charts, widgets, analytics, service calls, or query-hook wiring.

## 7. Canonical Feature Barrel

Created:

```text
frontend/src/features/dashboard/index.ts
```

It exports:

```typescript
export { DashboardPage } from "./DashboardPage";
```

No DTOs, services, hooks, query keys, or helper types are exported through this
feature barrel.

## 8. Export Convention

Canonical page export style:

```typescript
export function DashboardPage() {
  ...
}
```

The router consumes the named export through the feature boundary.

No default export was added.

## 9. Router Import Before and After

Before:

```typescript
import { DashboardPage } from "@/features/dashboard/DashboardPage";
```

After:

```typescript
import { DashboardPage } from "@/features/dashboard";
```

## 10. Route-Path Confirmation

Dashboard path remains:

```typescript
PATHS.DASHBOARD
```

Resolved value remains:

```text
/dashboard
```

Root and catch-all redirects continue to target `PATHS.DASHBOARD`.

## 11. Navigation Compatibility

Dashboard navigation metadata was not changed.

Verified existing registry entry:

- id: `NAVIGATION_ITEM_IDS.DASHBOARD`
- title: `Dashboard`
- href: `PATHS.DASHBOARD`
- icon: `LayoutDashboard`
- permission: `dashboard.view`

## 12. Dashboard Dependency Disposition

The restored page imports no dashboard services, no dashboard query hooks, no
analytics DTOs, and no backend endpoint contracts.

Existing dashboard hook/service diagnostics remain separate architecture work.

## 13. Placeholder Disposition

The Dashboard route now renders the same kind of minimal "Coming Soon" boundary
used by the current router for other unfinished modules.

No cards, charts, metrics, widgets, loading states, mocked data, or live data
were added.

## 14. Files Inspected

- `frontend/src/app/router.tsx`
- `frontend/src/routes/routes.ts`
- `frontend/src/features/`
- `frontend/src/features/dashboard/`
- `frontend/src/features/reports/`
- `frontend/src/navigation/navigation.ts`
- `frontend/src/layouts/`
- `frontend/src/hooks/queries/dashboard/`
- `frontend/src/services/dashboard/`
- ADR-007
- ADR-008
- ADR-009
- Migration 007
- Migration 025
- Migration 028
- Migration 029

## 15. Files Created

- `frontend/src/features/dashboard/index.ts`
- `frontend/docs/architecture/reviews/MIGRATION-030-DASHBOARD-PAGE-EXPORT.md`

## 16. Files Modified

- `frontend/src/features/dashboard/DashboardPage.tsx`
- `frontend/src/app/router.tsx`

## 17. Compiler Errors Before

Pre-migration baseline:

```text
107 TypeScript errors
```

## 18. Compiler Errors After

Post-migration result:

```text
106 TypeScript errors
```

## 19. Net Reduction

```text
107 -> 106
```

Net reduction:

```text
1 TypeScript error
```

## 20. Dashboard Diagnostics Before and After

Before:

- router named import failed because `DashboardPage` was not exported

After:

- no `DashboardPage` router import diagnostic remains
- no Dashboard page export diagnostic remains
- no feature barrel diagnostic remains

## 21. Newly Exposed Diagnostics

No Dashboard page internal diagnostics were newly exposed.

The existing dashboard hook diagnostics remain because they are unrelated to
the routed page export boundary:

- `@/types/apis` imports in dashboard hooks
- dashboard hook calls to `getOverview`, `getMetrics`, `getAlerts`, and
  `getActivity` while the service exposes different method names

## 22. New Diagnostics

No new TypeScript diagnostics were introduced.

## 23. Remaining Router and Feature Blockers

No remaining `src/app/router.tsx` diagnostics were reported after this
migration.

Remaining feature blockers are outside this migration and include page common
component typing, dashboard hook/service drift, inventory/procurement/sales
contract drift, and service barrel export drift.

## 24. Runtime Behavior Confirmation

Dashboard routing remains protected by the existing `ProtectedRoute` and
rendered inside the existing `AppLayout`.

The Dashboard page now renders a minimal placeholder and performs no runtime
data fetching.

## 25. Invariants Verified

- Dashboard has one canonical routed page owner.
- Dashboard page is exported through the Dashboard feature boundary.
- Router imports Dashboard through the feature boundary.
- Route paths and route nesting remain unchanged.
- Dashboard navigation metadata remains unchanged.
- No business dashboard functionality was introduced.
- No service or API call was added.
- No authorization behavior was changed.
- No provider or store behavior was changed.
- No unrelated feature page was modified.
- No backend file was changed.

## 26. Rollback Boundary

Rollback is limited to:

- `frontend/src/features/dashboard/DashboardPage.tsx`
- `frontend/src/features/dashboard/index.ts`
- `frontend/src/app/router.tsx`
- this review document

No service, hook, route constant, navigation, provider, store, backend, query
key, invalidation, or DTO rollback is required.

## 27. Recommended Next Migration

Recommended next migration:

```text
PageSection Prop Contract Alignment
```

The next top compiler diagnostic is:

```text
src/components/page/PageSection.tsx(28,18): Interface 'PageSectionProps' incorrectly extends interface 'HTMLAttributes<HTMLElement>'.
```
