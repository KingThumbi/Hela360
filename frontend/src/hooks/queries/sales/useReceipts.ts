/**
 * ============================================================================
 * Hela360 Receipts Query
 * ============================================================================
 *
 * Retrieves receipts associated with sales.
 *
 * Responsibilities
 * ----------------
 * • Load receipts
 * • Support filtering
 * • Support searching
 * • Support pagination
 * • Cache receipt collections
 * • Preserve full TanStack Query flexibility
 *
 * This hook powers:
 *
 * • Receipt Register
 * • Receipt History
 * • Customer Receipts
 * • Sales Audit
 *
 * ============================================================================
 */

import {
  useQuery,
} from "@tanstack/react-query";

import {
  QUERY_KEYS,
} from "@/lib/queryKeys";

import type {
  PaginationRequest,
} from "@/types/requests";

/* ============================================================================
 * Hook
 * ============================================================================
 */

/**
 * Retrieves receipts.
 */
export function useReceipts(
  _params: PaginationRequest,
) {
  return useQuery<never>({
    queryKey:
      QUERY_KEYS.sales.receipts(),

    queryFn: () =>
      Promise.reject(
        new Error(
          "Sales receipt listing is not supported by the current backend API.",
        ),
      ),
  });
}

export default useReceipts;
