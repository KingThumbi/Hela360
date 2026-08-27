/**
 * ============================================================================
 * Hela360 Create Product Request
 * ============================================================================
 *
 * Payload accepted by the current backend Product create route.
 *
 * ============================================================================
 */

type ProductDecimalInput = string | number;

export interface CreateProductRequest {
  internal_sku?: string;  
  name: string;
  supplier_sku?: string;
  generic_name?: string;
  description?: string;
  category_id?: string;
  category_name?: string;
  brand_id?: string;
  brand_name?: string;
  unit_id?: string;
  unit_code?: string;
  unit_name?: string;
  product_type?: string;
  track_inventory?: boolean;
  track_batches?: boolean;
  track_expiry?: boolean;
  requires_prescription?: boolean;
  allow_negative_stock?: boolean;
  reorder_level?: ProductDecimalInput;
  reorder_qty?: ProductDecimalInput;
  min_sale_price?: ProductDecimalInput;
  default_sale_price?: ProductDecimalInput;
  cost_price?: ProductDecimalInput;
  tax_code?: string;
  pack_size?: string;
  manufacturer?: string;
  country_of_origin?: string;
  image_url?: string;
  codes?: Array<{
    code_type: string;
    code_value: string;
    is_primary?: boolean;
    generated_by_system?: boolean;
  }>;
}
