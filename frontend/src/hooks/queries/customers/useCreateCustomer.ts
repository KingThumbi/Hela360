/**
 * ============================================================================
 * Hela360 Create Customer Mutation
 * ============================================================================
 *
 * Creates a new customer.
 *
 * Responsibilities
 * ----------------
 * • Create customers
 * • Invalidate affected caches
 * • Preserve full TanStack Query flexibility
 *
 * This hook powers:
 *
 * • New Customer
 * • Customer Registration
 * • Customer Import
 *
 * ============================================================================
 */

import {
  useCreateEntity,
} from "@/hooks/queries/common";

import { useQueryScope } from "@/hooks/useQueryScope";
import {
  invalidateCustomers,
} from "@/lib/queryInvalidation";

import {
  customerService,
} from "@/services/customers";

import type {
  Customer,
} from "@/types/entities";

import type {
  CreateCustomerRequest,
} from "@/types/requests";

/* ============================================================================
 * Hook
 * ============================================================================
 */

/**
 * Creates a customer.
 */
export function useCreateCustomer() {
  const {
    tenantScope,
  } = useQueryScope();

  return useCreateEntity<
    Customer,
    CreateCustomerRequest
  >(
    (payload) => {
      if (!tenantScope) {
        throw new Error(
          "Tenant scope is required to create customers.",
        );
      }

      return customerService.createCustomer(payload);
    },

    tenantScope
      ? (queryClient) =>
          invalidateCustomers(
            queryClient,
            tenantScope,
          )
      : undefined,
  );
}

export default useCreateCustomer;
