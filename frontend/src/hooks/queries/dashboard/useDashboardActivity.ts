/**
 * ============================================================================
 * Hela360 Enterprise Dashboard Activity Query
 * ============================================================================
 *
 * Retrieves the dashboard activity feed.
 *
 * Responsibilities
 * ----------------
 * • Load recent business activity
 * • Retrieve operational events
 * • Cache activity independently
 * • Support query selection
 * • Preserve full TanStack Query flexibility
 *
 * Typical activity includes:
 *
 * • Sales completed
 * • Purchase orders received
 * • Goods received
 * • Inventory adjustments
 * • Stock transfers
 * • Refunds
 * • User logins
 * • User approvals
 * • System events
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

export type UseDashboardActivityOptions<
  TData = never,
> = {
  select?: (data: never) => TData;
};

/* ============================================================================
 * Hook
 * ============================================================================
 */

/**
 * Retrieves the dashboard activity feed.
 */
export function useDashboardActivity<
  TData = never,
>(
  _options?: UseDashboardActivityOptions<TData>,
): UseQueryResult<
  TData,
  DefaultError
> {
  return useQuery<never, DefaultError, TData>({
    queryKey: QUERY_KEYS.dashboard.activity(),
    queryFn: () =>
      Promise.reject(
        new Error(
          "Dashboard activity is not supported by the current backend API.",
        ),
      ),
    enabled: false,
    retry: false,
  });
}

export default useDashboardActivity;
