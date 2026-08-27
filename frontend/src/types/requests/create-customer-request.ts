/**
 * ============================================================================
 * Hela360 Create Customer Request
 * ============================================================================
 *
 * Payload accepted by the current backend Customer create route.
 *
 * ============================================================================
 */

export interface CreateCustomerRequest {
  first_name: string;
  customer_number?: string;
  last_name?: string;
  other_names?: string;
  phone?: string;
  email?: string;
  gender?: string;
  date_of_birth?: string;
  id_number?: string;
  address?: string;
  city?: string;
  is_active?: boolean;
}
