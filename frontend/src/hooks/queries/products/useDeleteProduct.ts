/**
 * ============================================================================
 * Hela360 Delete Product Mutation
 * ============================================================================
 *
 * Permanently deletes an eligible archived Product.
 *
 * Permanent deletion is intentionally distinct from product archival.
 * The backend remains authoritative for deletion eligibility and rejects
 * products that retain historical or non-zero stock dependencies.
 *
 * Tenant scope is used for cache identity only. Backend tenant ownership
 * remains derived from the authenticated identity.
 *
 * ============================================================================
 */

import {
  useDeleteEntity,
} from "@/hooks/queries/common";

import {
  useQueryScope,
} from "@/hooks/useQueryScope";

import {
  invalidateProducts,
} from "@/lib/queryInvalidation";

import {
  productService,
} from "@/services/products";

import type {
  DeleteProductResponse,
} from "@/services/products";


/* ============================================================================
 * Hook
 * ============================================================================
 */

export function useDeleteProduct() {
  const {
    tenantScope,
  } = useQueryScope();

  return useDeleteEntity<DeleteProductResponse>(
    (id) => {
      if (!tenantScope) {
        throw new Error(
          "Tenant scope is required to delete products.",
        );
      }

      return productService.deleteProduct(id);
    },

    tenantScope
      ? (queryClient) =>
          invalidateProducts(
            queryClient,
            tenantScope,
          )
      : undefined,
  );
}

export default useDeleteProduct;
