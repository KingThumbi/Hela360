import {
  useQuery,
} from "@tanstack/react-query";

import { useQueryScope } from "@/hooks/useQueryScope";
import {
  QUERY_KEYS,
} from "@/lib/queryKeys";
import {
  salesService,
} from "@/services/sales";
import type {
  Sale,
} from "@/types/entities";

export function useRefundableSale(
  saleId: string,
  options?: {
    enabled?: boolean;
  },
) {
  const {
    branchScope,
    isBranchScopeReady,
  } = useQueryScope();
  const normalizedSaleId = saleId.trim();
  const enabled =
    Boolean(options?.enabled) &&
    isBranchScopeReady &&
    normalizedSaleId.length > 0;

  return useQuery<Sale>({
    queryKey:
      branchScope && normalizedSaleId
        ? QUERY_KEYS.sales.refundLookup(branchScope, normalizedSaleId)
        : QUERY_KEYS.sales.disabled("refund-lookup"),
    queryFn: () => salesService.getRefundableSale(normalizedSaleId),
    enabled,
  });
}

export default useRefundableSale;
