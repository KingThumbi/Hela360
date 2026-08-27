# Migration 050 - Route Permission Boundary

## 1. Migration Purpose

Migration 050 establishes route-level permission metadata and an
authenticated-but-forbidden UX boundary for the safe verified subset of
frontend routes.

The frontend flow is now:

```text
Authenticated?
  -> route permission metadata
  -> useAuthorization()
  -> allowed renders route
  -> denied renders AccessDeniedPage
```

Frontend route authorization remains usability-only. Backend decorators and
service-level authorization remain authoritative.

## 2. ADR Rules Applied

- ADR-006: route authorization consumes permissions from the authenticated
  tenant session and does not own tenant or branch selection.
- ADR-007: protected routes declare permission requirements and denied
  authenticated users receive an access-denied experience.
- ADR-008: route metadata, route guarding, authorization hook, navigation, and
  feature presentation remain separate owners.
- ADR-009: names use explicit route, permission, and access-denied terminology.

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

## 4. Route Inventory

Active router entries:

| Route | Page element | Parent | Current auth | Navigation item | Navigation permission | Backend evidence | Disposition |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `/` | redirect to `/dashboard` | none | none | none | none | none | public redirect unchanged |
| `/login` | `LoginPage` | none | public | none | none | login endpoint | unchanged |
| `/dashboard` | `DashboardPage` | `AppLayout` | parent `ProtectedRoute` | dashboard | `dashboard.view` | no backend evidence found | left auth-only |
| `/products` | placeholder `div` | `AppLayout` | parent plus child `ProtectedRoute` | products | `products.view` | `@require_permission("products.view")` on list/detail | migrated |
| `/customers` | placeholder `div` | `AppLayout` | parent plus child `ProtectedRoute` | customers | `customers.view` | `@require_permission("customers.view")` on list/detail | migrated |
| `/inventory` | placeholder `div` | `AppLayout` | parent only | inventory | `inventory.view` | no current route evidence found | left auth-only |
| `/sales` | placeholder `div` | `AppLayout` | parent only | sales history | `sales.view` | no `sales.view` backend route found | left auth-only |
| `/procurement` | placeholder `div` | `AppLayout` | parent only | none direct | none direct | suppliers evidence exists only for `/suppliers` API | left auth-only |
| `/finance` | placeholder `div` | `AppLayout` | parent only | none direct | none direct | no current route evidence found | left auth-only |
| `/reports` | placeholder `div` | `AppLayout` | parent only | reports | `reports.view` | permission constant only | left auth-only |
| `/administration` | placeholder `div` | `AppLayout` | parent only | none direct | none direct | admin permission constants differ from nav metadata | left auth-only |
| `/settings` | placeholder `div` | `AppLayout` | parent only | settings | `settings.view` | no backend evidence found | left auth-only |
| `*` | redirect to `/dashboard` | none | none | none | none | none | unchanged |

The router currently does not define child routes for navigation hrefs such as
`/sales/pos`, `/sales/refunds`, `/procurement/suppliers`,
`/administration/users`, or `/settings/tenant`.

## 5. Navigation Permission Inventory

Navigation currently supports one required permission per item. It does not
support any-of, all-of, or permissionless navigable items in its typed metadata.

Navigation metadata remains static and is filtered by `useNavigation()` through
`useAuthorization().permissions`.

Verified consistency after this migration:

| Navigation item | Href | Navigation permission | Route permission |
| --- | --- | --- | --- |
| products | `/products` | `products.view` | `products.view` |
| customers | `/customers` | `customers.view` | `customers.view` |

Other navigation items remain visibility-only metadata until matching route and
backend evidence are verified.

## 6. Backend Permission Evidence

Verified backend route families:

- Products list/detail use `products.view`; create uses `products.create`.
- Customers list/detail use `customers.view`; create uses `customers.create`.
- Suppliers list/detail use `suppliers.view`, but there is no active frontend
  `/suppliers` or `/procurement/suppliers` route in the router.
- Sales checkout uses `sales.create`; refunds use `sales.refund`; no
  `sales.view` backend route was found.

Administration/settings findings:

- Backend legacy permission constants include `users.read`, `roles.read`,
  `branches.read`, and `tenant.manage`.
- Frontend navigation metadata uses `users.view`, `roles.view`,
  `permissions.view`, `branches.view`, and related values.
- No matching backend route decorators were verified for administration pages.

## 7. Canonical Route Permission Metadata Owner

Owner:

```text
frontend/src/routes/permissions.ts
```

Contract:

```typescript
interface RoutePermissionRequirement {
  permission: PermissionCode;
}
```

Only single-permission route requirements were introduced because the current
verified migrated routes require only view access. No any/all route semantics,
role metadata, owner flags, tenant scope, branch scope, labels, or React objects
were added.

## 8. ProtectedRoute Before And After

Before:

```text
initializing -> loading
unauthenticated -> redirect to login
authenticated -> render
```

After:

```text
initializing -> loading
unauthenticated -> redirect to login
authenticated + no route permission -> render
authenticated + permission allowed -> render
authenticated + permission denied -> AccessDeniedPage
```

`ProtectedRoute` consumes `useAuthorization().can(permission)` and does not read
roles, apply owner/admin bypasses, call APIs, or recompute permissions.

## 9. AccessDenied Owner

Owner:

```text
frontend/src/features/auth/AccessDeniedPage.tsx
```

Behavior:

- renders in place;
- keeps the requested URL visible;
- distinguishes authorization denial from unauthenticated login redirect;
- does not expose permission lists, role details, backend exception data, or
  security internals.

No `/403` or `/forbidden` route was introduced.

## 10. Routes Migrated

Migrated:

- `/products` with `products.view`;
- `/customers` with `customers.view`.

Both route permissions are shared with matching navigation metadata through
`ROUTE_PERMISSION_REQUIREMENTS`.

## 11. Routes Left Auth-Only

Left auth-only:

- `/dashboard`;
- `/inventory`;
- `/sales`;
- `/procurement`;
- `/finance`;
- `/reports`;
- `/administration`;
- `/settings`;
- parent `AppLayout` route.

Reasons include placeholder route state, missing actual child route definitions,
missing backend view evidence, unsupported backend capability, or mismatched
administration permission vocabulary.

## 12. Backend Enforcement Matrix

| Frontend route | Frontend permission | Backend endpoint(s) | Backend enforcement | Status |
| --- | --- | --- | --- | --- |
| `/products` | `products.view` | `GET /products`, `GET /products/<product_id>`, `GET /products/by-code/<code_value>` | `@require_permission("products.view")` | verified and migrated |
| `/customers` | `customers.view` | `GET /customers`, `GET /customers/<customer_id>` | `@require_permission("customers.view")` | verified and migrated |

Backend gaps/deferred:

- `/sales` navigation uses `sales.view`, but sampled backend sales routes expose
  `sales.create` and `sales.refund` for operational actions.
- `/procurement/suppliers` navigation uses `suppliers.view`, and backend
  supplier list/detail enforcement exists, but no matching frontend route is
  currently registered.
- Administration navigation permissions did not match verified backend
  constants/decorators.

## 13. Component-Level Authorization Deferred

No create, edit, delete, refund, admin action, or feature-button gates were
added. Action-level authorization remains a later migration.

## 14. Tests And Static Verification

No frontend test harness exists in the repository, so no unit tests were added.

Static verification commands:

```bash
rg "ProtectedRoute" frontend/src
rg "permission=" frontend/src/app frontend/src/routes
rg "role ===|roles\\.includes|isAdmin|isOwner" frontend/src/routes frontend/src/navigation
rg "AccessDenied|Forbidden" frontend/src
rg "PermissionCode" frontend/src/routes frontend/src/navigation
```

Verified:

- no role-based route authorization;
- no owner/admin bypass in route/navigation authorization;
- one canonical access-denied page;
- route permission metadata uses `PermissionCode`;
- migrated route permissions match verified backend codes;
- route paths and navigation ids were not changed;
- direct route eligibility uses `useAuthorization()`.

## 15. Files Inspected

Inspected:

- required ADRs 006 through 009;
- Migration 049 and Migration 044 reports;
- `frontend/src/app/router.tsx`;
- `frontend/src/routes/`;
- `frontend/src/navigation/`;
- `frontend/src/types/navigation.ts`;
- `frontend/src/types/auth.ts`;
- `frontend/src/hooks/useAuthorization.ts`;
- frontend feature page files;
- sampled backend API route files and permission declarations.

## 16. Files Created

- `frontend/src/routes/permissions.ts`
- `frontend/src/features/auth/AccessDeniedPage.tsx`
- `frontend/docs/architecture/reviews/MIGRATION-050-ROUTE-PERMISSION-BOUNDARY.md`

## 17. Files Modified

- `frontend/src/routes/ProtectedRoute.tsx`
- `frontend/src/app/router.tsx`
- `frontend/src/navigation/navigation.ts`

No backend source files were modified.

## 18. Verification Results

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

## 19. Runtime Behavior Confirmation

Expected behavior:

- unauthenticated `/products` or `/customers` access still redirects to login;
- authenticated users with the matching permission see the current route
  element;
- authenticated users without the matching permission see `AccessDeniedPage`;
- auth-only routes keep existing authentication behavior;
- hidden navigation remains usability-only and is not treated as security
  enforcement.

## 20. Invariants Verified

Verified:

1. Authentication and authorization denial remain distinct.
2. Route authorization consumes effective backend-derived permissions.
3. Routes do not infer access from role names.
4. No owner/admin bypass is recreated.
5. Permission metadata has one canonical route owner.
6. Navigation and migrated route permissions remain consistent.
7. Direct URL access cannot bypass frontend route eligibility for migrated
   routes.
8. Access-denied behavior does not expose security internals.
9. Frontend remains usability-only; backend remains authoritative.
10. Tenant and branch scope remain unchanged.
11. No domain query key was migrated.
12. No backend file was changed.
13. TypeScript remains at zero errors.
14. Production build remains successful.

## 21. Rollback Boundary

Rollback is limited to:

- remove `frontend/src/routes/permissions.ts`;
- remove `frontend/src/features/auth/AccessDeniedPage.tsx`;
- restore `ProtectedRoute` to auth-only behavior;
- restore `/products` and `/customers` route elements to direct placeholders;
- restore product/customer navigation permissions to inline strings;
- remove this report.

## 22. Recommended Next Migration

Recommended next migration:

```text
Migration 051 - Route Registry Alignment For Operational Feature Pages
```

Goal:

```text
Register actual operational feature pages and child routes only where backend
capabilities and route permissions are verified, beginning with suppliers and
sales action routes.
```

