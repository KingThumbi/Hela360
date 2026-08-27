import {
  useMutation,
} from "@tanstack/react-query";

import { useQueryScope } from "@/hooks/useQueryScope";
import {
  queryClient,
} from "@/lib/queryClient";
import {
  invalidateTillShifts,
} from "@/lib/queryInvalidation";
import {
  tillShiftService,
} from "@/services/tills";
import type {
  TillShift,
} from "@/types/entities";
import type {
  OpenTillShiftRequest,
} from "@/types/requests";

export function useOpenTillShift() {
  const {
    branchScope,
  } = useQueryScope();

  return useMutation<TillShift, Error, OpenTillShiftRequest>({
    mutationFn: (payload) => {
      if (!branchScope) {
        throw new Error(
          "Branch scope is required to open a till shift.",
        );
      }

      return tillShiftService.open(payload);
    },

    onSuccess: async () => {
      if (branchScope) {
        await invalidateTillShifts(
          queryClient,
          branchScope,
        );
      }
    },
  });
}

export default useOpenTillShift;
