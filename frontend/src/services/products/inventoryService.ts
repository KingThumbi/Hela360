/**
 * ============================================================================
 * Hela360 Enterprise Inventory Service
 * ============================================================================
 *
 * Service responsible for enterprise inventory management.
 *
 * Responsibilities
 * ----------------
 * • Inventory CRUD
 * • Stock lookup
 * • Stock movements
 * • Batch management
 * • Lot tracking
 * • Stock adjustments
 * • Branch transfers
 * • Stock reservations
 * • Stock availability
 * • Cycle counting
 * • Inventory valuation
 * • Reorder monitoring
 * • Expiry monitoring
 *
 * Inventory is the operational core of Hela360 and is shared by Procurement,
 * Sales, POS, Warehouse, Reporting and Finance.
 *
 * ============================================================================
 */

import type { AxiosRequestConfig } from "axios";

import { API_ENDPOINTS } from "@/api/endpoints";

import BaseService from "@/services/base";

import type { ApiResponse } from "@/types/api";

import type { PaginatedResponse } from "@/types/api";

import type {
  InventoryItem,
  InventoryMovement,
} from "@/types/entities";

export interface InventoryAdjustmentRequest {
  quantity: number;

  reason: string;

  remarks?: string;
}

export interface BranchTransferRequest {
  destinationBranchId: string;

  quantity: number;

  remarks?: string;
}

export interface ReservationRequest {
  quantity: number;

  reference: string;
}

export interface ReleaseReservationRequest {
  reference: string;
}

export interface Batch {
  id: string;

  batchNumber: string;

  expiryDate?: string;

  quantity: number;

  costPrice: number;
}

export interface InventoryValuation {
  quantity: number;

  averageCost: number;

  totalValue: number;
}

/* ============================================================================
 * Inventory Service
 * ============================================================================
 */

export class InventoryService extends BaseService<
  InventoryItem
> {
  constructor() {
    super(API_ENDPOINTS.INVENTORY.ROOT);
  }

  /* ==========================================================================
   * Lookup
   * ==========================================================================
   */

  /**
   * Returns inventory for a product.
   */
  async byProduct(
    productId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<InventoryItem>> {
    const response =
      await this.getRequest<ApiResponse<InventoryItem>>(
        `${this.resource}/products/${productId}`,
        config,
      );

    return response.data;
  }

  /**
   * Returns inventory for a branch.
   */
  async byBranch(
    branchId: string,
    config?: AxiosRequestConfig,
  ): Promise<
    PaginatedResponse<InventoryItem>
  > {
    const response =
      await this.getRequest<
        PaginatedResponse<InventoryItem>
      >(
        `${this.resource}/branches/${branchId}`,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Stock
   * ==========================================================================
   */

  /**
   * Adjust stock quantity.
   */
  async adjust(
    inventoryId: string,
    payload: InventoryAdjustmentRequest,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.postRequest<ApiResponse<void>>(
        `${this.resource}/${inventoryId}/adjustments`,
        payload,
        config,
      );

    return response.data;
  }

  /**
   * Transfer stock.
   */
  async transfer(
    inventoryId: string,
    payload: BranchTransferRequest,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.postRequest<ApiResponse<void>>(
        `${this.resource}/${inventoryId}/transfers`,
        payload,
        config,
      );

    return response.data;
  }

  /**
   * Reserve stock.
   */
  async reserve(
    inventoryId: string,
    payload: ReservationRequest,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.postRequest<ApiResponse<void>>(
        `${this.resource}/${inventoryId}/reservations`,
        payload,
        config,
      );

    return response.data;
  }

  /**
   * Release reserved stock.
   */
  async releaseReservation(
    inventoryId: string,
    payload: ReleaseReservationRequest,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.postRequest<ApiResponse<void>>(
        `${this.resource}/${inventoryId}/reservations/release`,
        payload,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * History
   * ==========================================================================
   */

  /**
   * Returns stock movement history.
   */
  async movements(
    inventoryId: string,
    config?: AxiosRequestConfig,
  ): Promise<
    PaginatedResponse<InventoryMovement>
  > {
    const response =
      await this.getRequest<
        PaginatedResponse<InventoryMovement>
      >(
        `${this.resource}/${inventoryId}/movements`,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Batches
   * ==========================================================================
   */

  /**
   * Returns product batches.
   */
  async batches(
    inventoryId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<Batch[]>> {
    const response =
      await this.getRequest<ApiResponse<Batch[]>>(
        `${this.resource}/${inventoryId}/batches`,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Valuation
   * ==========================================================================
   */

  /**
   * Returns inventory valuation.
   */
  async valuation(
    inventoryId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<InventoryValuation>> {
    const response =
      await this.getRequest<ApiResponse<InventoryValuation>>(
        `${this.resource}/${inventoryId}/valuation`,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Monitoring
   * ==========================================================================
   */

  /**
   * Returns products below reorder level.
   */
  async reorderList(
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<InventoryItem[]>> {
    const response =
      await this.getRequest<ApiResponse<InventoryItem[]>>(
        `${this.resource}/reorder`,
        config,
      );

    return response.data;
  }

  /**
   * Returns products nearing expiry.
   */
  async expiring(
    days = 90,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<Batch[]>> {
    const response =
      await this.getRequest<ApiResponse<Batch[]>>(
        `${this.resource}/expiring`,
        {
          ...config,
          params: {
            days,
          },
        },
      );

    return response.data;
  }
}

/* ============================================================================
 * Singleton
 * ============================================================================
 */

export const legacyProductInventory =
  new InventoryService();

export default legacyProductInventory;
