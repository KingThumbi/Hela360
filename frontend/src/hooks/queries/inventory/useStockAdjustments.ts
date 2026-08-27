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
  PaginatedResponse,
} from "@/types/api";
import type {
  ListStockAdjustmentsRequest,
} from "@/types/requests";
import type {
  StockAdjustmentListItem,
} from "@/types/responses";

export function useStockAdjustments(
  params?: ListStockAdjustmentsRequest,
) {
  const {
    branchScope,
    isBranchScopeReady,
  } = useQueryScope();

  return useQuery<PaginatedResponse<StockAdjustmentListItem>>({
    queryKey: branchScope
      ? QUERY_KEYS.inventory.stockAdjustmentsList(branchScope, params)
      : QUERY_KEYS.inventory.disabled("stock-adjustments", "list"),

    queryFn: () =>
      inventoryService.listStockAdjustments(params),

    enabled: isBranchScopeReady,
  });
}

export default useStockAdjustments;
