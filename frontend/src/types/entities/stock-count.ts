export interface StockCountWarehouse {
  id: string;

  code: string;

  name: string;
}

export interface StockCountUser {
  id: string;

  name: string | null;

  username: string | null;
}

export interface StockCountProduct {
  id: string;

  internal_sku: string;

  name: string;

  track_batches: boolean;

  track_expiry: boolean;
}

export interface StockCountBatch {
  id: string;

  batch_number: string | null;

  expiry_date: string | null;

  is_expired: boolean;
}

export interface StockCountSummary {
  total_items: number;

  counted_items: number;

  uncounted_items: number;

  variance_items: number;

  positive_variance_items: number;

  negative_variance_items: number;
}

export interface StockCountAdjustmentLink {
  id: string;

  adjustment_number: string;
}

export interface StockCountItem {
  id: string;

  line_number: number;

  product: StockCountProduct;

  batch: StockCountBatch | null;

  snapshot_quantity: string;

  expected_quantity: string;

  counted_quantity: string | null;

  variance_quantity: string | null;

  counted_at: string | null;

  counted_by: StockCountUser | null;

  notes: string | null;
}

export interface StockCount {
  id: string;

  count_number: string;

  status: "open" | "completed" | "cancelled";

  scope_type: "full" | "selected";

  warehouse: StockCountWarehouse;

  snapshot_at: string | null;

  started_at: string | null;

  started_by: StockCountUser | null;

  completed_at: string | null;

  completed_by: StockCountUser | null;

  cancelled_at: string | null;

  cancelled_by: StockCountUser | null;

  notes: string | null;

  adjustment: StockCountAdjustmentLink | null;

  summary: StockCountSummary;

  items: StockCountItem[];

  created_at: string | null;

  updated_at: string | null;
}
