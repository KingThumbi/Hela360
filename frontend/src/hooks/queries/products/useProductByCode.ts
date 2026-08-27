/**
 * ============================================================================
 * Hela360 Product By-Code Query
 * ============================================================================
 *
 * Retrieves a Product through a registered ProductCode value.
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

import type { Product } from "@/types/entities";

export function useProductByCode<
  TData = Product,
>(
  codeValue: string,
  options?: UseEntityOptions<
    Product,
    TData
  >,
) {
  const {
    tenantScope,
    isTenantScopeReady,
  } = useQueryScope();

  const normalizedCode = codeValue.trim();

  return useEntity<
    Product,
    TData
  >(
    tenantScope
      ? QUERY_KEYS.products.byCode(
          tenantScope,
          normalizedCode,
        )
      : QUERY_KEYS.products.disabled(
          "by-code",
          normalizedCode,
        ),

    () =>
      productService.getProductByCode(
        normalizedCode,
      ),

    {
      ...options,
      enabled:
        isTenantScopeReady &&
        normalizedCode.length > 0 &&
        (options?.enabled ?? true),
    },
  );
}

export default useProductByCode;
