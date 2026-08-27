/**
 * ============================================================================
 * Hela360 Create Sale Request
 * ============================================================================
 *
 * Request payload for creating or checking out a sale.
 *
 * ============================================================================
 */

import type { CreateSaleItemRequest } from "./create-sale-item-request";
import type { CreateSalePaymentRequest } from "./create-sale-payment-request";

export interface CreateSaleRequest {
  warehouse_id?: string;

  till_id: string;

  customer_id?: string;

  notes?: string;

  items: CreateSaleItemRequest[];

  payments: CreateSalePaymentRequest[];
}
