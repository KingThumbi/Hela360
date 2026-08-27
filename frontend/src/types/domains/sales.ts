/**
 * ============================================================================
 * Hela360 Sales Domain Types
 * ============================================================================
 *
 * Public export surface for every Sales domain type.
 *
 * Consumers should import from this module rather than importing directly
 * from entities/, requests/, responses/, or enums/.
 *
 * This file serves as the stable public API for the Sales domain.
 *
 * ============================================================================
 */

/* ============================================================================
 * Entities
 * ============================================================================
 */

export * from "@/types/entities/sale";
export * from "@/types/entities/sale-item";
export * from "@/types/entities/sale-payment";

/* ============================================================================
 * Requests
 * ============================================================================
 */

export * from "@/types/requests/create-sale-item-request";
export * from "@/types/requests/create-sale-payment-request";
export * from "@/types/requests/create-sale-request";
export * from "@/types/requests/update-sale-request";

/* ============================================================================
 * Responses
 * ============================================================================
 */

export type {
  DailySalesSummary,
} from "@/types/responses/daily-sales-summary";
export type {
  CashierSummary,
} from "@/types/responses/cashier-summary";

/* ============================================================================
 * Enums
 * ============================================================================
 */

export * from "@/types/enums/payment-method";
export * from "@/types/enums/sale-status";
