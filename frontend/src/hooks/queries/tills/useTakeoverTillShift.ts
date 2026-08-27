import {
  useMutation,
} from "@tanstack/react-query";

import { useQueryScope } from "@/hooks/useQueryScope";
import {
  invalidateTillShifts,
} from "@/lib/queryInvalidation";
import {
  queryClient,
} from "@/lib/queryClient";
import {
  tillShiftService,
} from "@/services/tills";
import type {
  TillShift,
} from "@/types/entities";

export function useTakeoverTillShift() {
  const {
    branchScope,
  } = useQueryScope();

  return useMutation<TillShift, Error, string>({
    mutationFn: (id) => {
      if (!branchScope) {
        throw new Error(
          "Branch scope is required to take over a till shift.",
        );
      }

      return tillShiftService.takeover(id);
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

export default useTakeoverTillShift;
