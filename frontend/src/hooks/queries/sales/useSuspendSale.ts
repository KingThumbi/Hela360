/**
 * ============================================================================
 * Hela360 Suspend Sale Mutation
 * ============================================================================
 *
 * Suspends an in-progress sale.
 *
 * Responsibilities
 * ----------------
 * • Suspend POS transactions
 * • Preserve cart state
 * • Allow later resumption
 * • Refresh enterprise caches
 * • Preserve full TanStack Query flexibility
 *
 * This hook powers:
 *
 * • Hold Sale
 * • Park Transaction
 * • Queue Customer
 * • Pharmacy Consultation Workflow
 * • Interrupted Checkout
 *
 * Suspending a sale allows a cashier to temporarily save an in-progress
 * transaction without completing payment. The sale can later be resumed
 * and finalized.
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
 * Suspend sale is not supported by the verified backend API.
 */
export function useSuspendSale() {
  return useMutation({
    mutationFn: (
      _payload: unknown,
    ): Promise<never> =>
      Promise.reject(
        new Error(
          "Sale suspension is not supported by the current backend API.",
        ),
      ),
  });
}

export default useSuspendSale;
