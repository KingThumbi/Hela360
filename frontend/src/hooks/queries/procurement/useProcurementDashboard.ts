/**
 * ============================================================================
 * Hela360 Procurement Dashboard Query
 * ============================================================================
 *
 * Procurement dashboard retrieval is not supported by the verified backend API.
 *
 * ============================================================================
 */

import {
  useQuery,
} from "@tanstack/react-query";

import {
  QUERY_KEYS,
} from "@/lib/queryKeys";

export function useProcurementDashboard() {
  return useQuery<never>({
    queryKey:
      QUERY_KEYS.procurement.root,

    queryFn: () =>
      Promise.reject(
        new Error(
          "Procurement dashboard retrieval is not supported by the current backend API.",
        ),
      ),

    enabled: false,

    retry: false,
  });
}

export default useProcurementDashboard;
