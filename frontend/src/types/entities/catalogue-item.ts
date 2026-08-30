/**
 * ============================================================================
 * Hela360 Catalogue Item
 * ============================================================================
 *
 * Tenant-visible representation of an approved, active platform MasterItem.
 *
 * Master Catalogue data answers:
 *
 * "What is this item?"
 *
 * Tenant Product data remains responsible for:
 *
 * "How does this tenant sell and manage it?"
 *
 * ============================================================================
 */

export interface CatalogueItemAdoption {
  is_adopted: boolean;

  product_id: string | null;

  internal_sku: string | null;

  product_name: string | null;

  product_is_active: boolean | null;
}

export interface CatalogueItem {
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

  adoption: CatalogueItemAdoption;
}

/**
 * Tenant Product summary returned immediately after
 * a successful Master Catalogue adoption.
 *
 * This is intentionally not the full Product entity.
 */
export interface CatalogueAdoptedProduct {
  id: string;

  tenant_id: string;

  master_item_id: string;

  internal_sku: string;

  name: string;

  generic_name: string | null;

  category_id: string | null;

  brand_id: string | null;

  unit_id: string | null;

  requires_prescription: boolean;

  manufacturer: string | null;

  country_of_origin: string | null;

  is_active: boolean;
}
