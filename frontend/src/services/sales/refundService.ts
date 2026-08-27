/**
 * ============================================================================
 * Hela360 Enterprise Refund Service
 * ============================================================================
 *
 * Service responsible for sales refunds.
 *
 * Responsibilities
 * ----------------
 * • Full refunds
 * • Partial refunds
 * • Refund validation
 * • Inventory restoration
 * • Payment reversal
 * • Approval workflow
 * • Refund history
 * • Refund receipts
 * • Refund cancellation
 * • Refund reporting
 *
 * Integrates with:
 *
 * • Sales
 * • Inventory
 * • Finance
 * • Customers
 * • Audit
 *
 * ============================================================================
 */

import type { AxiosRequestConfig } from "axios";

import { API_ENDPOINTS } from "@/api/endpoints";

import BaseService from "@/services/base";

import type { ApiResponse } from "@/types/api";

/* ============================================================================
 * Types
 * ============================================================================
 */

export type RefundStatus =
  | "PENDING"
  | "APPROVED"
  | "COMPLETED"
  | "REJECTED"
  | "CANCELLED";

export interface RefundItem {
  id: string;

  saleItemId: string;

  productId: string;

  productName: string;

  quantity: number;

  unitPrice: number;

  refundAmount: number;

  reason?: string;
}

export interface Refund {
  id: string;

  refundNumber: string;

  saleId: string;

  customerId?: string;

  cashierId: string;

  approvedBy?: string;

  status: RefundStatus;

  reason: string;

  totalAmount: number;

  items: RefundItem[];

  createdAt: string;

  updatedAt: string;
}

export interface CreateRefundRequest {
  saleId: string;

  reason: string;

  items: {
    saleItemId: string;

    quantity: number;

    reason?: string;
  }[];
}

export interface RefundApprovalRequest {
  remarks?: string;
}

export interface RefundSummary {
  totalRefunds: number;

  totalAmount: number;

  itemsRefunded: number;
}

export interface RefundValidation {
  valid: boolean;

  refundable: boolean;

  message?: string;
}

/* ============================================================================
 * Refund Service
 * ============================================================================
 */

export class RefundService extends BaseService<
  Refund,
  CreateRefundRequest
> {
  constructor() {
    super(API_ENDPOINTS.REFUNDS.ROOT);
  }

  /* ==========================================================================
   * Validation
   * ==========================================================================
   */

  async validate(
    saleId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<RefundValidation>> {
    const response =
      await this.getRequest<ApiResponse<RefundValidation>>(
        `${this.resource}/validate/${saleId}`,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Workflow
   * ==========================================================================
   */

  async approve(
    refundId: string,
    payload?: RefundApprovalRequest,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<Refund>> {
    const response =
      await this.postRequest<ApiResponse<Refund>>(
        `${this.resource}/${refundId}/approve`,
        payload,
        config,
      );

    return response.data;
  }

  async reject(
    refundId: string,
    reason: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<Refund>> {
    const response =
      await this.postRequest<ApiResponse<Refund>>(
        `${this.resource}/${refundId}/reject`,
        { reason },
        config,
      );

    return response.data;
  }

  async complete(
    refundId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<Refund>> {
    const response =
      await this.postRequest<ApiResponse<Refund>>(
        `${this.resource}/${refundId}/complete`,
        undefined,
        config,
      );

    return response.data;
  }

  async cancel(
    refundId: string,
    reason: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<Refund>> {
    const response =
      await this.postRequest<ApiResponse<Refund>>(
        `${this.resource}/${refundId}/cancel`,
        { reason },
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Inventory
   * ==========================================================================
   */

  async inventoryImpact(
    refundId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<unknown>> {
    const response =
      await this.getRequest<ApiResponse<unknown>>(
        `${this.resource}/${refundId}/inventory`,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Payments
   * ==========================================================================
   */

  async paymentReversal(
    refundId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<unknown>> {
    const response =
      await this.getRequest<ApiResponse<unknown>>(
        `${this.resource}/${refundId}/payment`,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Summary
   * ==========================================================================
   */

  async summary(
    refundId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<RefundSummary>> {
    const response =
      await this.getRequest<ApiResponse<RefundSummary>>(
        `${this.resource}/${refundId}/summary`,
        config,
      );

      return response.data;
  }

  /* ==========================================================================
   * Receipt
   * ==========================================================================
   */

  async receipt(
    refundId: string,
    config?: AxiosRequestConfig,
  ): Promise<Blob> {
    const response =
      await this.download(
        `${this.resource}/${refundId}/receipt`,
        {
          ...config,
          responseType: "blob",
        },
      );

    return response.data;
  }

  /* ==========================================================================
   * History
   * ==========================================================================
   */

  async history(
    saleId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<Refund[]>> {
    const response =
      await this.getRequest<ApiResponse<Refund[]>>(
        `${API_ENDPOINTS.SALES.ROOT}/${saleId}/refunds`,
        config,
      );

    return response.data;
  }
}

/* ============================================================================
 * Singleton
 * ============================================================================
 */

export const refundService = new RefundService();

export default refundService;