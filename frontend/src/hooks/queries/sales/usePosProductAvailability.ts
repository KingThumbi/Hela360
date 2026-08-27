import {
  useQuery,
} from "@tanstack/react-query";

import { useQueryScope } from "@/hooks/useQueryScope";
import {
  QUERY_KEYS,
} from "@/lib/queryKeys";
import {
  salesService,
} from "@/services/sales";
import type {
  PosProductAvailability,
} from "@/types/responses";

export function usePosProductAvailability({
  tillId,
  productIds,
}: {
  tillId?: string | null;
  productIds: readonly string[];
}) {
  const {
    branchScope,
    isBranchScopeReady,
  } = useQueryScope();
  const normalizedTillId = tillId?.trim() ?? "";
  const normalizedProductIds = [
    ...new Set(productIds.map((id) => id.trim()).filter(Boolean)),
  ].sort();

  return useQuery<PosProductAvailability[]>({
    queryKey:
      branchScope &&
      normalizedTillId &&
      normalizedProductIds.length > 0
        ? QUERY_KEYS.sales.availability(
            branchScope,
            normalizedTillId,
            normalizedProductIds,
          )
        : QUERY_KEYS.sales.disabled("availability"),

    queryFn: () =>
      salesService.listPosProductAvailability({
        till_id: normalizedTillId,
        product_ids: normalizedProductIds,
      }),

    enabled:
      isBranchScopeReady &&
      normalizedTillId.length > 0 &&
      normalizedProductIds.length > 0,
  });
}

export default usePosProductAvailability;
