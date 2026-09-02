import {
  useQuery,
} from "@tanstack/react-query";

import {
  QUERY_KEYS,
} from "@/lib/queryKeys";

import {
  officeMasterItemService,
} from "@/services/office";


export function useOfficeMasterItem(
  masterItemId?: string,
) {
  const normalizedId =
    masterItemId?.trim() ?? "";

  return useQuery({
    queryKey:
      normalizedId
        ? QUERY_KEYS.office.masterItems.detail(
            normalizedId,
          )
        : QUERY_KEYS.office.masterItems.detail(
            "missing",
          ),

    queryFn: () =>
      officeMasterItemService.getItem(
        normalizedId,
      ),

    enabled:
      normalizedId.length > 0,
  });
}


export default useOfficeMasterItem;
