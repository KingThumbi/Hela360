/**
 * ============================================================================
 * Hela360 List Catalogue Items Request
 * ============================================================================
 *
 * Query parameters accepted by the tenant-facing Master Catalogue list API.
 *
 * ============================================================================
 */

export type CatalogueAdoptionStatus =
  | "all"
  | "available"
  | "adopted";

export interface ListCatalogueItemsRequest {
  page?: number;

  per_page?: number;

  search?: string;

  item_class?: string;

  category?: string;

  dosage_form?: string;

  adoption_status?: CatalogueAdoptionStatus;
}
