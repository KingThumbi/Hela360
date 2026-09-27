import { useQuery } from "@tanstack/react-query";

import { useQueryScope } from "@/hooks/useQueryScope";
import { QUERY_KEYS } from "@/lib/queryKeys";
import { productService } from "@/services/products";

import type {
  ProductSalesHistoryParams,
} from "@/types/responses/product-history";

export function useProductSalesHistory(
  productId: string,
  params: ProductSalesHistoryParams = {},
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
      ? QUERY_KEYS.products.historySales(
          tenantScope,
          productId,
          params,
        )
      : QUERY_KEYS.products.disabled(
          "history-sales",
          productId,
        ),

    queryFn: () =>
      productService.listProductSalesHistory(
        productId,
        params,
      ),

    enabled:
      isTenantScopeReady &&
      Boolean(productId) &&
      (options?.enabled ?? true),
  });
}

export default useProductSalesHistory;
