/**
 * ============================================================================
 * Hela360 Suppliers Query
 * ============================================================================
 *
 * Retrieves a paginated list of suppliers.
 *
 * Responsibilities
 * ----------------
 * • Load paginated suppliers
 * • Support searching
 * • Support filtering
 * • Support sorting
 * • Support server-side pagination
 * • Cache supplier collections
 *
 * This hook powers:
 *
 * • Supplier List
 * • Supplier Table
 * • Supplier Search
 * • Supplier Lookup
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
  supplierService,
} from "@/services/suppliers";

import type {
  Supplier,
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

/**
 * Retrieves a paginated supplier collection.
 */
export function useSuppliers(
  params: PaginationRequest,
) {
  const {
    tenantScope,
    isTenantScopeReady,
  } = useQueryScope();

  return usePaginatedQuery<
    Supplier,
    PaginatedResponse<Supplier>
  >(
    tenantScope
      ? QUERY_KEYS.suppliers.list(
          tenantScope,
          params,
        )
      : QUERY_KEYS.suppliers.disabled(
          "list",
        ),

    () => supplierService.listSuppliers(params),

    {
      enabled: isTenantScopeReady,
    },
  );
}

export default useSuppliers;
