/**
 * ============================================================================
 * Hela360 Archive Product Mutation
 * ============================================================================
 *
 * Archives a Product without deleting its master-data identity or historical
 * references.
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


export function useArchiveProduct() {
  const {
    tenantScope,
  } = useQueryScope();

  return useDeleteEntity<Product>(
    (id) => {
      if (!tenantScope) {
        throw new Error(
          "Tenant scope is required to archive products.",
        );
      }

      return productService.archiveProduct(id);
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

export default useArchiveProduct;
