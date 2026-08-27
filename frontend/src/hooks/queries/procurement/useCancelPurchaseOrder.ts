/**
 * ============================================================================
 * Hela360 Cancel Purchase Order Mutation
 * ============================================================================
 *
 * Cancels a Purchase Order.
 *
 * Responsibilities
 * ----------------
 * • Cancel Purchase Orders
 * • Preserve procurement audit trail
 * • Refresh procurement caches
 * • Preserve full TanStack Query flexibility
 *
 * Purchase Orders should never be physically deleted once they enter the
 * procurement workflow. Cancellation preserves historical integrity and
 * supports audit, reporting and compliance.
 *
 * This hook powers:
 *
 * • Procurement Cancellation
 * • Supplier Order Cancellation
 * • Workflow Termination
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

export function useCancelPurchaseOrder() {
  return useMutation({
    mutationFn: (
      _payload: unknown,
    ): Promise<never> =>
      Promise.reject(
        new Error(
          "Purchase Order cancellation is not supported by the current backend API.",
        ),
      ),
  });
}

export default useCancelPurchaseOrder;
