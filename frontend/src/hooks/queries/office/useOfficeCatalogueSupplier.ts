import {
  useQuery,
} from "@tanstack/react-query";

import {
  QUERY_KEYS,
} from "@/lib/queryKeys";

import {
  officeCatalogueSupplierService,
} from "@/services/office";


export function useOfficeCatalogueSupplier(
  supplierId?: string,
) {
  const normalizedId =
    supplierId?.trim() ?? "";

  return useQuery({
    queryKey:
      normalizedId
        ? QUERY_KEYS.office.catalogueSuppliers.detail(
            normalizedId,
          )
        : QUERY_KEYS.office.catalogueSuppliers.detail(
            "missing",
          ),

    queryFn: () =>
      officeCatalogueSupplierService.getSupplier(
        normalizedId,
      ),

    enabled:
      normalizedId.length > 0,
  });
}


export default useOfficeCatalogueSupplier;
