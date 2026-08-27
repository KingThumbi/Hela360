/**
 * ============================================================================
 * Hela360 Payment Method Service
 * ============================================================================
 *
 * Canonical public service boundary for active tenant Payment Method
 * reference data used by POS checkout.
 *
 * ============================================================================
 */

import type { AxiosRequestConfig } from "axios";

import { API_ENDPOINTS } from "@/api/endpoints";
import BaseService from "@/services/base";
import type { PaymentMethod } from "@/types/entities";

interface PaymentMethodListResponse {
  ok: true;

  items: PaymentMethod[];
}

export class PaymentMethodService extends BaseService<
  PaymentMethod
> {
  constructor() {
    super(API_ENDPOINTS.PAYMENT_METHODS.ROOT);
  }

  async listPaymentMethods(
    config?: AxiosRequestConfig,
  ): Promise<PaymentMethod[]> {
    const response =
      await this.getRequest<PaymentMethodListResponse>(
        this.resource,
        config,
      );

    return response.data.items;
  }
}

export const paymentMethodService =
  new PaymentMethodService();

export default paymentMethodService;
