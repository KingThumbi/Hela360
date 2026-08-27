# Migration 051 - Route Registry Alignment

## 1. Migration Purpose

Migration 051 audits the route registry, router, feature pages, navigation
hrefs, and route permission metadata after Migration 050.

This migration is inspection-only because no missing route can be registered
without either fabricating a page, activating an unsupported capability, or
changing route semantics beyond the route-registry alignment scope.

No runtime behavior was changed.

## 2. ADR Rules Applied

- ADR-007: route permission metadata remains backend-verified and limited to
  Products and Customers.
- ADR-008: `PATHS`, router composition, navigation, feature pages, services,
  and query hooks remain separate owners.
- ADR-009: route and navigation names remain descriptive and unchanged.

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

## 4. PATHS Inventory

Canonical URL owner:

```text
frontend/src/routes/routes.ts
```

| Constant | URL | Domain | Router route | Feature page | Navigation item | Permission metadata | Disposition |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ROOT` | `/` | app | yes, redirect | none | none | none | intentional public redirect |
| `LOGIN` | `/login` | auth | yes | `LoginPage` | none | none | operational public route |
| `DASHBOARD` | `/dashboard` | dashboard | yes | `DashboardPage` | dashboard | nav-only `dashboard.view` | placeholder route |
| `SALES.ROOT` | `/sales` | sales | yes | inline placeholder | sales-history | nav-only `sales.view` | placeholder/auth-only |
| `SALES.POS` | `/sales/pos` | sales | no | none | pos | nav-only `sales.pos` | navigation-only mismatch |
| `SALES.HISTORY` | `/sales` | sales | yes via `SALES.ROOT` | inline placeholder | sales-history | nav-only `sales.view` | duplicate URL alias |
| `SALES.RETURNS` | `/sales/refunds` | sales | no | none | refunds | nav-only `sales.refund` | navigation-only mismatch |
| `PRODUCTS.ROOT` | `/products` | products | yes | inline placeholder | products | route `products.view` | permission-protected placeholder |
| `CUSTOMERS.ROOT` | `/customers` | customers | yes | inline placeholder | customers | route `customers.view` | permission-protected placeholder |
| `INVENTORY.ROOT` | `/inventory` | inventory | yes | inline placeholder | inventory | nav-only `inventory.view` | backend-blocked placeholder |
| `INVENTORY.ADJUSTMENTS` | `/inventory/adjustments` | inventory | no | none | stock-adjustments | nav-only `inventory.adjust` | navigation-only mismatch |
| `WAREHOUSES.ROOT` | `/warehouses` | inventory | no | none | inventory-warehouses | nav-only `warehouses.view` | navigation-only mismatch |
| `PROCUREMENT.ROOT` | `/procurement` | procurement | yes | inline placeholder | none direct | none | backend-blocked placeholder |
| `PROCUREMENT.PURCHASE_ORDERS` | `/procurement/purchase-orders` | procurement | no | none | purchase-orders | nav-only `procurement.purchase_orders.view` | unsupported future route |
| `PROCUREMENT.SUPPLIERS` | `/procurement/suppliers` | suppliers | no | none | suppliers | nav-only `suppliers.view` | route missing; no page exists |
| `FINANCE.ROOT` | `/finance` | finance | yes | inline placeholder | none direct | none | placeholder/manual-review |
| `FINANCE.EXPENSES` | `/finance/expenses` | finance | no | none | expenses | nav-only `expenses.view` | navigation-only mismatch |
| `FINANCE.PAYMENTS` | `/finance/payments` | finance | no | none | payments | nav-only `payments.view` | navigation-only mismatch |
| `FINANCE.CASHBOOK` | `/finance/cashbook` | finance | no | none | cashbook | nav-only `cashbook.view` | navigation-only mismatch |
| `REPORTS.ROOT` | `/reports` | reports | yes | inline placeholder | reports | nav-only `reports.view` | placeholder/manual-review |
| `REPORTS.ANALYTICS` | `/reports/analytics` | reports | no | none | analytics | nav-only `analytics.view` | navigation-only mismatch |
| `ADMINISTRATION.ROOT` | `/administration` | administration | yes | inline placeholder | none direct | none | placeholder/manual-review |
| `ADMINISTRATION.USERS` | `/administration/users` | administration | no | none | users | nav-only `users.view` | navigation-only mismatch |
| `ADMINISTRATION.ROLES` | `/administration/roles` | administration | no | none | roles | nav-only `roles.view` | navigation-only mismatch |
| `ADMINISTRATION.PERMISSIONS` | `/administration/permissions` | administration | no | none | permissions | nav-only `permissions.view` | navigation-only mismatch |
| `ADMINISTRATION.BRANCHES` | `/administration/branches` | administration | no | none | branches | nav-only `branches.view` | navigation-only mismatch |
| `ADMINISTRATION.WAREHOUSES` | `/administration/warehouses` | administration | no | none | administration-warehouses | nav-only `warehouses.manage` | navigation-only mismatch |
| `ADMINISTRATION.PAYMENT_METHODS` | `/administration/payment-methods` | administration | no | none | payment-methods | nav-only `payment_methods.view` | navigation-only mismatch |
| `SETTINGS.ROOT` | `/settings` | settings | yes | inline placeholder | settings | nav-only `settings.view` | placeholder/manual-review |
| `SETTINGS.TENANT` | `/settings/tenant` | settings | no | none | tenant | nav-only `tenant.manage` | navigation-only mismatch |

Findings:

- No router route uses a URL string literal where a `PATHS` constant exists.
- No navigation href uses a URL string literal where a `PATHS` constant exists.
- `SALES.ROOT` and `SALES.HISTORY` intentionally share `/sales`.
- Many child `PATHS` are navigation-owned future routes without router entries.

## 5. Router Inventory

| Route | Element | Layout | Protection | Permission | Import source | Page exists | Reachable from navigation | Classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `/` | redirect to `/dashboard` | none | none | none | `PATHS` | n/a | no | intentional redirect |
| `/login` | `LoginPage` | none | public | none | deep auth page import | yes | no | operational public |
| `/dashboard` | `DashboardPage` | `AppLayout` | parent auth | none | `@/features/dashboard` | yes | yes | placeholder/auth-only |
| `/products` | inline placeholder | `AppLayout` | parent auth + child permission | `products.view` | n/a | feature file is zero-byte | yes | permission-protected placeholder |
| `/customers` | inline placeholder | `AppLayout` | parent auth + child permission | `customers.view` | n/a | feature file is zero-byte | yes | permission-protected placeholder |
| `/inventory` | inline placeholder | `AppLayout` | parent auth | none | n/a | feature file is zero-byte | yes | backend-blocked placeholder |
| `/sales` | inline placeholder | `AppLayout` | parent auth | none | n/a | feature file is zero-byte | yes | placeholder/auth-only |
| `/procurement` | inline placeholder | `AppLayout` | parent auth | none | n/a | feature file is zero-byte | no direct nav item | backend-blocked placeholder |
| `/finance` | inline placeholder | `AppLayout` | parent auth | none | n/a | feature file is zero-byte | no direct nav item | placeholder/manual-review |
| `/reports` | inline placeholder | `AppLayout` | parent auth | none | n/a | feature file is zero-byte | yes | placeholder/manual-review |
| `/administration` | inline placeholder | `AppLayout` | parent auth | none | n/a | feature file is zero-byte | no direct nav item | placeholder/manual-review |
| `/settings` | inline placeholder | `AppLayout` | parent auth | none | n/a | feature file is zero-byte | yes | placeholder/manual-review |
| `*` | redirect to `/dashboard` | none | none | none | `PATHS` redirect target | n/a | no | catch-all |

No routes were added or removed.

## 6. Navigation Inventory

| Navigation ID | href | PATHS owner | Route registered | Page exists | Status |
| --- | --- | --- | --- | --- | --- |
| `dashboard` | `/dashboard` | `PATHS.DASHBOARD` | yes | `DashboardPage` | placeholder route |
| `pos` | `/sales/pos` | `PATHS.SALES.POS` | no | none | navigation-only mismatch |
| `sales-history` | `/sales` | `PATHS.SALES.HISTORY` | yes via `/sales` | inline placeholder | placeholder route |
| `refunds` | `/sales/refunds` | `PATHS.SALES.RETURNS` | no | none | navigation-only mismatch |
| `products` | `/products` | `PATHS.PRODUCTS.ROOT` | yes | inline placeholder | permission-protected placeholder |
| `inventory` | `/inventory` | `PATHS.INVENTORY.ROOT` | yes | inline placeholder | backend-blocked placeholder |
| `inventory-warehouses` | `/warehouses` | `PATHS.WAREHOUSES.ROOT` | no | none | navigation-only mismatch |
| `stock-adjustments` | `/inventory/adjustments` | `PATHS.INVENTORY.ADJUSTMENTS` | no | none | navigation-only mismatch |
| `customers` | `/customers` | `PATHS.CUSTOMERS.ROOT` | yes | inline placeholder | permission-protected placeholder |
| `purchase-orders` | `/procurement/purchase-orders` | `PATHS.PROCUREMENT.PURCHASE_ORDERS` | no | none | unsupported future route |
| `suppliers` | `/procurement/suppliers` | `PATHS.PROCUREMENT.SUPPLIERS` | no | none | verified backend, no page |
| `expenses` | `/finance/expenses` | `PATHS.FINANCE.EXPENSES` | no | none | navigation-only mismatch |
| `payments` | `/finance/payments` | `PATHS.FINANCE.PAYMENTS` | no | none | navigation-only mismatch |
| `cashbook` | `/finance/cashbook` | `PATHS.FINANCE.CASHBOOK` | no | none | navigation-only mismatch |
| `reports` | `/reports` | `PATHS.REPORTS.ROOT` | yes | inline placeholder | placeholder route |
| `analytics` | `/reports/analytics` | `PATHS.REPORTS.ANALYTICS` | no | none | navigation-only mismatch |
| `users` | `/administration/users` | `PATHS.ADMINISTRATION.USERS` | no | none | navigation-only mismatch |
| `roles` | `/administration/roles` | `PATHS.ADMINISTRATION.ROLES` | no | none | navigation-only mismatch |
| `permissions` | `/administration/permissions` | `PATHS.ADMINISTRATION.PERMISSIONS` | no | none | navigation-only mismatch |
| `branches` | `/administration/branches` | `PATHS.ADMINISTRATION.BRANCHES` | no | none | navigation-only mismatch |
| `administration-warehouses` | `/administration/warehouses` | `PATHS.ADMINISTRATION.WAREHOUSES` | no | none | navigation-only mismatch |
| `payment-methods` | `/administration/payment-methods` | `PATHS.ADMINISTRATION.PAYMENT_METHODS` | no | none | navigation-only mismatch |
| `settings` | `/settings` | `PATHS.SETTINGS.ROOT` | yes | inline placeholder | placeholder route |
| `tenant` | `/settings/tenant` | `PATHS.SETTINGS.TENANT` | no | none | navigation-only mismatch |

Navigation IDs were not changed.

## 7. Feature-Page Inventory

| Feature | Page files | Feature barrel | Operational pages | Placeholder pages | Router reference |
| --- | --- | --- | --- | --- | --- |
| auth | `LoginPage.tsx`, `AccessDeniedPage.tsx` | components barrel only | `LoginPage`, `AccessDeniedPage` | none | login, access-denied boundary |
| dashboard | `DashboardPage.tsx` | `features/dashboard/index.ts` | none | `DashboardPage` | `/dashboard` |
| products | `pages/ProductsPage.tsx` zero bytes | none | none | none | router uses inline placeholder |
| customers | `pages/CustomersPage.tsx` zero bytes | none | none | none | router uses inline placeholder |
| suppliers | no feature page folder | none | none | none | none |
| sales | `pages/SalesPage.tsx` zero bytes | none | none | none | router uses inline placeholder |
| inventory | `pages/InventoryPage.tsx` zero bytes | none | none | none | router uses inline placeholder |
| procurement | `pages/ProcurementPage.tsx` zero bytes | none | none | none | router uses inline placeholder |
| finance | `pages/FinancePage.tsx` zero bytes | none | none | none | router uses inline placeholder |
| reports | `pages/ReportsPage.tsx` zero bytes | none | none | none | router uses inline placeholder |
| administration | `pages/AdministrationPage.tsx` zero bytes | none | none | none | router uses inline placeholder |
| settings | `pages/SettingsPage.tsx` zero bytes | none | none | none | router uses inline placeholder |

Do not treat the zero-byte page files as operational pages.

## 8. Route Classification Criteria

Operational requires:

1. a real page implementation;
2. active frontend behavior;
3. no unsupported public service/hook dependency;
4. verified backend capability;
5. render behavior without fabricated business data.

Placeholder requires:

- safe presentation with no speculative API request;
- no unsupported query/mutation execution;
- no fabricated business data.

Backend-blocked means required backend capability is absent or intentionally
closed by previous migration evidence.

## 9. Operational Routes

Operational routes:

- `/login`

No authenticated business-domain route currently satisfies all operational
criteria. `/products` and `/customers` have verified route permissions, but the
active routed elements are inline placeholders, not operational feature pages.

## 10. Placeholder Routes

Placeholder routes:

- `/dashboard`
- `/products`
- `/customers`
- `/inventory`
- `/sales`
- `/procurement`
- `/finance`
- `/reports`
- `/administration`
- `/settings`

All registered placeholders are inline `div` elements or the safe
`DashboardPage` placeholder and do not import unsupported hooks or issue
network calls.

## 11. Backend-Blocked Routes

Backend-blocked or backend-unverified route areas:

- Inventory public frontend capability remains blocked by Migration 040.
- Procurement remains blocked except for Supplier backend capability.
- Finance and Reports services require manual review and no registered backend
  route evidence was captured in Migration 044.
- Administration permission vocabulary and route support remain ambiguous.
- Sales read/history is unsupported; verified sales capabilities are create and
  refund only.

## 12. Orphaned Routes

Router routes without direct navigation items:

- `/login`: intentional public auth route.
- `/`: intentional redirect.
- `/procurement`: intentional parent placeholder with child nav items.
- `/finance`: intentional parent placeholder with child nav items.
- `/administration`: intentional parent placeholder with child nav items.
- `*`: intentional catch-all redirect.

No dead route was removed.

## 13. Navigation Without Route Findings

Navigation hrefs without router entries:

- `/sales/pos`
- `/sales/refunds`
- `/warehouses`
- `/inventory/adjustments`
- `/procurement/purchase-orders`
- `/procurement/suppliers`
- `/finance/expenses`
- `/finance/payments`
- `/finance/cashbook`
- `/reports/analytics`
- `/administration/users`
- `/administration/roles`
- `/administration/permissions`
- `/administration/branches`
- `/administration/warehouses`
- `/administration/payment-methods`
- `/settings/tenant`

These were not registered because matching implemented pages do not exist.

## 14. Route Without Navigation Findings

Registered routes without direct navigation entries:

- `/login`: intentional.
- `/`: intentional redirect.
- `/procurement`: parent placeholder only.
- `/finance`: parent placeholder only.
- `/administration`: parent placeholder only.
- `*`: intentional catch-all.

## 15. Products Disposition

`/products` remains:

- PATHS-owned by `PATHS.PRODUCTS.ROOT`;
- router-registered;
- navigation-owned by `NAVIGATION_ITEM_IDS.PRODUCTS`;
- route-permission protected by `products.view`;
- backend-verified through Products list/detail guards;
- placeholder, because `features/products/pages/ProductsPage.tsx` is zero bytes
  and the router uses an inline placeholder.

No behavior was changed.

## 16. Customers Disposition

`/customers` remains:

- PATHS-owned by `PATHS.CUSTOMERS.ROOT`;
- router-registered;
- navigation-owned by `NAVIGATION_ITEM_IDS.CUSTOMERS`;
- route-permission protected by `customers.view`;
- backend-verified through Customers list/detail guards;
- placeholder, because `features/customers/pages/CustomersPage.tsx` is zero
  bytes and the router uses an inline placeholder.

No behavior was changed.

## 17. Suppliers Disposition

Supplier backend/service/hook capability exists:

- `GET /suppliers` and `GET /suppliers/<id>` use `suppliers.view`.
- public Supplier service and query hook facades exist.

No Supplier page exists, and no `/procurement/suppliers` route is registered.

Disposition:

```text
Verified backend capability, route missing, page missing.
```

No route or permission metadata was added.

## 18. Sales Disposition

Verified backend Sales capabilities:

- `POST /sales/checkout` with `sales.create`;
- `POST /sales/<sale_id>/refund` with `sales.refund`.

No `sales.view` backend route was verified. `SalesPage.tsx` is zero bytes, and
the active `/sales` route is an inline placeholder.

Disposition:

```text
Sales root remains placeholder/auth-only; POS and Refund navigation remain
navigation-only mismatches until real pages exist.
```

No `sales.view` permission metadata was added.

## 19. Inventory Disposition

Migration 040 closed public Inventory operational hooks because no public
Inventory API exists.

`InventoryPage.tsx` is zero bytes, and `/inventory` is an inline placeholder.

Disposition:

```text
Backend-blocked placeholder.
```

No Inventory route or permission metadata was added.

## 20. Procurement Disposition

Migration 039 established Supplier as the only verified backend Procurement
area capability. Purchase Orders and related Procurement flows remain
unsupported.

`ProcurementPage.tsx` is zero bytes, and `/procurement` is an inline
placeholder.

Disposition:

```text
Backend-blocked placeholder, except Supplier remains verified but page-missing.
```

## 21. Administration Disposition

Administration route support remains ambiguous:

- `AdministrationPage.tsx` is zero bytes.
- `/administration` is an inline placeholder.
- navigation permissions such as `users.view` and `roles.view` do not match the
  verified legacy backend constants `users.read` and `roles.read`.

Disposition:

```text
Placeholder/manual-review; no route permission metadata added.
```

## 22. Finance Disposition

`FinancePage.tsx` is zero bytes, `/finance` is an inline placeholder, and
Migration 044 recorded Finance services as requiring manual review.

Disposition:

```text
Placeholder/manual-review.
```

## 23. Reports Disposition

`ReportsPage.tsx` is zero bytes, `/reports` is an inline placeholder, and
Migration 044 recorded `reportService` as requiring manual review.

Disposition:

```text
Placeholder/manual-review.
```

## 24. Settings Disposition

`SettingsPage.tsx` is zero bytes, `/settings` is an inline placeholder, and
`/settings/tenant` has no registered route or page.

Disposition:

```text
Placeholder/manual-review.
```

Tenant settings were not conflated with broader Administration.

## 25. Route Permission Disposition

Route permission metadata remains owned by:

```text
frontend/src/routes/permissions.ts
```

No permission metadata changed.

Still protected:

- `/products` -> `products.view`
- `/customers` -> `customers.view`

No new permission was fabricated.

## 26. Router Import-Boundary Changes

No router import boundary was changed.

Current router imports:

- `LoginPage` by deep auth page path because no auth feature barrel exists.
- `DashboardPage` through the established `@/features/dashboard` feature
  barrel.

No feature barrel was created merely for style.

## 27. Files Inspected

Inspected:

- ADR-007, ADR-008, ADR-009;
- Migration 025, 030, 044, 050 reports;
- `frontend/src/routes/routes.ts`;
- `frontend/src/routes/permissions.ts`;
- `frontend/src/app/router.tsx`;
- `frontend/src/navigation/navigation.ts`;
- `frontend/src/navigation/ids.ts`;
- `frontend/src/features/`;
- Supplier, Sales, Inventory, Procurement, Administration, Finance, and Reports
  service/hook/report evidence.

## 28. Files Created

- `frontend/docs/architecture/reviews/MIGRATION-051-ROUTE-REGISTRY-ALIGNMENT.md`

## 29. Files Modified

No runtime source files were modified.

## 30. Verification Results

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

## 31. Static Verification

Commands:

```bash
rg "path:" frontend/src/app/router.tsx
rg "href:" frontend/src/navigation/navigation.ts
rg '"/[a-zA-Z]' frontend/src/app/router.tsx frontend/src/navigation/navigation.ts
rg "PATHS\\." frontend/src/app/router.tsx frontend/src/navigation/navigation.ts
```

Findings:

- router routes consume `PATHS`;
- navigation hrefs consume `PATHS`;
- no duplicate route/navigation URL literals were found;
- catch-all route is the only non-`PATHS` router path and is intentional;
- Products and Customers permission metadata remains aligned;
- unsupported routes were not made operational.

## 32. Remaining Route/Navigation Mismatches

Remaining mismatches are intentionally deferred:

- navigation child routes without router entries;
- zero-byte feature page files not routed;
- Supplier backend capability without a Supplier page;
- Sales POS/refund capabilities without page implementations;
- Administration permission vocabulary mismatch;
- Finance/Reports manual-review backend status.

## 33. Runtime Behavior Confirmation

Because this migration did not modify runtime source:

- route paths are unchanged;
- navigation paths are unchanged;
- permission-protected Products and Customers behavior is unchanged;
- placeholders remain inert and do not issue unsupported API requests;
- backend remains the authorization security boundary.

## 34. Invariants Verified

Verified:

1. `PATHS` remains the canonical URL owner.
2. Router consumes `PATHS`.
3. Navigation consumes `PATHS`.
4. Operational routes map to real pages where operational behavior exists.
5. Placeholder routes are explicitly classified.
6. Backend-blocked routes remain non-operational.
7. Route permission metadata remains backend-verified.
8. No permission was fabricated.
9. Navigation IDs remain unchanged.
10. No unsupported API request was activated.
11. Authorization remains frontend usability only.
12. Query scope remains unchanged.
13. No backend files were changed.
14. TypeScript remains at zero errors.
15. Production build remains successful.

## 35. Rollback Boundary

Rollback is limited to removing this report.

No runtime source rollback is required.

## 36. Recommended Next Migration

Recommended next migration:

```text
Migration 052 - Supplier Page Boundary And Route Activation
```

Goal:

```text
Create the first real Supplier page boundary only if it can consume the
verified Supplier service and query-hook contracts without introducing
unsupported Procurement behavior.
```

