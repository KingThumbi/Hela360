/**
 * ============================================================================
 * Hela360 Sale Entity
 * ============================================================================
 */

import type { SaleStatus } from "@/types/enums";

import type { SaleItem } from "./sale-item";
import type { SalePayment } from "./sale-payment";

export interface Sale {
  id: string;

  tenant_id: string;

  sale_number: string | null;

  status: SaleStatus | string | null;

  branch_id: string | null;

  warehouse_id: string | null;

  till_id: string | null;

  till_shift_id: string | null;

  customer_id: string | null;

  cashier_id: string | null;

  subtotal: string;

  discount_amount: string;

  tax_amount: string;

  total_amount: string;

  paid_amount: string;

  balance_due: string;

  refunded_amount: string;

  refund_status: string;

  refund_count: number;

  refundable_amount: string;

  sold_at: string | null;

  created_at: string | null;

  updated_at: string | null;

  items?: SaleItem[];

  payments?: SalePayment[];
}
