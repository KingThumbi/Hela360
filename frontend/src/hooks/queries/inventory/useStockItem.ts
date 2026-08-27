/**
 * ============================================================================
 * Hela360 Stock Item Query
 * ============================================================================
 *
 * Inventory item detail retrieval is not supported by a verified registered
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

export function useStockItem<
  TData = never,
>(
  id: string,
  _options?: unknown,
) {
  return useQuery<TData>({
    queryKey:
      QUERY_KEYS.inventory.disabled("detail", id),

    queryFn: () =>
      Promise.reject(
        new Error(
          "Inventory item detail retrieval is not supported by the current backend API.",
        ),
      ),

    enabled: false,

    retry: false,
  });
}

export default useStockItem;
