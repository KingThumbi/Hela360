/**
 * ============================================================================
 * Hela360 Void Sale Mutation
 * ============================================================================
 *
 * Voids an existing sale.
 *
 * Responsibilities
 * ----------------
 * • Void sales
 * • Reverse unfinished transactions
 * • Preserve audit history
 * • Refresh enterprise caches
 * • Preserve full TanStack Query flexibility
 *
 * This hook powers:
 *
 * • Cashier Error Correction
 * • Duplicate Transaction Removal
 * • Incorrect Customer Transactions
 * * Cancel Before Settlement
 *
 * A void operation cancels the sale while preserving the transaction for
 * auditing. Sales should never be physically deleted.
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
 * Void sale is not supported by the verified backend API.
 */
export function useVoidSale() {
  return useMutation({
    mutationFn: (
      _payload: unknown,
    ): Promise<never> =>
      Promise.reject(
        new Error(
          "Sale void is not supported by the current backend API.",
        ),
      ),
  });
}

export default useVoidSale;
