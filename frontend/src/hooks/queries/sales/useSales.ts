/**
 * ============================================================================
 * Hela360 Sales Query
 * ============================================================================
 *
 * Retrieves a paginated collection of sales.
 *
 * Responsibilities
 * ----------------
 * • Load sales
 * • Support filtering
 * • Support searching
 * • Support sorting
 * • Support pagination
 * • Cache sales collections
 *
 * This hook powers:
 *
 * • Sales Register
 * • POS History
 * • Customer Sales
 * • Branch Sales
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
  ListSalesRequest,
} from "@/types/requests";

import type {
  PaginatedResponse,
} from "@/types/api";
import type {
  SaleSummary,
} from "@/types/responses";

/* ============================================================================
 * Hook
 * ============================================================================
 */

/**
 * Retrieves a paginated collection of sales.
 */
export function useSales(
  params?: ListSalesRequest,
) {
  const {
    branchScope,
    isBranchScopeReady,
  } = useQueryScope();

  return useQuery<PaginatedResponse<SaleSummary>>({
    queryKey:
      branchScope
        ? QUERY_KEYS.sales.list(branchScope, params)
        : QUERY_KEYS.sales.disabled("list"),

    queryFn: () => salesService.listSales(params),

    enabled: isBranchScopeReady,
  });
}

export default useSales;
