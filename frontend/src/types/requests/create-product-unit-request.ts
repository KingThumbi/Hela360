/**
 * Hela360 Create Product Unit Request
 *
 * Defines one product-specific receiving/selling representation.
 *
 * Decimal values remain strings at the frontend boundary so the browser
 * does not become the authoritative source of accounting/conversion
 * precision.
 */
export interface CreateProductUnitRequest {
  unit_id?: string;
  unit_code?: string;
  unit_name?: string;

  conversion_factor_to_base: string;

  can_sell?: boolean;
  can_receive?: boolean;

  sale_price?: string | null;
  minimum_sale_price?: string | null;
}
