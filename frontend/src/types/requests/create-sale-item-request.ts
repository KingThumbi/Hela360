import type { CreateSalePrescriptionContext } from "./create-sale-prescription-context";

/**
 * ============================================================================
 * Hela360 Create Sale Item Request
 * ============================================================================
 *
 * Represents a single line item in a sale creation request.
 *
 * ============================================================================
 */

export interface CreateSaleItemRequest {
  product_id?: string;

  product_unit_id?: string;

  barcode?: string;

  quantity: string | number;

  unit_price?: string | number;

  discount_amount?: string | number;

  tax_amount?: string | number;

  prescription?: CreateSalePrescriptionContext;
}
