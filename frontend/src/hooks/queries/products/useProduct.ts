/**
 * ============================================================================
 * Hela360 Product Query
 * ============================================================================
 *
 * Retrieves a single product.
 *
 * Responsibilities
 * ----------------
 * • Load a product by identifier
 * • Cache individual product records
 * • Support conditional loading
 * • Preserve full TanStack Query flexibility
 *
 * This hook powers:
 *
 * • Product Details
 * • Product Edit
 * • Product Preview
 * • Product Drawer
 *
 * ============================================================================
 */

import {
  useEntity,
  type UseEntityOptions,
} from "@/hooks/queries/common";

import { useQueryScope } from "@/hooks/useQueryScope";
import { QUERY_KEYS } from "@/lib/queryKeys";

import { productService } from "@/services/products";

import type {
  Product,
} from "@/types/entities";

/* ============================================================================
 * Hook
 * ============================================================================
 */

/**
 * Retrieves a single product.
 */
export function useProduct<
  TData = Product,
>(
  id: string,

  options?: UseEntityOptions<
    Product,
    TData
  >,
) {
  const {
    tenantScope,
    isTenantScopeReady,
  } = useQueryScope();

  return useEntity<
    Product,
    TData
  >(
    tenantScope
      ? QUERY_KEYS.products.detail(
          tenantScope,
          id,
        )
      : QUERY_KEYS.products.disabled(
          "detail",
          id,
        ),

    () => productService.getProduct(id),

    {
      ...options,

      enabled:
        isTenantScopeReady &&
        Boolean(id) &&
        (options?.enabled ?? true),
    },
  );
}

export default useProduct;
