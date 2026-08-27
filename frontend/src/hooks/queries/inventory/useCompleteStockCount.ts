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

export function useCompleteStockCount() {
  const queryClient = useQueryClient();
  const {
    branchScope,
  } = useQueryScope();

  return useMutation<StockCount, Error, string>({
    mutationFn: (countId) =>
      inventoryService.completeStockCount(countId),

    onSuccess: async () => {
      await invalidateStockCounts(
        queryClient,
        branchScope ?? undefined,
      );
    },
  });
}

export default useCompleteStockCount;
