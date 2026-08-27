/**
 * ============================================================================
 * Hela360 Receipt Query
 * ============================================================================
 *
 * Retrieves a single receipt.
 *
 * Responsibilities
 * ----------------
 * • Load receipt details
 * • Cache receipt data
 * • Support conditional loading
 * • Preserve full TanStack Query flexibility
 *
 * This hook powers:
 *
 * • Receipt Viewer
 * • Receipt Printing
 * • Receipt Reprint
 * • Customer Receipt Lookup
 *
 * ============================================================================
 */

import {
  useQuery,
} from "@tanstack/react-query";

import {
  QUERY_KEYS,
} from "@/lib/queryKeys";
import { useQueryScope } from "@/hooks/useQueryScope";
import {
  salesService,
} from "@/services/sales";
import type {
  SaleReceipt,
} from "@/types/responses";

/* ============================================================================
 * Hook
 * ============================================================================
 */

/**
 * Retrieves a single receipt.
 */
export function useReceipt<
  TData = SaleReceipt,
>(
  saleId: string,
  options?: {
    enabled?: boolean;
    select?: (receipt: SaleReceipt) => TData;
  },
) {
  const {
    branchScope,
    isBranchScopeReady,
  } = useQueryScope();
  const normalizedSaleId = saleId.trim();
  const enabled =
    isBranchScopeReady &&
    normalizedSaleId.length > 0 &&
    (options?.enabled ?? true);

  return useQuery<SaleReceipt, Error, TData>({
    queryKey:
      branchScope && normalizedSaleId
        ? QUERY_KEYS.sales.receipt(branchScope, normalizedSaleId)
        : QUERY_KEYS.sales.disabled("receipt"),
    queryFn: () => salesService.getReceipt(normalizedSaleId),
    enabled,
    select: options?.select,
  });
}

export default useReceipt;
