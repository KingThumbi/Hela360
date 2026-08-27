/**
 * ============================================================================
 * Hela360 Approve Purchase Order Mutation
 * ============================================================================
 *
 * Approves a Purchase Order.
 *
 * Responsibilities
 * ----------------
 * • Approve purchase orders
 * • Advance procurement workflow
 * • Refresh procurement caches
 * • Preserve full TanStack Query flexibility
 *
 * This hook powers:
 *
 * • Procurement Approval
 * • Purchasing Workflow
 * • Supplier Order Authorization
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

export function useApprovePurchaseOrder() {
  return useMutation({
    mutationFn: (
      _payload: unknown,
    ): Promise<never> =>
      Promise.reject(
        new Error(
          "Purchase Order approval is not supported by the current backend API.",
        ),
      ),
  });
}

export default useApprovePurchaseOrder;
