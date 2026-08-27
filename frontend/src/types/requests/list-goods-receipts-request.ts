export interface ListGoodsReceiptsRequest {
  page?: number;

  per_page?: number;

  search?: string;

  date_from?: string;

  date_to?: string;

  warehouse_id?: string;

  supplier_id?: string;
}
