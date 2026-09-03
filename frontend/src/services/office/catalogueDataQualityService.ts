import type {
  AxiosRequestConfig,
} from "axios";

import {
  API_ENDPOINTS,
} from "@/api/endpoints";

import BaseService from "@/services/base";

import type {
  OfficeCatalogueDataQualitySummary,
} from "@/types/officeCatalogue";


class OfficeCatalogueDataQualityService extends BaseService<
  OfficeCatalogueDataQualitySummary
> {
  constructor() {
    super(
      API_ENDPOINTS.OFFICE_CATALOGUE.DATA_QUALITY,
    );
  }

  async getSummary(
    config?: AxiosRequestConfig,
  ): Promise<OfficeCatalogueDataQualitySummary> {
    const response =
      await this.getRequest<{
        ok: true;
        summary: OfficeCatalogueDataQualitySummary;
      }>(
        this.resource,
        config,
      );

    return response.data.summary;
  }
}


export const officeCatalogueDataQualityService =
  new OfficeCatalogueDataQualityService();

export default officeCatalogueDataQualityService;
