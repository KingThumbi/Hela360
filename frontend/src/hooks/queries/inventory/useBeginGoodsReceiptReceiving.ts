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

export function useBeginGoodsReceiptReceiving() {
  const queryClient = useQueryClient();
  const {
    branchScope,
  } = useQueryScope();

  return useMutation<
    GoodsReceipt,
    Error,
    string
  >({
    mutationFn: (receiptId) =>
      inventoryService.beginGoodsReceiptReceiving(
        receiptId,
      ),

    onSuccess: async () => {
      await invalidateInventoryOperations(
        queryClient,
        branchScope ?? undefined,
      );
    },
  });
}

export default useBeginGoodsReceiptReceiving;
