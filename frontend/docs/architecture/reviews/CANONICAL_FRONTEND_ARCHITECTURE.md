# Canonical Frontend Architecture

## Repository State

This document is a target architecture specification for the Hela360 frontend. It is not a patch plan, compiler-error repair guide, or source-code migration script.

The repository is currently in a dirty state with existing tracked modifications, deletions, and untracked frontend architecture files. This document treats that state as intentional user work. It does not instruct restoring, deleting, moving, staging, committing, formatting, or repairing application source files.

Evidence standards used here:

- Accepted ADRs are authoritative over implementation drift.
- Mandatory `SHALL` and `MUST` statements are binding.
- ADR examples illustrate intent but do not override mandatory rules.
- When an ADR is missing, empty, ambiguous, or contradicted by implementation, this document marks the item as an open question.
- Current implementation observations are evidence of drift or partial implementation, not automatic authority.

ADR-008 is present as an accepted ADR filename but is a zero-byte file. No module-boundary rules can be derived from it. Any architecture that depends on ADR-008 requires ADR clarification before source migration.

## 1. Architectural Authority

The frontend architecture is governed by ADR-001 through ADR-010 under `frontend/docs/architecture/adr/`.

Authority order:

1. Accepted ADR mandatory language.
2. Explicit ADR dependency chain and conflict resolution.
3. Current implementation only where it does not conflict with accepted ADRs.
4. Migration reports as diagnostic evidence only.

Dependency chain:

- ADR-001 has no prerequisite ADR.
- ADR-002 depends on ADR-001.
- ADR-003 depends on ADR-001 and ADR-002.
- ADR-004 depends on ADR-001 through ADR-003.
- ADR-005 depends on ADR-001 through ADR-004.
- ADR-006 depends on ADR-001 through ADR-005.
- ADR-007 depends on ADR-001 through ADR-006.
- ADR-008 contains no readable rules.
- ADR-009 depends on ADR-001 through ADR-008.
- ADR-010 depends on ADR-001 through ADR-009.

Conflict rule:

- Later mandatory ADR language supersedes earlier examples when both address the same concern.
- Earlier mandatory ADR boundaries remain binding unless a later ADR explicitly changes them.
- Examples do not authorize public APIs that violate mandatory naming, ownership, or dependency rules.

## 2. Canonical Dependency Direction

Canonical dependency flow:

`components/routes/layouts -> hooks -> service facades -> internal domain services -> BaseService -> api client -> backend`

Shared type packages are importable by all layers, but types must not import runtime layers.

Cross-cutting layers:

- `providers` establish application, auth, tenant, branch, query, shell, theme, and authorization context.
- `navigation` consumes authorization state through helpers and exposes route/menu metadata.
- `lib/queryKeys.ts` owns all TanStack Query keys.
- `lib/queryInvalidation.ts` owns all cache invalidation policy.
- `lib/errors.ts` owns normalized frontend error contracts.
- `store` may hold UI/session state, but business operations still flow through hooks and services.

Prohibited bypasses:

- Components must not import Axios, `apiClient`, `BaseService`, endpoint constants, or domain services directly.
- Hooks must not call Axios, construct URLs, import `BaseService`, or communicate across domains.
- Services must not import React, TanStack Query, providers, routes, navigation, UI state, or cache invalidation helpers.
- Services must not manually manage tenant, branch, auth header, or refresh-token behavior.
- Types must not import services, hooks, providers, stores, routes, navigation runtime modules, or components.
- Domain internals must not be exported as public APIs unless a facade intentionally exposes them.
- Mutation hooks and workflows must not directly define invalidation policy.

## 3. Canonical Frontend Folder Structure

| Path | Canonical responsibility | Public boundary | Prohibited contents |
| --- | --- | --- | --- |
| `src/api` | API client, request enrichment, refresh, interceptors, transport concerns | API client used by services/BaseService only | React hooks, components, business service methods, domain DTO definitions |
| `src/app` | App bootstrap composition when needed | App-level entry modules | Domain business logic |
| `src/assets` | Static frontend assets | Imported by UI only | Runtime business contracts |
| `src/authorization` | Authorization service/context helpers from ADR-007 | `can`, `canAny`, `canAll`, role/permission helpers | Backend security enforcement, domain hook logic |
| `src/components` | Reusable UI components | Component exports | API calls, service calls, business workflows |
| `src/constants` | Stable app constants that are not query keys or permissions | Named constants | Endpoint construction in components/hooks, business entities |
| `src/features` | Feature-level UI composition where domain screens are grouped | Feature views and local UI glue | Shared service facades, global types |
| `src/hooks` | Query, mutation, and UI hooks | Hook barrels by domain/common area | Axios calls, endpoint strings, DTO definitions, cross-domain service calls |
| `src/layouts` | Layout shells and route frame components | Layout components | Domain operations |
| `src/lib` | Query keys, invalidation, errors, storage, utility libraries | Stable library functions | Domain-specific facades, UI screens |
| `src/navigation` | Navigation registry, route/menu metadata, breadcrumb/filter helpers | Registry and helper functions | Permission decisions outside authorization helpers |
| `src/providers` | Context providers and provider composition | Provider components and public access hooks | Business service implementation |
| `src/routes` | Route configuration, protected route boundaries | Route objects/components | Raw authorization logic duplicated across screens |
| `src/services` | Domain service facades and internal domain services | One facade per business domain unless ADR clarifies otherwise | React state, hooks, cache invalidation, business entity definitions |
| `src/store` | UI/session/application state stores | Store hooks/actions | Backend business rules, service facades |
| `src/types` | Canonical reusable TypeScript contracts | Type barrels | Runtime imports from navigation/services/hooks/components |
| `src/validation` | UI/form/workflow input validation schemas | Validation schemas/types | Backend-only business rule enforcement |

Open question: ADR-008 was expected to clarify module boundaries but is empty. The table above is derived from ADR-001 through ADR-007, ADR-009, ADR-010, and current implementation structure. It should be confirmed once ADR-008 is restored or rewritten.

## 4. Domain Module Ownership

Canonical business domains currently identified by ADRs:

- Products
- Customers
- Suppliers
- Inventory
- Procurement
- Sales
- Finance
- Administration
- Reports and dashboard views as read/query domains
- Auth, tenant, branch, authorization as cross-cutting domains

Ownership rules:

- A domain service facade owns public business operations for its domain.
- Internal domain services may exist only behind the facade.
- Domain query hooks own data-fetching integration for UI consumers.
- Domain mutation hooks own one business operation each.
- Domain types are not owned by services or hooks; they live under `src/types`.
- Cross-domain effects are represented in centralized invalidation, not cross-domain hook calls.

Administration open question:

ADR-001 requires every business domain to expose a single public service facade. The current implementation appears to expose lower-level administration services such as user, role, permission, branch, and tenant services. Canonically, these should sit behind an `administrationService` facade unless a later ADR explicitly treats them as independent business domains.

## 5. Public/Internal Module Boundaries

Public boundaries:

- Domain service facade: `src/services/<domain>/index.ts` should expose the public facade and approved type-only exports.
- Domain hooks: `src/hooks/queries/<domain>/index.ts` and mutation hook barrels expose UI-facing hooks.
- Types: `src/types/index.ts` and category barrels expose canonical type contracts.
- Providers: provider barrels expose provider components and access hooks, not raw contexts unless deliberately documented.
- Navigation: navigation barrel exposes registry and helper names consumed by routes/layouts.

Internal boundaries:

- `src/services/<domain>/*Service.ts` files other than the facade are internal delegates.
- Transport helpers inside `BaseService` are not UI APIs.
- Query key implementation details are accessed through `QUERY_KEYS`, not hardcoded arrays.
- Invalidation policy is accessed through named helper functions, not ad hoc invalidation in hooks.

Current drift examples:

- `src/services/sales/index.ts` exports decomposed sales services directly while several of those files are empty. The canonical boundary is a complete `salesService` facade that may delegate internally.
- `src/providers/index.ts` is empty while `src/main.tsx` imports `AppProvider` from the provider barrel. The canonical boundary requires public barrels to match consumers.
- `src/hooks/useNavigation.ts` imports helper names that are not exported by `src/navigation/index.ts`. The canonical boundary requires exported helper names to be stable.

## 6. Canonical Type System

ADR-004 owns type placement.

Canonical categories:

| Type category | Location | Examples |
| --- | --- | --- |
| Business entities | `src/types/entities` | `Sale`, `Customer`, `Supplier`, `Product`, `InventoryItem`, `PurchaseOrder`, `Branch`, `User`, `Role`, `Permission` |
| Request DTOs | `src/types/requests` | `LoginRequest`, `CreateSaleRequest`, `UpdateSaleRequest`, `RefundSaleRequest`, `PaginationRequest` when used as backend query input |
| Response DTOs | `src/types/responses` | `SalesDashboard`, `InventorySummary`, `CashierSummary`, `DailySalesSummary` |
| Business enums or unions | `src/types/enums` | sale status, payment method, permission names, branch status |
| Generic API wrappers | `src/types/api` | `ApiResponse`, `ApiError`, `PaginatedResponse`, `PaginationMeta` |
| Common value objects | `src/types/common` | `Money`, `Address`, `PhoneNumber`, `AuditFields`, `DateRange`, `Coordinates` |

Canonical ownership decisions:

- `ApiResponse`, `ApiError`, `PaginatedResponse`, and `PaginationMeta` belong under `src/types/api`.
- `PaginationRequest` belongs under `src/types/requests` when it represents request/query input sent to the backend.
- Auth request DTOs belong under `src/types/requests`.
- Auth response DTOs belong under `src/types/responses`.
- `Tenant`, `Branch`, `User`, `Role`, and `Permission` are entities.
- Session identity and authorization context are cross-cutting common contracts unless the backend returns them as named response projections.
- Hook option contracts that are purely hook-layer API may be public exports from `src/hooks/queries/common`; if reused outside the hook layer, they should move to `src/types/common`.

Type invariants:

- A reusable type has one owner.
- Services consume shared types and do not define business entities.
- Hooks consume shared types and do not define DTOs for backend contracts.
- Type-only imports must use `import type` under `verbatimModuleSyntax`.
- Type modules must not import navigation runtime modules, providers, hooks, services, stores, or components.

Current drift examples:

- `src/types/auth.ts` duplicates contracts also present in request and response type files.
- `src/types/navigation.ts` imports runtime navigation modules, violating type-layer dependency direction.
- Current enum usage conflicts with the active TypeScript `erasableSyntaxOnly` setting.

## 7. Canonical Service Layer

ADR-001 owns the service layer.

Service rules:

- Every business domain exposes one public service facade.
- Public service methods use business-oriented names.
- Services hide HTTP, Axios, URLs, REST shape, backend routing, and DTO conversion.
- Services propagate normalized errors but do not decide presentation.
- Services inherit `BaseService` for generic CRUD and transport helpers.
- Services do not contain React state, hooks, TanStack Query logic, cache invalidation, UI logic, or business entity definitions.
- Domain services are tenant-agnostic. Tenant and branch context are attached by the centralized API layer.

Forbidden public method names from ADR-001 include:

- `checkout`
- `post`
- `patch`
- `payments`
- `receipt`

Canonical service facade table:

| Domain | Canonical public facade | Internal delegates allowed |
| --- | --- | --- |
| Auth | `authService` | token/session helpers behind facade |
| Products | `productService` | catalog/category/pricing delegates |
| Customers | `customerService` | profile/ledger delegates |
| Suppliers | `supplierService` | supplier performance/payment delegates |
| Inventory | `inventoryService` | stock/movement/count delegates |
| Procurement | `procurementService` | purchase order/goods receipt delegates |
| Sales | `salesService` | query/workflow/payment/receipt/refund/dashboard/prescription delegates |
| Finance | `financeService` | invoice/payment/accounting delegates |
| Administration | `administrationService` unless ADR clarifies subdomains | user/role/permission/tenant/branch delegates |

## 8. Canonical Sales Service Architecture

The Sales domain requires a complete public `salesService` facade. Internal decomposition is permitted only if the facade remains the single UI/hook-facing public API.

Current implementation evidence:

- `legacySalesService.ts` defines a `SalesService` extending `BaseService`, but exposes legacy names including `checkout`, `payments`, and `receipt`.
- Sales index exports decomposed services directly.
- Several decomposed sales service files are empty.
- Sales hooks call `completeSale` and `listSales`, while the legacy service exposes different method names.

Canonical sales facade:

| Public method | Purpose | Internal delegate | Request type | Response type | Verification required |
| --- | --- | --- | --- | --- | --- |
| `listSales` | Retrieve filterable/paginated sales | `salesQueryService` | sales filters plus `PaginationRequest` | `PaginatedResponse<Sale>` or backend wrapper | Confirm backend list filters, tenant/branch scoping, response wrapper |
| `getSale` | Retrieve one sale by id | `salesQueryService` | sale id | `Sale` or `ApiResponse<Sale>` | Confirm endpoint and wrapper |
| `createSale` | Create a sale draft or initial sale record | `salesWorkflowService` | `CreateSaleRequest` | `Sale` | Confirm whether backend distinguishes draft, cart, and sale |
| `updateSale` | Update mutable sale details | `salesWorkflowService` | `UpdateSaleRequest` | `Sale` | Confirm whether completed sales are mutable |
| `deleteSale` | Delete/cancel a removable sale record if supported | `salesWorkflowService` | sale id | `void` or mutation response | Confirm whether deletion is allowed or replaced by voiding |
| `completeSale` | Complete sale workflow | `salesWorkflowService` | `CompleteSaleRequest` | `Sale` or completion response | Confirm payment and receipt behavior |
| `suspendSale` | Suspend an in-progress sale | `salesWorkflowService` | `SuspendSaleRequest` | `Sale` | Confirm backend support |
| `resumeSale` | Resume a suspended sale | `salesWorkflowService` | sale id or `ResumeSaleRequest` | `Sale` | Confirm backend support |
| `voidSale` | Void a sale | `salesWorkflowService` | `VoidSaleRequest` | `Sale` or void response | Confirm authorization and audit fields |
| `refundSale` | Refund a completed sale | `refundService` | `RefundSaleRequest` | `SaleRefund` or refund response | Confirm partial/full refund model |
| `listSalePayments` | List payments for a sale | `paymentService` | sale id plus optional pagination | `SalePayment[]` or paginated wrapper | Confirm endpoint naming |
| `getSalePayment` | Retrieve one payment | `paymentService` | payment id | `SalePayment` | Confirm entity name |
| `listReceipts` | List receipts | `receiptService` | filters plus pagination | `SalesReceipt[]` or paginated wrapper | Resolve `Receipt` vs `SalesReceipt` naming |
| `getReceipt` | Retrieve receipt metadata or printable receipt | `receiptService` | receipt id or sale id | `SalesReceipt`, printable payload, or file response | Confirm backend representation |
| `getSalesDashboard` | Retrieve sales dashboard projection | `salesDashboardService` | date/branch filters | `SalesDashboard` | Confirm projection shape |
| `listPrescriptionsForSale` | Retrieve linked prescriptions if sales owns this concern | `prescriptionService` | sale/customer filters | prescription projection | Confirm domain ownership |

Canonical sales rules:

- Hooks import only `salesService` from the public sales service boundary.
- Internal sales delegates are not consumed by components or hooks.
- Legacy names such as `checkout`, `complete`, `payments`, and `receipt` are not public facade methods.
- Workflow methods describe business outcomes, not HTTP mechanics.
- Sales service methods never invalidate query caches.
- Sales mutation hooks call centralized invalidation helpers after successful workflows.

Open questions:

- Whether sale deletion exists or must be modeled only as voiding.
- Whether receipts are entities, response projections, printable files, or all three.
- Whether prescriptions are owned by Sales or another clinical/pharmacy domain.
- Whether dashboard projections are Sales-owned or Reports-owned.

## 9. Canonical Query and Mutation Hook Layer

ADR-002 owns hook architecture.

Canonical query hooks:

- Live under `src/hooks/queries/<domain>`.
- Begin with `use`.
- Fetch data only.
- Invoke domain service facades only.
- Use `QUERY_KEYS` only for cache keys.
- Expose loading, error, and data state.
- Do not mutate backend state.
- Do not construct URLs or call Axios.

Canonical mutation hooks:

- Expose one business operation.
- Invoke a service facade method.
- Propagate normalized errors.
- Call centralized invalidation helpers after success.
- Do not duplicate invalidation policy.
- Do not call other domain hooks or services.

Common hook API:

- Shared hook utilities live under `src/hooks/queries/common`.
- Hook-specific option contracts may be exported by the common hook barrel when they describe hook API, not business data.
- Business DTOs and reusable app contracts still belong under `src/types`.

## 10. Canonical Query-Key Architecture

ADR-003 owns query keys. ADR-009 adds naming constraints.

Canonical rules:

- Every cache key comes from `src/lib/queryKeys.ts`.
- Hardcoded query key arrays are prohibited outside the query-key module.
- Each domain has a root namespace.
- Nested keys derive from the root.
- List and detail keys are explicit.
- Tenant and branch context must be represented so cache data cannot leak across tenant or branch boundaries.

Canonical shape:

```ts
QUERY_KEYS.sales.root
QUERY_KEYS.sales.list(scope, filters)
QUERY_KEYS.sales.detail(scope, saleId)
QUERY_KEYS.sales.payments(scope, saleId)
QUERY_KEYS.sales.receipts(scope, filters)
QUERY_KEYS.sales.dashboard(scope, filters)
```

`scope` means tenant and active branch context, or another canonical tenant/branch key object approved during implementation.

Sales naming resolution:

- Use `sales.root`.
- Use `sales.list(...)`.
- Use `sales.detail(id)`.
- Do not use `sales.sales`.
- Do not use `sales.sale`.

Open question:

ADR-003 examples use plural domain roots while ADR-009 states query key root names should be singular. Because ADR-009 is later and mandatory naming is stronger than examples, implementation should document the final root convention before migration. For Sales specifically, the project request requires ADR-style root/list/detail under `sales`, so this document uses `sales.root`, `sales.list`, and `sales.detail`.

## 11. Canonical Cache Invalidation Architecture

ADR-003 owns invalidation.

Canonical rules:

- All invalidation policy lives in `src/lib/queryInvalidation.ts`.
- Mutation hooks and workflows invoke named invalidation helpers.
- Mutation hooks do not decide individual query keys.
- Services never invalidate caches.
- Components never invalidate caches directly.
- Cross-domain invalidation is centralized.

Canonical business invalidation:

| Business operation | Required invalidation domains |
| --- | --- |
| Sale completion | Sales, Inventory, Finance, Customers, Reports, Dashboard |
| Goods receipt | Procurement, Inventory, Suppliers, Finance, Dashboard |
| Stock adjustment | Inventory, Dashboard |
| Authorization refresh | Current user, permissions, navigation, dashboard, feature config |
| Tenant switch | All tenant-scoped state and cache |
| Branch switch | Branch-scoped domain data |

Tenant and branch invalidation:

- Tenant change clears or rebuilds all scoped cache and local state.
- Branch change invalidates branch-scoped data without requiring re-authentication.
- Cache keys and invalidation helpers must share the same scope model.

## 12. Multi-Tenant and Branch Architecture

ADR-006 owns tenant and branch architecture.

Canonical rules:

- Successful authentication establishes user, tenant, active branch, permissions, and roles.
- Authentication fails if tenant context is missing.
- Every authenticated API request includes tenant context through the centralized API layer.
- Services are tenant-agnostic and branch-agnostic.
- Hooks obtain tenant and branch context from providers/state, never hardcoded values.
- Tenant and branch identity participate in query-key scoping and invalidation.
- Tenant changes clear and rebuild scoped state.
- Branch changes refresh branch-scoped data without re-authentication.
- Frontend role/permission checks improve UX; backend remains the security boundary.

Current implementation evidence:

- API interceptors attach `X-Tenant-ID` and `X-Branch-ID` from storage.
- Storage persists tenant and branch ids.
- Auth identity includes tenant and branch fields.
- Auth store stores identity but does not fully establish tenant/branch storage as a canonical lifecycle.
- Branch hook and shell store are placeholders and do not yet drive cache invalidation.

Open questions:

- Whether active branch is owned by AuthProvider, ShellProvider, a dedicated BranchProvider, or ApplicationProvider.
- Exact backend header names and whether they are final.
- Whether tenant switching is supported for the same authenticated user or only logout/login.

## 13. Authorization Architecture

ADR-007 owns authorization.

Canonical rules:

- Backend enforces RBAC.
- Frontend exposes centralized authorization helpers for UX and navigation.
- Permissions use lowercase dot notation.
- Components use authorization helpers, not hardcoded role checks.
- Hooks do not implement authorization.
- Services do not enforce frontend authorization.
- Protected routes declare authorization requirements.
- Unauthorized navigation renders an access-denied experience.
- Navigation menus are permission-aware.
- Authorization changes invalidate user, permissions, navigation, dashboard, and feature config.

Canonical authorization surface:

```ts
authorizationService.can(permission)
authorizationService.canAny(permissions)
authorizationService.canAll(permissions)
authorizationService.hasRole(role)
authorizationService.hasAnyRole(roles)
```

Open questions:

- Exact location of permission constants: ADR-007 requires centralization but ADR-004/ADR-009 constrain type/value ownership.
- Whether permission names are string unions, const objects, or another erasable TypeScript-compatible representation.

## 14. Provider Architecture

Canonical provider composition must establish cross-cutting context before consumers render.

Current supported composition evidence:

`ThemeProvider -> QueryProvider -> AuthProvider -> ShellProvider -> TooltipProvider -> application children/toaster`

Canonical additions required by ADRs:

- Authorization context/service must be available to routes, navigation, menus, and components.
- Tenant and branch context must be established after auth and before scoped data loads.
- Application-level context must expose stable public hooks, not private context internals.

Provider boundary rules:

- Provider barrels export provider components and public access hooks.
- Consumers prefer hooks such as `useApplicationContext`, `useAuthorization`, `useCurrentTenant`, and `useCurrentBranch`.
- Raw context exports are optional and should be deliberate.
- Providers may coordinate state and lifecycle, but do not implement domain services.

Current drift examples:

- `src/providers/index.ts` is empty while the app imports `AppProvider` from it.
- `ApplicationContext` is private while another hook imports it directly.
- `ProtectedRoute` does not yet express permission requirements.

Open question:

The ADRs do not mandate whether authorization, tenant, and branch should be separate providers or merged into existing auth/application providers. Implementation should choose one composition and document it before migration.

## 15. Navigation Architecture

ADR-007 and ADR-009 govern navigation.

Canonical rules:

- Navigation registry lives under `src/navigation`.
- Navigation item ids are stable and unique.
- Route paths and item ids are consistent with protected route declarations.
- Permission requirements are declared as data.
- Filtering uses authorization helpers.
- Components and hooks do not duplicate permission logic.
- Navigation barrel exports the exact helper names consumed by routes/layouts/hooks.
- Breadcrumb helpers derive from the canonical registry.

TypeScript compatibility:

- Runtime values used by navigation must be valid under `erasableSyntaxOnly`.
- Enums are not canonical unless the compiler configuration permits them.
- Suitable representations include const objects with derived unions or string unions plus runtime constants.

Current drift examples:

- Duplicate `warehouses` navigation item ids exist.
- Navigation types import runtime navigation modules.
- `useNavigation` imports helper names not exported by the navigation barrel.

## 16. Error Architecture

ADR-005 owns error architecture.

Canonical error categories:

- Infrastructure
- Transport
- Business
- Presentation

Canonical normalized error shape:

```ts
{
  code: string
  message: string
  category: "infrastructure" | "transport" | "business" | "presentation"
  details?: unknown
  retryable: boolean
}
```

Canonical rules:

- API and service layers normalize HTTP/API errors.
- Hooks and components do not interpret raw HTTP status codes.
- Validation errors preserve field-level information.
- Auth failures trigger session invalidation and redirect behavior centrally.
- Authorization failures go through the authorization layer.
- Mutation hooks propagate normalized errors without presentation transformation.
- Unexpected errors are logged centrally without hard dependency on a vendor.

TypeScript compatibility:

- Runtime error codes must be runtime values.
- Type aliases must not be used as runtime objects.
- `AppError` should include category and retryable fields required by ADR-005.

## 17. Domain Event Architecture

ADR-010 owns workflow and domain-event architecture.

Canonical rules:

- Frontend business operations are modeled as workflows.
- A workflow represents one business outcome.
- Workflows invoke services and then centralized invalidation.
- Workflows expose progress and normalized errors.
- Domain events are occurred facts named in past tense.
- Commands are requested actions.
- Backend remains source of truth.
- Frontend coordinates sequence but does not implement backend business rules.

Allowed immediate model:

- Workflow hooks may be the initial implementation of frontend workflow orchestration.
- Events may be represented as typed facts emitted after confirmed backend success.
- Cache side effects still go through `queryInvalidation.ts`.

Not yet specified by ADRs:

- A global event bus.
- Publisher/subscriber mechanics.
- Event persistence.
- Sagas, CQRS, offline queues, or push synchronization.

Open question:

Whether ADR-010 requires a concrete domain-event runtime now or only typed workflow/event modeling during migration.

## 18. TypeScript and Runtime Compatibility Constraints

Current TypeScript settings impose architectural constraints.

Canonical constraints:

- Use `import type` for type-only imports.
- Do not import runtime modules from type packages.
- Do not rely on TypeScript enums if `erasableSyntaxOnly` rejects them.
- Prefer const objects plus derived unions for runtime constants that also need type safety.
- Avoid parameter properties when `erasableSyntaxOnly` is enabled.
- Runtime symbols must exist at runtime; type aliases are erased.
- Barrels must export the values/types their consumers import.
- JSX runtime usage must match the active TypeScript and Vite configuration.

Architecture implication:

The canonical architecture must be compatible with the compiler, not merely with conceptual ADR boundaries. Navigation ids, permission constants, error codes, and enum-like domain values must be represented in a way that survives the configured runtime constraints.

## 19. Architecture Invariants

These invariants define migration gates.

| Invariant | Verification method |
| --- | --- |
| One public service facade per business domain | Inspect `src/services/<domain>/index.ts` exports |
| Hooks call services, never Axios | Search hooks for Axios/API client/imported endpoint usage |
| Components do not call services directly | Search components/routes/layouts/features for service imports |
| Services do not import React or TanStack Query | Search services for React/query imports |
| Services do not define business entities | Search service files for exported entity interfaces/types |
| All query keys come from `QUERY_KEYS` | Search for hardcoded query key arrays outside `queryKeys.ts` |
| Invalidation policy lives in `queryInvalidation.ts` | Search for direct `invalidateQueries` outside allowed framework/helper files |
| Tenant and branch scope participate in cache keys | Inspect query key signatures and invalidation helpers |
| Tenant/branch headers are centralized | Inspect API client/interceptors only |
| Authorization is centralized | Inspect route/menu/component permission checks |
| Navigation ids are unique | Validate navigation registry ids |
| Type packages do not import runtime layers | Search `src/types` imports |
| Runtime constants are compiler-compatible | Run TypeScript diagnostics |
| Provider barrels match consumers | Compare provider imports against provider index exports |
| Workflow hooks invalidate centrally after success | Inspect mutation/workflow hooks |

## 20. Canonical Architecture Decision Tables

### Type Ownership

| Item | Canonical owner |
| --- | --- |
| `Sale`, `Customer`, `Supplier`, `Product`, `InventoryItem` | `src/types/entities` |
| `CreateSaleRequest`, `UpdateSaleRequest`, `RefundSaleRequest` | `src/types/requests` |
| `PaginationRequest` | `src/types/requests` when sent as backend query input |
| `SalesDashboard`, `CashierSummary`, `DailySalesSummary` | `src/types/responses` |
| `ApiResponse`, `ApiError`, `PaginatedResponse`, `PaginationMeta` | `src/types/api` |
| `Money`, `DateRange`, `AuditFields` | `src/types/common` |
| Permission names | `src/types/enums` or authorization constants with type re-export, pending compiler-compatible design |
| Navigation item ids | navigation runtime constants plus type-safe representation, not type modules importing runtime registry |

### Service Ownership

| Concern | Canonical owner |
| --- | --- |
| Sale list/detail/dashboard | `salesService` facade delegating internally |
| Sale completion/suspension/void/refund | `salesService` workflow methods |
| Payment and receipt details | `salesService` facade delegating to payment/receipt internals |
| Product catalog | `productService` |
| Stock movements/counts | `inventoryService` |
| Purchase orders/goods receipts | `procurementService` |
| Users/roles/permissions/branches/tenants | `administrationService` unless ADR clarifies subdomains |
| Auth/session refresh | `authService` and API refresh infrastructure |

### Hook Ownership

| Hook type | Canonical responsibility |
| --- | --- |
| Query hook | Fetch through service facade, consume query keys |
| Mutation hook | One business operation, call service facade, invoke invalidation helper |
| Workflow hook | Coordinate UI-triggered workflow, expose progress/error, invoke service and invalidation |
| Common query hook | Reusable query mechanics only, no business DTO ownership |
| Navigation hook | Read navigation registry and authorization output, no raw permission logic |

### Boundary Decisions

| Decision | Canonical answer |
| --- | --- |
| May hooks import decomposed sales internals? | No |
| May services invalidate TanStack Query cache? | No |
| May query keys omit tenant/branch? | No for authenticated tenant/branch-scoped data |
| May components hardcode role names? | No |
| May type files import navigation registry values? | No |
| May domain events bypass backend confirmation? | No |
| May ADR-008 be assumed to contain boundaries? | No |

## 21. Open Questions and Verification Requirements

Open questions:

- ADR-008 must be restored, rewritten, or explicitly deprecated before module-boundary migration is treated as complete.
- Final query-key root naming needs confirmation where ADR-003 examples and ADR-009 naming language conflict.
- Exact tenant/branch scope object shape for query keys and invalidation needs implementation design.
- Whether administration is one facade or several independent business-domain facades needs ADR clarification.
- Whether Sales owns prescriptions and dashboard projections needs backend/domain confirmation.
- Receipt, payment, refund, and sale workflow response shapes need backend verification.
- Whether sale deletion exists or voiding is the only supported business operation needs backend verification.
- Provider composition for authorization, tenant, and branch context needs one documented implementation decision.
- Whether ADR-010 requires a runtime event bus now needs clarification.
- Permission constant representation must satisfy ADR-007 and TypeScript `erasableSyntaxOnly`.

Verification requirements before first source migration:

- Capture current `git status --short`.
- Capture current TypeScript diagnostic baseline.
- Confirm ADR-008 disposition.
- Confirm backend Sales endpoints and DTO wrappers.
- Confirm tenant/branch header and cache-scope requirements.
- Confirm whether enum-like values will use const objects, unions, or compiler-supported enums.
- Confirm public barrel exports for providers, services, hooks, navigation, and types.

## 22. Implementation Prerequisites

Before source migration begins:

1. Freeze the repository baseline so existing user work is not overwritten.
2. Decide ADR-008 disposition.
3. Define canonical type ownership and barrel export policy.
4. Define compiler-compatible runtime constant strategy for permissions, navigation ids, statuses, and error codes.
5. Verify backend Sales contracts, including list/detail/workflow/payment/receipt/refund/dashboard endpoints and response wrappers.
6. Define tenant/branch query-key scope shape.
7. Define provider composition for auth, tenant, branch, authorization, query, shell, and theme.
8. Define public service facade contracts before changing hooks.
9. Define query invalidation helper names and scopes before changing mutation hooks.
10. Define navigation registry id and permission representation before changing protected routes or menus.

Five most important prerequisites:

- Protect the dirty worktree and keep a reproducible baseline.
- Resolve ADR-008 or mark its scope explicitly deferred.
- Lock canonical type ownership and TypeScript runtime-value strategy.
- Verify backend Sales contracts before reconstructing `salesService`.
- Define tenant/branch-scoped query keys and invalidation before migrating hooks.

## 23. Recommended Migration Dependency Order

| Order | Migration area | Prerequisites | Affected areas | Expected diagnostic reduction | Verification gate |
| --- | --- | --- | --- | --- | --- |
| 1 | Baseline protection | Current status/diff captured | Git working tree only | None directly | No unrelated files changed |
| 2 | ADR-008 disposition | Architecture owner decision | Documentation/ADR set | Prevents boundary rework | ADR-008 restored, rewritten, or explicitly deferred |
| 3 | Canonical type system | Type ownership table approved | `src/types`, type imports | Reduces duplicate/missing type errors | Type barrels export canonical contracts |
| 4 | Runtime constants and errors | TypeScript strategy approved | `src/lib/errors`, navigation ids, permissions, enums | Reduces `erasableSyntaxOnly`, type-as-value errors | TypeScript accepts runtime constants |
| 5 | Base service and facade contracts | Public service table approved | `src/services/base`, domain service barrels | Reduces service import/method mismatch | Facades expose approved method names |
| 6 | Sales facade reconstruction | Backend Sales contract verified | `src/services/sales` | Reduces missing sales method errors | Sales hooks can target one facade contract |
| 7 | Query-key scope model | Tenant/branch scope shape approved | `src/lib/queryKeys.ts` | Reduces query key drift | Authenticated keys include scope |
| 8 | Invalidation policy alignment | Query keys stable | `src/lib/queryInvalidation.ts` | Reduces duplicated/stale invalidation | Business helpers invalidate required domains |
| 9 | Query and mutation hook alignment | Service facades and invalidation stable | `src/hooks/queries`, mutation/workflow hooks | Reduces hook/service mismatch | Hooks call services and helper invalidation only |
| 10 | Authorization foundation | Auth identity and permission model stable | `src/authorization`, auth/provider types | Reduces route/navigation permission drift | `can/canAny/canAll/hasRole` available |
| 11 | Provider and protected-route alignment | Authorization and tenant/branch model stable | `src/providers`, `src/routes` | Reduces missing provider/context exports | App imports provider barrel successfully |
| 12 | Navigation reconstruction | Authorization helpers and runtime id strategy stable | `src/navigation`, navigation hooks | Reduces duplicate id/missing export/type errors | Unique ids and exported helper names verified |
| 13 | Barrel/export normalization | Domains and providers stable | Service/hook/type/provider/navigation barrels | Reduces `TS2305` missing export errors | Consumer imports match public barrels |
| 14 | Strict TypeScript cleanup | Architecture migration complete | Remaining frontend source | Reduces residual diagnostics | TypeScript diagnostic count reaches agreed target |

First source migration blocker:

The first source migration should not begin until ADR-008 disposition, type ownership, runtime constant strategy, backend Sales contracts, and tenant/branch query-scope design are settled. Without those decisions, code changes risk replacing current drift with a different undocumented drift.
