/**
 * ============================================================================
 * Hela360 Create Product Mutation
 * ============================================================================
 *
 * Creates a new product.
 *
 * Responsibilities
 * ----------------
 * • Create products
 * • Invalidate affected caches
 * • Preserve full TanStack Query flexibility
 *
 * This hook powers:
 *
 * • New Product
 * • Product Import
 * • Product Duplication
 *
 * ============================================================================
 */

import {
  useCreateEntity,
} from "@/hooks/queries/common";

import { useQueryScope } from "@/hooks/useQueryScope";
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
  CreateProductRequest,
} from "@/types/requests";

/* ============================================================================
 * Hook
 * ============================================================================
 */

/**
 * Creates a product.
 */
export function useCreateProduct() {
  const {
    tenantScope,
  } = useQueryScope();

  return useCreateEntity<
    Product,
    CreateProductRequest
  >(
    (payload) => {
      if (!tenantScope) {
        throw new Error(
          "Tenant scope is required to create products.",
        );
      }

      return productService.createProduct(payload);
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

export default useCreateProduct;
