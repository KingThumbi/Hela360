/**
 * ============================================================================
 * Hela360 Update Supplier Mutation
 * ============================================================================
 *
 * Updates an existing supplier.
 *
 * Responsibilities
 * ----------------
 * • Update suppliers
 * • Invalidate affected caches
 * • Preserve full TanStack Query flexibility
 *
 * This hook powers:
 *
 * • Supplier Edit
 * • Supplier Maintenance
 * • Supplier Administration
 *
 * ============================================================================
 */

import {
  useUpdateEntity,
} from "@/hooks/queries/common";

import { useQueryScope } from "@/hooks/useQueryScope";
import {
  invalidateSuppliers,
} from "@/lib/queryInvalidation";

import {
  supplierService,
} from "@/services/suppliers";

import type {
  Supplier,
} from "@/types/entities";

import type {
  UpdateSupplierRequest,
} from "@/types/requests";

/* ============================================================================
 * Hook
 * ============================================================================
 */

/**
 * Updates an existing supplier.
 */
export function useUpdateSupplier() {
  const {
    tenantScope,
  } = useQueryScope();

  return useUpdateEntity<
    Supplier,
    UpdateSupplierRequest
  >(
    ({ id, data }) => {
      if (!tenantScope) {
        throw new Error(
          "Tenant scope is required to update suppliers.",
        );
      }

      return supplierService.updateSupplier(id, data);
    },

    tenantScope
      ? (queryClient) =>
          invalidateSuppliers(
            queryClient,
            tenantScope,
          )
      : undefined,
  );
}

export default useUpdateSupplier;
