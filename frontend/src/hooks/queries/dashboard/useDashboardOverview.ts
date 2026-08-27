/**
 * ============================================================================
 * Hela360 Tenant Dashboard Overview Query
 * ============================================================================
 *
 * Retrieves the authenticated tenant and branch dashboard projection.
 *
 * Scope is resolved by the backend authenticated identity. The frontend does
 * not supply tenant_id or branch_id.
 *
 * Query execution may be disabled when the authenticated user is not allowed
 * to consume this dashboard projection.
 * ============================================================================
 */

import {
  useQuery,
  type DefaultError,
  type UseQueryResult,
} from "@tanstack/react-query";

import { createQueryOptions } from "@/lib/queryFactory";
import { QUERY_KEYS } from "@/lib/queryKeys";

import {
  dashboardService,
  type DashboardOverview,
  type DashboardOverviewParams,
} from "@/services/dashboard";

/* ============================================================================
 * Options
 * ============================================================================
 */

export interface UseDashboardOverviewOptions<
  TData = DashboardOverview,
> {
  params?: DashboardOverviewParams;

  enabled?: boolean;

  select?: (
    data: DashboardOverview,
  ) => TData;
}

/* ============================================================================
 * Hook
 * ============================================================================
 */

export function useDashboardOverview<
  TData = DashboardOverview,
>(
  options?: UseDashboardOverviewOptions<TData>,
): UseQueryResult<TData, DefaultError> {
  const params = options?.params;

  return useQuery({
    ...createQueryOptions(
      QUERY_KEYS.dashboard.overview(
        params?.operational_date,
      ),
      () => dashboardService.overview(params),
      {
        enabled: options?.enabled ?? true,
      },
    ),

    select: options?.select,
  });
}

export default useDashboardOverview;
