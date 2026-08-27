/**
 * ============================================================================
 * Hela360 Delete Customer Mutation
 * ============================================================================
 *
 * Deletes an existing customer.
 *
 * Responsibilities
 * ----------------
 * • Delete customers
 * • Invalidate affected caches
 * • Preserve full TanStack Query flexibility
 *
 * This hook powers:
 *
 * • Customer Deletion
 * • Customer Administration
 * • Customer Cleanup
 *
 * ============================================================================
 */

import {
  useDeleteEntity,
} from "@/hooks/queries/common";

import {
  customerService,
} from "@/services/customers";

/* ============================================================================
 * Hook
 * ============================================================================
 */

/**
 * Deletes an existing customer.
 */
export function useDeleteCustomer() {
  return useDeleteEntity(
    (id) => customerService.delete(id),
  );
}

export default useDeleteCustomer;
