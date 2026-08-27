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
  StockAdjustment,
} from "@/types/entities";

export function useStockAdjustment(
  adjustmentId?: string,
) {
  const {
    branchScope,
    isBranchScopeReady,
  } = useQueryScope();
  const normalizedAdjustmentId = adjustmentId?.trim();

  return useQuery<StockAdjustment>({
    queryKey:
      branchScope && normalizedAdjustmentId
        ? QUERY_KEYS.inventory.stockAdjustment(
            branchScope,
            normalizedAdjustmentId,
          )
        : QUERY_KEYS.inventory.disabled("stock-adjustments", "detail"),

    queryFn: () =>
      inventoryService.getStockAdjustment(normalizedAdjustmentId ?? ""),

    enabled:
      isBranchScopeReady &&
      Boolean(normalizedAdjustmentId),
  });
}

export default useStockAdjustment;
