/**
 * ============================================================================
 * Hela360 Purchase Requisition Query
 * ============================================================================
 *
 * Purchase Requisition detail retrieval is not supported by the verified
 * backend API.
 *
 * ============================================================================
 */

import {
  useQuery,
} from "@tanstack/react-query";

import {
  QUERY_KEYS,
} from "@/lib/queryKeys";

export function usePurchaseRequisition<
  TData = never,
>(
  id: string,
  _options?: unknown,
) {
  void id;

  return useQuery<TData>({
    queryKey:
      QUERY_KEYS.procurement.root,

    queryFn: () =>
      Promise.reject(
        new Error(
          "Purchase Requisition detail retrieval is not supported by the current backend API.",
        ),
      ),

    enabled: false,

    retry: false,
  });
}

export default usePurchaseRequisition;
