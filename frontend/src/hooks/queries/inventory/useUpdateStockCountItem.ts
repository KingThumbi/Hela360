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
import type {
  UpdateStockCountItemRequest,
} from "@/types/requests";

interface UpdateStockCountItemVariables {
  countId: string;
  itemId: string;
  payload: UpdateStockCountItemRequest;
}

export function useUpdateStockCountItem() {
  const queryClient = useQueryClient();
  const {
    branchScope,
  } = useQueryScope();

  return useMutation<StockCount, Error, UpdateStockCountItemVariables>({
    mutationFn: ({
      countId,
      itemId,
      payload,
    }) =>
      inventoryService.updateStockCountItem(
        countId,
        itemId,
        payload,
      ),

    onSuccess: async () => {
      await invalidateStockCounts(
        queryClient,
        branchScope ?? undefined,
      );
    },
  });
}

export default useUpdateStockCountItem;
