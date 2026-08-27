import type {
  StockCountMode,
} from "@/types/entities/stock-count";


export interface CreateStockCountRequest {
  warehouse_id: string;

  idempotency_key: string;

  product_ids?: string[];

  count_mode?: StockCountMode;

  notes?: string;
}
