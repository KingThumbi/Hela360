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
  ListOfficeCatalogueSuppliersRequest,
  OfficeCatalogueSupplier,
  OfficeCatalogueSupplierDetail,
} from "@/types/officeSupplier";


interface OfficeCatalogueSupplierListResponse {
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

  suppliers: OfficeCatalogueSupplier[];
}


class OfficeCatalogueSupplierService extends BaseService<
  OfficeCatalogueSupplier
> {
  constructor() {
    super(
      API_ENDPOINTS.OFFICE_CATALOGUE.SUPPLIERS,
    );
  }


  async getSupplier(
    supplierId: string,
    config?: AxiosRequestConfig,
  ): Promise<OfficeCatalogueSupplierDetail> {
    const response =
      await this.getRequest<{
        ok: true;
        supplier: OfficeCatalogueSupplierDetail;
      }>(
        API_ENDPOINTS.OFFICE_CATALOGUE.SUPPLIER(
          supplierId,
        ),
        config,
      );

    return response.data.supplier;
  }


  async listSuppliers(
    params?: ListOfficeCatalogueSuppliersRequest,
    config?: AxiosRequestConfig,
  ): Promise<
    PaginatedResponse<OfficeCatalogueSupplier>
  > {
    const response =
      await this.getRequest<
        OfficeCatalogueSupplierListResponse
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
      items: response.data.suppliers,
      pagination:
        response.data.pagination,
    };
  }
}


export const officeCatalogueSupplierService =
  new OfficeCatalogueSupplierService();

export default officeCatalogueSupplierService;
