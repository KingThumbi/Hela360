/**
 * ============================================================================
 * Hela360 Customers Query
 * ============================================================================
 *
 * Retrieves a paginated list of customers.
 *
 * Responsibilities
 * ----------------
 * • Load paginated customers
 * • Support searching
 * • Support filtering
 * • Support sorting
 * • Support server-side pagination
 * • Cache customer collections
 *
 * This hook powers:
 *
 * • Customer List
 * • Customer Table
 * • Customer Search
 * • Customer Lookup
 *
 * ============================================================================
 */

import {
  usePaginatedQuery,
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

import type {
  PaginationRequest,
} from "@/types/requests";

import type {
  PaginatedResponse,
} from "@/types/api";

/* ============================================================================
 * Hook
 * ============================================================================
 */

export function useCustomers(
  params: PaginationRequest,
) {
  const {
    tenantScope,
    isTenantScopeReady,
  } = useQueryScope();

  return usePaginatedQuery<
    Customer,
    PaginatedResponse<Customer>
  >(
    tenantScope
      ? QUERY_KEYS.customers.list(
          tenantScope,
          params,
        )
      : QUERY_KEYS.customers.disabled(
          "list",
        ),

    () => customerService.listCustomers(params),

    {
      enabled: isTenantScopeReady,
    },
  );
}

export default useCustomers;
