
/**
 * ============================================================================
 * Hela360 Enterprise Query Keys
 * ============================================================================
 *
 * Central registry for every TanStack Query key used throughout the
 * application.
 *
 * All hooks must consume query keys from this file.
 *
 * ============================================================================
 */

import type {
  ListGoodsReceiptsRequest,
  ListInventoryMovementsRequest,
  ListSalesRequest,
  ListInventoryRequest,
  ListStockAdjustmentsRequest,
  ListStockCountsRequest,
  ListCatalogueItemsRequest,
  ListProductsRequest,
  PaginationRequest,
} from "@/types/requests";
import type {
  ListOfficeMasterItemsRequest,
} from "@/types/officeCatalogue";
import {
  createBranchQueryKey,
  createIdentityQueryKey,
  createTenantQueryKey,
  type QueryKeySegment,
} from "@/lib/queryScope";
import type {
  BranchQueryScope,
  TenantQueryScope,
} from "@/types/domains/query-scope";

/* ============================================================================
 * Query Key Normalization
 * ============================================================================
 */

interface NormalizedPaginationRequest {
  readonly page: number;

  readonly per_page: number;

  readonly search?: string;

  readonly q?: string;
}

interface NormalizedListProductsRequest {
  readonly page: number;

  readonly per_page: number;

  readonly search?: string;

  readonly is_active?: boolean;

  readonly product_type?: string;
}

interface NormalizedListSalesRequest {
  readonly page: number;

  readonly per_page: number;

  readonly search?: string;

  readonly date_from?: string;

  readonly date_to?: string;

  readonly status?: string;

  readonly customer_id?: string;
}

interface NormalizedListInventoryRequest {
  readonly page: number;

  readonly per_page: number;

  readonly search?: string;

  readonly warehouse_id?: string;

  readonly stock_status?: string;

  readonly expires_before?: string;
}

interface NormalizedListInventoryMovementsRequest {
  readonly page: number;

  readonly per_page: number;

  readonly date_from?: string;

  readonly date_to?: string;

  readonly product_id?: string;

  readonly warehouse_id?: string;

  readonly movement_type?: string;

  readonly reference_type?: string;

  readonly reference_id?: string;
}

interface NormalizedListGoodsReceiptsRequest {
  readonly page: number;

  readonly per_page: number;

  readonly search?: string;

  readonly date_from?: string;

  readonly date_to?: string;

  readonly warehouse_id?: string;

  readonly supplier_id?: string;
}

interface NormalizedListStockCountsRequest {
  readonly page: number;

  readonly per_page: number;

  readonly status?: string;

  readonly warehouse_id?: string;

  readonly date_from?: string;

  readonly date_to?: string;
}

interface NormalizedListStockAdjustmentsRequest {
  readonly page: number;

  readonly per_page: number;

  readonly warehouse_id?: string;

  readonly reason_code?: string;

  readonly source_type?: string;

  readonly date_from?: string;

  readonly date_to?: string;
}

function normalizePaginationRequest(
  params?: PaginationRequest,
): NormalizedPaginationRequest {
  const search = params?.search?.trim();

  const q = params?.q?.trim();

  return Object.freeze({
    page: params?.page ?? 1,

    per_page: params?.per_page ?? 25,

    ...(search ? { search } : {}),

    ...(q ? { q } : {}),
  });
}

interface NormalizedListOfficeMasterItemsRequest {
  readonly page: number;
  readonly per_page: number;
  readonly search?: string;
  readonly review_status?: string;
  readonly is_active?: boolean;
  readonly item_class?: string;
  readonly category?: string;
  readonly dosage_form?: string;
}

function normalizeListOfficeMasterItemsRequest(
  params?: ListOfficeMasterItemsRequest,
): NormalizedListOfficeMasterItemsRequest {
  const search =
    params?.search?.trim();

  const reviewStatus =
    params?.review_status?.trim();

  const itemClass =
    params?.item_class?.trim();

  const category =
    params?.category?.trim();

  const dosageForm =
    params?.dosage_form?.trim();

  return Object.freeze({
    page: params?.page ?? 1,
    per_page: params?.per_page ?? 25,

    ...(search
      ? { search }
      : {}),

    ...(reviewStatus
      ? { review_status: reviewStatus }
      : {}),

    ...(params?.is_active !== undefined
      ? { is_active: params.is_active }
      : {}),

    ...(itemClass
      ? { item_class: itemClass }
      : {}),

    ...(category
      ? { category }
      : {}),

    ...(dosageForm
      ? { dosage_form: dosageForm }
      : {}),
  });
}


interface NormalizedListCatalogueItemsRequest {
  readonly page: number;

  readonly per_page: number;

  readonly search?: string;

  readonly item_class?: string;

  readonly category?: string;

  readonly dosage_form?: string;

  readonly adoption_status?:
    ListCatalogueItemsRequest["adoption_status"];
}

function normalizeListCatalogueItemsRequest(
  params?: ListCatalogueItemsRequest,
): NormalizedListCatalogueItemsRequest {
  const search = params?.search?.trim();

  const itemClass =
    params?.item_class?.trim();

  const category =
    params?.category?.trim();

  const dosageForm =
    params?.dosage_form?.trim();

  return Object.freeze({
    page: params?.page ?? 1,

    per_page: params?.per_page ?? 25,

    ...(search ? { search } : {}),

    ...(itemClass
      ? { item_class: itemClass }
      : {}),

    ...(category ? { category } : {}),

    ...(dosageForm
      ? { dosage_form: dosageForm }
      : {}),

    ...(params?.adoption_status
      ? {
          adoption_status:
            params.adoption_status,
        }
      : {}),
  });
}


function normalizeListProductsRequest(
  params?: ListProductsRequest,
): NormalizedListProductsRequest {
  const search = params?.search?.trim();

  const productType =
    params?.product_type?.trim();

  return Object.freeze({
    page: params?.page ?? 1,

    per_page: params?.per_page ?? 25,

    ...(search ? { search } : {}),

    ...(params?.is_active !== undefined
      ? { is_active: params.is_active }
      : {}),

    ...(productType
      ? { product_type: productType }
      : {}),
  });
}

function normalizeListSalesRequest(
  params?: ListSalesRequest,
): NormalizedListSalesRequest {
  const search = params?.search?.trim();
  const dateFrom = params?.date_from?.trim();
  const dateTo = params?.date_to?.trim();
  const status = params?.status?.trim();
  const customerId = params?.customer_id?.trim();

  return Object.freeze({
    page: params?.page ?? 1,

    per_page: params?.per_page ?? 25,

    ...(search ? { search } : {}),

    ...(dateFrom ? { date_from: dateFrom } : {}),

    ...(dateTo ? { date_to: dateTo } : {}),

    ...(status ? { status } : {}),

    ...(customerId ? { customer_id: customerId } : {}),
  });
}

function normalizeListInventoryRequest(
  params?: ListInventoryRequest,
): NormalizedListInventoryRequest {
  const search = params?.search?.trim();
  const warehouseId = params?.warehouse_id?.trim();
  const stockStatus = params?.stock_status?.trim();
  const expiresBefore = params?.expires_before?.trim();

  return Object.freeze({
    page: params?.page ?? 1,

    per_page: params?.per_page ?? 25,

    ...(search ? { search } : {}),

    ...(warehouseId ? { warehouse_id: warehouseId } : {}),

    ...(stockStatus ? { stock_status: stockStatus } : {}),

    ...(expiresBefore ? { expires_before: expiresBefore } : {}),
  });
}

function normalizeListInventoryMovementsRequest(
  params?: ListInventoryMovementsRequest,
): NormalizedListInventoryMovementsRequest {
  const dateFrom = params?.date_from?.trim();
  const dateTo = params?.date_to?.trim();
  const productId = params?.product_id?.trim();
  const warehouseId = params?.warehouse_id?.trim();
  const movementType = params?.movement_type?.trim();
  const referenceType = params?.reference_type?.trim();
  const referenceId = params?.reference_id?.trim();

  return Object.freeze({
    page: params?.page ?? 1,

    per_page: params?.per_page ?? 25,

    ...(dateFrom ? { date_from: dateFrom } : {}),

    ...(dateTo ? { date_to: dateTo } : {}),

    ...(productId ? { product_id: productId } : {}),

    ...(warehouseId ? { warehouse_id: warehouseId } : {}),

    ...(movementType ? { movement_type: movementType } : {}),

    ...(referenceType ? { reference_type: referenceType } : {}),

    ...(referenceId ? { reference_id: referenceId } : {}),
  });
}

function normalizeListGoodsReceiptsRequest(
  params?: ListGoodsReceiptsRequest,
): NormalizedListGoodsReceiptsRequest {
  const search = params?.search?.trim();
  const dateFrom = params?.date_from?.trim();
  const dateTo = params?.date_to?.trim();
  const warehouseId = params?.warehouse_id?.trim();
  const supplierId = params?.supplier_id?.trim();

  return Object.freeze({
    page: params?.page ?? 1,

    per_page: params?.per_page ?? 25,

    ...(search ? { search } : {}),

    ...(dateFrom ? { date_from: dateFrom } : {}),

    ...(dateTo ? { date_to: dateTo } : {}),

    ...(warehouseId ? { warehouse_id: warehouseId } : {}),

    ...(supplierId ? { supplier_id: supplierId } : {}),
  });
}

function normalizeListStockCountsRequest(
  params?: ListStockCountsRequest,
): NormalizedListStockCountsRequest {
  const status = params?.status?.trim();
  const warehouseId = params?.warehouse_id?.trim();
  const dateFrom = params?.date_from?.trim();
  const dateTo = params?.date_to?.trim();

  return Object.freeze({
    page: params?.page ?? 1,

    per_page: params?.per_page ?? 25,

    ...(status ? { status } : {}),

    ...(warehouseId ? { warehouse_id: warehouseId } : {}),

    ...(dateFrom ? { date_from: dateFrom } : {}),

    ...(dateTo ? { date_to: dateTo } : {}),
  });
}

function normalizeListStockAdjustmentsRequest(
  params?: ListStockAdjustmentsRequest,
): NormalizedListStockAdjustmentsRequest {
  const warehouseId = params?.warehouse_id?.trim();
  const reasonCode = params?.reason_code?.trim();
  const sourceType = params?.source_type?.trim();
  const dateFrom = params?.date_from?.trim();
  const dateTo = params?.date_to?.trim();

  return Object.freeze({
    page: params?.page ?? 1,

    per_page: params?.per_page ?? 25,

    ...(warehouseId ? { warehouse_id: warehouseId } : {}),

    ...(reasonCode ? { reason_code: reasonCode } : {}),

    ...(sourceType ? { source_type: sourceType } : {}),

    ...(dateFrom ? { date_from: dateFrom } : {}),

    ...(dateTo ? { date_to: dateTo } : {}),
  });
}

export const QUERY_KEYS = {
  /* ==========================================================================
   * Authentication
   * ==========================================================================
   */

  auth: {
    root: ["auth"] as const,

    currentSession: () => createIdentityQueryKey("session"),

    currentUser: () => [...QUERY_KEYS.auth.root, "current-user"] as const,

    profile: () => [...QUERY_KEYS.auth.root, "profile"] as const,

    permissions: () => [...QUERY_KEYS.auth.root, "permissions"] as const,
  },

  /* ==========================================================================
   * Dashboard
   * ==========================================================================
   */

  dashboard: {
    root: ["dashboard"] as const,

    all: () => QUERY_KEYS.dashboard.root,

    overview: (operationalDate?: string) =>
      [
        ...QUERY_KEYS.dashboard.root,
        "overview",
        operationalDate?.trim() || "current",
      ] as const,

    metrics: () => [...QUERY_KEYS.dashboard.root, "metrics"] as const,

    alerts: () => [...QUERY_KEYS.dashboard.root, "alerts"] as const,

    activity: () => [...QUERY_KEYS.dashboard.root, "activity"] as const,
  },

  /* ==========================================================================
   * Products
   * ==========================================================================
   */

  products: {
    root: (scope: TenantQueryScope) =>
      createTenantQueryKey(scope, "products"),

    disabled: (
      ...segments: readonly QueryKeySegment[]
    ) =>
      createIdentityQueryKey(
        "disabled",
        "products",
        ...segments,
      ),

    lists: (scope: TenantQueryScope) =>
      [...QUERY_KEYS.products.root(scope), "list"] as const,

    list: (
      scope: TenantQueryScope,
      params?: ListProductsRequest,
    ) =>
      [
        ...QUERY_KEYS.products.lists(scope),
        normalizeListProductsRequest(params),
      ] as const,

    details: (scope: TenantQueryScope) =>
      [...QUERY_KEYS.products.root(scope), "detail"] as const,

    detail: (
      scope: TenantQueryScope,
      id: string | number,
    ) =>
      [...QUERY_KEYS.products.details(scope), id] as const,

    units: (
      scope: TenantQueryScope,
      productId: string | number,
    ) =>
      [
        ...QUERY_KEYS.products.detail(scope, productId),
        "units",
      ] as const,

    byCode: (
      scope: TenantQueryScope,
      codeValue: string,
    ) =>
      [
        ...QUERY_KEYS.products.root(scope),
        "by-code",
        codeValue.trim(),
      ] as const,

    taxCodes: (scope: TenantQueryScope) =>
      [
        ...QUERY_KEYS.products.root(scope),
        "tax-codes",
      ] as const,
  },

  /* ==========================================================================
   * Hela360 Office
   * ==========================================================================
   */

  office: {
    masterItems: {
      root: () =>
        createIdentityQueryKey(
          "office",
          "master-items",
        ),

      lists: () =>
        [
          ...QUERY_KEYS.office.masterItems.root(),
          "list",
        ] as const,

      list: (
        params?: ListOfficeMasterItemsRequest,
      ) =>
        [
          ...QUERY_KEYS.office.masterItems.lists(),
          normalizeListOfficeMasterItemsRequest(
            params,
          ),
        ] as const,


      details: () =>
        [
          ...QUERY_KEYS.office.masterItems.root(),
          "detail",
        ] as const,

      detail: (
        masterItemId: string,
      ) =>
        [
          ...QUERY_KEYS.office.masterItems.details(),
          masterItemId.trim(),
        ] as const,


      supplierEvidence: (
        masterItemId: string,
      ) =>
        [
          ...QUERY_KEYS.office.masterItems.detail(
            masterItemId,
          ),
          "supplier-evidence",
        ] as const,
    },
  },

  /* ==========================================================================
   * Master Catalogue
   * ==========================================================================
   */

  catalogue: {
    root: (scope: TenantQueryScope) =>
      createTenantQueryKey(
        scope,
        "catalogue",
      ),

    disabled: (
      ...segments: readonly QueryKeySegment[]
    ) =>
      createIdentityQueryKey(
        "disabled",
        "catalogue",
        ...segments,
      ),

    lists: (scope: TenantQueryScope) =>
      [
        ...QUERY_KEYS.catalogue.root(scope),
        "list",
      ] as const,

    list: (
      scope: TenantQueryScope,
      params?: ListCatalogueItemsRequest,
    ) =>
      [
        ...QUERY_KEYS.catalogue.lists(scope),
        normalizeListCatalogueItemsRequest(
          params,
        ),
      ] as const,

    details: (scope: TenantQueryScope) =>
      [
        ...QUERY_KEYS.catalogue.root(scope),
        "detail",
      ] as const,

    detail: (
      scope: TenantQueryScope,
      masterItemId: string,
    ) =>
      [
        ...QUERY_KEYS.catalogue.details(scope),
        masterItemId.trim(),
      ] as const,
  },

  /* ==========================================================================
   * Customers
   * ==========================================================================
   */

  customers: {
    root: (scope: TenantQueryScope) =>
      createTenantQueryKey(scope, "customers"),

    disabled: (
      ...segments: readonly QueryKeySegment[]
    ) =>
      createIdentityQueryKey(
        "disabled",
        "customers",
        ...segments,
      ),

    lists: (scope: TenantQueryScope) =>
      [...QUERY_KEYS.customers.root(scope), "list"] as const,

    list: (
      scope: TenantQueryScope,
      params?: PaginationRequest,
    ) =>
      [
        ...QUERY_KEYS.customers.lists(scope),
        normalizePaginationRequest(params),
      ] as const,

    details: (scope: TenantQueryScope) =>
      [...QUERY_KEYS.customers.root(scope), "detail"] as const,

    detail: (
      scope: TenantQueryScope,
      id: string | number,
    ) =>
      [...QUERY_KEYS.customers.details(scope), id] as const,
  },

  /* ==========================================================================
   * Suppliers
   * ==========================================================================
   */

  suppliers: {
    root: (scope: TenantQueryScope) =>
      createTenantQueryKey(scope, "suppliers"),

    disabled: (
      ...segments: readonly QueryKeySegment[]
    ) =>
      createIdentityQueryKey(
        "disabled",
        "suppliers",
        ...segments,
      ),

    lists: (scope: TenantQueryScope) =>
      [...QUERY_KEYS.suppliers.root(scope), "list"] as const,

    list: (
      scope: TenantQueryScope,
      params?: PaginationRequest,
    ) =>
      [
        ...QUERY_KEYS.suppliers.lists(scope),
        normalizePaginationRequest(params),
      ] as const,

    details: (scope: TenantQueryScope) =>
      [...QUERY_KEYS.suppliers.root(scope), "detail"] as const,

    detail: (
      scope: TenantQueryScope,
      id: string | number,
    ) =>
      [...QUERY_KEYS.suppliers.details(scope), id] as const,
  },

  /* ==========================================================================
   * Payment Methods
   * ==========================================================================
   */

  paymentMethods: {
    root: (scope: TenantQueryScope) =>
      createTenantQueryKey(scope, "payment-methods"),

    disabled: (
      ...segments: readonly QueryKeySegment[]
    ) =>
      createIdentityQueryKey(
        "disabled",
        "payment-methods",
        ...segments,
      ),

    list: (scope: TenantQueryScope) =>
      [
        ...QUERY_KEYS.paymentMethods.root(scope),
        "list",
      ] as const,
  },

  /* ==========================================================================
   * Tills
   * ==========================================================================
   */

  tills: {
    root: (scope: BranchQueryScope) =>
      createBranchQueryKey(scope, "tills"),

    disabled: (
      ...segments: readonly QueryKeySegment[]
    ) =>
      createIdentityQueryKey(
        "disabled",
        "tills",
        ...segments,
      ),

    list: (scope: BranchQueryScope) =>
      [
        ...QUERY_KEYS.tills.root(scope),
        "list",
      ] as const,
  },

  /* ==========================================================================
   * Warehouses
   * ==========================================================================
   */

  warehouses: {
    root: (scope: BranchQueryScope) =>
      createBranchQueryKey(scope, "warehouses"),

    disabled: (
      ...segments: readonly QueryKeySegment[]
    ) =>
      createIdentityQueryKey(
        "disabled",
        "warehouses",
        ...segments,
      ),

    list: (scope: BranchQueryScope) =>
      [
        ...QUERY_KEYS.warehouses.root(scope),
        "list",
      ] as const,
  },

  /* ==========================================================================
   * Till Shifts
   * ==========================================================================
   */

  tillShifts: {
    root: (scope: BranchQueryScope) =>
      createBranchQueryKey(scope, "till-shifts"),

    disabled: (
      ...segments: readonly QueryKeySegment[]
    ) =>
      createIdentityQueryKey(
        "disabled",
        "till-shifts",
        ...segments,
      ),

    current: (
      scope: BranchQueryScope,
      tillId?: string,
    ) =>
      [
        ...QUERY_KEYS.tillShifts.root(scope),
        "current",
        ...(tillId ? [tillId.trim()] : []),
      ] as const,
  },

  /* ==========================================================================
   * Inventory
   * ==========================================================================
   */

  inventory: {
    root: ["inventory"] as const,

    branchRoot: (scope: BranchQueryScope) =>
      createBranchQueryKey(scope, "inventory"),

    disabled: (
      ...segments: readonly QueryKeySegment[]
    ) =>
      createIdentityQueryKey(
        "disabled",
        "inventory",
        ...segments,
      ),

    lists: (scope: BranchQueryScope) =>
      [...QUERY_KEYS.inventory.branchRoot(scope), "list"] as const,

    list: (
      scope: BranchQueryScope,
      params?: ListInventoryRequest,
    ) =>
      [
        ...QUERY_KEYS.inventory.lists(scope),
        normalizeListInventoryRequest(params),
      ] as const,

    details: (scope: BranchQueryScope) =>
      [...QUERY_KEYS.inventory.branchRoot(scope), "detail"] as const,

    detail: (
      scope: BranchQueryScope,
      id: string | number,
    ) =>
      [...QUERY_KEYS.inventory.details(scope), id] as const,

    batches: (
      scope: BranchQueryScope,
      stockBalanceId: string,
    ) =>
      [
        ...QUERY_KEYS.inventory.branchRoot(scope),
        "batches",
        stockBalanceId.trim(),
      ] as const,

    movementLists: (scope: BranchQueryScope) =>
      [
        ...QUERY_KEYS.inventory.branchRoot(scope),
        "movements",
        "list",
      ] as const,

    movements: (
      scope: BranchQueryScope,
      params?: ListInventoryMovementsRequest,
    ) =>
      [
        ...QUERY_KEYS.inventory.movementLists(scope),
        normalizeListInventoryMovementsRequest(params),
      ] as const,

    goodsReceiptDetails: (scope: BranchQueryScope) =>
      [
        ...QUERY_KEYS.inventory.branchRoot(scope),
        "goods-receipts",
        "detail",
      ] as const,

    goodsReceiptLists: (scope: BranchQueryScope) =>
      [
        ...QUERY_KEYS.inventory.branchRoot(scope),
        "goods-receipts",
        "list",
      ] as const,

    goodsReceipts: (
      scope: BranchQueryScope,
      params?: ListGoodsReceiptsRequest,
    ) =>
      [
        ...QUERY_KEYS.inventory.goodsReceiptLists(scope),
        normalizeListGoodsReceiptsRequest(params),
      ] as const,

    goodsReceipt: (
      scope: BranchQueryScope,
      id: string | number,
    ) =>
      [
        ...QUERY_KEYS.inventory.goodsReceiptDetails(scope),
        String(id).trim(),
      ] as const,

    stockCounts: () =>
      [...QUERY_KEYS.inventory.root, "stock-counts"] as const,

    stockCountLists: (scope: BranchQueryScope) =>
      [
        ...QUERY_KEYS.inventory.branchRoot(scope),
        "stock-counts",
        "list",
      ] as const,

    stockCountsList: (
      scope: BranchQueryScope,
      params?: ListStockCountsRequest,
    ) =>
      [
        ...QUERY_KEYS.inventory.stockCountLists(scope),
        normalizeListStockCountsRequest(params),
      ] as const,

    stockCountDetails: (scope: BranchQueryScope) =>
      [
        ...QUERY_KEYS.inventory.branchRoot(scope),
        "stock-counts",
        "detail",
      ] as const,

    stockCount: (
      scope: BranchQueryScope,
      id: string | number,
    ) =>
      [
        ...QUERY_KEYS.inventory.stockCountDetails(scope),
        String(id).trim(),
      ] as const,

    stockAdjustmentLists: (scope: BranchQueryScope) =>
      [
        ...QUERY_KEYS.inventory.branchRoot(scope),
        "stock-adjustments",
        "list",
      ] as const,

    stockAdjustmentsList: (
      scope: BranchQueryScope,
      params?: ListStockAdjustmentsRequest,
    ) =>
      [
        ...QUERY_KEYS.inventory.stockAdjustmentLists(scope),
        normalizeListStockAdjustmentsRequest(params),
      ] as const,

    stockAdjustmentDetails: (scope: BranchQueryScope) =>
      [
        ...QUERY_KEYS.inventory.branchRoot(scope),
        "stock-adjustments",
        "detail",
      ] as const,

    stockAdjustment: (
      scope: BranchQueryScope,
      id: string | number,
    ) =>
      [
        ...QUERY_KEYS.inventory.stockAdjustmentDetails(scope),
        String(id).trim(),
      ] as const,
  },

  /* ==========================================================================
   * Procurement
   * ==========================================================================
   */

  procurement: {
    root: ["procurement"] as const,

    purchaseOrders: () =>
      [...QUERY_KEYS.procurement.root, "purchase-orders"] as const,

    purchaseOrder: (id: string | number) =>
      [...QUERY_KEYS.procurement.root, "purchase-orders", id] as const,

    goodsReceipts: () =>
      [...QUERY_KEYS.procurement.root, "goods-receipts"] as const,

    goodsReceipt: (id: string | number) =>
      [...QUERY_KEYS.procurement.root, "goods-receipts", id] as const,
  },

  /* ==========================================================================
   * Sales
   * ==========================================================================
   */

  sales: {
    root: ["sales"] as const,

    branchRoot: (scope: BranchQueryScope) =>
      createBranchQueryKey(scope, "sales"),

    lists: (scope: BranchQueryScope) =>
      [...QUERY_KEYS.sales.branchRoot(scope), "list"] as const,

    list: (
      scope: BranchQueryScope,
      params?: ListSalesRequest,
    ) =>
      [
        ...QUERY_KEYS.sales.lists(scope),
        normalizeListSalesRequest(params),
      ] as const,

    detail: (id: string | number) =>
      [...QUERY_KEYS.sales.root, id] as const,

    payments: (saleId: string) =>
      [...QUERY_KEYS.sales.root, saleId, "payments"] as const,

    payment: (paymentId: string) =>
      [...QUERY_KEYS.sales.root, "payments", paymentId] as const,

    receipts: () =>
      [...QUERY_KEYS.sales.root, "receipts"] as const,

    receipt: (
      scope: BranchQueryScope,
      saleId: string,
    ) =>
      [
        ...QUERY_KEYS.sales.branchRoot(scope),
        "receipt",
        saleId.trim(),
      ] as const,

    dashboard: () =>
      [...QUERY_KEYS.sales.root, "dashboard"] as const,

    refunds: () =>
      [...QUERY_KEYS.sales.root, "refunds"] as const,

    refundLookup: (
      scope: BranchQueryScope,
      saleId: string,
    ) =>
      [
        ...QUERY_KEYS.sales.branchRoot(scope),
        "refund-lookup",
        saleId.trim(),
      ] as const,

    availability: (
      scope: BranchQueryScope,
      tillId: string,
      productIds: readonly string[],
    ) =>
      [
        ...QUERY_KEYS.sales.branchRoot(scope),
        "availability",
        tillId.trim(),
        [...new Set(productIds.map((id) => id.trim()).filter(Boolean))].sort(),
      ] as const,

    disabled: (...segments: readonly QueryKeySegment[]) =>
      [...QUERY_KEYS.sales.root, "disabled", ...segments] as const,

    suspended: () =>
      [...QUERY_KEYS.sales.root, "suspended"] as const,

    prescriptions: () =>
      [...QUERY_KEYS.sales.root, "prescriptions"] as const,
  },

  /* ==========================================================================
   * Finance
   * ==========================================================================
   */

  finance: {
    root: ["finance"] as const,

    invoices: () =>
      [...QUERY_KEYS.finance.root, "invoices"] as const,

    invoice: (id: string | number) =>
      [...QUERY_KEYS.finance.root, "invoice", id] as const,

    payments: () =>
      [...QUERY_KEYS.finance.root, "payments"] as const,

    payment: (id: string | number) =>
      [...QUERY_KEYS.finance.root, "payment", id] as const,
  },

  /* ==========================================================================
   * Administration
   * ==========================================================================
   */

  administration: {
    root: ["administration"] as const,

    users: () =>
      [...QUERY_KEYS.administration.root, "users"] as const,

    user: (id: string | number) =>
      [...QUERY_KEYS.administration.root, "user", id] as const,

    roles: () =>
      [...QUERY_KEYS.administration.root, "roles"] as const,

    permissions: () =>
      [...QUERY_KEYS.administration.root, "permissions"] as const,

    branches: () =>
      [...QUERY_KEYS.administration.root, "branches"] as const,

    tenants: () =>
      [...QUERY_KEYS.administration.root, "tenants"] as const,
  },

  /* ==========================================================================
   * Reports
   * ==========================================================================
   */

  reports: {
    root: ["reports"] as const,

    sales: () =>
      [...QUERY_KEYS.reports.root, "sales"] as const,

    inventory: () =>
      [...QUERY_KEYS.reports.root, "inventory"] as const,

    finance: () =>
      [...QUERY_KEYS.reports.root, "finance"] as const,

    procurement: () =>
      [...QUERY_KEYS.reports.root, "procurement"] as const,

    audit: () =>
      [...QUERY_KEYS.reports.root, "audit"] as const,
  },
} as const;

export default QUERY_KEYS;
