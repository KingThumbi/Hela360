import { useMemo } from "react";

import { useAuthStore } from "@/store/authStore";
import { useShellStore } from "@/store/shellStore";
import type {
  BranchQueryScope,
  QueryScopeReadiness,
  TenantQueryScope,
} from "@/types/domains/query-scope";

function normalizeOptionalScopeId(value: string | null | undefined): string | null {
  if (value === undefined || value === null) {
    return null;
  }

  const normalized = value.trim();

  return normalized.length > 0 ? normalized : null;
}

export function useQueryScope(): QueryScopeReadiness {
  const isInitializing = useAuthStore(
    (state) => state.isInitializing,
  );

  const tenantId = useAuthStore((state) =>
    isInitializing
      ? null
      : normalizeOptionalScopeId(state.identity?.tenantId),
  );
  const branchId = useShellStore((state) =>
    normalizeOptionalScopeId(state.selectedBranchId),
  );

  return useMemo(() => {
    const tenantScope: TenantQueryScope | null =
      tenantId === null
        ? null
        : Object.freeze({
            tenantId,
          });

    const branchScope: BranchQueryScope | null =
      tenantId === null || branchId === null
        ? null
        : Object.freeze({
            tenantId,
            branchId,
          });

    return {
      tenantId,
      branchId,
      tenantScope,
      branchScope,
      isTenantScopeReady: tenantScope !== null,
      isBranchScopeReady: branchScope !== null,
    };
  }, [branchId, tenantId]);
}

export default useQueryScope;
