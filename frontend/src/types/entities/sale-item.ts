/**
 * ============================================================================
 * Hela360 Sale Item Entity
 * ============================================================================
 *
 * Represents a single line item belonging to a sale.
 *
 * ============================================================================
 */

export interface SaleItem {
  id: string;

  sale_id: string;

  product_id: string | null;

  product_name?: string | null;

  sku?: string | null;

  quantity: string;

  unit_price: string;

  discount_amount: string;

  tax_amount: string;

  line_total: string;

  refunded_quantity?: string;

  remaining_refundable_quantity?: string;

  is_refundable?: boolean;

  created_at: string | null;
}
