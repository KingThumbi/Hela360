# Migration 027 - Sidebar Component Export Alignment

## 1. Migration Purpose

Migration 027 aligns Sidebar component imports and exports so navigation
components have one canonical runtime owner and one consistent public import
style.

This migration resolves the `SidebarGroup` named/default `SidebarItem` mismatch
and removes the unused `depth` prop from `SidebarItem`.

It does not redesign Sidebar rendering, navigation grouping, navigation
visibility, authorization, routes, registry entries, styling, or interaction
behavior.

## 2. ADR Rules Applied

- ADR-007: Sidebar components display navigation data and do not implement
  authorization policy.
- ADR-008: reusable component modules expose stable public contracts through a
  barrel where appropriate.
- ADR-009: React components use PascalCase names and component files match
  component names.
- Migration 025: navigation IDs and registry entries remain unchanged.
- Migration 026: navigation helper public exports remain unchanged.

## 3. Sidebar Components Found

Found active Sidebar-related components:

- `frontend/src/components/layout/AppSidebar.tsx`
- `frontend/src/components/navigation/SidebarGroup.tsx`
- `frontend/src/components/navigation/SidebarItem.tsx`
- `frontend/src/components/navigation/SidebarLogo.tsx`

No duplicate `SidebarItem`, `SidebarGroup`, or `SidebarLogo` implementation was
found.

## 4. Export Conventions Found

Nearby page, layout, and navigation components generally expose:

```typescript
export function ComponentName(...) {
  ...
}

export default ComponentName;
```

`SidebarGroup` and `SidebarLogo` already followed this convention.

`SidebarItem` was the outlier: it had only a default export while
`SidebarGroup` imported it as a named export.

## 5. Canonical SidebarItem Owner

Canonical owner:

```text
frontend/src/components/navigation/SidebarItem.tsx
```

## 6. Canonical Export Style

Canonical style:

```typescript
export function SidebarItem(...) {
  ...
}

export default SidebarItem;
```

This matches neighboring component files and preserves the existing default
export for local compatibility without creating a second implementation or alias.

## 7. SidebarGroup Import Disposition

`SidebarGroup` continues to import the canonical named component:

```typescript
import { SidebarItem } from "./SidebarItem";
```

This import now resolves because `SidebarItem.tsx` exports `SidebarItem` as a
named runtime value.

## 8. Navigation Component Barrel Disposition

Created:

```text
frontend/src/components/navigation/index.ts
```

The barrel exports existing navigation components exactly once:

- `SidebarGroup`
- `SidebarItem`
- `SidebarLogo`

It does not expose navigation registry internals or authorization
implementations.

## 9. Root Component Barrel Disposition

No root component barrel existed at:

```text
frontend/src/components/index.ts
```

This migration did not create one, because doing so would broaden the change
beyond Sidebar component export alignment.

## 10. `depth` Prop Disposition

Disposition:

```text
Path B - depth is obsolete
```

`depth` was declared and defaulted in `SidebarItemProps`, but no caller passed
it and no JSX, styling, recursive rendering, accessibility behavior, or route
logic used it.

The prop was removed from `SidebarItemProps` and from the component parameter
destructure. Rendered output is unchanged.

## 11. Recursive Rendering Disposition

No active recursive Sidebar rendering path was found.

Navigation children remain supported by shared navigation types and helpers, but
the current Sidebar components render the section's direct items only.

## 12. Prop Type Ownership

Sidebar prop interfaces remain local component implementation details:

- `SidebarItemProps`
- `SidebarGroupProps`

They are not exported because no external consumers use them. Navigation data
types continue to come from `frontend/src/types/navigation.ts`.

## 13. Authorization Boundary Confirmation

No permission checks, role checks, tenant checks, branch checks, feature flag
checks, provider imports, store imports, or authorization service imports were
added to Sidebar components.

## 14. Styling and Runtime Confirmation

No CSS classes, Tailwind classes, icon rendering, labels, routes, active-state
behavior, collapsed-state behavior, accessibility attributes, or click behavior
were changed.

## 15. Files Inspected

- `frontend/src/components/navigation/SidebarGroup.tsx`
- `frontend/src/components/navigation/SidebarItem.tsx`
- `frontend/src/components/navigation/SidebarLogo.tsx`
- `frontend/src/components/navigation/index.ts`
- `frontend/src/components/layout/AppSidebar.tsx`
- `frontend/src/components/index.ts`
- `frontend/src/layouts/`
- `frontend/src/navigation/`
- `frontend/src/hooks/useNavigation.ts`
- ADR-007
- ADR-008
- ADR-009
- Migration 025 report
- Migration 026 report

## 16. Files Created

- `frontend/src/components/navigation/index.ts`
- `frontend/docs/architecture/reviews/MIGRATION-027-SIDEBAR-COMPONENT-EXPORTS.md`

## 17. Files Modified

- `frontend/src/components/navigation/SidebarItem.tsx`
- `frontend/src/components/layout/AppSidebar.tsx`

## 18. Compiler Errors Before

Frontend compiler baseline before this migration:

```text
145 TypeScript errors
```

## 19. Compiler Errors After

Frontend compiler count after this migration:

```text
143 TypeScript errors
```

## 20. Net Reduction

This migration reduced the frontend TypeScript baseline by:

```text
2 errors
```

## 21. Sidebar Export Diagnostics Before and After

Before:

```text
src/components/navigation/SidebarGroup.tsx: Module '"./SidebarItem"' has no exported member 'SidebarItem'.
```

After:

```text
No SidebarItem named/default export diagnostic remains.
```

## 22. Unused Prop Diagnostics Before and After

Before:

```text
src/components/navigation/SidebarItem.tsx: 'depth' is declared but its value is never read.
```

After:

```text
No SidebarItem depth diagnostic remains.
```

## 23. New Diagnostics

No new diagnostics were introduced by this migration.

## 24. Remaining Navigation-Component Blockers

No `SidebarItem`, `SidebarGroup`, `SidebarLogo`, or
`components/navigation/index.ts` diagnostics remain in the post-migration
compiler output.

Remaining global categories include layout shell/UI component API drift,
missing login subcomponents, dashboard API type path drift, domain query/service
contract drift, sales service export drift, and the deferred
`src/lib/storage.ts` `erasableSyntaxOnly` diagnostic.

## 25. Invariants Verified

- Each Sidebar component has one canonical runtime owner.
- `SidebarItem` uses one consistent named component export.
- The navigation component barrel exports only existing components.
- Component prop types are not duplicated.
- Navigation business types are consumed from the canonical navigation type
  boundary.
- Recursive rendering behavior remains unchanged.
- No permission policy is implemented in Sidebar components.
- No navigation registry content changed.
- No route path changed.
- No styling or interaction behavior changed.
- No backend file changed.
- No unrelated component was changed.
- Runtime Sidebar behavior remains unchanged.

## 26. Rollback Boundary

Rollback is limited to:

- `frontend/src/components/navigation/SidebarItem.tsx`
- `frontend/src/components/navigation/index.ts`
- `frontend/src/components/layout/AppSidebar.tsx`
- this review document

## 27. Recommended Next Migration

Recommended next migration:

```text
Migration 028 - Layout Shell Dependency Alignment
```

Rationale:

The next visible compiler cluster is in the layout shell and UI sidebar
dependency boundary, especially missing `@/components/ui/sidebar` and layout
constant shape drift.
