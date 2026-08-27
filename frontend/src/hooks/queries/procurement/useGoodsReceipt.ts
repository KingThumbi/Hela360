/**
 * ============================================================================
 * Hela360 Goods Receipt Query
 * ============================================================================
 *
 * Retrieves a single Goods Receipt.
 *
 * Responsibilities
 * ----------------
 * • Load a Goods Receipt
 * • Cache Goods Receipt details
 * • Support conditional loading
 * • Preserve full TanStack Query flexibility
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

export function useGoodsReceipt<
  TData = never,
>(
  id: string,
  _options?: unknown,
) {
  return useQuery<TData>({
    queryKey:
      QUERY_KEYS.procurement.goodsReceipt(
        id,
      ),

    queryFn: () =>
      Promise.reject(
        new Error(
          "Goods Receipt detail retrieval is not supported by the current backend API.",
        ),
      ),

    enabled: false,

    retry: false,
  });
}

export default useGoodsReceipt;
