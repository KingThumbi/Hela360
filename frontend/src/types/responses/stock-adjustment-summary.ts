import type {
  StockAdjustmentReasonCode,
} from "@/types/requests";
import type {
  StockAdjustmentSource,
} from "@/types/entities/stock-adjustment";
import type {
  StockCountUser,
  StockCountWarehouse,
} from "@/types/entities";

export interface StockAdjustmentListItem {
  id: string;

  adjustment_number: string;

  status: "posted";

  warehouse: StockCountWarehouse;

  reason_code: StockAdjustmentReasonCode;

  reason: string | null;

  source: StockAdjustmentSource;

  posted_at: string | null;

  posted_by: StockCountUser | null;

  item_count: number;

  notes: string | null;

  created_at: string | null;

  updated_at: string | null;
}
