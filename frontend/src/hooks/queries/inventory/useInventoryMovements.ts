import {
  useQuery,
} from "@tanstack/react-query";

import { useQueryScope } from "@/hooks/useQueryScope";
import {
  QUERY_KEYS,
} from "@/lib/queryKeys";
import {
  inventoryService,
} from "@/services/inventory";
import type {
  ListInventoryMovementsRequest,
} from "@/types/requests";
import type {
  InventoryMovementSummary,
} from "@/types/responses";
import type {
  PaginatedResponse,
} from "@/types/api";

export function useInventoryMovements(
  params?: ListInventoryMovementsRequest,
) {
  const {
    branchScope,
    isBranchScopeReady,
  } = useQueryScope();

  return useQuery<PaginatedResponse<InventoryMovementSummary>>({
    queryKey: branchScope
      ? QUERY_KEYS.inventory.movements(branchScope, params)
      : QUERY_KEYS.inventory.disabled("movements", "list"),

    queryFn: () =>
      inventoryService.listMovements(params),

    enabled: isBranchScopeReady,
  });
}

export default useInventoryMovements;
