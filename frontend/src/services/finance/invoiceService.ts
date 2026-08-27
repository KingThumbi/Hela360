/**
 * ============================================================================
 * Hela360 Enterprise Invoice Service
 * ============================================================================
 *
 * Service responsible for invoice management.
 *
 * Responsibilities
 * ----------------
 * • Invoice CRUD
 * • Customer invoices
 * • Supplier invoices
 * • Invoice posting
 * • Invoice cancellation
 * • Invoice settlement
 * • Invoice payments
 * • Invoice PDF
 * • Invoice history
 * • Outstanding invoices
 *
 * Integrates with:
 *
 * • Customers
 * • Suppliers
 * • Payments
 * • Sales
 * • Procurement
 *
 * ============================================================================
 */

import type { RequestOptions } from "@/services/base";

import { API_ENDPOINTS } from "@/api/endpoints";

import BaseService from "@/services/base";

import type { ApiResponse } from "@/types/api";

import type { PaginatedResponse } from "@/types/api";
/* ============================================================================
 * Types
 * ============================================================================
 */

export type InvoiceStatus =
  | "DRAFT"
  | "POSTED"
  | "PARTIALLY_PAID"
  | "PAID"
  | "OVERDUE"
  | "VOIDED";

export interface InvoiceItem {
  id: string;

  description: string;

  quantity: number;

  unitPrice: number;

  discount: number;

  tax: number;

  total: number;
}

export interface Invoice {
  id: string;

  invoiceNumber: string;

  customerId?: string;

  supplierId?: string;

  issueDate: string;

  dueDate: string;

  status: InvoiceStatus;

  subtotal: number;

  discountTotal: number;

  taxTotal: number;

  grandTotal: number;

  balance: number;

  items: InvoiceItem[];

  createdAt: string;

  updatedAt: string;
}

export interface CreateInvoiceRequest {
  customerId?: string;

  supplierId?: string;

  dueDate: string;

  items: {
    description: string;

    quantity: number;

    unitPrice: number;

    discount?: number;

    tax?: number;
  }[];
}

export interface UpdateInvoiceRequest {
  dueDate?: string;

  status?: InvoiceStatus;
}

export interface InvoiceSummary {
  totalInvoices: number;

  totalAmount: number;

  outstandingAmount: number;

  paidAmount: number;

  overdueAmount: number;
}

/* ============================================================================
 * Invoice Service
 * ============================================================================
 */

export class InvoiceService extends BaseService<
  Invoice,
  CreateInvoiceRequest,
  UpdateInvoiceRequest
> {
  constructor() {
    super(API_ENDPOINTS.INVOICES.ROOT);
  }

  /* ==========================================================================
   * Workflow
   * ==========================================================================
   */

  async post(
    invoiceId: string,
    config?: RequestOptions,
  ): Promise<ApiResponse<Invoice>> {
    const response =
      await this.postRequest<ApiResponse<Invoice>>(
          this.resourceUrl(invoiceId, "post"),
          undefined,
          config,
  );

return response.data;  }

  async void(
    invoiceId: string,
    reason: string,
    config?: RequestOptions,
  ): Promise<ApiResponse<Invoice>> {
    const response =
      await this.postRequest<ApiResponse<Invoice>>(
        this.resourceUrl(invoiceId, "void"),
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
    invoiceId: string,
    config?: RequestOptions,
  ): Promise<ApiResponse<unknown[]>> {
    const response =
      await this.getRequest<ApiResponse<unknown[]>>(
        `${this.resource}/${invoiceId}/payments`,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Customer Invoices
   * ==========================================================================
   */

  async customerInvoices(
    customerId: string,
    config?: RequestOptions,
  ): Promise<PaginatedResponse<Invoice>> {
    const response =
      await this.getRequest<PaginatedResponse<Invoice>>(
        `${API_ENDPOINTS.CUSTOMERS.ROOT}/${customerId}/invoices`,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Supplier Invoices
   * ==========================================================================
   */

  async supplierInvoices(
    supplierId: string,
    config?: RequestOptions,
  ): Promise<PaginatedResponse<Invoice>> {
    const response =
      await this.getRequest<PaginatedResponse<Invoice>>(
        `${API_ENDPOINTS.SUPPLIERS.ROOT}/${supplierId}/invoices`,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Outstanding
   * ==========================================================================
   */

  async outstanding(
    config?: RequestOptions,
  ): Promise<ApiResponse<Invoice[]>> {
    const response =
      await this.getRequest<ApiResponse<Invoice[]>>(
        `${this.resource}/outstanding`,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Summary
   * ==========================================================================
   */

  async summary(
    config?: RequestOptions,
  ): Promise<ApiResponse<InvoiceSummary>> {
    const response =
      await this.getRequest<ApiResponse<InvoiceSummary>>(
        `${this.resource}/summary`,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * PDF
   * ==========================================================================
   */

  async pdf(
    invoiceId: string,
    config?: RequestOptions,
  ): Promise<Blob> {
    const response =
      await this.download(
        `${this.resource}/${invoiceId}/pdf`,
        {
          ...config,
          responseType: "blob",
        },
      );

    return response.data;
  }
}

/* ============================================================================
 * Singleton
 * ============================================================================
 */

export const invoiceService = new InvoiceService();

export default invoiceService;