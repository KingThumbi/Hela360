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
  TillShiftReconciliation,
} from "@/types/entities";
import type {
  CloseTillShiftRequest,
} from "@/types/requests";

interface CloseTillShiftVariables {
  readonly id: string;

  readonly payload: CloseTillShiftRequest;
}

interface CloseTillShiftResult {
  readonly reconciliation: TillShiftReconciliation;
}

export function useCloseTillShift() {
  const {
    branchScope,
  } = useQueryScope();

  return useMutation<
    CloseTillShiftResult,
    Error,
    CloseTillShiftVariables
  >({
    mutationFn: ({ id, payload }) => {
      if (!branchScope) {
        throw new Error(
          "Branch scope is required to close a till shift.",
        );
      }

      return tillShiftService.close(id, payload);
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

export default useCloseTillShift;
