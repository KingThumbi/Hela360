import {
  useQuery,
} from "@tanstack/react-query";

import { useQueryScope } from "@/hooks/useQueryScope";
import {
  QUERY_KEYS,
} from "@/lib/queryKeys";
import {
  warehouseService,
} from "@/services/warehouses";
import type {
  Warehouse,
} from "@/types/entities";

export function useWarehouses() {
  const {
    branchScope,
    isBranchScopeReady,
  } = useQueryScope();

  return useQuery<Warehouse[]>({
    queryKey: branchScope
      ? QUERY_KEYS.warehouses.list(branchScope)
      : QUERY_KEYS.warehouses.disabled("list"),

    queryFn: () =>
      warehouseService.listWarehouses(),

    enabled: isBranchScopeReady,
  });
}

export default useWarehouses;
