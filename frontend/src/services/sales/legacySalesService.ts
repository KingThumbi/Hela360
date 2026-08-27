/**
 * ============================================================================
 * Hela360 Enterprise Sales Service
 * ============================================================================
 *
 * Service responsible for Point of Sale (POS) operations.
 *
 * Responsibilities
 * ----------------
 * • Sales CRUD
 * • POS checkout
 * • Quotes
 * • Sale completion
 * • Sale cancellation
 * • Receipt generation
 * • Payments
 * • Discounts
 * • Taxes
 * • Customer sales
 * • Branch sales
 * • Daily summaries
 * • Cashier summaries
 *
 * This service integrates:
 *
 * • Inventory
 * • Customers
 * • Finance
 * • Prescriptions
 * • Receipts
 * • Refunds
 *
 * ============================================================================
 */

import type { AxiosRequestConfig } from "axios";

import { API_ENDPOINTS } from "@/api/endpoints";

import BaseService from "@/services/base";

import type { ApiResponse } from "@/types/api";

import type { PaginatedResponse } from "@/types/api";
import type {
  Sale,
  SalePayment,
} from "@/types/entities";

import type {
  CreateSaleRequest,
  UpdateSaleRequest,
} from "@/types/requests";

import type {
  CashierSummary,
  DailySalesSummary,
} from "@/types/responses";

/* ============================================================================
 * Sales Service
 * ============================================================================
 */

export class SalesService extends BaseService<
  Sale,
  CreateSaleRequest,
  UpdateSaleRequest
> {
  constructor() {
    super(API_ENDPOINTS.SALES.ROOT);
  }

  /* ==========================================================================
   * Checkout
   * ==========================================================================
   */

  async checkout(
    payload: CreateSaleRequest,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<Sale>> {
    const response =
      await this.postRequest<ApiResponse<Sale>>(
        `${this.resource}/checkout`,
        payload,
        config,
      );

    return response.data;
  }

  async complete(
    saleId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<Sale>> {
    const response =
      await this.postRequest<ApiResponse<Sale>>(
        `${this.resource}/${saleId}/complete`,
        undefined,
        config,
      );

    return response.data;
  }

  async void(
    saleId: string,
    reason: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.postRequest<ApiResponse<void>>(
        `${this.resource}/${saleId}/void`,
        { reason },
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Payments
   * ==========================================================================
   */

  async payments(
    saleId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<SalePayment[]>> {
    const response =
      await this.getRequest<ApiResponse<SalePayment[]>>(
        `${this.resource}/${saleId}/payments`,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Receipt
   * ==========================================================================
   */

  async receipt(
    saleId: string,
    config?: AxiosRequestConfig,
  ): Promise<Blob> {
    const response =
      await this.download(
        `${this.resource}/${saleId}/receipt`,
        {
          ...config,
          responseType: "blob",
        },
      );

    return response.data;
  }

  /* ==========================================================================
   * Customer Sales
   * ==========================================================================
   */

  async customerSales(
    customerId: string,
    config?: AxiosRequestConfig,
  ): Promise<PaginatedResponse<Sale>> {
    const response =
      await this.getRequest<
        PaginatedResponse<Sale>
      >(
        `${API_ENDPOINTS.CUSTOMERS.ROOT}/${customerId}/sales`,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Daily Summary
   * ==========================================================================
   */

  async dailySummary(
    date: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<DailySalesSummary>> {
    const response =
      await this.getRequest<
        ApiResponse<DailySalesSummary>
      >(
        `${this.resource}/daily-summary`,
        {
          ...config,
          params: { date },
        },
      );

    return response.data;
  }

  async cashierSummary(
    cashierId: string,
    date: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<CashierSummary>> {
    const response =
      await this.getRequest<
        ApiResponse<CashierSummary>
      >(
        `${this.resource}/cashiers/${cashierId}/summary`,
        {
          ...config,
          params: { date },
        },
      );

    return response.data;
  }
}

/* ============================================================================
 * Singleton
 * ============================================================================
 */

export const salesService =
  new SalesService();

export default salesService;
