import {
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

import { useQueryScope } from "@/hooks/useQueryScope";
import {
  invalidateInventoryOperations,
} from "@/lib/queryInvalidation";
import {
  inventoryService,
} from "@/services/inventory";
import type {
  GoodsReceipt,
} from "@/types/entities";
import type {
  UpdateGoodsReceiptRequest,
} from "@/types/requests";

interface UpdateGoodsReceiptVariables {
  receiptId: string;
  payload: UpdateGoodsReceiptRequest;
}

export function useUpdateGoodsReceipt() {
  const queryClient = useQueryClient();
  const {
    branchScope,
  } = useQueryScope();

  return useMutation<
    GoodsReceipt,
    Error,
    UpdateGoodsReceiptVariables
  >({
    mutationFn: ({
      receiptId,
      payload,
    }) =>
      inventoryService.updateGoodsReceipt(
        receiptId,
        payload,
      ),

    onSuccess: async () => {
      await invalidateInventoryOperations(
        queryClient,
        branchScope ?? undefined,
      );
    },
  });
}

export default useUpdateGoodsReceipt;
