/**
 * ============================================================================
 * Hela360 Enterprise Customer Service
 * ============================================================================
 *
 * Service responsible for customer management.
 *
 * Responsibilities
 * ----------------
 * • Customer CRUD
 * • Customer search
 * • Customer lookup
 * • Customer purchase history
 * • Customer balances
 * • Customer loyalty
 * • Customer prescriptions
 * • Customer invoices
 * • Customer statistics
 *
 * This service integrates Sales, Finance and Pharmacy modules.
 *
 * ============================================================================
 */

import type { AxiosRequestConfig } from "axios";

import { API_ENDPOINTS } from "@/api/endpoints";

import BaseService from "@/services/base";

import type {
  PaginatedResponse,
} from "@/types/api";

import type {
  Customer,
} from "@/types/entities";

import type {
  CreateCustomerRequest,
  PaginationRequest,
  UpdateCustomerRequest,
} from "@/types/requests";

interface CustomerItemResponse {
  ok: true;

  item: Customer;

  message?: string;
}

interface CustomerListResponse {
  ok: true;

  count: number;

  items: Customer[];
}

/* ============================================================================
 * Customer Service
 * ============================================================================
 */

export class CustomerService extends BaseService<
  Customer,
  CreateCustomerRequest,
  UpdateCustomerRequest
> {
  constructor() {
    super(API_ENDPOINTS.CUSTOMERS.ROOT);
  }

  /* ==========================================================================
   * Public Facade
   * ==========================================================================
   */

  async listCustomers(
    params?: PaginationRequest,
    config?: AxiosRequestConfig,
  ): Promise<PaginatedResponse<Customer>> {
    const response =
      await this.getRequest<CustomerListResponse>(
        this.resource,
        {
          ...config,

          params: {
            ...config?.params,
            ...params,
          },
        },
      );

    const page = params?.page ?? 1;

    const perPage =
      params?.per_page ?? response.data.items.length;

    return {
      items: response.data.items,

      pagination: {
        page,
        per_page: perPage,
        total: response.data.count,
        pages:
          perPage > 0
            ? Math.ceil(response.data.count / perPage)
            : 0,
        has_next:
          perPage > 0 &&
          page <
            Math.ceil(response.data.count / perPage),
        has_prev: page > 1,
      },
    };
  }

  async getCustomer(
    customerId: string,
    config?: AxiosRequestConfig,
  ): Promise<Customer> {
    const response =
      await this.getRequest<CustomerItemResponse>(
        this.resourceUrl(customerId),
        config,
      );

    return response.data.item;
  }

  async createCustomer(
    payload: CreateCustomerRequest,
    config?: AxiosRequestConfig,
  ): Promise<Customer> {
    const response =
      await this.postRequest<CustomerItemResponse>(
        this.resource,
        payload,
        config,
      );

    return response.data.item;
  }
}

/* ============================================================================
 * Singleton
 * ============================================================================
 */

export const customerService =
  new CustomerService();

export default customerService;
