/**
 * ============================================================================
 * Hela360 Adopt Catalogue Item Request
 * ============================================================================
 *
 * Optional tenant-owned values supplied when adopting a canonical
 * Master Catalogue item into the tenant Product catalogue.
 *
 * ============================================================================
 */

export interface AdoptCatalogueItemRequest {
  internal_sku?: string;

  name?: string;

  category_name?: string;

  brand_name?: string;

  unit_code?: string;

  unit_name?: string;
}
