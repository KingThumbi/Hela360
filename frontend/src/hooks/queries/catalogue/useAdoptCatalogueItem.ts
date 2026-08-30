/**
 * ============================================================================
 * Hela360 Adopt Master Catalogue Item Mutation
 * ============================================================================
 *
 * Adoption changes both:
 *
 * • tenant-visible Catalogue adoption state
 * • tenant Product catalogue
 *
 * Therefore both cache domains are invalidated after success.
 *
 * ============================================================================
 */

import {
  useCreateEntity,
} from "@/hooks/queries/common";

import {
  useQueryScope,
} from "@/hooks/useQueryScope";

import {
  invalidateCatalogue,
  invalidateProducts,
} from "@/lib/queryInvalidation";

import {
  catalogueService,
} from "@/services/catalogue";

import type {
  CatalogueAdoptedProduct,
} from "@/types/entities";

import type {
  AdoptCatalogueItemRequest,
} from "@/types/requests";


export interface AdoptCatalogueItemVariables {
  masterItemId: string;

  data: AdoptCatalogueItemRequest;
}


export function useAdoptCatalogueItem() {
  const {
    tenantScope,
  } = useQueryScope();

  return useCreateEntity<
    CatalogueAdoptedProduct,
    AdoptCatalogueItemVariables
  >(
    ({
      masterItemId,
      data,
    }) => {
      if (!tenantScope) {
        throw new Error(
          "Tenant scope is required to "
          + "adopt catalogue items.",
        );
      }

      return catalogueService.adoptItem(
        masterItemId,
        data,
      );
    },

    tenantScope
      ? async (queryClient) => {
          await Promise.all([
            invalidateCatalogue(
              queryClient,
              tenantScope,
            ),
            invalidateProducts(
              queryClient,
              tenantScope,
            ),
          ]);
        }
      : undefined,
  );
}


export default useAdoptCatalogueItem;
