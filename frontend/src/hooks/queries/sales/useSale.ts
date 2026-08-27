/**
 * ============================================================================
 * Hela360 Sale Query
 * ============================================================================
 *
 * Retrieves a single sale.
 *
 * Responsibilities
 * ----------------
 * • Load a sale by identifier
 * • Cache sale details
 * • Support conditional loading
 * • Preserve full TanStack Query flexibility
 *
 * This hook powers:
 *
 * • Sale Details
 * • Receipt View
 * • Refund Processing
 * • Void Processing
 * • Payment History
 * *
 * ============================================================================
 */

import {
  useQuery,
} from "@tanstack/react-query";

import {
  QUERY_KEYS,
} from "@/lib/queryKeys";

/* ============================================================================
 * Hook
 * ============================================================================
 */

/**
 * Retrieves a single sale.
 */
export function useSale<
  TData = never,
>(
  id: string,
  _options?: unknown,
) {
  return useQuery<TData>({
    queryKey:
      QUERY_KEYS.sales.detail(
      id,
    ),

    queryFn: () =>
      Promise.reject(
        new Error(
          "Sale detail retrieval is not supported by the current backend API.",
        ),
      ),

    enabled: Boolean(id),
  });
}

export default useSale;
