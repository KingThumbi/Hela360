/**
 * Hela360 Update Product Unit Request
 *
 * Structural identity is intentionally excluded:
 *
 * - tenant_id
 * - product_id
 * - unit_id
 * - is_base
 * - is_active
 *
 * Lifecycle state is managed through archive/restore commands.
 */
export interface UpdateProductUnitRequest {
  conversion_factor_to_base?: string;

  can_sell?: boolean;
  can_receive?: boolean;

  sale_price?: string | null;
  minimum_sale_price?: string | null;
}
