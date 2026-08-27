/**
 * ============================================================================
 * Hela360 Inventory Item Entity
 * ============================================================================
 *
 * Canonical frontend representation of a stock balance record.
 *
 * Backend persistence owner: app/models/inventory.py::StockBalance.
 * No public backend serializer is currently verified, so this contract follows
 * the backend model's snake_case field names.
 *
 * ============================================================================
 */

export interface InventoryItem {
  id: string;
  tenant_id: string;
  branch_id: string;
  warehouse_id: string;
  product_id: string;
  quantity_on_hand: string;
  quantity_reserved: string;
  quantity_available: string;
  avg_unit_cost: string;
  created_at: string | null;
  updated_at: string | null;
}
