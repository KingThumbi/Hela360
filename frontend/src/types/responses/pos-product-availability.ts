export type PosProductAvailabilityStatus =
  | "in_stock"
  | "out_of_stock"
  | "not_tracked"
  | "inactive";

export interface PosProductAvailability {
  product_id: string;

  warehouse_id: string;

  track_inventory: boolean;

  track_batches: boolean;

  track_expiry: boolean;

  requires_prescription: boolean;

  is_active: boolean;

  status: PosProductAvailabilityStatus;

  sellable_quantity: string | null;

  is_low_stock: boolean;

  is_out_of_stock: boolean;

  expired_only: boolean;

  earliest_sellable_expiry_date: string | null;
}
