import {
  usePaginatedQuery,
} from "@/hooks/queries/common";

import {
  QUERY_KEYS,
} from "@/lib/queryKeys";

import {
  officeCatalogueSupplierService,
} from "@/services/office";

import type {
  ListOfficeCatalogueSuppliersRequest,
  OfficeCatalogueSupplier,
} from "@/types/officeSupplier";


export function useOfficeCatalogueSuppliers(
  params?: ListOfficeCatalogueSuppliersRequest,
  options?: {
    enabled?: boolean;
  },
) {
  return usePaginatedQuery<OfficeCatalogueSupplier>(
    QUERY_KEYS.office.catalogueSuppliers.list(
      params,
    ),

    () =>
      officeCatalogueSupplierService
        .listSuppliers(
          params,
        ),

    {
      enabled:
        options?.enabled ?? true,
    },
  );
}


export default useOfficeCatalogueSuppliers;
