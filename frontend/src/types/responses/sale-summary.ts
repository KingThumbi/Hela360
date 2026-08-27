export interface SaleSummaryCustomer {
  id: string;
  customer_number: string;
  full_name: string | null;
  phone: string | null;
}

export interface SaleSummaryCashier {
  id: string;
  name: string | null;
  username: string | null;
}

export interface SaleSummaryTill {
  id: string;
  code: string;
  name: string;
}

export interface SaleSummary {
  id: string;
  sale_number: string | null;
  status: string | null;
  sold_at: string | null;
  created_at: string | null;
  customer: SaleSummaryCustomer | null;
  cashier: SaleSummaryCashier | null;
  till: SaleSummaryTill | null;
  till_shift_id: string | null;
  subtotal: string;
  discount_amount: string;
  tax_amount: string;
  total_amount: string;
  paid_amount: string;
  balance_due: string;
  refund_status: string | null;
  refunded_amount: string;
}
