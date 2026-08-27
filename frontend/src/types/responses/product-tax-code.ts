/**
 * ============================================================================
 * Product Tax Code
 * ============================================================================
 *
 * Tenant-owned product tax classification returned by the Hela360 API.
 *
 * ============================================================================
 */

export interface ProductTaxCode {
  id: string;
  code: string;
  name: string;
  rate: string;
  description: string | null;
}
