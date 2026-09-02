import {
  usePaginatedQuery,
} from "@/hooks/queries/common";

import {
  QUERY_KEYS,
} from "@/lib/queryKeys";

import {
  officeMasterItemService,
} from "@/services/office";

import type {
  ListOfficeMasterItemsRequest,
  OfficeMasterItem,
} from "@/types/officeCatalogue";


export function useOfficeMasterItems(
  params?: ListOfficeMasterItemsRequest,
  options?: {
    enabled?: boolean;
  },
) {
  return usePaginatedQuery<OfficeMasterItem>(
    QUERY_KEYS.office.masterItems.list(
      params,
    ),

    () =>
      officeMasterItemService.listItems(
        params,
      ),

    {
      enabled:
        options?.enabled ?? true,
    },
  );
}


export default useOfficeMasterItems;
