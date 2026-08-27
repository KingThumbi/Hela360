export interface SaleReceiptSeller {
  id: string;
  display_name: string | null;
  legal_name: string | null;
  phone: string | null;
  email: string | null;
  currency: string | null;
}

export interface SaleReceiptBranch {
  id: string;
  code: string | null;
  name: string | null;
  phone: string | null;
  email: string | null;
  address_line1: string | null;
  address_line2: string | null;
  city: string | null;
  county_state: string | null;
  country: string | null;
}

export interface SaleReceiptCustomer {
  id: string;
  customer_number: string;
  full_name: string | null;
  phone: string | null;
}

export interface SaleReceiptSale {
  id: string;
  sale_number: string | null;
  status: string | null;
  sold_at: string | null;
  created_at: string | null;
  till_shift_id: string | null;
  refund_status: string | null;
  refunded_amount: string;
}

export interface SaleReceiptItem {
  id: string;
  product_id: string | null;
  description: string;
  sku: string | null;
  quantity: string;
  unit_price: string;
  discount_amount: string;
  tax_amount: string;
  line_total: string;
}

export interface SaleReceiptPaymentMethod {
  id: string;
  name: string;
  code: string;
  method_type: string;
}

export interface SaleReceiptPayment {
  id: string;
  payment_method_id: string | null;
  payment_method: SaleReceiptPaymentMethod | null;
  amount: string;
  reference: string | null;
  paid_at: string | null;
}

export interface SaleReceiptTotals {
  subtotal: string;
  discount_amount: string;
  tax_amount: string;
  total_amount: string;
  paid_amount: string;
  balance_due: string;
  currency: string | null;
}

export interface SaleReceiptCashier {
  id: string;
  name: string | null;
  username: string | null;
}

export interface SaleReceiptTill {
  id: string;
  code: string;
  name: string;
}

export interface SaleReceiptTillShift {
  id: string;
  opened_at: string | null;
  closed_at: string | null;
  status: string;
}

export interface SaleReceipt {
  sale: SaleReceiptSale;
  seller: SaleReceiptSeller;
  branch: SaleReceiptBranch;
  customer: SaleReceiptCustomer | null;
  items: SaleReceiptItem[];
  payments: SaleReceiptPayment[];
  totals: SaleReceiptTotals;
  cashier: SaleReceiptCashier | null;
  till: SaleReceiptTill | null;
  till_shift: SaleReceiptTillShift | null;
}
