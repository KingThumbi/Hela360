# Hela360 Frontend Architectural Baseline

Generated on 2026-08-03 from repository root `/home/thumbi/Hela360`.

This is an evidence-only architectural baseline. It does not recommend fixes and does not modify source.

## 1. Repository and Toolchain Baseline

- Actual frontend path: `frontend/`; the working directory was the monorepo root, not `frontend/`.
- Package manager: npm, evidenced by `frontend/package-lock.json`.
- Type-check/build command: `npm run build`, which runs `tsc -b && vite build` from `frontend/package.json`.
- React: `^19.2.7` in `frontend/package.json`.
- TypeScript: `~6.0.2` in `frontend/package.json`.
- Vite: `^8.1.1` in `frontend/package.json`.
- TanStack Query: `@tanstack/react-query ^5.101.2` and devtools `^5.101.2` in `frontend/package.json`.
- Path alias: `@/* -> src/*` in `frontend/tsconfig.app.json`; `frontend/vite.config.ts` enables `resolve.tsconfigPaths: true`.
- Strict TypeScript options explicitly enabled in `frontend/tsconfig.app.json`: `noUnusedLocals`, `noUnusedParameters`, `erasableSyntaxOnly`, `noFallthroughCasesInSwitch`, `verbatimModuleSyntax`, `moduleDetection: "force"`, `allowImportingTsExtensions`, `allowArbitraryExtensions`, `noEmit`.
- Strict options not explicitly enabled: `strict`, `noImplicitAny`, `strictNullChecks`, `exactOptionalPropertyTypes`, `noUncheckedIndexedAccess`.

## 2. Current Top-Level Frontend Structure

- `src/api`: Axios client, interceptors, refresh flow, endpoint registry.
- `src/app`: application shell entry/router files; `src/app/router.tsx` imports feature pages.
- `src/components`: layout, navigation, page, datatable, feedback, form, table, and UI components.
- `src/features`: page-level feature areas for administration, auth, customers, dashboard, finance, inventory, procurement, products, reports, sales, settings.
- `src/hooks`: shell hooks and TanStack Query hooks under `src/hooks/queries`.
- `src/lib`: query client/factory/keys/invalidation, storage, errors, utils.
- `src/navigation`: navigation registry, section registry, permissions, helpers, public barrel.
- `src/providers`: App, Application, Auth, Query, Shell, Theme providers; public barrel is empty.
- `src/routes`: route constants and protected route.
- `src/services`: BaseService plus domain service folders.
- `src/types`: shared type folders for entities, requests, responses, enums, domains, plus `api.ts`, `auth.ts`, `navigation.ts`, `pagination.ts`, `response.ts`.

Observed competing structures:

- Page ownership is duplicated between route literals in `src/app/router.tsx` and `PATHS` in `src/routes/routes.ts`.
- Inventory hooks import `inventoryService` from `src/services/products`, so product/inventory ownership is currently combined at `src/services/products/index.ts`.
- Sales has a decomposition barrel, but the decomposed service files `salesQueryService.ts`, `salesWorkflowService.ts`, `paymentService.ts`, `receiptService.ts`, and `salesDashboardService.ts` are empty; the exported `salesService` facade comes from `src/services/sales/legacySalesService.ts`.
- Shared types are split across `src/types/*`, empty placeholders, domain re-export bundles, and service-local business interfaces.

## 3. Type-System Inventory

Files under `src/types`:

- `src/types/api.ts`: exports `HttpMethod`, `RequestConfig`, `ValidationError`, `ApiError`, `EntityId`.
- `src/types/auth.ts`: exports `Identity`, `Tenant`, `Branch`, `LoginRequest`, `AuthResponse`, `RefreshTokenRequest`, `RefreshTokenResponse`.
- `src/types/navigation.ts`: exports `NavigationItemId` enum, `NavigationItem`, `NavigationSection`.
- `src/types/pagination.ts`: exports `PaginationRequest`, `PaginationMeta`, `PaginatedResponse`.
- `src/types/response.ts`: exports `ApiResponse`, `ListResponse`, `MutationResponse`, `HealthResponse`, `EmptyResponse`.
- `src/types/domains/index.ts`: exports sales, inventory, procurement, finance, customers domain bundles.
- `src/types/domains/sales.ts`: re-exports sale entities, sale requests, daily/cashier summaries, payment and sale enums.
- `src/types/domains/customers.ts`, `finance.ts`, `inventory.ts`, `procurement.ts`: present but contain no exported symbols.
- `src/types/entities/index.ts`: exports only `sale`, `sale-item`, `sale-payment`.
- `src/types/entities/sale.ts`, `sale-item.ts`, `sale-payment.ts`: export `Sale`, `SaleItem`, `SalePayment`.
- `src/types/entities/branch.ts`, `permission.ts`, `role.ts`, `tenant.ts`, `user.ts`: empty.
- `src/types/enums/index.ts`: exports `sale-status`, `payment-method`.
- `src/types/enums/payment-method.ts`, `sale-status.ts`: export `PaymentMethod`, `SaleStatus` as type unions.
- `src/types/requests/index.ts`: exports only sale item/payment/create/update request DTOs.
- `src/types/requests/auth.ts`: exports `LoginRequest`, `RefreshTokenRequest`, `ForgotPasswordRequest`, `ResetPasswordRequest`, `ChangePasswordRequest`, but the barrel does not export this file.
- `src/types/requests/branch.ts`, `pagination.ts`, `permission.ts`, `role.ts`, `tenant.ts`, `user.ts`: empty.
- `src/types/responses/index.ts`: exports only `DailySalesSummary` and `CashierSummary`.
- `src/types/responses/auth.ts`: exports `AuthUser`, `AuthTenant`, `LoginData`, `LoginResponse`, `RefreshTokenData`, `RefreshTokenResponse`, `CurrentUserResponse`, but the barrel does not export this file.
- `src/types/responses/common.ts`, `pagination.ts`: empty.
- `src/types/sales/entities.ts`, `enums.ts`, `index.ts`, `requests.ts`, `responses.ts`: empty.

Duplicated definitions and unresolved ownership:

- Authentication DTOs exist in both `src/types/auth.ts` and `src/types/requests/auth.ts`/`src/types/responses/auth.ts`; consumers use both paths.
- `PaginatedResponse` is owned by `src/types/pagination.ts`, but hooks import it from `@/types/response` in multiple files, including `src/hooks/queries/common/usePaginatedQuery.ts:43`.
- `ApiResponse` is singular at `src/types/response.ts`, while response DTO barrels live under plural `src/types/responses`. Both paths are active.
- Sale types are centralized enough for the legacy service through `src/types/domains/sales.ts`, but the parallel `src/types/sales/*` folder is empty.
- Business types still declared inside services include `Customer`/`CreateCustomerRequest` in `src/services/customers/customerService.ts:43-91`, `Product`/`CreateProductRequest` in `src/services/products/productService.ts:41-101`, `InventoryItem` in `src/services/products/inventoryService.ts:44`, `Supplier` in `src/services/suppliers/supplierService.ts:38`, administration entities in `src/services/administration/*.ts`, dashboard response types in `src/services/dashboard/dashboardService.ts:42-116`, finance types in `src/services/finance/*.ts`, procurement types in `src/services/procurement/*.ts`, and refund/prescription types in `src/services/sales/*.ts`.

## 4. Service Inventory

Inherited `BaseService` public methods for extending services: `list`, `paginate`, `get`, `create`, `update`, `delete`, `createMany`, `deleteMany`, `search`, `count`, `exists`, `refresh` from `src/services/base/BaseService.ts:412-657`. Protected transport helpers wrap Axios at `src/services/base/BaseService.ts:673-832`.

| Domain | Service file | Class / instance | Public service methods beyond BaseService | Endpoint owner | Local business types | Hook consumers |
|---|---|---|---|---|---|---|
| Auth | `src/services/auth/authService.ts` | `AuthService`, `authService` | `login`, `logout`, `refreshToken`, `me`, `forgotPassword`, `resetPassword`, `changePassword`, `validateSession` | `API_ENDPOINTS.AUTH.*` | none local; imports request/response DTOs | `useCurrentUser`, `useLogin`, `useLogout`, but barrel is empty |
| Customers | `src/services/customers/customerService.ts` | `CustomerService`, `customerService` | `searchByPhone`, `searchByNationalId`, `statistics`, `balance`, `purchaseHistory`, `prescriptions`, `loyalty` | `API_ENDPOINTS.CUSTOMERS.ROOT`; customer sales via route composition | `CustomerStatus`, `Customer`, create/update DTOs, statistics/balance | customer query hooks |
| Dashboard | `src/services/dashboard/dashboardService.ts` | `DashboardService`, `dashboardService` | `overview`, `metrics`, `alerts`, `activity`, `lowStock`, `expiringProducts`, `recentSales` | `API_ENDPOINTS.DASHBOARD.ROOT` | dashboard widget/alert/activity types | dashboard hooks expect `getOverview`, `getMetrics`, `getAlerts`, `getActivity` |
| Products | `src/services/products/productService.ts` | `ProductService`, `productService` | `bySku`, `byBarcode`, `updatePrice`, `inventory`, `movements`, `activate`, `deactivate`, `uploadImage`, `removeImage` | `API_ENDPOINTS.PRODUCTS.*` | product and inventory summary/movement types | product hooks expect `findById`; list hook calls `paginate` |
| Categories | `src/services/products/categoryService.ts` | `CategoryService`, `categoryService` | `tree`, `children`, `parent`, `products`, `productCount`, `activate`, `deactivate` | `API_ENDPOINTS.CATEGORIES.ROOT` | category types | no direct query hooks observed |
| Inventory | `src/services/products/inventoryService.ts` | `InventoryService`, `inventoryService` | `byProduct`, `byBranch`, `adjust`, `transfer`, `reserve`, `releaseReservation`, `movements`, `batches`, `valuation`, `reorderList`, `expiring` | `API_ENDPOINTS.INVENTORY.*` | inventory, adjustment, movement, batch, valuation types | inventory hooks import from `@/services/products` and expect `adjustStock`, `receiveStock`, `stockCount`, `stockMovements`, `findById` |
| Suppliers | `src/services/suppliers/supplierService.ts` | `SupplierService`, `supplierService` | `products`, `purchaseHistory`, `performance`, `activate`, `deactivate` | `API_ENDPOINTS.SUPPLIERS.ROOT` | supplier/product/performance types | supplier hooks expect `findById` |
| Procurement / Purchase Orders | `src/services/procurement/purchaseOrderService.ts` | `PurchaseOrderService`, `purchaseOrderService` | `submit`, `approve`, `cancel`, `close`, `receivingProgress`, `summary`, `print`, `email` | `API_ENDPOINTS.PURCHASE_ORDERS.*` | PO status/entity/request/summary types | procurement hooks expect some matching methods plus absent names `cancelPurchaseOrder`, `receive`, `findById` |
| Procurement / Goods Receipts | `src/services/procurement/goodsReceiptService.ts` | `GoodsReceiptService`, `goodsReceiptService` | `purchaseOrder`, `post`, `reverse`, `summary`, `batches`, `print`, `validate` | `API_ENDPOINTS.GOODS_RECEIPTS.ROOT` | receipt status/entity/request/summary types | hooks expect absent `getGoodsReceipt`, `listGoodsReceipts` |
| Finance / Payments | `src/services/finance/paymentService.ts` | `PaymentService`, `paymentService` | `allocate`, `reverse`, `customerPayments`, `supplierPayments`, `dailySummary`, `outstandingBalance` | `API_ENDPOINTS.PAYMENTS.ROOT`; customer/supplier balance paths composed | payment method/status/entity/request/summary types | finance hook barrel is empty |
| Finance / Invoices | `src/services/finance/invoiceService.ts` | `InvoiceService`, `invoiceService` | `post`, `void`, `payments`, `customerInvoices`, `supplierInvoices`, `outstanding`, `summary`, `pdf` | `API_ENDPOINTS.INVOICES.*`; customer/supplier invoice paths composed | invoice status/entity/request/summary types | finance hook barrel is empty |
| Reports | `src/services/reports/reportService.ts` | `ReportService`, `reportService` | `sales`, `inventory`, `finance`, `procurement`, `customers`, `suppliers`, `audit`, `tax`, `export` | `API_ENDPOINTS.REPORTS.ROOT` | report DTOs | reports hook barrel is empty |
| Sales legacy | `src/services/sales/legacySalesService.ts` | `SalesService`, `salesService` | `checkout`, `complete`, `void`, `payments`, `receipt`, `customerSales`, `dailySummary`, `cashierSummary` | `API_ENDPOINTS.SALES.*`; customer sales path composed | imports sale types from `src/types/domains/sales.ts` | all sales hooks import the `salesService` facade |
| Sales prescriptions | `src/services/sales/prescriptionService.ts` | `PrescriptionService`, `prescriptionService` | `validate`, `dispense`, `refill`, `customerPrescriptions`, `prescriberPrescriptions`, `history` | `API_ENDPOINTS.PRESCRIPTIONS.ROOT`; customer path composed | prescription types | exported from sales barrel |
| Sales refunds | `src/services/sales/refundService.ts` | `RefundService`, `refundService` | `validate`, `approve`, `reject`, `complete`, `cancel`, `inventoryImpact`, `paymentReversal`, `summary`, `receipt`, `history` | `API_ENDPOINTS.REFUNDS.ROOT`; sale refund history path composed | refund types | exported from sales barrel; sales refund hook uses legacy `salesService.refundSale`, not this service |

Internal dependencies are consistently `BaseService`, `API_ENDPOINTS`, `ApiResponse`, and sometimes `PaginatedResponse`. `AuthService` directly imports `apiClient` instead of extending `BaseService`.

## 5. Sales Service Decomposition

- `src/services/sales/salesQueryService.ts`: empty.
- `src/services/sales/salesWorkflowService.ts`: empty.
- `src/services/sales/paymentService.ts`: empty.
- `src/services/sales/receiptService.ts`: empty.
- `src/services/sales/salesDashboardService.ts`: empty.
- `src/services/sales/refundService.ts`: implemented as `RefundService`/`refundService` with refund workflow methods at `src/services/sales/refundService.ts:135-324`.
- `src/services/sales/prescriptionService.ts`: implemented as `PrescriptionService`/`prescriptionService`.
- `src/services/sales/index.ts:18-24` exports the empty decomposition service instances, causing missing-export compiler errors.
- `src/services/sales/index.ts:38` exports `salesService` from `legacySalesService`; therefore the current sales facade is `SalesService` from `src/services/sales/legacySalesService.ts:59`.
- Hooks expect absent facade methods: `createSale`, `completeSale`, `suspendSale`, `resumeSale`, `voidSale`, `refundSale`, `getSale`, `listSales`, `getSalePayment`, `listSalePayments`, `getReceipt`, `listReceipts`, `getDashboard`.
- Legacy facade actually supplies: inherited `create`, `get`, `list`, `paginate`, etc., plus `checkout`, `complete`, `void`, `payments`, `receipt`, `customerSales`, `dailySummary`, `cashierSummary`.

## 6. Query-Hook Inventory

| Domain | Query hooks | Mutation hooks | Service method calls | Query keys | Invalidation | Direct Axios / direct invalidation / cross-domain imports |
|---|---|---|---|---|---|---|
| Common | `useEntity`, `useEntityList`, `usePaginatedQuery`, `useSearchQuery` | `useCreateEntity`, `useUpdateEntity`, `useDeleteEntity` | accepts callback | caller-supplied | caller-supplied callback | no direct Axios; calls provided invalidation callback |
| Auth | `useCurrentUser` | `useLogin`, `useLogout` | `authService.me/login/logout` | `QUERY_KEYS.auth.currentUser()` | authentication, dashboard, administration helpers | blocked by empty `src/services/auth/index.ts` |
| Dashboard | overview, metrics, alerts, activity | none | hooks call `getOverview/getMetrics/getAlerts/getActivity` | matching dashboard keys | none | service exposes `overview/metrics/alerts/activity` instead |
| Products | `useProducts`, `useProduct` | create/update/delete | `paginate`, `findById`, create/update/delete | `products.list(params)`, `products.detail(id)` | `invalidateProducts` | `products.list` takes no params; `findById` absent |
| Customers | `useCustomers`, `useCustomer` | create/update/delete | `paginate`, `findById`, create/update/delete | `customers.list(params)`, `customers.detail(id)` | `invalidateCustomers` | `customers.list` takes no params; `findById` absent |
| Suppliers | `useSuppliers`, `useSupplier` | create/update/delete | `paginate`, `findById`, create/update/delete | `suppliers.list(params)`, `suppliers.detail(id)` | `invalidateSuppliers` | `suppliers.index.ts` contains an inline duplicate `useDeleteSupplier` and a re-export |
| Inventory | inventory list, stock item, movements | receive, adjust, transfer, stock count | `paginate`, `findById`, `stockMovements`, `receiveStock`, `adjustStock`, `transferStock`, `stockCount` | inventory list/detail/movements | `invalidateInventoryOperations` | imports service from `@/services/products`; several method names absent |
| Procurement | purchase orders, purchase order, goods receipts, goods receipt, dashboard, requisitions, supplier deliveries | create, approve, receive, cancel PO | mix of `list`, `findById`, `approve`, absent `receive`, `cancelPurchaseOrder`, absent requisition/delivery/dashboard services | purchase order/goods receipt keys plus absent dashboard/requisition/delivery keys | `invalidateProcurementOperations` | no direct Axios; several services absent from procurement barrel |
| Sales | sales, sale, payments, payment, receipts, receipt, dashboard | create, complete, suspend, resume, void, refund | all against `salesService`; most expected business names absent | sales list/detail are called as `sales.sales()` and `sales.sale(id)`, but registry exposes `list()`/`detail(id)` | `invalidateSalesOperations` | refund hook does not use `refundService`; facade mismatch dominates |
| Finance | none; `src/hooks/queries/finance/index.ts` empty | none | none | none | none | service layer exists without hooks |
| Reports | none; `src/hooks/queries/reports/index.ts` empty | none | none | none | none | service layer exists without hooks |
| Administration | none; `src/hooks/queries/administration/index.ts` empty | none | none | none | none | service layer exists without hooks |

No query hook imports `apiClient` or `axios` directly. No hook calls `queryClient.invalidateQueries` directly; direct invalidation is centralized in `src/lib/queryInvalidation.ts:44` and `src/lib/queryInvalidation.ts:379`.

## 7. Query-Key Inventory

Current `QUERY_KEYS` hierarchy from `src/lib/queryKeys.ts`:

- `auth`: `root`, `currentUser()`, `profile()`, `permissions()`.
- `dashboard`: `root`, `all()`, `overview()`, `metrics()`, `alerts()`, `activity()`.
- `products`: `root`, `list()`, `detail(id)`, `categories()`.
- `customers`: `root`, `list()`, `detail(id)`.
- `suppliers`: `root`, `list()`, `detail(id)`.
- `inventory`: `root`, `list()`, `detail(id)`, `movements()`, `stockCounts()`.
- `procurement`: `root`, `purchaseOrders()`, `purchaseOrder(id)`, `goodsReceipts()`, `goodsReceipt(id)`.
- `sales`: `root`, `list()`, `detail(id)`, `payments(saleId)`, `payment(paymentId)`, `receipts()`, `receipt(receiptId)`, `dashboard()`, `refunds()`, `suspended()`, `prescriptions()`.
- `finance`: `root`, `invoices()`, `invoice(id)`, `payments()`, `payment(id)`.
- `administration`: `root`, `users()`, `user(id)`, `roles()`, `permissions()`, `branches()`, `tenants()`.
- `reports`: `root`, `sales()`, `inventory()`, `finance()`, `procurement()`, `audit()`.

Functions accepting filters or pagination: none. Hooks pass params to no-arg key functions in `products.list(params)`, `customers.list(params)`, `suppliers.list(params)`, `inventory.list(params)`, `inventory.movements(params)`, `procurement.purchaseOrders(params)`, and `procurement.goodsReceipts(params)`.

Hooks calling nonexistent keys:

- `QUERY_KEYS.sales.sales()` in `src/hooks/queries/sales/useSales.ts:66`.
- `QUERY_KEYS.sales.sale(id)` in `src/hooks/queries/sales/useSale.ts:65`.
- `QUERY_KEYS.procurement.dashboard()` in `src/hooks/queries/procurement/useProcurementDashboard.ts:51`.
- `QUERY_KEYS.procurement.purchaseRequisition(...)` in `src/hooks/queries/procurement/usePurchaseRequisition.ts:57`.
- `QUERY_KEYS.procurement.purchaseRequisitions(...)` in `src/hooks/queries/procurement/usePurchaseRequisitions.ts:62`.
- `QUERY_KEYS.procurement.supplierDeliveries(...)` in `src/hooks/queries/procurement/useSupplierDeliveries.ts:58`.

Hardcoded query keys were not observed in query hooks; hooks consistently import the central registry.

## 8. Cache Invalidation Inventory

Centralized helpers in `src/lib/queryInvalidation.ts`:

- `invalidateAuthentication`: auth root, current user, profile, permissions.
- `invalidateDashboard`: dashboard root.
- `invalidateProducts`, `invalidateCustomers`, `invalidateSuppliers`: respective roots.
- `invalidateInventory`: inventory root.
- `invalidateInventoryOperations`: inventory root, inventory movements, dashboard root.
- `invalidateProcurement`: procurement root.
- `invalidateProcurementOperations`: procurement, inventory, suppliers, finance, dashboard roots.
- `invalidateSales`: sales root.
- `invalidateSalesOperations`: sales, inventory, customers, finance, reports, dashboard roots.
- `invalidateFinance`, `invalidateFinanceOperations`, `invalidateReports`, `invalidateAdministration`, `invalidateAll`.

Operations covered are broad domain and workflow invalidations, but not detail-level invalidations for a single entity. Mutation hooks generally use the framework helpers. Direct cache invalidation exists only inside the framework (`invalidateMany` and `invalidateAll`), not in services/components/hooks found by search.

Compiler baseline shows invalidation-helper signature drift in common mutation hooks: `useCreateEntity.ts:104`, `useDeleteEntity.ts:104`, and `useUpdateEntity.ts:114` call TanStack mutation lifecycle callbacks with three arguments where the current type expects four.

## 9. Provider and Route Inventory

Provider hierarchy is declared in `src/providers/AppProvider.tsx:55-73`: `ThemeProvider -> QueryProvider -> AuthProvider -> ShellProvider -> TooltipProvider -> Toaster/children`.

Public provider exports: `src/providers/index.ts` is empty. This conflicts with `src/main.tsx:4`, which imports `{ AppProvider }` from `@/providers`.

Context ownership:

- `ApplicationProvider` owns `ApplicationContextValue` and `useApplicationContext`, but `ApplicationContext` itself is private at `src/providers/ApplicationProvider.tsx:63`.
- `ShellProvider` owns `ShellContextValue` and `useShell` at `src/providers/ShellProvider.tsx:58-167`.
- `AuthProvider` initializes auth store state via `storage` and `useAuthStore`.
- `QueryProvider` owns QueryClient creation.
- `ThemeProvider` initializes theme state.

Protected route dependencies:

- `src/routes/ProtectedRoute.tsx` imports `APP_ROUTES` from `@/constants/auth`, but the compiler reports no named export at line 34.
- `ProtectedRoute` obtains auth through `useApplication`; compiler reports `auth` as unknown at lines 77 and 92.
- `useApplication.ts` imports a non-exported `ApplicationContext` at line 49, while `ApplicationProvider` only exports `useApplicationContext`.

Provider/context contract mismatches include the empty provider barrel, private context versus consumer import, and `AppProvider` passing `delayDuration` to `TooltipProvider` at `src/providers/AppProvider.tsx:59`, which the current component props do not accept.

## 10. Navigation Inventory

- Section ID source: `NavigationSectionId` enum in `src/navigation/sections.ts:17`.
- Item ID source: `NavigationItemId` enum in `src/types/navigation.ts:16`.
- Navigation registry: `src/navigation/navigation.ts`.
- Permission associations: inline `permission` values in navigation items map to `PERMISSIONS` string values in `src/navigation/permissions.ts`, but the registry uses string literals rather than imported constants.
- Filtering functions: `flattenNavigation`, `findNavigationItemById`, `findNavigationItemByPath`, `findNavigationSection`, `isNavigationItemActive`, `getProtectedNavigationItems`, `filterNavigationByPermissions`, `buildBreadcrumbs` in `src/navigation/helpers.ts`.
- Public exports: `src/navigation/index.ts` exports `navigation`, `PERMISSIONS`, `NavigationSectionId`, and helper names.

Conflicts:

- `navigation.ts` assigns raw strings such as `"dashboard"` to fields typed as enum values; with `erasableSyntaxOnly`, `NavigationSectionId` and `NavigationItemId` enums also produce TS1294.
- The public barrel does not export `filterNavigation` or `filterNavigationSection`, yet `src/hooks/useNavigation.ts:5-6` imports those names.
- `AppSidebar.tsx` imports `navigationSections`, but `src/navigation/index.ts` exports `navigation`.
- `SidebarGroup.tsx` imports `visibleNavigationItems`, but no exported helper uses that name.
- `warehouses` appears as an inventory item ID at `src/navigation/navigation.ts:85` and again as an administration item ID at `src/navigation/navigation.ts:218`; `NavigationItemId` contains `WAREHOUSES = "warehouses"` and `ADMIN_WAREHOUSES = "admin-warehouses"`.

## 11. Barrel-Export Inventory

Empty or missing public barrels:

- `src/services/auth/index.ts`: empty; auth hooks import `authService` from `@/services/auth`.
- `src/services/index.ts`: empty.
- `src/providers/index.ts`: empty; `src/main.tsx` imports `AppProvider` from it.
- `src/hooks/queries/administration/index.ts`, `finance/index.ts`, `reports/index.ts`: empty.
- `src/types/sales/index.ts`: empty.

Duplicate or conflicting barrels:

- `src/hooks/queries/auth/index.ts:11-17` exports the same names both as named exports and default aliases, causing duplicate identifier errors.
- `src/hooks/queries/suppliers/index.ts:28-81` contains an implementation of `useDeleteSupplier` and also re-exports `useDeleteSupplier`, causing redeclaration/export conflicts.

Obsolete exports or exports pointing to absent symbols:

- `src/services/sales/index.ts:18-24` exports instances from empty decomposition files.
- `src/services/products/index.ts:40-44` exports absent `ProductStatus`, `ProductType`, `ProductSummary`.
- `src/services/products/index.ts:75-79` exports absent `InventoryAdjustment`, `InventoryMovement`, `InventorySummary`, `CreateInventoryAdjustmentRequest`, `StockTransferRequest`; implementation has `InventoryAdjustmentRequest`, `BranchTransferRequest`, and local `StockMovement`.
- `src/services/suppliers/index.ts:48-52` exports absent `SupplierStatus`, `SupplierType`, `SupplierSummary`, `SupplierContact`.
- `src/services/administration/index.ts:32` exports absent `UserStatus`; line 65 exports absent `PermissionCategory`.
- `src/types/requests/index.ts` omits auth request DTOs; `src/types/responses/index.ts` omits auth response DTOs.

## 12. Compiler Baseline

Command run: `npm run build` from `frontend/`.

Result: exit code 2. `tsc -b` failed; Vite build did not run.

Total compiler error count: 294 occurrences of `error TS`.

Error codes by count:

- TS2305: 109
- TS2339: 41
- TS2322: 40
- TS2724: 14
- TS2614: 14
- TS2693: 11
- TS2554: 11
- TS6133: 10
- TS2307: 9
- TS7006: 7
- TS2551: 6
- TS2300: 6
- TS1294: 3
- TS2686: 2
- TS2349: 2
- TS2323: 2
- TS18046: 2
- TS2739, TS2559, TS2484, TS2430, TS1484: 1 each

Estimated compiler errors by architectural category:

- Type ownership: 83. Missing or mislocated entities/requests/responses, especially `@/types/entities`, `@/types/requests`, `@/types/responses`, and `@/types/response`.
- Service facade: 31. Empty auth/sales/procurement facades and legacy facade mismatch.
- Hook/service contract: 49. Hooks expect old method names such as `findById`, `getOverview`, `listSales`, `receiveStock`, and `cancelPurchaseOrder`.
- Query keys: 11. Nonexistent keys and incompatible no-arg key signatures.
- Invalidation: 3. Common mutation helper callback argument drift.
- Navigation: 39. Enum/runtime-value mismatch, missing navigation helper exports, duplicate `warehouses` item ID.
- Providers/routes: 8. Empty provider barrel, private ApplicationContext import, unknown auth value, protected-route constants.
- Barrel exports: 22. Duplicate hook exports and obsolete type exports.
- Error handling: 12. `AppError.fromAxios` missing at `src/api/interceptors.ts:187`; `ErrorCode` type used as value in `src/lib/errors.ts:151-181`.
- TypeScript strictness: 22. `erasableSyntaxOnly` enum errors, `verbatimModuleSyntax` type-only import, unused locals/params, implicit `any`, React UMD reference.
- Isolated implementation defects: 14. Missing UI/auth component modules, incompatible UI component props, layout constant names, page prop extension issue.

Top ten architectural breakpoints:

1. `src/types` has incomplete barrels and empty ownership files while services still own many business DTOs.
2. `src/types/response.ts` and `src/types/responses/` coexist with active imports to both singular and plural paths.
3. `BaseService` method names differ from hook assumptions: `get` versus `findById`, `list`/`paginate` versus domain-specific `listX`.
4. Sales decomposition is declared in the barrel but most decomposed service files are empty; the active facade is still legacy.
5. Sales hooks are written against expected business-method names that the legacy facade does not provide.
6. `QUERY_KEYS` does not accept list filters/pagination but hooks pass params into list/movement/order key factories.
7. Procurement hooks reference dashboard/requisition/delivery keys and services that are not present in the registry/barrel.
8. Navigation runtime config uses raw strings against enum-typed IDs under `erasableSyntaxOnly`; duplicated `warehouses` IDs add runtime ambiguity.
9. Provider public surface is absent even though `main.tsx` imports from it; `useApplication` imports a private context.
10. Barrel files alternate between empty, duplicated exports, and stale exports to absent service-local symbols.

Uncertainties requiring additional inspection:

- Whether service-local business types are intentionally temporary during ADR migration or are now the de facto source of truth.
- Whether the expected hook method names reflect a previous API (`findById`, `listSales`) or the target ADR contract.
- Whether empty service files represent planned decomposition stubs or accidental truncation.
- Whether navigation IDs should be runtime string unions, const objects, or enums under the current TypeScript 6 `erasableSyntaxOnly` setting.
- Whether `src/types/auth.ts` or `src/types/requests/auth.ts`/`src/types/responses/auth.ts` is intended to own authentication DTOs.
- Whether finance, reports, and administration hooks are intentionally deferred or missing from the architecture baseline implementation.
