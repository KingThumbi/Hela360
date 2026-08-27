/**
 * ============================================================================
 * Hela360 Payment Method Entity
 * ============================================================================
 *
 * Tenant-owned tender method reference data returned by the backend for POS
 * checkout payment selection.
 *
 * ============================================================================
 */

export interface PaymentMethod {
  id: string;

  code: string;

  name: string;

  method_type: string;

  is_active: boolean;
}
