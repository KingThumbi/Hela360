/**
 * ============================================================================
 * Hela360 Supplier Entity
 * ============================================================================
 *
 * Canonical frontend representation of the verified backend Supplier
 * serializer payload.
 *
 * The supplier service currently returns backend JSON directly, so this entity
 * uses the backend snake_case field names truthfully until a verified service
 * mapping is introduced.
 *
 * ============================================================================
 */

export interface Supplier {
  id: string;

  tenant_id: string;

  supplier_code: string;

  name: string;

  legal_name: string | null;

  contact_person: string | null;

  email: string | null;

  phone: string | null;

  alternate_phone: string | null;

  address_line_1: string | null;

  address_line_2: string | null;

  city: string | null;

  county_or_region: string | null;

  country: string | null;

  postal_code: string | null;

  tax_number: string | null;

  registration_number: string | null;

  payment_terms_days: number;

  credit_limit: string;

  currency: string;

  notes: string | null;

  is_active: boolean;

  created_at: string | null;

  updated_at: string | null;
}
