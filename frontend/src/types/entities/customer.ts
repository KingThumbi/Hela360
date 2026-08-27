/**
 * ============================================================================
 * Hela360 Customer Entity
 * ============================================================================
 *
 * Canonical frontend representation of the backend Customer serializer.
 *
 * The current Customer service returns backend JSON directly, so this contract
 * intentionally uses snake_case field names.
 *
 * ============================================================================
 */

export interface Customer {
  id: string;
  tenant_id: string;
  customer_number: string;
  first_name: string;
  last_name: string | null;
  other_names: string | null;
  full_name: string;
  phone: string | null;
  email: string | null;
  gender: string | null;
  date_of_birth: string | null;
  id_number: string | null;
  address: string | null;
  city: string | null;
  loyalty_points: string;
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
}
