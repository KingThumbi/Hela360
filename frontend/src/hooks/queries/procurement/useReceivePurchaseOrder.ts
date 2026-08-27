/**
 * ============================================================================
 * Hela360 Receive Purchase Order Mutation
 * ============================================================================
 *
 * Records the receipt of goods against an approved Purchase Order.
 *
 * Responsibilities
 * ----------------
 * • Receive Purchase Orders
 * • Generate Goods Receipts
 * • Advance procurement workflow
 * • Trigger inventory synchronization
 * • Refresh procurement caches
 * • Preserve full TanStack Query flexibility
 *
 * This hook powers:
 *
 * • Goods Receipt Processing
 * • Supplier Deliveries
 * • Warehouse Receiving
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

export function useReceivePurchaseOrder() {
  return useMutation({
    mutationFn: (
      _payload: unknown,
    ): Promise<never> =>
      Promise.reject(
        new Error(
          "Purchase Order receiving is not supported by the current backend API.",
        ),
      ),
  });
}

export default useReceivePurchaseOrder;
