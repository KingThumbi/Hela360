export interface CreateGoodsReceiptItemRequest {
  product_id: string;

  product_unit_id?: string;

  quantity: string;

  invoiced_quantity?: string;
  received_quantity?: string;
  accepted_quantity?: string;
  rejected_quantity?: string;
  bonus_quantity?: string;

  batch_number?: string;
  manufacture_date?: string;
  expiry_date?: string;

  unit_cost: string;

  supplier_item_code?: string;
  supplier_item_name?: string;
  supplier_pack_description?: string;
  supplier_batch_reference?: string;

  discount_rate?: string;
  discount_amount?: string;
  tax_rate?: string;
  tax_amount?: string;

  discrepancy_reason?: string;
  discrepancy_notes?: string;
}

export interface CreateGoodsReceiptRequest {
  warehouse_id: string;
  idempotency_key: string;

  supplier_id?: string;
  supplier_reference?: string;

  supplier_invoice_number?: string;
  supplier_invoice_date?: string;
  payment_terms?: string;
  invoice_currency?: string;

  supplier_subtotal?: string;
  supplier_discount_total?: string;
  supplier_tax_total?: string;
  supplier_invoice_total?: string;

  received_at?: string;
  notes?: string;

  items: CreateGoodsReceiptItemRequest[];
}

export interface CreateGoodsReceiptDraftRequest {
  warehouse_id: string;
  idempotency_key: string;

  supplier_id?: string;
  supplier_reference?: string;

  supplier_invoice_number?: string;
  supplier_invoice_date?: string;
  payment_terms?: string;
  invoice_currency?: string;

  supplier_subtotal?: string;
  supplier_discount_total?: string;
  supplier_tax_total?: string;
  supplier_invoice_total?: string;

  notes?: string;
}

export interface UpdateGoodsReceiptRequest {
  warehouse_id: string;

  supplier_id?: string;
  supplier_reference?: string;

  supplier_invoice_number?: string;
  supplier_invoice_date?: string;
  payment_terms?: string;
  invoice_currency?: string;

  supplier_subtotal?: string;
  supplier_discount_total?: string;
  supplier_tax_total?: string;
  supplier_invoice_total?: string;

  notes?: string;

  items: CreateGoodsReceiptItemRequest[];
}
