/**
 * ============================================================================
 * Hela360 Purchase Requisitions Query
 * ============================================================================
 *
 * Purchase Requisition listing is not supported by the verified backend API.
 *
 * ============================================================================
 */

import {
  useQuery,
} from "@tanstack/react-query";

import {
  QUERY_KEYS,
} from "@/lib/queryKeys";

export function usePurchaseRequisitions(
  _params?: unknown,
) {
  return useQuery<never>({
    queryKey:
      QUERY_KEYS.procurement.root,

    queryFn: () =>
      Promise.reject(
        new Error(
          "Purchase Requisition listing is not supported by the current backend API.",
        ),
      ),

    enabled: false,

    retry: false,
  });
}

export default usePurchaseRequisitions;
