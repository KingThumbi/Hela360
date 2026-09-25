export interface ListStockCountsRequest {
  page?: number;

  per_page?: number;

  status?:
    | "open"
    | "completed"
    | "cancelled"
    | "superseded";

  lifecycle?:
    | "counting"
    | "awaiting_posting"
    | "posted"
    | "completed"
    | "cancelled"
    | "superseded";

  warehouse_id?: string;

  date_from?: string;

  date_to?: string;
}
