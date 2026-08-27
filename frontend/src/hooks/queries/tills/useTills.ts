import {
  useQuery,
} from "@tanstack/react-query";

import { useQueryScope } from "@/hooks/useQueryScope";
import {
  QUERY_KEYS,
} from "@/lib/queryKeys";
import {
  tillService,
} from "@/services/tills";
import type {
  Till,
} from "@/types/entities";

export function useTills() {
  const {
    branchScope,
    isBranchScopeReady,
  } = useQueryScope();

  return useQuery<Till[]>({
    queryKey: branchScope
      ? QUERY_KEYS.tills.list(branchScope)
      : QUERY_KEYS.tills.disabled("list"),

    queryFn: () => tillService.listTills(),

    enabled: isBranchScopeReady,
  });
}

export default useTills;
