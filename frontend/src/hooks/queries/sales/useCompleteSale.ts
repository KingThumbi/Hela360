/**
 * ============================================================================
 * Hela360 Complete Sale Mutation
 * ============================================================================
 *
 * Completes a sale transaction.
 *
 * Responsibilities
 * ----------------
 * • Complete sales
 * • Finalize POS transactions
 * • Confirm payments
 * • Deduct inventory
 * • Generate receipts
 * • Refresh enterprise caches
 * • Preserve full TanStack Query flexibility
 *
 * This hook powers:
 *
 * • POS Checkout
 * • Cash Sales
 * • Card Payments
 * • Mobile Money Payments
 * • Credit Sales
 *
 * ============================================================================
 */

import {
  useMutation,
} from "@tanstack/react-query";

/* ============================================================================
 * Hook
 * ============================================================================
 */

/**
 * Complete sale is not supported by the verified backend API.
 */
export function useCompleteSale() {
  return useMutation({
    mutationFn: (
      _payload: unknown,
    ): Promise<never> =>
      Promise.reject(
        new Error(
          "Sale completion is not supported by the current backend API.",
        ),
      ),
  });
}

export default useCompleteSale;
