/**
 * ============================================================================
 * Hela360 Customer Query
 * ============================================================================
 *
 * Retrieves a single customer.
 *
 * Responsibilities
 * ----------------
 * • Load a customer by identifier
 * • Cache individual customer records
 * • Support conditional loading
 * • Preserve full TanStack Query flexibility
 *
 * This hook powers:
 *
 * • Customer Details
 * • Customer Profile
 * • Customer Edit
 * • Customer Preview
 *
 * ============================================================================
 */

import {
  useEntity,
  type UseEntityOptions,
} from "@/hooks/queries/common";

import { useQueryScope } from "@/hooks/useQueryScope";
import {
  QUERY_KEYS,
} from "@/lib/queryKeys";

import {
  customerService,
} from "@/services/customers";

import type {
  Customer,
} from "@/types/entities";

/* ============================================================================
 * Hook
 * ============================================================================
 */

/**
 * Retrieves a single customer.
 */
export function useCustomer<
  TData = Customer,
>(
  id: string,

  options?: UseEntityOptions<
    Customer,
    TData
  >,
) {
  const {
    tenantScope,
    isTenantScopeReady,
  } = useQueryScope();

  return useEntity<
    Customer,
    TData
  >(
    tenantScope
      ? QUERY_KEYS.customers.detail(
          tenantScope,
          id,
        )
      : QUERY_KEYS.customers.disabled(
          "detail",
          id,
        ),

    () => customerService.getCustomer(id),

    {
      ...options,

      enabled:
        isTenantScopeReady &&
        Boolean(id) &&
        (options?.enabled ?? true),
    },
  );
}

export default useCustomer;
