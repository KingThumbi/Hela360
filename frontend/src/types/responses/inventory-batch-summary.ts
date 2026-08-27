export interface InventoryBatchSummary {
  id: string;

  batch_number: string | null;

  expiry_date: string | null;

  manufacture_date: string | null;

  received_at: string | null;

  quantity_on_hand: string;

  quantity_reserved: string;

  quantity_available: string;

  status: string;

  is_expired: boolean;

  is_sellable: boolean;

  days_to_expiry: number | null;

  created_at: string | null;

  updated_at: string | null;
}
