/**
 * ============================================================================
 * Hela360 Product Units Query
 * ============================================================================
 *
 * Retrieves the units configured for a product.
 *
 * Responsibilities
 * ----------------
 * • Load product-specific units
 * • Preserve tenant-scoped query caching
 * • Support conditional query execution
 * • Expose unit conversion and pricing metadata
 *
 * This hook powers:
 *
 * • POS unit selection
 * • Product unit inspection
 * • Inventory receiving workflows
 * • Multi-unit pricing workflows
 *
 * ============================================================================
 */

import {
  useEntityList,
} from "@/hooks/queries/common";

import { useQueryScope } from "@/hooks/useQueryScope";
import { QUERY_KEYS } from "@/lib/queryKeys";

import { productService } from "@/services/products";

import type {
  ProductUnit,
} from "@/types/entities";


/* ============================================================================
 * Hook
 * ============================================================================
 */

/**
 * Retrieve the units configured for a product within the active tenant scope.
 */
export function useProductUnits(
  productId: string | number | undefined,
  options?: {
    enabled?: boolean;
  },
) {
  const {
    tenantScope,
    isTenantScopeReady,
  } = useQueryScope();

  const normalizedProductId =
    productId !== undefined
      ? String(productId).trim()
      : "";

  return useEntityList<ProductUnit>(
    tenantScope && normalizedProductId
      ? QUERY_KEYS.products.units(
          tenantScope,
          normalizedProductId,
        )
      : QUERY_KEYS.products.disabled(
          "units",
          normalizedProductId,
        ),

    () =>
      productService.listProductUnits(
        normalizedProductId,
      ),

    {
      enabled:
        isTenantScopeReady &&
        normalizedProductId.length > 0 &&
        (options?.enabled ?? true),
    },
  );
}

export default useProductUnits;