# Migration 025 - Navigation ID Boundary

## 1. Migration Purpose

Migration 025 restores one canonical runtime/type contract for navigation identifiers.

This migration addresses navigation ID ownership, enum removal, registry/type alignment, and duplicate item identity. It does not implement authorization filtering, change route paths, redesign menus, add navigation entries, remove business modules, or change services, hooks, query keys, invalidation, or backend files.

## 2. ADR Rules Applied

- ADR-007: navigation remains permission-aware metadata, but authorization filtering behavior is not implemented in this migration.
- ADR-008: navigation runtime contracts are owned by the navigation module and exposed through its public barrel.
- ADR-009: runtime constants use uppercase constant-object naming, and type names remain descriptive.

## 3. Existing ID Definitions Found

Found before migration:

- `NavigationSectionId` enum in `frontend/src/navigation/sections.ts`
- `NavigationItemId` enum in `frontend/src/types/navigation.ts`
- raw string IDs in `frontend/src/navigation/navigation.ts`

This created three drifting representations:

- section runtime enum
- item runtime enum in a type module
- raw registry strings

## 4. Enum Definitions Found

Enum definitions found and removed:

- `NavigationSectionId`
- `NavigationItemId`

Both produced `erasableSyntaxOnly` diagnostics because TypeScript enum syntax is rejected under the current compiler settings.

## 5. Canonical Section-ID Owner

Canonical section-ID owner:

```text
frontend/src/navigation/ids.ts
```

Section IDs are navigation runtime metadata, so they are owned by `src/navigation`, not a type-only module.

## 6. Canonical Item-ID Owner

Canonical item-ID owner:

```text
frontend/src/navigation/ids.ts
```

Item IDs are also navigation runtime metadata and are owned beside section IDs.

## 7. Runtime Constant Names

Canonical runtime constants:

```typescript
NAVIGATION_SECTION_IDS
NAVIGATION_ITEM_IDS
```

## 8. Derived Type Names

Derived types:

```typescript
NavigationSectionId
NavigationItemId
```

Both types derive from their runtime constant objects.

## 9. Complete Section ID List

Canonical section IDs:

- `dashboard`
- `sales`
- `inventory`
- `customers`
- `procurement`
- `finance`
- `reports`
- `administration`
- `settings`

## 10. Complete Item ID List

Canonical item IDs:

- `dashboard`
- `pos`
- `sales-history`
- `refunds`
- `products`
- `inventory`
- `inventory-warehouses`
- `stock-adjustments`
- `customers`
- `purchase-orders`
- `suppliers`
- `expenses`
- `payments`
- `cashbook`
- `reports`
- `analytics`
- `users`
- `roles`
- `permissions`
- `branches`
- `administration-warehouses`
- `payment-methods`
- `settings`
- `tenant`

## 11. Duplicate ID Analysis

The previous registry used `warehouses` for two different navigation items:

- Inventory -> Warehouses, route `/warehouses`, permission `warehouses.view`
- Administration -> Warehouses, route `/administration/warehouses`, permission `warehouses.manage`

`findNavigationItemById` searches flattened navigation items by a single item ID, so item IDs are treated as globally unique in the current helper contract.

## 12. `warehouses` Disposition

Disposition:

```text
Path A - IDs must be globally unique
```

The duplicate was resolved by renaming only internal item IDs:

- `inventory-warehouses`
- `administration-warehouses`

Labels, routes, ordering, icons, and permissions were unchanged.

## 13. Canonical Registry Owner

Canonical runtime navigation registry:

```text
frontend/src/navigation/navigation.ts
```

This file owns the sidebar registry consumed by layouts/hooks.

## 14. `sections.ts` Disposition

`frontend/src/navigation/sections.ts` is now a compatibility/support module.

It no longer defines a section enum. It imports the canonical section constants from `ids.ts` and derives:

- `NAVIGATION_SECTION_ORDER`
- `NAVIGATION_SECTION_LABELS`

## 15. Navigation Barrel Changes

`frontend/src/navigation/index.ts` now exports runtime ID constants as values:

```typescript
NAVIGATION_SECTION_IDS
NAVIGATION_ITEM_IDS
```

It exports identifier types type-only:

```typescript
NavigationSectionId
NavigationItemId
```

It also exports the section order and label metadata from `sections.ts`.

`frontend/src/types/index.ts` exports the reusable navigation interfaces and
identifier types type-only from `src/types/navigation.ts`.

## 16. Route-Path Compatibility

No route paths were changed.

The following route associations remain unchanged:

- `/dashboard`
- `/sales/pos`
- `/sales`
- `/sales/refunds`
- `/products`
- `/inventory`
- `/warehouses`
- `/inventory/adjustments`
- `/customers`
- `/procurement/purchase-orders`
- `/procurement/suppliers`
- `/finance/expenses`
- `/finance/payments`
- `/finance/cashbook`
- `/reports`
- `/reports/analytics`
- `/administration/users`
- `/administration/roles`
- `/administration/permissions`
- `/administration/branches`
- `/administration/warehouses`
- `/administration/payment-methods`
- `/settings`
- `/settings/tenant`

## 17. Breadcrumb Compatibility

Breadcrumb behavior was not changed.

Navigation item labels, titles, and breadcrumb fields remain unchanged.

## 18. Files Inspected

- `frontend/src/types/navigation.ts`
- `frontend/src/navigation/navigation.ts`
- `frontend/src/navigation/sections.ts`
- `frontend/src/navigation/index.ts`
- `frontend/src/navigation/helpers.ts`
- `frontend/src/navigation/permissions.ts`
- `frontend/src/routes/routes.ts`
- `frontend/src/types/index.ts`
- `frontend/src/hooks/useNavigation.ts`
- `frontend/src/hooks/useBreadcrumbs.ts`
- `frontend/src/components/layout/AppSidebar.tsx`
- `frontend/src/components/navigation/SidebarGroup.tsx`
- `frontend/src/components/navigation/SidebarItem.tsx`
- `frontend/src/layouts/`
- ADR-007
- ADR-008
- ADR-009
- ADR compliance matrix
- canonical frontend architecture report
- Migration 006 report
- Migration 007 report
- Migration 024 report

## 19. Files Created

- `frontend/src/navigation/ids.ts`
- `frontend/docs/architecture/reviews/MIGRATION-025-NAVIGATION-ID-BOUNDARY.md`

## 20. Files Modified

- `frontend/src/types/navigation.ts`
- `frontend/src/types/index.ts`
- `frontend/src/navigation/navigation.ts`
- `frontend/src/navigation/sections.ts`
- `frontend/src/navigation/index.ts`

## 21. Compiler Errors Before

Frontend compiler baseline before this migration:

```text
188 TypeScript errors
```

Navigation ID assignment diagnostics before:

```text
35 NavigationSectionId/NavigationItemId assignment diagnostics in navigation.ts
```

Enum diagnostics before:

```text
src/navigation/sections.ts(17,13): error TS1294
src/types/navigation.ts(16,13): error TS1294
```

## 22. Compiler Errors After

Frontend compiler count after this migration:

```text
149 TypeScript errors
```

## 23. Net Reduction

This migration reduced the frontend TypeScript baseline by:

```text
39 errors
```

## 24. Navigation ID Diagnostics Before and After

Before:

```text
Registry string section IDs were not assignable to NavigationSectionId.
Registry string item IDs were not assignable to NavigationItemId.
```

After:

```text
No NavigationSectionId or NavigationItemId registry assignment diagnostics remain.
```

## 25. Enum Diagnostics Before and After

Before:

```text
NavigationSectionId enum rejected by erasableSyntaxOnly.
NavigationItemId enum rejected by erasableSyntaxOnly.
```

After:

```text
No navigation enum diagnostics remain.
```

## 26. New Diagnostics

No new diagnostics were introduced by this migration.

## 27. Remaining Navigation Blockers

Remaining navigation diagnostics are outside this ID-boundary migration:

- `SidebarGroup` imports `SidebarItem` as a named export while `SidebarItem.tsx` currently exports it as default.
- `visibleNavigationItems` is imported from `@/navigation` but no public helper exists.
- `filterNavigation` is imported from `@/navigation` but no public helper exists.
- `filterNavigationSection` is imported from `@/navigation` but no public helper exists.
- `SidebarItem` has an existing unused `depth` prop diagnostic.

Authorization/filtering behavior is intentionally deferred.

## 28. Runtime Behavior Confirmation

Runtime navigation behavior is unchanged except for corrected internal identity consistency.

Unchanged:

- menu order
- labels
- routes
- icons
- permissions
- breadcrumbs
- feature behavior

Changed:

- internal ID constants now drive registry identity
- duplicate `warehouses` item IDs are now globally unique

## 29. Invariants Verified

- Navigation section IDs have one canonical runtime owner.
- Navigation item IDs have one canonical runtime owner.
- Compile-time ID types derive from runtime values.
- No TypeScript enum syntax remains for navigation IDs.
- Every registry section ID is valid.
- Every registry item ID is valid.
- Duplicate item ID semantics were resolved for `warehouses`.
- Navigation IDs remain distinct from route paths.
- Registry ordering and labels remain unchanged.
- No authorization filtering was implemented.
- No service, query, or backend behavior changed.
- Runtime navigation behavior remains equivalent aside from corrected internal identity consistency.
- Runtime and type-only exports comply with `verbatimModuleSyntax`.

## 30. Rollback Boundary

Rollback is limited to:

- `frontend/src/navigation/ids.ts`
- `frontend/src/types/navigation.ts`
- `frontend/src/navigation/navigation.ts`
- `frontend/src/navigation/sections.ts`
- `frontend/src/navigation/index.ts`
- `frontend/src/types/index.ts`
- this review document

## 31. Recommended Next Migration

Recommended next migration:

```text
Migration 026 - Navigation Helper Public Exports
```

Rationale:

The remaining navigation diagnostics are public-helper and component import alignment issues, especially missing filtering helper exports and the `SidebarItem` default/named export mismatch.
