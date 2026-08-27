/**
 * ============================================================================
 * Hela360 Enterprise Dashboard Alerts Query
 * ============================================================================
 *
 * Retrieves operational alerts displayed on the dashboard.
 *
 * Responsibilities
 * ----------------
 * • Load dashboard alerts
 * • Retrieve actionable business notifications
 * • Cache alerts independently
 * • Support query selection
 * • Preserve full TanStack Query flexibility
 *
 * Typical alerts include:
 *
 * • Low stock products
 * • Out of stock products
 * • Expiring medicines
 * • Pending purchase orders
 * • Pending approvals
 * • Overdue supplier invoices
 * • Failed integrations
 * • System health notifications
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

export type UseDashboardAlertsOptions<
  TData = never,
> = {
  select?: (data: never) => TData;
};

/* ============================================================================
 * Hook
 * ============================================================================
 */

/**
 * Retrieves operational dashboard alerts.
 */
export function useDashboardAlerts<
  TData = never,
>(
  _options?: UseDashboardAlertsOptions<TData>,
): UseQueryResult<
  TData,
  DefaultError
> {
  return useQuery<never, DefaultError, TData>({
    queryKey: QUERY_KEYS.dashboard.alerts(),
    queryFn: () =>
      Promise.reject(
        new Error(
          "Dashboard alerts are not supported by the current backend API.",
        ),
      ),
    enabled: false,
    retry: false,
  });
}

export default useDashboardAlerts;
