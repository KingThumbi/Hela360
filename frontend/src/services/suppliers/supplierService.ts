/**
 * ============================================================================
 * Hela360 Enterprise Supplier Service
 * ============================================================================
 *
 * Service responsible for supplier management.
 *
 * Responsibilities
 * ----------------
 * • Supplier CRUD operations
 * • Supplier lookup
 * • Supplier contacts
 * • Purchase history
 * • Supplier products
 * • Supplier performance
 * • Supplier activation
 * • Supplier deactivation
 *
 * Suppliers are the foundation of the procurement lifecycle.
 *
 * ============================================================================
 */

import type { AxiosRequestConfig } from "axios";

import { API_ENDPOINTS } from "@/api/endpoints";

import BaseService from "@/services/base";

import type { PaginatedResponse } from "@/types/api";
import type { Supplier } from "@/types/entities";
import type {
  CreateSupplierRequest,
  PaginationRequest,
  UpdateSupplierRequest,
} from "@/types/requests";
interface SupplierItemResponse {
  ok: true;

  item: Supplier;

  message?: string;
}

interface SupplierListResponse {
  ok: true;

  items: Supplier[];

  pagination: {
    page: number;

    page_size: number;

    total: number;

    pages: number;

    has_next: boolean;

    has_prev: boolean;
  };
}

/* ============================================================================
 * Supplier Service
 * ============================================================================
 */

export class SupplierService extends BaseService<
  Supplier,
  CreateSupplierRequest,
  UpdateSupplierRequest
> {
  constructor() {
    super(API_ENDPOINTS.SUPPLIERS.ROOT);
  }

  /* ==========================================================================
   * Public Facade
   * ==========================================================================
   */

  /**
   * Lists suppliers using the verified backend pagination envelope.
   */
  async listSuppliers(
    params?: PaginationRequest,
    config?: AxiosRequestConfig,
  ): Promise<PaginatedResponse<Supplier>> {
    const response =
      await this.getRequest<SupplierListResponse>(
        this.resource,
        {
          ...config,

          params: {
            ...config?.params,
            ...params,
          },
        },
      );

    return {
      items: response.data.items,

      pagination: {
        page: response.data.pagination.page,
        per_page: response.data.pagination.page_size,
        total: response.data.pagination.total,
        pages: response.data.pagination.pages,
        has_next: response.data.pagination.has_next,
        has_prev: response.data.pagination.has_prev,
      },
    };
  }

  /**
   * Retrieves one supplier by identifier.
   */
  async getSupplier(
    supplierId: string | number,
    config?: AxiosRequestConfig,
  ): Promise<Supplier> {
    const response =
      await this.getRequest<SupplierItemResponse>(
        this.resourceUrl(supplierId),
        config,
      );

    return response.data.item;
  }

  /**
   * Creates a supplier and returns the verified Supplier payload.
   */
  async createSupplier(
    payload: CreateSupplierRequest,
    config?: AxiosRequestConfig,
  ): Promise<Supplier> {
    const response =
      await this.postRequest<SupplierItemResponse>(
        this.resource,
        payload,
        config,
      );

    return response.data.item;
  }

  /**
   * Updates a supplier using the verified PATCH endpoint.
   */
  async updateSupplier(
    supplierId: string | number,
    payload: UpdateSupplierRequest,
    config?: AxiosRequestConfig,
  ): Promise<Supplier> {
    const response =
      await this.patchRequest<SupplierItemResponse>(
        this.resourceUrl(supplierId),
        payload,
        config,
      );

    return response.data.item;
  }

  /**
   * Deactivates a supplier. The backend does not support hard delete.
   */
  async deactivateSupplier(
    supplierId: string | number,
    config?: AxiosRequestConfig,
  ): Promise<Supplier> {
    const response =
      await this.postRequest<SupplierItemResponse>(
        this.resourceUrl(supplierId, "deactivate"),
        undefined,
        config,
      );

    return response.data.item;
  }

  /**
   * Reactivates a supplier.
   */
  async reactivateSupplier(
    supplierId: string | number,
    config?: AxiosRequestConfig,
  ): Promise<Supplier> {
    const response =
      await this.postRequest<SupplierItemResponse>(
        this.resourceUrl(supplierId, "reactivate"),
        undefined,
        config,
      );

    return response.data.item;
  }

}

/* ============================================================================
 * Singleton
 * ============================================================================
 */

export const supplierService =
  new SupplierService();

export default supplierService;
