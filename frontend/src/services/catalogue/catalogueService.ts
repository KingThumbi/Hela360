/**
 * ============================================================================
 * Hela360 Master Catalogue Service
 * ============================================================================
 *
 * Tenant-facing access to the platform Master Catalogue.
 *
 * Responsibilities
 * ----------------
 * • Browse approved, active Master Catalogue items
 * • Retrieve one Master Catalogue item
 * • Adopt a Master Catalogue item into the tenant Product catalogue
 *
 * The Master Catalogue is platform-owned, but read responses include
 * tenant-specific Product adoption state.
 *
 * ============================================================================
 */

import type {
  AxiosRequestConfig,
} from "axios";

import {
  API_ENDPOINTS,
} from "@/api/endpoints";

import BaseService from "@/services/base";

import type {
  PaginatedResponse,
} from "@/types/api";

import type {
  CatalogueAdoptedProduct,
  CatalogueItem,
} from "@/types/entities";

import type {
  AdoptCatalogueItemRequest,
  ListCatalogueItemsRequest,
} from "@/types/requests";


interface CatalogueItemResponse {
  ok: true;

  item: CatalogueItem;
}


interface CatalogueListResponse {
  ok: true;

  count: number;

  pagination: {
    page: number;

    per_page: number;

    total: number;

    pages: number;

    has_next: boolean;

    has_prev: boolean;
  };

  items: CatalogueItem[];
}


interface CatalogueAdoptionResponse {
  ok: true;

  message: string;

  item: CatalogueAdoptedProduct;
}


/* ============================================================================
 * Service
 * ============================================================================
 */

class CatalogueService extends BaseService<
  CatalogueItem,
  AdoptCatalogueItemRequest
> {
  constructor() {
    super(API_ENDPOINTS.CATALOGUE.ROOT);
  }


  async listItems(
    params?: ListCatalogueItemsRequest,
    config?: AxiosRequestConfig,
  ): Promise<
    PaginatedResponse<CatalogueItem>
  > {
    const response =
      await this.getRequest<
        CatalogueListResponse
      >(
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

      pagination:
        response.data.pagination,
    };
  }


  async getItem(
    masterItemId: string,
    config?: AxiosRequestConfig,
  ): Promise<CatalogueItem> {
    const response =
      await this.getRequest<
        CatalogueItemResponse
      >(
        API_ENDPOINTS.CATALOGUE.BY_ID(
          masterItemId,
        ),
        config,
      );

    return response.data.item;
  }


  async adoptItem(
    masterItemId: string,
    payload: AdoptCatalogueItemRequest,
    config?: AxiosRequestConfig,
  ): Promise<CatalogueAdoptedProduct> {
    const response =
      await this.postRequest<
        CatalogueAdoptionResponse
      >(
        API_ENDPOINTS.CATALOGUE.ADOPT(
          masterItemId,
        ),
        payload,
        config,
      );

    return response.data.item;
  }
}


export const catalogueService =
  new CatalogueService();

export default catalogueService;
