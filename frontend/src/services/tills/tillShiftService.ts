/**
 * Canonical public service boundary for operational TillShift lifecycle.
 */

import type { AxiosRequestConfig } from "axios";

import { API_ENDPOINTS } from "@/api/endpoints";
import BaseService from "@/services/base";
import type {
  TillShift,
  TillShiftReconciliation,
} from "@/types/entities";
import type {
  CloseTillShiftRequest,
  OpenTillShiftRequest,
} from "@/types/requests";

interface CurrentTillShiftResponse {
  ok: true;

  item: TillShift | null;
}

interface TillShiftMutationResponse {
  ok: true;

  message: string;

  item: TillShift;
}

interface CloseTillShiftResponse
  extends TillShiftMutationResponse {
  reconciliation: TillShiftReconciliation;
}

export class TillShiftService extends BaseService<TillShift> {
  constructor() {
    super(API_ENDPOINTS.TILL_SHIFTS.ROOT);
  }

  async getCurrent(
    tillId?: string,
    config?: AxiosRequestConfig,
  ): Promise<TillShift | null> {
    const response =
      await this.getRequest<CurrentTillShiftResponse>(
        API_ENDPOINTS.TILL_SHIFTS.CURRENT,
        {
          ...config,
          params: {
            ...config?.params,
            ...(tillId ? { till_id: tillId } : {}),
          },
        },
      );

    return response.data.item;
  }

  async open(
    payload: OpenTillShiftRequest,
    config?: AxiosRequestConfig,
  ): Promise<TillShift> {
    const response =
      await this.postRequest<TillShiftMutationResponse>(
        API_ENDPOINTS.TILL_SHIFTS.OPEN,
        payload,
        config,
      );

    return response.data.item;
  }

  async takeover(
    id: string,
  ): Promise<TillShift> {
    const response =
      await this.postRequest<TillShiftMutationResponse>(
        `/till-shifts/${id}/takeover`,
        {},
      );

    return response.data.item;
  }

  async close(
    id: string,
    payload: CloseTillShiftRequest,
    config?: AxiosRequestConfig,
  ): Promise<CloseTillShiftResponse> {
    const response =
      await this.postRequest<CloseTillShiftResponse>(
        API_ENDPOINTS.TILL_SHIFTS.CLOSE(id),
        payload,
        config,
      );

    return response.data;
  }
}

export const tillShiftService =
  new TillShiftService();

export default tillShiftService;
