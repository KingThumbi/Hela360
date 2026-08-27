/**
 * ============================================================================
 * Hela360 Goods Receipts Query
 * ============================================================================
 *
 * Retrieves a paginated collection of Goods Receipts.
 *
 * Responsibilities
 * ----------------
 * • Load Goods Receipts
 * • Support filtering
 * • Support searching
 * • Support sorting
 * • Support pagination
 * • Cache Goods Receipt collections
 *
 * Goods Receipts represent physical receipt of goods into the warehouse and
 * form the bridge between Procurement and Inventory.
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

export function useGoodsReceipts(
  _params?: unknown,
) {
  return useQuery<never>({
    queryKey:
      QUERY_KEYS.procurement.goodsReceipts(),

    queryFn: () =>
      Promise.reject(
        new Error(
          "Goods Receipt listing is not supported by the current backend API.",
        ),
      ),

    enabled: false,

    retry: false,
  });
}

export default useGoodsReceipts;
