export interface OfficeMasterItem {
  id: string;
  master_code: string;
  canonical_name: string;
  brand_name: string | null;
  generic_name: string | null;
  strength: string | null;
  dosage_form: string | null;
  pack_quantity: string | null;
  pack_unit: string | null;
  pack_type: string | null;
  item_class: string | null;
  category_name: string | null;
  subcategory_name: string | null;
  manufacturer: string | null;
  country_of_origin: string | null;
  cold_chain: boolean | null;
  restricted_item: boolean | null;
  requires_prescription: boolean | null;
  tax_classification: string | null;
  review_status: string;
  is_active: boolean;
}

export interface ListOfficeMasterItemsRequest {
  page?: number;
  per_page?: number;
  search?: string;
  review_status?: string;
  is_active?: boolean;
  item_class?: string;
  category?: string;
  dosage_form?: string;
}


export interface OfficeSupplierPriceEvidence {
  id: string;
  source_offer_key: string | null;
  price_type: string;
  amount: string;
  currency: string;
  discount_percent: string | null;
  vat_source: string | null;
  effective_date: string | null;
  source_document: string | null;
  source_location: string | null;
  is_comparable_procurement: boolean;
}


export interface OfficeCatalogueSupplierEvidence {
  id: string;
  name: string;
  country: string | null;
  is_active: boolean;
}


export interface OfficeSupplierMappingEvidence {
  id: string;

  supplier: OfficeCatalogueSupplierEvidence;

  supplier_item_code: string | null;
  supplier_item_name: string;
  source_description: string | null;
  is_active: boolean;

  latest_comparable_price:
    | OfficeSupplierPriceEvidence
    | null;

  prices: OfficeSupplierPriceEvidence[];
}


export interface OfficeMasterItemSupplierEvidence {
  master_item_id: string;
  master_code: string;
  canonical_name: string;

  mapping_count: number;
  price_observation_count: number;
  comparable_observation_count: number;

  mappings: OfficeSupplierMappingEvidence[];
}


export interface OfficeMasterItemApprovalResult {
  id: string;
  master_code: string;
  canonical_name: string;
  review_status: string;
  is_active: boolean;
}


export interface OfficeCatalogueDataQualityCatalogue {
  total: number;
  approved: number;
  draft: number;
  active: number;
  inactive: number;
}


export interface OfficeCatalogueDataQualityEnrichment {
  categorized: number;
  uncategorized: number;
  classified: number;
  unclassified: number;
  dosage_form_populated: number;
  dosage_form_missing: number;
  complete_pack_definition: number;
  incomplete_pack_definition: number;
  generic_name_populated: number;
  generic_name_missing: number;
  manufacturer_populated: number;
  manufacturer_missing: number;
}


export interface OfficeCatalogueDataQualityProvenance {
  with_supplier_mapping: number;
  without_supplier_mapping: number;
  with_price_evidence: number;
  without_price_evidence: number;
  with_comparable_evidence: number;
  with_dated_comparable_evidence: number;
}


export interface OfficeCatalogueDataQualitySummary {
  catalogue: OfficeCatalogueDataQualityCatalogue;
  enrichment: OfficeCatalogueDataQualityEnrichment;
  provenance: OfficeCatalogueDataQualityProvenance;
}


export interface OfficeCatalogueSubcategorySummary {
  name: string;
  item_count: number;
}


export interface OfficeCatalogueCategorySummary {
  name: string;
  item_count: number;
  approved_count: number;
  draft_count: number;
  active_count: number;
  inactive_count: number;
  subcategories: OfficeCatalogueSubcategorySummary[];
}


export interface OfficeCatalogueCategoryOverview {
  total_items: number;
  categorized_items: number;
  uncategorized_items: number;
  category_count: number;
  categories: OfficeCatalogueCategorySummary[];
}
