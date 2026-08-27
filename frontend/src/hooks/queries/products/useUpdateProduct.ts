/**
 * ============================================================================
 * Hela360 Update Product Mutation
 * ============================================================================
 *
 * Updates approved Product master-data fields and refreshes Product caches.
 *
 * Tenant scope is used for cache identity only. Backend tenant ownership
 * remains derived from the authenticated identity.
 *
 * ============================================================================
 */

import {
  useUpdateEntity,
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

import type {
  UpdateProductRequest,
} from "@/types/requests";


export function useUpdateProduct() {
  const {
    tenantScope,
  } = useQueryScope();

  return useUpdateEntity<
    Product,
    UpdateProductRequest
  >(
    ({ id, data }) => {
      if (!tenantScope) {
        throw new Error(
          "Tenant scope is required to update products.",
        );
      }

      return productService.updateProduct(
        id,
        data,
      );
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

export default useUpdateProduct;
