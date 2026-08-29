export type StockCountMode =
  | "blind"
  | "visible";

export type StockCountSourceType =
  | "snapshot"
  | "discovered";


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


export type StockCountScopeResolutionStatus =
  | "unresolved"
  | "physical_lines"
  | "no_stock_confirmed";


export interface StockCountScopeProduct {
  product: StockCountProduct;

  resolution_status: StockCountScopeResolutionStatus;

  /*
   * Number of physical Stock Count identities currently represented
   * by snapshot or discovered lines for this selected Product.
   *
   * This is a line count, not a stock quantity.
   */
  physical_line_count: number;

  no_stock_confirmed_at: string | null;

  no_stock_confirmed_by: StockCountUser | null;
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

  /*
   * Variance fields are intentionally absent while an open
   * blind count is in progress.
   */
  variance_items?: number;

  positive_variance_items?: number;

  negative_variance_items?: number;
}


export interface StockCountAdjustmentLink {
  id: string;

  adjustment_number: string;
}


export interface StockCountItem {
  id: string;

  line_number: number;

  source_type: StockCountSourceType;

  product: StockCountProduct;

  /*
   * Canonical inventory batch attached to snapshot lines.
   *
   * Discovered lines initially have no InventoryBatch and
   * therefore return null here.
   */
  batch: StockCountBatch | null;

  observed_batch_number: string | null;

  observed_expiry_date: string | null;

  /*
   * System-derived quantities are deliberately omitted from
   * open blind-count responses.
   */
  snapshot_quantity?: string;

  expected_quantity?: string;

  counted_quantity: string | null;

  variance_quantity?: string | null;

  counted_at: string | null;

  counted_by: StockCountUser | null;

  notes: string | null;
}


export interface StockCount {
  id: string;

  count_number: string;

  status:
    | "open"
    | "completed"
    | "cancelled";

  scope_type:
    | "full"
    | "selected";

  count_mode: StockCountMode;

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

  /*
   * Explicit selected Product membership.
   *
   * Full Warehouse counts return an empty array.
   */
  scope_products: StockCountScopeProduct[];

  items: StockCountItem[];

  created_at: string | null;

  updated_at: string | null;
}
