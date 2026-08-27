import {
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

import { useQueryScope } from "@/hooks/useQueryScope";
import {
  invalidateStockAdjustments,
} from "@/lib/queryInvalidation";
import {
  inventoryService,
} from "@/services/inventory";
import type {
  StockAdjustment,
} from "@/types/entities";
import type {
  CreateStockAdjustmentFromCountRequest,
} from "@/types/requests";

interface CreateStockAdjustmentFromCountVariables {
  countId: string;
  payload: CreateStockAdjustmentFromCountRequest;
}

export function useCreateStockAdjustmentFromCount() {
  const queryClient = useQueryClient();
  const {
    branchScope,
  } = useQueryScope();

  return useMutation<
    StockAdjustment,
    Error,
    CreateStockAdjustmentFromCountVariables
  >({
    mutationFn: ({
      countId,
      payload,
    }) =>
      inventoryService.createStockAdjustmentFromCount(
        countId,
        payload,
      ),

    onSuccess: async () => {
      await invalidateStockAdjustments(
        queryClient,
        branchScope ?? undefined,
        {
          includeStockCounts: true,
        },
      );
    },
  });
}

export default useCreateStockAdjustmentFromCount;
