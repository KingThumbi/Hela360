/**
 * ============================================================================
 * Hela360 Enterprise Product Service
 * ============================================================================
 *
 * Service responsible for enterprise product management.
 *
 * Responsibilities
 * ----------------
 * • Product list
 * • Product lookup
 * • Product creation
 * • Product-code lookup
 *
 * Every inventory-driven workflow depends on this service.
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
  Product,
  ProductUnit,
} from "@/types/entities";

import type {
  CreateProductRequest,
  ListProductsRequest,
  UpdateProductRequest,
} from "@/types/requests";

import type {
  ProductTaxCode,
} from "@/types/responses";

interface ProductItemResponse {
  ok: true;

  item: Product;

  message?: string;
}

interface ProductListResponse {
  ok: true;

  count: number;

  items: Product[];
}

interface ProductUnitListResponse {
  ok: true;

  items: ProductUnit[];
}

interface ProductTaxCodeListResponse {
  ok: true;

  items: ProductTaxCode[];
}

/* ============================================================================
 * Product Service
 * ============================================================================
 */

class ProductService extends BaseService<
  Product,
  CreateProductRequest,
  UpdateProductRequest
> {
  constructor() {
    super(API_ENDPOINTS.PRODUCTS.ROOT);
  }

  /* ==========================================================================
   * Public Facade
   * ==========================================================================
   */

  async listProducts(
    params?: ListProductsRequest,
    config?: AxiosRequestConfig,
  ): Promise<PaginatedResponse<Product>> {
    const response =
      await this.getRequest<ProductListResponse>(
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

  async getProduct(
    productId: string | number,
    config?: AxiosRequestConfig,
  ): Promise<Product> {
    const response =
      await this.getRequest<ProductItemResponse>(
        this.resourceUrl(productId),
        config,
      );

    return response.data.item;
  }

  async createProduct(
    payload: CreateProductRequest,
    config?: AxiosRequestConfig,
  ): Promise<Product> {
    const response =
      await this.postRequest<ProductItemResponse>(
        this.resource,
        payload,
        config,
      );

    return response.data.item;
  }

  async updateProduct(
    productId: string | number,
    payload: UpdateProductRequest,
    config?: AxiosRequestConfig,
  ): Promise<Product> {
    const response =
      await this.patchRequest<ProductItemResponse>(
        API_ENDPOINTS.PRODUCTS.BY_ID(
          String(productId),
        ),
        payload,
        config,
      );

    return response.data.item;
  }

  async archiveProduct(
    productId: string | number,
    config?: AxiosRequestConfig,
  ): Promise<Product> {
    const response =
      await this.postRequest<ProductItemResponse>(
        API_ENDPOINTS.PRODUCTS.ARCHIVE(
          String(productId),
        ),
        undefined,
        config,
      );

    return response.data.item;
  }

  async restoreProduct(
    productId: string | number,
    config?: AxiosRequestConfig,
  ): Promise<Product> {
    const response =
      await this.postRequest<ProductItemResponse>(
        API_ENDPOINTS.PRODUCTS.RESTORE(
          String(productId),
        ),
        undefined,
        config,
      );

    return response.data.item;
  }

  async searchProducts(
    search: string,
    params?: Omit<
      ListProductsRequest,
      "search"
    >,
    config?: AxiosRequestConfig,
  ): Promise<PaginatedResponse<Product>> {
    return this.listProducts(
      {
        ...params,
        search,
      },
      config,
    );
  }

  async getProductByCode(
    codeValue: string,
    config?: AxiosRequestConfig,
  ): Promise<Product> {
    const response =
      await this.getRequest<ProductItemResponse>(
        this.resourceUrl(
          "by-code",
          codeValue,
        ),
        config,
      );

    return response.data.item;
  }

  async listProductUnits(
    productId: string | number,
    config?: AxiosRequestConfig,
  ): Promise<ProductUnit[]> {
    const response =
      await this.getRequest<ProductUnitListResponse>(
        this.resourceUrl(productId, "units"),
        config,
      );

    return response.data.items;
  }

  async listTaxCodes(
    config?: AxiosRequestConfig,
  ): Promise<ProductTaxCode[]> {
    const response =
      await this.getRequest<ProductTaxCodeListResponse>(
        API_ENDPOINTS.PRODUCTS.TAX_CODES,
        config,
      );

    return response.data.items;
  }
}

/* ============================================================================
 * Singleton
 * ============================================================================
 */

export const productService =
  new ProductService();

export default productService;
