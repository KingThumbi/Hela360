/**
 * ============================================================================
 * Hela360 Create Sale Payment Request
 * ============================================================================
 *
 * Represents a payment submitted during sale creation.
 *
 * ============================================================================
 */

export interface CreateSalePaymentRequest {
  payment_method_id: string;

  amount: string | number;

  reference?: string;
}
