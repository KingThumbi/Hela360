/**
 * Hela360 Office Catalogue Supplier contracts.
 *
 * CatalogueSupplier is platform-owned and deliberately separate from
 * tenant-owned Supplier records.
 */

import type {
  OfficeSupplierPriceEvidence,
} from "@/types/officeCatalogue";


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


export interface OfficeCatalogueSupplierMasterItem {
  id: string;
  master_code: string;
  canonical_name: string;
  review_status: string;
  is_active: boolean;
}


export interface OfficeCatalogueSupplierMapping {
  id: string;

  supplier_item_code: string | null;
  supplier_item_name: string;
  source_description: string | null;
  is_active: boolean;

  master_item: OfficeCatalogueSupplierMasterItem;

  price_observation_count: number;
  comparable_observation_count: number;
  non_comparable_observation_count: number;

  latest_comparable_price:
    | OfficeSupplierPriceEvidence
    | null;
}


export interface OfficeCatalogueSupplierDetail
  extends OfficeCatalogueSupplier {
  mappings: OfficeCatalogueSupplierMapping[];
}
