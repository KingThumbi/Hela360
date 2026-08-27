/**
 * Canonical public service boundary for active branch Till discovery.
 */

import type { AxiosRequestConfig } from "axios";

import { API_ENDPOINTS } from "@/api/endpoints";
import BaseService from "@/services/base";
import type { Till } from "@/types/entities";

interface TillListResponse {
  ok: true;

  items: Till[];
}

export class TillService extends BaseService<Till> {
  constructor() {
    super(API_ENDPOINTS.TILLS.ROOT);
  }

  async listTills(
    config?: AxiosRequestConfig,
  ): Promise<Till[]> {
    const response =
      await this.getRequest<TillListResponse>(
        this.resource,
        config,
      );

    return response.data.items;
  }
}

export const tillService = new TillService();

export default tillService;
