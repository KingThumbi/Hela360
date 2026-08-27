/**
 * Canonical public service boundary for active branch Warehouse discovery.
 */

import type { AxiosRequestConfig } from "axios";

import { API_ENDPOINTS } from "@/api/endpoints";
import BaseService from "@/services/base";
import type { Warehouse } from "@/types/entities";

interface WarehouseListResponse {
  ok: true;

  items: Warehouse[];
}

export class WarehouseService extends BaseService<Warehouse> {
  constructor() {
    super(API_ENDPOINTS.WAREHOUSES.ROOT);
  }

  async listWarehouses(
    config?: AxiosRequestConfig,
  ): Promise<Warehouse[]> {
    const response =
      await this.getRequest<WarehouseListResponse>(
        this.resourceUrl(),
        config,
      );

    return response.data.items;
  }
}

export const warehouseService = new WarehouseService();

export default warehouseService;
