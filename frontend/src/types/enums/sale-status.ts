/**
 * ============================================================================
 * Hela360 Sale Status
 * ============================================================================
 */

export const SALE_STATUSES = {
  COMPLETED: "completed",
  PAID: "paid",
  PARTIALLY_PAID: "partially_paid",
  VOIDED: "voided",
  PARTIALLY_REFUNDED: "partially_refunded",
  REFUNDED: "refunded",
} as const;

export type SaleStatus =
  (typeof SALE_STATUSES)[keyof typeof SALE_STATUSES];
