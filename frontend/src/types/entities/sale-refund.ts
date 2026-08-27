/**
 * ============================================================================
 * Hela360 Sale Refund Entity
 * ============================================================================
 *
 * Verified refund result returned by the current Sales refund route, with
 * persisted refund fields represented where backend model evidence exists.
 *
 * ============================================================================
 */

export interface SaleRefund {
  id: string;

  refund_number: string;

  status: string;

  refund_total_amount: string;

  stock_returned: boolean;

  tenant_id?: string;

  sale_id?: string;

  branch_id?: string;

  warehouse_id?: string;

  till_id?: string;

  till_shift_id: string | null;

  cashier_id?: string;

  customer_id?: string | null;

  refund_subtotal?: string;

  refund_discount_amount?: string;

  refund_tax_amount?: string;

  reason?: string | null;

  notes?: string | null;

  created_at?: string;

  updated_at?: string;
}
