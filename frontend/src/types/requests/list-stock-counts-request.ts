export interface ListStockCountsRequest {
  page?: number;

  per_page?: number;

  status?: "open" | "completed" | "cancelled";

  lifecycle?:
    | "counting"
    | "awaiting_posting"
    | "posted"
    | "completed"
    | "cancelled";

  warehouse_id?: string;

  date_from?: string;

  date_to?: string;
}
