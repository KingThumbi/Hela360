export interface ListStockCountsRequest {
  page?: number;

  per_page?: number;

  status?: "open" | "completed" | "cancelled";

  warehouse_id?: string;

  date_from?: string;

  date_to?: string;
}
