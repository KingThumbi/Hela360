import {
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

import {
  QUERY_KEYS,
} from "@/lib/queryKeys";

import {
  officeMasterItemService,
} from "@/services/office";

import type {
  OfficeMasterItemApprovalResult,
} from "@/types/officeCatalogue";


export function useApproveOfficeMasterItem() {
  const queryClient =
    useQueryClient();

  return useMutation<
    OfficeMasterItemApprovalResult,
    Error,
    string
  >({
    mutationFn: (
      masterItemId,
    ) =>
      officeMasterItemService.approveItem(
        masterItemId,
      ),

    onSuccess: async (
      item,
    ) => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey:
            QUERY_KEYS.office.masterItems.detail(
              item.id,
            ),
        }),

        queryClient.invalidateQueries({
          queryKey:
            QUERY_KEYS.office.masterItems.lists(),
        }),
      ]);
    },
  });
}


export default useApproveOfficeMasterItem;
