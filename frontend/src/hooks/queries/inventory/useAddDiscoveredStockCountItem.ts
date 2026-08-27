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
  AddDiscoveredStockCountItemRequest,
} from "@/types/requests";


interface AddDiscoveredStockCountItemVariables {
  countId: string;

  payload: AddDiscoveredStockCountItemRequest;
}


export function useAddDiscoveredStockCountItem() {
  const queryClient = useQueryClient();

  const {
    branchScope,
  } = useQueryScope();

  return useMutation<
    StockCount,
    Error,
    AddDiscoveredStockCountItemVariables
  >({
    mutationFn: ({
      countId,
      payload,
    }) =>
      inventoryService.addDiscoveredStockCountItem(
        countId,
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


export default useAddDiscoveredStockCountItem;
