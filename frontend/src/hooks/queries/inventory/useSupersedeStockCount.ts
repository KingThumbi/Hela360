import {
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

import { useQueryScope } from "@/hooks/useQueryScope";
import {
  invalidateStockCounts,
} from "@/lib/queryInvalidation";
import {
  inventoryService,
} from "@/services/inventory";
import type {
  StockCount,
} from "@/types/entities";

interface SupersedeStockCountInput {
  countId: string;

  reason: string;
}

export function useSupersedeStockCount() {
  const queryClient = useQueryClient();

  const {
    branchScope,
  } = useQueryScope();

  return useMutation<
    StockCount,
    Error,
    SupersedeStockCountInput
  >({
    mutationFn: ({
      countId,
      reason,
    }) =>
      inventoryService.supersedeStockCount(
        countId,
        {
          reason,
        },
      ),

    onSuccess: async () => {
      await invalidateStockCounts(
        queryClient,
        branchScope ?? undefined,
      );
    },
  });
}

export default useSupersedeStockCount;
