/**
 * ============================================================================
 * Hela360 Enterprise Payment Service
 * ============================================================================
 *
 * Service responsible for payment processing.
 *
 * Responsibilities
 * ----------------
 * • Payment CRUD
 * • Receive payments
 * • Allocate payments
 * • Reverse payments
 * • Payment history
 * • Customer payments
 * • Supplier payments
 * • Outstanding balances
 * • Daily cash summary
 * • Payment methods
 *
 * Integrates with:
 *
 * • Sales
 * • Procurement
 * • Customers
 * • Suppliers
 * • Finance
 *
 * ============================================================================
 */

import type { AxiosRequestConfig } from "axios";

import { API_ENDPOINTS } from "@/api/endpoints";
import BaseService from "@/services/base";

import type { ApiResponse } from "@/types/api";

import type { PaginatedResponse } from "@/types/api";
/* ============================================================================
 * Types
 * ============================================================================
 */

export type PaymentMethod =
  | "CASH"
  | "CARD"
  | "MPESA"
  | "BANK_TRANSFER"
  | "CHEQUE"
  | "CREDIT";

export type PaymentStatus =
  | "PENDING"
  | "COMPLETED"
  | "FAILED"
  | "REVERSED"
  | "CANCELLED";

export interface Payment {
  id: string;

  paymentNumber: string;

  reference?: string;

  customerId?: string;

  supplierId?: string;

  saleId?: string;

  purchaseOrderId?: string;

  method: PaymentMethod;

  status: PaymentStatus;

  amount: number;

  paidAt: string;

  notes?: string;

  createdAt: string;

  updatedAt: string;
}

export interface CreatePaymentRequest {
  customerId?: string;

  supplierId?: string;

  saleId?: string;

  purchaseOrderId?: string;

  method: PaymentMethod;

  amount: number;

  reference?: string;

  notes?: string;
}

export interface UpdatePaymentRequest {
  reference?: string;

  notes?: string;
}

export interface PaymentAllocationRequest {
  invoiceId: string;

  amount: number;
}

export interface PaymentSummary {
  totalPayments: number;

  totalAmount: number;

  cash: number;

  card: number;

  mpesa: number;

  bankTransfer: number;
}

/* ============================================================================
 * Payment Service
 * ============================================================================
 */

export class PaymentService extends BaseService<
  Payment,
  CreatePaymentRequest,
  UpdatePaymentRequest
> {
  constructor() {
    super(API_ENDPOINTS.PAYMENTS.ROOT);
  }

  /* ==========================================================================
   * Allocation
   * ==========================================================================
   */

  async allocate(
    paymentId: string,
    payload: PaymentAllocationRequest[],
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<Payment>> {
    const response =
      await this.postRequest<ApiResponse<Payment>>(
        `${this.resource}/${paymentId}/allocate`,
        payload,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Workflow
   * ==========================================================================
   */

  async reverse(
    paymentId: string,
    reason: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<Payment>> {
    const response =
      await this.postRequest<ApiResponse<Payment>>(
        `${this.resource}/${paymentId}/reverse`,
        { reason },
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Customer Payments
   * ==========================================================================
   */

  async customerPayments(
    customerId: string,
    config?: AxiosRequestConfig,
  ): Promise<PaginatedResponse<Payment>> {
    const response =
      await this.getRequest<PaginatedResponse<Payment>>(
        `${API_ENDPOINTS.CUSTOMERS.ROOT}/${customerId}/payments`,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Supplier Payments
   * ==========================================================================
   */

  async supplierPayments(
    supplierId: string,
    config?: AxiosRequestConfig,
  ): Promise<PaginatedResponse<Payment>> {
    const response =
      await this.getRequest<PaginatedResponse<Payment>>(
        `${API_ENDPOINTS.SUPPLIERS.ROOT}/${supplierId}/payments`,
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
  ): Promise<ApiResponse<PaymentSummary>> {
    const response =
      await this.getRequest<ApiResponse<PaymentSummary>>(
        `${this.resource}/daily-summary`,
        {
          ...config,
          params: {
            date,
          },
        },
      );

    return response.data;
  }

  /* ==========================================================================
   * Outstanding Balance
   * ==========================================================================
   */

  async outstandingBalance(
    customerId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<number>> {
    const response =
      await this.getRequest<ApiResponse<number>>(
        `${API_ENDPOINTS.CUSTOMERS.ROOT}/${customerId}/balance`,
        config,
      );

    return response.data;
  }
}

/* ============================================================================
 * Singleton
 * ============================================================================
 */

export const paymentService =
  new PaymentService();

export default paymentService;