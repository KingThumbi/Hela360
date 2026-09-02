import {
  useQuery,
} from "@tanstack/react-query";

import {
  QUERY_KEYS,
} from "@/lib/queryKeys";

import {
  officeMasterItemService,
} from "@/services/office";


export function useOfficeMasterItemSupplierEvidence(
  masterItemId?: string,
) {
  const normalizedId =
    masterItemId?.trim() ?? "";

  return useQuery({
    queryKey:
      normalizedId
        ? QUERY_KEYS.office.masterItems
            .supplierEvidence(
              normalizedId,
            )
        : QUERY_KEYS.office.masterItems
            .supplierEvidence(
              "missing",
            ),

    queryFn: () =>
      officeMasterItemService
        .getSupplierEvidence(
          normalizedId,
        ),

    enabled:
      normalizedId.length > 0,
  });
}


export default useOfficeMasterItemSupplierEvidence;
