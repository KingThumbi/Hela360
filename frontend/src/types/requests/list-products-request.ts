/**
 * ============================================================================
 * Hela360 List Products Request
 * ============================================================================
 *
 * Query parameters accepted by the verified Product list route.
 *
 * ============================================================================
 */

export interface ListProductsRequest {
  page?: number;

  per_page?: number;

  search?: string;

  is_active?: boolean;

  product_type?: string;
}
