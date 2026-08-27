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
  CreateGoodsReceiptRequest,
} from "@/types/requests";

export function useCreateGoodsReceipt() {
  const queryClient = useQueryClient();
  const {
    branchScope,
  } = useQueryScope();

  return useMutation<GoodsReceipt, Error, CreateGoodsReceiptRequest>({
    mutationFn: (payload) =>
      inventoryService.createGoodsReceipt(payload),

    onSuccess: async () => {
      await invalidateInventoryOperations(
        queryClient,
        branchScope ?? undefined,
      );
    },
  });
}

export default useCreateGoodsReceipt;
