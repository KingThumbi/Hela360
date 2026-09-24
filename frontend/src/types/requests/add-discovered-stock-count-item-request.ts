export interface AddDiscoveredStockCountItemRequest {
  product_id: string;

  batch_number?: string;

  expiry_date?: string;

  counted_quantity: string;

  product_unit_id?: string;

  notes?: string;
}
