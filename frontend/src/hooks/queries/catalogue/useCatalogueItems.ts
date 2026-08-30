/**
 * ============================================================================
 * Hela360 Master Catalogue List Query
 * ============================================================================
 */

import {
  usePaginatedQuery,
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

import type {
  ListCatalogueItemsRequest,
} from "@/types/requests";


export function useCatalogueItems(
  params?: ListCatalogueItemsRequest,
  options?: {
    enabled?: boolean;
  },
) {
  const {
    tenantScope,
    isTenantScopeReady,
  } = useQueryScope();

  return usePaginatedQuery<CatalogueItem>(
    tenantScope
      ? QUERY_KEYS.catalogue.list(
          tenantScope,
          params,
        )
      : QUERY_KEYS.catalogue.disabled(
          "list",
        ),

    () =>
      catalogueService.listItems(
        params,
      ),

    {
      enabled:
        isTenantScopeReady &&
        Boolean(tenantScope) &&
        (options?.enabled ?? true),
    },
  );
}


export default useCatalogueItems;
