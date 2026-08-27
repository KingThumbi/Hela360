/**
 * ============================================================================
 * Hela360 Create Supplier Mutation
 * ============================================================================
 *
 * Creates a new supplier.
 *
 * Responsibilities
 * ----------------
 * • Create suppliers
 * • Invalidate affected caches
 * • Preserve full TanStack Query flexibility
 *
 * This hook powers:
 *
 * • New Supplier
 * • Supplier Registration
 * • Supplier Import
 *
 * ============================================================================
 */

import {
  useCreateEntity,
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
  CreateSupplierRequest,
} from "@/types/requests";

/* ============================================================================
 * Hook
 * ============================================================================
 */

/**
 * Creates a supplier.
 */
export function useCreateSupplier() {
  const {
    tenantScope,
  } = useQueryScope();

  return useCreateEntity<
    Supplier,
    CreateSupplierRequest
  >(
    (payload) => {
      if (!tenantScope) {
        throw new Error(
          "Tenant scope is required to create suppliers.",
        );
      }

      return supplierService.createSupplier(payload);
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

export default useCreateSupplier;
