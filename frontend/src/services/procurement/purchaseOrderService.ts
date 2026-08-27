/**
 * ============================================================================
 * Hela360 Enterprise Purchase Order Service
 * ============================================================================
 *
 * Service responsible for enterprise purchase order management.
 *
 * Responsibilities
 * ----------------
 * • Purchase order CRUD
 * • Draft management
 * • Supplier ordering
 * • Approval workflow
 * • Purchase order line items
 * • Purchase totals
 * • Receiving status
 * • Purchase history
 * • PDF generation
 * • Emailing purchase orders
 * • Purchase cancellation
 * • Purchase completion
 *
 * Purchase Orders form the backbone of the procurement module and integrate
 * Suppliers, Inventory, Finance and Goods Receipt.
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

export type PurchaseOrderStatus =
  | "DRAFT"
  | "SUBMITTED"
  | "APPROVED"
  | "ORDERED"
  | "PARTIALLY_RECEIVED"
  | "RECEIVED"
  | "CLOSED"
  | "CANCELLED";

export interface PurchaseOrderItem {
  id: string;

  productId: string;

  sku: string;

  productName: string;

  quantity: number;

  receivedQuantity: number;

  unitCost: number;

  taxAmount: number;

  lineTotal: number;
}

export interface PurchaseOrder {
  id: string;

  orderNumber: string;

  supplierId: string;

  supplierName: string;

  orderDate: string;

  expectedDeliveryDate?: string;

  status: PurchaseOrderStatus;

  subtotal: number;

  taxTotal: number;

  discountTotal: number;

  grandTotal: number;

  remarks?: string;

  items: PurchaseOrderItem[];

  createdAt: string;

  updatedAt: string;
}

export interface CreatePurchaseOrderRequest {
  supplierId: string;

  expectedDeliveryDate?: string;

  remarks?: string;

  items: Omit<
    PurchaseOrderItem,
    | "id"
    | "receivedQuantity"
    | "lineTotal"
    | "productName"
    | "sku"
  >[];
}

export interface UpdatePurchaseOrderRequest {
  expectedDeliveryDate?: string;

  remarks?: string;

  items?: PurchaseOrderItem[];
}

export interface ApprovalRequest {
  remarks?: string;
}

export interface CancellationRequest {
  reason: string;
}

export interface PurchaseSummary {
  totalItems: number;

  subtotal: number;

  taxTotal: number;

  discountTotal: number;

  grandTotal: number;
}

/* ============================================================================
 * Purchase Order Service
 * ============================================================================
 */

export class PurchaseOrderService extends BaseService<
  PurchaseOrder,
  CreatePurchaseOrderRequest,
  UpdatePurchaseOrderRequest
> {
  constructor() {
    super(API_ENDPOINTS.PURCHASE_ORDERS.ROOT);
  }

  /* ==========================================================================
   * Workflow
   * ==========================================================================
   */

  async submit(
    purchaseOrderId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.postRequest<ApiResponse<void>>(
        `${this.resource}/${purchaseOrderId}/submit`,
        undefined,
        config,
      );

    return response.data;
  }

  async approve(
    purchaseOrderId: string,
    payload?: ApprovalRequest,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.postRequest<ApiResponse<void>>(
        `${this.resource}/${purchaseOrderId}/approve`,
        payload,
        config,
      );

    return response.data;
  }

  async cancel(
    purchaseOrderId: string,
    payload: CancellationRequest,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.postRequest<ApiResponse<void>>(
        `${this.resource}/${purchaseOrderId}/cancel`,
        payload,
        config,
      );

    return response.data;
  }

  async close(
    purchaseOrderId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.postRequest<ApiResponse<void>>(
        `${this.resource}/${purchaseOrderId}/close`,
        undefined,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Receiving
   * ==========================================================================
   */

  async receivingProgress(
    purchaseOrderId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<PurchaseOrder>> {
    const response =
      await this.getRequest<ApiResponse<PurchaseOrder>>(
        `${this.resource}/${purchaseOrderId}/receiving`,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Summary
   * ==========================================================================
   */

  async summary(
    purchaseOrderId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<PurchaseSummary>> {
    const response =
      await this.getRequest<ApiResponse<PurchaseSummary>>(
        `${this.resource}/${purchaseOrderId}/summary`,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Documents
   * ==========================================================================
   */

  async print(
    purchaseOrderId: string,
    config?: AxiosRequestConfig,
  ): Promise<Blob> {
    const response =
      await this.download(
        `${this.resource}/${purchaseOrderId}/print`,
        {
          ...config,
          responseType: "blob",
        },
      );

    return response.data;
  }

  async email(
    purchaseOrderId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.postRequest<ApiResponse<void>>(
        `${this.resource}/${purchaseOrderId}/email`,
        undefined,
        config,
      );

    return response.data;
  }
}

/* ============================================================================
 * Singleton
 * ============================================================================
 */

export const purchaseOrderService =
  new PurchaseOrderService();

export default purchaseOrderService;