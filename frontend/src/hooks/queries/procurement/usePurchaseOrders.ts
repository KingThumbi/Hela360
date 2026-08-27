/**
 * ============================================================================
 * Hela360 Purchase Orders Query
 * ============================================================================
 *
 * Retrieves a paginated collection of purchase orders.
 *
 * Responsibilities
 * ----------------
 * • Load purchase orders
 * • Support filtering
 * • Support searching
 * • Support sorting
 * • Support pagination
 * • Cache purchase order collections
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

export function usePurchaseOrders(
  _params?: unknown,
) {
  return useQuery<never>({
    queryKey:
      QUERY_KEYS.procurement.purchaseOrders(),

    queryFn: () =>
      Promise.reject(
        new Error(
          "Purchase Order listing is not supported by the current backend API.",
        ),
      ),

    enabled: false,

    retry: false,
  });
}

export default usePurchaseOrders;
