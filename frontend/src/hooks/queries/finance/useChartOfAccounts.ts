import {
  useCreateEntity,
  useEntityList,
  useUpdateEntity,
} from "@/hooks/queries/common";
import { useQueryScope } from "@/hooks/useQueryScope";
import { QUERY_KEYS } from "@/lib/queryKeys";
import { chartOfAccountsService } from "@/services/finance";
import type {
  ChartOfAccount,
  CreateChartOfAccountRequest,
  UpdateChartOfAccountRequest,
} from "@/services/finance";

export function useChartOfAccounts(
  options: { enabled?: boolean } = {},
) {
  const { tenantScope, branchId, isTenantScopeReady } = useQueryScope();

  return useEntityList<ChartOfAccount>(
    tenantScope
      ? QUERY_KEYS.finance.chartOfAccounts(tenantScope, branchId)
      : QUERY_KEYS.finance.disabled("chart-of-accounts"),
    () => chartOfAccountsService.list(),
    { enabled: isTenantScopeReady && (options.enabled ?? true) },
  );
}

export function useCreateChartOfAccount() {
  const { tenantScope, branchId } = useQueryScope();

  return useCreateEntity<ChartOfAccount, CreateChartOfAccountRequest>(
    (payload) => {
      if (!tenantScope) {
        throw new Error("Tenant scope is required to create an account.");
      }
      return chartOfAccountsService.create(payload);
    },
    tenantScope
      ? async (queryClient) => {
          await queryClient.invalidateQueries({
            queryKey: QUERY_KEYS.finance.chartOfAccounts(tenantScope, branchId),
          });
        }
      : undefined,
  );
}

export function useUpdateChartOfAccount() {
  const { tenantScope, branchId } = useQueryScope();

  return useUpdateEntity<ChartOfAccount, UpdateChartOfAccountRequest>(
    ({ id, data }) => {
      if (!tenantScope) {
        throw new Error("Tenant scope is required to update an account.");
      }
      return chartOfAccountsService.update(String(id), data);
    },
    tenantScope
      ? async (queryClient) => {
          await queryClient.invalidateQueries({
            queryKey: QUERY_KEYS.finance.chartOfAccounts(tenantScope, branchId),
          });
        }
      : undefined,
  );
}
