# Hela360 Frontend ADR Compliance Matrix

Generated on 2026-08-03 from repository root `/home/thumbi/Hela360`.

Actual frontend path: `frontend/`. The requested report path is therefore `frontend/docs/architecture/reviews/ADR_COMPLIANCE_MATRIX.md`.

This report uses only these classifications: `Compliant`, `Partially compliant`, `Non-compliant`, `Not implemented`, `Insufficient evidence`.

## Repository State and Evidence Reliability

- Relevant ADR files are present at `frontend/docs/architecture/adr/ADR-001...ADR-010`. Git reports `frontend/docs/architecture/adr/` as untracked, so the ADRs are authoritative for this review but not verifiable as committed history.
- The previous baseline is present at `frontend/docs/architecture/reviews/FRONTEND_ARCHITECTURAL_BASELINE.md` and is also under untracked `frontend/docs/architecture/reviews/`.
- The frontend architecture is heavily present as untracked content: `frontend/src/api/client.ts`, `frontend/src/hooks/`, `frontend/src/lib/`, `frontend/src/navigation/`, `frontend/src/providers/`, `frontend/src/services/`, and most `frontend/src/types/*`.
- Relevant tracked modifications include `frontend/package.json`, `frontend/tsconfig.app.json`, `frontend/vite.config.ts`, `frontend/src/main.tsx`, `frontend/src/routes/ProtectedRoute.tsx`, `frontend/src/store/authStore.ts`, and `frontend/src/types/auth.ts`.
- Relevant tracked deletions include `frontend/src/api/axios.ts` and `frontend/src/app/providers.tsx`.
- Git history cannot reliably identify the canonical implementation because much of the architecture is untracked while older tracked files are modified or deleted. Conclusions below are based on current filesystem content unless explicitly described as Git state.
- Untracked files are not treated as invalid. They are treated as intentional current work with lower history reliability.

## Compliance Summary

| ADR | Title | Status | Classification | Migration risk |
|---|---|---|---|---|
| ADR-001 | Service Layer Architecture Standard | Accepted | Non-compliant | Critical |
| ADR-002 | Query & Mutation Hook Architecture | Accepted | Partially compliant | High |
| ADR-003 | TanStack Query Cache & Invalidation Strategy | Accepted | Partially compliant | High |
| ADR-004 | Type System Organization | Accepted | Non-compliant | Critical |
| ADR-005 | Enterprise Error Handling Strategy | Accepted | Partially compliant | High |
| ADR-006 | Multi-Tenant Architecture | Accepted | Partially compliant | Critical |
| ADR-007 | Authorization & Permission Architecture | Accepted | Partially compliant | High |
| ADR-008 | Frontend Module Boundaries | Accepted file, empty content | Insufficient evidence | High |
| ADR-009 | Enterprise Naming Conventions | Accepted | Partially compliant | High |
| ADR-010 | Domain Event & Workflow Architecture | Accepted | Not implemented | High |

## ADR-001: Service Layer Architecture Standard

- ADR identity: ADR-001, `Service Layer Architecture Standard`, `Accepted`, dependencies: none.
- Architectural intent: every business domain presents a stable business-language service facade, hides HTTP/Axios/URLs/REST, wraps `BaseService`, keeps React/cache/UI concerns out of services, and uses shared types.
- Mandatory rules: domain services SHALL expose one public facade (`ADR-001:43`); the facade SHALL hide HTTP/Axios/URLs/REST/backend details (`ADR-001:57-67`); services SHALL NOT contain React state/hooks/cache invalidation/UI/component logic (`ADR-001:81-87`); methods SHALL be business-oriented (`ADR-001:93`); names such as `checkout`, `post`, `patch`, `payments`, and `receipt` SHALL NOT be public (`ADR-001:159-171`); all domain services SHALL inherit `BaseService` and wrap generic CRUD names with business-specific names (`ADR-001:199-215`); services SHALL NOT define business entities (`ADR-001:246-260`); internal decomposition SHALL preserve the public facade (`ADR-001:410-429`).
- Current compliant implementation: `BaseService` exists at `src/services/base/BaseService.ts:65-832`; most concrete services extend it, e.g. `ProductService` at `src/services/products/productService.ts:162-364`, `CustomerService` at `src/services/customers/customerService.ts:134-268`, `SupplierService` at `src/services/suppliers/supplierService.ts:153-273`, `SalesService` at `src/services/sales/legacySalesService.ts:59-224`.
- Partial compliance: services do not import React hooks or call TanStack invalidation by search; cache invalidation is not present in `src/services/*`. Service folders have domain `index.ts` barrels.
- Concrete violations: `AuthService` does not extend `BaseService` and imports `apiClient` directly at `src/services/auth/authService.ts:25-183`; services expose generic/ineligible public names such as `checkout`, `complete`, `void`, `payments`, `receipt` at `src/services/sales/legacySalesService.ts:73-152`, `post`/`void` at `src/services/finance/invoiceService.ts:159-181`, and `post` at `src/services/procurement/goodsReceiptService.ts:167`; `BaseService` generic CRUD methods leak to hook consumers through `productService.paginate`, `customerService.paginate`, and `purchaseOrderService.list`; many services define business entities locally; the sales decomposition is public but empty/stubbed.
- Evidence: sales barrel exports empty decomposition instances at `src/services/sales/index.ts:18-24` and exports `salesService` from the legacy layer at `src/services/sales/index.ts:38`; empty decomposed files have 0 lines: `paymentService.ts`, `receiptService.ts`, `salesDashboardService.ts`, `salesQueryService.ts`, `salesWorkflowService.ts`; compiler examples include TS2305 for missing `salesQueryService`, `salesWorkflowService`, `paymentService`, `receiptService`, `salesDashboardService`, and TS2339/TS2551 for absent sales facade methods.
- Architectural consequence: consumers cannot depend on a stable business facade; internal decomposition leaks through barrels; hook/service contracts split between ADR target names and current generic/legacy names.
- Required migration: establish one facade per domain that wraps `BaseService` and any internal decomposition behind business methods; move business entities/DTOs out of services; decide whether `salesService` is canonical or legacy and align exports/consumers accordingly.
- Dependencies on other migrations: ADR-004 type ownership, ADR-009 naming, ADR-002 hook contracts, ADR-003 invalidation, ADR-010 workflows.
- Migration risk: Critical.
- Verification criteria: consumers import one domain facade per domain; public service methods use names such as `listSales`, `getSale`, `completeSale`; no services define business entities; no service imports React/TanStack invalidation; decomposition files are internal behind the facade.

## ADR-002: Query & Mutation Hook Architecture

- ADR identity: ADR-002, `Query & Mutation Hook Architecture`, `Accepted`, dependencies: ADR-001.
- Architectural intent: query hooks retrieve data, mutation hooks change data, each domain owns hooks, hooks are thin service callers with cache invalidation delegated to the framework.
- Mandatory rules: hooks SHALL be divided into query and mutation hooks (`ADR-002:31-41`); each domain owns its hooks (`ADR-002:45-70`); query hooks SHALL never mutate (`ADR-002:97`); mutation hooks SHALL expose one business operation (`ADR-002:103-131`); hooks SHALL invoke services and expose query states, but SHALL NOT call Axios, build URLs, contain business logic, or manipulate DTOs (`ADR-002:137-150`); hooks SHALL communicate exclusively with services (`ADR-002:156-178`); mutation hooks SHALL use `queryInvalidation.ts` and SHALL NOT directly call `queryClient.invalidateQueries` (`ADR-002:182-206`); hooks SHALL NOT communicate across domains (`ADR-002:254-260`).
- Current compliant implementation: hook domains exist under `src/hooks/queries/{auth,common,customers,dashboard,inventory,procurement,products,sales,suppliers}`; mutation hooks generally map one operation, e.g. `useCompleteSale` at `src/hooks/queries/sales/useCompleteSale.ts:58-75`, `useReceiveStock` at `src/hooks/queries/inventory/useReceiveStock.ts:54-73`, `useApprovePurchaseOrder` at `src/hooks/queries/procurement/useApprovePurchaseOrder.ts:53-72`; no hook imports Axios or `apiClient`; no hook directly calls `queryClient.invalidateQueries`.
- Partial compliance: hooks call services and invalidation helpers, but several call service methods that do not exist; `finance`, `reports`, and `administration` hook barrels exist but are empty.
- Concrete violations: inventory hooks import `inventoryService` from `@/services/products` (`src/hooks/queries/inventory/useReceiveStock.ts:35-36`, `useInventory.ts:36-37`), which is a domain-boundary ambiguity; hooks import store state directly for auth/navigation (`src/hooks/queries/auth/useLogin.ts:36`, `src/hooks/useNavigation.ts:11`); some hook barrels contain duplicate implementation/export content (`src/hooks/queries/suppliers/index.ts:28-81`); hooks depend on missing common type exports (`UseEntityOptions`) even though `useEntity.ts` defines it.
- Evidence: representative compiler diagnostics include TS2305 for empty `@/services/auth` barrel, TS2339 for `productService.findById`, `salesService.completeSale`, `inventoryService.receiveStock`, and TS2554 for query-key parameter mismatches.
- Architectural consequence: hook naming mostly follows ADR, but hook behavior cannot be verified at compile time because service/barrel contracts are unstable.
- Required migration: align hook calls with domain service facades, keep query/mutation separation, remove cross-domain service ownership ambiguity, and ensure mutation hooks only call centralized invalidation helpers.
- Dependencies on other migrations: ADR-001 facade stabilization, ADR-003 key/invalidation contract, ADR-004 exported DTOs, ADR-008 boundary rules once available.
- Migration risk: High.
- Verification criteria: every hook compiles against its domain facade, no hook imports Axios/API endpoints, mutation hooks have one operation and one framework invalidation call, and hook barrels only export hook modules.

## ADR-003: TanStack Query Cache & Invalidation Strategy

- ADR identity: ADR-003, `TanStack Query Cache & Invalidation Strategy`, `Accepted`, dependencies: ADR-001 and ADR-002.
- Architectural intent: all query keys come from one registry, invalidation policy is centralized, mutation hooks invoke business invalidation helpers, and multi-domain workflows refresh all affected domains.
- Mandatory rules: cache invalidation SHALL be centralized (`ADR-003:63`); mutation hooks SHALL never decide query keys to invalidate and SHALL call helpers (`ADR-003:65-77`); every cache key SHALL originate from `src/lib/queryKeys.ts`; hardcoded keys are prohibited (`ADR-003:81-101`); all invalidation SHALL occur through `src/lib/queryInvalidation.ts` (`ADR-003:105-119`); services, hooks, and components SHALL NOT define invalidation policy (`ADR-003:231-245`); root/list/detail key hierarchy is required conceptually (`ADR-003:197-227`).
- Current compliant implementation: `src/lib/queryKeys.ts:15-249` defines central `QUERY_KEYS`; `src/lib/queryInvalidation.ts:33-379` centralizes invalidation; mutation hooks call helpers such as `invalidateSalesOperations` in `src/hooks/queries/sales/useCompleteSale.ts:69-72` and `invalidateProcurementOperations` in `src/hooks/queries/procurement/useApprovePurchaseOrder.ts:65-68`.
- Partial compliance: all observed hook query keys use `QUERY_KEYS`; direct `queryClient.invalidateQueries` appears only inside `queryInvalidation.ts:44` and `queryInvalidation.ts:379`.
- Concrete violations: list keys do not accept filters/pagination, but hooks pass params to them (`src/hooks/queries/products/useProducts.ts:62`, `customers/useCustomers.ts:63`, `suppliers/useSuppliers.ts:66`, `inventory/useInventory.ts:66`, `procurement/usePurchaseOrders.ts:56`); hooks reference nonexistent key functions (`QUERY_KEYS.sales.sales` at `src/hooks/queries/sales/useSales.ts:66`, `QUERY_KEYS.sales.sale` at `src/hooks/queries/sales/useSale.ts:65`, `QUERY_KEYS.procurement.dashboard` at `src/hooks/queries/procurement/useProcurementDashboard.ts:51`); query keys do not encode tenant/branch context required by ADR-006.
- Evidence: `src/lib/queryKeys.ts:143-173` exposes `sales.list()` and `sales.detail(id)`, not `sales.sales()` or `sales.sale(id)`; `src/lib/queryKeys.ts:122-134` exposes only purchase-order/goods-receipt procurement keys; compiler includes TS2339 and TS2554 around these key mismatches.
- Architectural consequence: cache identity is centralized but not complete; filter/pagination collisions and cross-tenant/branch reuse are possible architectural risks.
- Required migration: define canonical key signatures for root/list/detail/filter/pagination/tenant/branch contexts and update hooks to use only existing registry functions; keep invalidation policy inside `queryInvalidation.ts`.
- Dependencies on other migrations: ADR-006 tenant/branch context, ADR-002 hook alignment, ADR-001 service operations.
- Migration risk: High.
- Verification criteria: all hook key calls compile; list keys include canonical params where required; tenant/branch-scoped data cannot share keys across contexts; invalidation remains centralized.

## ADR-004: Type System Organization

- ADR identity: ADR-004, `Type System Organization`, `Accepted`, dependencies: ADR-001, ADR-002, ADR-003.
- Architectural intent: all reusable and business types have one owner under `src/types`, with entities, requests, responses, enums, API wrappers, and common types separated by responsibility.
- Mandatory rules: all reusable types SHALL live under `src/types` (`ADR-004:43-49`); canonical directories SHALL include `entities`, `requests`, `responses`, `enums`, `api`, `common`, `index.ts` (`ADR-004:53-71`); entities SHALL live in `src/types/entities` (`ADR-004:75-111`); requests in `src/types/requests` (`ADR-004:115-137`); responses in `src/types/responses` (`ADR-004:141-163`); business enums in `src/types/enums` (`ADR-004:167-191`); API wrappers in `src/types/api` (`ADR-004:195-216`); each type has a single owner (`ADR-004:248-263`); types SHALL NOT import services/hooks/components (`ADR-004:266-290`); services SHALL consume shared types, not define entities (`ADR-004:334-355`).
- Current compliant implementation: `src/types/entities/sale.ts`, `sale-item.ts`, `sale-payment.ts`; `src/types/requests/create-sale*.ts`; `src/types/responses/daily-sales-summary.ts`, `cashier-summary.ts`; `src/types/enums/payment-method.ts`, `sale-status.ts`; public root barrel at `src/types/index.ts:19-22`.
- Partial compliance: some sale types are centrally owned; `src/types/auth.ts` owns identity-related state currently used by `src/store/authStore.ts:26`.
- Concrete violations: `src/types/api.ts`, `src/types/pagination.ts`, and `src/types/response.ts` are files, not the ADR's `src/types/api/` and `src/types/common/` directories; `src/types/common/` does not exist; many entity/request/response files are empty placeholders; many business types remain inside services; `src/types/navigation.ts` imports from runtime navigation modules (`src/types/navigation.ts:3-4`), violating type import direction; auth DTOs are duplicated between `src/types/auth.ts` and `src/types/requests/auth.ts`/`src/types/responses/auth.ts`; response path singular/plural inconsistency exists between `src/types/response.ts` and `src/types/responses/`.
- Canonical ownership findings: `Sale` and `SalePayment` have current canonical files under `src/types/entities`; `Product`, `Supplier`, `SalesReceipt`/`Receipt`, `SaleRefund`, many procurement/inventory/customer/admin entities are currently service-local or missing from `src/types/entities`; `PaginationRequest` exists in `src/types/pagination.ts`, while hooks import it from `@/types/requests`; `PaginatedResponse` exists in `src/types/pagination.ts`, while hooks import it from `@/types/response`; authentication DTO ownership is unresolved between `src/types/auth.ts`, `requests/auth.ts`, and `responses/auth.ts`.
- Evidence: service-local `Product` at `src/services/products/productService.ts:41-101`; `Supplier` at `src/services/suppliers/supplierService.ts:38-98`; `Customer` at `src/services/customers/customerService.ts:43-91`; `Refund` at `src/services/sales/refundService.ts:70-114`; empty canonical files include `src/types/entities/branch.ts`, `permission.ts`, `role.ts`, `tenant.ts`, `user.ts`; compiler has many TS2305 missing type exports from `@/types/entities`, `@/types/requests`, `@/types/responses`, and `@/types/response`.
- Architectural consequence: type imports cannot express domain ownership reliably; service facades and hooks compile against different imagined type surfaces.
- Required migration: establish single type owners under the ADR hierarchy, move reusable business types out of services, create API/common directories or record an ADR amendment, and normalize singular/plural response paths.
- Dependencies on other migrations: ADR-001 service cleanup, ADR-002 hook DTO contracts, ADR-005 error model, ADR-007 authorization context.
- Migration risk: Critical.
- Verification criteria: every reusable business/API/common type has one owner; barrels export intended public types; services/hooks/components import rather than redefine; no `src/types/*` import runtime layers.

## ADR-005: Enterprise Error Handling Strategy

- ADR identity: ADR-005, `Enterprise Error Handling Strategy`, `Accepted`, dependencies: ADR-001 through ADR-004.
- Architectural intent: normalize infrastructure, transport, business, and presentation errors into a common model; services propagate normalized errors; components own display.
- Mandatory rules: errors SHALL be categorized into four layers (`ADR-005:42-49`); services SHALL normalize HTTP/API errors and hooks/components SHALL NOT interpret raw status codes (`ADR-005:103-106`); services SHALL expose a common error shape (`ADR-005:151-176`); validation errors SHALL preserve fields (`ADR-005:180-196`); auth failures SHALL clear session and redirect without component duplication (`ADR-005:200-212`); authorization decisions belong to the authorization layer (`ADR-005:216-223`); mutation hooks SHALL propagate normalized errors without presentation transformation (`ADR-005:226-239`); unexpected errors SHALL use centralized logging (`ADR-005:260-271`).
- Current compliant implementation: `src/lib/errors.ts:33-187` defines `ERROR_CODES`, `ErrorCode`, `AppError`, typed subclasses, and `createAppError`; tenant/branch errors exist as `TenantError` and `BranchError` at `src/lib/errors.ts:135-137`; `src/api/interceptors.ts:159-178` handles 401 refresh/invalidation; `src/api/refresh.ts:117-121` clears storage and auth store on invalid session; validation shape exists in `src/types/api.ts:60-102`.
- Partial compliance: the interceptor layer is the intended normalization point, and hooks do not transform errors for UI in inspected mutation hooks.
- Concrete violations: `ErrorCode` is a type alias, but `createAppError` uses `ErrorCode.NETWORK` etc. as runtime values at `src/lib/errors.ts:151-181`; `AppError.fromAxios` is called at `src/api/interceptors.ts:187` but no such static method exists on `AppError`; the declared `AppError` class has `code`, `status`, `details`, `validationErrors`, but lacks ADR fields `category` and `retryable`; services do not visibly normalize errors themselves; centralized logging service is absent.
- Evidence: compiler diagnostics include TS2693 for `ErrorCode` used as a value in `src/lib/errors.ts:151-181` and TS2339 for `AppError.fromAxios` in `src/api/interceptors.ts:187`.
- Architectural consequence: transport-error normalization is designed but currently nonfunctional at compile time; normalized error propagation cannot be guaranteed.
- Required migration: define a runtime error-code contract, implement transport normalization into the ADR model, ensure validation details survive, and introduce or explicitly defer centralized logging.
- Dependencies on other migrations: ADR-004 API error type ownership, ADR-006 auth/tenant/branch context, ADR-007 authorization layer.
- Migration risk: High.
- Verification criteria: `AppError` exposes `code`, `message`, `category`, `details`, `retryable`; Axios errors are normalized once; auth failures clear session; hooks expose normalized errors without presentation mapping; no TS type/value conflicts.

## ADR-006: Multi-Tenant Architecture

- ADR identity: ADR-006, `Multi-Tenant Architecture`, `Accepted`, dependencies: ADR-001 through ADR-005.
- Architectural intent: tenant and branch context are established after authentication, propagated centrally to requests, isolated in cache/storage/navigation, and refreshed on changes.
- Mandatory rules: frontend SHALL be tenant-aware at every layer (`ADR-006:47-50`); authenticated session SHALL expose tenant context (`ADR-006:54-83`); successful auth SHALL establish user, tenant, active branch, permissions, roles (`ADR-006:86-97`); every authenticated request SHALL include tenant context via centralized API layer, not services/components (`ADR-006:100-108`); branch changes SHALL refresh branch-scoped data (`ADR-006:112-128`); tenant-scoped data SHALL be cache-isolated (`ADR-006:132-155`); services SHALL remain tenant-agnostic (`ADR-006:159-169`); hooks SHALL obtain tenant/branch context from providers/state and SHALL NOT hardcode tenant IDs (`ADR-006:173-179`); cross-tenant cache/navigation/local persistence/optimistic updates shall be prevented (`ADR-006:195-204`).
- Current compliant implementation: `Identity` includes `tenantId`, `tenantName`, `branchId`, `branchName`, `roles`, and `permissions` at `src/types/auth.ts:18-57`; `authStore` stores identity/tokens at `src/store/authStore.ts:33-211`; request interceptors attach `X-Tenant-ID` and `X-Branch-ID` from storage at `src/api/interceptors.ts:47-110`; `storage.clearSession()` clears tenant and branch IDs at `src/lib/storage.ts:309-319`; services generally do not store tenant state.
- Partial compliance: request context is centralized in the API interceptor; branch context has a shell hook and store (`src/hooks/useCurrentBranch.ts:83-121`, `src/store/shellStore.ts:27`, `166-169`).
- Concrete violations: query keys do not include tenant or branch context (`src/lib/queryKeys.ts:15-249`); branch switching only updates shell store and does not invalidate branch-scoped caches (`src/hooks/useCurrentBranch.ts:73-80`, `src/store/shellStore.ts:166-169`); login/hydrate in `authStore` does not persist tenant/branch IDs to storage, while interceptors read tenant/branch from storage; no evidence of cross-tenant navigation state partitioning or tenant-scoped local persistence beyond session clearing.
- Evidence: `storage` has tenant/branch getters/setters (`src/lib/storage.ts:235-280`) but `authStore.login` only sets in-memory identity/tokens (`src/store/authStore.ts:153-164`); `QUERY_KEYS` root namespaces begin with domains, not tenant/branch (`src/lib/queryKeys.ts:22`, `37`, `56`, `143`).
- Architectural consequence: request headers may work only if storage is separately populated; cache reuse across tenant/branch contexts remains possible.
- Required migration: define tenant/branch context ownership, persist/synchronize it during auth and branch changes, include context in cache identity or invalidation lifecycle, and verify all branch switches refresh affected data.
- Dependencies on other migrations: ADR-003 query keys, ADR-007 authorization context, ADR-005 auth failure handling.
- Migration risk: Critical.
- Verification criteria: auth establishes tenant/branch in state and request context; all scoped keys include or are invalidated on tenant/branch change; branch switch triggers affected invalidation; local persisted scoped data is partitioned or cleared.

## ADR-007: Authorization & Permission Architecture

- ADR identity: ADR-007, `Authorization & Permission Architecture`, `Accepted`, dependencies: ADR-001 through ADR-006.
- Architectural intent: backend-originated RBAC/permissions are consumed by a frontend authorization context/service for route protection, navigation filtering, feature visibility, and action enablement.
- Mandatory rules: implement RBAC with explicit permissions (`ADR-007:38-41`); frontend SHALL expose centralized Authorization Context (`ADR-007:121-143`); frontend SHALL expose Authorization Service with `can`, `canAny`, `canAll`, role helpers (`ADR-007:147-166`); protected routes SHALL declare authorization requirements (`ADR-007:170-184`); menus SHALL be permission-aware (`ADR-007:188-209`); components SHALL rely on authorization helpers and not hardcode role checks (`ADR-007:213-237`); hooks SHALL NOT implement authorization (`ADR-007:241-248`); services SHALL NOT enforce frontend authorization (`ADR-007:251-257`); authorization changes SHALL invalidate current user, permissions, navigation, dashboard, feature config (`ADR-007:271-281`).
- Current compliant implementation: `Identity` carries roles/permissions (`src/types/auth.ts:54-56`); `PERMISSIONS` registry exists at `src/navigation/permissions.ts:18-145`; navigation items declare permission strings (`src/navigation/navigation.ts:33-250`); `filterNavigationByPermissions` filters items against a permission set (`src/navigation/helpers.ts:102-138`); `invalidateAuthentication` includes current user/profile/permissions (`src/lib/queryInvalidation.ts:66-76`).
- Partial compliance: navigation is conceptually permission-aware, but current `useNavigation` imports missing helper names and passes an array to functions expected to receive a `ReadonlySet`.
- Concrete violations: `src/authorization/index.ts` is empty; no `AuthorizationContext` or authorization service (`can`, `canAny`, `canAll`, `hasRole`) exists; `ProtectedRoute` only checks authentication and has no permission declaration (`src/routes/ProtectedRoute.tsx:42-110`); route registry `src/routes/routes.ts` carries paths only, no authorization requirements; `useNavigation` implements permission filtering in a hook and imports nonexistent `filterNavigation`/`filterNavigationSection` (`src/hooks/useNavigation.ts:4-9`, `100-136`); compiler reports `auth` as `unknown` in `ProtectedRoute`.
- Evidence: ADR service requirement has no implementation in `src/authorization/index.ts` (0 lines); navigation barrel exports `filterNavigationByPermissions`, not `filterNavigation` (`src/navigation/index.ts:25-34`); compiler includes TS2724 for missing navigation helpers and TS18046 for unknown auth state.
- Architectural consequence: authorization is represented as raw identity data and navigation filtering, not as a centralized authorization layer; route/feature-level enforcement is incomplete.
- Required migration: introduce an authorization context/service contract, route authorization metadata, navigation filtering through authorization helpers, and invalidation support for authorization changes.
- Dependencies on other migrations: ADR-006 tenant context, ADR-004 authorization types, ADR-003 invalidation, provider/barrel stabilization.
- Migration risk: High.
- Verification criteria: `authorizationService.can(...)` and context are available; protected routes declare required permissions; navigation filters through the authorization layer; hooks/services do not evaluate permissions directly.

## ADR-008: Frontend Module Boundaries

- ADR identity: ADR-008, file `ADR-008-frontend-module-boundaries.md`, status cannot be read from content because the file is zero bytes; dependencies: insufficient evidence.
- Architectural intent: insufficient evidence from the authoritative ADR. The user requested boundary verification, but the ADR contains no accepted rules to apply.
- Mandatory rules: none can be extracted without inventing them.
- Current compliant implementation: insufficient evidence.
- Partial compliance: public barrels exist for many modules (`src/navigation/index.ts`, `src/services/*/index.ts`, `src/hooks/queries/*/index.ts`, `src/types/*/index.ts`), but without ADR-008 content this cannot be classified as compliance.
- Concrete violations: none classified against ADR-008 because mandatory rules are absent.
- Evidence: `docs/architecture/adr/ADR-008-frontend-module-boundaries.md` has 0 lines and 0 bytes.
- Architectural consequence: module-boundary decisions cannot be audited authoritatively. Observed open questions include whether hooks may import stores, whether `src/types/navigation.ts` may import `src/navigation`, whether inventory belongs under products, and which barrels define public contracts.
- Required migration: restore or authoritatively provide ADR-008 content before enforcing module-boundary rules.
- Dependencies on other migrations: all boundary-sensitive migrations should wait for ADR-008 or a replacement decision.
- Migration risk: High.
- Verification criteria: ADR-008 text is present and accepted; dependency-direction and public-entry-point rules can be applied mechanically.

## ADR-009: Enterprise Naming Conventions

- ADR identity: ADR-009, `Enterprise Naming Conventions`, `Accepted`, dependencies: ADR-001 through ADR-008.
- Architectural intent: consistent business terminology across services, hooks, files, folders, types, DTOs, enums, query keys, endpoints, constants, and imports.
- Mandatory rules: names SHALL prioritize clarity and business terminology (`ADR-009:41-45`); services and service classes SHALL end with `Service` (`ADR-009:114-136`); entity types SHALL be singular, request DTOs end in `Request`, responses describe returned business concept (`ADR-009:140-172`); business files and directories SHALL use kebab-case unless framework conventions override (`ADR-009:196-219`); query key roots SHALL be singular and nested keys describe resources/views (`ADR-009:235-261`); avoid literal URLs throughout code (`ADR-009:265-279`); constants intended as immutable application constants use UPPER_SNAKE_CASE (`ADR-009:302-314`); function names SHALL describe actions (`ADR-009:348-374`).
- Current compliant implementation: hook names largely follow `useX`/business-operation style (`useCompleteSale`, `useReceiveStock`, `useApprovePurchaseOrder`); service classes/instances end with `Service`; request DTOs generally end with `Request`; `API_ENDPOINTS` centralizes endpoint constants.
- Partial compliance: many current names align with examples, but ADR-001/ADR-009 target business method names are not consistently implemented.
- Concrete violations: current service public methods expose `get` vs expected `getProduct/getSale`, `list`/`paginate` vs `listSales`, `complete` vs `completeSale`, `receipt` vs `getReceipt`, `payments` vs `listSalePayments`; `src/types/response.ts` conflicts with `src/types/responses/`; `Receipt`/`SalesReceipt` ownership is unresolved; `QUERY_KEYS` roots use plural `products`, `customers`, `suppliers`, whereas ADR-009 says roots SHALL be singular and even gives `customer.root`; many business files use camelCase (`productService.ts`, `queryInvalidation.ts`, `queryKeys.ts`) while ADR examples prefer kebab-case unless framework conventions require otherwise.
- Evidence: `src/services/sales/legacySalesService.ts:73-152`; `src/lib/queryKeys.ts:56`, `73`, `87`; `src/hooks/queries/sales/useSales.ts:66-71`; `src/types/response.ts` and `src/types/responses/index.ts`.
- Architectural consequence: name drift obscures whether code is targeting ADR language, legacy compatibility, or generic `BaseService` language.
- Required migration: choose ADR names as public contracts, reserve generic names inside `BaseService`, normalize response and receipt terminology after backend/domain verification, and either align file/query-key naming or record ADR amendments.
- Dependencies on other migrations: ADR-001 facades, ADR-004 type ownership, ADR-003 query keys, ADR-008 boundary rules.
- Migration risk: High.
- Verification criteria: public methods match business terminology; DTO/entity/response names have one owner; query key roots/nested names match ADR or documented amended ADR; no unresolved `Receipt`/`SalesReceipt` ambiguity remains.

## ADR-010: Domain Event & Workflow Architecture

- ADR identity: ADR-010, `Domain Event & Workflow Architecture`, `Accepted`, dependencies: ADR-001 through ADR-009.
- Architectural intent: model business operations as workflows, use command/event business language, invoke services, trigger centralized invalidation, expose progress/error state, and avoid frontend business rules.
- Mandatory rules: frontend SHALL model business operations as workflows (`ADR-010:46-51`); workflows SHALL represent one outcome, invoke services, trigger cache invalidation, expose progress/errors, and remain idempotent where practical (`ADR-010:55-64`); domain events are past-tense business facts (`ADR-010:67-92`); commands express intent and backend validates/executes them (`ADR-010:95-116`); workflow completion SHALL invoke centralized invalidation and not duplicate invalidation logic (`ADR-010:195-209`); long-running workflows SHALL expose progress and support polling/future push (`ADR-010:213-225`); workflow errors use ADR-005 model (`ADR-010:229-235`); UI initiates workflows but SHALL NOT implement business rules (`ADR-010:239-248`); workflow hooks and services use matching business methods (`ADR-010:252-269`).
- Current compliant implementation: some mutation hooks are named as workflow hooks and call centralized invalidation, e.g. `useCompleteSale` (`src/hooks/queries/sales/useCompleteSale.ts:58-72`), `useReceiveStock`, and `useApprovePurchaseOrder`.
- Partial compliance: mutation hooks expose TanStack loading/error/success state by returning `useMutation`, but compile-time contract drift prevents confirming working workflows.
- Concrete violations: no domain-event implementation exists by search (`DomainEvent`, `EventBus`, `publish`, `subscribe`, `SaleCompleted`, etc. absent under `src`); `salesWorkflowService.ts` is empty; workflow hooks call missing matching business service methods (`salesService.completeSale`, `inventoryService.receiveStock`, `purchaseOrderService.receive`); workflow error normalization depends on incomplete ADR-005 implementation.
- Evidence: `src/services/sales/salesWorkflowService.ts` has 0 lines; ADR event names only appear in docs and hook comments, not implementation; compiler representative diagnostics include TS2339 for missing workflow service methods and TS2305 for missing request/entity types used by workflow hooks.
- Architectural consequence: workflow naming is present at the hook layer, but no complete workflow/event architecture exists.
- Required migration: define workflow ownership, implement matching service methods/facades, decide whether event publication/consumption is required now or intentionally deferred, and connect workflow completion to centralized invalidation.
- Dependencies on other migrations: ADR-001 service facades, ADR-002 hooks, ADR-003 invalidation, ADR-004 command/event/request types, ADR-005 errors.
- Migration risk: High.
- Verification criteria: each business workflow has a hook and matching service method, uses centralized invalidation, exposes progress/errors, avoids UI business rules, and domain-event implementation or documented deferral exists.

## Cross-ADR Architectural Breakpoints

| Breakpoint | Affected ADRs | Evidence | Dependent modules | Compiler categories | Prerequisites | Impact | Dependency order |
|---|---|---|---|---|---|---|---|
| Canonical type-system ownership | 001, 004, 005, 006, 007, 009, 010 | service-local entities; incomplete `src/types` barrels; `response` vs `responses` | services, hooks, stores, errors | TS2305, TS2724 | decide type owners and barrels | Critical | 1 |
| Service facade drift | 001, 002, 009, 010 | `BaseService` generic names and missing business wrappers | all domain hooks/services | TS2339, TS2551 | type owners first | Critical | 2 |
| Sales facade decomposition | 001, 002, 009, 010 | empty decomposed sales files; legacy export | sales hooks/services | TS2305, TS2339 | service facade contract | Critical | 3 |
| Hook/service contract drift | 001, 002, 009, 010 | hooks call absent methods | hooks/services | TS2339, TS2551 | facade contract | High | 4 |
| Query-key drift | 003, 006, 009 | nonexistent keys and no tenant/branch context | query hooks, invalidation | TS2339, TS2554 | tenant/branch cache strategy | High | 5 |
| Invalidation drift | 002, 003, 006, 007, 010 | broad helpers exist, branch/authorization refresh incomplete | hooks, queryInvalidation | TS2554 plus behavioral gaps | key strategy | High | 6 |
| Provider/context drift | 006, 007, 008 | empty provider barrel, private context import, unknown auth state | providers, routes, hooks | TS2305, TS18046 | context ownership | High | 7 |
| Navigation architecture drift | 006, 007, 008, 009 | raw enum strings, duplicate `warehouses`, missing filtering exports | navigation, layout, auth | TS2322, TS2724, TS1294 | authorization service/context | High | 8 |
| Barrel/public export drift | 001, 002, 004, 008, 009 | empty/stale/duplicate barrels | services, hooks, types, providers | TS2300, TS2305, TS2614 | owner contracts | High | 9 |
| TypeScript strictness migration | 004, 009 | `erasableSyntaxOnly`, `verbatimModuleSyntax`, unused locals | navigation, lib, UI | TS1294, TS1484, TS6133 | naming/type strategy | Medium | 10 |
| Repository tracking uncertainty | all | architecture mostly untracked | all reviewed files | not a compiler category | establish canonical source control state | High | 0 |

## Compiler Traceability

Exact baseline from the prior build in `FRONTEND_ARCHITECTURAL_BASELINE.md:242-269`: `npm run build` failed during `tsc -b` with exactly 294 `error TS` diagnostics. Exact error-code counts were mechanically counted there: TS2305 109, TS2339 41, TS2322 40, TS2724 14, TS2614 14, TS2693 11, TS2554 11, TS6133 10, TS2307 9, TS7006 7, TS2551 6, TS2300 6, TS1294 3, TS2686 2, TS2349 2, TS2323 2, TS18046 2, and five singleton codes.

Estimated architectural category counts from the baseline are estimates, not mechanically exact: type ownership 83, service facade 31, hook/service contract 49, query keys 11, invalidation 3, navigation 39, providers/routes 8, barrel exports 22, error handling 12, TypeScript strictness 22, isolated implementation defects 14.

Representative diagnostics:

- Type ownership: missing `Customer`, `Product`, `Supplier`, `PaginationRequest`, `PaginatedResponse`, auth DTO exports from `@/types/*`.
- Service facade: missing `authService` export, empty sales decomposition exports, absent `salesService.completeSale`.
- Query keys: absent `QUERY_KEYS.sales.sales`, `QUERY_KEYS.sales.sale`, `QUERY_KEYS.procurement.dashboard`.
- Navigation: raw strings incompatible with enum-typed IDs and `erasableSyntaxOnly` enum diagnostics.
- Error handling: `AppError.fromAxios` missing and `ErrorCode` type/value conflict.

## Ten Highest-Impact Confirmed Violations

1. Business types are still defined in services despite ADR-004 and ADR-001 requiring shared type ownership.
2. The exported sales facade is explicitly a legacy compatibility layer, while decomposed sales services are empty.
3. Hooks call business methods that domain services do not implement.
4. Auth service barrel is empty while auth hooks import `authService` from it.
5. Query keys omit tenant/branch context, so ADR-006 cache isolation is not satisfied.
6. Query hooks call nonexistent or incorrectly parameterized query-key factories.
7. Authorization service/context is absent even though route and navigation decisions require it.
8. Error normalization cannot compile because `AppError.fromAxios` does not exist and `ErrorCode` is used as a value.
9. Provider public export/context contracts are mismatched, including empty `src/providers/index.ts` and private `ApplicationContext`.
10. ADR-008 is empty, leaving module-boundary enforcement without authoritative rules.

## Recommended Migration Dependency Order

1. Establish repository/source-control baseline for current architecture files without deleting or restoring user work.
2. Restore or authoritatively define ADR-008 module-boundary rules.
3. Stabilize canonical type ownership and type barrels.
4. Stabilize API/error/auth tenant context types.
5. Define service facade contracts per domain, beginning with sales.
6. Align hooks to facades and remove generic/legacy method assumptions.
7. Redesign query keys for filters/pagination and tenant/branch isolation.
8. Verify invalidation helpers against business operations, tenant/branch switches, and authorization refresh.
9. Introduce authorization context/service and route metadata.
10. Implement or explicitly defer domain-event infrastructure, then complete workflow services.

## Evidence Gaps

- ADR-008 content is absent.
- Backend permission catalogue, route authorization requirements, and tenant/branch header contract are not locally authoritative.
- Backend API response/request DTOs are not verified against implementation.
- No tests were inspected or run for behavioral tenant/cache/authorization isolation.
- It is unclear whether empty service/type files are intentional scaffolds or interrupted migration artifacts.

## Backend Contracts Requiring Later Verification

- Auth login/current-user/refresh response shape and identity fields.
- Tenant/branch propagation mechanism and exact header names.
- Permission naming catalogue and route-level access rules.
- Sales receipt terminology: `SalesReceipt`, `Receipt`, or binary receipt response.
- Refund, payment, procurement, inventory, and dashboard DTO shapes.
- Workflow command/event names and whether frontend should publish/consume events now.

## Items That Must Remain Untouched Until Ownership Is Established

- Untracked ADR and architecture-review documentation.
- Empty but intentional-looking service/type scaffolds.
- Tracked deletions such as `frontend/src/api/axios.ts` and `frontend/src/app/providers.tsx`.
- Modified TypeScript/Vite/package configuration.
- Existing route/provider/auth store modifications.
- Any untracked `frontend/src/*` architecture directories until canonical ownership is confirmed.
