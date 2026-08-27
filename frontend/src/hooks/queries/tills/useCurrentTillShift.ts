import {
  useQuery,
} from "@tanstack/react-query";

import { useQueryScope } from "@/hooks/useQueryScope";
import {
  QUERY_KEYS,
} from "@/lib/queryKeys";
import {
  tillShiftService,
} from "@/services/tills";
import type {
  TillShift,
} from "@/types/entities";

export function useCurrentTillShift(
  tillId?: string,
) {
  const {
    branchScope,
    isBranchScopeReady,
  } = useQueryScope();

  return useQuery<TillShift | null>({
    queryKey: branchScope
      ? QUERY_KEYS.tillShifts.current(
          branchScope,
          tillId,
        )
      : QUERY_KEYS.tillShifts.disabled(
          "current",
          tillId,
        ),

    queryFn: () =>
      tillShiftService.getCurrent(tillId),

    enabled: isBranchScopeReady,
  });
}

export default useCurrentTillShift;
