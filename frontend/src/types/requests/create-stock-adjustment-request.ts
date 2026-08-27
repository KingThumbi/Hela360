export type StockAdjustmentReasonCode =
  | "stock_count"
  | "damage"
  | "expiry"
  | "breakage"
  | "correction"
  | "opening_balance"
  | "other";

export interface CreateStockAdjustmentItemRequest {
  product_id: string;

  batch_id?: string;

  quantity_delta: string;

  reason?: string;
}

export interface CreateStockAdjustmentRequest {
  warehouse_id: string;

  idempotency_key: string;

  reason_code?: Exclude<StockAdjustmentReasonCode, "stock_count">;

  reason?: string;

  notes?: string;

  items: CreateStockAdjustmentItemRequest[];
}

export interface CreateStockAdjustmentFromCountRequest {
  idempotency_key: string;

  reason_code?: "stock_count";

  reason?: string;

  notes?: string;
}
