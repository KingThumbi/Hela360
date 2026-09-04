import type {
  AxiosRequestConfig,
} from "axios";

import {
  API_ENDPOINTS,
} from "@/api/endpoints";

import BaseService from "@/services/base";

import type {
  OfficeCatalogueBrandOverview,
} from "@/types/officeCatalogue";


class OfficeCatalogueBrandService extends BaseService<
  OfficeCatalogueBrandOverview
> {
  constructor() {
    super(
      API_ENDPOINTS.OFFICE_CATALOGUE.BRANDS,
    );
  }

  async getSummary(
    config?: AxiosRequestConfig,
  ): Promise<OfficeCatalogueBrandOverview> {
    const response =
      await this.getRequest<{
        ok: true;
        summary: OfficeCatalogueBrandOverview;
      }>(
        this.resource,
        config,
      );

    return response.data.summary;
  }
}


export const officeCatalogueBrandService =
  new OfficeCatalogueBrandService();

export default officeCatalogueBrandService;
