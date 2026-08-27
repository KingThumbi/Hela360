/**
 * ============================================================================
 * Hela360 Cashier Summary
 * ============================================================================
 *
 * Sales performance metrics for a cashier.
 *
 * ============================================================================
 */

export interface CashierSummary {
  cashierId: string;

  cashierName: string;

  totalSales: number;

  transactions: number;
}