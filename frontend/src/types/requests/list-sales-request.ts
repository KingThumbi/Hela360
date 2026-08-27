export interface ListSalesRequest {
  page?: number;
  per_page?: number;
  search?: string;
  date_from?: string;
  date_to?: string;
  status?: string;
  customer_id?: string;
}
