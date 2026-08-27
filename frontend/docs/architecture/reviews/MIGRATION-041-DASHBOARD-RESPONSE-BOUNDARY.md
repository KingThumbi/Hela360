# Migration 041 - Dashboard Response Boundary

## 1. Migration Purpose

Migration 041 aligns the frontend Dashboard boundary with verified backend
capabilities.

This migration does not create Dashboard endpoints, response DTOs, service
methods, query keys, invalidation rules, fake metrics, routes, or backend
contracts.

## 2. ADR Rules Applied

- ADR-001: public service facades must expose verified backend operations.
- ADR-002: hooks must not issue unsupported network requests.
- ADR-003: query keys remain centralized and unchanged.
- ADR-004: response projections must not be fabricated.
- ADR-005: unsupported operations reject explicitly without fallback data.
- ADR-006: tenant/branch context remains backend/API-layer owned.
- ADR-008: public module boundaries expose only stable contracts.
- ADR-009: Dashboard names remain business-oriented, but unsupported names are
  not made public.

## 3. Compiler Baseline

Pre-migration command:

```bash
cd /home/thumbi/Hela360/frontend
npx tsc -b --pretty false 2>&1 | tee /tmp/hela360-migration-041-errors.txt
grep -c "error TS" /tmp/hela360-migration-041-errors.txt
```

Pre-migration total:

```text
14 TypeScript errors
```

## 4. Initial Dashboard Diagnostics

Direct Dashboard diagnostics before this migration:

```text
8 errors
```

| Category | Count |
| --- | ---: |
| Missing `@/types/apis` response projection module | 4 |
| Missing Dashboard facade methods on `dashboardService` | 4 |

Affected files:

- `useDashboardActivity.ts`
- `useDashboardAlerts.ts`
- `useDashboardMetrics.ts`
- `useDashboardOverview.ts`

## 5. Backend Capability Matrix

Current active app-factory registrations in `app/__init__.py`:

```text
auth, health, products, customers, sales, suppliers
```

No registered Dashboard blueprint or route was found.

Searches across `app/api`, `app/models`, `app/schemas`, `app/serializers`, and
`app/services` found only internal or unrelated support code:

- `app/api/sales.py` has internal sales summary serialization helpers.
- `app/services/tenant/auth/login_attempt_service.py` has authentication
  statistics helpers.
- `app/models/security.py` references analytics/reporting in comments.

The repository currently has no `tests` directory to inspect.

| Dashboard concept | Registered route | Response schema | Frontend disposition |
| --- | --- | --- | --- |
| Application Dashboard | None | None | Unsupported |
| Sales Dashboard | None | None | Private blocked placeholder from earlier migration |
| Procurement Dashboard | None | None | Private blocked placeholder from earlier migration |
| Inventory Dashboard | None | None | Unsupported |
| Reporting/Analytics Summary | None | None | Insufficient backend evidence |

## 6. Application Dashboard Disposition

Application Dashboard hooks are not publicly operational.

Private hooks retained:

- `useDashboardOverview`
- `useDashboardMetrics`
- `useDashboardAlerts`
- `useDashboardActivity`

Disposition:

- removed from the public Dashboard hook barrel;
- disabled with `enabled: false`;
- configured with `retry: false`;
- use existing Dashboard query keys only;
- issue no service request;
- return no fake metrics, alerts, activity, or summary data.

## 7. Sales Dashboard Disposition

Sales Dashboard remains unsupported as a public frontend capability.

This migration did not modify Sales files or the Sales canonical facade. Static
verification confirms `useSalesDashboard` remains only as a private placeholder
hook.

## 8. Procurement Dashboard Disposition

Procurement Dashboard remains unsupported as a public frontend capability.

This migration did not modify Procurement files. Static verification confirms
`useProcurementDashboard` remains only as a private placeholder hook.

## 9. Inventory Dashboard Disposition

Inventory Dashboard remains unsupported as a public frontend capability.

This migration did not modify Inventory files and did not create Inventory
dashboard response projections or service methods.

## 10. Response Projection Disposition

No Dashboard response projections were created.

Unsupported symbols intentionally remain absent:

- `DashboardOverviewResponse`
- `DashboardMetricsResponse`
- `DashboardAlertsResponse`
- `DashboardActivityResponse`

Service-local Dashboard interfaces remain private implementation details in
`dashboardService.ts` and are no longer exported through the public Dashboard
service barrel.

## 11. Canonical Service Owner

No canonical Dashboard service owner was established.

The existing private Dashboard service file is preserved as unfinished code,
but it is not exported publicly until a registered backend Dashboard contract
exists.

## 12. Canonical Facade Method

No canonical Dashboard facade method was created.

Unsupported method names such as `getOverview`, `getMetrics`, `getAlerts`, and
`getActivity` were removed from hook call sites instead of being added to the
service facade.

## 13. Response Unwrapping

No response-unwrapping contract was introduced because no backend Dashboard
response contract was verified.

## 14. Public Barrel Changes

Service barrel:

```text
frontend/src/services/dashboard/index.ts
```

Before:

```text
exported DashboardService, dashboardService, and service-local Dashboard types
```

After:

```text
export {}
```

Hook barrel:

```text
frontend/src/hooks/queries/dashboard/index.ts
```

Before:

```text
exported useDashboardOverview, useDashboardMetrics, useDashboardAlerts, useDashboardActivity
```

After:

```text
export {}
```

## 15. DashboardPage Preservation

`DashboardPage` remains the placeholder implemented by the frontend capability
shell:

```text
Dashboard Module (Coming Soon)
```

No route, navigation, or presentation behavior was changed.

## 16. Query Key And Invalidation Preservation

No query keys were added, removed, renamed, or reshaped.

No invalidation policy was added or modified.

Existing Dashboard query keys remain available for future backend-backed
migrations:

- `QUERY_KEYS.dashboard.overview()`
- `QUERY_KEYS.dashboard.metrics()`
- `QUERY_KEYS.dashboard.alerts()`
- `QUERY_KEYS.dashboard.activity()`

## 17. Files Modified

- `frontend/src/services/dashboard/index.ts`
- `frontend/src/hooks/queries/dashboard/index.ts`
- `frontend/src/hooks/queries/dashboard/useDashboardOverview.ts`
- `frontend/src/hooks/queries/dashboard/useDashboardMetrics.ts`
- `frontend/src/hooks/queries/dashboard/useDashboardAlerts.ts`
- `frontend/src/hooks/queries/dashboard/useDashboardActivity.ts`

## 18. Files Created

- `frontend/docs/architecture/reviews/MIGRATION-041-DASHBOARD-RESPONSE-BOUNDARY.md`

## 19. Verification

Post-migration TypeScript command:

```bash
cd /home/thumbi/Hela360/frontend
npx tsc -b --pretty false
```

Post-migration TypeScript total:

```text
6 TypeScript errors
```

Dashboard diagnostics after this migration:

```text
0 errors
```

Build command:

```bash
cd /home/thumbi/Hela360/frontend
npm run build
```

Build result:

```text
failed during tsc with the same 6 remaining non-Dashboard errors
```

Static verification:

```bash
rg -n "SalesDashboard|ProcurementDashboard|InventoryDashboard|useSalesDashboard|useProcurementDashboard|salesDashboardService|procurementDashboardService|getDashboard" frontend/src
```

Result:

```text
only private useSalesDashboard and useProcurementDashboard placeholders remain
```

Static Dashboard mismatch verification:

```bash
rg -n "@/services/dashboard|@/types/apis|dashboardService\.get|getOverview|getMetrics|getAlerts|getActivity" frontend/src/hooks/queries/dashboard frontend/src/services/dashboard/index.ts
```

Result:

```text
no matches
```

## 20. Compiler Delta

| Scope | Before | After | Delta |
| --- | ---: | ---: | ---: |
| Total TypeScript errors | 14 | 6 | -8 |
| Direct Dashboard errors | 8 | 0 | -8 |

## 21. Remaining Global Diagnostics

Remaining non-Dashboard compiler errors:

| Cluster | Count |
| --- | ---: |
| Administration enum export boundary | 2 |
| Strict TypeScript cleanup | 4 |

Remaining files:

- `src/services/administration/index.ts`
- `src/hooks/useTheme.ts`
- `src/lib/queryFactory.ts`
- `src/main.tsx`

## 22. Backend Work Required

A future Dashboard implementation needs a registered backend capability before
the frontend can expose public hooks or service methods.

Required backend evidence:

- registered Dashboard route or blueprint;
- request and response schemas;
- serializer behavior;
- route-level tests;
- a documented ownership boundary for cross-domain summaries.

## 23. Runtime Behavior

Public Dashboard imports are no longer available from the Dashboard barrels.

Private Dashboard hooks are inert by default. They do not fetch, retry, or
fabricate data. If a private caller invokes the stored `queryFn` manually, it
rejects with an explicit unsupported-capability error.

## 24. Invariants Preserved

- No backend files changed.
- No query key files changed.
- No invalidation files changed.
- No Sales canonical facade changes.
- No Procurement, Inventory, route, navigation, Administration, or strict
  cleanup changes were made.
- No fake Dashboard data was introduced.

## 25. Recommended Next Migration

Migration 042 should address the Administration enum export boundary.

That is the remaining architecture-boundary cluster before the final strict
TypeScript cleanup.
