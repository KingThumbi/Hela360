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
  CreateStockAdjustmentRequest,
} from "@/types/requests";

export function useCreateStockAdjustment() {
  const queryClient = useQueryClient();
  const {
    branchScope,
  } = useQueryScope();

  return useMutation<StockAdjustment, Error, CreateStockAdjustmentRequest>({
    mutationFn: (payload) =>
      inventoryService.createStockAdjustment(payload),

    onSuccess: async () => {
      await invalidateStockAdjustments(
        queryClient,
        branchScope ?? undefined,
      );
    },
  });
}

export default useCreateStockAdjustment;
