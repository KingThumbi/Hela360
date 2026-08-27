import {
  useQuery,
} from "@tanstack/react-query";

import { useQueryScope } from "@/hooks/useQueryScope";
import {
  QUERY_KEYS,
} from "@/lib/queryKeys";
import {
  inventoryService,
} from "@/services/inventory";
import type {
  StockCount,
} from "@/types/entities";

export function useStockCount(
  countId?: string,
) {
  const {
    branchScope,
    isBranchScopeReady,
  } = useQueryScope();
  const normalizedCountId = countId?.trim();

  return useQuery<StockCount>({
    queryKey:
      branchScope && normalizedCountId
        ? QUERY_KEYS.inventory.stockCount(
            branchScope,
            normalizedCountId,
          )
        : QUERY_KEYS.inventory.disabled("stock-counts", "detail"),

    queryFn: () =>
      inventoryService.getStockCount(normalizedCountId ?? ""),

    enabled:
      isBranchScopeReady &&
      Boolean(normalizedCountId),
  });
}

export default useStockCount;
