import {
  useQuery,
} from "@tanstack/react-query";

import { useQueryScope } from "@/hooks/useQueryScope";
import {
  QUERY_KEYS,
} from "@/lib/queryKeys";
import {
  inventoryService,
} from "@/services/inventory";
import type {
  GoodsReceipt,
} from "@/types/entities";

export function useGoodsReceipt(
  receiptId?: string,
) {
  const {
    branchScope,
    isBranchScopeReady,
  } = useQueryScope();
  const normalizedReceiptId = receiptId?.trim();

  return useQuery<GoodsReceipt>({
    queryKey:
      branchScope && normalizedReceiptId
        ? QUERY_KEYS.inventory.goodsReceipt(
            branchScope,
            normalizedReceiptId,
          )
        : QUERY_KEYS.inventory.disabled("goods-receipts", "detail"),

    queryFn: () =>
      inventoryService.getGoodsReceipt(normalizedReceiptId ?? ""),

    enabled:
      isBranchScopeReady &&
      Boolean(normalizedReceiptId),
  });
}

export default useGoodsReceipt;
