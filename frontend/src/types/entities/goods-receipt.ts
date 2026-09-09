export type GoodsReceiptStatus =
  | "draft"
  | "receiving"
  | "received"
  | "under_review"
  | "approved"
  | "posted"
  | "cancelled";

export interface GoodsReceiptWarehouse {
  id: string;
  code: string;
  name: string;
}

export interface GoodsReceiptSupplier {
  id: string;
  supplier_code: string;
  name: string;
}

export interface GoodsReceiptUser {
  id: string;
  name: string | null;
  username: string | null;
}

export interface GoodsReceiptProduct {
  id: string;
  internal_sku: string;
  name: string;
}

export interface GoodsReceiptBatch {
  id: string;
  batch_number: string | null;
  expiry_date: string | null;
}

export interface GoodsReceiptItem {
  id: string;
  line_number: number;
  product: GoodsReceiptProduct;

  quantity: string;
  invoiced_quantity?: string | null;
  received_quantity?: string | null;
  accepted_quantity?: string | null;
  rejected_quantity?: string | null;
  bonus_quantity?: string | null;

  base_quantity: string;

  product_unit_id: string | null;
  unit_code: string | null;
  unit_name: string | null;
  conversion_factor_to_base: string;

  batch: GoodsReceiptBatch | null;
  batch_number: string | null;
  manufacture_date: string | null;
  expiry_date: string | null;

  unit_cost: string;
  base_unit_cost: string;

  supplier_item_code?: string | null;
  supplier_item_name?: string | null;
  supplier_pack_description?: string | null;
  supplier_batch_reference: string | null;

  discount_rate?: string | null;
  discount_amount?: string | null;
  tax_rate?: string | null;
  tax_amount?: string | null;
  net_amount?: string | null;

  discrepancy_reason?: string | null;
  discrepancy_notes?: string | null;
}

export interface GoodsReceipt {
  id: string;
  receipt_number: string;

  warehouse: GoodsReceiptWarehouse;
  supplier: GoodsReceiptSupplier | null;

  supplier_reference: string | null;
  supplier_invoice_number?: string | null;
  supplier_invoice_date?: string | null;
  payment_terms?: string | null;
  invoice_currency?: string | null;

  supplier_subtotal?: string | null;
  supplier_discount_total?: string | null;
  supplier_tax_total?: string | null;
  supplier_invoice_total?: string | null;

  calculated_subtotal?: string | null;
  calculated_tax_total?: string | null;
  calculated_total?: string | null;
  reconciliation_difference?: string | null;

  status: GoodsReceiptStatus;

  receiving_started_at?: string | null;
  receiving_started_by?: string | null;

  received_at: string | null;
  received_by: GoodsReceiptUser | null;

  under_review_at?: string | null;
  under_review_by?: string | null;

  approved_at?: string | null;
  approved_by?: string | null;

  posted_at?: string | null;
  posted_by?: string | null;

  cancelled_at?: string | null;
  cancelled_by?: string | null;

  notes: string | null;

  items: GoodsReceiptItem[];

  created_at: string | null;
  updated_at: string | null;
}
