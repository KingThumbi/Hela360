import type {
  AxiosRequestConfig,
} from "axios";

import {
  API_ENDPOINTS,
} from "@/api/endpoints";

import {
  platformApiClient,
} from "@/api/platformClient";

import BaseService from "@/services/base";

import type {
  OfficeCatalogueCategoryOverview,
} from "@/types/officeCatalogue";


class OfficeCatalogueCategoryService extends BaseService<
  OfficeCatalogueCategoryOverview
> {
  constructor() {
    super(
      API_ENDPOINTS.OFFICE_CATALOGUE.CATEGORIES,
      platformApiClient,
    );
  }

  async getSummary(
    config?: AxiosRequestConfig,
  ): Promise<OfficeCatalogueCategoryOverview> {
    const response =
      await this.getRequest<{
        ok: true;
        summary: OfficeCatalogueCategoryOverview;
      }>(
        this.resource,
        config,
      );

    return response.data.summary;
  }
}


export const officeCatalogueCategoryService =
  new OfficeCatalogueCategoryService();

export default officeCatalogueCategoryService;
