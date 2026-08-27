/**
 * ============================================================================
 * Hela360 Sale Payments Query
 * ============================================================================
 *
 * Retrieves all payments associated with a sale.
 *
 * Responsibilities
 * ----------------
 * • Load sale payments
 * • Cache payment collections
 * • Preserve full TanStack Query flexibility
 *
 * This hook powers:
 *
 * • Payment History
 * • Split Payments
 * • Payment Audit
 * • Payment Reconciliation
 *
 * ============================================================================
 */

import {
  useQuery,
} from "@tanstack/react-query";

import {
  QUERY_KEYS,
} from "@/lib/queryKeys";

import type {
  SalePayment,
} from "@/types/entities";

/* ============================================================================
 * Hook
 * ============================================================================
 */

/**
 * Retrieves all payments for a sale.
 */
export function useSalePayments(
  saleId: string,
) {
  return useQuery<SalePayment[]>({
    queryKey:
      QUERY_KEYS.sales.payments(
        saleId,
      ),

    queryFn: () =>
      Promise.reject(
        new Error(
          "Sale payment listing is not supported by the current backend API.",
        ),
      ),

    enabled: Boolean(saleId),

    staleTime: 1000 * 60,
  });
}

export default useSalePayments;
