/**
 * ============================================================================
 * Hela360 Create Sale Mutation
 * ============================================================================
 *
 * Creates a new sale.
 *
 * Responsibilities
 * ----------------
 * • Execute POS checkout
 * • Create sales transactions
 * • Refresh sales caches
 * • Refresh inventory
 * • Refresh customer balances
 * • Refresh finance
 * • Refresh dashboards
 * • Preserve full TanStack Query flexibility
 *
 * This hook powers:
 *
 * • Pharmacy POS
 * • Retail POS
 * • Hospital POS
 * • Wholesale Sales
 *
 * ============================================================================
 */

import {
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

import {
  invalidateSalesOperations,
} from "@/lib/queryInvalidation";
import { useQueryScope } from "@/hooks/useQueryScope";

import {
  salesService,
} from "@/services/sales";

import type {
  Sale,
} from "@/types/entities";

import type {
  CreateSaleRequest,
} from "@/types/requests";

/* ============================================================================
 * Hook
 * ============================================================================
 */

/**
 * Executes a complete sale transaction.
 */
export function useCreateSale() {
  const queryClient = useQueryClient();
  const {
    branchScope,
  } = useQueryScope();

  return useMutation({
    mutationFn: (
      payload: CreateSaleRequest,
    ): Promise<Sale> =>
      salesService.createSale(
        payload,
      ),

    onSuccess: async () => {
      await invalidateSalesOperations(
        queryClient,
        branchScope ?? undefined,
      );
    },
  });
}

export default useCreateSale;
