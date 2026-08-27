/**
 * ============================================================================
 * Hela360 Refund Sale Request
 * ============================================================================
 *
 * Payload for the verified Sales refund route.
 *
 * The backend receives `sale_id` as the route parameter for
 * POST /sales/<sale_id>/refund. It is included here so a frontend service can
 * route the request without treating it as a body field.
 *
 * ============================================================================
 */

export interface RefundSaleItemRequest {
  sale_item_id: string;

  quantity: string | number;

  return_to_stock?: boolean;

  condition_note?: string;
}

export interface RefundSaleRequest {
  sale_id: string;

  items: RefundSaleItemRequest[];

  reason?: string;

  notes?: string;
}
