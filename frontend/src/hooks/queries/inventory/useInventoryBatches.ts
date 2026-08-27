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
  InventoryBatchSummary,
  InventoryStockSummary,
} from "@/types/responses";

interface InventoryBatchesResult {
  stock: InventoryStockSummary;

  items: InventoryBatchSummary[];
}

export function useInventoryBatches(
  stockBalanceId: string | null | undefined,
) {
  const {
    branchScope,
    isBranchScopeReady,
  } = useQueryScope();

  const normalizedId = stockBalanceId?.trim() ?? "";

  return useQuery<InventoryBatchesResult>({
    queryKey:
      branchScope && normalizedId
        ? QUERY_KEYS.inventory.batches(branchScope, normalizedId)
        : QUERY_KEYS.inventory.disabled("batches"),

    queryFn: () =>
      inventoryService.getStockBatches(normalizedId),

    enabled: isBranchScopeReady && normalizedId.length > 0,
  });
}

export default useInventoryBatches;
