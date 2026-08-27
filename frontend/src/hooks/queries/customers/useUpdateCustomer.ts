/**
 * ============================================================================
 * Hela360 Update Customer Mutation
 * ============================================================================
 *
 * Customer update placeholder.
 *
 * Responsibilities
 * ----------------
 * • Update customers
 * • Invalidate affected caches
 * • Preserve full TanStack Query flexibility
 *
 * This hook powers:
 *
 * • Customer Edit
 * • Customer Maintenance
 * • Customer Administration
 *
 * ============================================================================
 */

import {
  useUpdateEntity,
} from "@/hooks/queries/common";

import type {
  Customer,
} from "@/types/entities";

import type {
  UpdateCustomerRequest,
} from "@/types/requests";

/* ============================================================================
 * Hook
 * ============================================================================
 */

/**
 * Customer update is not supported by the verified backend API.
 */
export function useUpdateCustomer() {
  return useUpdateEntity<
    Customer,
    UpdateCustomerRequest
  >(
    async (): Promise<Customer> => {
      throw new Error(
        "Customer update is not supported by the current backend API.",
      );
    },
  );
}

export default useUpdateCustomer;
