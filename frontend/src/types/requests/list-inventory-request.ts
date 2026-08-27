export type InventoryStockStatusFilter =
  | "in_stock"
  | "out_of_stock"
  | "low_stock"
  | "expired_stock";

export interface ListInventoryRequest {
  page?: number;

  per_page?: number;

  search?: string;

  warehouse_id?: string;

  stock_status?: InventoryStockStatusFilter;

  expires_before?: string;
}
