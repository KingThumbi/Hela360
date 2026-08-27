/**
 * ============================================================================
 * Hela360 Create Purchase Order Mutation
 * ============================================================================
 *
 * Creates a new Purchase Order.
 *
 * Responsibilities
 * ----------------
 * • Create Purchase Orders
 * • Trigger procurement workflow
 * • Refresh procurement caches
 * • Preserve full TanStack Query flexibility
 *
 * This hook powers:
 *
 * • Procurement
 * • Supplier Purchasing
 * • Inventory Replenishment
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

export function useCreatePurchaseOrder() {
  return useMutation({
    mutationFn: (
      _payload: unknown,
    ): Promise<never> =>
      Promise.reject(
        new Error(
          "Purchase Order creation is not supported by the current backend API.",
        ),
      ),
  });
}

export default useCreatePurchaseOrder;
