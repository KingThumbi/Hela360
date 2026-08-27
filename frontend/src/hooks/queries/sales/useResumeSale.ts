/**
 * ============================================================================
 * Hela360 Resume Sale Mutation
 * ============================================================================
 *
 * Resumes a previously suspended sale.
 *
 * Responsibilities
 * ----------------
 * • Resume suspended sales
 * • Restore POS transactions
 * • Continue checkout workflow
 * • Refresh enterprise caches
 * • Preserve full TanStack Query flexibility
 *
 * This hook powers:
 *
 * • Resume Held Sale
 * • Resume Parked Transaction
 * • Continue Checkout
 * • Pharmacy Consultation Workflow
 * • Interrupted Checkout Recovery
 *
 * Resuming a sale restores a previously suspended transaction so the cashier
 * can continue the checkout process from where it was paused.
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
 * Resume sale is not supported by the verified backend API.
 */
export function useResumeSale() {
  return useMutation({
    mutationFn: (
      _payload: unknown,
    ): Promise<never> =>
      Promise.reject(
        new Error(
          "Sale resume is not supported by the current backend API.",
        ),
      ),
  });
}

export default useResumeSale;
