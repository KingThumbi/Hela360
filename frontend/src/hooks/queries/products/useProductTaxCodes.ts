import {
  useQuery,
  type UseQueryResult,
} from "@tanstack/react-query";

import { useQueryScope } from "@/hooks/useQueryScope";
import { QUERY_KEYS } from "@/lib/queryKeys";
import { productService } from "@/services/products";

import type {
  ProductTaxCode,
} from "@/types/responses";

/**
 * Returns active tax classifications available to the
 * authenticated tenant for product creation and maintenance.
 */
export function useProductTaxCodes(): UseQueryResult<
  ProductTaxCode[],
  Error
> {
  const {
    tenantScope,
    isTenantScopeReady,
  } = useQueryScope();

  return useQuery({
    queryKey:
      tenantScope
        ? QUERY_KEYS.products.taxCodes(
            tenantScope,
          )
        : QUERY_KEYS.products.disabled(
            "tax-codes",
          ),

    queryFn: () =>
      productService.listTaxCodes(),

    enabled:
      isTenantScopeReady &&
      Boolean(tenantScope),

    staleTime: 5 * 60 * 1000,
  });
}

export default useProductTaxCodes;
