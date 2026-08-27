/**
 * ============================================================================
 * Hela360 Product Entity
 * ============================================================================
 *
 * Canonical frontend representation of the backend Product serializer.
 *
 * The current Product service returns backend JSON directly, so this contract
 * intentionally uses snake_case field names.
 *
 * ============================================================================
 */

export interface Product {
  id: string;
  tenant_id: string;
  internal_sku: string;
  supplier_sku: string | null;
  name: string;
  generic_name: string | null;
  description: string | null;
  product_type: string;
  track_inventory: boolean;
  track_batches: boolean;
  track_expiry: boolean;
  requires_prescription: boolean;
  allow_negative_stock: boolean;
  reorder_level: string | null;
  reorder_qty: string | null;
  min_sale_price: string | null;
  default_sale_price: string | null;
  cost_price: string | null;
  tax_code: string | null;
  pack_size: string | null;
  manufacturer: string | null;
  country_of_origin: string | null;
  image_url: string | null;
  is_active: boolean;
  category: {
    id: string;
    name: string;
    code: string | null;
  } | null;
  brand: {
    id: string;
    name: string;
  } | null;
  unit: {
    id: string;
    code: string;
    name: string;
  } | null;
  codes: Array<{
    id: string;
    code_type: string;
    code_value: string;
    product_unit_id: string | null;
    is_primary: boolean;
    generated_by_system: boolean;
  }>;
  created_at: string | null;
  updated_at: string | null;
}
