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
  ListStockCountsRequest,
} from "@/types/requests";
import type {
  StockCountListItem,
} from "@/types/responses";
import type {
  PaginatedResponse,
} from "@/types/api";

export function useStockCounts(
  params?: ListStockCountsRequest,
) {
  const {
    branchScope,
    isBranchScopeReady,
  } = useQueryScope();

  return useQuery<PaginatedResponse<StockCountListItem>>({
    queryKey: branchScope
      ? QUERY_KEYS.inventory.stockCountsList(branchScope, params)
      : QUERY_KEYS.inventory.disabled("stock-counts", "list"),

    queryFn: () =>
      inventoryService.listStockCounts(params),

    enabled: isBranchScopeReady,
  });
}

export default useStockCounts;
