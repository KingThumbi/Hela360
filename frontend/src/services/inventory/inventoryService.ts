import type { AxiosRequestConfig } from "axios";

import { API_ENDPOINTS } from "@/api/endpoints";
import BaseService from "@/services/base";
import type {
  AddDiscoveredStockCountItemRequest,
  CreateGoodsReceiptRequest,
  CreateStockAdjustmentFromCountRequest,
  CreateStockAdjustmentRequest,
  CreateStockCountRequest,
  ListGoodsReceiptsRequest,
  ListInventoryMovementsRequest,
  ListInventoryRequest,
  ListStockAdjustmentsRequest,
  ListStockCountsRequest,
  UpdateStockCountItemRequest,
} from "@/types/requests";
import type {
  GoodsReceipt,
  StockAdjustment,
  StockCount,
} from "@/types/entities";
import type {
  GoodsReceiptSummary,
  InventoryBatchSummary,
  InventoryMovementSummary,
  InventoryStockSummary,
  StockAdjustmentListItem,
  StockCountListItem,
} from "@/types/responses";
import type {
  PaginatedResponse,
} from "@/types/api";

interface InventoryListResponse {
  ok: true;

  items: InventoryStockSummary[];

  pagination: PaginatedResponse<InventoryStockSummary>["pagination"];
}

interface InventoryBatchesResponse {
  ok: true;

  stock: InventoryStockSummary;

  items: InventoryBatchSummary[];
}

interface InventoryMovementListResponse {
  ok: true;

  items: InventoryMovementSummary[];

  pagination: PaginatedResponse<InventoryMovementSummary>["pagination"];
}

interface GoodsReceiptResponse {
  ok: true;

  item: GoodsReceipt;
}

interface GoodsReceiptListResponse {
  ok: true;

  items: GoodsReceiptSummary[];

  pagination: PaginatedResponse<GoodsReceiptSummary>["pagination"];
}

interface StockCountResponse {
  ok: true;

  item: StockCount;
}

interface StockCountListResponse {
  ok: true;

  items: StockCountListItem[];

  pagination: PaginatedResponse<StockCountListItem>["pagination"];
}

interface StockAdjustmentResponse {
  ok: true;

  item: StockAdjustment;
}

interface StockAdjustmentListResponse {
  ok: true;

  items: StockAdjustmentListItem[];

  pagination: PaginatedResponse<StockAdjustmentListItem>["pagination"];
}

function inventoryListParams(
  params?: ListInventoryRequest,
): Record<string, string | number> {
  const query: Record<string, string | number> = {};

  if (params?.page !== undefined) {
    query.page = params.page;
  }

  if (params?.per_page !== undefined) {
    query.per_page = params.per_page;
  }

  const search = params?.search?.trim();
  if (search) {
    query.search = search;
  }

  const warehouseId = params?.warehouse_id?.trim();
  if (warehouseId) {
    query.warehouse_id = warehouseId;
  }

  const stockStatus = params?.stock_status?.trim();
  if (stockStatus) {
    query.stock_status = stockStatus;
  }

  const expiresBefore = params?.expires_before?.trim();
  if (expiresBefore) {
    query.expires_before = expiresBefore;
  }

  return query;
}

function movementListParams(
  params?: ListInventoryMovementsRequest,
): Record<string, string | number> {
  const query: Record<string, string | number> = {};

  if (params?.page !== undefined) {
    query.page = params.page;
  }

  if (params?.per_page !== undefined) {
    query.per_page = params.per_page;
  }

  const dateFrom = params?.date_from?.trim();
  if (dateFrom) {
    query.date_from = dateFrom;
  }

  const dateTo = params?.date_to?.trim();
  if (dateTo) {
    query.date_to = dateTo;
  }

  const productId = params?.product_id?.trim();
  if (productId) {
    query.product_id = productId;
  }

  const warehouseId = params?.warehouse_id?.trim();
  if (warehouseId) {
    query.warehouse_id = warehouseId;
  }

  const movementType = params?.movement_type?.trim();
  if (movementType) {
    query.movement_type = movementType;
  }

  const referenceType = params?.reference_type?.trim();
  if (referenceType) {
    query.reference_type = referenceType;
  }

  const referenceId = params?.reference_id?.trim();
  if (referenceId) {
    query.reference_id = referenceId;
  }

  return query;
}

function goodsReceiptListParams(
  params?: ListGoodsReceiptsRequest,
): Record<string, string | number> {
  const query: Record<string, string | number> = {};

  if (params?.page !== undefined) {
    query.page = params.page;
  }

  if (params?.per_page !== undefined) {
    query.per_page = params.per_page;
  }

  const search = params?.search?.trim();
  if (search) {
    query.search = search;
  }

  const dateFrom = params?.date_from?.trim();
  if (dateFrom) {
    query.date_from = dateFrom;
  }

  const dateTo = params?.date_to?.trim();
  if (dateTo) {
    query.date_to = dateTo;
  }

  const warehouseId = params?.warehouse_id?.trim();
  if (warehouseId) {
    query.warehouse_id = warehouseId;
  }

  const supplierId = params?.supplier_id?.trim();
  if (supplierId) {
    query.supplier_id = supplierId;
  }

  return query;
}

function stockCountListParams(
  params?: ListStockCountsRequest,
): Record<string, string | number> {
  const query: Record<string, string | number> = {};

  if (params?.page !== undefined) {
    query.page = params.page;
  }

  if (params?.per_page !== undefined) {
    query.per_page = params.per_page;
  }

  const status = params?.status?.trim();
  if (status) {
    query.status = status;
  }

  const warehouseId = params?.warehouse_id?.trim();
  if (warehouseId) {
    query.warehouse_id = warehouseId;
  }

  const dateFrom = params?.date_from?.trim();
  if (dateFrom) {
    query.date_from = dateFrom;
  }

  const dateTo = params?.date_to?.trim();
  if (dateTo) {
    query.date_to = dateTo;
  }

  return query;
}

function stockAdjustmentListParams(
  params?: ListStockAdjustmentsRequest,
): Record<string, string | number> {
  const query: Record<string, string | number> = {};

  if (params?.page !== undefined) {
    query.page = params.page;
  }

  if (params?.per_page !== undefined) {
    query.per_page = params.per_page;
  }

  const warehouseId = params?.warehouse_id?.trim();
  if (warehouseId) {
    query.warehouse_id = warehouseId;
  }

  const reasonCode = params?.reason_code?.trim();
  if (reasonCode) {
    query.reason_code = reasonCode;
  }

  const sourceType = params?.source_type?.trim();
  if (sourceType) {
    query.source_type = sourceType;
  }

  const dateFrom = params?.date_from?.trim();
  if (dateFrom) {
    query.date_from = dateFrom;
  }

  const dateTo = params?.date_to?.trim();
  if (dateTo) {
    query.date_to = dateTo;
  }

  return query;
}

export class InventoryService extends BaseService<InventoryStockSummary> {
  constructor() {
    super(API_ENDPOINTS.INVENTORY.ROOT);
  }

  async listStock(
    params?: ListInventoryRequest,
    config?: AxiosRequestConfig,
  ): Promise<PaginatedResponse<InventoryStockSummary>> {
    const response = await this.getRequest<InventoryListResponse>(
      this.resourceUrl(),
      {
        ...config,
        params: inventoryListParams(params),
      },
    );

    return {
      items: response.data.items,
      pagination: response.data.pagination,
    };
  }

  async getStockBatches(
    stockBalanceId: string,
    config?: AxiosRequestConfig,
  ): Promise<InventoryBatchesResponse> {
    const response = await this.getRequest<InventoryBatchesResponse>(
      API_ENDPOINTS.INVENTORY.STOCK_BATCHES(stockBalanceId),
      config,
    );

    return response.data;
  }

  async listMovements(
    params?: ListInventoryMovementsRequest,
    config?: AxiosRequestConfig,
  ): Promise<PaginatedResponse<InventoryMovementSummary>> {
    const response = await this.getRequest<InventoryMovementListResponse>(
      API_ENDPOINTS.INVENTORY.MOVEMENTS,
      {
        ...config,
        params: movementListParams(params),
      },
    );

    return {
      items: response.data.items,
      pagination: response.data.pagination,
    };
  }

  async createGoodsReceipt(
    payload: CreateGoodsReceiptRequest,
    config?: AxiosRequestConfig,
  ): Promise<GoodsReceipt> {
    const response = await this.postRequest<GoodsReceiptResponse>(
      API_ENDPOINTS.INVENTORY.GOODS_RECEIPTS,
      payload,
      config,
    );

    return response.data.item;
  }

  async listGoodsReceipts(
    params?: ListGoodsReceiptsRequest,
    config?: AxiosRequestConfig,
  ): Promise<PaginatedResponse<GoodsReceiptSummary>> {
    const response = await this.getRequest<GoodsReceiptListResponse>(
      API_ENDPOINTS.INVENTORY.GOODS_RECEIPTS,
      {
        ...config,
        params: goodsReceiptListParams(params),
      },
    );

    return {
      items: response.data.items,
      pagination: response.data.pagination,
    };
  }

  async getGoodsReceipt(
    id: string,
    config?: AxiosRequestConfig,
  ): Promise<GoodsReceipt> {
    const response = await this.getRequest<GoodsReceiptResponse>(
      API_ENDPOINTS.INVENTORY.GOODS_RECEIPT(id),
      config,
    );

    return response.data.item;
  }

  async createStockCount(
    payload: CreateStockCountRequest,
    config?: AxiosRequestConfig,
  ): Promise<StockCount> {
    const response = await this.postRequest<StockCountResponse>(
      API_ENDPOINTS.INVENTORY.STOCK_COUNTS,
      payload,
      config,
    );

    return response.data.item;
  }

  async listStockCounts(
    params?: ListStockCountsRequest,
    config?: AxiosRequestConfig,
  ): Promise<PaginatedResponse<StockCountListItem>> {
    const response = await this.getRequest<StockCountListResponse>(
      API_ENDPOINTS.INVENTORY.STOCK_COUNTS,
      {
        ...config,
        params: stockCountListParams(params),
      },
    );

    return {
      items: response.data.items,
      pagination: response.data.pagination,
    };
  }

  async getStockCount(
    id: string,
    config?: AxiosRequestConfig,
  ): Promise<StockCount> {
    const response = await this.getRequest<StockCountResponse>(
      API_ENDPOINTS.INVENTORY.STOCK_COUNT(id),
      config,
    );

    return response.data.item;
  }

  async addDiscoveredStockCountItem(
    countId: string,
    payload: AddDiscoveredStockCountItemRequest,
    config?: AxiosRequestConfig,
  ): Promise<StockCount> {
    const response = await this.postRequest<StockCountResponse>(
      API_ENDPOINTS.INVENTORY.DISCOVERED_STOCK_COUNT_ITEM(countId),
      payload,
      config,
    );

    return response.data.item;
  }

  async updateStockCountItem(
    countId: string,
    itemId: string,
    payload: UpdateStockCountItemRequest,
    config?: AxiosRequestConfig,
  ): Promise<StockCount> {
    const response = await this.putRequest<StockCountResponse>(
      API_ENDPOINTS.INVENTORY.STOCK_COUNT_ITEM(countId, itemId),
      payload,
      config,
    );

    return response.data.item;
  }

  async confirmStockCountNoStock(
    countId: string,
    productId: string,
    config?: AxiosRequestConfig,
  ): Promise<StockCount> {
    const response = await this.postRequest<StockCountResponse>(
      API_ENDPOINTS.INVENTORY.CONFIRM_STOCK_COUNT_NO_STOCK(
        countId,
        productId,
      ),
      {},
      config,
    );

    return response.data.item;
  }

  async completeStockCount(
    id: string,
    config?: AxiosRequestConfig,
  ): Promise<StockCount> {
    const response = await this.postRequest<StockCountResponse>(
      API_ENDPOINTS.INVENTORY.COMPLETE_STOCK_COUNT(id),
      {},
      config,
    );

    return response.data.item;
  }

  async cancelStockCount(
    id: string,
    config?: AxiosRequestConfig,
  ): Promise<StockCount> {
    const response = await this.postRequest<StockCountResponse>(
      API_ENDPOINTS.INVENTORY.CANCEL_STOCK_COUNT(id),
      {},
      config,
    );

    return response.data.item;
  }

  async createStockAdjustment(
    payload: CreateStockAdjustmentRequest,
    config?: AxiosRequestConfig,
  ): Promise<StockAdjustment> {
    const response = await this.postRequest<StockAdjustmentResponse>(
      API_ENDPOINTS.INVENTORY.STOCK_ADJUSTMENTS,
      payload,
      config,
    );

    return response.data.item;
  }

  async createStockAdjustmentFromCount(
    countId: string,
    payload: CreateStockAdjustmentFromCountRequest,
    config?: AxiosRequestConfig,
  ): Promise<StockAdjustment> {
    const response = await this.postRequest<StockAdjustmentResponse>(
      API_ENDPOINTS.INVENTORY.STOCK_ADJUSTMENT_FROM_COUNT(countId),
      payload,
      config,
    );

    return response.data.item;
  }

  async listStockAdjustments(
    params?: ListStockAdjustmentsRequest,
    config?: AxiosRequestConfig,
  ): Promise<PaginatedResponse<StockAdjustmentListItem>> {
    const response = await this.getRequest<StockAdjustmentListResponse>(
      API_ENDPOINTS.INVENTORY.STOCK_ADJUSTMENTS,
      {
        ...config,
        params: stockAdjustmentListParams(params),
      },
    );

    return {
      items: response.data.items,
      pagination: response.data.pagination,
    };
  }

  async getStockAdjustment(
    id: string,
    config?: AxiosRequestConfig,
  ): Promise<StockAdjustment> {
    const response = await this.getRequest<StockAdjustmentResponse>(
      API_ENDPOINTS.INVENTORY.STOCK_ADJUSTMENT(id),
      config,
    );

    return response.data.item;
  }
}

export const inventoryService = new InventoryService();

export default inventoryService;
