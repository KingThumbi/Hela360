export interface ListInventoryMovementsRequest {
  page?: number;

  per_page?: number;

  date_from?: string;

  date_to?: string;

  product_id?: string;

  warehouse_id?: string;

  movement_type?: string;

  reference_type?: string;

  reference_id?: string;
}
