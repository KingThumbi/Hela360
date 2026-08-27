/**
 * ============================================================================
 * Hela360 Sales Dashboard Query
 * ============================================================================
 *
 * Retrieves dashboard metrics for the Sales module.
 *
 * Responsibilities
 * ----------------
 * • Load sales KPIs
 * • Cache dashboard metrics
 * • Support automatic refresh
 * • Preserve full TanStack Query flexibility
 *
 * Dashboard metrics may include:
 *
 * • Gross Sales
 * • Net Sales
 * • Daily Sales
 * • Monthly Sales
 * • Average Basket Value
 * • Sales by Branch
 * • Sales by Cashier
 * • Sales by Payment Method
 * • Refund Totals
 * • Void Totals
 * • Top Selling Products
 * • Top Customers
 *
 * ============================================================================
 */

import {
  useQuery,
} from "@tanstack/react-query";

import {
  QUERY_KEYS,
} from "@/lib/queryKeys";

/* ============================================================================
 * Hook
 * ============================================================================
 */

/**
 * Retrieves Sales dashboard metrics.
 */
export function useSalesDashboard() {
  return useQuery<never>({
    queryKey:
      QUERY_KEYS.sales.dashboard(),

    queryFn: () =>
      Promise.reject(
        new Error(
          "Sales dashboard retrieval is not supported by the current backend API.",
        ),
      ),

    staleTime:
      1000 * 60,
  });
}

export default useSalesDashboard;
