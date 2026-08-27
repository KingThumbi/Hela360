/**
 * ============================================================================
 * Hela360 Sale Payment Query
 * ============================================================================
 *
 * Retrieves a single sale payment.
 *
 * Responsibilities
 * ----------------
 * • Load payment details
 * • Cache payment records
 * • Support conditional loading
 * • Preserve full TanStack Query flexibility
 *
 * This hook powers:
 *
 * • Payment Details
 * • Payment Audit
 * • Financial Investigation
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
 * Retrieves a single payment.
 */
export function useSalePayment<
  TData = SalePayment,
>(
  paymentId: string,
  _options?: unknown,
) {
  return useQuery<TData>({
    queryKey:
      QUERY_KEYS.sales.payment(
      paymentId,
    ),

    queryFn: () =>
      Promise.reject(
        new Error(
          "Sale payment detail retrieval is not supported by the current backend API.",
        ),
      ),

    enabled: Boolean(paymentId),
  });
}

export default useSalePayment;
