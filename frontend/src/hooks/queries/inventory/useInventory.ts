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
  ListInventoryRequest,
} from "@/types/requests";
import type {
  InventoryStockSummary,
} from "@/types/responses";
import type {
  PaginatedResponse,
} from "@/types/api";

export function useInventory(
  params?: ListInventoryRequest,
) {
  const {
    branchScope,
    isBranchScopeReady,
  } = useQueryScope();

  return useQuery<PaginatedResponse<InventoryStockSummary>>({
    queryKey: branchScope
      ? QUERY_KEYS.inventory.list(branchScope, params)
      : QUERY_KEYS.inventory.disabled("list"),

    queryFn: () =>
      inventoryService.listStock(params),

    enabled: isBranchScopeReady,
  });
}

export default useInventory;
