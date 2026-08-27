/**
 * ============================================================================
 * Hela360 Inventory Movement Entity
 * ============================================================================
 *
 * Canonical frontend representation of an inventory movement ledger record.
 *
 * Backend persistence owner: app/models/inventory.py::InventoryMovement.
 * No public backend serializer is currently verified, so this contract follows
 * the backend model's snake_case field names.
 *
 * ============================================================================
 */

export interface InventoryMovement {
  id: string;
  tenant_id: string;
  branch_id: string;
  warehouse_id: string;
  product_id: string;
  batch_id: string | null;
  movement_type: string;
  quantity: string;
  unit_cost: string | null;
  unit_price: string | null;
  reference_type: string;
  reference_id: string;
  notes: string | null;
  created_by: string;
  created_at: string | null;
  updated_at: string | null;
}
