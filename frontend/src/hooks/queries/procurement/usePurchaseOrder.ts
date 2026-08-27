/**
 * ============================================================================
 * Hela360 Purchase Order Query
 * ============================================================================
 *
 * Retrieves a single purchase order.
 *
 * Responsibilities
 * ----------------
 * • Load a purchase order by identifier
 * • Cache purchase order records
 * • Support conditional loading
 * • Preserve full TanStack Query flexibility
 *
 * This hook powers:
 *
 * • Purchase Order Details
 * • Purchase Order Review
 * • Purchase Order Approval
 * • Purchase Order Receiving
 *
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
 * Retrieves a single purchase order.
 */
export function usePurchaseOrder<
  TData = never,
>(
  id: string,
  _options?: unknown,
) {
  return useQuery<TData>({
    queryKey:
      QUERY_KEYS.procurement.purchaseOrder(
        id,
      ),

    queryFn: () =>
      Promise.reject(
        new Error(
          "Purchase Order detail retrieval is not supported by the current backend API.",
        ),
      ),

    enabled: false,

    retry: false,
  });
}

export default usePurchaseOrder;
