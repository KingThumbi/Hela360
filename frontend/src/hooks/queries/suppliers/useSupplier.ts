/**
 * ============================================================================
 * Hela360 Supplier Query
 * ============================================================================
 *
 * Retrieves a single supplier.
 *
 * Responsibilities
 * ----------------
 * • Load a supplier by identifier
 * • Cache individual supplier records
 * • Support conditional loading
 * • Preserve full TanStack Query flexibility
 *
 * This hook powers:
 *
 * • Supplier Details
 * • Supplier Profile
 * • Supplier Edit
 * • Supplier Preview
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
  supplierService,
} from "@/services/suppliers";

import type {
  Supplier,
} from "@/types/entities";

/* ============================================================================
 * Hook
 * ============================================================================
 */

/**
 * Retrieves a single supplier.
 */
export function useSupplier<
  TData = Supplier,
>(
  id: string,

  options?: UseEntityOptions<
    Supplier,
    TData
  >,
) {
  const {
    tenantScope,
    isTenantScopeReady,
  } = useQueryScope();

  return useEntity<
    Supplier,
    TData
  >(
    tenantScope
      ? QUERY_KEYS.suppliers.detail(
          tenantScope,
          id,
        )
      : QUERY_KEYS.suppliers.disabled(
          "detail",
          id,
        ),

    () => supplierService.getSupplier(id),

    {
      ...options,

      enabled:
        isTenantScopeReady &&
        Boolean(id) &&
        (options?.enabled ?? true),
    },
  );
}

export default useSupplier;
