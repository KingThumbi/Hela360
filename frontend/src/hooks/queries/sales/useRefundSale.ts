/**
 * ============================================================================
 * Hela360 Refund Sale Mutation
 * ============================================================================
 *
 * Processes a refund for a completed sale.
 *
 * Responsibilities
 * ----------------
 * • Process full refunds
 * • Process partial refunds
 * • Record the verified refund transaction
 * • Return inventory where applicable
 * • Preserve audit history
 * • Refresh enterprise caches
 * • Preserve full TanStack Query flexibility
 *
 * This hook powers:
 *
 * • Customer Returns
 * • Product Exchanges
 * • Refund Processing
 * • Return Merchandise Authorization (RMA)
 *
 * A refund creates a new financial transaction that references the original
 * sale. The original sale remains immutable for accounting, compliance and
 * auditing purposes.
 *
 * ============================================================================
 */

import {
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

import { useQueryScope } from "@/hooks/useQueryScope";
import {
  invalidateSalesOperations,
} from "@/lib/queryInvalidation";

import {
  salesService,
} from "@/services/sales";

import type {
  SaleRefund,
} from "@/types/entities";

import type {
  RefundSaleRequest,
} from "@/types/requests";

/* ============================================================================
 * Hook
 * ============================================================================
 */

/**
 * Processes a refund.
 */
export function useRefundSale() {
  const queryClient = useQueryClient();
  const {
    branchScope,
  } = useQueryScope();

  return useMutation({
    mutationFn: (
      payload: RefundSaleRequest,
    ): Promise<SaleRefund> => {
      const {
        sale_id,
        ...refundPayload
      } = payload;

      return salesService.refundSale(
        sale_id,
        refundPayload,
      );
    },

    onSuccess: async (_refund, variables) => {
      await invalidateSalesOperations(
        queryClient,
        branchScope ?? undefined,
        variables.sale_id,
      );
    },
  });
}

export default useRefundSale;
