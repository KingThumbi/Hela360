export interface CreateStockCountRequest {
  warehouse_id: string;

  idempotency_key: string;

  product_ids?: string[];

  notes?: string;
}
