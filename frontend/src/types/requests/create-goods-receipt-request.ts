export interface CreateGoodsReceiptItemRequest {
  product_id: string;

  product_unit_id?: string;

  quantity: string;

  batch_number?: string;

  manufacture_date?: string;

  expiry_date?: string;

  unit_cost: string;

  supplier_batch_reference?: string;
}

export interface CreateGoodsReceiptRequest {
  warehouse_id: string;

  idempotency_key: string;

  supplier_id?: string;

  supplier_reference?: string;

  received_at?: string;

  notes?: string;

  items: CreateGoodsReceiptItemRequest[];
}
