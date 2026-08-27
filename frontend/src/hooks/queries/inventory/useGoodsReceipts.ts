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
  ListGoodsReceiptsRequest,
} from "@/types/requests";
import type {
  GoodsReceiptSummary,
} from "@/types/responses";
import type {
  PaginatedResponse,
} from "@/types/api";

export function useGoodsReceipts(
  params?: ListGoodsReceiptsRequest,
) {
  const {
    branchScope,
    isBranchScopeReady,
  } = useQueryScope();

  return useQuery<PaginatedResponse<GoodsReceiptSummary>>({
    queryKey: branchScope
      ? QUERY_KEYS.inventory.goodsReceipts(branchScope, params)
      : QUERY_KEYS.inventory.disabled("goods-receipts", "list"),

    queryFn: () =>
      inventoryService.listGoodsReceipts(params),

    enabled: isBranchScopeReady,
  });
}

export default useGoodsReceipts;
