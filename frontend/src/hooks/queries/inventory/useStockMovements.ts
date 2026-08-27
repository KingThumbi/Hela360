/**
 * ============================================================================
 * Hela360 Stock Movements Query
 * ============================================================================
 *
 * Inventory movement listing is not supported by a verified registered backend
 * API.
 *
 * ============================================================================
 */

import {
  useQuery,
} from "@tanstack/react-query";

import {
  QUERY_KEYS,
} from "@/lib/queryKeys";

export function useStockMovements(
  _params?: unknown,
) {
  return useQuery<never>({
    queryKey:
      QUERY_KEYS.inventory.disabled("legacy", "movements"),

    queryFn: () =>
      Promise.reject(
        new Error(
          "Inventory movement listing is not supported by the current backend API.",
        ),
      ),

    enabled: false,

    retry: false,
  });
}

export default useStockMovements;
