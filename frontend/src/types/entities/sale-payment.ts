/**
 * ============================================================================
 * Hela360 Sale Payment Entity
 * ============================================================================
 */

export interface SalePayment {
  id: string;

  sale_id: string;

  payment_method_id: string | null;

  amount: string;

  reference: string | null;

  paid_at: string | null;

  received_by: string | null;

  created_at: string | null;

  notes?: string | null;
}
