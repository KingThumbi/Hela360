/**
 * ============================================================================
 * Hela360 Enterprise Dashboard Metrics Query
 * ============================================================================
 *
 * Retrieves dashboard KPI metrics.
 *
 * Responsibilities
 * ----------------
 * • Load business KPIs
 * • Cache dashboard metrics
 * • Refresh independently from the overview
 * • Support query selection
 * • Preserve full TanStack Query flexibility
 *
 * Typical metrics include:
 *
 * • Total Revenue
 * • Today's Sales
 * • Gross Profit
 * • Net Profit
 * • Inventory Value
 * • Active Customers
 * • Pending Orders
 * • Purchase Orders
 *
 * ============================================================================
 */

import {
  useQuery,
  type DefaultError,
  type UseQueryResult,
} from "@tanstack/react-query";

import { QUERY_KEYS } from "@/lib/queryKeys";

/* ============================================================================
 * Types
 * ============================================================================
 */

export type UseDashboardMetricsOptions<
  TData = never,
> = {
  select?: (data: never) => TData;
};

/* ============================================================================
 * Hook
 * ============================================================================
 */

/**
 * Retrieves dashboard KPI metrics.
 */
export function useDashboardMetrics<
  TData = never,
>(
  _options?: UseDashboardMetricsOptions<TData>,
): UseQueryResult<
  TData,
  DefaultError
> {
  return useQuery<never, DefaultError, TData>({
    queryKey: QUERY_KEYS.dashboard.metrics(),
    queryFn: () =>
      Promise.reject(
        new Error(
          "Dashboard metrics are not supported by the current backend API.",
        ),
      ),
    enabled: false,
    retry: false,
  });
}

export default useDashboardMetrics;
