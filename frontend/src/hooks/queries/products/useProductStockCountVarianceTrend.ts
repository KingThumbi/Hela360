import { useQuery } from "@tanstack/react-query";

import { useQueryScope } from "@/hooks/useQueryScope";
import { QUERY_KEYS } from "@/lib/queryKeys";
import { productService } from "@/services/products";

import type {
  ProductStockCountHistoryParams,
} from "@/types/responses/product-history";

export function useProductStockCountVarianceTrend(
  productId: string,
  params: ProductStockCountHistoryParams = {},
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
      ? QUERY_KEYS.products.historyStockCountVarianceTrend(
          tenantScope,
          productId,
          params,
        )
      : QUERY_KEYS.products.disabled(
          "history-stock-count-variance-trend",
          productId,
        ),

    queryFn: () =>
      productService.listProductStockCountVarianceTrend(
        productId,
        params,
      ),

    enabled:
      isTenantScopeReady &&
      Boolean(productId) &&
      (options?.enabled ?? true),
  });
}

export default useProductStockCountVarianceTrend;
