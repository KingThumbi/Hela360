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
  CreateProductUnitRequest,
  ListProductsRequest,
  UpdateProductRequest,
  UpdateProductUnitRequest,
} from "@/types/requests";

import type {
  ProductTaxCode,
} from "@/types/responses";

import type {
  ProductBatchHistoryItem,
  ProductBatchHistoryParams,
  ProductHistoryListResponse,
  ProductHistorySummary,
  ProductHistorySummaryResponse,
  ProductMovementHistoryItem,
  ProductMovementHistoryParams,
  ProductMovementTimelineResponse,
  ProductPriceTrendParams,
  ProductPriceTrendResponse,
  ProductPurchaseHistoryItem,
  ProductPurchaseHistoryParams,
  ProductSalesHistoryItem,
  ProductSalesHistoryParams,
  ProductStockCountHistoryItem,
  ProductStockCountHistoryParams,
  ProductStockCountVarianceTrendResponse,
} from "@/types/responses/product-history";

interface ProductItemResponse {
  ok: true;

  item: Product;

  message?: string;
}

export interface DeleteProductResponse {
  ok: true;

  id: string;

  message: string;
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

interface ProductUnitItemResponse {
  ok: true;

  item: ProductUnit;

  message?: string;
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

    async getProductHistory(
      productId: string | number,
      config?: AxiosRequestConfig,
    ): Promise<ProductHistorySummary> {
      const response =
        await this.getRequest<ProductHistorySummaryResponse>(
          API_ENDPOINTS.PRODUCTS.HISTORY(
            String(productId),
          ),
          config,
        );

      return response.data.item;
    }

    async listProductSalesHistory(
      productId: string | number,
      params?: ProductSalesHistoryParams,
      config?: AxiosRequestConfig,
    ): Promise<
      ProductHistoryListResponse<ProductSalesHistoryItem>
    > {
      const response =
        await this.getRequest<
          ProductHistoryListResponse<ProductSalesHistoryItem>
        >(
          API_ENDPOINTS.PRODUCTS.HISTORY_SALES(
            String(productId),
          ),
          {
            ...config,
            params: {
              ...config?.params,
              ...params,
            },
          },
        );

      return response.data;
    }

    async listProductPurchaseHistory(
      productId: string | number,
      params?: ProductPurchaseHistoryParams,
      config?: AxiosRequestConfig,
    ): Promise<
      ProductHistoryListResponse<ProductPurchaseHistoryItem>
    > {
      const response =
        await this.getRequest<
          ProductHistoryListResponse<ProductPurchaseHistoryItem>
        >(
          API_ENDPOINTS.PRODUCTS.HISTORY_PURCHASES(
            String(productId),
          ),
          {
            ...config,
            params: {
              ...config?.params,
              ...params,
            },
          },
        );

      return response.data;
    }

    async listProductSalesPriceTrend(
      productId: string | number,
      params?: ProductPriceTrendParams,
      config?: AxiosRequestConfig,
    ): Promise<ProductPriceTrendResponse> {
      const response =
        await this.getRequest<ProductPriceTrendResponse>(
          API_ENDPOINTS.PRODUCTS.HISTORY_SALES_PRICE_TREND(
            String(productId),
          ),
          {
            ...config,
            params: {
              ...config?.params,
              ...params,
            },
          },
        );

      return response.data;
    }

    async listProductPurchasePriceTrend(
      productId: string | number,
      params?: ProductPriceTrendParams,
      config?: AxiosRequestConfig,
    ): Promise<ProductPriceTrendResponse> {
      const response =
        await this.getRequest<ProductPriceTrendResponse>(
          API_ENDPOINTS.PRODUCTS.HISTORY_PURCHASE_PRICE_TREND(
            String(productId),
          ),
          {
            ...config,
            params: {
              ...config?.params,
              ...params,
            },
          },
        );

      return response.data;
    }

    async listProductMovementTimeline(
      productId: string | number,
      params?: ProductMovementHistoryParams,
      config?: AxiosRequestConfig,
    ): Promise<ProductMovementTimelineResponse> {
      const response =
        await this.getRequest<ProductMovementTimelineResponse>(
          API_ENDPOINTS.PRODUCTS.HISTORY_MOVEMENT_TIMELINE(
            String(productId),
          ),
          {
            ...config,
            params: {
              ...config?.params,
              ...params,
            },
          },
        );

      return response.data;
    }

    async listProductMovementHistory(
      productId: string | number,
      params?: ProductMovementHistoryParams,
      config?: AxiosRequestConfig,
    ): Promise<
      ProductHistoryListResponse<ProductMovementHistoryItem>
    > {
      const response =
        await this.getRequest<
          ProductHistoryListResponse<ProductMovementHistoryItem>
        >(
          API_ENDPOINTS.PRODUCTS.HISTORY_MOVEMENTS(
            String(productId),
          ),
          {
            ...config,
            params: {
              ...config?.params,
              ...params,
            },
          },
        );

      return response.data;
    }

  async listProductBatchHistory(
    productId: string | number,
    params?: ProductBatchHistoryParams,
    config?: AxiosRequestConfig,
  ): Promise<
    ProductHistoryListResponse<ProductBatchHistoryItem>
  > {
    const response =
      await this.getRequest<
        ProductHistoryListResponse<ProductBatchHistoryItem>
      >(
        API_ENDPOINTS.PRODUCTS.HISTORY_BATCHES(
          String(productId),
        ),
        {
          ...config,
          params: {
            ...config?.params,
            ...params,
          },
        },
      );

    return response.data;
  }

  async listProductStockCountVarianceTrend(
    productId: string | number,
    params?: ProductStockCountHistoryParams,
    config?: AxiosRequestConfig,
  ): Promise<ProductStockCountVarianceTrendResponse> {
    const response =
      await this.getRequest<ProductStockCountVarianceTrendResponse>(
        API_ENDPOINTS.PRODUCTS.HISTORY_STOCK_COUNT_VARIANCE_TREND(
          String(productId),
        ),
        {
          ...config,
          params: {
            ...config?.params,
            ...params,
          },
        },
      );

    return response.data;
  }

  async listProductStockCountHistory(
    productId: string | number,
    params?: ProductStockCountHistoryParams,
    config?: AxiosRequestConfig,
  ): Promise<
    ProductHistoryListResponse<ProductStockCountHistoryItem>
  > {
    const response =
      await this.getRequest<
        ProductHistoryListResponse<ProductStockCountHistoryItem>
      >(
        API_ENDPOINTS.PRODUCTS.HISTORY_STOCK_COUNTS(
          String(productId),
        ),
        {
          ...config,
          params: {
            ...config?.params,
            ...params,
          },
        },
      );

    return response.data;
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

  async deleteProduct(
    productId: string | number,
    config?: AxiosRequestConfig,
  ): Promise<DeleteProductResponse> {
    const response =
      await this.deleteRequest<DeleteProductResponse>(
        API_ENDPOINTS.PRODUCTS.BY_ID(
          String(productId),
        ),
        config,
      );

    return response.data;
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
        API_ENDPOINTS.PRODUCTS.UNITS(productId),
        config,
      );

    return response.data.items;
  }

  async createProductUnit(
    productId: string | number,
    payload: CreateProductUnitRequest,
    config?: AxiosRequestConfig,
  ): Promise<ProductUnit> {
    const response =
      await this.postRequest<ProductUnitItemResponse>(
        API_ENDPOINTS.PRODUCTS.UNITS(productId),
        payload,
        config,
      );

    return response.data.item;
  }

  async updateProductUnit(
    productId: string | number,
    productUnitId: string | number,
    payload: UpdateProductUnitRequest,
    config?: AxiosRequestConfig,
  ): Promise<ProductUnit> {
    const response =
      await this.patchRequest<ProductUnitItemResponse>(
        API_ENDPOINTS.PRODUCTS.UNIT(
          productId,
          productUnitId,
        ),
        payload,
        config,
      );

    return response.data.item;
  }

  async archiveProductUnit(
    productId: string | number,
    productUnitId: string | number,
    config?: AxiosRequestConfig,
  ): Promise<ProductUnit> {
    const response =
      await this.postRequest<ProductUnitItemResponse>(
        API_ENDPOINTS.PRODUCTS.ARCHIVE_UNIT(
          productId,
          productUnitId,
        ),
        {},
        config,
      );

    return response.data.item;
  }

  async restoreProductUnit(
    productId: string | number,
    productUnitId: string | number,
    config?: AxiosRequestConfig,
  ): Promise<ProductUnit> {
    const response =
      await this.postRequest<ProductUnitItemResponse>(
        API_ENDPOINTS.PRODUCTS.RESTORE_UNIT(
          productId,
          productUnitId,
        ),
        {},
        config,
      );

    return response.data.item;
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
