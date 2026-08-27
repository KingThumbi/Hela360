# Migration 031 - PageSection Prop Contract Alignment

## 1. Migration Purpose

Migration 031 aligns the `PageSection` prop contract with its actual runtime
behavior.

`PageSection` renders a custom section header from a `title?: ReactNode` prop
while also forwarding native section props. The previous interface extended
`HTMLAttributes<HTMLElement>` directly, which introduced a conflict with the
native HTML `title?: string` attribute.

## 2. ADR Rules Applied

- ADR-008: `PageSection` remains owned by the shared page component boundary.
- ADR-008: public component contracts should match runtime behavior and avoid
  leaking invalid implementation assumptions.
- ADR-009: the `PageSection` component and `PageSectionProps` names remain
  descriptive PascalCase names.
- Migration 028: layout/page component behavior remains unchanged.
- Migration 030: routed feature placeholders remain outside this shared page
  component migration.

## 3. Exact Initial Diagnostic

Before migration:

```text
src/components/page/PageSection.tsx(28,18): error TS2430: Interface 'PageSectionProps' incorrectly extends interface 'HTMLAttributes<HTMLElement>'.
  Types of property 'title' are incompatible.
    Type 'ReactNode' is not assignable to type 'string | undefined'.
      Type 'null' is not assignable to type 'string | undefined'.
```

Diagnostic classification:

- code: `TS2430`
- origin: `frontend/src/components/page/PageSection.tsx`
- symbol: `PageSectionProps`
- root cause: custom `title?: ReactNode` conflicted with native
  `HTMLAttributes<HTMLElement>["title"]`
- consumer origin: none

## 4. PageSection Implementations Found

One runtime implementation was found:

```text
frontend/src/components/page/PageSection.tsx
```

No duplicate `PageSection` implementation was found.

## 5. Consumer Inventory

No current JSX consumers were found for:

- `<PageSection`
- `PageSection(`
- `import { PageSection`
- `import PageSection`

This migration therefore required no feature or layout consumer edits.

## 6. Canonical PageSection Owner

Canonical owner:

```text
frontend/src/components/page/PageSection.tsx
```

## 7. Canonical Public Import Path

Canonical public path:

```typescript
import { PageSection } from "@/components/page";
```

The existing page component barrel already exports `PageSection`.

## 8. Canonical Prop Contract

Canonical contract:

```typescript
export interface PageSectionProps
  extends Omit<
    HTMLAttributes<HTMLElement>,
    "title"
  > {
  title?: ReactNode;
  description?: ReactNode;
  children: ReactNode;
}
```

## 9. Required Props

Required:

- `children: ReactNode`

The component is a logical grouping of page content and renders children as its
body.

## 10. Optional Props

Optional:

- `title?: ReactNode`
- `description?: ReactNode`
- inherited non-conflicting native section attributes
- `className` through inherited native attributes

## 11. Children Disposition

`children` remains required.

No consumer exists that requires header-only or empty `PageSection` rendering.

## 12. Title, Description, and Actions Disposition

`title` remains the canonical header prop.

`description` remains the canonical secondary text prop.

No `actions` prop exists in the current runtime JSX, and no consumers require
one, so no action prop was introduced.

## 13. Native HTML Prop Disposition

`PageSection` forwards remaining props to the root `<section>` element.

Native props remain supported except for native `title`, which is intentionally
omitted because `PageSection` owns a custom rendered `title?: ReactNode` prop.

No `ref` support was added.

## 14. Export Convention

`PageSection` continues to provide:

- named runtime export: `PageSection`
- default export: `PageSection`

The page component barrel continues to expose the named runtime export only.

## 15. Consumers Changed

None.

No current consumer needed prop alignment.

## 16. Files Inspected

- `frontend/src/components/page/PageSection.tsx`
- `frontend/src/components/page/`
- `frontend/src/components/page/index.ts`
- `frontend/src/features/`
- `frontend/src/layouts/`
- ADR-008
- ADR-009
- Migration 028
- Migration 030

## 17. Files Created

- `frontend/docs/architecture/reviews/MIGRATION-031-PAGESECTION-PROP-CONTRACT.md`

## 18. Files Modified

- `frontend/src/components/page/PageSection.tsx`

## 19. Compiler Errors Before

Pre-migration baseline:

```text
106 TypeScript errors
```

## 20. Compiler Errors After

Post-migration result:

```text
105 TypeScript errors
```

## 21. Net Reduction

```text
106 -> 105
```

Net reduction:

```text
1 TypeScript error
```

## 22. PageSection Diagnostics Before and After

Before:

- `PageSectionProps` conflicted with native `HTMLAttributes<HTMLElement>` due
  to the `title` property type.

After:

- no `PageSection`
- no `PageSectionProps`
- no `src/components/page/PageSection.tsx`

diagnostics remain.

## 23. New Diagnostics

No new diagnostics were introduced.

## 24. Remaining Page-Component Blockers

The next page-adjacent blocker is outside `PageSection`:

```text
src/components/ui/scroll-area.tsx(3,1): error TS6133: 'React' is declared but its value is never read.
```

No remaining diagnostics originate from `frontend/src/components/page/`.

## 25. Runtime and Visual Behavior Confirmation

Runtime JSX is unchanged:

- same `<section>` root
- same `space-y-6` class
- same optional header rendering
- same title heading classes
- same description paragraph classes
- same children rendering
- same prop forwarding behavior except for the type-level native `title`
  conflict

## 26. Invariants Verified

- `PageSection` has one canonical runtime owner.
- The prop contract matches actual runtime behavior.
- Required and optional props are truthful.
- Page components remain in `frontend/src/components/page/`.
- No feature redefines `PageSectionProps`.
- Component barrels export existing symbols.
- No business logic exists in `PageSection`.
- No service, store, query, route, provider, navigation, or authorization
  dependency was introduced.
- Visual behavior remains unchanged.
- No unrelated component was changed.
- No backend file was changed.

## 27. Rollback Boundary

Rollback is limited to:

- `frontend/src/components/page/PageSection.tsx`
- this review document

No feature, layout, route, provider, store, service, query, navigation, backend,
or DTO rollback is required.

## 28. Recommended Next Migration

Recommended next migration:

```text
ScrollArea Unused React Import Alignment
```

The next top compiler diagnostic is:

```text
src/components/ui/scroll-area.tsx(3,1): error TS6133: 'React' is declared but its value is never read.
```
