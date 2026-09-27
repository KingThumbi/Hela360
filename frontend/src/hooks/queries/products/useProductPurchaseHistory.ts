import { useQuery } from "@tanstack/react-query";

import { useQueryScope } from "@/hooks/useQueryScope";
import { QUERY_KEYS } from "@/lib/queryKeys";
import { productService } from "@/services/products";

import type {
  ProductPurchaseHistoryParams,
} from "@/types/responses/product-history";

export function useProductPurchaseHistory(
  productId: string,
  params: ProductPurchaseHistoryParams = {},
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
      ? QUERY_KEYS.products.historyPurchases(
          tenantScope,
          productId,
          params,
        )
      : QUERY_KEYS.products.disabled(
          "history-purchases",
          productId,
        ),

    queryFn: () =>
      productService.listProductPurchaseHistory(
        productId,
        params,
      ),

    enabled:
      isTenantScopeReady &&
      Boolean(productId) &&
      (options?.enabled ?? true),
  });
}

export default useProductPurchaseHistory;
