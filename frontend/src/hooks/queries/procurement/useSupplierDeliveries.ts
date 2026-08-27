/**
 * ============================================================================
 * Hela360 Supplier Deliveries Query
 * ============================================================================
 *
 * Supplier Delivery listing is not supported by the verified backend API.
 *
 * ============================================================================
 */

import {
  useQuery,
} from "@tanstack/react-query";

import {
  QUERY_KEYS,
} from "@/lib/queryKeys";

export function useSupplierDeliveries(
  _params?: unknown,
) {
  return useQuery<never>({
    queryKey:
      QUERY_KEYS.procurement.root,

    queryFn: () =>
      Promise.reject(
        new Error(
          "Supplier Delivery listing is not supported by the current backend API.",
        ),
      ),

    enabled: false,

    retry: false,
  });
}

export default useSupplierDeliveries;
