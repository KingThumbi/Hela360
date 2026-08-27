/**
 * ============================================================================
 * Hela360 Sales Service Facade
 * ============================================================================
 *
 * Canonical public service boundary for verified Sales backend operations.
 *
 * ============================================================================
 */

import type { AxiosRequestConfig } from "axios";

import { API_ENDPOINTS } from "@/api/endpoints";

import BaseService from "@/services/base";

import type {
  Sale,
  SaleRefund,
} from "@/types/entities";

import type {
  CreateSaleRequest,
  ListSalesRequest,
  RefundSaleRequest,
} from "@/types/requests";
import type {
  PosProductAvailability,
  SaleSummary,
  SaleReceipt,
} from "@/types/responses";
import type {
  PaginatedResponse,
} from "@/types/api";

type RefundSaleBody =
  Omit<RefundSaleRequest, "sale_id">;

interface SaleItemResponse {
  ok: true;

  item: Sale;

  message?: string;

  shift_id?: string;
}

interface SaleRefundResponse {
  ok: true;

  message?: string;

  refund: SaleRefund;
}

interface SaleReceiptResponse {
  ok: true;

  receipt: SaleReceipt;
}

interface SaleListResponse {
  ok: true;

  items: SaleSummary[];

  pagination: PaginatedResponse<SaleSummary>["pagination"];
}

interface PosProductAvailabilityResponse {
  ok: true;

  items: PosProductAvailability[];
}

function salesListParams(
  params?: ListSalesRequest,
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

  const status = params?.status?.trim();
  if (status) {
    query.status = status;
  }

  const customerId = params?.customer_id?.trim();
  if (customerId) {
    query.customer_id = customerId;
  }

  return query;
}

/* ============================================================================
 * Sales Service
 * ============================================================================
 */

export class SalesService extends BaseService<
  Sale,
  CreateSaleRequest
> {
  constructor() {
    super(API_ENDPOINTS.SALES.ROOT);
  }

  async createSale(
    payload: CreateSaleRequest,
    config?: AxiosRequestConfig,
  ): Promise<Sale> {
    const response =
      await this.postRequest<SaleItemResponse>(
        this.resourceUrl("checkout"),
        payload,
        config,
      );

    return response.data.item;
  }

  async listSales(
    params?: ListSalesRequest,
    config?: AxiosRequestConfig,
  ): Promise<PaginatedResponse<SaleSummary>> {
    const response =
      await this.getRequest<SaleListResponse>(
        this.resourceUrl(),
        {
          ...config,
          params: salesListParams(params),
        },
      );

    return {
      items: response.data.items,
      pagination: response.data.pagination,
    };
  }

  async listPosProductAvailability(
    params: {
      till_id: string;
      product_ids: string[];
    },
    config?: AxiosRequestConfig,
  ): Promise<PosProductAvailability[]> {
    const response =
      await this.getRequest<PosProductAvailabilityResponse>(
        API_ENDPOINTS.SALES.AVAILABILITY,
        {
          ...config,
          params: {
            till_id: params.till_id,
            product_ids: params.product_ids.join(","),
          },
        },
      );

    return response.data.items;
  }

  async refundSale(
    saleId: string,
    payload: RefundSaleBody,
    config?: AxiosRequestConfig,
  ): Promise<SaleRefund> {
    const response =
      await this.postRequest<SaleRefundResponse>(
        this.resourceUrl(saleId, "refund"),
        payload,
        config,
      );

    return response.data.refund;
  }

  async getRefundableSale(
    saleId: string,
    config?: AxiosRequestConfig,
  ): Promise<Sale> {
    const response =
      await this.getRequest<SaleItemResponse>(
        this.resourceUrl(saleId),
        config,
      );

    return response.data.item;
  }

  async getReceipt(
    saleId: string,
    config?: AxiosRequestConfig,
  ): Promise<SaleReceipt> {
    const response =
      await this.getRequest<SaleReceiptResponse>(
        API_ENDPOINTS.SALES.RECEIPT(saleId),
        config,
      );

    return response.data.receipt;
  }
}

/* ============================================================================
 * Singleton
 * ============================================================================
 */

export const salesService =
  new SalesService();

export default salesService;
