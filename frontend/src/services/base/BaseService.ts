/**
 * ============================================================================
 * Hela360 Enterprise Base Service
 * ============================================================================
 *
 * Abstract foundation for all HTTP services.
 *
 * Responsibilities
 * ----------------
 * • Standardize CRUD operations
 * • Provide strongly typed API access
 * • Centralize pagination
 * • Centralize searching
 * • Centralize filtering
 * • Centralize sorting
 * • Support request cancellation
 * • Normalize endpoint construction
 * • Reduce duplicated service code
 *
 * Every domain service should extend this class.
 *
 * Example
 * -------
 *
 * class ProductService extends BaseService<
 *   Product,
 *   CreateProductRequest,
 *   UpdateProductRequest
 * > {
 *   constructor() {
 *     super(API_ENDPOINTS.PRODUCTS.ROOT);
 *   }
 * }
 *
 * This class intentionally contains no business logic. Domain-specific
 * operations belong in concrete services that extend this foundation.
 *
 * ============================================================================
 */

import type {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
} from "axios";

import apiClient from "@/api/client";

import type {
  ApiResponse,
  PaginatedResponse,
} from "@/types/api";

import type { EntityIdentifier } from "./types";

import type {
  FilterOptions,
  QueryOptions,
} from "./query";

import type { RequestOptions } from "./request";

/* ============================================================================
 * Base Service
 * ============================================================================
 */

export abstract class BaseService<
  TEntity,
  TCreate = Partial<TEntity>,
  TUpdate = Partial<TEntity>,
  TIdentifier extends EntityIdentifier = EntityIdentifier,
> {
  /**
   * Base API endpoint for the resource.
   *
   * Examples
   * --------
   * /products
   * /customers
   * /sales
   * /inventory
   */
  protected readonly endpoint: string;

  protected readonly client: AxiosInstance;

  protected constructor(
    endpoint: string,
    client: AxiosInstance = apiClient,
  ) {
    this.endpoint = this.normalizeEndpoint(endpoint);
    this.client = client;
  }

  /* ==========================================================================
   * Endpoint Helpers
   * ==========================================================================
   */

  /**
   * Ensures endpoint consistency.
   *
   * Examples
   * --------
   * products      -> /products
   * /products     -> /products
   * /products/    -> /products
   */
  protected normalizeEndpoint(
    endpoint: string,
  ): string {
    const normalized = endpoint.trim();

    if (!normalized.startsWith("/")) {
      return `/${normalized.replace(/\/+$/, "")}`;
    }

    return normalized.replace(/\/+$/, "");
  }

  /**
   * Returns the collection endpoint.
   *
   * Example:
   *
   * /products
   */
  protected collectionUrl(): string {
    return this.endpoint;
  }

  /**
   * Returns the URL for a specific entity.
   *
   * Example:
   *
   * /products/{id}
   */
  protected url(
    id?: TIdentifier,
  ): string {
    return id === undefined
      ? this.collectionUrl()
      : `${this.collectionUrl()}/${String(id)}`;
  }

  /**
   * Builds a resource endpoint using path segments.
   *
   * Examples
   * --------
   *
   * resourceUrl(productId, "inventory")
   * → /products/{id}/inventory
   *
   * resourceUrl(productId, "stock", "history")
   * → /products/{id}/stock/history
   *
   * resourceUrl("search")
   * → /products/search
   */
  protected resourceUrl(
    ...segments: ReadonlyArray<
      string | number | TIdentifier
    >
  ): string {
    if (segments.length === 0) {
      return this.collectionUrl();
    }

    return [
      this.collectionUrl(),
      ...segments.map((segment) =>
        encodeURIComponent(String(segment)),
      ),
    ].join("/");
  }

  /**
   * Returns a child resource endpoint.
   *
   * Example:
   *
   * childResourceUrl(orderId, "items")
   * → /orders/{id}/items
   */
  protected childResourceUrl(
    id: TIdentifier,
    child: string,
  ): string {
    return `${this.url(id)}/${encodeURIComponent(
      child,
    )}`;
  }

  /**
   * Returns a nested child resource endpoint.
   *
   * Example:
   *
   * nestedResourceUrl(
   *   orderId,
   *   "items",
   *   itemId,
   * )
   *
   * → /orders/{id}/items/{itemId}
   */
  protected nestedResourceUrl(
    id: TIdentifier,
    child: string,
    childId: string | number,
  ): string {
    return `${this.childResourceUrl(
      id,
      child,
    )}/${encodeURIComponent(String(childId))}`;
  }

  /* ==========================================================================
   * Query & Request Helpers
   * ==========================================================================
   */

  /**
   * Converts enterprise query options into HTTP query parameters.
   *
   * Responsibilities
   * ----------------
   * • Pagination
   * • Searching
   * • Sorting
   * • Filtering
   * • Ignore undefined values
   * • Preserve array filters
   */
  protected buildQuery(
    options?: QueryOptions<TEntity>,
  ): Record<string, unknown> {
    if (!options) {
      return {};
    }

    const params: Record<string, unknown> = {};

    /*
     * Pagination
     */

    if (options.page !== undefined) {
      params.page = options.page;
    }

    if (options.pageSize !== undefined) {
      params.page_size = options.pageSize;
    }

    /*
     * Search
     */

    if (options.search?.trim()) {
      params.search = options.search.trim();
    }

    /*
     * Sorting
     */

    if (options.sortBy) {
      params.sort_by = options.sortBy;
    }

    if (options.sortDirection) {
      params.sort_direction =
        options.sortDirection;
    }

    /*
     * Filters
     */

    if (options.filters) {
      Object.entries(options.filters).forEach(
        ([key, value]) => {
          if (
            value === undefined ||
            value === null
          ) {
            return;
          }

          /*
           * Arrays become repeated query parameters.
           *
           * Example:
           *
           * status[]=ACTIVE
           * status[]=PENDING
           */

          if (Array.isArray(value)) {
            params[key] = value.filter(
              (item) =>
                item !== undefined &&
                item !== null,
            );

            return;
          }

          params[key] = value;
        },
      );
    }

    return params;
  }

  /**
   * Builds the Axios request configuration.
   *
   * This method provides a single extension point for future
   * enterprise capabilities without changing every CRUD method.
   *
   * Future Enhancements
   * -------------------
   * • Correlation IDs
   * • Request tracing
   * • ETag support
   * • Retry metadata
   * • Cache hints
   * • Offline synchronization
   * • Telemetry
   */
  protected buildConfig(
    config?: RequestOptions,
  ): AxiosRequestConfig {
    return {
      ...config,

      signal: config?.signal,
    };
  }

  /**
   * Builds the Axios configuration together with query parameters.
   *
   * Keeps CRUD methods concise and consistent.
   */
  protected buildQueryConfig(
    options?: QueryOptions<TEntity>,
    config?: RequestOptions,
  ): AxiosRequestConfig {
    return {
      ...this.buildConfig(config),

      params: this.buildQuery(options),
    };
  }

  /**
   * Creates FormData from a plain object.
   *
   * Used by upload endpoints.
   */
  protected createFormData(
    values: Record<string, unknown>,
  ): FormData {
    const formData = new FormData();

    Object.entries(values).forEach(
      ([key, value]) => {
        if (
          value === undefined ||
          value === null
        ) {
          return;
        }

        if (Array.isArray(value)) {
          value.forEach((item) => {
            if (
              item !== undefined &&
              item !== null
            ) {
              formData.append(
                key,
                item as Blob | string,
              );
            }
          });

          return;
        }

        formData.append(
          key,
          value as Blob | string,
        );
      },
    );

    return formData;
  } 
  
  /* ==========================================================================
   * CRUD Operations
   * ==========================================================================
   */

  /**
   * Retrieves all resources.
   *
   * Supports:
   * • Filtering
   * • Searching
   * • Sorting
   */
  async list(
    options?: QueryOptions<TEntity>,
    config?: RequestOptions,
  ): Promise<ApiResponse<TEntity[]>> {
    const response =
      await this.client.get<ApiResponse<TEntity[]>>(
        this.collectionUrl(),
        this.buildQueryConfig(
          options,
          config,
        ),
      );

    return response.data;
  }

  /**
   * Retrieves a paginated collection.
   *
   * Intended for grids and tables.
   */
  async paginate(
    options?: QueryOptions<TEntity>,
    config?: RequestOptions,
  ): Promise<
    PaginatedResponse<TEntity>
  > {
    const response =
      await this.client.get<
        PaginatedResponse<TEntity>
      >(
        this.collectionUrl(),
        this.buildQueryConfig(
          options,
          config,
        ),
      );

    return response.data;
  }

  /**
   * Retrieves a single resource.
   */
  async get(
    id: TIdentifier,
    config?: RequestOptions,
  ): Promise<ApiResponse<TEntity>> {
    const response =
      await this.client.get<
        ApiResponse<TEntity>
      >(
        this.url(id),
        this.buildConfig(config),
      );

    return response.data;
  }

  /**
   * Creates a new resource.
   */
  async create(
    payload: TCreate,
    config?: RequestOptions,
  ): Promise<ApiResponse<TEntity>> {
    const response =
      await this.client.post<
        ApiResponse<TEntity>
      >(
        this.collectionUrl(),
        payload,
        this.buildConfig(config),
      );

    return response.data;
  }

  /**
   * Replaces an existing resource.
   *
   * Uses HTTP PUT.
   */
  async update(
    id: TIdentifier,
    payload: TUpdate,
    config?: RequestOptions,
  ): Promise<ApiResponse<TEntity>> {
    const response =
      await this.client.put<
        ApiResponse<TEntity>
      >(
        this.url(id),
        payload,
        this.buildConfig(config),
      );

    return response.data;
  }

/**
 * Partially updates a resource.
 *
 * Uses HTTP PATCH.
 */
async patch(
  id: TIdentifier,
  payload: Partial<TUpdate>,
  config?: RequestOptions,
): Promise<ApiResponse<TEntity>> {
  const response =
    await this.client.patch<ApiResponse<TEntity>>(
      this.url(id),
      payload,
      this.buildConfig(config),
    );

  return response.data;
}

  /**
   * Deletes a resource.
   */
  async delete(
    id: TIdentifier,
    config?: RequestOptions,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.client.delete<
        ApiResponse<void>
      >(
        this.url(id),
        this.buildConfig(config),
      );

    return response.data;
  }  

  /* ==========================================================================
   * Convenience Operations
   * ==========================================================================
   */

  /**
   * Creates multiple resources.
   *
   * The default implementation executes individual create requests in
   * parallel. Services may override this method if the backend exposes a
   * dedicated bulk-create endpoint.
   */
  async createMany(
    payloads: readonly TCreate[],
    config?: RequestOptions,
  ): Promise<ApiResponse<TEntity>[]> {
    return Promise.all(
      payloads.map((payload) =>
        this.create(payload, config),
      ),
    );
  }

  /**
   * Deletes multiple resources.
   *
   * The default implementation performs parallel delete requests.
   * Override when the API exposes a bulk-delete endpoint.
   */
  async deleteMany(
    ids: readonly TIdentifier[],
    config?: RequestOptions,
  ): Promise<ApiResponse<void>[]> {
    return Promise.all(
      ids.map((id) =>
        this.delete(id, config),
      ),
    );
  }

  /**
   * Searches resources.
   */
  async search(
    search: string,
    options?: Omit<
      QueryOptions<TEntity>,
      "search"
    >,
    config?: RequestOptions,
  ): Promise<ApiResponse<TEntity[]>> {
    return this.list(
      {
        ...options,
        search,
      },
      config,
    );
  }

  /**
   * Counts resources.
   *
   * The default implementation derives the count from the paginated
   * response. Services may override this when the backend exposes a
   * dedicated count endpoint.
   */
  async count(
    filters?: FilterOptions<TEntity>,
    config?: RequestOptions,
  ): Promise<number> {
    const response =
      await this.paginate(
        {
          page: 1,
          pageSize: 1,
          filters,
        },
        config,
      );

    return response.pagination.total;
  }

  /**
   * Determines whether a resource exists.
   *
   * Services may override this to use a dedicated HEAD or EXISTS endpoint.
   */
  async exists(
    id: TIdentifier,
    config?: RequestOptions,
  ): Promise<boolean> {
    try {
      await this.get(id, config);

      return true;
    } catch {
      return false;
    }
  }

  /**
   * Refreshes a resource by retrieving its latest representation.
   *
   * Included primarily for semantic clarity when used with mutation flows.
   */
  async refresh(
    id: TIdentifier,
    config?: RequestOptions,
  ): Promise<ApiResponse<TEntity>> {
    return this.get(id, config);
  } 
  
  /* ==========================================================================
   * Transport Helpers
   * ==========================================================================
   *
   * These helpers intentionally expose the configured API client without
   * exposing Axios directly to concrete services.
   *
   * Services should use these methods whenever implementing custom
   * endpoints beyond the standard CRUD operations.
   * ==========================================================================
   */

  /**
   * Performs a GET request.
   */
  protected getRequest<TResult>(
    url: string,
    config?: RequestOptions,
  ): Promise<AxiosResponse<TResult>> {
    return this.client.get<TResult>(
      url,
      this.buildConfig(config),
    );
  }

  /**
   * Performs a POST request.
   */
  protected postRequest<TResult>(
    url: string,
    data?: unknown,
    config?: RequestOptions,
  ): Promise<AxiosResponse<TResult>> {
    return this.client.post<TResult>(
      url,
      data,
      this.buildConfig(config),
    );
  }

  /**
   * Performs a PUT request.
   */
  protected putRequest<TResult>(
    url: string,
    data?: unknown,
    config?: RequestOptions,
  ): Promise<AxiosResponse<TResult>> {
    return this.client.put<TResult>(
      url,
      data,
      this.buildConfig(config),
    );
  }

  /**
   * Performs a PATCH request.
   */
  protected patchRequest<TResult>(
    url: string,
    data?: unknown,
    config?: RequestOptions,
  ): Promise<AxiosResponse<TResult>> {
    return this.client.patch<TResult>(
      url,
      data,
      this.buildConfig(config),
    );
  }

  /**
   * Performs a DELETE request.
   */
  protected deleteRequest<TResult>(
    url: string,
    config?: RequestOptions,
  ): Promise<AxiosResponse<TResult>> {
    return this.client.delete<TResult>(
      url,
      this.buildConfig(config),
    );
  }

  /**
   * Performs a HEAD request.
   *
   * Useful for existence checks and metadata retrieval.
   */
  protected head(
    url: string,
    config?: RequestOptions,
  ): Promise<AxiosResponse<void>> {
    return this.client.head<void>(
      url,
      this.buildConfig(config),
    );
  }

  /**
   * Performs an OPTIONS request.
   *
   * Useful for capability discovery and CORS diagnostics.
   */
  protected options<TResult>(
    url: string,
    config?: RequestOptions,
  ): Promise<AxiosResponse<TResult>> {
    return this.client.options<TResult>(
      url,
      this.buildConfig(config),
    );
  }

  /**
   * Uploads multipart form data.
   *
   * Intended for:
   * • Product images
   * • Customer documents
   * • Supplier contracts
   * • Prescriptions
   * • Attachments
   */
  protected upload<TResult>(
    url: string,
    data: FormData,
    config?: RequestOptions,
  ): Promise<AxiosResponse<TResult>> {
    return this.client.post<TResult>(
      url,
      data,
      {
        ...this.buildConfig(config),

        headers: {
          ...(config?.headers ?? {}),

          "Content-Type":
            "multipart/form-data",
        },
      },
    );
  }

  /**
   * Downloads a binary resource.
   *
   * Intended for:
   * • Reports
   * • PDFs
   * • Excel exports
   * • Labels
   * • Receipts
   */
  protected download(
    url: string,
    config?: RequestOptions,
  ): Promise<AxiosResponse<Blob>> {
    return this.client.get<Blob>(
      url,
      {
        ...this.buildConfig(config),

        responseType: "blob",
      },
    );
  }
  
  /* ==========================================================================
   * Metadata
   * ==========================================================================
   */

  /**
   * Returns the normalized API endpoint for this service.
   *
   * This is primarily intended for diagnostics, testing and advanced
   * subclasses. Business logic should rarely need direct access.
   */
  public get resource(): string {
    return this.endpoint;
  }
}

/* ============================================================================
 * Export
 * ============================================================================
 */

export default BaseService;  
