import { useQuery } from "@tanstack/react-query";

import { useQueryScope } from "@/hooks/useQueryScope";
import { QUERY_KEYS } from "@/lib/queryKeys";
import { productService } from "@/services/products";

import type {
  ProductPriceTrendParams,
} from "@/types/responses/product-history";

export function useProductSalesPriceTrend(
  productId: string,
  params: ProductPriceTrendParams = {},
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
      ? QUERY_KEYS.products.historySalesPriceTrend(
          tenantScope,
          productId,
          params,
        )
      : QUERY_KEYS.products.disabled(
          "history-sales-price-trend",
          productId,
        ),

    queryFn: () =>
      productService.listProductSalesPriceTrend(
        productId,
        params,
      ),

    enabled:
      isTenantScopeReady &&
      Boolean(productId) &&
      (options?.enabled ?? true),
  });
}

export default useProductSalesPriceTrend;
