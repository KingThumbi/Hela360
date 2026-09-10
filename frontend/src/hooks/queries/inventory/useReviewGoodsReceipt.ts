import {
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

import {
  invalidateInventoryOperations,
} from "@/lib/queryInvalidation";
import { useQueryScope } from "@/hooks/useQueryScope";
import { inventoryService } from "@/services/inventory";

export function useReviewGoodsReceipt() {
  const queryClient = useQueryClient();
  const { branchScope } = useQueryScope();

  return useMutation({
    mutationFn: (receiptId: string) =>
      inventoryService.reviewGoodsReceipt(receiptId),

    onSuccess: async () => {
      if (!branchScope) {
        return;
      }

      await invalidateInventoryOperations(
        queryClient,
        branchScope,
      );
    },
  });
}

export default useReviewGoodsReceipt;
