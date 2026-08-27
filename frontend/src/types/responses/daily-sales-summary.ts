/**
 * ============================================================================
 * Hela360 Daily Sales Summary
 * ============================================================================
 *
 * Aggregated sales metrics for a single business day.
 *
 * ============================================================================
 */

export interface DailySalesSummary {
  salesCount: number;

  grossSales: number;

  discounts: number;

  taxes: number;

  refunds: number;

  netSales: number;
}