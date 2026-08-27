/**
 * ============================================================================
 * Hela360 Delete Supplier Mutation
 * ============================================================================
 *
 * Deactivates an existing supplier.
 *
 * Responsibilities
 * ----------------
 * • Deactivate suppliers
 * • Invalidate affected caches
 * • Preserve full TanStack Query flexibility
 *
 * This hook powers:
 *
 * • Supplier deactivation
 * • Supplier Administration
 * • Supplier Cleanup
 *
 * ============================================================================
 */

import {
  useDeleteEntity,
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

/* ============================================================================
 * Hook
 * ============================================================================
 */

/**
 * Transitional compatibility hook for Supplier deactivation.
 *
 * The verified backend does not support hard deletion.
 */
export function useDeleteSupplier() {
  const {
    tenantScope,
  } = useQueryScope();

  return useDeleteEntity<Supplier>(
    (id) => {
      if (!tenantScope) {
        throw new Error(
          "Tenant scope is required to deactivate suppliers.",
        );
      }

      return supplierService.deactivateSupplier(id);
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

export default useDeleteSupplier;
