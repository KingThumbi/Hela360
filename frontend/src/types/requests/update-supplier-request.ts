/**
 * ============================================================================
 * Hela360 Update Supplier Request
 * ============================================================================
 *
 * PATCH payload accepted by the verified backend update supplier schema.
 *
 * ============================================================================
 */

export interface UpdateSupplierRequest {
  name?: string;

  legal_name?: string | null;

  contact_person?: string | null;

  email?: string | null;

  phone?: string | null;

  alternate_phone?: string | null;

  address_line_1?: string | null;

  address_line_2?: string | null;

  city?: string | null;

  county_or_region?: string | null;

  country?: string | null;

  postal_code?: string | null;

  tax_number?: string | null;

  registration_number?: string | null;

  payment_terms_days?: number;

  credit_limit?: string | number;

  currency?: string;

  notes?: string | null;
}
