/**
 * ============================================================================
 * Hela360 Master Catalogue Item Query
 * ============================================================================
 */

import {
  useEntity,
} from "@/hooks/queries/common";

import {
  useQueryScope,
} from "@/hooks/useQueryScope";

import {
  QUERY_KEYS,
} from "@/lib/queryKeys";

import {
  catalogueService,
} from "@/services/catalogue";

import type {
  CatalogueItem,
} from "@/types/entities";


export function useCatalogueItem(
  masterItemId: string | undefined,
  options?: {
    enabled?: boolean;
  },
) {
  const {
    tenantScope,
    isTenantScopeReady,
  } = useQueryScope();

  const normalizedId =
    masterItemId?.trim() ?? "";

  return useEntity<CatalogueItem>(
    tenantScope && normalizedId
      ? QUERY_KEYS.catalogue.detail(
          tenantScope,
          normalizedId,
        )
      : QUERY_KEYS.catalogue.disabled(
          "detail",
          normalizedId,
        ),

    () =>
      catalogueService.getItem(
        normalizedId,
      ),

    {
      enabled:
        isTenantScopeReady &&
        Boolean(tenantScope) &&
        normalizedId.length > 0 &&
        (options?.enabled ?? true),
    },
  );
}


export default useCatalogueItem;
