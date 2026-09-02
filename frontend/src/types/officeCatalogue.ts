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
