/**
 * ============================================================================
 * Hela360 Update Product Request
 * ============================================================================
 *
 * Approved ordinary Product master-data editing surface.
 *
 * Structural identity, lifecycle state, inventory configuration, product
 * units and product codes are intentionally excluded.
 *
 * Lifecycle transitions are owned by the dedicated archive/restore commands.
 *
 * ============================================================================
 */

export interface UpdateProductRequest {
  supplier_sku?: string | null;

  name?: string;
  generic_name?: string | null;
  description?: string | null;

  category_id?: string | null;
  brand_id?: string | null;

  requires_prescription?: boolean;
  allow_negative_stock?: boolean;

  reorder_level?: number | string;
  reorder_qty?: number | string;

  min_sale_price?: number | string | null;
  default_sale_price?: number | string | null;
  cost_price?: number | string | null;

  tax_code?: string | null;

  pack_size?: string | null;
  manufacturer?: string | null;
  country_of_origin?: string | null;
  image_url?: string | null;
}
