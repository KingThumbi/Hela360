export interface InventoryMovementProductSummary {
  id: string;

  internal_sku: string;

  name: string;

  generic_name: string | null;
}

export interface InventoryMovementWarehouseSummary {
  id: string;

  code: string;

  name: string;
}

export interface InventoryMovementBatchSummary {
  id: string;

  batch_number: string | null;

  expiry_date: string | null;
}

export interface InventoryMovementReferenceSummary {
  type: string;

  id: string;
}

export interface InventoryMovementPerformerSummary {
  id: string;

  name: string | null;

  username: string | null;
}

export interface InventoryMovementSummary {
  id: string;

  movement_type: string;

  quantity: string;

  product: InventoryMovementProductSummary;

  warehouse: InventoryMovementWarehouseSummary;

  batch: InventoryMovementBatchSummary | null;

  sale_item_id: string | null;

  reference: InventoryMovementReferenceSummary;

  performed_by: InventoryMovementPerformerSummary | null;

  created_at: string | null;
}
