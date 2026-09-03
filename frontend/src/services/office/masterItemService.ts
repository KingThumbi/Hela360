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
  ListOfficeMasterItemsRequest,
  OfficeMasterItem,
  OfficeMasterItemApprovalResult,
  OfficeMasterItemSupplierEvidence,
} from "@/types/officeCatalogue";

interface OfficeMasterItemListResponse {
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

  items: OfficeMasterItem[];
}

class OfficeMasterItemService extends BaseService<
  OfficeMasterItem
> {
  constructor() {
    super(
      API_ENDPOINTS.OFFICE_CATALOGUE.MASTER_ITEMS,
    );
  }

  async getSupplierEvidence(
    masterItemId: string,
    config?: AxiosRequestConfig,
  ): Promise<OfficeMasterItemSupplierEvidence> {
    const response =
      await this.getRequest<{
        ok: true;
        evidence: OfficeMasterItemSupplierEvidence;
      }>(
        API_ENDPOINTS.OFFICE_CATALOGUE
          .MASTER_ITEM_SUPPLIER_EVIDENCE(
            masterItemId,
          ),
        config,
      );

    return response.data.evidence;
  }


  async approveItem(
    masterItemId: string,
    config?: AxiosRequestConfig,
  ): Promise<OfficeMasterItemApprovalResult> {
    const response =
      await this.postRequest<{
        ok: true;
        message: string;
        item: OfficeMasterItemApprovalResult;
      }>(
        API_ENDPOINTS.OFFICE_CATALOGUE
          .MASTER_ITEM_APPROVE(
            masterItemId,
          ),
        undefined,
        config,
      );

    return response.data.item;
  }


  async getItem(
    masterItemId: string,
    config?: AxiosRequestConfig,
  ): Promise<OfficeMasterItem> {
    const response =
      await this.getRequest<{
        ok: true;
        item: OfficeMasterItem;
      }>(
        API_ENDPOINTS.OFFICE_CATALOGUE.MASTER_ITEM(
          masterItemId,
        ),
        config,
      );

    return response.data.item;
  }


  async listItems(
    params?: ListOfficeMasterItemsRequest,
    config?: AxiosRequestConfig,
  ): Promise<
    PaginatedResponse<OfficeMasterItem>
  > {
    const response =
      await this.getRequest<
        OfficeMasterItemListResponse
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
}

export const officeMasterItemService =
  new OfficeMasterItemService();

export default officeMasterItemService;
