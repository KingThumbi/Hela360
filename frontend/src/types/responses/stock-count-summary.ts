import type {
  StockCountSummary as StockCountLineSummary,
  StockCountAdjustmentLink,
  StockCountUser,
  StockCountWarehouse,
} from "@/types/entities";

export interface StockCountListItem {
  id: string;

  count_number: string;

  status:
    | "open"
    | "completed"
    | "cancelled"
    | "superseded";

  scope_type: "full" | "selected";

  warehouse: StockCountWarehouse;

  snapshot_at: string | null;

  started_at: string | null;

  started_by: StockCountUser | null;

  completed_at: string | null;

  cancelled_at: string | null;

  superseded_at: string | null;

  superseded_reason: string | null;

  notes: string | null;

  adjustment: StockCountAdjustmentLink | null;

  summary: StockCountLineSummary;

  created_at: string | null;

  updated_at: string | null;
}
