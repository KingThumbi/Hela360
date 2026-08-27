/**
 * ============================================================================
 * Hela360 Restore Product Mutation
 * ============================================================================
 *
 * Restores an archived Product to active operational use.
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
  Product,
} from "@/types/entities";


export function useRestoreProduct() {
  const {
    tenantScope,
  } = useQueryScope();

  return useDeleteEntity<Product>(
    (id) => {
      if (!tenantScope) {
        throw new Error(
          "Tenant scope is required to restore products.",
        );
      }

      return productService.restoreProduct(id);
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

export default useRestoreProduct;
