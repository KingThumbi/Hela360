/**
 * ============================================================================
 * Hela360 Products Query
 * ============================================================================
 *
 * Retrieves a tenant-scoped, paginated collection of products.
 *
 * Responsibilities
 * ----------------
 * • Load paginated product collections
 * • Support search and filtering
 * • Preserve server-side pagination semantics
 * • Cache product list queries by tenant scope and request parameters
 * • Respect query enablement and tenant-readiness state
 *
 * This hook powers:
 *
 * • Product List
 * • Product Table
 * • Product Search
 * • Product Lookup
 * • POS product discovery
 *
 * ============================================================================
 */

import {
  usePaginatedQuery,
} from "@/hooks/queries/common";

import { useQueryScope } from "@/hooks/useQueryScope";
import { QUERY_KEYS } from "@/lib/queryKeys";

import { productService } from "@/services/products";

import type {
  PaginatedResponse,
} from "@/types/api";

import type {
  Product,
} from "@/types/entities";

import type {
  ListProductsRequest,
} from "@/types/requests";


/* ============================================================================
 * Hook
 * ============================================================================
 */

/**
 * Retrieve a paginated product collection within the active tenant scope.
 */
export function useProducts(
  params: ListProductsRequest,
  options?: {
    enabled?: boolean;
  },
) {
  const {
    tenantScope,
    isTenantScopeReady,
  } = useQueryScope();

  return usePaginatedQuery<
    Product,
    PaginatedResponse<Product>
  >(
    tenantScope
      ? QUERY_KEYS.products.list(
          tenantScope,
          params,
        )
      : QUERY_KEYS.products.disabled(
          "list",
        ),

    () =>
      productService.listProducts(
        params,
      ),

    {
      enabled:
        isTenantScopeReady &&
        (options?.enabled ?? true),
    },
  );
}

export default useProducts;