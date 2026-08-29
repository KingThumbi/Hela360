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


interface ConfirmStockCountNoStockVariables {
  countId: string;

  productId: string;
}


export function useConfirmStockCountNoStock() {
  const queryClient = useQueryClient();

  const {
    branchScope,
  } = useQueryScope();

  return useMutation<
    StockCount,
    Error,
    ConfirmStockCountNoStockVariables
  >({
    mutationFn: ({
      countId,
      productId,
    }) =>
      inventoryService.confirmStockCountNoStock(
        countId,
        productId,
      ),

    onSuccess: async () => {
      await invalidateStockCounts(
        queryClient,
        branchScope ?? undefined,
      );
    },
  });
}


export default useConfirmStockCountNoStock;
