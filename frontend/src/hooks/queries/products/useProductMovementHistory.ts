import { useQuery } from "@tanstack/react-query";

import { useQueryScope } from "@/hooks/useQueryScope";
import { QUERY_KEYS } from "@/lib/queryKeys";
import { productService } from "@/services/products";

import type {
  ProductMovementHistoryParams,
} from "@/types/responses/product-history";

export function useProductMovementHistory(
  productId: string,
  params: ProductMovementHistoryParams = {},
  options?: {
    enabled?: boolean;
  },
) {
  const {
    tenantScope,
    isTenantScopeReady,
  } = useQueryScope();

  return useQuery({
    queryKey: tenantScope
      ? QUERY_KEYS.products.historyMovements(
          tenantScope,
          productId,
          params,
        )
      : QUERY_KEYS.products.disabled(
          "history-movements",
          productId,
        ),

    queryFn: () =>
      productService.listProductMovementHistory(
        productId,
        params,
      ),

    enabled:
      isTenantScopeReady &&
      Boolean(productId) &&
      (options?.enabled ?? true),
  });
}

export default useProductMovementHistory;
