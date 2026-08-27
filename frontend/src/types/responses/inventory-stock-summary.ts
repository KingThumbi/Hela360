export interface InventoryStockProductSummary {
  id: string;

  internal_sku: string;

  supplier_sku: string | null;

  name: string;

  generic_name: string | null;

  track_inventory: boolean;

  track_batches: boolean;

  track_expiry: boolean;

  requires_prescription: boolean;

  reorder_level: string;

  reorder_qty: string;

  is_active: boolean;
}

export interface InventoryStockWarehouseSummary {
  id: string;

  branch_id: string;

  code: string;

  name: string;

  warehouse_type: string;

  is_active: boolean;
}

export interface InventoryStockSummary {
  id: string;

  product: InventoryStockProductSummary;

  warehouse: InventoryStockWarehouseSummary;

  quantity_on_hand: string;

  quantity_reserved: string;

  quantity_available: string;

  sellable_quantity: string;

  expired_quantity: string;

  batch_count: number;

  expired_batch_count: number;

  expiring_batch_count: number;

  earliest_sellable_expiry_date: string | null;

  has_expired_stock: boolean;

  has_expiring_stock: boolean;

  is_low_stock: boolean;

  is_out_of_stock: boolean;

  created_at: string | null;

  updated_at: string | null;
}
