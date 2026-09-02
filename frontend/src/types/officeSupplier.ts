/**
 * Hela360 Office Catalogue Supplier contracts.
 *
 * CatalogueSupplier is platform-owned and deliberately separate from
 * tenant-owned Supplier records.
 */

export interface OfficeCatalogueSupplier {
  id: string;
  name: string;
  country: string | null;
  is_active: boolean;

  mapping_count: number;
  price_observation_count: number;
  comparable_observation_count: number;
  non_comparable_observation_count: number;

  latest_effective_date: string | null;
  procurement_comparable: boolean;
}

export interface ListOfficeCatalogueSuppliersRequest {
  page?: number;
  per_page?: number;
  search?: string;
  is_active?: boolean;
}
