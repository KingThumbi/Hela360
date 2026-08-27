import type {
  StockCountUser,
  StockCountWarehouse,
} from "./stock-count";

export interface StockAdjustmentProduct {
  id: string;

  internal_sku: string;

  name: string;

  track_batches: boolean;

  track_expiry: boolean;
}

export interface StockAdjustmentBatch {
  id: string;

  batch_number: string | null;

  expiry_date: string | null;
}

export interface StockAdjustmentSource {
  type: "manual" | "stock_count";

  id: string | null;

  stock_count: {
    id: string;
    count_number: string;
  } | null;
}

export interface StockAdjustmentItem {
  id: string;

  line_number: number;

  product: StockAdjustmentProduct;

  batch: StockAdjustmentBatch | null;

  stock_count_item_id: string | null;

  quantity_delta: string;

  reason: string | null;
}

export interface StockAdjustment {
  id: string;

  adjustment_number: string;

  status: "posted";

  warehouse: StockCountWarehouse;

  reason_code:
    | "stock_count"
    | "damage"
    | "expiry"
    | "breakage"
    | "correction"
    | "opening_balance"
    | "other";

  reason: string | null;

  source: StockAdjustmentSource;

  posted_at: string | null;

  posted_by: StockCountUser | null;

  notes: string | null;

  items: StockAdjustmentItem[];

  created_at: string | null;

  updated_at: string | null;
}
