/**
 * ============================================================================
 * Hela360 Reactivate Supplier Mutation
 * ============================================================================
 *
 * Reactivates an existing supplier.
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

export function useReactivateSupplier() {
  const {
    tenantScope,
  } = useQueryScope();

  return useDeleteEntity<Supplier>(
    (id) => {
      if (!tenantScope) {
        throw new Error(
          "Tenant scope is required to reactivate suppliers.",
        );
      }

      return supplierService.reactivateSupplier(id);
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

export default useReactivateSupplier;
