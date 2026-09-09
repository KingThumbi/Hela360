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
  CreateGoodsReceiptDraftRequest,
} from "@/types/requests";

export function useCreateGoodsReceiptDraft() {
  const queryClient = useQueryClient();
  const {
    branchScope,
  } = useQueryScope();

  return useMutation<
    GoodsReceipt,
    Error,
    CreateGoodsReceiptDraftRequest
  >({
    mutationFn: (payload) =>
      inventoryService.createGoodsReceiptDraft(payload),

    onSuccess: async () => {
      await invalidateInventoryOperations(
        queryClient,
        branchScope ?? undefined,
      );
    },
  });
}

export default useCreateGoodsReceiptDraft;
