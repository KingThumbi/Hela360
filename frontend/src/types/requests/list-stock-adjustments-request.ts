import type {
  StockAdjustmentReasonCode,
} from "./create-stock-adjustment-request";

export interface ListStockAdjustmentsRequest {
  page?: number;

  per_page?: number;

  warehouse_id?: string;

  reason_code?: StockAdjustmentReasonCode;

  source_type?: "manual" | "stock_count";

  date_from?: string;

  date_to?: string;
}
